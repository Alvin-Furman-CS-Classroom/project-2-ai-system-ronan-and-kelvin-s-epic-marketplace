"""Tests for EvaluationPipeline (single-query and batch)."""

from unittest.mock import MagicMock, patch

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module1.filters import SearchFilters
from src.module1.retrieval import SearchResult
from src.module2.ranker import RankedResult
from src.module5.holdout import HeldOutSet
from src.module5.pipeline import (
    BatchEvaluationResult,
    EvaluationPipeline,
    EvaluationResult,
)


@pytest.fixture
def _products():
    return [
        Product(id="p1", title="A", price=10, category="E", seller_rating=4.8, store="S"),
        Product(id="p2", title="B", price=20, category="E", seller_rating=4.5, store="S"),
        Product(id="p3", title="C", price=30, category="E", seller_rating=4.0, store="S"),
    ]


@pytest.fixture
def _catalog(_products):
    return ProductCatalog(_products)


@pytest.fixture
def _pipeline(_catalog, _products):
    """Pipeline with mocked upstream modules."""
    retrieval = MagicMock()
    retrieval.search.return_value = SearchResult(
        candidate_ids=["p1", "p2", "p3"],
        strategy="linear",
        total_scanned=3,
        elapsed_ms=0.01,
    )

    ranker = MagicMock()
    ranker.rank.return_value = RankedResult(
        ranked_candidates=[("p1", 0.9), ("p2", 0.7), ("p3", 0.5)],
        strategy="baseline",
        iterations=0,
        objective_value=1.0,
        elapsed_ms=0.1,
    )

    ltr = MagicMock()
    ltr.rank.return_value = [("p1", 0.92), ("p2", 0.78), ("p3", 0.55)]

    return EvaluationPipeline(
        catalog=_catalog,
        retrieval=retrieval,
        ranker=ranker,
        ltr_pipeline=ltr,
    )


@pytest.fixture
def _holdout():
    return HeldOutSet({"test query": {"p1", "p2"}})


class TestEvaluateSingleQuery:

    def test_returns_evaluation_result(self, _pipeline, _holdout):
        result = _pipeline.evaluate(
            "test query", SearchFilters(), _holdout, k=3,
        )
        assert isinstance(result, EvaluationResult)
        assert result.query == "test query"

    def test_payload_has_results(self, _pipeline, _holdout):
        result = _pipeline.evaluate(
            "test query", SearchFilters(), _holdout, k=3,
        )
        assert result.payload.num_results <= 3
        assert result.payload.num_results > 0

    def test_metrics_populated(self, _pipeline, _holdout):
        result = _pipeline.evaluate(
            "test query", SearchFilters(), _holdout, k=3,
        )
        assert "precision_at_k" in result.metrics
        assert "ndcg_at_k" in result.metrics
        assert "reciprocal_rank" in result.metrics
        assert "average_precision" in result.metrics

    def test_metrics_in_valid_range(self, _pipeline, _holdout):
        result = _pipeline.evaluate(
            "test query", SearchFilters(), _holdout, k=3,
        )
        for key, val in result.metrics.items():
            assert 0.0 <= val <= 1.0, f"{key} = {val}"

    def test_precision_correct(self, _pipeline, _holdout):
        """p1 and p2 relevant in top 3 → P@3 = 2/3."""
        result = _pipeline.evaluate(
            "test query", SearchFilters(), _holdout, k=3,
        )
        assert result.metrics["precision_at_k"] == pytest.approx(2 / 3)

    def test_empty_search_result(self, _catalog, _holdout):
        retrieval = MagicMock()
        retrieval.search.return_value = SearchResult(
            candidate_ids=[], strategy="linear",
            total_scanned=0, elapsed_ms=0.0,
        )
        pipeline = EvaluationPipeline(
            catalog=_catalog, retrieval=retrieval,
            ranker=MagicMock(), ltr_pipeline=MagicMock(),
        )
        result = pipeline.evaluate("q", SearchFilters(), _holdout, k=3)
        assert result.payload.num_results == 0

    def test_query_not_in_holdout(self, _pipeline):
        holdout = HeldOutSet({"other query": {"p1"}})
        result = _pipeline.evaluate(
            "unknown query", SearchFilters(), holdout, k=3,
        )
        assert result.metrics["precision_at_k"] == pytest.approx(0.0)


class TestBatchEvaluate:

    def test_batch_returns_result(self, _pipeline, _holdout):
        queries = [("test query", SearchFilters())]
        result = _pipeline.batch_evaluate(queries, _holdout, k=3)
        assert isinstance(result, BatchEvaluationResult)
        assert result.num_queries == 1

    def test_aggregate_metrics(self, _pipeline):
        holdout = HeldOutSet({
            "q1": {"p1", "p2"},
            "q2": {"p1"},
        })
        queries = [
            ("q1", SearchFilters()),
            ("q2", SearchFilters()),
        ]
        result = _pipeline.batch_evaluate(queries, holdout, k=3)
        assert "mean_precision_at_k" in result.aggregate
        assert "mean_ndcg_at_k" in result.aggregate

    def test_per_query_results(self, _pipeline):
        holdout = HeldOutSet({"q1": {"p1"}, "q2": {"p2"}})
        queries = [("q1", SearchFilters()), ("q2", SearchFilters())]
        result = _pipeline.batch_evaluate(queries, holdout, k=3)
        assert "q1" in result.per_query
        assert "q2" in result.per_query

    def test_empty_batch(self, _pipeline, _holdout):
        result = _pipeline.batch_evaluate([], _holdout, k=3)
        assert result.num_queries == 0
        assert result.aggregate == {}
