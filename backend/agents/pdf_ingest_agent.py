"""
backend/agents/pdf_ingest_agent.py
LangGraph node — ingests a PDF and builds a vectorless page-tree index.

Writes to state:
    parsed_document  — ParsedDocument.model_dump()
    page_index       — {page_num: page_text}
    error            — set on failure
"""

from backend.models.graph_state import AnalysisGraphState
from backend.integrations.document_parser import (
    parse_pdf,
    DocumentParserError,
)


def pdf_ingest_agent(state: AnalysisGraphState) -> dict:
    """Parse the uploaded PDF and build the page-tree index."""
    raw_input = state.get("raw_input")
    filename = "uploaded.pdf"

    # Try to extract a filename if the caller passed metadata
    if isinstance(raw_input, bytes):
        file_bytes = raw_input
    else:
        return {"error": "PDF ingest received non-bytes input."}

    try:
        parsed_doc, page_index = parse_pdf(file_bytes, filename=filename)
    except DocumentParserError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Unexpected error during PDF parsing: {exc}"}

    return {
        "parsed_document": parsed_doc.model_dump(),
        "page_index": page_index,
        "error": None,
        "degraded_clause_ids": [],
        "extraction_attempts": 0,
    }
