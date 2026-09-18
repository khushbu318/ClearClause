"""Streamlit UI component to render individual ClauseCard objects."""

from typing import Any, Union

import streamlit as st

from backend.models.clause import ClauseCard


def render_clause_card(card: Union[dict[str, Any], ClauseCard]):
    """Render a styled ClauseCard in Streamlit."""
    if isinstance(card, ClauseCard):
        c_dict = card.model_dump()
    else:
        c_dict = card

    priority = c_dict.get("priority", "Medium")
    title = c_dict.get("title", "Clause Review")
    plain_meaning = c_dict.get("plain_meaning", "")
    questions = c_dict.get("questions_to_ask") or []
    review_label = c_dict.get("review_label", "Standard")
    sec_ref = c_dict.get("section_reference", "Doc Excerpt")
    orig_text = c_dict.get("original_text", "")

    p_lower = priority.lower()

    # CSS classes
    card_class = f"clause-card clause-card-{p_lower}"
    badge_class = f"priority-badge badge-{p_lower}"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #0F172A;">{title}</h3>
                <div>
                    <span style="font-size: 0.8rem; color: #64748B; margin-right: 8px;"><b>{sec_ref}</b> ({review_label})</span>
                    <span class="{badge_class}">{priority}</span>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <p style="margin: 0; font-size: 0.95rem; color: #334155; line-height: 1.5;">
                    <b>What it means:</b> {plain_meaning}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Questions & Original Text sub-block
    if questions:
        with st.expander(f"❓ Questions to Ask Before Signing ({len(questions)})", expanded=False):
            for q in questions:
                st.markdown(f"- {q}")

    with st.expander("📄 Verbatim Original Text", expanded=False):
        st.caption(orig_text)
