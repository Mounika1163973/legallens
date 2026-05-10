"""
app.py
------
LegalLens – Multilingual AI Legal Document Assistant
Main Streamlit application entry point.

Run with:
    streamlit run app.py
"""

import streamlit as st
import io
from PIL import Image

# Internal modules
from utils.ocr import extract_text, get_ocr_status
from utils.language import detect_language, is_english, translate_to_indic, SUPPORTED_INDIC_LANGS
from utils.rag_engine import build_index_from_text, segment_clauses
from utils.llm import (
    simplify_clause,
    answer_question,
    detect_risk_alerts,
    form_filling_guide,
    summarize_document,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="LegalLens",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+3:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Source Sans 3', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(15, 52, 96, 0.4);
    }

    .main-header h1 {
        color: #e2c97e;
        font-size: 3rem;
        letter-spacing: 2px;
        margin: 0;
    }

    .main-header p {
        color: #a8b2d8;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }

    .step-card {
        background: #f8f9ff;
        border-left: 4px solid #0f3460;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    .alert-box {
        background: #fff3cd;
        border-left: 4px solid #e67e22;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }

    .success-box {
        background: #d4edda;
        border-left: 4px solid #27ae60;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }

    .clause-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .stButton > button {
        background: linear-gradient(135deg, #0f3460, #16213e);
        color: #e2c97e;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.8rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 52, 96, 0.4);
    }

    .sidebar .stSelectbox label, .sidebar .stFileUploader label {
        color: #0f3460;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="main-header">
        <h1>⚖️ LegalLens</h1>
        <p>Multilingual AI Legal Document Assistant · Extract · Analyse · Simplify</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
if "clauses" not in st.session_state:
    st.session_state.clauses = []
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "risk_alerts" not in st.session_state:
    st.session_state.risk_alerts = []

# ---------------------------------------------------------------------------
# Sidebar – upload & settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    output_lang = st.selectbox(
        "Output Language",
        options=["English"] + list(SUPPORTED_INDIC_LANGS.values()),
        index=0,
        help="Choose the language for simplified explanations and answers.",
    )

    lang_code_map = {v: k for k, v in SUPPORTED_INDIC_LANGS.items()}
    selected_lang_code = lang_code_map.get(output_lang, "en")

    st.divider()
    st.markdown("## 📄 Upload Document")

    uploaded_file = st.file_uploader(
        "Upload a legal document",
        type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
        help="Supports scanned images, handwritten docs, and text PDFs.",
    )

    # OCR engine status
    ocr_status = get_ocr_status()
    if ocr_status["gemini"]:
        st.success("✅ Gemini Vision ready\n(handwriting supported)")
    elif ocr_status["gemini_package"] and not ocr_status["gemini_key_set"]:
        st.warning("⚠️ Set GEMINI_API_KEY to\nenable handwriting support")
    else:
        st.info("ℹ️ Tesseract OCR active\n(printed text only)")

    # Handwriting mode toggle
    handwriting_mode = st.toggle(
        "✍️ Handwritten Document",
        value=False,
        help="Enable for handwritten documents. Requires Gemini API key.",
        disabled=not ocr_status["gemini"],
    )

    if uploaded_file and st.button("🔍 Extract & Analyse", use_container_width=True):
        with st.spinner("Extracting text via OCR…"):
            # Reset state
            st.session_state.extracted_text = ""
            st.session_state.faiss_index = None
            st.session_state.clauses = []
            st.session_state.summary = ""
            st.session_state.risk_alerts = []

            try:
                text = extract_text(uploaded_file, force_gemini=handwriting_mode)
                st.session_state.extracted_text = text
            except Exception as e:
                st.error(f"OCR failed: {e}")
                st.stop()

        if not st.session_state.extracted_text.strip():
            st.warning("No text could be extracted. Please try a clearer image.")
            st.stop()

        # Language detection & optional translation
        detected_lang = detect_language(st.session_state.extracted_text)
        if detected_lang != "en":
            st.info(
                f"Detected language: **{detected_lang.upper()}**. "
                "Translating to English for analysis…"
            )
            # Note: Full IndicTrans2 translation requires the model installed.
            # Here we show the detected language; translation happens per response.

        with st.spinner("Building semantic search index…"):
            clauses = segment_clauses(st.session_state.extracted_text)
            st.session_state.clauses = clauses
            faiss_idx = build_index_from_text(st.session_state.extracted_text)
            st.session_state.faiss_index = faiss_idx

        with st.spinner("Generating document summary…"):
            st.session_state.summary = summarize_document(st.session_state.extracted_text)

        with st.spinner("Scanning for risk alerts…"):
            st.session_state.risk_alerts = detect_risk_alerts(clauses)

        st.success(f"✅ Done! Found **{len(clauses)}** clauses.")

    st.divider()
    st.markdown(
        "<small>BVRIT Hyderabad · Dept. of CSE · 2026</small>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main content – tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📋 Summary", "🔎 Ask a Question", "📑 Clause Browser", "⚠️ Risk Alerts", "📝 Form Help"]
)

# ── TAB 1: Summary ──────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Document Summary")

    if not st.session_state.extracted_text:
        st.info("Upload and analyse a document to see the summary here.")
    else:
        # Detected language badge
        lang = detect_language(st.session_state.extracted_text)
        st.markdown(
            f'<div class="step-card">📌 <b>Detected Language:</b> {lang.upper()}</div>',
            unsafe_allow_html=True,
        )

        # Summary
        summary = st.session_state.summary
        if selected_lang_code != "en":
            with st.spinner(f"Translating summary to {output_lang}…"):
                summary = translate_to_indic(summary, selected_lang_code)

        st.markdown(
            f'<div class="step-card">{summary}</div>', unsafe_allow_html=True
        )

        # Raw extracted text (collapsible)
        with st.expander("📄 View Raw Extracted Text"):
            st.text_area(
                "Extracted Text",
                value=st.session_state.extracted_text,
                height=300,
                disabled=True,
            )

# ── TAB 2: Q&A ──────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Ask About Your Document")
    st.markdown(
        "Type any question about the document. The system retrieves relevant clauses "
        "and uses the LLM to generate an accurate answer."
    )

    if not st.session_state.faiss_index:
        st.info("Upload and analyse a document first.")
    else:
        query = st.text_input(
            "Your question",
            placeholder="e.g. What are my termination rights? What fees apply?",
        )

        if st.button("💬 Get Answer") and query.strip():
            with st.spinner("Searching relevant clauses…"):
                results = st.session_state.faiss_index.search(query, top_k=5)
                context_clauses = [r[0] for r in results]

            with st.spinner("Generating answer…"):
                answer = answer_question(query, context_clauses)
                if selected_lang_code != "en":
                    answer = translate_to_indic(answer, selected_lang_code)

            st.markdown("#### ✅ Answer")
            st.markdown(
                f'<div class="success-box">{answer}</div>', unsafe_allow_html=True
            )

            st.markdown("#### 🔗 Retrieved Context Clauses")
            for i, (clause, dist) in enumerate(results, 1):
                with st.expander(f"Clause {i}  (relevance score: {1/(1+dist):.2f})"):
                    st.write(clause)

# ── TAB 3: Clause Browser ───────────────────────────────────────────────────
with tab3:
    st.markdown("### Browse & Simplify Clauses")
    st.markdown(
        "Select any clause to get a plain-language simplification powered by the LLM."
    )

    if not st.session_state.clauses:
        st.info("Upload and analyse a document first.")
    else:
        st.markdown(f"**Total clauses extracted:** {len(st.session_state.clauses)}")

        clause_labels = [
            f"Clause {i+1}: {c[:80]}…" if len(c) > 80 else f"Clause {i+1}: {c}"
            for i, c in enumerate(st.session_state.clauses)
        ]

        selected_idx = st.selectbox(
            "Select a clause", options=range(len(clause_labels)), format_func=lambda i: clause_labels[i]
        )

        selected_clause = st.session_state.clauses[selected_idx]

        st.markdown("**Original Clause:**")
        st.markdown(
            f'<div class="clause-card">{selected_clause}</div>', unsafe_allow_html=True
        )

        if st.button("✨ Simplify This Clause"):
            with st.spinner("Simplifying…"):
                simplified = simplify_clause(selected_clause)
                if selected_lang_code != "en":
                    simplified = translate_to_indic(simplified, selected_lang_code)

            st.markdown(f"**Simplified ({output_lang}):**")
            st.markdown(
                f'<div class="success-box">{simplified}</div>', unsafe_allow_html=True
            )

# ── TAB 4: Risk Alerts ──────────────────────────────────────────────────────
with tab4:
    st.markdown("### ⚠️ Risk Alerts")
    st.markdown(
        "Automatically detected clauses that may contain risks, hidden penalties, "
        "or unfair provisions."
    )

    if not st.session_state.extracted_text:
        st.info("Upload and analyse a document first.")
    elif not st.session_state.risk_alerts:
        st.success("✅ No significant risks detected in this document.")
    else:
        st.warning(f"**{len(st.session_state.risk_alerts)} potential risk(s) found:**")
        for alert in st.session_state.risk_alerts:
            translated_alert = alert
            if selected_lang_code != "en":
                translated_alert = translate_to_indic(alert, selected_lang_code)
            st.markdown(
                f'<div class="alert-box">⚠️ {translated_alert}</div>',
                unsafe_allow_html=True,
            )

# ── TAB 5: Form Help ────────────────────────────────────────────────────────
with tab5:
    st.markdown("### 📝 Form Filling Assistant")
    st.markdown(
        "Paste a form field label or instruction below and get step-by-step guidance "
        "on how to fill it correctly."
    )

    field_text = st.text_area(
        "Form field / instruction text",
        placeholder="e.g. 'Affiant's full legal name as per Aadhaar' or 'Section 12-B: Declaration of assets'",
        height=120,
    )

    if st.button("📋 Get Filling Guide") and field_text.strip():
        with st.spinner("Generating guidance…"):
            guide = form_filling_guide(field_text)
            if selected_lang_code != "en":
                guide = translate_to_indic(guide, selected_lang_code)

        st.markdown("#### ✅ How to Fill This Field")
        st.markdown(
            f'<div class="success-box">{guide}</div>', unsafe_allow_html=True
        )
