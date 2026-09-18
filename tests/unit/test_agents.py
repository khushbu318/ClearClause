"""Unit tests for LangGraph agents (ClauseExtract, CardBuilder, Summary)."""

from unittest.mock import MagicMock

from backend.agents.card_builder_agent import card_builder_node
from backend.agents.clause_extract_agent import clause_extract_node
from backend.agents.summary_agent import summary_node
from backend.models.graph_state import AnalysisGraphState


def test_clause_extract_node_pdf():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = {
        "clauses": [
            {
                "id": "clause-1",
                "section_reference": "Page 1",
                "clause_text": "Termination penalty applies.",
                "review_label": "Review carefully",
                "plain_language": "Early exit fee.",
                "why_it_matters": "Financial cost.",
                "questions_to_consider": ["Can fee be waived?"],
            }
        ]
    }

    state: AnalysisGraphState = {
        "input_type": "pdf",
        "raw_input": b"%PDF-1.4 test",
        "document_context": "Tenant lease",
        "page_index": {1: "Sample lease clause text."},
        "extraction_attempts": 0,
        "degraded_clauses": [],
    }

    res = clause_extract_node(state, llm_client=mock_llm)
    assert "raw_clauses" in res
    assert len(res["raw_clauses"]) == 1
    assert res["raw_clauses"][0]["id"] == "clause-1"


def test_card_builder_node():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = {
        "title": "Early Termination Fee",
        "plain_meaning": "You must pay 2 months rent if leaving early.",
        "priority": "High",
        "questions_to_ask": ["Is there a waiver for job loss?"],
    }

    state: AnalysisGraphState = {
        "raw_clauses": [
            {
                "id": "clause-1",
                "section_reference": "Page 1",
                "review_label": "Review carefully",
                "plain_language": "Early exit fee.",
                "why_it_matters": "Financial cost.",
                "clause_text": "Tenant pays termination fee.",
                "questions_to_consider": ["Is there a waiver?"],
            }
        ]
    }

    res = card_builder_node(state, llm_client=mock_llm)
    assert "clause_cards" in res
    assert len(res["clause_cards"]) == 1
    card = res["clause_cards"][0]
    assert card["priority"] == "High"
    assert card["title"] == "Early Termination Fee"


def test_summary_node():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = {
        "document_type": "Residential Lease",
        "parties": ["Landlord LLC", "Jane Doe"],
        "summary": "12-month lease with early termination fee.",
        "key_obligations": ["Pay rent on 1st"],
        "key_dates": ["Lease start: Jan 1"],
        "key_financial_terms": ["Rent: $1500/mo"],
    }

    state: AnalysisGraphState = {
        "document_context": "Tenant lease",
        "clause_cards": [
            {
                "id": "clause-1",
                "title": "Early Termination Fee",
                "plain_meaning": "You must pay 2 months rent if leaving early.",
                "priority": "High",
                "questions_to_ask": ["Is there a waiver?"],
                "review_label": "Review carefully",
                "section_reference": "Page 1",
                "original_text": "Tenant pays termination fee.",
            }
        ],
    }

    res = summary_node(state, llm_client=mock_llm)
    assert "analysis" in res
    analysis = res["analysis"]
    assert analysis["document_type"] == "Residential Lease"
    assert len(analysis["parties"]) == 2
