"""
backend/agents/pdf_ingest_agent.py
LangGraph node — ingests a PDF and builds a vectorless page-tree index.
"""

from backend.integrations.document_parser import (
    DocumentParserError,
    parse_pdf,
)
from backend.models.graph_state import AnalysisGraphState
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def pdf_ingest_agent(state: AnalysisGraphState) -> dict:
    """Parse the uploaded PDF and build the page-tree index."""
    raw_input = state.get("raw_input")
    filename = "uploaded.pdf"

    logger.info("Executing PDF ingest node...")
    if isinstance(raw_input, bytes):
        file_bytes = raw_input
    else:
        logger.error("PDF ingest node received non-bytes input")
        return {"error": "PDF ingest received non-bytes input."}

    try:
        parsed_doc, page_index = parse_pdf(file_bytes, filename=filename)
        logger.info(
            f"PDF ingest node completed successfully [pages={len(page_index)}, char_count={parsed_doc.char_count}]"
        )
    except DocumentParserError as exc:
        logger.warning(f"PDF ingest failed with parser error: {exc}")
        return {"error": str(exc)}
    except Exception as exc:
        logger.error(f"Unexpected error during PDF ingestion: {exc}")
        return {"error": f"Unexpected error during PDF parsing: {exc}"}

    return {
        "parsed_document": parsed_doc.model_dump(),
        "page_index": page_index,
        "error": None,
        "degraded_clause_ids": [],
        "extraction_attempts": 0,
    }
