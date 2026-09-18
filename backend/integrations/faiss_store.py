"""
backend/integrations/faiss_store.py
Data Access Layer — session-scoped FAISS vector index builder and searcher.
"""

from __future__ import annotations

import re

import numpy as np

from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class IndexBuildError(Exception):
    """Raised when FAISS index construction fails."""


class FAISSStore:
    """Thin wrapper around a FAISS IndexFlatL2."""

    def __init__(self, index, dimension: int, total_vectors: int):
        self._index = index
        self.dimension = dimension
        self.total_vectors = total_vectors

    @classmethod
    def build(cls, vectors: np.ndarray) -> FAISSStore:
        """Build an IndexFlatL2 from a float32 vector matrix."""
        logger.info(f"Building FAISS index [shape={vectors.shape}]")
        try:
            import faiss
        except ImportError as exc:
            logger.error("faiss-cpu import failed")
            raise ImportError(
                "faiss-cpu is required: pip install faiss-cpu"
            ) from exc

        if vectors.ndim != 2:
            raise IndexBuildError(f"Expected 2D vector array, got shape {vectors.shape}.")
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)

        n, d = vectors.shape
        if n == 0:
            raise IndexBuildError("Cannot build a FAISS index from zero vectors.")

        try:
            index = faiss.IndexFlatL2(d)
            index.add(vectors)  # type: ignore[attr-defined]
            logger.info(f"FAISS index built successfully [ntotal={n}, d={d}]")
        except Exception as exc:
            logger.error(f"FAISS index construction failed: {exc}")
            raise IndexBuildError(f"FAISS index construction failed: {exc}") from exc

        return cls(index=index, dimension=d, total_vectors=n)

    def search(self, query_vector: np.ndarray, k: int = 5) -> list[int]:
        """Return indices of the k nearest chunks to the query vector."""
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        k_actual = min(k, self.total_vectors)
        logger.info(f"FAISS search [k_requested={k}, k_actual={k_actual}, total_vectors={self.total_vectors}]")
        _, indices = self._index.search(query_vector, k_actual)  # type: ignore[attr-defined]
        results = [int(i) for i in indices[0] if i >= 0]
        logger.info(f"FAISS search completed [found_indices={results}]")
        return results

    def serialize(self) -> bytes:
        """Serialize the FAISS index to bytes for session_state storage."""
        try:
            import faiss
            data = faiss.serialize_index(self._index)
            logger.info(f"FAISS index serialized [size_bytes={len(data)}]")
            return data
        except Exception as exc:
            logger.error(f"FAISS serialization failed: {exc}")
            raise IndexBuildError(f"FAISS serialization failed: {exc}") from exc

    @classmethod
    def deserialize(cls, data: bytes) -> FAISSStore:
        """Restore a FAISSStore from serialized bytes."""
        try:
            import faiss
            index = faiss.deserialize_index(data)
            logger.info(f"FAISS index deserialized [ntotal={index.ntotal}, d={index.d}]")
        except Exception as exc:
            logger.error(f"FAISS deserialization failed: {exc}")
            raise IndexBuildError(f"FAISS deserialization failed: {exc}") from exc

        return cls(
            index=index,
            dimension=index.d,
            total_vectors=index.ntotal,
        )


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[str]:
    """Split text into overlapping token-approximate chunks."""
    logger.info(f"Chunking text [char_count={len(text)}, target_chunk_size={chunk_size}, overlap={overlap}]")
    chunk_words = int(chunk_size * 0.75)
    overlap_words = int(overlap * 0.75)

    sentence_pattern = re.compile(r"(?<=[.!?])\s+")
    sentences = sentence_pattern.split(text.strip())

    words: list[str] = []
    for sentence in sentences:
        words.extend(sentence.split())

    if not words:
        logger.warning("chunk_text produced 0 words from input text")
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_words, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end == len(words):
            break
        start = end - overlap_words

    logger.info(f"Chunking completed [produced_chunks={len(chunks)}]")
    return chunks
