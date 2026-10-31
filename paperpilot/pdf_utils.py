from __future__ import annotations

from dataclasses import dataclass

import pymupdf


class PdfProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class Document:
    filename: str
    pages: list[PageText]
    scanned_pages: list[int]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def word_count(self) -> int:
        return sum(len(page.text.split()) for page in self.pages)

    @property
    def text_coverage(self) -> float:
        if not self.pages:
            return 0.0
        return sum(bool(page.text.strip()) for page in self.pages) / len(self.pages)


def extract_document(pdf_bytes: bytes, filename: str = "document.pdf") -> Document:
    if not pdf_bytes:
        raise PdfProcessingError("The uploaded file is empty. Choose a readable PDF and try again.")
    if len(pdf_bytes) > 50 * 1024 * 1024:
        raise PdfProcessingError("This PDF is larger than the 50 MB limit.")
    try:
        pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as error:
        raise PdfProcessingError("This file is not a valid PDF or could not be opened.") from error
    if pdf.page_count == 0:
        pdf.close()
        raise PdfProcessingError("This PDF has no pages.")
    pages: list[PageText] = []
    scanned_pages: list[int] = []
    try:
        for index, page in enumerate(pdf, start=1):
            text = " ".join(page.get_text("text").split())
            pages.append(PageText(index, text))
            if len(text) < 20:
                scanned_pages.append(index)
    finally:
        pdf.close()
    if not any(page.text for page in pages):
        raise PdfProcessingError("No selectable text was found. This looks like a scanned PDF; OCR is not available in this version.")
    return Document(filename=filename or "document.pdf", pages=pages, scanned_pages=scanned_pages)
