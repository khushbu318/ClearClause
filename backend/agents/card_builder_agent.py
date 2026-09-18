"""LangGraph node for building synthesized ClauseCards from raw extracted clauses in batch."""

import json
from typing import Any

from pydantic import BaseModel, Field

from backend.integrations.llm_client import LLMClient, LLMError
from backend.models.clause import PriorityLevel
from backend.models.graph_state import AnalysisGraphState
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class CardItemOutput(BaseModel):
    id: str = Field(description="Matching clause ID (e.g. clause-1)")
    title: str = Field(description="Short, plain-English headline for the clause")
    plain_meaning: str = Field(description="Single clear sentence explaining practical meaning")
    priority: PriorityLevel = Field(description="Urgency priority level: High, Medium, Low, FYI")
    questions_to_ask: list[str] = Field(default_factory=list, description="2-4 concrete questions to ask")


class BatchCardSynthesisOutput(BaseModel):
    cards: list[CardItemOutput] = Field(default_factory=list)


BATCH_CARD_SYSTEM_PROMPT = """You are a legal clarity assistant synthesizing clear, actionable Clause Cards for a layperson.

For EACH extracted clause provided in the input JSON array:
1. `title`: Short, punchy plain-English headline (3-6 words, e.g. "Early Termination Penalty" or "IP & Invention Assignment").
2. `plain_meaning`: EXACTLY one clear, direct sentence explaining what this clause means in practice.
3. `priority`: Select EXACTLY one from ["High", "Medium", "Low", "FYI"]:
   - "High": Significant financial/legal risk, severe restriction, heavy penalty, or non-compete/IP loss.
   - "Medium": Meaningful obligation, specific deadline, notice requirement, or standard variable clause.
   - "Low": Standard boilerplate, standard legal mechanics, low risk.
   - "FYI": Purely informational provision.
4. `questions_to_ask`: 2 to 4 concrete, actionable questions the reader should ask the other party before signing.

Return your output as a JSON object matching this schema:
{
  "cards": [
    {
      "id": "clause-1",
      "title": "...",
      "plain_meaning": "...",
      "priority": "High",
      "questions_to_ask": ["...", "..."]
    }
  ]
}
"""


def card_builder_node(state: AnalysisGraphState, llm_client: LLMClient | None = None) -> dict[str, Any]:
    """LangGraph node that synthesizes rich ClauseCard objects from raw_clauses in a single batch LLM call."""
    raw_clauses = state.get("raw_clauses") or []
    logger.info(f"Executing CardBuilder node [input_raw_clauses={len(raw_clauses)}]")
    if not raw_clauses:
        logger.warning("CardBuilder node received 0 raw clauses")
        return {"clause_cards": []}

    if llm_client is None:
        llm_client = LLMClient()

    priority_map: dict[str, PriorityLevel] = {
        "Review carefully": "High",
        "Potentially important": "Medium",
        "Standard": "Low",
        "Beneficial": "FYI",
        "Unclear": "High",
    }

    formatted_input = []
    for clause in raw_clauses:
        formatted_input.append({
            "id": clause.get("id"),
            "section_reference": clause.get("section_reference"),
            "review_label": clause.get("review_label"),
            "plain_language": clause.get("plain_language"),
            "why_it_matters": clause.get("why_it_matters"),
            "clause_text": clause.get("clause_text"),
        })

    user_prompt = f"Please synthesize Clause Cards for the following extracted clauses:\n\n{json.dumps(formatted_input, indent=2)}"

    synthesized_dict: dict[str, dict[str, Any]] = {}
    try:
        res = llm_client.complete(
            system_prompt=BATCH_CARD_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=BatchCardSynthesisOutput,
        )
        if "cards" in res:
            for card_item in res.get("cards", []):
                synthesized_dict[card_item.get("id", "")] = card_item
        elif "title" in res:
            cid = raw_clauses[0].get("id", "clause-1") if raw_clauses else "clause-1"
            synthesized_dict[cid] = res

        logger.info(f"Batch card synthesis returned {len(synthesized_dict)} synthesized cards")
    except LLMError as err:
        logger.warning(f"Batch card synthesis failed: {err}. Using local fallback field mapping.")

    clause_cards: list[dict[str, Any]] = []
    for clause in raw_clauses:
        cid = clause.get("id", "clause-1")
        sec_ref = clause.get("section_reference", "General")
        rev_label = clause.get("review_label", "Standard")
        orig_text = clause.get("clause_text", "")
        plain_lang = clause.get("plain_language", "")

        syn = synthesized_dict.get(cid)
        if syn:
            title = syn.get("title") or clause.get("plain_language", "Clause Review")[:40]
            plain_meaning = syn.get("plain_meaning") or plain_lang
            priority = syn.get("priority") or priority_map.get(rev_label, "Medium")
            questions = syn.get("questions_to_ask") or clause.get("questions_to_consider", [])
        else:
            title = plain_lang[:40] if plain_lang else f"Clause ({sec_ref})"
            plain_meaning = plain_lang or "Clause requires review."
            priority = priority_map.get(rev_label, "Medium")
            questions = clause.get("questions_to_consider") or ["What does this clause mean in context?"]

        clause_cards.append({
            "id": cid,
            "title": title,
            "plain_meaning": plain_meaning,
            "priority": priority,
            "questions_to_ask": questions,
            "review_label": rev_label,
            "section_reference": sec_ref,
            "original_text": orig_text,
        })

    logger.info(f"CardBuilder node completed [total_cards={len(clause_cards)}]")
    return {"clause_cards": clause_cards}
