"""
backend/integrations/embedding_client.py
Data Access Layer — HuggingFace sentence-transformers embedding wrapper.

Uses all-MiniLM-L6-v2 (~90 MB, CPU-only, no API key needed).
The model is loaded once and cached at module level to avoid re-downloading
on every call within the same Streamlit session.
"""

from __future__ import annotations

import numpy as np

_model = None  # module-level cache


def _get_model():
    """Load the embedding model once; return the cached instance thereafter."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required: pip install sentence-transformers"
            ) from exc
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


class EmbeddingError(Exception):
    """Raised when embedding fails."""


def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed a list of text strings into float32 vectors.

    Args:
        texts: List of strings to embed. Must be non-empty.
        batch_size: Number of texts to encode per forward pass.

    Returns:
        np.ndarray of shape (len(texts), 384), dtype float32.
        384 is the output dimension of all-MiniLM-L6-v2.

    Raises:
        EmbeddingError: if texts is empty or model inference fails.
    """
    if not texts:
        raise EmbeddingError("Cannot embed an empty list of texts.")

    try:
        model = _get_model()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,  # unit-norm → cosine sim = dot product
            show_progress_bar=False,
        )
        return vectors.astype(np.float32)
    except Exception as exc:
        raise EmbeddingError(f"Embedding failed: {exc}") from exc


def embed_single(text: str) -> np.ndarray:
    """Convenience wrapper — embed a single string, return shape (1, 384)."""
    return embed([text])
