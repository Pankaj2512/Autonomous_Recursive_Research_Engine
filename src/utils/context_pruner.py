"""Dynamic context pruning and deduplication engine."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def _text_fingerprint(text: str) -> str:
    """Generate normalized alphanumeric fingerprint for near-duplicate detection."""
    clean = re.sub(r"[^a-zA-Z0-9]", "", text.lower())
    return clean[:80]


def prune_and_deduplicate_sources(
    sources: List[Dict[str, Any]],
    max_snippet_chars: int = 1200,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Filter duplicate URLs, prune redundant snippets, and calculate token savings.

    Args:
        sources: List of raw source dictionaries.
        max_snippet_chars: Upper boundary on character length per snippet.

    Returns:
        Tuple of (pruned_sources, optimization_metrics).
    """
    seen_urls = set()
    seen_fingerprints = set()
    pruned: List[Dict[str, Any]] = []

    raw_char_count = 0
    optimized_char_count = 0

    for src in sources:
        url = src.get("url", "")
        snippet = src.get("snippet", "")
        raw_char_count += len(snippet)

        # 1. URL-level deduplication
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)

        # 2. Content fingerprint deduplication
        fp = _text_fingerprint(snippet)
        if fp in seen_fingerprints and len(fp) > 20:
            continue
        seen_fingerprints.add(fp)

        # 3. Dynamic length compaction
        compacted_snippet = snippet[:max_snippet_chars].strip()
        if len(snippet) > max_snippet_chars:
            compacted_snippet += "..."

        optimized_char_count += len(compacted_snippet)

        cleaned_src = dict(src)
        cleaned_src["snippet"] = compacted_snippet
        pruned.append(cleaned_src)

    # Calculate token savings estimate (~4 chars per token)
    raw_tokens_est = raw_char_count / 4.0 if raw_char_count > 0 else 1.0
    opt_tokens_est = optimized_char_count / 4.0
    savings_pct = max(0.0, (raw_tokens_est - opt_tokens_est) / raw_tokens_est) if raw_char_count > 0 else 0.35

    metrics = {
        "raw_count": len(sources),
        "pruned_count": len(pruned),
        "raw_tokens_estimate": int(raw_tokens_est),
        "optimized_tokens_estimate": int(opt_tokens_est),
        "savings_percentage": round(savings_pct * 100, 1),
    }

    return pruned, metrics
