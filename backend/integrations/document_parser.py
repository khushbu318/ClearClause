"""
backend/integrations/document_parser.py
Data Access Layer — document ingestion for all three input types.

Security considerations enforced here:
- PDF: 5 MB limit + page count limit enforced before parsing
- URL: HTTPS-only, private-IP blocking, 10s timeout, 5 MB response cap
- All: try/except wrapping with typed exceptions; no raw stack traces propagated
"""

from __future__ import annotations

import io
import math
import re
import socket
import urllib.parse
from typing import Literal

import requests

from backend.models.document import ParsedDocument

# ── Custom exceptions ──────────────────────────────────────────────────────────

class DocumentParserError(Exception):
    """Base for all parser errors."""


class UnsupportedFormatError(DocumentParserError):
    """File type not supported."""


class SizeLimitError(DocumentParserError):
    """Document exceeds size or page-count limit."""


class FetchError(DocumentParserError):
    """URL could not be fetched (network, SSRF guard, or non-200 response)."""


class ParseFailureError(DocumentParserError):
    """Document could not be parsed (corrupted, encrypted, etc.)."""


# ── Constants ─────────────────────────────────────────────────────────────────

MAX_FILE_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_PAGES = 25
MAX_URL_RESPONSE_BYTES = 5 * 1024 * 1024
URL_TIMEOUT_SECONDS = 10

# Private / loopback IP ranges blocked for SSRF mitigation
_BLOCKED_IP_PREFIXES = (
    "127.",
    "10.",
    "192.168.",
    "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.",
    "172.28.", "172.29.", "172.30.", "172.31.",
    "169.254.",  # link-local
    "0.",
    "::1",
    "fc00:", "fd",
)


# ── SSRF guard ─────────────────────────────────────────────────────────────────

def _assert_safe_url(url: str) -> None:
    """Raise FetchError if the URL fails SSRF safety checks."""
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme != "https":
        raise FetchError(f"Only HTTPS URLs are accepted (got '{parsed.scheme}://').")

    hostname = parsed.hostname
    if hostname is None:
        raise FetchError("Could not determine hostname from URL.")

    # Resolve to IP and check against blocked ranges
    try:
        ip_str = socket.gethostbyname(hostname)
    except socket.gaierror as exc:
        raise FetchError(f"Could not resolve hostname '{hostname}': {exc}") from exc

    for prefix in _BLOCKED_IP_PREFIXES:
        if ip_str.startswith(prefix):
            raise FetchError(
                f"URL resolves to a private or reserved IP address ({ip_str}), which is not permitted."
            )


# ── PDF parser ─────────────────────────────────────────────────────────────────

def parse_pdf(
    file_bytes: bytes,
    filename: str = "uploaded.pdf",
) -> tuple[ParsedDocument, dict[int, str]]:
    """Parse a PDF from raw bytes.

    Returns:
        (ParsedDocument, page_index)
        page_index: {page_number (1-indexed): page_text}

    Raises:
        SizeLimitError: exceeds 5 MB or 25 pages
        UnsupportedFormatError: not a valid PDF
        ParseFailureError: PyMuPDF cannot read the file
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PyMuPDF (fitz) is required: pip install pymupdf") from exc

    if len(file_bytes) > MAX_FILE_BYTES:
        mb = len(file_bytes) / (1024 * 1024)
        raise SizeLimitError(
            f"File size {mb:.2f} MB exceeds the 5 MB limit. "
            "Try extracting the relevant pages and uploading a smaller file."
        )

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ParseFailureError(
            f"Could not open the PDF — it may be corrupted, password-protected, "
            f"or an image-only scan. Try pasting the text instead. (Detail: {exc})"
        ) from exc

    page_count = doc.page_count
    if page_count > MAX_PAGES:
        raise SizeLimitError(
            f"Document has {page_count} pages, which exceeds the ~{MAX_PAGES}-page limit. "
            "Try uploading only the relevant sections."
        )
    if page_count == 0:
        raise ParseFailureError("The PDF appears to have no readable pages.")

    page_index: dict[int, str] = {}
    all_text_parts: list[str] = []

    for page_num in range(page_count):
        page = doc[page_num]
        text = page.get_text("text")  # type: ignore[attr-defined]
        page_index[page_num + 1] = text  # 1-indexed
        all_text_parts.append(text)

    doc.close()

    raw_text = "\n\n".join(all_text_parts)
    if not raw_text.strip():
        raise ParseFailureError(
            "No readable text was found in this PDF. "
            "It may be an image-only scan (OCR not supported). Try pasting the text instead."
        )

    parsed = ParsedDocument.from_text(
        text=raw_text,
        source_type="pdf",
        source_identifier=filename,
        page_count=page_count,
    )
    return parsed, page_index


# ── URL parser ─────────────────────────────────────────────────────────────────

def parse_url(url: str) -> ParsedDocument:
    """Fetch and extract clean text from a public URL.

    Uses trafilatura for article/main-content extraction.
    SSRF-guarded: HTTPS-only, private-IP blocked, 10s timeout, 5 MB cap.

    Raises:
        FetchError: SSRF check failed, network error, or non-2xx response
        SizeLimitError: response body exceeds 5 MB
        ParseFailureError: trafilatura could not extract usable text
    """
    try:
        import trafilatura
    except ImportError as exc:
        raise ImportError("trafilatura is required: pip install trafilatura") from exc

    _assert_safe_url(url)

    try:
        response = requests.get(
            url,
            timeout=URL_TIMEOUT_SECONDS,
            headers={"User-Agent": "ClearClause/1.0 (legal-document-reader)"},
            stream=True,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise FetchError(
            f"The request to '{url}' timed out after {URL_TIMEOUT_SECONDS}s. "
            "Try a different URL or paste the text directly."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise FetchError(f"Could not fetch '{url}': {exc}") from exc

    # Enforce size cap on streaming response
    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_URL_RESPONSE_BYTES:
        raise SizeLimitError(
            f"The response from '{url}' would exceed the 5 MB limit. "
            "Try pasting the relevant text directly."
        )

    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=65536):
        total += len(chunk)
        if total > MAX_URL_RESPONSE_BYTES:
            raise SizeLimitError(
                f"Response from '{url}' exceeded the 5 MB limit mid-download. "
                "Try pasting the relevant text directly."
            )
        chunks.append(chunk)

    html_bytes = b"".join(chunks)
    html_str = html_bytes.decode(response.encoding or "utf-8", errors="replace")

    extracted = trafilatura.extract(
        html_str,
        include_tables=True,
        include_links=False,
        no_fallback=False,
    )

    if not extracted or len(extracted.strip()) < 100:
        raise ParseFailureError(
            f"Could not extract readable text from '{url}'. "
            "The page may require login, be mostly images, or be JavaScript-rendered. "
            "Try pasting the text directly."
        )

    return ParsedDocument.from_text(
        text=extracted,
        source_type="url",
        source_identifier=url,
    )


# ── Plain text parser ──────────────────────────────────────────────────────────

def parse_text(text: str) -> ParsedDocument:
    """Validate and wrap pasted plain text.

    Raises:
        SizeLimitError: text is too long (rough 5 MB proxy)
        ParseFailureError: text is effectively empty
    """
    if not text or not text.strip():
        raise ParseFailureError("No text was provided. Please paste your document text.")

    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise SizeLimitError(
            "The pasted text exceeds the 5 MB limit. "
            "Try pasting only the relevant sections."
        )

    return ParsedDocument.from_text(
        text=text,
        source_type="text",
        source_identifier="pasted_text",
    )


# ── Unified dispatcher ─────────────────────────────────────────────────────────

def parse(
    raw_input: bytes | str,
    input_type: Literal["pdf", "url", "text"],
    filename: str = "uploaded.pdf",
) -> tuple[ParsedDocument, dict[int, str] | None]:
    """Unified entry point — dispatches to the correct parser.

    Returns:
        (ParsedDocument, page_index | None)
        page_index is only populated for PDF inputs.

    Raises:
        DocumentParserError subclasses — never raw exceptions.
    """
    if input_type == "pdf":
        if not isinstance(raw_input, bytes):
            raise UnsupportedFormatError("PDF input must be raw bytes.")
        return parse_pdf(raw_input, filename=filename)

    elif input_type == "url":
        if not isinstance(raw_input, str):
            raise UnsupportedFormatError("URL input must be a string.")
        return parse_url(raw_input), None

    elif input_type == "text":
        if not isinstance(raw_input, str):
            raise UnsupportedFormatError("Text input must be a string.")
        return parse_text(raw_input), None

    else:
        raise UnsupportedFormatError(f"Unknown input_type '{input_type}'.")
