"""LangGraph node for extracting clauses from indexed documents (PDF or FAISS-indexed text/URL)."""

from typing import Any

from pydantic import BaseModel, Field

from backend.integrations.llm_client import LLMClient, LLMError
from backend.models.clause import Clause
from backend.models.graph_state import AnalysisGraphState
from backend.prompts.extract_clauses import (
    EXTRACT_CLAUSES_SYSTEM_PROMPT,
    EXTRACT_CLAUSES_USER_PROMPT,
)
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class ClauseExtractionResponse(BaseModel):
    clauses: list[Clause] = Field(default_factory=list)


def clause_extract_node(state: AnalysisGraphState, llm_client: LLMClient | None = None) -> dict[str, Any]:
    """LangGraph node that extracts raw legal clauses from the ingested document."""
    input_type = state.get("input_type")
    document_context = state.get("document_context") or "General document review"
    raw_clauses: list[dict[str, Any]] = []
    degraded_clauses: list[str] = list(state.get("degraded_clauses") or [])
    attempts = state.get("extraction_attempts", 0) + 1

    logger.info(f"Executing ClauseExtract node [input_type={input_type}, attempt={attempts}]")

    if llm_client is None:
        llm_client = LLMClient()

    try:
        if input_type == "pdf":
            page_index = state.get("page_index") or {}
            if not page_index:
                parsed_doc = state.get("parsed_document") or {}
                raw_text = parsed_doc.get("raw_text", "")
                page_index = {1: raw_text}

            sorted_pages = sorted(page_index.keys())
            total_chars = sum(len(page_index[p]) for p in sorted_pages)
            logger.info(f"PDF clause extraction input [total_pages={len(sorted_pages)}, total_chars={total_chars}]")

            if total_chars < 50000:
                combined_text = "\n\n--- Page Break ---\n\n".join(
                    f"[Page {p}]\n{page_index[p]}" for p in sorted_pages
                )
                section_ref = f"Pages 1-{sorted_pages[-1]}" if len(sorted_pages) > 1 else "Page 1"
                batches = [(section_ref, combined_text)]
            else:
                batch_size = 5
                batches = []
                for i in range(0, len(sorted_pages), batch_size):
                    page_group = sorted_pages[i : i + batch_size]
                    comb = "\n\n--- Page Break ---\n\n".join(
                        f"[Page {p}]\n{page_index[p]}" for p in page_group
                    )
                    s_ref = f"Pages {page_group[0]}-{page_group[-1]}" if len(page_group) > 1 else f"Page {page_group[0]}"
                    batches.append((s_ref, comb))

            clause_counter = 1
            for section_ref, text_content in batches:
                logger.info(f"Extracting clauses from section batch [{section_ref}, chars={len(text_content)}]")
                user_prompt = EXTRACT_CLAUSES_USER_PROMPT.format(
                    document_context=document_context,
                    section_ref=section_ref,
                    text_content=text_content,
                )

                try:
                    res = llm_client.complete(
                        system_prompt=EXTRACT_CLAUSES_SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        schema=ClauseExtractionResponse,
                    )
                    extracted = res.get("clauses", [])
                    logger.info(f"Extracted {len(extracted)} clauses from batch [{section_ref}]")
                    for item in extracted:
                        item["id"] = f"clause-{clause_counter}"
                        clause_counter += 1
                        raw_clauses.append(item)
                except LLMError as err:
                    logger.warning(f"Clause extraction failed for batch [{section_ref}]: {err}")
                    fallback_id = f"clause-{clause_counter}"
                    clause_counter += 1
                    raw_clauses.append({
                        "id": fallback_id,
                        "section_reference": section_ref,
                        "clause_text": text_content[:300] + "...",
                        "review_label": "Unclear",
                        "plain_language": "Clause text could not be fully parsed by AI model.",
                        "why_it_matters": "Requires manual review.",
                        "questions_to_consider": ["What are the exact terms in this section?"],
                    })
                    degraded_clauses.append(fallback_id)

        else:
            chunks = state.get("chunks") or []
            if not chunks:
                parsed_doc = state.get("parsed_document") or {}
                raw_text = parsed_doc.get("raw_text", "")
                chunks = [raw_text] if raw_text else []

            combined_text = "\n\n--- Chunk Break ---\n\n".join(chunks)
            if len(combined_text) < 50000:
                batches = [("Full Document", combined_text)]
            else:
                batch_size = 5
                batches = []
                for i in range(0, len(chunks), batch_size):
                    chunk_group = chunks[i : i + batch_size]
                    comb = "\n\n--- Chunk Break ---\n\n".join(chunk_group)
                    s_ref = f"Section {i + 1}-{min(i + batch_size, len(chunks))}"
                    batches.append((s_ref, comb))

            clause_counter = 1
            for section_ref, text_content in batches:
                logger.info(f"Extracting clauses from chunk batch [{section_ref}, chars={len(text_content)}]")
                user_prompt = EXTRACT_CLAUSES_USER_PROMPT.format(
                    document_context=document_context,
                    section_ref=section_ref,
                    text_content=text_content,
                )

                try:
                    res = llm_client.complete(
                        system_prompt=EXTRACT_CLAUSES_SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        schema=ClauseExtractionResponse,
                    )
                    extracted = res.get("clauses", [])
                    logger.info(f"Extracted {len(extracted)} clauses from batch [{section_ref}]")
                    for item in extracted:
                        item["id"] = f"clause-{clause_counter}"
                        clause_counter += 1
                        raw_clauses.append(item)
                except LLMError as err:
                    logger.warning(f"Clause extraction failed for batch [{section_ref}]: {err}")
                    fallback_id = f"clause-{clause_counter}"
                    clause_counter += 1
                    raw_clauses.append({
                        "id": fallback_id,
                        "section_reference": section_ref,
                        "clause_text": text_content[:300] + "...",
                        "review_label": "Unclear",
                        "plain_language": "Clause text could not be fully parsed by AI model.",
                        "why_it_matters": "Requires manual review.",
                        "questions_to_consider": ["What are the exact terms in this section?"],
                    })
                    degraded_clauses.append(fallback_id)

        logger.info(
            f"ClauseExtract node completed [extracted_clauses={len(raw_clauses)}, degraded={len(degraded_clauses)}]"
        )
        return {
            "raw_clauses": raw_clauses,
            "extraction_attempts": attempts,
            "degraded_clauses": degraded_clauses,
        }

    except Exception as exc:
        logger.error(f"Error in clause extraction node: {exc}")
        return {
            "error": f"Clause extraction failed: {str(exc)}",
            "extraction_attempts": attempts,
            "raw_clauses": raw_clauses,
            "degraded_clauses": degraded_clauses,
        }
