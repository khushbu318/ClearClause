"""
backend/agents/input_router.py
LangGraph conditional-edge routing function — decides which ingest node to run.
"""

from backend.models.graph_state import AnalysisGraphState
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


def route_input(state: AnalysisGraphState) -> str:
    """Return the name of the next node based on input_type."""
    input_type = state.get("input_type")
    logger.info(f"InputRouter evaluating routing [input_type={input_type}]")
    if input_type == "pdf":
        target = "pdf_ingest"
    elif input_type == "url":
        target = "url_ingest"
    elif input_type == "text":
        target = "text_ingest"
    else:
        logger.warning(f"Unknown input_type '{input_type}', defaulting to text_ingest")
        target = "text_ingest"

    logger.info(f"InputRouter routing to node [{target}]")
    return target
