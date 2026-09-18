"""Service layer for document analysis orchestrating graph execution."""

import time
from typing import Literal

from backend.graphs.analysis_graph import build_analysis_graph
from backend.integrations.llm_client import LLMClient
from backend.models.graph_state import AnalysisGraphState
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentAnalysisService:
    """Service to execute the document analysis LangGraph pipeline."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client
        self.graph = build_analysis_graph(llm_client=self.llm_client)

    def analyze(
        self,
        raw_input: bytes | str,
        input_type: Literal["pdf", "url", "text"],
        document_context: str | None = None,
    ) -> AnalysisGraphState:
        """Run the analysis graph for a given input."""
        start_time = time.time()
        input_len = len(raw_input) if isinstance(raw_input, (bytes, str)) else 0
        logger.info(
            f"Starting document analysis pipeline [input_type={input_type}, size={input_len}, context='{document_context}']"
        )

        initial_state: AnalysisGraphState = {
            "input_type": input_type,
            "raw_input": raw_input,
            "document_context": document_context,
            "parsed_document": None,
            "page_index": None,
            "faiss_index_bytes": None,
            "chunks": None,
            "raw_clauses": None,
            "extraction_attempts": 0,
            "clause_cards": None,
            "analysis": None,
            "error": None,
            "degraded_clauses": [],
        }

        try:
            final_state = self.graph.invoke(initial_state)
            elapsed = time.time() - start_time
            if final_state.get("error"):
                logger.error(
                    f"Document analysis pipeline failed [elapsed={elapsed:.2f}s, error='{final_state['error']}']"
                )
            else:
                cards_count = len(final_state.get("clause_cards") or [])
                logger.info(
                    f"Document analysis pipeline completed successfully [elapsed={elapsed:.2f}s, cards_count={cards_count}]"
                )
            return final_state
        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error(f"Error executing analysis graph [elapsed={elapsed:.2f}s]: {exc}")
            initial_state["error"] = f"Failed to complete document analysis: {str(exc)}"
            return initial_state


def analyze_document(
    raw_input: bytes | str,
    input_type: Literal["pdf", "url", "text"],
    document_context: str | None = None,
    llm_client: LLMClient | None = None,
) -> AnalysisGraphState:
    """Helper function to create service and run analysis."""
    service = DocumentAnalysisService(llm_client=llm_client)
    return service.analyze(
        raw_input=raw_input,
        input_type=input_type,
        document_context=document_context,
    )
