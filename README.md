# PaperPilot AI — Intelligent PDF Research Assistant

PaperPilot is a Streamlit application for asking grounded questions about PDF documents, generating summaries, and tracing answers back to source pages. It uses PyMuPDF for local text extraction and an optional LLM API for natural-language answers.

## Features

- PDF upload validation with a five-minute local research workflow
- PyMuPDF page extraction and document preview
- Page-aware local keyword retrieval
- Grounded question answering with source excerpts
- Clear no-answer behavior when relevant text is not found
- Document summary with key findings and takeaways
- Built-in sample document mode
- Current-session conversation history
- Scanned-PDF detection with an explicit OCR-unavailable message
- Dark responsive interface with loading states and error handling

## Setup

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add an API key to `.env` if you want LLM-generated language:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

The sample document and extractive fallback work without an API key. API keys are read only from environment variables and are never stored in the application.

## Run

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, select **Sample document** in the sidebar, or upload a PDF.

## Test

```powershell
python -m pytest -q
```

The tests cover PyMuPDF extraction, invalid and scanned PDF handling, retrieval ranking, and page citation context.

## OCR limitation

PaperPilot does not run OCR. A PDF with no selectable text is rejected with a message explaining that OCR is unavailable. PDFs with mixed content are accepted, and pages with very little extracted text are flagged in the sidebar.
