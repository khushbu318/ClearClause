"""
backend/agents/input_router.py
LangGraph conditional-edge routing function — decides which ingest node to run
based on the `input_type` field in AnalysisGraphState.

Not a full agent node — used as the `route` argument to add_conditional_edges().
"""

from backend.models.graph_state import AnalysisGraphState


def route_input(state: AnalysisGraphState) -> str:
    """Return the name of the next node based on input_type.

    Used as:
        graph.add_conditional_edges("__start__", route_input, {
            "pdf_ingest": "pdf_ingest",
            "url_ingest": "url_ingest",
            "text_ingest": "text_ingest",
        })
    """
    input_type = state.get("input_type")
    if input_type == "pdf":
        return "pdf_ingest"
    elif input_type == "url":
        return "url_ingest"
    elif input_type == "text":
        return "text_ingest"
    else:
        # Fallback — propagate error to next node which will check state["error"]
        return "text_ingest"
