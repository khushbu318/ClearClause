"""
frontend/pages/1_Understand_Document.py
Single-document analysis page — Phase 0 placeholder with full readable dummy UI.
Real LangGraph pipeline will be wired in Phase 2–4.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from frontend.ui.theme import GLOBAL_CSS, PRIORITY_COLORS, LABEL_COLORS

st.set_page_config(
    page_title="Understand a Document — ClearClause",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


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

if input_type == "📄 PDF Upload":
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
    url_input = st.text_input(
        "Paste a public document URL (https:// only)",
        placeholder="https://example.com/terms-of-service",
        key="url_input",
    )
    st.caption("We'll fetch and extract the text. Private or login-gated pages are not supported.")

elif input_type == "📝 Paste Text":
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
if context_choice == "Other — I'll describe below":
    custom_context = st.text_input(
        "Describe your context",
        placeholder="e.g. I'm a freelancer reviewing a client services agreement",
        key="custom_context",
    )

st.divider()

# ── Analyze button ────────────────────────────────────────────────────────────
has_input = bool(uploaded_file or url_input.strip() or text_input.strip())
analyze_btn = st.button(
    "⚡ Analyze Document",
    type="primary",
    use_container_width=True,
    disabled=not has_input,
    key="analyze_btn",
)

if not has_input:
    st.caption("Provide a document above to enable analysis.")

# ── Processing state (dummy staged steps for Phase 0) ─────────────────────────
if analyze_btn and has_input:
    st.divider()
    st.markdown("### Processing…")
    steps = [
        ("Document received", True, True),
        ("Building index…", True, False),
        ("Extracting clauses…", False, False),
        ("Building Clause Cards…", False, False),
        ("Summarizing…", False, False),
        ("Results ready", False, False),
    ]
    for label, done, active in steps:
        if done:
            cls = "cc-step-done"
            icon = "✅"
        elif active:
            cls = "cc-step-active"
            icon = "⏳"
        else:
            cls = "cc-step-pending"
            icon = "○"
        st.markdown(
            f"<p class='{cls}' style='margin:0.2rem 0;'>{icon} {label}</p>",
            unsafe_allow_html=True,
        )
    st.info(
        "⚙️ **Phase 0 placeholder** — The LangGraph analysis pipeline will be wired here in Phase 2. "
        "The staged steps above reflect the real processing states from the graph.",
        icon=None,
    )

st.divider()

# ── Results area (dummy) ──────────────────────────────────────────────────────
st.markdown("### Results")
st.caption("Results will appear here after analysis. Showing example output for layout reference.")

tab_summary, tab_cards, tab_qa, tab_checklist = st.tabs(
    ["📋 Summary", "🃏 Clause Cards", "💬 Ask a Question", "📝 Review Checklist"]
)

# ── Tab: Summary ──────────────────────────────────────────────────────────────
with tab_summary:
    st.markdown("#### Document Summary")
    st.markdown(
        """
        <div class="cc-card">
            <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.4rem;">DOCUMENT TYPE</p>
            <p style="color:#E8EDF2; font-size:1rem; font-weight:500; margin-bottom:1rem;">Residential Lease Agreement</p>
            <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.4rem;">PARTIES</p>
            <p style="color:#E8EDF2; font-size:0.95rem; margin-bottom:1rem;">
                Landlord: Acme Property Management LLC &nbsp;·&nbsp; Tenant: [You]
            </p>
            <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.4rem;">PLAIN SUMMARY</p>
            <p style="color:#B0BEC5; font-size:0.95rem; margin-bottom:0;">
                This is a 12-month residential lease for an apartment at 123 Main Street.
                Rent is $1,800/month due on the 1st, with a 5-day grace period.
                You are responsible for utilities except water. Pets are allowed with a deposit.
                Breaking the lease early costs two months' rent. The lease auto-renews unless
                you give 60 days' notice.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Key Obligations**")
        for item in [
            "Pay $1,800 rent by the 1st of each month",
            "Give 60 days' notice before move-out",
            "Maintain apartment in good condition",
            "No subletting without written consent",
        ]:
            st.markdown(f"- {item}")

    with col_b:
        st.markdown("**Key Dates & Financial Terms**")
        for item in [
            "Lease start: 1 Jan 2025",
            "Lease end: 31 Dec 2025",
            "Security deposit: $3,600 (2 months)",
            "Early termination fee: $3,600 (2 months)",
            "Pet deposit: $300 (refundable)",
        ]:
            st.markdown(f"- {item}")

# ── Tab: Clause Cards ─────────────────────────────────────────────────────────
with tab_cards:
    st.markdown("#### Clause Cards")
    st.caption("Each clause from the document, simplified and prioritized.")

    dummy_cards = [
        {
            "priority": "High",
            "review_label": "Review carefully",
            "title": "Early Termination Fee",
            "plain_meaning": "If you leave before the lease ends, you owe two months' rent — regardless of the reason.",
            "original_text": "Tenant shall pay a termination fee equal to two (2) months' Base Rent if Tenant vacates the Premises prior to the expiration of the Lease Term.",
            "section": "Page 4, §7.2",
            "questions": [
                "Is there a waiver clause for job loss or medical emergency?",
                "What counts as 'written notice' — email or certified mail?",
                "Can I sublet instead of paying the fee?",
            ],
        },
        {
            "priority": "Medium",
            "review_label": "Potentially important",
            "title": "Automatic Renewal",
            "plain_meaning": "Your lease renews for another 12 months automatically unless you notify the landlord 60 days before it ends.",
            "original_text": "Unless Tenant provides written notice of non-renewal no less than sixty (60) days prior to expiration, this Lease shall automatically renew for a period of twelve (12) months.",
            "section": "Page 2, §3.1",
            "questions": [
                "How do I send written notice — email or physical letter?",
                "Can I opt for month-to-month instead of a full renewal?",
            ],
        },
        {
            "priority": "Low",
            "review_label": "Standard",
            "title": "Landlord Entry Rights",
            "plain_meaning": "The landlord can enter your apartment with 24 hours' notice for inspections, repairs, or showings.",
            "original_text": "Landlord may enter the Premises upon twenty-four (24) hours' written notice for inspection, repair, or showing purposes.",
            "section": "Page 5, §9.1",
            "questions": [
                "Can I refuse entry if the timing is inconvenient?",
            ],
        },
        {
            "priority": "FYI",
            "review_label": "Beneficial",
            "title": "Pet Policy",
            "plain_meaning": "Pets are allowed with a refundable $300 deposit, returned if there is no pet-related damage at move-out.",
            "original_text": "Tenant may keep domestic pets upon payment of a refundable pet deposit of $300.00, subject to inspection at lease termination.",
            "section": "Page 6, §11.4",
            "questions": [
                "What counts as 'pet damage' vs. normal wear and tear?",
            ],
        },
    ]

    for card in dummy_cards:
        priority = card["priority"]
        label = card["review_label"]
        p_color = PRIORITY_COLORS.get(priority, "#6B7280")
        l_color = LABEL_COLORS.get(label, "#6B7280")
        questions_html = "".join(
            f"<li style='color:#8B9CB3; font-size:0.88rem; margin-bottom:0.3rem;'>{q}</li>"
            for q in card["questions"]
        )
        with st.expander(f"{card['title']} — {priority} priority", expanded=(priority == "High")):
            st.markdown(
                f"""
                <div style="margin-bottom:0.75rem;">
                    <span class="cc-badge" style="background:{p_color}22; color:{p_color}; border:1px solid {p_color}44; margin-right:0.5rem;">
                        {priority}
                    </span>
                    <span class="cc-badge" style="background:{l_color}22; color:{l_color}; border:1px solid {l_color}44;">
                        {label}
                    </span>
                </div>
                <p style="color:#B0BEC5; font-size:1rem; margin-bottom:0.75rem;">{card['plain_meaning']}</p>
                <hr class="cc-divider">
                <p style="color:#8B9CB3; font-size:0.82rem; margin-bottom:0.4rem;">
                    📍 {card['section']}
                </p>
                <p style="color:#6B7280; font-size:0.85rem; font-style:italic; margin-bottom:0.75rem;">
                    "{card['original_text']}"
                </p>
                <hr class="cc-divider">
                <p style="color:#E8EDF2; font-size:0.88rem; font-weight:600; margin-bottom:0.4rem;">
                    Questions to ask:
                </p>
                <ul style="padding-left:1.2rem; margin:0;">{questions_html}</ul>
                """,
                unsafe_allow_html=True,
            )

# ── Tab: Ask a Question ───────────────────────────────────────────────────────
with tab_qa:
    st.markdown("#### Ask a Question About This Document")
    st.caption("Questions are answered strictly from the document. You'll see citations for every answer.")

    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []

    question = st.chat_input("Ask something about the document…", key="qa_input")

    # Show example exchange
    if not st.session_state.qa_history:
        st.markdown(
            """
            <div class="cc-card" style="opacity:0.7;">
                <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.3rem;">Example question</p>
                <p style="color:#E8EDF2; font-size:0.95rem; margin-bottom:0.75rem;">
                    "What happens if I need to break the lease early?"
                </p>
                <p style="color:#8B9CB3; font-size:0.85rem; margin-bottom:0.3rem;">Example answer</p>
                <p style="color:#B0BEC5; font-size:0.9rem; margin-bottom:0.5rem;">
                    According to §7.2 (Page 4), if you vacate before the lease ends you owe a
                    termination fee equal to two months' rent ($3,600). There is no waiver
                    clause for circumstances like job loss.
                </p>
                <p style="color:#0E9B8A; font-size:0.8rem;">📎 Cited: Clause §7.2 — Early Termination Fee</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if question:
        st.session_state.qa_history.append({"role": "user", "content": question})
        st.session_state.qa_history.append({
            "role": "assistant",
            "content": "⚙️ Q&A pipeline not yet wired (Phase 4). Your question was received: *" + question + "*",
            "citation": "—",
        })

    for msg in st.session_state.qa_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if msg.get("citation") and msg["citation"] != "—":
                    st.caption(f"📎 {msg['citation']}")

    if st.session_state.qa_history:
        if st.button("🔄 Clear conversation", key="clear_qa"):
            st.session_state.qa_history = []
            st.rerun()

    st.divider()
    st.caption(
        "⚠️ Answers are grounded strictly in the uploaded document. "
        "ClearClause will say 'not covered in this document' if your question isn't addressed. "
        "This is not legal advice."
    )

# ── Tab: Review Checklist ─────────────────────────────────────────────────────
with tab_checklist:
    st.markdown("#### Review Checklist")
    st.caption("A curated list of open questions from High and Medium priority clauses — ready to bring to a lawyer, landlord, or HR.")

    checklist_md = """
## ClearClause Review Checklist
*Generated from: Sample Rental Agreement · 16 Sep 2025*

### Document Summary
12-month residential lease at $1,800/month. Key risks: early termination fee (2 months), automatic 12-month renewal, no subletting without consent.

---

### High Priority — Review Carefully

**Early Termination Fee (§7.2, Page 4)**
- [ ] Is there a waiver clause for job loss or medical emergency?
- [ ] What counts as adequate written notice?
- [ ] Can I sublet instead of paying the termination fee?

---

### Medium Priority — Worth Discussing

**Automatic Renewal (§3.1, Page 2)**
- [ ] How do I send written notice — email or certified mail?
- [ ] Can I opt for month-to-month at renewal instead of another 12 months?

**Landlord Entry Rights (§9.1, Page 5)**
- [ ] Can I refuse entry if the timing is genuinely inconvenient?

---

*⚠️ This checklist is for informational purposes only — not legal advice.*
    """.strip()

    st.markdown(checklist_md)
    st.divider()

    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        st.download_button(
            "📥 Download Markdown",
            data=checklist_md,
            file_name="clearclause_checklist.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_md",
        )
    with col_dl2:
        st.download_button(
            "📥 Download TXT",
            data=checklist_md.replace("**", "").replace("##", "").replace("- [ ]", "[ ]"),
            file_name="clearclause_checklist.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl_txt",
        )
    with col_dl3:
        if st.button("📋 Copy to Clipboard", use_container_width=True, key="copy_clipboard"):
            st.toast("Copied to clipboard! *(wired in Phase 5)*")

st.divider()
st.warning(
    "⚠️ ClearClause is an informational tool — not legal advice. "
    "Always consult a qualified lawyer before signing any legally binding document.",
    icon=None,
)
