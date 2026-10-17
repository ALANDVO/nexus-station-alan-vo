"""Deterministic TF-IDF semantic ranking engine.

Ranks memory records by cosine similarity between a query's TF-IDF vector
and each memory's TF-IDF vector. Fully offline — no LLM key required.

Pipeline:
  1. tokenize(text) -> list of normalized tokens
  2. TFIDFRanker.index(memories) builds the vocabulary and TF-IDF vectors
  3. rank(query) -> list of (memory_id, score) sorted by score descending

Determinism: no randomness. Same input always produces the same ranking.

TF-IDF formulas:
  TF(t, d) = count(t, d) / total_tokens(d)
  IDF(t)   = ln((1 + N) / (1 + df(t))) + 1    [sklearn-style +1 smoothing]
  TFIDF(t, d) = TF(t, d) * IDF(t)
  Cosine = (v_d · v_q) / (||v_d|| * ||v_q||)

Vectors are L2-normalized so cosine similarity = dot product.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Sequence

from ..models.memory import Memory

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens.

    Strips punctuation, lowercases, returns tokens in document order.
    """
    return _TOKEN_RE.findall(text.lower())


def _term_frequency(tokens: Sequence[str]) -> dict[str, float]:
    """Count raw term frequencies normalized by total token count."""
    if not tokens:
        return {}
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    return {t: c / total for t, c in counts.items()}


@dataclass
class _DocVector:
    """Stored TF-IDF vector (L2-normalized) and raw tokens for a document."""

    tfidf: dict[str, float] = field(default_factory=dict)
    tokens: list[str] = field(default_factory=list)
    norm: float = 0.0


def _l2_normalize(vec: dict[str, float]) -> dict[str, float]:
    """L2-normalize a sparse vector. Returns empty dict if norm is zero."""
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return {}
    return {t: v / norm for t, v in vec.items()}


class TFIDFRanker:
    """Deterministic TF-IDF ranking engine for memory records."""

    def __init__(self) -> None:
        self._docs: dict[str, _DocVector] = {}
        self._df: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._N: int = 0
        self._indexed: bool = False

    def index(self, memories: Sequence[Memory]) -> None:
        """Build the TF-IDF index from a sequence of Memory records."""
        self._docs = {}
        self._df = {}
        self._idf = {}
        self._N = 0

        # First pass: accumulate document frequency
        doc_tokens: dict[str, list[str]] = {}
        for mem in memories:
            tokens = tokenize(mem.title + " " + mem.content)
            doc_tokens[mem.id] = tokens
            self._N += 1
            for t in set(tokens):
                self._df[t] = self._df.get(t, 0) + 1

        # Compute IDF with +1 smoothing (standard sklearn formula)
        for term, df in self._df.items():
            self._idf[term] = math.log((1 + self._N) / (1 + df)) + 1

        # Second pass: compute TF-IDF vectors and L2-normalize
        for mem_id, tokens in doc_tokens.items():
            tf = _term_frequency(tokens)
            tfidf = {t: tf_val * self._idf.get(t, 0.0) for t, tf_val in tf.items()}
            normalized = _l2_normalize(tfidf)
            self._docs[mem_id] = _DocVector(
                tfidf=normalized,
                tokens=tokens,
                norm=math.sqrt(sum(v * v for v in normalized.values())),
            )

        self._indexed = True

    def _query_vector(self, query: str) -> dict[str, float]:
        """Build a L2-normalized TF-IDF vector for a query string."""
        q_tokens = tokenize(query)
        if not q_tokens:
            return {}
        q_tf = _term_frequency(q_tokens)
        q_tfidf = {t: tf_val * self._idf.get(t, 0.0) for t, tf_val in q_tf.items()}
        return _l2_normalize(q_tfidf)

    def rank(self, query: str, limit: int = 20) -> list[tuple[str, float]]:
        """Rank all indexed documents by cosine similarity to the query.

        Returns list of (memory_id, score) sorted by score descending.
        Scores are in [0, 1]; empty query or no matches returns empty list.
        """
        if not self._indexed or self._N == 0:
            return []

        q_vec = self._query_vector(query)
        if not q_vec:
            return []

        # Since vectors are L2-normalized, cosine similarity = dot product
        results: list[tuple[str, float]] = []
        for mem_id, doc in self._docs.items():
            if not doc.tfidf:
                continue
            dot = 0.0
            for t, q_val in q_vec.items():
                d_val = doc.tfidf.get(t)
                if d_val is not None:
                    dot += d_val * q_val
            if dot > 0:
                results.append((mem_id, round(dot, 6)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    @property
    def document_count(self) -> int:
        return self._N

    @property
    def vocabulary_size(self) -> int:
        return len(self._df)

    def is_indexed(self) -> bool:
        return self._indexed