from paperpilot.pdf_utils import Document, PageText
from paperpilot.llm import _sanitize_citations
from paperpilot.retrieval import build_context, retrieve_chunks


def test_retrieval_returns_real_page_citations():
    document = Document("test.pdf", [PageText(1, "The study measured response time."), PageText(2, "The result was a 31 percent improvement.")], [])
    chunks = retrieve_chunks(document, "What was the result?")
    assert chunks
    assert chunks[0].page_number == 2
    assert build_context(chunks).startswith("[Page 2]")


def test_retrieval_returns_no_citation_for_unrelated_question():
    document = Document("test.pdf", [PageText(1, "The study measured response time."), PageText(2, "The result was a 31 percent improvement.")], [])
    assert retrieve_chunks(document, "What is the weather in Delhi?") == []


def test_citation_sanitizer_removes_pages_not_in_context():
    answer = _sanitize_citations("Supported [Page 2], unsupported [Page 99].", "[Page 2]\nEvidence")
    assert answer == "Supported [Page 2], unsupported ."
