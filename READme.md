# 📜 ClearClause — GenAI Legal Document Simplifier & Risk Analyzer

ClearClause is an AI-powered legal document analysis and simplification system designed to help users quickly understand complex legal contracts, terms of service, NDAs, and privacy policies. 

Using **LangGraph** agentic workflows, **HuggingFace** embeddings, **FAISS** vector storage, and **OpenRouter** LLMs, ClearClause translates dense legalese into plain English, highlights hidden risks, categorizes clauses into bite-sized **Clause Cards**, enables interactive document Q&A, and performs side-by-side contract comparisons.

---

## 🚀 Key Features

* **Multi-Format Ingestion**: Process legal documents via **PDF**, **Web URL**, or **Direct Text** input.
* **Vectorless Page-Tree Indexing (PDFs)**: Parses PDF structures by page and section hierarchy to preserve exact page context.
* **FAISS + HuggingFace Vector Store (URLs & Text)**: Semantic search chunking using `all-MiniLM-L6-v2` embeddings for fast retrieval.
* **Structured Clause Cards**: Automatically extracts key clauses and highlights:
  * **Title & Plain-English Translation**
  * **Priority Level** (🔴 *High / Red Flag*, 🟡 *Medium*, 🔵 *Low / Informational*)
  * **Key Takeaway & Follow-Up Questions**
* **Interactive Document Q&A**: Ask natural language questions about your uploaded document with grounded context citations.
* **Document Comparison**: Compare two contracts side-by-side to highlight differences, risk variations, and key clause discrepancies.
* **Review Checklist & Risk Summary**: Instant executive overview of red flags, missing standard protections, and overall risk rating.

---

## 🛠️ Tech Stack & Architecture

* **Frontend**: Streamlit multi-page UI custom-themed for high readability.
* **Orchestration**: LangGraph for stateful agent workflows and control flow.
* **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (runs locally, 0 API cost).
* **Vector Store**: FAISS (`faiss-cpu`) stored in session memory for zero data persistence.
* **Document Parsing**: PyMuPDF (`fitz`) for PDFs and Trafilatura for Web URLs with SSRF protection.
* **LLM Engine**: OpenRouter API integration supporting open-weights and commercial models.

---

## 📂 Repository Structure

```text
ClearClause/
├── backend/
│   ├── agents/          # LangGraph nodes (ingest, extract, card builder, QA, comparison)
│   ├── graphs/          # LangGraph graph definitions (analysis, QA, comparison)
│   ├── integrations/    # PyMuPDF, Trafilatura, HuggingFace embeddings, FAISS store
│   ├── models/          # Pydantic & TypedDict schemas
│   ├── prompts/         # Structured LLM prompt templates
│   └── services/        # Service layer orchestrators
├── frontend/
│   ├── Home.py          # Main landing page
│   ├── pages/
│   │   ├── 1_Understand_Document.py   # Document upload, Clause Cards & Q&A
│   │   └── 2_Compare_Documents.py      # Contract comparison dashboard
│   └── ui/              # Custom design system, CSS styles & theme components
├── tests/               # Pytest unit and integration test suite
├── .env.example         # Template for environment variables
├── pyproject.toml       # Ruff linter & Pytest configuration
├── requirements.txt     # Python dependencies
└── READme.md            # Project documentation
```

---

## ⚙️ Quickstart & How to Run

### 1. Prerequisites

* **Python 3.11+** installed on your system.
* An **OpenRouter API Key** (or compatible LLM provider key).

---

### 2. Setup Virtual Environment

Navigate to the project directory:

```bash
cd ClearClause
```

Create a virtual environment (e.g. `my_venv`):

* **Windows (PowerShell/CMD):**
  ```powershell
  python -m venv my_venv
  my_venv\Scripts\activate
  ```

* **macOS / Linux:**
  ```bash
  python3 -m venv my_venv
  source my_venv/bin/activate
  ```

---

### 3. Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

---

### 4. Configure API Key

Create or edit your Streamlit secrets file at `frontend/.streamlit/secrets.toml`:

```toml
OPENROUTER_API_KEY = "your-openrouter-api-key-here"
```

*(Alternatively, set `OPENROUTER_API_KEY` as an environment variable in your terminal or `.env` file).*

---

### 5. Launch the Web Application

Run the Streamlit application from the project root:

```bash
streamlit run frontend/Home.py
```

The web interface will automatically open in your browser at `http://localhost:8501`.

---

## 🧪 Running Tests

Run unit and integration tests using `pytest`:

```bash
pytest tests/
```

To run linting checks with `ruff`:

```bash
ruff check .
```

---

## ⚠️ Legal Disclaimer

> **IMPORTANT**: ClearClause is an AI-powered document analysis tool built solely for educational and informational purposes. **ClearClause DOES NOT provide legal advice.** It is not a substitute for professional legal counsel from a qualified attorney. Always consult a licensed lawyer before signing or agreeing to any legal contract.
