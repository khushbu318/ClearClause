"""
backend/integrations/faiss_store.py
Data Access Layer — session-scoped FAISS vector index builder and searcher.

Design:
- Indexes are NEVER written to disk; they are serialized to bytes and stored
  in Streamlit session_state, satisfying the no-persistence requirement.
- Uses IndexFlatL2 (exact search) — sufficient for the small chunk counts
  typical of a single legal document (~50–200 chunks).
- All-MiniLM-L6-v2 vectors are L2-normalized so IndexFlatL2 with normalized
  vectors is equivalent to maximum cosine similarity search.
"""

from __future__ import annotations

import numpy as np


class IndexBuildError(Exception):
    """Raised when FAISS index construction fails."""


class FAISSStore:
    """Thin wrapper around a FAISS IndexFlatL2.

    Usage (URL/text ingest path):
        vectors = embedding_client.embed(chunks)
        store = FAISSStore.build(vectors)
        index_bytes = store.serialize()               # → store in session_state
        ...
        store = FAISSStore.deserialize(index_bytes)   # → restore from session_state
        indices = store.search(query_vector, k=5)     # → chunk indices
    """

    def __init__(self, index, dimension: int, total_vectors: int):
        self._index = index
        self.dimension = dimension
        self.total_vectors = total_vectors

    # ── Construction ───────────────────────────────────────────────────────────

    @classmethod
    def build(cls, vectors: np.ndarray) -> "FAISSStore":
        """Build an IndexFlatL2 from a float32 vector matrix.

        Args:
            vectors: shape (n, d), dtype float32.  n >= 1.

        Returns:
            FAISSStore wrapping the built index.

        Raises:
            IndexBuildError: if faiss is not installed or construction fails.
        """
        try:
            import faiss
        except ImportError as exc:
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
        except Exception as exc:
            raise IndexBuildError(f"FAISS index construction failed: {exc}") from exc

        return cls(index=index, dimension=d, total_vectors=n)

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(self, query_vector: np.ndarray, k: int = 5) -> list[int]:
        """Return indices of the k nearest chunks to the query vector.

        Args:
            query_vector: shape (1, d) or (d,), dtype float32.
            k: number of nearest neighbours to return.

        Returns:
            List of integer chunk indices (into the original chunks list),
            ordered nearest-first. Length <= k (may be fewer if index is small).
        """
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        k_actual = min(k, self.total_vectors)
        _, indices = self._index.search(query_vector, k_actual)  # type: ignore[attr-defined]
        # indices is shape (1, k_actual); flatten and filter sentinel -1s
        return [int(i) for i in indices[0] if i >= 0]

    # ── Serialization ──────────────────────────────────────────────────────────

    def serialize(self) -> bytes:
        """Serialize the FAISS index to bytes for session_state storage."""
        try:
            import faiss
            return faiss.serialize_index(self._index)
        except Exception as exc:
            raise IndexBuildError(f"FAISS serialization failed: {exc}") from exc

    @classmethod
    def deserialize(cls, data: bytes) -> "FAISSStore":
        """Restore a FAISSStore from serialized bytes.

        Args:
            data: bytes produced by serialize().

        Returns:
            FAISSStore ready for search.
        """
        try:
            import faiss
            index = faiss.deserialize_index(data)
        except Exception as exc:
            raise IndexBuildError(f"FAISS deserialization failed: {exc}") from exc

        return cls(
            index=index,
            dimension=index.d,
            total_vectors=index.ntotal,
        )


# ── Text chunker (shared by URL and text ingest agents) ───────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[str]:
    """Split text into overlapping token-approximate chunks.

    Uses a word-count proxy for token size (1 token ≈ 0.75 words).
    Splits on sentence boundaries when possible; falls back to word boundaries.

    Args:
        text: Full document text.
        chunk_size: Target chunk size in approximate tokens.
        overlap: Overlap between consecutive chunks in approximate tokens.

    Returns:
        List of non-empty string chunks, each roughly chunk_size tokens.
    """
    import re

    # Convert token targets to word counts (rough approximation)
    chunk_words = int(chunk_size * 0.75)
    overlap_words = int(overlap * 0.75)

    # Split into sentences first for cleaner boundaries
    sentence_pattern = re.compile(r"(?<=[.!?])\s+")
    sentences = sentence_pattern.split(text.strip())

    words: list[str] = []
    for sentence in sentences:
        words.extend(sentence.split())

    if not words:
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
        start = end - overlap_words  # back up for overlap

    return chunks
