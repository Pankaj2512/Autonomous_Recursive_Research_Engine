"""ChromaDB and In-Memory Vector Store for semantic research document retrieval."""
from __future__ import annotations

import logging
import math
import re
import uuid
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text for vector embedding calculations."""
    return re.findall(r"\b\w{2,}\b", text.lower())


def _cosine_similarity(vec_a: Counter[str], vec_b: Counter[str]) -> float:
    """Compute cosine similarity between two term-frequency vector representations."""
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    dot_product = sum(vec_a[x] * vec_b[x] for x in intersection)

    norm_a = math.sqrt(sum(val ** 2 for val in vec_a.values()))
    norm_b = math.sqrt(sum(val ** 2 for val in vec_b.values()))

    if not norm_a or not norm_b:
        return 0.0

    return dot_product / (norm_a * norm_b)


class VectorMemoryStore:
    """Hybrid Vector Store with ChromaDB backend and native in-memory semantic fallback."""

    def __init__(self, collection_name: str = "research_context") -> None:
        self.collection_name = collection_name
        self._chroma_client = None
        self._collection = None
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._vectors: Dict[str, Counter[str]] = {}
        self._init_chromadb()

    def _init_chromadb(self) -> None:
        """Attempt initialization of persistent/in-memory ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._chroma_client = chromadb.Client(
                ChromaSettings(anonymized_telemetry=False, is_persistent=False)
            )
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            logger.info("ChromaDB vector collection initialized successfully.")
        except Exception as exc:
            logger.info(f"ChromaDB not available ({exc}). Using native in-memory vector index.")
            self._chroma_client = None
            self._collection = None

    def add_document(
        self,
        text: str,
        title: str = "",
        url: str = "",
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Index a document into the vector store."""
        uid = doc_id or str(uuid.uuid4())[:8]
        meta = metadata or {}
        meta.update({"title": title, "url": url})

        if self._collection is not None:
            try:
                self._collection.upsert(
                    ids=[uid],
                    documents=[text],
                    metadatas=[meta],
                )
            except Exception as exc:
                logger.warning(f"ChromaDB upsert failed: {exc}. Indexing in memory.")

        # Always maintain in-memory representation for guaranteed resilience
        self._documents[uid] = {
            "id": uid,
            "text": text,
            "title": title,
            "url": url,
            "metadata": meta,
        }
        self._vectors[uid] = Counter(_tokenize(text))
        return uid

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Perform semantic vector similarity search."""
        if not query.strip() or not self._documents:
            return []

        # 1. Try ChromaDB semantic search if available
        if self._collection is not None and self._collection.count() > 0:
            try:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(top_k, self._collection.count()),
                )
                hits = []
                ids = results.get("ids", [[]])[0]
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0] if "distances" in results else []

                for i in range(len(ids)):
                    dist = distances[i] if i < len(distances) else 0.2
                    score = round(max(0.0, 1.0 - float(dist)), 3)
                    meta_item = metas[i] if i < len(metas) else {}
                    hits.append({
                        "id": ids[i],
                        "text": docs[i],
                        "title": meta_item.get("title", "Untitled Source"),
                        "url": meta_item.get("url", ""),
                        "score": score,
                    })
                return hits
            except Exception as exc:
                logger.warning(f"ChromaDB query failed: {exc}. Falling back to in-memory cosine search.")

        # 2. In-memory cosine similarity ranking
        query_vec = Counter(_tokenize(query))
        scored = []
        for uid, doc in self._documents.items():
            sim = _cosine_similarity(query_vec, self._vectors[uid])
            scored.append((sim, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = []
        for sim, doc in scored[:top_k]:
            top_matches.append({
                "id": doc["id"],
                "text": doc["text"],
                "title": doc["title"],
                "url": doc["url"],
                "score": round(float(sim), 3),
            })
        return top_matches

    def count(self) -> int:
        """Return total number of indexed passages."""
        return len(self._documents)

    def clear(self) -> None:
        """Clear indexed vectors and documents."""
        self._documents.clear()
        self._vectors.clear()
        if self._collection is not None:
            try:
                self._chroma_client.delete_collection(self.collection_name)
                self._collection = self._chroma_client.create_collection(self.collection_name)
            except Exception:
                pass


# Singleton Vector Store instance
_global_vector_store: Optional[VectorMemoryStore] = None


def get_vector_store() -> VectorMemoryStore:
    """Retrieve or initialize singleton VectorMemoryStore."""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorMemoryStore()
    return _global_vector_store


def search_vector_store(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """Helper function to execute vector search across the singleton store."""
    return get_vector_store().search(query=query, top_k=top_k)


def index_document(text: str, title: str = "", url: str = "", doc_id: str = "") -> Dict[str, Any]:
    """Helper function to index a passage into the vector store."""
    uid = get_vector_store().add_document(text=text, title=title, url=url, doc_id=doc_id or None)
    return {"status": "indexed", "id": uid, "total_documents": get_vector_store().count()}
