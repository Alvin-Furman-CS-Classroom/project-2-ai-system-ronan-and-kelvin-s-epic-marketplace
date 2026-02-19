"""
Unit tests for the heuristic ranker (src/module2/ranker.py).

Tests cover:
- RankedResult container properties
- NDCG@k correctness
- Baseline ranking (descending by score)
- Hill-climbing optimiser behaviour
- Simulated-annealing optimiser behaviour
- HeuristicRanker.rank() dispatch + edge cases
"""

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import SearchResult
from src.module1.filters import SearchFilters
from src.module2.ranker import (
    HeuristicRanker,
    RankedResult,
    RANKING_STRATEGIES,
    ndcg_at_k,
    _hill_climb,
    _simulated_annealing,
)
from src.module2.scorer import ScoringConfig
from src.module2.exceptions import RankingError


# ===================================================================
# RankedResult
# ===================================================================

class TestRankedResult:
    """Tests for the RankedResult frozen dataclass."""

    def test_len(self):
        """len() returns number of candidates."""
        r = RankedResult([("a", 0.9), ("b", 0.7)], "baseline", 0, 1.0, 0.1)
        assert len(r) == 2

    def test_iteration(self):
        """Iteration yields (id, score) tuples."""
        items = [("a", 0.9), ("b", 0.7)]
        r = RankedResult(items, "baseline", 0, 1.0, 0.1)
        assert list(r) == items

    def test_ids_property(self):
        """ids property returns just product IDs."""
        r = RankedResult([("a", 0.9), ("b", 0.7)], "baseline", 0, 1.0, 0.1)
        assert r.ids == ["a", "b"]

    def test_scores_property(self):
        """scores property returns just scores."""
        r = RankedResult([("a", 0.9), ("b", 0.7)], "baseline", 0, 1.0, 0.1)
        assert r.scores == [0.9, 0.7]

    def test_count_property(self):
        """count matches len."""
        r = RankedResult([("a", 0.9)], "baseline", 0, 1.0, 0.1)
        assert r.count == 1

    def test_empty_result(self):
        """Empty result has len 0."""
        r = RankedResult([], "baseline", 0, 1.0, 0.0)
        assert len(r) == 0
        assert r.ids == []

    def test_frozen(self):
        """RankedResult is immutable."""
        r = RankedResult([("a", 0.9)], "baseline", 0, 1.0, 0.1)
        with pytest.raises(AttributeError):
            r.strategy = "other"


# ===================================================================
# NDCG@k
# ===================================================================

class TestNDCG:
    """Tests for the ndcg_at_k function."""

    def test_perfect_ordering(self):
        """Descending scores → NDCG = 1.0."""
        assert ndcg_at_k([3, 2, 1], k=3) == pytest.approx(1.0)

    def test_reversed_ordering(self):
        """Ascending scores → NDCG < 1.0."""
        assert ndcg_at_k([1, 2, 3], k=3) < 1.0

    def test_single_item(self):
        """Single item → NDCG = 1.0."""
        assert ndcg_at_k([5.0], k=1) == pytest.approx(1.0)

    def test_empty(self):
        """Empty scores → 1.0 (trivially perfect)."""
        assert ndcg_at_k([], k=5) == pytest.approx(1.0)

    def test_all_zeros(self):
        """All zero scores → 1.0 (no preference)."""
        assert ndcg_at_k([0, 0, 0], k=3) == pytest.approx(1.0)

    def test_k_larger_than_list(self):
        """k > list length doesn't crash."""
        assert ndcg_at_k([3, 1], k=10) == pytest.approx(1.0)

    def test_k_equals_one(self):
        """NDCG@1 cares only about the top item."""
        # Best item is in position 1 (optimal)
        assert ndcg_at_k([10, 1, 1], k=1) == pytest.approx(1.0)
        # Best item is NOT in position 1
        assert ndcg_at_k([1, 10, 1], k=1) < 1.0


# ===================================================================
# Hill climbing
# ===================================================================

class TestHillClimbing:
    """Tests for the _hill_climb optimiser."""

    def test_already_optimal(self):
        """Optimal ordering stays unchanged."""
        ordering = [("a", 3.0), ("b", 2.0), ("c", 1.0)]
        result, iters, ndcg = _hill_climb(ordering, k=3)
        assert ndcg == pytest.approx(1.0)
        assert [pid for pid, _ in result] == ["a", "b", "c"]

    def test_reverses_bad_ordering(self):
        """Reversed ordering gets improved."""
        ordering = [("c", 1.0), ("b", 2.0), ("a", 3.0)]
        result, iters, ndcg = _hill_climb(ordering, k=3)
        assert ndcg == pytest.approx(1.0)
        assert [pid for pid, _ in result] == ["a", "b", "c"]

    def test_returns_positive_iterations(self):
        """At least one iteration is performed."""
        ordering = [("c", 1.0), ("b", 2.0), ("a", 3.0)]
        _, iters, _ = _hill_climb(ordering, k=3)
        assert iters >= 1

    def test_single_item(self):
        """Single item — no swaps possible."""
        ordering = [("a", 5.0)]
        result, iters, ndcg = _hill_climb(ordering, k=1)
        assert result == ordering
        assert ndcg == pytest.approx(1.0)

    def test_two_items_swap(self):
        """Two items in wrong order get swapped."""
        ordering = [("b", 1.0), ("a", 5.0)]
        result, _, ndcg = _hill_climb(ordering, k=2)
        assert [pid for pid, _ in result] == ["a", "b"]

    def test_objective_never_decreases(self):
        """Each iteration's objective ≥ the starting value."""
        ordering = [("d", 1.0), ("c", 2.0), ("b", 3.0), ("a", 4.0)]
        initial_ndcg = ndcg_at_k([s for _, s in ordering], k=4)
        _, _, final_ndcg = _hill_climb(ordering, k=4)
        assert final_ndcg >= initial_ndcg


# ===================================================================
# Simulated annealing
# ===================================================================

class TestSimulatedAnnealing:
    """Tests for the _simulated_annealing optimiser."""

    def test_already_optimal(self):
        """Optimal ordering stays near-optimal."""
        ordering = [("a", 3.0), ("b", 2.0), ("c", 1.0)]
        result, _, ndcg = _simulated_annealing(ordering, k=3, seed=42)
        assert ndcg >= 0.95  # may not stay at exactly 1.0 due to randomness

    def test_improves_bad_ordering(self):
        """Reversed ordering gets improved."""
        ordering = [("c", 1.0), ("b", 2.0), ("a", 3.0)]
        initial_ndcg = ndcg_at_k([s for _, s in ordering], k=3)
        _, _, final_ndcg = _simulated_annealing(ordering, k=3, seed=42)
        assert final_ndcg >= initial_ndcg

    def test_deterministic_with_seed(self):
        """Same seed → same result."""
        ordering = [("c", 1.0), ("b", 2.0), ("a", 3.0)]
        r1, i1, n1 = _simulated_annealing(ordering, k=3, seed=123)
        r2, i2, n2 = _simulated_annealing(ordering, k=3, seed=123)
        assert r1 == r2
        assert i1 == i2
        assert n1 == n2

    def test_different_seeds_may_differ(self):
        """Different seeds can produce different paths."""
        ordering = [("d", 1), ("c", 2), ("b", 3), ("a", 4),
                    ("e", 0.5), ("f", 0.1)]
        r1, _, _ = _simulated_annealing(ordering, k=4, seed=1)
        r2, _, _ = _simulated_annealing(ordering, k=4, seed=9999)
        # They may or may not differ, but shouldn't crash
        assert len(r1) == len(r2) == 6

    def test_returns_positive_iterations(self):
        """At least one iteration is performed."""
        ordering = [("b", 1.0), ("a", 2.0)]
        _, iters, _ = _simulated_annealing(ordering, k=2, seed=42)
        assert iters >= 1

    def test_single_item(self):
        """Single item — cannot swap."""
        ordering = [("a", 5.0)]
        result, iters, ndcg = _simulated_annealing(ordering, k=1, seed=42)
        assert result == ordering
        assert ndcg == pytest.approx(1.0)

    def test_preserves_all_items(self):
        """All items present after optimisation (no loss/duplication)."""
        ordering = [("a", 1), ("b", 2), ("c", 3), ("d", 4)]
        result, _, _ = _simulated_annealing(ordering, k=4, seed=42)
        assert sorted(pid for pid, _ in result) == ["a", "b", "c", "d"]


# ===================================================================
# HeuristicRanker.rank()
# ===================================================================

class TestHeuristicRankerBaseline:
    """Tests for the baseline ranking strategy."""

    def test_returns_ranked_result(self, ranker, electronics_result):
        """rank() returns a RankedResult."""
        result = ranker.rank(electronics_result)
        assert isinstance(result, RankedResult)

    def test_strategy_is_baseline(self, ranker, electronics_result):
        """Default strategy is 'baseline'."""
        result = ranker.rank(electronics_result)
        assert result.strategy == "baseline"

    def test_scores_descending(self, ranker, electronics_result):
        """Baseline sorts scores in descending order."""
        result = ranker.rank(electronics_result)
        scores = result.scores
        assert scores == sorted(scores, reverse=True)

    def test_all_candidates_present(self, ranker, electronics_result):
        """All input candidate IDs appear in the output."""
        result = ranker.rank(electronics_result)
        assert set(result.ids) == set(electronics_result.candidate_ids)

    def test_zero_iterations_for_baseline(self, ranker, electronics_result):
        """Baseline performs 0 optimiser iterations."""
        result = ranker.rank(electronics_result)
        assert result.iterations == 0

    def test_max_results_truncates(self, ranker, all_result):
        """max_results limits output length."""
        result = ranker.rank(all_result, max_results=3)
        assert len(result) == 3

    def test_max_results_zero(self, ranker, all_result):
        """max_results=0 returns empty."""
        result = ranker.rank(all_result, max_results=0)
        assert len(result) == 0

    def test_elapsed_ms_positive(self, ranker, electronics_result):
        """Elapsed time is positive."""
        result = ranker.rank(electronics_result)
        assert result.elapsed_ms >= 0

    def test_target_category_affects_ordering(self, ranker, all_result):
        """Specifying target_category changes which items rank highest."""
        elec = ranker.rank(all_result, target_category="electronics")
        home = ranker.rank(all_result, target_category="home")
        # Top item should differ based on category boost
        assert elec.ids[0] != home.ids[0]


class TestHeuristicRankerHillClimbing:
    """Tests for hill_climbing strategy via HeuristicRanker."""

    def test_returns_ranked_result(self, ranker, electronics_result):
        """Hill climbing returns a valid RankedResult."""
        result = ranker.rank(electronics_result, strategy="hill_climbing")
        assert isinstance(result, RankedResult)
        assert result.strategy == "hill_climbing"

    def test_all_candidates_present(self, ranker, electronics_result):
        """No candidates lost during optimisation."""
        result = ranker.rank(electronics_result, strategy="hill_climbing")
        assert set(result.ids) == set(electronics_result.candidate_ids)

    def test_objective_at_least_baseline(self, ranker, electronics_result):
        """Hill climbing objective ≥ baseline objective."""
        baseline = ranker.rank(electronics_result, strategy="baseline")
        hc = ranker.rank(electronics_result, strategy="hill_climbing")
        assert hc.objective_value >= baseline.objective_value - 1e-9

    def test_positive_iterations(self, ranker, electronics_result):
        """Hill climbing performs at least 1 iteration."""
        result = ranker.rank(electronics_result, strategy="hill_climbing")
        assert result.iterations >= 1


class TestHeuristicRankerSimulatedAnnealing:
    """Tests for simulated_annealing strategy via HeuristicRanker."""

    def test_returns_ranked_result(self, ranker, electronics_result):
        """SA returns a valid RankedResult."""
        result = ranker.rank(electronics_result, strategy="simulated_annealing",
                             seed=42)
        assert isinstance(result, RankedResult)
        assert result.strategy == "simulated_annealing"

    def test_all_candidates_present(self, ranker, electronics_result):
        """No candidates lost during optimisation."""
        result = ranker.rank(electronics_result, strategy="simulated_annealing",
                             seed=42)
        assert set(result.ids) == set(electronics_result.candidate_ids)

    def test_deterministic_with_seed(self, ranker, electronics_result):
        """Same seed → same ranking."""
        r1 = ranker.rank(electronics_result, strategy="simulated_annealing",
                         seed=123)
        r2 = ranker.rank(electronics_result, strategy="simulated_annealing",
                         seed=123)
        assert r1.ids == r2.ids
        assert r1.scores == r2.scores


class TestHeuristicRankerEdgeCases:
    """Edge-case tests for HeuristicRanker."""

    def test_unknown_strategy_raises(self, ranker, electronics_result):
        """Invalid strategy raises RankingError."""
        with pytest.raises(RankingError):
            ranker.rank(electronics_result, strategy="invalid")

    def test_empty_search_result(self, ranker):
        """Empty SearchResult → empty RankedResult."""
        empty = SearchResult(candidate_ids=[], strategy="linear",
                             total_scanned=0, elapsed_ms=0)
        result = ranker.rank(empty)
        assert len(result) == 0
        assert result.objective_value == 1.0

    def test_single_candidate(self, ranking_catalog):
        """Single candidate has NDCG = 1.0."""
        sr = SearchResult(candidate_ids=["cheap-good"], strategy="linear",
                          total_scanned=1, elapsed_ms=0)
        ranker = HeuristicRanker(ranking_catalog)
        result = ranker.rank(sr)
        assert len(result) == 1
        assert result.objective_value == pytest.approx(1.0)

    def test_missing_candidate_ids_skipped(self, ranking_catalog):
        """IDs not in catalog are silently skipped."""
        sr = SearchResult(
            candidate_ids=["cheap-good", "NONEXISTENT", "home-star"],
            strategy="linear", total_scanned=3, elapsed_ms=0,
        )
        ranker = HeuristicRanker(ranking_catalog)
        result = ranker.rank(sr)
        assert len(result) == 2
        assert "NONEXISTENT" not in result.ids

    def test_custom_config(self, ranking_catalog, electronics_result):
        """Custom ScoringConfig changes the ranking order."""
        # Only care about price — cheapest should be first
        cheap_config = ScoringConfig(price=1, rating=0, popularity=0,
                                     category_match=0, richness=0)
        ranker = HeuristicRanker(ranking_catalog, config=cheap_config)
        result = ranker.rank(electronics_result)
        # cheap-bad ($5) should be first
        assert result.ids[0] == "cheap-bad"

    def test_all_strategies_valid(self):
        """RANKING_STRATEGIES contains the expected strategies."""
        assert "baseline" in RANKING_STRATEGIES
        assert "hill_climbing" in RANKING_STRATEGIES
        assert "simulated_annealing" in RANKING_STRATEGIES
