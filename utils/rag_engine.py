"""Lightweight retrieval helpers for legal document clauses."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances


def segment_clauses(text: str) -> list[str]:
    """Split extracted legal text into searchable clause-like chunks."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    numbered = re.split(r"(?=(?:\d+\.|\([a-zA-Z0-9]+\)|[A-Z][A-Z\s]{4,}:))", cleaned)
    clauses = [part.strip() for part in numbered if len(part.strip()) > 30]

    if clauses:
        return clauses

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) > 30]


@dataclass
class TfidfClauseIndex:
    clauses: list[str]
    vectorizer: TfidfVectorizer
    matrix: object

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        if not self.clauses:
            return []
        query_vector = self.vectorizer.transform([query])
        distances = cosine_distances(query_vector, self.matrix)[0]
        ranked = sorted(enumerate(distances), key=lambda item: item[1])[:top_k]
        return [(self.clauses[index], float(distance)) for index, distance in ranked]


def build_index_from_text(text: str) -> TfidfClauseIndex:
    clauses = segment_clauses(text)
    if not clauses:
        clauses = [text.strip()] if text.strip() else ["No document text available."]

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(clauses)
    return TfidfClauseIndex(clauses=clauses, vectorizer=vectorizer, matrix=matrix)
