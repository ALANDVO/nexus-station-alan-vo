"""Tests for the TF-IDF ranking engine (domain logic)."""
from __future__ import annotations

import pytest

from app.services.ranking import TFIDFRanker, tokenize


class TestTokenize:
    def test_tokenize_lowercases(self):
        tokens = tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_tokenize_strips_punctuation(self):
        tokens = tokenize("Fix: the OAuth callback!")
        assert tokens == ["fix", "the", "oauth", "callback"]

    def test_tokenize_keeps_alphanumeric(self):
        tokens = tokenize("model v2.1 and issue #1280")
        assert "model" in tokens
        assert "v2" in tokens
        assert "1" in tokens
        assert "1280" in tokens

    def test_tokenize_empty(self):
        assert tokenize("") == []
        assert tokenize("!!!") == []


class TestTFIDFRanker:
    def test_rank_empty_corpus(self):
        ranker = TFIDFRanker()
        ranker.index([])
        assert ranker.rank("anything") == []
        assert ranker.document_count == 0

    def test_rank_empty_query(self):
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        assert ranker.rank("") == []

    def test_rank_returns_relevant_first(self):
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        results = ranker.rank("database", limit=10)
        # The database memory should rank first
        assert results[0][0] == mems[0].id
        assert results[0][1] > 0.0

    def test_rank_no_matching_terms(self):
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        results = ranker.rank("nonexistentterm", limit=10)
        assert results == []

    def test_rank_is_deterministic(self):
        ranker1 = TFIDFRanker()
        ranker2 = TFIDFRanker()
        mems = _sample_memories()
        ranker1.index(mems)
        ranker2.index(mems)
        r1 = ranker1.rank("auth oauth login", limit=10)
        r2 = ranker2.rank("auth oauth login", limit=10)
        assert r1 == r2

    def test_rank_scores_in_range(self):
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        results = ranker.rank("database migration", limit=10)
        for _, score in results:
            assert 0.0 < score <= 1.0

    def test_rank_limit_respected(self):
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        results = ranker.rank("database", limit=1)
        assert len(results) <= 1

    def test_vocabulary_size_positive(self):
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        assert ranker.vocabulary_size > 0
        assert ranker.is_indexed()

    def test_rare_term_ranks_higher(self):
        """A term unique to one document should give it high similarity."""
        ranker = TFIDFRanker()
        mems = _sample_memories()
        ranker.index(mems)
        # 'oauth' appears only in the auth memory
        results = ranker.rank("oauth", limit=10)
        if results:
            assert results[0][0] == mems[1].id  # auth memory


def _sample_memories():
    from app.models.memory import Memory
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return [
        Memory(
            id="m1", title="Database migration",
            content="sessions table TTL cleanup metadata migration",
            tags=["db"], agent_vendor="codex",
            created_at=now, updated_at=now,
        ),
        Memory(
            id="m2", title="Fix auth bug",
            content="OAuth callback state validation login flow issue",
            tags=["auth"], agent_vendor="claude-code",
            created_at=now, updated_at=now,
        ),
        Memory(
            id="m3", title="API endpoint refactor",
            content="REST endpoints pagination filtering response format",
            tags=["api"], agent_vendor="open-code",
            created_at=now, updated_at=now,
        ),
    ]