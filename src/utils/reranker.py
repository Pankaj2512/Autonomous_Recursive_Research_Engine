"""Hybrid Search Re-Ranking Engine combining lexical matching and semantic vector scoring."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List


def _tokenize(text: str) -> List[str]:
    """Extract normalized alphanumeric tokens from text."""
    return re.findall(r"\b\w{2,}\b", text.lower())


def _compute_bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    avg_doc_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute BM25 score approximation for a document given query terms."""
    if not doc_tokens or not query_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    doc_freqs = Counter(doc_tokens)
    score = 0.0

    for token in query_tokens:
        tf = doc_freqs.get(token, 0)
        if tf > 0:
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / (avg_doc_len or 1.0)))
            score += numerator / (denominator or 1.0)

    return score


def hybrid_rerank_passages(
    query: str,
    passages: List[Dict[str, Any]],
    alpha: float = 0.65,
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    """Re-rank retrieved passages using hybrid lexical (BM25) and semantic vector fusion.

    Args:
        query: User search query or sub-question.
        passages: List of passage dicts containing 'text' and optional 'score' (semantic).
        alpha: Weight for semantic score (1.0 = purely semantic, 0.0 = purely lexical).
        top_k: Maximum ranked passages to return.

    Returns:
        List of re-ranked passages with updated composite 'hybrid_score'.
    """
    if not passages:
        return []

    query_tokens = _tokenize(query)
    doc_token_lists = [_tokenize(p.get("text", "") or p.get("snippet", "")) for p in passages]
    avg_len = sum(len(dt) for dt in doc_token_lists) / (len(doc_token_lists) or 1.0)

    # 1. Compute raw lexical BM25 scores
    lexical_scores = [
        _compute_bm25_score(query_tokens, dt, avg_len) for dt in doc_token_lists
    ]
    max_lex = max(lexical_scores) if lexical_scores and max(lexical_scores) > 0 else 1.0
    norm_lexical = [s / max_lex for s in lexical_scores]

    # 2. Extract and normalize semantic scores
    semantic_scores = [float(p.get("score", 0.5)) for p in passages]
    max_sem = max(semantic_scores) if semantic_scores and max(semantic_scores) > 0 else 1.0
    norm_semantic = [s / max_sem for s in semantic_scores]

    # 3. Fuse scores via weighted linear combination
    reranked = []
    for i, p in enumerate(passages):
        composite_score = (alpha * norm_semantic[i]) + ((1.0 - alpha) * norm_lexical[i])
        item = dict(p)
        item["semantic_score"] = round(norm_semantic[i], 3)
        item["lexical_score"] = round(norm_lexical[i], 3)
        item["hybrid_score"] = round(composite_score, 3)
        reranked.append(item)

    reranked.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return reranked[:top_k]
