from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .pdf_utils import Document


STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "where", "which", "who", "why", "with"}


@dataclass(frozen=True)
class RetrievedChunk:
    page_number: int
    text: str
    score: float


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9'-]+", text.lower()) if token not in STOP_WORDS]


def _chunks_for_page(page_number: int, text: str, max_words: int = 110) -> list[RetrievedChunk]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max_words - 20
    for start in range(0, len(words), step):
        chunk_text = " ".join(words[start:start + max_words])
        chunks.append(RetrievedChunk(page_number, chunk_text, 0.0))
        if start + max_words >= len(words):
            break
    return chunks


def retrieve_chunks(document: Document, query: str, limit: int = 3, minimum_score: float = 0.05) -> list[RetrievedChunk]:
    query_terms = Counter(tokenize(query))
    if not query_terms:
        return []
    candidates = []
    for page in document.pages:
        for chunk in _chunks_for_page(page.page_number, page.text):
            terms = Counter(tokenize(chunk.text))
            overlap = sum(min(count, terms[term]) for term, count in query_terms.items())
            coverage = overlap / max(sum(query_terms.values()), 1)
            exact_phrase = query.lower().strip() in chunk.text.lower()
            score = coverage + (0.35 if exact_phrase else 0.0)
            if score >= minimum_score:
                candidates.append(RetrievedChunk(chunk.page_number, chunk.text, score))
    candidates.sort(key=lambda item: (-item.score, item.page_number))
    selected: list[RetrievedChunk] = []
    seen_pages: set[int] = set()
    for candidate in candidates:
        if candidate.page_number not in seen_pages or len(selected) < limit:
            selected.append(candidate)
            seen_pages.add(candidate.page_number)
        if len(selected) == limit:
            break
    return selected


def build_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[Page {chunk.page_number}]\n{chunk.text}" for chunk in chunks)
