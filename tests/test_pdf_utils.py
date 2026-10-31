import pymupdf
import pytest

from paperpilot.pdf_utils import PdfProcessingError, extract_document


def make_pdf(*page_texts: str) -> bytes:
    document = pymupdf.open()
    for text in page_texts:
        page = document.new_page()
        page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def test_extract_document_reads_text_and_pages():
    document = extract_document(make_pdf("First page content", "Second page content"), "research.pdf")
    assert document.filename == "research.pdf"
    assert document.page_count == 2
    assert document.pages[0].page_number == 1
    assert "First page" in document.pages[0].text
    assert document.word_count == 6


def test_extract_document_rejects_invalid_pdf():
    with pytest.raises(PdfProcessingError, match="valid PDF"):
        extract_document(b"not a pdf")


def test_extract_document_explains_scanned_pdf():
    document = pymupdf.open()
    document.new_page()
    data = document.tobytes()
    document.close()
    with pytest.raises(PdfProcessingError, match="OCR"):
        extract_document(data)
