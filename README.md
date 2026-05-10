# LegalLens

LegalLens is a multilingual AI legal document assistant that helps users extract, analyze, simplify, and question legal documents. It combines OCR, semantic retrieval, and Gemini-powered language generation to turn dense legal text into clearer summaries, clause explanations, risk alerts, and form-filling guidance.

## Features

- Upload legal documents as PDFs or images.
- Extract printed and handwritten text using Tesseract OCR with optional Gemini Vision fallback.
- Generate concise legal document summaries.
- Ask document-specific questions using retrieval over extracted clauses.
- Browse and simplify individual clauses in plain language.
- Detect potentially risky clauses, penalties, and unfair provisions.
- Translate responses into supported Indic languages.
- Get step-by-step help for legal form fields and instructions.

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- Tesseract OCR
- PyMuPDF
- Pillow
- FAISS / semantic retrieval

## Project Structure

```text
LegalLens/
|-- app.py
|-- ocr.py
|-- utils/
|   |-- __init__.py
|   |-- language.py
|   |-- llm.py
|   |-- ocr.py
|   `-- rag_engine.py
|-- README.md
|-- requirements.txt
|-- .env.example
`-- .gitignore
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username/legallens-ai-legal-assistant.git
cd legallens-ai-legal-assistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file from `.env.example` and add your Gemini API key:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

## Resume Summary

- Built LegalLens, an AI-powered legal document assistant using Python and Gemini API to analyze, summarize, and simplify complex legal documents.
- Improved document query workflows using context-aware retrieval and structured clause segmentation.
- Integrated OCR support for PDFs, scanned images, and handwritten legal documents with multilingual output support.

## Disclaimer

LegalLens is designed for educational and productivity support. It does not provide legal advice and should not replace consultation with a qualified legal professional.
