"""
tests/unit/test_embedding_client.py
Unit tests for backend/integrations/embedding_client.py

All SentenceTransformer calls are mocked — no model download needed in CI.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def _make_mock_model(n_texts: int, d: int = 384):
    """Return a mock SentenceTransformer that produces (n_texts, d) float32 vectors."""
    mock_model = MagicMock()
    vectors = np.random.default_rng(0).random((n_texts, d)).astype(np.float32)
    mock_model.encode.return_value = vectors
    return mock_model


class TestEmbedClient:
    def _patched_embed(self, texts: list[str]):
        """Run embed() with a mocked SentenceTransformer."""
        import backend.integrations.embedding_client as ec
        mock_model = _make_mock_model(len(texts))
        with patch.object(ec, "_model", mock_model):
            return ec.embed(texts)

    def test_embed_returns_correct_shape(self):
        texts = ["Clause one about rent.", "Clause two about termination."]
        result = self._patched_embed(texts)
        assert result.shape == (2, 384)

    def test_embed_returns_float32(self):
        texts = ["Single clause."]
        result = self._patched_embed(texts)
        assert result.dtype == np.float32

    def test_embed_empty_list_raises_embedding_error(self):
        import backend.integrations.embedding_client as ec
        with pytest.raises(ec.EmbeddingError):
            ec.embed([])

    def test_embed_single_returns_shape_1_d(self):
        import backend.integrations.embedding_client as ec
        mock_model = _make_mock_model(1)
        with patch.object(ec, "_model", mock_model):
            result = ec.embed_single("A single clause.")
        assert result.shape == (1, 384)

    def test_embed_model_exception_raises_embedding_error(self):
        import backend.integrations.embedding_client as ec
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("GPU OOM")
        with patch.object(ec, "_model", mock_model):
            with pytest.raises(ec.EmbeddingError, match="GPU OOM"):
                ec.embed(["some text"])
