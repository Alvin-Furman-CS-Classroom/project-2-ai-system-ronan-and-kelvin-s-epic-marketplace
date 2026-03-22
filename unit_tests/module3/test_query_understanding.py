"""
Unit tests for src/module3/query_understanding — orchestrator.

Owner: Ronan

Tests:
  - understand() returns a QueryResult with all fields populated
  - keywords list is non-empty for normal queries
  - query_embedding has shape (100,)
  - inferred_category is a valid category string
  - search_by_text returns ranked product IDs
  - End-to-end: query -> keywords + embedding + category
"""

import numpy as np
import pytest

from src.module3.embeddings import EMBEDDING_DIM
from src.module3.query_understanding import QueryResult, QueryUnderstanding


class TestQueryUnderstanding:
    """Tests for the QueryUnderstanding orchestrator."""

    def test_understand_returns_query_result(self, query_understanding):
        """understand() returns a QueryResult with all fields populated."""
        result = query_understanding.understand("bluetooth headphones for running")
        assert isinstance(result, QueryResult)
        assert result.keywords is not None
        assert result.query_embedding is not None
        assert result.inferred_category is not None or result.confidence == 0

    def test_keywords_non_empty_for_normal_query(self, query_understanding):
        """Keywords list is non-empty for normal queries."""
        result = query_understanding.understand("bluetooth headphones wireless")
        assert len(result.keywords) > 0
        assert all(isinstance(kw, tuple) and len(kw) == 2 for kw in result.keywords)

    def test_query_embedding_shape(self, query_understanding):
        """query_embedding has shape (EMBEDDING_DIM,)."""
        result = query_understanding.understand("laptop stand adjustable")
        assert result.query_embedding.shape == (EMBEDDING_DIM,)

    def test_inferred_category_valid(self, query_understanding):
        """inferred_category is a valid category string."""
        valid = {"audio", "footwear", "accessories", "electronics"}
        result = query_understanding.understand("wireless speaker portable")
        assert result.inferred_category in valid

    def test_search_by_text_returns_ranked_ids(self, query_understanding):
        """search_by_text returns ranked (item_id, score) tuples."""
        texts = {
            "speaker": "portable bluetooth speaker waterproof",
            "shoes": "running shoes lightweight breathable",
            "keyboard": "mechanical keyboard rgb gaming",
        }
        ranked = query_understanding.search_by_text("bluetooth speaker", texts, top_k=5)
        assert isinstance(ranked, list)
        assert len(ranked) <= 5
        assert all(isinstance(r, tuple) and len(r) == 2 for r in ranked)
        assert ranked[0][0] == "speaker"

    def test_search_by_text_empty_dict(self, query_understanding):
        """search_by_text with empty texts returns empty list."""
        assert query_understanding.search_by_text("bluetooth", {}) == []

    def test_understand_empty_query(self, query_understanding):
        """Empty query returns minimal but valid result."""
        result = query_understanding.understand("")
        assert result.keywords == []
        assert result.query_embedding.shape == (EMBEDDING_DIM,)
        assert np.allclose(result.query_embedding, 0.0)

    def test_end_to_end_pipeline(self, query_understanding):
        """Full pipeline: query -> keywords + embedding + category."""
        result = query_understanding.understand("bluetooth headphones for running")
        assert len(result.keywords) > 0
        assert any("bluetooth" in kw or "headphones" in kw or "running" in kw for kw, _ in result.keywords)
        assert result.query_embedding.dtype == np.float32
        assert result.inferred_category in {"audio", "footwear", "accessories", "electronics"}
        assert 0 <= result.confidence <= 1
