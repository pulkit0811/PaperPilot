from __future__ import annotations

from html import escape

import streamlit as st
from dotenv import load_dotenv

from paperpilot.llm import answer_question, generate_summary
from paperpilot.pdf_utils import Document, PdfProcessingError, extract_document
from paperpilot.retrieval import build_context, retrieve_chunks
from paperpilot.sample_data import sample_document

load_dotenv()

st.set_page_config(
    page_title="PaperPilot AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #f4f7ff; --muted: #99a5be; --panel: #131a2a; --line: rgba(160, 175, 210, .15); --blue: #5d8dff; --purple: #9a6cff; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 75% 0%, rgba(76, 98, 190, .15), transparent 28rem), #080c16; color: var(--ink); }
    [data-testid="stSidebar"] { background: #0d1320; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -.03em; }
    h1 { font-size: clamp(2.2rem, 5vw, 4.2rem) !important; line-height: 1.02 !important; margin-bottom: .7rem !important; }
    h2 { font-size: 1.45rem !important; }
    .brand { display: flex; align-items: center; gap: .7rem; margin-bottom: 2.8rem; }
    .brand-mark { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 12px; background: linear-gradient(135deg, #5d8dff, #9a6cff); box-shadow: 0 8px 24px rgba(93, 141, 255, .25); font-size: 1.3rem; }
    .brand-name { font: 700 1.12rem 'Space Grotesk', sans-serif; }
    .eyebrow { color: #87aaff; font-size: .76rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
    .hero-copy { color: var(--muted); max-width: 660px; font-size: 1.07rem; line-height: 1.65; }
    .hero { padding: 1.5rem 0 1.6rem; }
    .panel { background: rgba(19, 26, 42, .86); border: 1px solid var(--line); border-radius: 18px; padding: 1.1rem 1.2rem; }
    .metric { background: #101727; border: 1px solid var(--line); border-radius: 14px; padding: 1rem; }
    .metric-value { font: 700 1.55rem 'Space Grotesk', sans-serif; }
    .metric-label { color: var(--muted); font-size: .78rem; margin-top: .2rem; }
    .empty { text-align: center; padding: 4.8rem 1rem; border: 1px dashed rgba(143, 160, 200, .28); border-radius: 20px; background: rgba(19, 26, 42, .48); }
    .empty-icon { font-size: 2.2rem; margin-bottom: .6rem; }
    .empty p { color: var(--muted); max-width: 500px; margin: .5rem auto 0; line-height: 1.6; }
    .source-card { border: 1px solid var(--line); border-radius: 13px; padding: .75rem .9rem; background: rgba(11, 16, 28, .75); margin-top: .6rem; }
    .source-title { color: #a9c2ff; font-weight: 700; font-size: .8rem; }
    .source-text { color: #c2cbe0; font-size: .87rem; line-height: 1.5; margin-top: .35rem; }
    .answer-box { border-left: 3px solid #7798ff; background: rgba(93, 141, 255, .07); padding: 1rem 1.1rem; border-radius: 0 13px 13px 0; line-height: 1.7; }
    .history-user { color: #b5c9ff; font-weight: 600; font-size: .86rem; }
    .history-answer { color: #c5cddd; font-size: .88rem; line-height: 1.5; margin: .35rem 0 1rem; }
    .stButton > button, .stDownloadButton > button { border-radius: 10px; border: 1px solid rgba(130, 157, 255, .35); background: linear-gradient(135deg, rgba(93, 141, 255, .2), rgba(154, 108, 255, .2)); color: #f4f7ff; }
    .stButton > button:hover { border-color: #84a3ff; color: #fff; }
    [data-testid="stFileUploader"] { background: rgba(19, 26, 42, .7); border: 1px dashed rgba(130, 157, 255, .43); border-radius: 16px; padding: .35rem; }
    div[data-baseweb="tab-list"] { gap: 1.2rem; }
    button[data-baseweb="tab"] { color: var(--muted); }
    button[data-baseweb="tab"][aria-selected="true"] { color: #a8c2ff; }
    .stAlert { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    if "document" not in st.session_state:
        st.session_state.document = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "document_signature" not in st.session_state:
        st.session_state.document_signature = None


def set_document(document: Document, signature: str) -> None:
    if st.session_state.document_signature != signature:
        st.session_state.document = document
        st.session_state.document_signature = signature
        st.session_state.history = []
        st.session_state.summary = None


def render_sources(chunks: list) -> None:
    if not chunks:
        return
    st.markdown("**Sources used**")
    for chunk in chunks:
        st.markdown(
            f'<div class="source-card"><div class="source-title">Page {chunk.page_number}</div><div class="source-text">{escape(chunk.text)}</div></div>',
            unsafe_allow_html=True,
        )


def render_sidebar(document: Document | None) -> None:
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">✦</div><div class="brand-name">PaperPilot AI</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Workspace</div>', unsafe_allow_html=True)
        mode = st.radio("Input mode", ["Upload PDF", "Sample document"], label_visibility="collapsed")
        if mode == "Upload PDF":
            uploaded = st.file_uploader("Choose a PDF", type=["pdf"], help="PDF files up to 50 MB")
            if uploaded:
                raw = uploaded.getvalue()
                try:
                    parsed = extract_document(raw, filename=uploaded.name)
                    set_document(parsed, f"upload:{uploaded.name}:{len(raw)}")
                except PdfProcessingError as error:
                    st.error(str(error))
        else:
            if st.button("Load research sample", use_container_width=True):
                set_document(sample_document(), "sample:v1")
            st.caption("A small built-in research brief lets you explore the full flow without an API key.")
        st.divider()
        if document:
            st.markdown(f"**{document.filename}**")
            st.caption(f"{document.page_count} pages · {document.word_count:,} words")
            if document.scanned_pages:
                st.warning(f"{len(document.scanned_pages)} page(s) appear scanned or contain little text. OCR is not enabled.")
            if st.button("Clear workspace", use_container_width=True):
                st.session_state.document = None
                st.session_state.document_signature = None
                st.session_state.history = []
                st.session_state.summary = None
                st.rerun()
        else:
            st.caption("Your document stays in this session. Add a PDF or load the sample to begin.")
        st.divider()
        st.caption("Grounded answers · page-level citations · private session workspace")


def render_document_overview(document: Document) -> None:
    st.markdown("### Document overview")
    metric_columns = st.columns(3)
    metrics = [("Pages", document.page_count), ("Words", f"{document.word_count:,}"), ("Text coverage", f"{document.text_coverage:.0%}")]
    for column, (label, value) in zip(metric_columns, metrics):
        with column:
            st.markdown(f'<div class="metric"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    with st.expander("Preview extracted text", expanded=False):
        for page in document.pages[:5]:
            st.markdown(f"**Page {page.page_number}**")
            st.write(page.text or "No extractable text on this page.")


def render_summary(document: Document) -> None:
    st.markdown("### Summary")
    if st.button("Generate document summary", type="primary"):
        with st.spinner("Reading the document and identifying the important ideas..."):
            st.session_state.summary = generate_summary(document)
    if st.session_state.summary:
        summary = st.session_state.summary
        st.markdown(f'<div class="answer-box">{escape(summary.overview)}</div>', unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            st.markdown("**Key findings**")
            for finding in summary.key_findings:
                st.markdown(f"- {finding}")
        with right:
            st.markdown("**Takeaways**")
            for takeaway in summary.takeaways:
                st.markdown(f"- {takeaway}")
        render_sources(summary.sources)


def render_qa(document: Document) -> None:
    st.markdown("### Ask your document")
    question = st.text_area("Question", placeholder="What is the main conclusion, and what evidence supports it?", height=90, label_visibility="collapsed")
    ask = st.button("Ask PaperPilot", type="primary", use_container_width=True)
    if ask:
        if not question.strip():
            st.warning("Enter a question to search the document.")
            return
        with st.spinner("Searching relevant pages..."):
            chunks = retrieve_chunks(document, question)
        if not chunks:
            answer = "I couldn't find enough relevant information in this document to answer that question."
        else:
            context = build_context(chunks)
            with st.spinner("Writing a grounded answer..."):
                answer = answer_question(question, context)
        st.session_state.history.insert(0, {"question": question.strip(), "answer": answer, "sources": chunks})
    if st.session_state.history:
        latest = st.session_state.history[0]
        st.markdown('<div class="eyebrow">Latest answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-box">{escape(latest["answer"])}</div>', unsafe_allow_html=True)
        render_sources(latest["sources"])
        if len(st.session_state.history) > 1:
            st.markdown("### Conversation history")
            for item in st.session_state.history[1:]:
                with st.expander(item["question"]):
                    st.markdown(f'<div class="history-answer">{escape(item["answer"])}</div>', unsafe_allow_html=True)
                    render_sources(item["sources"])


def render_empty() -> None:
    st.markdown('<div class="empty"><div class="empty-icon">✦</div><h3>Your research desk is ready</h3><p>Upload a PDF or load the sample document. PaperPilot will extract its text, find the right pages, and answer from the document only.</p></div>', unsafe_allow_html=True)


init_state()
render_sidebar(st.session_state.document)

st.markdown('<div class="hero"><div class="eyebrow">Intelligent PDF research assistant</div><h1>Turn dense papers into<br><span style="background: linear-gradient(90deg, #7ea4ff, #bd8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">clear decisions.</span></h1><p class="hero-copy">Ask questions, surface key findings, and trace every answer back to the page that supports it.</p></div>', unsafe_allow_html=True)

document = st.session_state.document
if not document:
    render_empty()
else:
    render_document_overview(document)
    overview_tab, ask_tab = st.tabs(["Summary & insights", "Questions"])
    with overview_tab:
        render_summary(document)
    with ask_tab:
        render_qa(document)
