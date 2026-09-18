"""
frontend/pages/2_Compare_Documents.py
Two-document comparison page — Phase 0 placeholder with full readable dummy UI.
Real LangGraph comparison pipeline will be wired in Phase 6.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st

from frontend.ui.theme import GLOBAL_CSS

st.set_page_config(
    page_title="Compare Documents — ClearClause",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="color:#E8EDF2; margin-bottom:0.2rem;">🔍 Compare Two Documents</h1>
    <p style="color:#8B9CB3; font-size:1rem; margin-bottom:1.5rem;">
        Compare two versions of a contract — lease drafts, NDA revisions, employment offer updates —
        and see exactly what changed and what it means for you.
    </p>
    """,
    unsafe_allow_html=True,
)


def _input_panel(label: str, key_prefix: str):
    """Renders one document input panel (PDF / URL / Text)."""
    st.markdown(f"#### {label}")
    input_type = st.radio(
        "Input method",
        options=["📄 PDF Upload", "🌐 URL", "📝 Paste Text"],
        horizontal=True,
        key=f"{key_prefix}_type",
    )
    if input_type == "📄 PDF Upload":
        f = st.file_uploader(
            "Upload PDF (max 5 MB)",
            type=["pdf"],
            key=f"{key_prefix}_pdf",
        )
        if f:
            st.caption(f"📎 {f.name} — {f.size / (1024*1024):.2f} MB")
        return f, None, None
    elif input_type == "🌐 URL":
        url = st.text_input(
            "Public URL (https:// only)",
            placeholder="https://example.com/contract-v2",
            key=f"{key_prefix}_url",
        )
        return None, url, None
    else:
        txt = st.text_area(
            "Paste document text",
            placeholder="Paste the full text of the document…",
            height=160,
            key=f"{key_prefix}_text",
        )
        return None, None, txt


# ── Two-column input ──────────────────────────────────────────────────────────
st.markdown("### Step 1 — Provide both documents")

col_a, col_sep, col_b = st.columns([5, 0.3, 5])

with col_a:
    file_a, url_a, text_a = _input_panel("Document A — Original", "doc_a")

with col_sep:
    st.markdown(
        "<div style='border-left:1px solid #2A3F55; height:300px; margin:2rem auto;'></div>",
        unsafe_allow_html=True,
    )

with col_b:
    file_b, url_b, text_b = _input_panel("Document B — Revised", "doc_b")

st.divider()

# ── Optional focus ────────────────────────────────────────────────────────────
st.markdown("### Step 2 — Set a comparison focus *(optional)*")
focus = st.text_input(
    "What should we focus the comparison on?",
    placeholder="e.g. termination clauses, payment terms, liability caps",
    key="compare_focus",
)
st.caption("Leave blank for a full comparison. Adding a focus makes the diff analysis more targeted.")

st.divider()

# ── Compare button ────────────────────────────────────────────────────────────
has_a = bool(file_a or (url_a and url_a.strip()) or (text_a and text_a.strip()))
has_b = bool(file_b or (url_b and url_b.strip()) or (text_b and text_b.strip()))
compare_btn = st.button(
    "🔍 Compare Documents",
    type="primary",
    width="stretch",
    disabled=not (has_a and has_b),
    key="compare_btn",
)
if not (has_a and has_b):
    st.caption("Provide both documents above to enable comparison.")

# ── Processing state ──────────────────────────────────────────────────────────
if compare_btn and has_a and has_b:
    st.divider()
    st.markdown("### Processing…")
    steps = [
        ("Document A received", True, False),
        ("Document B received", True, False),
        ("Analyzing Document A…", True, False),
        ("Analyzing Document B…", False, True),
        ("Aligning clauses semantically…", False, False),
        ("Categorizing differences…", False, False),
        ("Results ready", False, False),
    ]
    for label, done, active in steps:
        if done:
            cls, icon = "cc-step-done", "✅"
        elif active:
            cls, icon = "cc-step-active", "⏳"
        else:
            cls, icon = "cc-step-pending", "○"
        st.markdown(
            f"<p class='{cls}' style='margin:0.2rem 0;'>{icon} {label}</p>",
            unsafe_allow_html=True,
        )
    st.info(
        "⚙️ **Phase 0 placeholder** — The LangGraph comparison pipeline will be wired in Phase 6.",
        icon=None,
    )

st.divider()

# ── Results area (dummy) ──────────────────────────────────────────────────────
st.markdown("### Results")
st.caption("Results will appear here after comparison. Showing example output for layout reference.")

tab_overview, tab_table, tab_detail = st.tabs(
    ["📊 Overview", "📋 Difference Table", "🃏 Detailed Clause Comparison"]
)

# ── Tab: Overview ─────────────────────────────────────────────────────────────
with tab_overview:
    st.markdown("#### Comparison Overview")
    st.markdown(
        """
        <div class="cc-card">
            <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.4rem;">DOCUMENT PAIR</p>
            <p style="color:#E8EDF2; margin-bottom:0.75rem;">
                <strong>A:</strong> Lease Agreement — Original Draft (Jan 2025) &nbsp;·&nbsp;
                <strong>B:</strong> Lease Agreement — Revised Draft (Feb 2025)
            </p>
            <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.4rem;">COMPARISON SUMMARY</p>
            <p style="color:#B0BEC5; font-size:0.95rem; margin-bottom:0;">
                Document B introduced 4 meaningful changes from Document A.
                The most significant change is the removal of the rent freeze clause,
                which now allows the landlord to increase rent by up to 10% on renewal.
                The early termination fee was also increased from one to two months' rent.
                Two standard clauses were added about utilities and renter's insurance.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    stats = [
        ("Added", "2", "#10B981"),
        ("Removed", "1", "#EF4444"),
        ("Modified", "3", "#F59E0B"),
        ("Unchanged", "8", "#6B7280"),
    ]
    for col, (label, count, color) in zip([col1, col2, col3, col4], stats):
        with col:
            st.markdown(
                f"""
                <div class="cc-card" style="text-align:center; padding:1rem;">
                    <p style="font-size:2rem; font-weight:700; color:{color}; margin:0;">{count}</p>
                    <p style="color:#8B9CB3; font-size:0.85rem; margin:0;">{label}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Tab: Difference Table ─────────────────────────────────────────────────────
with tab_table:
    st.markdown("#### Structured Difference Table")

    diff_data = [
        {"Clause": "Early Termination Fee", "Status": "Modified 🔶", "Category": "Potentially more restrictive", "Impact": "Fee increased from 1 → 2 months' rent"},
        {"Clause": "Rent Freeze on Renewal", "Status": "Removed 🔴", "Category": "Potentially more restrictive", "Impact": "Landlord can now raise rent up to 10% on renewal"},
        {"Clause": "Utilities (Water)", "Status": "Added 🟢", "Category": "Requires review", "Impact": "Tenant now responsible for water bill"},
        {"Clause": "Renter's Insurance Requirement", "Status": "Added 🟢", "Category": "Standard", "Impact": "Tenant must maintain $100K liability policy"},
        {"Clause": "Pet Policy", "Status": "Modified 🔶", "Category": "Requires review", "Impact": "Pet deposit increased from $200 → $300"},
        {"Clause": "Landlord Entry Rights", "Status": "Unchanged ⚪", "Category": "Unchanged", "Impact": "—"},
        {"Clause": "Security Deposit", "Status": "Unchanged ⚪", "Category": "Unchanged", "Impact": "—"},
        {"Clause": "Lease Term", "Status": "Unchanged ⚪", "Category": "Unchanged", "Impact": "—"},
    ]

    import pandas as pd
    st.dataframe(
        pd.DataFrame(diff_data),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Clause": st.column_config.TextColumn("Clause"),
            "Status": st.column_config.TextColumn("Status"),
            "Category": st.column_config.TextColumn("Category"),
            "Impact": st.column_config.TextColumn("What Changed"),
        },
    )

# ── Tab: Detailed Clause Comparison ──────────────────────────────────────────
with tab_detail:
    st.markdown("#### Detailed Clause-by-Clause Comparison")
    st.caption("Each changed clause shown side by side with a plain-language explanation of what the change means.")

    detailed_diffs = [
        {
            "title": "Early Termination Fee",
            "category": "Potentially more restrictive",
            "category_color": "#F59E0B",
            "doc_a": "If Tenant vacates before the Lease Term ends, Tenant shall pay a termination fee equal to one (1) month's Base Rent.",
            "doc_b": "If Tenant vacates before the Lease Term ends, Tenant shall pay a termination fee equal to two (2) months' Base Rent.",
            "explanation": "The revised draft doubles the early termination fee from $1,800 to $3,600. This is a significant financial change that makes breaking the lease substantially more expensive.",
        },
        {
            "title": "Rent Freeze on Renewal (REMOVED)",
            "category": "Potentially more restrictive",
            "category_color": "#EF4444",
            "doc_a": "Rent shall not increase upon automatic renewal unless mutually agreed in writing by both parties.",
            "doc_b": "— (Clause removed in Document B)",
            "explanation": "The original draft protected you from rent increases on renewal. The revised draft removed this protection entirely, allowing the landlord to raise rent by up to the legal maximum (10% in this jurisdiction) with only the standard renewal notice.",
        },
        {
            "title": "Pet Policy",
            "category": "Requires review",
            "category_color": "#3B82F6",
            "doc_a": "Tenant may keep domestic pets with a refundable pet deposit of $200.",
            "doc_b": "Tenant may keep domestic pets with a refundable pet deposit of $300.",
            "explanation": "The pet deposit increased by $100. This is a minor financial change but worth confirming whether the additional deposit is fully refundable under the same conditions.",
        },
    ]

    for diff in detailed_diffs:
        c_color = diff["category_color"]
        with st.expander(f"{diff['title']} — {diff['category']}", expanded=True):
            st.markdown(
                f"""
                <span class="cc-badge" style="background:{c_color}22; color:{c_color}; border:1px solid {c_color}44; margin-bottom:0.75rem; display:inline-block;">
                    {diff['category']}
                </span>
                """,
                unsafe_allow_html=True,
            )
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**Document A (Original)**")
                st.markdown(
                    f"<div class='cc-card'><p style='color:#B0BEC5; font-style:italic; font-size:0.9rem;'>\"{diff['doc_a']}\"</p></div>",
                    unsafe_allow_html=True,
                )
            with col_right:
                st.markdown("**Document B (Revised)**")
                st.markdown(
                    f"<div class='cc-card'><p style='color:#B0BEC5; font-style:italic; font-size:0.9rem;'>\"{diff['doc_b']}\"</p></div>",
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"""
                <div class="cc-card" style="border-left:3px solid {c_color};">
                    <p style="color:#8B9CB3; font-size:0.82rem; margin-bottom:0.3rem;">WHAT THIS MEANS FOR YOU</p>
                    <p style="color:#E8EDF2; font-size:0.95rem; margin:0;">{diff['explanation']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()
st.warning(
    "⚠️ ClearClause is an informational tool — not legal advice. "
    "Always consult a qualified lawyer before signing any legally binding document.",
    icon=None,
)
