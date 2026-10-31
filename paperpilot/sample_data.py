from .pdf_utils import Document, PageText


SAMPLE_TEXT = """PaperPilot Research Brief

Page 1
Remote knowledge work has changed how teams share expertise. This research brief examines a six-month study of 240 employees across 18 teams. The study compares a searchable internal knowledge base with informal chat-only workflows.

Page 2
Teams using a structured knowledge base resolved recurring support questions 31 percent faster than teams using chat alone. Participants also reported fewer duplicated investigations and stronger confidence that decisions could be revisited later. The largest improvement appeared in teams with clear ownership for updating documents.

Page 3
The study found that a knowledge base did not improve outcomes when information was outdated or difficult to search. Successful teams used short decision records, consistent labels, and monthly review sessions. The authors recommend measuring freshness and search success alongside adoption.

Page 4
The main conclusion is that searchable documentation works best as a maintained system rather than a passive archive. The evidence supports investing in information design, ownership, and review habits. The study is observational, so the results show an association rather than proof of causation."""


def sample_document() -> Document:
    pages = [
        PageText(1, "Remote knowledge work has changed how teams share expertise. This research brief examines a six-month study of 240 employees across 18 teams. The study compares a searchable internal knowledge base with informal chat-only workflows."),
        PageText(2, "Teams using a structured knowledge base resolved recurring support questions 31 percent faster than teams using chat alone. Participants also reported fewer duplicated investigations and stronger confidence that decisions could be revisited later. The largest improvement appeared in teams with clear ownership for updating documents."),
        PageText(3, "The study found that a knowledge base did not improve outcomes when information was outdated or difficult to search. Successful teams used short decision records, consistent labels, and monthly review sessions. The authors recommend measuring freshness and search success alongside adoption."),
        PageText(4, "The main conclusion is that searchable documentation works best as a maintained system rather than a passive archive. The evidence supports investing in information design, ownership, and review habits. The study is observational, so the results show an association rather than proof of causation."),
    ]
    return Document("paperpilot-research-brief.pdf", pages, [])
