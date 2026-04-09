"""Tests for Module 5 evaluation metrics."""

import math

import pytest

from src.module5.metrics import (
    average_precision,
    compute_all_metrics,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


# ── Precision@k ──────────────────────────────────────────────────────────

class TestPrecisionAtK:

    def test_perfect_ranking(self, perfect_ranking, relevant_set):
        assert precision_at_k(perfect_ranking, relevant_set, 3) == pytest.approx(1.0)

    def test_no_relevant_in_top_k(self, relevant_set):
        ranked = ["p5", "p6", "p3"]
        assert precision_at_k(ranked, relevant_set, 3) == pytest.approx(0.0)

    def test_partial_overlap(self, relevant_set):
        ranked = ["p1", "p5", "p2", "p6"]
        assert precision_at_k(ranked, relevant_set, 4) == pytest.approx(0.5)

    def test_k_larger_than_list(self, relevant_set):
        ranked = ["p1", "p2"]
        assert precision_at_k(ranked, relevant_set, 5) == pytest.approx(2 / 5)

    def test_empty_ranked_list(self, relevant_set):
        assert precision_at_k([], relevant_set, 3) == pytest.approx(0.0)

    def test_empty_relevant_set(self, perfect_ranking):
        assert precision_at_k(perfect_ranking, set(), 3) == pytest.approx(0.0)

    def test_k_zero(self, perfect_ranking, relevant_set):
        assert precision_at_k(perfect_ranking, relevant_set, 0) == pytest.approx(0.0)

    def test_single_relevant_at_top(self, relevant_set):
        ranked = ["p1"]
        assert precision_at_k(ranked, relevant_set, 1) == pytest.approx(1.0)


# ── Recall@k ─────────────────────────────────────────────────────────────

class TestRecallAtK:

    def test_full_recall(self, perfect_ranking, relevant_set):
        assert recall_at_k(perfect_ranking, relevant_set, 3) == pytest.approx(1.0)

    def test_partial_recall(self, relevant_set):
        ranked = ["p1", "p5", "p6"]
        assert recall_at_k(ranked, relevant_set, 3) == pytest.approx(1 / 3)

    def test_no_recall(self, relevant_set):
        ranked = ["p5", "p6", "p3"]
        assert recall_at_k(ranked, relevant_set, 3) == pytest.approx(0.0)

    def test_empty_relevant_vacuous(self):
        assert recall_at_k(["p1", "p2"], set(), 2) == pytest.approx(1.0)

    def test_k_zero(self, perfect_ranking, relevant_set):
        assert recall_at_k(perfect_ranking, relevant_set, 0) == pytest.approx(0.0)


# ── NDCG@k ───────────────────────────────────────────────────────────────

class TestNDCGAtK:

    def test_perfect_binary_ranking(self, relevant_set):
        ranked = ["p1", "p2", "p4", "p5", "p6"]
        assert ndcg_at_k(ranked, relevant_set, 3) == pytest.approx(1.0)

    def test_suboptimal_ranking(self, relevant_set):
        """One relevant item at position 3 instead of 1 → NDCG < 1."""
        ranked = ["p5", "p6", "p1", "p2", "p4"]
        val = ndcg_at_k(ranked, relevant_set, 3)
        assert 0.0 < val < 1.0

    def test_known_value(self):
        """Hand-computed: relevant at positions 1 and 3 of 3."""
        ranked = ["a", "b", "c"]
        relevant = {"a", "c"}
        dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
        ideal_dcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
        expected = dcg / ideal_dcg
        assert ndcg_at_k(ranked, relevant, 3) == pytest.approx(expected)

    def test_empty_ranking(self, relevant_set):
        assert ndcg_at_k([], relevant_set, 3) == pytest.approx(1.0)

    def test_no_relevant_items(self):
        ranked = ["a", "b", "c"]
        assert ndcg_at_k(ranked, set(), 3) == pytest.approx(1.0)

    def test_k_zero(self, relevant_set):
        assert ndcg_at_k(["p1"], relevant_set, 0) == pytest.approx(1.0)

    def test_graded_relevance(self):
        ranked = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        grades = {"a": 3.0, "b": 2.0, "c": 1.0}
        assert ndcg_at_k(ranked, relevant, 3, relevance_scores=grades) == pytest.approx(1.0)

    def test_graded_relevance_imperfect(self):
        ranked = ["c", "b", "a"]
        relevant = {"a", "b", "c"}
        grades = {"a": 3.0, "b": 2.0, "c": 1.0}
        val = ndcg_at_k(ranked, relevant, 3, relevance_scores=grades)
        assert val < 1.0


# ── Reciprocal Rank ──────────────────────────────────────────────────────

class TestReciprocalRank:

    def test_first_item_relevant(self, relevant_set):
        ranked = ["p1", "p5", "p6"]
        assert reciprocal_rank(ranked, relevant_set) == pytest.approx(1.0)

    def test_second_item_relevant(self, relevant_set):
        ranked = ["p5", "p2", "p6"]
        assert reciprocal_rank(ranked, relevant_set) == pytest.approx(0.5)

    def test_no_relevant_item(self):
        ranked = ["p5", "p6", "p3"]
        relevant = {"p99"}
        assert reciprocal_rank(ranked, relevant) == pytest.approx(0.0)

    def test_empty_list(self, relevant_set):
        assert reciprocal_rank([], relevant_set) == pytest.approx(0.0)


# ── Average Precision ────────────────────────────────────────────────────

class TestAveragePrecision:

    def test_perfect_ranking(self, relevant_set):
        ranked = ["p1", "p2", "p4", "p5", "p6"]
        assert average_precision(ranked, relevant_set) == pytest.approx(1.0)

    def test_known_value(self):
        """Relevant at positions 1, 3, 5 of 5 → AP = (1/1 + 2/3 + 3/5) / 3."""
        ranked = ["a", "x", "b", "y", "c"]
        relevant = {"a", "b", "c"}
        expected = (1.0 + 2 / 3 + 3 / 5) / 3
        assert average_precision(ranked, relevant) == pytest.approx(expected)

    def test_no_relevant(self):
        ranked = ["a", "b", "c"]
        assert average_precision(ranked, set()) == pytest.approx(0.0)

    def test_none_found(self):
        ranked = ["x", "y", "z"]
        relevant = {"a", "b"}
        assert average_precision(ranked, relevant) == pytest.approx(0.0)


# ── compute_all_metrics ──────────────────────────────────────────────────

class TestComputeAllMetrics:

    def test_returns_all_keys(self, perfect_ranking, relevant_set):
        m = compute_all_metrics(perfect_ranking, relevant_set, 3)
        assert "precision_at_k" in m
        assert "recall_at_k" in m
        assert "ndcg_at_k" in m
        assert "reciprocal_rank" in m
        assert "average_precision" in m

    def test_values_in_valid_range(self, perfect_ranking, relevant_set):
        m = compute_all_metrics(perfect_ranking, relevant_set, 3)
        for key, val in m.items():
            assert 0.0 <= val <= 1.0, f"{key} out of range: {val}"
