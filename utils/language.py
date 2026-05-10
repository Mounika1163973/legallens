"""Language detection and translation helpers for LegalLens."""

from __future__ import annotations

SUPPORTED_INDIC_LANGS = {
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
}


def detect_language(text: str) -> str:
    """Return a best-effort ISO language code for the given text."""
    if not text.strip():
        return "en"

    try:
        from langdetect import detect

        return detect(text)
    except Exception:
        return "en"


def is_english(text: str) -> bool:
    return detect_language(text) == "en"


def translate_to_indic(text: str, target_lang: str) -> str:
    """Translate text into an Indic language when a translator is available."""
    if not text.strip() or target_lang == "en":
        return text

    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception:
        return text
