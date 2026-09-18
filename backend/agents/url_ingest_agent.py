"""
backend/agents/url_ingest_agent.py
LangGraph node — scrapes a URL, chunks the text, embeds chunks, builds FAISS index.
"""

from backend.integrations import embedding_client
from backend.integrations.document_parser import DocumentParserError, parse_url
from backend.integrations.embedding_client import EmbeddingError
from backend.integrations.faiss_store import FAISSStore, IndexBuildError, chunk_text
from backend.models.graph_state import AnalysisGraphState
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def url_ingest_agent(state: AnalysisGraphState) -> dict:
    """Scrape URL → chunk → embed → FAISS index."""
    raw_input = state.get("raw_input")
    logger.info("Executing URL ingest node...")

    if not isinstance(raw_input, str) or not raw_input.strip():
        logger.error("URL ingest received empty or non-string input")
        return {"error": "URL ingest received an empty or non-string URL."}

    url = raw_input.strip()

    try:
        parsed_doc = parse_url(url)
    except DocumentParserError as exc:
        logger.warning(f"URL parsing failed: {exc}")
        return {"error": str(exc)}
    except Exception as exc:
        logger.error(f"Unexpected error fetching URL '{url}': {exc}")
        return {"error": f"Unexpected error fetching URL: {exc}"}

    chunks = chunk_text(parsed_doc.raw_text)
    if not chunks:
        logger.warning(f"No chunks produced for URL '{url}'")
        return {"error": "No text chunks could be produced from the fetched URL content."}

    try:
        vectors = embedding_client.embed(chunks)
    except EmbeddingError as exc:
        logger.error(f"Embedding failed for URL chunks: {exc}")
        return {"error": f"Embedding failed: {exc}"}

    try:
        store = FAISSStore.build(vectors)
        index_bytes = store.serialize()
        logger.info(f"URL ingest completed successfully [url={url}, chunks={len(chunks)}]")
    except IndexBuildError as exc:
        logger.error(f"FAISS index build failed for URL chunks: {exc}")
        return {"error": f"FAISS index build failed: {exc}"}

    return {
        "parsed_document": parsed_doc.model_dump(),
        "chunks": chunks,
        "faiss_index_bytes": index_bytes,
        "error": None,
        "degraded_clause_ids": [],
        "extraction_attempts": 0,
    }
