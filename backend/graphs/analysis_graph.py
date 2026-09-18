"""LangGraph StateGraph definition for single document analysis pipeline."""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.card_builder_agent import card_builder_node
from backend.agents.clause_extract_agent import clause_extract_node
from backend.agents.input_router import route_input
from backend.agents.pdf_ingest_agent import pdf_ingest_agent
from backend.agents.summary_agent import summary_node
from backend.agents.text_ingest_agent import text_ingest_agent
from backend.agents.url_ingest_agent import url_ingest_agent
from backend.integrations.llm_client import LLMClient
from backend.models.graph_state import AnalysisGraphState

logger = logging.getLogger(__name__)


def build_analysis_graph(llm_client: LLMClient | None = None):
    """Construct and compile the LangGraph StateGraph for document analysis."""

    builder = StateGraph(AnalysisGraphState)

    # Define Node functions wrapped with optional LLM injection
    def pdf_node_fn(state: AnalysisGraphState) -> dict[str, Any]:
        return pdf_ingest_agent(state)

    def url_node_fn(state: AnalysisGraphState) -> dict[str, Any]:
        return url_ingest_agent(state)

    def text_node_fn(state: AnalysisGraphState) -> dict[str, Any]:
        return text_ingest_agent(state)

    def clause_extract_fn(state: AnalysisGraphState) -> dict[str, Any]:
        return clause_extract_node(state, llm_client=llm_client)

    def card_builder_fn(state: AnalysisGraphState) -> dict[str, Any]:
        return card_builder_node(state, llm_client=llm_client)

    def summary_fn(state: AnalysisGraphState) -> dict[str, Any]:
        return summary_node(state, llm_client=llm_client)

    # Add Nodes
    builder.add_node("pdf_ingest", pdf_node_fn)
    builder.add_node("url_ingest", url_node_fn)
    builder.add_node("text_ingest", text_node_fn)
    builder.add_node("extract_clauses", clause_extract_fn)
    builder.add_node("build_cards", card_builder_fn)
    builder.add_node("summarize", summary_fn)

    # Conditional router from START
    builder.add_conditional_edges(
        START,
        route_input,
        {
            "pdf_ingest": "pdf_ingest",
            "url_ingest": "url_ingest",
            "text_ingest": "text_ingest",
        },
    )

    # Edges from ingestion to clause extraction
    builder.add_edge("pdf_ingest", "extract_clauses")
    builder.add_edge("url_ingest", "extract_clauses")
    builder.add_edge("text_ingest", "extract_clauses")

    # Linear edges for extraction -> cards -> summary -> END
    builder.add_edge("extract_clauses", "build_cards")
    builder.add_edge("build_cards", "summarize")
    builder.add_edge("summarize", END)

    return builder.compile()
