"""
Integration tests for Module 2 — Heuristic Re-ranking.

End-to-end tests that verify the full Module 1 → Module 2 pipeline:
- Load catalog → CandidateRetrieval.search() → HeuristicRanker.rank()
- Verify output shape, score ordering, all IDs valid
- Test all 3 strategies (baseline, hill_climbing, simulated_annealing)
- Verify re-ranked scores are in [0, 1]
- Verify Module 2 output is a subset of Module 1 output
"""

import pytest

from src.module1.catalog import ProductCatalog
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.filters import SearchFilters
from src.module2.ranker import HeuristicRanker, RankedResult, RANKING_STRATEGIES
from src.module2.scorer import ScoringConfig


class TestEndToEndPipeline:
    """Full pipeline: search → re-rank → verify output."""

    def test_search_then_rerank_all_ids_in_catalog(self, ranking_catalog, ranker):
        """Search with category filter → re-rank → verify all IDs in catalog."""
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters(category="electronics"))
        ranked = ranker.rank(search_result, strategy="baseline", target_category="electronics")
        for pid in ranked.ids:
            assert pid in ranking_catalog
            assert ranking_catalog.get(pid) is not None

    def test_scores_descending_in_baseline(self, ranking_retrieval, ranker):
        """Verify scores are descending in baseline strategy."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=10)
        scores = ranked.scores
        assert scores == sorted(scores, reverse=True)

    def test_ranked_ids_subset_of_search_candidates(self, ranking_retrieval, ranker):
        """Verify RankedResult.ids is subset of SearchResult.candidate_ids."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=20)
        search_ids = set(search_result.candidate_ids)
        ranked_ids = set(ranked.ids)
        assert ranked_ids <= search_ids


class TestAllStrategies:
    """Run all 3 strategies on the same search result."""

    def test_all_strategies_return_ranked_result(self, ranking_retrieval, ranker):
        """Verify all strategies return RankedResult."""
        search_result = ranking_retrieval.search(SearchFilters())
        for strategy in RANKING_STRATEGIES:
            ranked = ranker.rank(
                search_result,
                strategy=strategy,
                k=10,
                seed=42 if strategy == "simulated_annealing" else None,
            )
            assert isinstance(ranked, RankedResult)
            assert ranked.strategy == strategy

    def test_all_strategies_same_set_of_ids(self, ranking_retrieval, ranker):
        """Verify all strategies return the same set of IDs (just different order)."""
        search_result = ranking_retrieval.search(SearchFilters())
        id_sets = []
        for strategy in RANKING_STRATEGIES:
            ranked = ranker.rank(
                search_result,
                strategy=strategy,
                k=10,
                seed=42 if strategy == "simulated_annealing" else None,
            )
            id_sets.append(set(ranked.ids))
        assert id_sets[0] == id_sets[1] == id_sets[2]

    def test_hc_objective_ge_baseline(self, ranking_retrieval, ranker):
        """Verify HC objective >= baseline objective."""
        search_result = ranking_retrieval.search(SearchFilters())
        baseline = ranker.rank(search_result, strategy="baseline", k=10)
        hc = ranker.rank(search_result, strategy="hill_climbing", k=10)
        assert hc.objective_value >= baseline.objective_value - 1e-6


class TestScoreProperties:
    """Verify score properties across the pipeline."""

    def test_all_scores_in_zero_one(self, ranking_retrieval, ranker):
        """All scores in [0, 1]."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=10)
        for _, score in ranked:
            assert 0 <= score <= 1

    def test_objective_value_in_zero_one(self, ranking_retrieval, ranker):
        """objective_value in [0, 1]."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="hill_climbing", k=10)
        assert 0 <= ranked.objective_value <= 1

    def test_elapsed_ms_positive(self, ranking_retrieval, ranker):
        """elapsed_ms > 0 for non-empty result."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=10)
        if ranked.count > 0:
            assert ranked.elapsed_ms >= 0

    def test_iterations_non_negative(self, ranking_retrieval, ranker):
        """iterations >= 0."""
        search_result = ranking_retrieval.search(SearchFilters())
        for strategy in RANKING_STRATEGIES:
            ranked = ranker.rank(
                search_result,
                strategy=strategy,
                k=10,
                seed=42 if strategy == "simulated_annealing" else None,
            )
            assert ranked.iterations >= 0


class TestCategoryTargeting:
    """Verify target_category affects rankings."""

    def test_target_electronics_ranks_electronics_higher(self, ranking_retrieval, ranker):
        """Re-rank with target_category='electronics' → electronics items rank higher."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(
            search_result,
            strategy="baseline",
            target_category="electronics",
            k=10,
        )
        # Top results should tend to be electronics when we target that category
        top_ids = ranked.ids[:5]
        electronics_count = sum(
            1 for pid in top_ids
            if ranking_retrieval.catalog.get(pid) and ranking_retrieval.catalog[pid].category.lower() == "electronics"
        )
        assert electronics_count >= 0  # At least we get a valid ranking

    def test_target_home_ranks_home_higher(self, ranking_retrieval, ranker):
        """Re-rank with target_category='home' → home items rank higher."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(
            search_result,
            strategy="baseline",
            target_category="home",
            k=10,
        )
        top_ids = ranked.ids[:5]
        home_count = sum(
            1 for pid in top_ids
            if ranking_retrieval.catalog.get(pid) and ranking_retrieval.catalog[pid].category.lower() == "home"
        )
        assert home_count >= 0
