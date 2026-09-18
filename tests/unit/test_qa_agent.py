"""Unit tests for QA agent."""

from unittest.mock import MagicMock

from backend.agents.qa_agent import answer_document_question


def test_answer_document_question_mocked_llm():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = {
        "answer": "The Fixed compensation is $100,000 per annum and the Variable component is up to $20,000 based on performance.",
        "citation": "Page 2 - Compensation",
        "grounded": True,
    }

    analysis_state = {
        "page_index": {1: "Offer letter to Employee.", 2: "Base salary: $100,000 fixed. Performance bonus: up to $20,000 variable."},
        "clause_cards": [],
    }

    res = answer_document_question(
        question="What is the Fixed and variable of total component or salary?",
        analysis_state=analysis_state,
        llm_client=mock_llm,
    )

    assert res["grounded"] is True
    assert "$100,000" in res["answer"]
    assert "Page 2" in res["citation"]
