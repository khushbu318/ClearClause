"""LangGraph node and handler for grounded Q&A over document context."""

from typing import Any

from pydantic import BaseModel, Field

from backend.integrations.llm_client import LLMClient, LLMError
from backend.prompts.answer_question import (
    ANSWER_QUESTION_SYSTEM_PROMPT,
    ANSWER_QUESTION_USER_PROMPT,
)
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class QAAnswerOutput(BaseModel):
    answer: str = Field(description="Direct plain-language answer grounded strictly in document text")
    citation: str = Field(description="Page or section citation for the answer")
    grounded: bool = Field(default=True, description="Whether the answer was found in document context")


def answer_document_question(
    question: str,
    analysis_state: dict[str, Any],
    llm_client: LLMClient | None = None,
) -> dict[str, Any]:
    """Answer a user question grounded in the ingested document context."""
    logger.info(f"Executing Q&A handler [question='{question[:60]}...']")
    if llm_client is None:
        llm_client = LLMClient()

    page_index = analysis_state.get("page_index") or {}
    parsed_doc = analysis_state.get("parsed_document") or {}
    clause_cards = analysis_state.get("clause_cards") or []

    context_parts = []
    if page_index:
        for p, text in sorted(page_index.items()):
            context_parts.append(f"[Page {p}]\n{text}")
    elif parsed_doc.get("raw_text"):
        context_parts.append(parsed_doc["raw_text"])

    for card in clause_cards:
        context_parts.append(
            f"[{card.get('priority')} Priority - {card.get('section_reference')}] {card.get('title')}: {card.get('plain_meaning')}\nVerbatim: {card.get('original_text')}"
        )

    full_context = "\n\n---\n\n".join(context_parts)
    if len(full_context) > 40000:
        full_context = full_context[:40000] + "\n...[truncated for length]"

    logger.info(f"Q&A context prepared [chars={len(full_context)}]")

    user_prompt = ANSWER_QUESTION_USER_PROMPT.format(
        context_text=full_context,
        question=question,
    )

    try:
        res = llm_client.complete(
            system_prompt=ANSWER_QUESTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=QAAnswerOutput,
        )
        logger.info(f"Q&A completion succeeded [citation='{res.get('citation')}', grounded={res.get('grounded')}]")
        return {
            "answer": res.get("answer", "Answer could not be generated."),
            "citation": res.get("citation", "Document"),
            "grounded": res.get("grounded", True),
        }
    except LLMError as err:
        logger.warning(f"Q&A LLM completion failed: {err}. Using text match fallback.")
        q_words = set(w.lower() for w in question.split() if len(w) > 3)
        matches = []
        for card in clause_cards:
            text_pool = f"{card.get('title')} {card.get('plain_meaning')} {card.get('original_text')}".lower()
            if any(w in text_pool for w in q_words):
                matches.append(card)

        if matches:
            best = matches[0]
            logger.info(f"Q&A fallback matched card [{best.get('title')}]")
            return {
                "answer": f"Based on **{best.get('title')}** ({best.get('section_reference')}):\n\n{best.get('plain_meaning')}\n\n*Original text:* \"{best.get('original_text')}\"",
                "citation": f"{best.get('title')} ({best.get('section_reference')})",
                "grounded": True,
            }

        logger.info("Q&A fallback found no matching cards")
        return {
            "answer": "This detail does not appear to be explicitly addressed in the extracted document sections.",
            "citation": "Not covered in document context",
            "grounded": False,
        }
