"""Gemini-backed legal analysis helpers with local fallbacks."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_READY = bool(GEMINI_API_KEY)
except Exception:
    genai = None
    GEMINI_READY = False


def _generate(prompt: str) -> str:
    if not GEMINI_READY or genai is None:
        return ""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return ""


def summarize_document(text: str) -> str:
    prompt = f"""
Summarize this legal document in clear, non-technical language.
Include the parties, purpose, important obligations, dates, payments, and risks.

Document:
{text[:12000]}
"""
    return _generate(prompt) or "Summary unavailable. Please set GEMINI_API_KEY to enable AI summaries."


def simplify_clause(clause: str) -> str:
    prompt = f"""
Explain this legal clause in simple language.
Mention what the user must do, what the other party can do, and any risk.

Clause:
{clause}
"""
    return _generate(prompt) or clause


def answer_question(query: str, context_clauses: list[str]) -> str:
    context = "\n\n".join(context_clauses)
    prompt = f"""
Answer the question using only the document clauses below.
If the answer is not present, say that the document does not clearly state it.

Question: {query}

Relevant clauses:
{context}
"""
    return _generate(prompt) or "I could not generate an AI answer. Please check your GEMINI_API_KEY."


def detect_risk_alerts(clauses: list[str]) -> list[str]:
    risky_terms = [
        "penalty",
        "termination",
        "non-refundable",
        "liability",
        "indemnity",
        "arbitration",
        "interest",
        "breach",
        "forfeit",
        "damages",
    ]
    alerts = []
    for clause in clauses:
        lower_clause = clause.lower()
        if any(term in lower_clause for term in risky_terms):
            prompt = f"Briefly explain the possible legal risk in this clause:\n{clause}"
            explanation = _generate(prompt)
            alerts.append(explanation or clause)
    return alerts[:8]


def form_filling_guide(field_text: str) -> str:
    prompt = f"""
Give simple step-by-step guidance for filling this legal form field.
Mention what information is needed and common mistakes to avoid.

Field:
{field_text}
"""
    return _generate(prompt) or "Provide accurate information exactly as shown in your official records."
