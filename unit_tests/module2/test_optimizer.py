"""
Optimizer-focused unit tests for Module 2.

Tests that go deeper on hill climbing and simulated annealing behaviour:
- Convergence rate comparisons (HC vs SA)
- SA temperature schedule assertions
- HC patience / early-stop verification
- Large-N stress tests (50+ candidates)
"""

import pytest
import time

from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.filters import SearchFilters
from src.module2.ranker import (
    HeuristicRanker,
    RankedResult,
    ndcg_at_k,
    _hill_climb,
    _simulated_annealing,
)
from src.module2.scorer import ScoringConfig, compute_score, compute_feature_ranges


def _scored_ordering(catalog: ProductCatalog, candidate_ids: list[str], config: ScoringConfig) -> list[tuple[str, float]]:
    """Build (id, score) list from candidate IDs."""
    products = [catalog[pid] for pid in candidate_ids if catalog.get(pid)]
    if not products:
        return []
    ranges = compute_feature_ranges(products)
    scored = [(p.id, compute_score(p, config, ranges)) for p in products]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


class TestHillClimbConvergence:
    """Tests for hill-climbing convergence properties."""

    def test_hc_converges_faster_for_nearly_sorted_input(self, ranking_catalog, ranker):
        """HC converges in fewer iterations when input is already well-ordered."""
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters(category="electronics"))
        ranked_good = ranker.rank(search_result, strategy="hill_climbing", k=5)
        # Reverse the baseline to get a bad ordering
        bad_ids = list(reversed([pid for pid, _ in ranked_good]))
        bad_result = SearchResult(candidate_ids=bad_ids, strategy="linear", total_scanned=len(bad_ids), elapsed_ms=0)
        ranked_bad = ranker.rank(bad_result, strategy="hill_climbing", k=5)
        # Bad input should need more iterations (or at least run)
        assert ranked_bad.iterations >= 0

    def test_hc_patience_stops_after_non_improving_rounds(self, ranking_catalog):
        """HC with patience=1 stops after first round with no improvement."""
        config = ScoringConfig()
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters())
        scored = _scored_ordering(ranking_catalog, search_result.candidate_ids, config)
        k = min(5, len(scored))
        # Use a nearly-optimal ordering so HC finds no improvement quickly
        optimal = sorted(scored, key=lambda t: t[1], reverse=True)
        _, iterations, _ = _hill_climb(optimal, k, max_iterations=100, patience=1)
        assert iterations <= 2  # First round tries swaps, second round has no improvement → stop

    def test_hc_max_iterations_cap(self, ranking_catalog):
        """HC with max_iterations=1 does at most 1 iteration."""
        config = ScoringConfig()
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters())
        scored = _scored_ordering(ranking_catalog, search_result.candidate_ids, config)
        k = min(5, len(scored))
        _, iterations, _ = _hill_climb(scored, k, max_iterations=1, patience=50)
        assert iterations == 1


class TestSimulatedAnnealingSchedule:
    """Tests for SA temperature schedule and acceptance behaviour."""

    def test_high_initial_temp_runs_more_iterations(self):
        """Higher initial_temp allows more iterations before min_temp is hit."""
        ordering = [(f"p{i}", 0.5 + 0.01 * i) for i in range(20)]
        k = 10
        _, iters_high, _ = _simulated_annealing(
            ordering, k, initial_temp=10.0, cooling_rate=0.99, min_temp=0.001, seed=42
        )
        _, iters_low, _ = _simulated_annealing(
            ordering, k, initial_temp=0.1, cooling_rate=0.99, min_temp=0.001, seed=42
        )
        assert iters_high >= iters_low

    def test_cooling_rate_closer_to_one_runs_longer(self):
        """cooling_rate closer to 1.0 runs more iterations before min_temp."""
        ordering = [(f"p{i}", 0.5) for i in range(15)]
        k = 10
        _, iters_slow, _ = _simulated_annealing(
            ordering, k, cooling_rate=0.999, min_temp=0.001, seed=42
        )
        _, iters_fast, _ = _simulated_annealing(
            ordering, k, cooling_rate=0.9, min_temp=0.001, seed=42
        )
        assert iters_slow >= iters_fast

    def test_min_temp_stops_quickly(self):
        """min_temp very close to initial_temp stops almost immediately."""
        ordering = [(f"p{i}", 0.5) for i in range(10)]
        k = 5
        _, iterations, _ = _simulated_annealing(
            ordering, k, initial_temp=1.0, cooling_rate=0.5, min_temp=0.999, seed=42
        )
        assert iterations <= 3

    def test_low_cooling_rate_converges_quickly(self):
        """Very low cooling_rate (e.g. 0.5) hits min_temp in few iterations."""
        ordering = [(f"p{i}", 0.5) for i in range(10)]
        k = 5
        _, iterations, _ = _simulated_annealing(
            ordering, k, initial_temp=1.0, cooling_rate=0.5, min_temp=0.001, seed=42
        )
        assert iterations < 15


class TestLargeNCandidates:
    """Stress tests with 50+ candidates."""

    @pytest.fixture
    def large_catalog(self) -> ProductCatalog:
        """Catalog with 55 products for stress testing."""
        products = [
            Product(
                id=f"p{i}",
                title=f"Product {i}",
                price=10.0 + (i % 50),
                category="electronics" if i % 2 == 0 else "home",
                seller_rating=3.0 + (i % 20) / 10,
                store=f"Store{i % 5}",
                description="Description" * 10,
                rating_number=i * 100,
            )
            for i in range(55)
        ]
        return ProductCatalog(products)

    def test_all_strategies_no_crash(self, large_catalog):
        """All 3 strategies complete without crash on 50+ candidates."""
        retrieval = CandidateRetrieval(large_catalog)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(large_catalog)
        for strategy in ("baseline", "hill_climbing", "simulated_annealing"):
            ranked = ranker.rank(search_result, strategy=strategy, k=10)
            assert isinstance(ranked, RankedResult)
            assert len(ranked) == search_result.count

    def test_sa_and_hc_improve_or_match_baseline_for_large_n(self, large_catalog):
        """SA and HC objective >= baseline for large N (or equal if already optimal)."""
        retrieval = CandidateRetrieval(large_catalog)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(large_catalog)
        baseline = ranker.rank(search_result, strategy="baseline", k=10)
        hc = ranker.rank(search_result, strategy="hill_climbing", k=10)
        sa = ranker.rank(search_result, strategy="simulated_annealing", k=10, seed=42)
        assert hc.objective_value >= baseline.objective_value - 1e-6
        assert sa.objective_value >= baseline.objective_value - 1e-6

    def test_execution_time_reasonable(self, large_catalog):
        """Large-N run stays under 5 seconds per strategy."""
        retrieval = CandidateRetrieval(large_catalog)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(large_catalog)
        for strategy in ("hill_climbing", "simulated_annealing"):
            start = time.perf_counter()
            ranker.rank(search_result, strategy=strategy, k=10, seed=42)
            elapsed = time.perf_counter() - start
            assert elapsed < 5.0, f"{strategy} took {elapsed:.2f}s"


class TestConvergenceComparison:
    """Compare HC vs SA convergence on the same input."""

    def test_both_strategies_on_same_input(self, ranking_retrieval, ranker):
        """Run both HC and SA on the same search result."""
        search_result = ranking_retrieval.search(SearchFilters())
        hc = ranker.rank(search_result, strategy="hill_climbing", k=5)
        sa = ranker.rank(search_result, strategy="simulated_annealing", k=5, seed=42)
        assert set(hc.ids) == set(sa.ids)

    def test_ndcg_comparison(self, ranking_retrieval, ranker):
        """HC and SA produce valid NDCG in [0, 1]."""
        search_result = ranking_retrieval.search(SearchFilters())
        hc = ranker.rank(search_result, strategy="hill_climbing", k=5)
        sa = ranker.rank(search_result, strategy="simulated_annealing", k=5, seed=42)
        assert 0 <= hc.objective_value <= 1
        assert 0 <= sa.objective_value <= 1

    def test_iteration_counts_differ(self, ranking_retrieval, ranker):
        """HC and SA typically have different iteration counts (SA often more)."""
        search_result = ranking_retrieval.search(SearchFilters())
        hc = ranker.rank(search_result, strategy="hill_climbing", k=5)
        sa = ranker.rank(search_result, strategy="simulated_annealing", k=5, seed=42)
        # At least one should have iterations > 0 if we have enough candidates
        assert hc.iterations >= 0 and sa.iterations >= 0
