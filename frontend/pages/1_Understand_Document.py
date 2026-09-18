"""
frontend/pages/1_Understand_Document.py
Single-document analysis page — Integrated with LangGraph Backend.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st

from backend.services.document_analysis_service import analyze_document
from frontend.ui.clause_card import render_clause_card
from frontend.ui.processing_status import render_processing_status
from frontend.ui.theme import apply_custom_css

st.set_page_config(
    page_title="Understand a Document — ClearClause",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="color:#E8EDF2; margin-bottom:0.2rem;">📄 Understand a Document</h1>
    <p style="color:#8B9CB3; font-size:1rem; margin-bottom:1.5rem;">
        Upload a PDF, paste text, or enter a URL — ClearClause will break it down clause by clause.
    </p>
    """,
    unsafe_allow_html=True,
)

# Disclaimer banner
st.markdown(
    """
    <div class="disclaimer-banner">
        🛡️ <b>Privacy-First & Informational Only:</b> Your documents are processed temporarily in memory and never persisted.
        ClearClause provides plain-language explanations, not legal advice.
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Input section ─────────────────────────────────────────────────────────────
st.markdown("### Step 1 — Provide your document")

input_type = st.radio(
    "Choose input method",
    options=["📄 PDF Upload", "🌐 URL", "📝 Paste Text"],
    horizontal=True,
    key="input_type_radio",
)

uploaded_file = None
url_input = ""
text_input = ""
backend_input_type = "pdf"

if input_type == "📄 PDF Upload":
    backend_input_type = "pdf"
    uploaded_file = st.file_uploader(
        "Upload a PDF (max 5 MB, ~25 pages)",
        type=["pdf"],
        key="pdf_uploader",
        help="Accepts standard text-based PDFs. Scanned/image PDFs are not supported.",
    )
    if uploaded_file:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.caption(f"📎 {uploaded_file.name} — {size_mb:.2f} MB")

elif input_type == "🌐 URL":
    backend_input_type = "url"
    url_input = st.text_input(
        "Paste a public document URL (https:// only)",
        placeholder="https://example.com/terms-of-service",
        key="url_input",
    )
    st.caption("We'll fetch and extract the text. Private or login-gated pages are not supported.")

elif input_type == "📝 Paste Text":
    backend_input_type = "text"
    text_input = st.text_area(
        "Paste your document text here",
        placeholder="Paste the full text of your lease, NDA, job offer, or terms of service...",
        height=200,
        key="text_input",
    )
    if text_input:
        word_count = len(text_input.split())
        st.caption(f"~{word_count:,} words entered")

st.divider()

# ── Optional context ──────────────────────────────────────────────────────────
st.markdown("### Step 2 — Add context *(optional)*")
context_options = [
    "None — just analyze the document",
    "I'm the tenant reviewing a lease",
    "I'm an employee reviewing a job offer",
    "I'm reviewing an NDA before signing",
    "I'm reviewing terms of service before signing up",
    "Other — I'll describe below",
]
context_choice = st.selectbox(
    "What is your relationship to this document?",
    options=context_options,
    key="context_choice",
)

document_context = context_choice
if context_choice == "Other — I'll describe below":
    custom_context = st.text_input(
        "Describe your context",
        placeholder="e.g. I'm a freelancer reviewing a client services agreement",
        key="custom_context",
    )
    if custom_context:
        document_context = custom_context

st.divider()

# ── Analyze button ────────────────────────────────────────────────────────────
has_input = bool(uploaded_file or url_input.strip() or text_input.strip())
analyze_btn = st.button(
    "⚡ Analyze Document",
    type="primary",
    width="stretch",
    disabled=not has_input,
    key="analyze_btn",
)

if not has_input:
    st.caption("Provide a document above to enable analysis.")

# ── Execute Analysis Pipeline ──────────────────────────────────────────────────
if analyze_btn and has_input:
    with st.spinner("Processing document through LangGraph pipeline..."):
        render_processing_status(2)

        raw_input_data = None
        if backend_input_type == "pdf":
            raw_input_data = uploaded_file.read()
        elif backend_input_type == "url":
            raw_input_data = url_input.strip()
        else:
            raw_input_data = text_input.strip()

        # Run backend LangGraph pipeline
        result_state = analyze_document(
            raw_input=raw_input_data,
            input_type=backend_input_type,
            document_context=document_context,
        )

        st.session_state["analysis_result"] = result_state

        if result_state.get("error"):
            st.error(f"❌ Analysis failed: {result_state['error']}")
        else:
            st.success("✅ Analysis completed successfully!")

st.divider()

# ── Results Display ────────────────────────────────────────────────────────────
st.markdown("### Analysis Results")

analysis_state = st.session_state.get("analysis_result")

if not analysis_state:
    st.info("👆 Provide a document and click **⚡ Analyze Document** to see insights here.")
else:
    error_msg = analysis_state.get("error")
    if error_msg:
        st.error(f"Analysis error: {error_msg}")

    analysis_data = analysis_state.get("analysis") or {}
    clause_cards = analysis_state.get("clause_cards") or []

    tab_summary, tab_cards, tab_qa, tab_checklist = st.tabs(
        ["📋 Summary", f"🃏 Clause Cards ({len(clause_cards)})", "💬 Ask a Question", "📝 Review Checklist"]
    )

    # ── Tab: Whole Document Summary ───────────────────────────────────────────
    with tab_summary:
        st.markdown("#### Whole-Document Summary")

        doc_type = analysis_data.get("document_type", "Legal Agreement")
        parties = analysis_data.get("parties", [])
        summary_text = analysis_data.get("summary", "No summary available.")
        obligations = analysis_data.get("key_obligations", [])
        dates = analysis_data.get("key_dates", [])
        financial_terms = analysis_data.get("key_financial_terms", [])

        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <p style="color: #64748B; font-size: 0.8rem; font-weight: 700; margin-bottom: 4px; text-transform: uppercase;">DOCUMENT TYPE</p>
                <p style="color: #0F172A; font-size: 1.1rem; font-weight: 600; margin-bottom: 14px;">{doc_type}</p>
                <p style="color: #64748B; font-size: 0.8rem; font-weight: 700; margin-bottom: 4px; text-transform: uppercase;">PARTIES INVOLVED</p>
                <p style="color: #334155; font-size: 0.95rem; margin-bottom: 14px;">{', '.join(parties) if parties else 'Not explicitly specified'}</p>
                <p style="color: #64748B; font-size: 0.8rem; font-weight: 700; margin-bottom: 4px; text-transform: uppercase;">PLAIN SUMMARY</p>
                <p style="color: #334155; font-size: 0.95rem; line-height: 1.6; margin: 0;">{summary_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### 📌 Key Obligations")
            if obligations:
                for item in obligations:
                    st.markdown(f"- {item}")
            else:
                st.caption("No specific key obligations flagged.")

        with col_b:
            st.markdown("##### 📅 Key Dates & 💰 Financial Terms")
            if dates:
                st.markdown("**Dates & Deadlines:**")
                for item in dates:
                    st.markdown(f"- 📅 {item}")
            if financial_terms:
                st.markdown("**Financial Terms:**")
                for item in financial_terms:
                    st.markdown(f"- 💰 {item}")
            if not dates and not financial_terms:
                st.caption("No specific dates or financial terms flagged.")

    # ── Tab: Clause Cards ─────────────────────────────────────────────────────
    with tab_cards:
        st.markdown("#### Clause-by-Clause Breakdown")
        st.caption("Each extracted clause simplified into a priority-coded Clause Card.")

        if not clause_cards:
            st.warning("No clauses extracted from this document.")
        else:
            priority_filter = st.multiselect(
                "Filter by priority level:",
                options=["High", "Medium", "Low", "FYI"],
                default=["High", "Medium", "Low", "FYI"],
                key="clause_priority_filter",
            )

            filtered_cards = [c for c in clause_cards if c.get("priority") in priority_filter]

            st.caption(f"Showing {len(filtered_cards)} of {len(clause_cards)} clause cards.")

            for card in filtered_cards:
                render_clause_card(card)

    # ── Tab: Ask a Question ───────────────────────────────────────────────────
    with tab_qa:
        st.markdown("#### Ask a Question Grounded in This Document")
        st.caption("Questions are answered strictly from the document with citations.")

        if "qa_history" not in st.session_state:
            st.session_state.qa_history = []

        question = st.chat_input("Ask a question about your uploaded document...", key="qa_input")

        if question:
            st.session_state.qa_history.append({"role": "user", "content": question})
            with st.spinner("Searching document context for answer..."):
                from backend.agents.qa_agent import answer_document_question
                qa_res = answer_document_question(question, analysis_state)

            st.session_state.qa_history.append({
                "role": "assistant",
                "content": qa_res.get("answer", ""),
                "citation": qa_res.get("citation", ""),
            })

        for msg in st.session_state.qa_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    if msg.get("citation"):
                        st.caption(f"📎 {msg['citation']}")

        if st.session_state.qa_history:
            if st.button("🔄 Clear conversation", key="clear_qa"):
                st.session_state.qa_history = []
                st.rerun()

    # ── Tab: Review Checklist ─────────────────────────────────────────────────
    with tab_checklist:
        st.markdown("#### Exportable Review Checklist")
        st.caption("Curated questions from High & Medium priority clauses to bring to a lawyer, HR, or landlord.")

        high_medium_cards = [c for c in clause_cards if c.get("priority") in ("High", "Medium")]

        checklist_lines = [
            "# ClearClause Review Checklist",
            f"**Document Type:** {analysis_data.get('document_type', 'Document')}",
            f"**Parties:** {', '.join(analysis_data.get('parties', [])) or 'N/A'}\n",
            "## Whole-Document Summary",
            f"{analysis_data.get('summary', '')}\n",
            "---",
            "## High & Medium Priority Review Questions\n",
        ]

        for card in high_medium_cards:
            checklist_lines.append(
                f"### {card.get('priority')} — {card.get('title')} ({card.get('section_reference')})"
            )
            checklist_lines.append(f"*{card.get('plain_meaning')}*\n")
            for q in card.get("questions_to_ask", []):
                checklist_lines.append(f"- [ ] {q}")
            checklist_lines.append("")

        checklist_lines.append("---\n*⚠️ Informational review checklist — not legal advice.*")
        checklist_text = "\n".join(checklist_lines)

        st.markdown(checklist_text)
        st.divider()

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "📥 Download Markdown Checklist",
                data=checklist_text,
                file_name="clearclause_review_checklist.md",
                mime="text/markdown",
                width="stretch",
                key="dl_md",
            )
        with col_dl2:
            st.download_button(
                "📥 Download TXT Checklist",
                data=checklist_text.replace("#", "").replace("- [ ]", "[ ]"),
                file_name="clearclause_review_checklist.txt",
                mime="text/plain",
                width="stretch",
                key="dl_txt",
            )

st.divider()
st.warning(
    "⚠️ ClearClause is an informational tool — not legal advice. "
    "Always consult a qualified lawyer before signing any legally binding document.",
    icon=None,
)
