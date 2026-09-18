"""
backend/agents/url_ingest_agent.py
LangGraph node — scrapes a URL, chunks the text, embeds chunks, builds FAISS index.

Writes to state:
    parsed_document    — ParsedDocument.model_dump()
    chunks             — list[str] of text chunks
    faiss_index_bytes  — serialized FAISS index bytes
    error              — set on failure
"""

from backend.models.graph_state import AnalysisGraphState
from backend.integrations.document_parser import parse_url, DocumentParserError
from backend.integrations.faiss_store import FAISSStore, chunk_text
from backend.integrations import embedding_client
from backend.integrations.embedding_client import EmbeddingError
from backend.integrations.faiss_store import IndexBuildError


def url_ingest_agent(state: AnalysisGraphState) -> dict:
    """Scrape URL → chunk → embed → FAISS index."""
    raw_input = state.get("raw_input")

    if not isinstance(raw_input, str) or not raw_input.strip():
        return {"error": "URL ingest received an empty or non-string URL."}

    url = raw_input.strip()

    # 1. Scrape and parse
    try:
        parsed_doc = parse_url(url)
    except DocumentParserError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error fetching URL: {exc}"}

    # 2. Chunk
    chunks = chunk_text(parsed_doc.raw_text)
    if not chunks:
        return {"error": "No text chunks could be produced from the fetched URL content."}

    # 3. Embed
    try:
        vectors = embedding_client.embed(chunks)
    except EmbeddingError as exc:
        return {"error": f"Embedding failed: {exc}"}

    # 4. Build FAISS index
    try:
        store = FAISSStore.build(vectors)
        index_bytes = store.serialize()
    except IndexBuildError as exc:
        return {"error": f"FAISS index build failed: {exc}"}

    return {
        "parsed_document": parsed_doc.model_dump(),
        "chunks": chunks,
        "faiss_index_bytes": index_bytes,
        "error": None,
        "degraded_clause_ids": [],
        "extraction_attempts": 0,
    }
