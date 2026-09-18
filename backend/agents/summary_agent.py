"""LangGraph node for generating whole-document summary and analysis."""

from typing import Any

from pydantic import BaseModel, Field

from backend.integrations.llm_client import LLMClient, LLMError
from backend.models.graph_state import AnalysisGraphState
from backend.prompts.summarize import (
    SUMMARIZE_SYSTEM_PROMPT,
    SUMMARIZE_USER_PROMPT,
)
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentSummaryOutput(BaseModel):
    document_type: str = Field(description="Detected type of document")
    parties: list[str] = Field(default_factory=list, description="Parties involved")
    summary: str = Field(description="Overall plain-language summary")
    key_obligations: list[str] = Field(default_factory=list, description="Key obligations")
    key_dates: list[str] = Field(default_factory=list, description="Key dates or timelines")
    key_financial_terms: list[str] = Field(default_factory=list, description="Key financial terms or fees")


def summary_node(state: AnalysisGraphState, llm_client: LLMClient | None = None) -> dict[str, Any]:
    """LangGraph node that produces the whole-document summary analysis."""
    clause_cards = state.get("clause_cards") or []
    document_context = state.get("document_context") or "General document review"
    logger.info(f"Executing Summary node [clause_cards_count={len(clause_cards)}]")

    if llm_client is None:
        llm_client = LLMClient()

    summaries_lines = []
    for card in clause_cards:
        line = f"- [{card.get('priority', 'Medium')}] {card.get('title')}: {card.get('plain_meaning')} ({card.get('section_reference')})"
        summaries_lines.append(line)

    clause_summaries_text = "\n".join(summaries_lines) if summaries_lines else "No specific clauses extracted."

    user_prompt = SUMMARIZE_USER_PROMPT.format(
        document_context=document_context,
        clause_summaries_text=clause_summaries_text,
    )

    try:
        res = llm_client.complete(
            system_prompt=SUMMARIZE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=DocumentSummaryOutput,
        )

        analysis_dict = {
            "document_type": res.get("document_type", "Legal Agreement"),
            "parties": res.get("parties", []),
            "summary": res.get("summary", "Document analyzed."),
            "key_obligations": res.get("key_obligations", []),
            "key_dates": res.get("key_dates", []),
            "key_financial_terms": res.get("key_financial_terms", []),
            "clause_cards": clause_cards,
        }
        logger.info(
            f"Summary node completed successfully [doc_type={analysis_dict['document_type']}, parties={analysis_dict['parties']}]"
        )
    except LLMError as err:
        logger.warning(f"Failed whole-document summarization: {err}")
        analysis_dict = {
            "document_type": "Legal Document",
            "parties": [],
            "summary": "Document successfully ingested and parsed into clause breakdown.",
            "key_obligations": ["Review individual clause cards for detailed obligations."],
            "key_dates": [],
            "key_financial_terms": [],
            "clause_cards": clause_cards,
        }

    return {"analysis": analysis_dict}
