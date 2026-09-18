"""
frontend/Home.py — ClearClause entry point (Streamlit multipage Home).
Renders branding, how-it-works, feature cards, and CTAs.
All content is readable dummy/placeholder text for Phase 0.
"""

import os
import sys

# Make backend importable from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from frontend.ui.theme import GLOBAL_CSS, PRIORITY_COLORS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClearClause — Read | Understand | Aware",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject global CSS ─────────────────────────────────────────────────────────
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────


# ── Hero section ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding: 3rem 1rem 1.5rem;">
        <h1 style="font-size:2.8rem; font-weight:700; color:#E8EDF2; margin-bottom:0.4rem;">
            ⚖️ ClearClause
        </h1>
        <p style="font-size:1.3rem; color:#0E9B8A; font-weight:500; letter-spacing:0.08em; margin-bottom:1.2rem;">
            READ &nbsp;|&nbsp; UNDERSTAND &nbsp;|&nbsp; AWARE
        </p>
        <p style="font-size:1.1rem; color:#8B9CB3; max-width:620px; margin:0 auto 2rem;">
            Legal documents are long, confusing, and easy to sign without really understanding.
            ClearClause breaks them down into plain language — clause by clause —
            so you know what you're agreeing to <em>before</em> you sign.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Privacy callout ───────────────────────────────────────────────────────────
st.info(
    "🔒 **Your document stays private.** "
    "Nothing you upload is store on our sedrvers. "
    "All processing happens in your session and is discarded when you leave."
    "This tool is for informational use only — not legal advice.",
    icon=None,
)

st.divider()

# ── Primary CTAs ──────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2, gap="large")

with col_a:
    st.markdown(
        """
        <div class="cc-card" style="text-align:center; padding:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">📄</div>
            <h3 style="color:#E8EDF2; margin-bottom:0.5rem;">Understand a Document</h3>
            <p style="color:#8B9CB3; font-size:0.95rem;">
                Upload a PDF, paste text, or provide a URL.
                Get a plain-language summary, clause-by-clause breakdown,
                and questions worth asking.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📄 Understand a Document", width="stretch", type="primary"):
        st.switch_page("pages/1_Understand_Document.py")

with col_b:
    st.markdown(
        """
        <div class="cc-card" style="text-align:center; padding:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">🔍</div>
            <h3 style="color:#E8EDF2; margin-bottom:0.5rem;">Compare Two Documents</h3>
            <p style="color:#8B9CB3; font-size:0.95rem;">
                Got two versions of a contract? Compare them side-by-side
                to see what was added, removed, or changed — and what it means for you.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🔍 Compare Two Documents", width="stretch"):
        st.switch_page("pages/2_Compare_Documents.py")

st.divider()

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("### How it works")

col1, col2, col3 = st.columns(3, gap="medium")

steps = [
    ("1️⃣", "Provide your document", "Upload a PDF, paste the text, or drop in a public URL. We accept leases, NDAs, job offers, terms of service — any text-based legal document."),
    ("2️⃣", "AI analyzes it", "ClearClause extracts every clause, simplifies it into plain English, flags anything that deserves a closer look, and generates questions you should ask."),
    ("3️⃣", "Explore the insights", "Browse Clause Cards, read the summary, ask your own questions about the document, and export a Review Checklist to bring to your next conversation."),
]

for col, (icon, title, desc) in zip([col1, col2, col3], steps):
    with col:
        st.markdown(
            f"""
            <div class="cc-card" style="text-align:center; height:100%;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">{icon}</div>
                <h4 style="color:#E8EDF2; margin-bottom:0.5rem;">{title}</h4>
                <p style="color:#8B9CB3; font-size:0.9rem;">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Feature cards — dummy example clause cards ─────────────────────────────────
st.markdown("### What you get — example Clause Cards")
st.caption("These are example outputs from a sample rental agreement. Your results will reflect your document.")

example_cards = [
    {
        "priority": "High",
        "title": "Early Termination Fee",
        "plain_meaning": "If you move out before the lease ends, you must pay the equivalent of two months' rent as a penalty.",
        "section": "Page 4, §7.2",
        "questions": ["Is there any waiver clause if I lose my job?", "What counts as adequate written notice?"],
    },
    {
        "priority": "Medium",
        "title": "Automatic Renewal",
        "plain_meaning": "This lease renews automatically for another 12 months unless you give 60 days' written notice before the end date.",
        "section": "Page 2, §3.1",
        "questions": ["How do I send written notice — email or physical letter?", "Can I switch to month-to-month instead of a full renewal?"],
    },
    {
        "priority": "FYI",
        "title": "Pet Policy",
        "plain_meaning": "Pets are allowed with a refundable $300 pet deposit. The deposit is returned if no pet damage is found on move-out inspection.",
        "section": "Page 6, §11.4",
        "questions": ["What counts as 'pet damage' vs. normal wear and tear?"],
    },
]

for card in example_cards:
    priority = card["priority"]
    color = PRIORITY_COLORS.get(priority, "#6B7280")
    questions_html = "".join(f"<li style='color:#8B9CB3; font-size:0.88rem; margin-bottom:0.25rem;'>{q}</li>" for q in card["questions"])
    st.markdown(
        f"""
        <div class="cc-card">
            <span class="cc-badge" style="background:{color}22; color:{color}; border:1px solid {color}44;">
                {priority}
            </span>
            <h4 style="color:#E8EDF2; margin:0.4rem 0 0.3rem;">{card['title']}</h4>
            <p style="color:#B0BEC5; font-size:0.95rem; margin-bottom:0.5rem;">{card['plain_meaning']}</p>
            <hr class="cc-divider">
            <p style="color:#8B9CB3; font-size:0.82rem; margin-bottom:0.4rem;">📍 {card['section']}</p>
            <p style="color:#8B9CB3; font-size:0.88rem; font-weight:600; margin-bottom:0.3rem;">Questions to ask:</p>
            <ul style="padding-left:1.2rem; margin:0;">{questions_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.warning(
    "⚠️ **ClearClause is an informational tool — not legal advice.** "
    "AI analysis can make mistakes, miss context, or mischaracterize clauses. "
    "Always consult a qualified lawyer before signing any legally binding document.",
    icon=None,
)

st.markdown(
    "<p style='text-align:center; color:#8B9CB3; font-size:0.8rem; margin-top:2rem;'>"
    "ClearClause · Built with Streamlit + LangGraph · "
    "No documents stored · Open-source"
    "</p>",
    unsafe_allow_html=True,
)
