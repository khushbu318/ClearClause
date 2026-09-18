"""
backend/integrations/embedding_client.py
Data Access Layer — HuggingFace sentence-transformers embedding wrapper.

Uses all-MiniLM-L6-v2 (~90 MB, CPU-only, no API key needed).
"""

from __future__ import annotations

import time

import numpy as np

from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

_model = None  # module-level cache


def _get_model():
    """Load the embedding model once; return the cached instance thereafter."""
    global _model
    if _model is None:
        logger.info("Loading HuggingFace sentence-transformers model [all-MiniLM-L6-v2]...")
        start_t = time.time()
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            logger.error("sentence-transformers import failed")
            raise ImportError(
                "sentence-transformers is required: pip install sentence-transformers"
            ) from exc
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info(f"Model all-MiniLM-L6-v2 loaded in {time.time() - start_t:.2f}s")
    return _model


class EmbeddingError(Exception):
    """Raised when embedding fails."""


def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed a list of text strings into float32 vectors."""
    if not texts:
        logger.warning("embed() called with an empty list of texts")
        raise EmbeddingError("Cannot embed an empty list of texts.")

    logger.info(f"Embedding texts [count={len(texts)}, batch_size={batch_size}]")
    start_t = time.time()
    try:
        model = _get_model()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,  # unit-norm → cosine sim = dot product
            show_progress_bar=False,
        )
        res = vectors.astype(np.float32)
        logger.info(f"Embedding completed [shape={res.shape}, elapsed={time.time() - start_t:.2f}s]")
        return res
    except Exception as exc:
        logger.error(f"Embedding inference failed: {exc}")
        raise EmbeddingError(f"Embedding failed: {exc}") from exc


def embed_single(text: str) -> np.ndarray:
    """Convenience wrapper — embed a single string, return shape (1, 384)."""
    return embed([text])
