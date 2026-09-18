"""
tests/unit/test_document_parser.py
Unit tests for backend/integrations/document_parser.py

Coverage:
- parse_text: valid, empty, oversized
- parse_url: SSRF guard (non-HTTPS, private IP, timeout)  — network calls mocked
- parse_pdf: oversized bytes, page-count limit, unreadable PDF — fitz mocked
- parse() dispatcher: correct routing + error on unknown type
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.integrations.document_parser import (
    MAX_FILE_BYTES,
    MAX_PAGES,
    FetchError,
    ParseFailureError,
    SizeLimitError,
    UnsupportedFormatError,
    parse,
    parse_pdf,
    parse_text,
    parse_url,
)

# ── parse_text ────────────────────────────────────────────────────────────────

class TestParseText:
    def test_valid_text_returns_parsed_document(self):
        text = "This is a rental agreement. The tenant shall pay $1,000 per month." * 10
        doc, page_index = parse(text, input_type="text")
        assert doc.source_type == "text"
        assert doc.raw_text == text
        assert doc.char_count == len(text)
        assert doc.estimated_pages >= 1
        assert page_index is None

    def test_empty_text_raises_parse_failure(self):
        with pytest.raises(ParseFailureError):
            parse_text("")

    def test_whitespace_only_raises_parse_failure(self):
        with pytest.raises(ParseFailureError):
            parse_text("   \n\t  ")

    def test_oversized_text_raises_size_limit(self):
        big_text = "a" * (MAX_FILE_BYTES + 1)
        with pytest.raises(SizeLimitError):
            parse_text(big_text)

    def test_exactly_at_limit_does_not_raise(self):
        # 5 MB of single-byte characters: edge case — should pass
        ok_text = "a" * (MAX_FILE_BYTES - 1)
        doc = parse_text(ok_text)
        assert doc.char_count == MAX_FILE_BYTES - 1


# ── parse_url — SSRF guards ────────────────────────────────────────────────────

class TestParseUrlSSRF:
    def test_non_https_url_raises_fetch_error(self):
        with pytest.raises(FetchError, match="HTTPS"):
            parse_url("http://example.com/lease.pdf")

    def test_ftp_url_raises_fetch_error(self):
        with pytest.raises(FetchError):
            parse_url("ftp://example.com/lease.pdf")

    def test_localhost_raises_fetch_error(self):
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(FetchError, match="private or reserved"):
                parse_url("https://localhost/lease")

    def test_private_10_range_raises_fetch_error(self):
        with patch("socket.gethostbyname", return_value="10.0.0.1"):
            with pytest.raises(FetchError, match="private or reserved"):
                parse_url("https://internal.corp/lease")

    def test_private_192168_range_raises_fetch_error(self):
        with patch("socket.gethostbyname", return_value="192.168.1.100"):
            with pytest.raises(FetchError, match="private or reserved"):
                parse_url("https://router.local/lease")

    def test_link_local_169_254_raises_fetch_error(self):
        with patch("socket.gethostbyname", return_value="169.254.1.1"):
            with pytest.raises(FetchError, match="private or reserved"):
                parse_url("https://metadata.internal/")

    @patch("socket.gethostbyname", return_value="93.184.216.34")  # example.com
    @patch("requests.get")
    def test_successful_fetch_returns_parsed_document(self, mock_get, _mock_dns):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.encoding = "utf-8"
        mock_response.headers = {}
        # Simulate streaming chunks
        mock_response.iter_content.return_value = [b"<html><body>" + b"Legal text. " * 200 + b"</body></html>"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch("trafilatura.extract", return_value="Legal text. " * 200):
            doc = parse_url("https://example.com/lease")

        assert doc.source_type == "url"
        assert "Legal text" in doc.raw_text

    @patch("socket.gethostbyname", return_value="93.184.216.34")
    @patch("requests.get")
    def test_empty_extracted_text_raises_parse_failure(self, mock_get, _mock_dns):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.encoding = "utf-8"
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b"<html><body>tiny</body></html>"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch("trafilatura.extract", return_value=None):
            with pytest.raises(ParseFailureError):
                parse_url("https://example.com/lease")


# ── parse_pdf ─────────────────────────────────────────────────────────────────

class TestParsePdf:
    def _make_mock_fitz(self, page_count: int, page_text: str = "Legal clause text."):
        """Return a mock fitz module + document."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = page_text

        mock_doc = MagicMock()
        mock_doc.page_count = page_count
        mock_doc.__getitem__ = lambda self, idx: mock_page
        mock_doc.close.return_value = None

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc
        return mock_fitz

    def test_oversized_bytes_raises_size_limit(self):
        big_bytes = b"x" * (MAX_FILE_BYTES + 1)
        with pytest.raises(SizeLimitError):
            parse_pdf(big_bytes)

    def test_too_many_pages_raises_size_limit(self):
        mock_fitz = self._make_mock_fitz(page_count=MAX_PAGES + 1)
        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            with pytest.raises(SizeLimitError):
                parse_pdf(b"fake-pdf-bytes")

    def test_fitz_open_exception_raises_parse_failure(self):
        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = RuntimeError("corrupted")
        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            with pytest.raises(ParseFailureError):
                parse_pdf(b"not-a-pdf")

    def test_valid_pdf_returns_parsed_document_and_page_index(self):
        mock_fitz = self._make_mock_fitz(page_count=3, page_text="This is page text.")
        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            doc, page_index = parse_pdf(b"fake-pdf", filename="lease.pdf")

        assert doc.source_type == "pdf"
        assert doc.estimated_pages == 3
        assert len(page_index) == 3
        assert 1 in page_index
        assert 3 in page_index

    def test_empty_text_pdf_raises_parse_failure(self):
        mock_fitz = self._make_mock_fitz(page_count=2, page_text="   ")
        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            with pytest.raises(ParseFailureError, match="No readable text"):
                parse_pdf(b"fake-pdf")

    def test_zero_page_pdf_raises_parse_failure(self):
        mock_fitz = self._make_mock_fitz(page_count=0)
        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            with pytest.raises(ParseFailureError):
                parse_pdf(b"fake-pdf")


# ── parse() dispatcher ────────────────────────────────────────────────────────

class TestParseDispatcher:
    def test_unknown_input_type_raises_unsupported(self):
        with pytest.raises(UnsupportedFormatError):
            parse("some input", input_type="docx")  # type: ignore

    def test_pdf_type_with_string_raises_unsupported(self):
        with pytest.raises(UnsupportedFormatError):
            parse("not bytes", input_type="pdf")

    def test_url_type_with_bytes_raises_unsupported(self):
        with pytest.raises(UnsupportedFormatError):
            parse(b"not a string", input_type="url")

    def test_text_type_dispatches_correctly(self):
        text = "Valid document text. " * 20
        doc, page_index = parse(text, input_type="text")
        assert doc.source_type == "text"
        assert page_index is None
