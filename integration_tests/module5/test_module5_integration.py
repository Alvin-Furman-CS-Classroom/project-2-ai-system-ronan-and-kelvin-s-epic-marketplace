"""
Integration tests: Module 5 evaluation with Modules 1-2-4 pipeline.

Tests the full flow from retrieval through scoring to evaluation metrics
and top-k payload assembly.  Module 3 (NLP) is not wired here to keep
tests fast; the LTR pipeline uses quality-only (7-dim) features.
"""

import pytest

from src.module1.filters import SearchFilters
from src.module1.retrieval import CandidateRetrieval
from src.module2.ranker import HeuristicRanker
from src.module4.pipeline import LearningToRankPipeline
from src.module5.holdout import HeldOutSet
from src.module5.pipeline import EvaluationPipeline, EvaluationResult, BatchEvaluationResult


def test_module5_package_importable():
    import src.module5 as m5

    assert m5.__doc__
    assert "EvaluationPipeline" in m5.__all__
    assert "TopKResult" in m5.__all__
    assert "precision_at_k" in m5.__all__
    assert "ndcg_at_k" in m5.__all__
    assert "HeldOutSet" in m5.__all__


def test_single_query_evaluation(integration_catalog, integration_holdout):
    """Full pipeline: retrieve → heuristic rank → LTR → evaluate."""
    retrieval = CandidateRetrieval(integration_catalog)
    ranker = HeuristicRanker(integration_catalog)
    ltr = LearningToRankPipeline()

    pipeline = EvaluationPipeline(
        catalog=integration_catalog,
        retrieval=retrieval,
        ranker=ranker,
        ltr_pipeline=ltr,
    )

    filters = SearchFilters(category="Electronics")
    result = pipeline.evaluate(
        "general electronics", filters, integration_holdout, k=5,
    )

    assert isinstance(result, EvaluationResult)
    assert result.query == "general electronics"
    assert result.payload.num_results <= 5
    assert result.payload.num_results > 0

    for key in ("precision_at_k", "recall_at_k", "ndcg_at_k",
                "reciprocal_rank", "average_precision"):
        assert key in result.metrics
        assert 0.0 <= result.metrics[key] <= 1.0


def test_batch_evaluation(integration_catalog, integration_holdout):
    """Batch evaluate multiple queries and check aggregation."""
    retrieval = CandidateRetrieval(integration_catalog)
    ranker = HeuristicRanker(integration_catalog)
    ltr = LearningToRankPipeline()

    pipeline = EvaluationPipeline(
        catalog=integration_catalog,
        retrieval=retrieval,
        ranker=ranker,
        ltr_pipeline=ltr,
    )

    queries = [
        ("general electronics", SearchFilters(category="Electronics")),
        ("usb hub adapter", SearchFilters(category="Electronics")),
    ]

    batch = pipeline.batch_evaluate(queries, integration_holdout, k=5)

    assert isinstance(batch, BatchEvaluationResult)
    assert batch.num_queries == 2
    assert "mean_precision_at_k" in batch.aggregate
    assert "mean_ndcg_at_k" in batch.aggregate

    for key, val in batch.aggregate.items():
        assert 0.0 <= val <= 1.0, f"{key} = {val}"


def test_payload_schema(integration_catalog, integration_holdout):
    """Verify the top-k payload contains expected fields."""
    retrieval = CandidateRetrieval(integration_catalog)
    ranker = HeuristicRanker(integration_catalog)
    ltr = LearningToRankPipeline()

    pipeline = EvaluationPipeline(
        catalog=integration_catalog,
        retrieval=retrieval,
        ranker=ranker,
        ltr_pipeline=ltr,
    )

    result = pipeline.evaluate(
        "general electronics",
        SearchFilters(category="Electronics"),
        integration_holdout,
        k=3,
    )

    payload_dict = result.payload.to_dict()
    assert "query" in payload_dict
    assert "k" in payload_dict
    assert "num_results" in payload_dict
    assert "results" in payload_dict
    assert "metrics" in payload_dict

    for item in payload_dict["results"]:
        assert "id" in item
        assert "score" in item
        assert "title" in item
        assert "price" in item


def test_reproducible_across_runs(integration_catalog, integration_holdout):
    """Same inputs should produce identical metrics."""
    retrieval = CandidateRetrieval(integration_catalog)
    ranker = HeuristicRanker(integration_catalog)

    results = []
    for _ in range(2):
        ltr = LearningToRankPipeline()
        pipeline = EvaluationPipeline(
            catalog=integration_catalog,
            retrieval=retrieval,
            ranker=ranker,
            ltr_pipeline=ltr,
        )
        r = pipeline.evaluate(
            "general electronics",
            SearchFilters(category="Electronics"),
            integration_holdout,
            k=5,
        )
        results.append(r)

    for key in results[0].metrics:
        assert results[0].metrics[key] == pytest.approx(results[1].metrics[key])
