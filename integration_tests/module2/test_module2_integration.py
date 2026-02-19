"""
Integration tests for Module 2 — Heuristic Re-ranking.

End-to-end tests that verify the full Module 1 → Module 2 pipeline:
- Load working-set catalog → CandidateRetrieval.search() → HeuristicRanker.rank()
- Verify output shape, score ordering, all IDs valid
- Test all 3 strategies (baseline, hill_climbing, simulated_annealing)
- Verify re-ranked scores are in [0, 1]
- Verify Module 2 output is a subset of Module 1 output

TODO (Ronan): Implement all test functions.
"""

import pytest

from src.module1.catalog import ProductCatalog
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.filters import SearchFilters
from src.module2.ranker import HeuristicRanker, RankedResult, RANKING_STRATEGIES
from src.module2.scorer import ScoringConfig


# TODO: fixture to load catalog (working set or conftest products)
# TODO: fixture to create retrieval + ranker


class TestEndToEndPipeline:
    """Full pipeline: search → re-rank → verify output."""

    # TODO: search with category filter → re-rank → verify all IDs in catalog
    # TODO: verify scores are descending in baseline
    # TODO: verify RankedResult.ids is subset of SearchResult.candidate_ids
    pass


class TestAllStrategies:
    """Run all 3 strategies on the same search result."""

    # TODO: verify all strategies return RankedResult
    # TODO: verify all strategies return the same set of IDs (just different order)
    # TODO: verify HC objective >= baseline objective
    pass


class TestScoreProperties:
    """Verify score properties across the pipeline."""

    # TODO: all scores in [0, 1]
    # TODO: objective_value in [0, 1]
    # TODO: elapsed_ms > 0
    # TODO: iterations >= 0
    pass


class TestCategoryTargeting:
    """Verify target_category affects rankings."""

    # TODO: re-rank with target_category="electronics" → electronics items rank higher
    # TODO: re-rank with target_category="home" → home items rank higher
    pass
