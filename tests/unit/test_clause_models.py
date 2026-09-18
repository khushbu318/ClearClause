"""Unit tests for Clause and ClauseCard models."""

from backend.models.analysis import DocumentAnalysis
from backend.models.clause import Clause, ClauseCard


def test_clause_instantiation():
    clause = Clause(
        id="clause-1",
        section_reference="Page 1",
        clause_text="Tenant shall pay rent by 1st of month.",
        review_label="Standard",
        plain_language="Rent is due on the 1st.",
        why_it_matters="Late rent incurs fees.",
        questions_to_consider=["Is there a grace period?"],
    )
    assert clause.id == "clause-1"
    assert clause.review_label == "Standard"
    assert len(clause.questions_to_consider) == 1


def test_clause_card_instantiation():
    card = ClauseCard(
        id="clause-1",
        title="Rent Payment Deadline",
        plain_meaning="You must pay rent on the first day of every month.",
        priority="Medium",
        questions_to_ask=["What payment methods are accepted?"],
        review_label="Standard",
        section_reference="Page 1",
        original_text="Tenant shall pay rent by 1st of month.",
    )
    assert card.priority == "Medium"
    assert card.title == "Rent Payment Deadline"


def test_document_analysis_instantiation():
    card = ClauseCard(
        id="clause-1",
        title="Rent Payment",
        plain_meaning="Pay rent monthly.",
        priority="Low",
        questions_to_ask=[],
        review_label="Standard",
        section_reference="Page 1",
        original_text="Pay rent.",
    )
    analysis = DocumentAnalysis(
        document_type="Lease",
        parties=["Landlord", "Tenant"],
        summary="Standard lease agreement.",
        key_obligations=["Pay rent"],
        key_dates=["1st of month"],
        key_financial_terms=["$1000/mo"],
        clause_cards=[card],
    )
    assert len(analysis.clause_cards) == 1
    assert analysis.document_type == "Lease"
