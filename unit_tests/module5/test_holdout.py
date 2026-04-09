"""Tests for HeldOutSet and holdout builders."""

import pandas as pd
import pytest

from src.module5.exceptions import HeldOutDataError
from src.module5.holdout import (
    HeldOutSet,
    build_holdout_from_reviews,
    train_test_split_holdout,
)


# ── HeldOutSet basics ────────────────────────────────────────────────────

class TestHeldOutSet:

    def test_empty_holdout(self):
        h = HeldOutSet()
        assert h.num_queries == 0
        assert h.queries == []

    def test_add_and_retrieve(self):
        h = HeldOutSet()
        h.add("headphones", {"p1", "p2"})
        assert h.num_queries == 1
        assert h.get_relevant("headphones") == {"p1", "p2"}

    def test_get_relevance_binary(self):
        h = HeldOutSet({"q1": {"p1", "p3"}})
        assert h.get_relevance("q1", "p1") == 1
        assert h.get_relevance("q1", "p2") == 0

    def test_unknown_query_returns_empty(self):
        h = HeldOutSet({"q1": {"p1"}})
        assert h.get_relevant("unknown") == set()
        assert h.get_relevance("unknown", "p1") == 0

    def test_queries_sorted(self):
        h = HeldOutSet({"zebra": {"p1"}, "apple": {"p2"}, "mango": {"p3"}})
        assert h.queries == ["apple", "mango", "zebra"]

    def test_add_replaces(self):
        h = HeldOutSet({"q1": {"p1"}})
        h.add("q1", {"p2", "p3"})
        assert h.get_relevant("q1") == {"p2", "p3"}


# ── build_holdout_from_reviews ────────────────────────────────────────────

class TestBuildHoldoutFromReviews:

    @pytest.fixture
    def reviews_df(self):
        return pd.DataFrame({
            "parent_asin": ["p1", "p1", "p2", "p3", "p3", "p4"],
            "rating": [5.0, 3.0, 4.5, 2.0, 1.0, 4.0],
        })

    def test_default_threshold(self, reviews_df):
        mapping = {"q1": ["p1", "p2", "p3", "p4"]}
        h = build_holdout_from_reviews(reviews_df, mapping)
        relevant = h.get_relevant("q1")
        assert "p1" in relevant
        assert "p2" in relevant
        assert "p4" in relevant
        assert "p3" not in relevant

    def test_custom_threshold(self, reviews_df):
        mapping = {"q1": ["p1", "p2", "p3"]}
        h = build_holdout_from_reviews(reviews_df, mapping, rating_threshold=5.0)
        assert h.get_relevant("q1") == {"p1"}

    def test_missing_column_raises(self, reviews_df):
        with pytest.raises(HeldOutDataError, match="missing required column"):
            build_holdout_from_reviews(
                reviews_df, {"q1": ["p1"]}, rating_column="nonexistent"
            )

    def test_empty_mapping(self, reviews_df):
        h = build_holdout_from_reviews(reviews_df, {})
        assert h.num_queries == 0

    def test_candidate_not_in_reviews(self, reviews_df):
        mapping = {"q1": ["p99"]}
        h = build_holdout_from_reviews(reviews_df, mapping)
        assert h.get_relevant("q1") == set()


# ── train_test_split_holdout ─────────────────────────────────────────────

class TestTrainTestSplitHoldout:

    def test_split_sizes(self):
        h = HeldOutSet({f"q{i}": {f"p{i}"} for i in range(10)})
        train, test = train_test_split_holdout(h, test_fraction=0.3, seed=42)
        assert train.num_queries + test.num_queries == 10
        assert test.num_queries >= 1

    def test_deterministic(self):
        h = HeldOutSet({f"q{i}": {f"p{i}"} for i in range(10)})
        t1_train, t1_test = train_test_split_holdout(h, seed=42)
        t2_train, t2_test = train_test_split_holdout(h, seed=42)
        assert t1_train.queries == t2_train.queries
        assert t1_test.queries == t2_test.queries

    def test_different_seeds_differ(self):
        h = HeldOutSet({f"q{i}": {f"p{i}"} for i in range(20)})
        _, t1 = train_test_split_holdout(h, seed=1)
        _, t2 = train_test_split_holdout(h, seed=99)
        assert t1.queries != t2.queries

    def test_no_overlap(self):
        h = HeldOutSet({f"q{i}": {f"p{i}"} for i in range(10)})
        train, test = train_test_split_holdout(h, seed=42)
        assert set(train.queries).isdisjoint(set(test.queries))
