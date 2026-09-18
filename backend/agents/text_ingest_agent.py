"""
backend/agents/text_ingest_agent.py
LangGraph node — chunks pasted text, embeds chunks, builds FAISS index.
"""

from backend.integrations import embedding_client
from backend.integrations.document_parser import DocumentParserError, parse_text
from backend.integrations.embedding_client import EmbeddingError
from backend.integrations.faiss_store import FAISSStore, IndexBuildError, chunk_text
from backend.models.graph_state import AnalysisGraphState
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def text_ingest_agent(state: AnalysisGraphState) -> dict:
    """Chunk pasted text → embed → FAISS index."""
    raw_input = state.get("raw_input")
    logger.info("Executing Text ingest node...")

    if not isinstance(raw_input, str) or not raw_input.strip():
        logger.error("Text ingest received empty or non-string input")
        return {"error": "Text ingest received empty or non-string input."}

    try:
        parsed_doc = parse_text(raw_input)
    except DocumentParserError as exc:
        logger.warning(f"Pasted text validation failed: {exc}")
        return {"error": str(exc)}

    chunks = chunk_text(parsed_doc.raw_text)
    if not chunks:
        logger.warning("No chunks produced from pasted text")
        return {"error": "No text chunks could be produced from the pasted text."}

    try:
        vectors = embedding_client.embed(chunks)
    except EmbeddingError as exc:
        logger.error(f"Embedding failed for pasted text chunks: {exc}")
        return {"error": f"Embedding failed: {exc}"}

    try:
        store = FAISSStore.build(vectors)
        index_bytes = store.serialize()
        logger.info(f"Text ingest completed successfully [chunks={len(chunks)}]")
    except IndexBuildError as exc:
        logger.error(f"FAISS index build failed for pasted text chunks: {exc}")
        return {"error": f"FAISS index build failed: {exc}"}

    return {
        "parsed_document": parsed_doc.model_dump(),
        "chunks": chunks,
        "faiss_index_bytes": index_bytes,
        "error": None,
        "degraded_clause_ids": [],
        "extraction_attempts": 0,
    }
