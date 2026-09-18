"""Integration tests for document analysis LangGraph pipeline."""

from unittest.mock import MagicMock

from backend.services.document_analysis_service import analyze_document


def test_analyze_document_text_pipeline():
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = [
        # 1. clause_extract
        {
            "clauses": [
                {
                    "id": "clause-1",
                    "section_reference": "Section 1",
                    "clause_text": "Non-compete clause for 24 months.",
                    "review_label": "Review carefully",
                    "plain_language": "Cannot work for competitors for 2 years.",
                    "why_it_matters": "Restricts future job options.",
                    "questions_to_consider": ["Is geographic scope limited?"],
                }
            ]
        },
        # 2. card_builder
        {
            "title": "2-Year Non-Compete",
            "plain_meaning": "You cannot work for a competitor for 24 months post-employment.",
            "priority": "High",
            "questions_to_ask": ["What specific companies are considered competitors?"],
        },
        # 3. summary
        {
            "document_type": "Employment Offer Letter",
            "parties": ["TechCorp Inc.", "Employee"],
            "summary": "Employment agreement containing a strict non-compete clause.",
            "key_obligations": ["Abide by 2-year non-compete restriction"],
            "key_dates": ["Start date: Oct 1"],
            "key_financial_terms": ["Base salary: $120,000/yr"],
        },
    ]

    sample_text = """
    EMPLOYMENT OFFER LETTER
    TechCorp Inc. hereby offers employment to Employee.
    Section 1: Non-Compete. Employee agrees not to engage in any competing business for 24 months following termination.
    Salary: $120,000 per year. Start date: October 1.
    """

    res = analyze_document(
        raw_input=sample_text,
        input_type="text",
        document_context="Job offer review",
        llm_client=mock_llm,
    )

    assert res.get("error") is None
    analysis = res.get("analysis")
    assert analysis is not None
    assert analysis["document_type"] == "Employment Offer Letter"
    assert len(analysis["clause_cards"]) == 1
    card = analysis["clause_cards"][0]
    assert card["priority"] == "High"
    assert card["title"] == "2-Year Non-Compete"
