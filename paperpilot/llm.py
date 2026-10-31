from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .pdf_utils import Document
from .retrieval import RetrievedChunk, build_context, retrieve_chunks


@dataclass(frozen=True)
class SummaryResult:
    overview: str
    key_findings: list[str]
    takeaways: list[str]
    sources: list[RetrievedChunk]


def _client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=key)


def _model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _call_llm(system: str, user: str) -> str | None:
    client = _client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(model=_model(), temperature=0.1, max_tokens=700, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def answer_question(question: str, context: str) -> str:
    if not context.strip():
        return "I couldn't find enough relevant information in this document to answer that question."
    system = "You answer questions using only the supplied document excerpts. If the excerpts do not support an answer, say exactly that you could not find the answer in the document. Do not use outside knowledge. Keep citations in the form [Page N] only when that page marker appears in the excerpts."
    prompt = f"Document excerpts:\n{context}\n\nQuestion: {question}\n\nAnswer concisely with supporting page citations."
    result = _call_llm(system, prompt)
    if result:
        return _sanitize_citations(result, context)
    return _extractive_answer(question, context)


def _sanitize_citations(text: str, context: str) -> str:
    allowed_pages = {int(page) for page in re.findall(r"\[Page\s+(\d+)\]", context)}

    def replace(match: re.Match[str]) -> str:
        page = int(match.group(1))
        return match.group(0) if page in allowed_pages else ""

    return re.sub(r"\[Page\s+(\d+)\]", replace, text)


def _extractive_answer(question: str, context: str) -> str:
    query_terms = set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9'-]+", question.lower()))
    sentences = re.split(r"(?<=[.!?])\s+", context.replace("\n", " "))
    ranked = sorted(sentences, key=lambda sentence: len(query_terms.intersection(set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9'-]+", sentence.lower())))), reverse=True)
    useful = [sentence.strip() for sentence in ranked if sentence.strip()][:2]
    if not useful:
        return "I couldn't find enough relevant information in this document to answer that question."
    return " ".join(useful)


def generate_summary(document: Document) -> SummaryResult:
    chunks = retrieve_chunks(document, "main purpose findings results evidence conclusion implications", limit=5, minimum_score=0.0)
    if not chunks:
        chunks = [RetrievedChunk(page.page_number, page.text, 0.0) for page in document.pages if page.text][:5]
    context = build_context(chunks)
    system = "Create a concise summary using only the supplied document excerpts. Return exactly three sections titled Overview, Key findings, and Takeaways. Use bullets in the last two sections. Never invent facts or page numbers."
    prompt = f"Document excerpts:\n{context}"
    result = _call_llm(system, prompt)
    if result:
        overview, findings, takeaways = _parse_summary(result)
        return SummaryResult(overview, findings, takeaways, chunks)
    return _fallback_summary(document, chunks)


def _parse_summary(text: str) -> tuple[str, list[str], list[str]]:
    sections = re.split(r"\n\s*(?=(?:Overview|Key findings|Takeaways)\s*:?)", text, flags=re.IGNORECASE)
    overview = text.strip()
    findings: list[str] = []
    takeaways: list[str] = []
    for section in sections:
        lower = section.lower()
        cleaned = re.sub(r"^(overview|key findings|takeaways)\s*:? *", "", section.strip(), flags=re.IGNORECASE).strip()
        bullets = [re.sub(r"^[-*•]\s*", "", line).strip() for line in cleaned.splitlines() if re.match(r"^\s*[-*•]", line)]
        if "key findings" in lower:
            findings = bullets or [cleaned]
        elif "takeaways" in lower:
            takeaways = bullets or [cleaned]
        elif "overview" in lower:
            overview = cleaned
    return overview, findings[:5], takeaways[:5]


def _fallback_summary(document: Document, chunks: list[RetrievedChunk]) -> SummaryResult:
    nonempty = [page for page in document.pages if page.text]
    overview = f"This document contains {document.page_count} page(s) and approximately {document.word_count:,} words of selectable text. The extractive summary below is based on the most information-dense passages."
    findings = [chunk.text[:220].rstrip() + ("…" if len(chunk.text) > 220 else "") for chunk in chunks[:3]]
    takeaways = [f"Review Page {chunk.page_number} for the supporting passage." for chunk in chunks[:3]]
    if not findings and nonempty:
        findings = [nonempty[0].text[:220]]
        takeaways = [f"Review Page {nonempty[0].page_number} for the available text."]
    return SummaryResult(overview, findings, takeaways, chunks)
