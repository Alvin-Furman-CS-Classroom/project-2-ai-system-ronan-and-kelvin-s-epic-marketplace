"""Tests for TopKResult and build_top_k_payload."""

import pytest

from src.module5.payload import TopKResult, build_top_k_payload


class TestTopKResult:

    def test_frozen(self):
        r = TopKResult(query="test", k=5, results=())
        with pytest.raises(AttributeError):
            r.query = "other"

    def test_num_results(self):
        results = ({"id": "p1", "score": 0.9}, {"id": "p2", "score": 0.8})
        r = TopKResult(query="q", k=5, results=results)
        assert r.num_results == 2

    def test_product_ids(self):
        results = (
            {"id": "p1", "score": 0.9, "title": "A", "price": 10},
            {"id": "p2", "score": 0.8, "title": "B", "price": 20},
        )
        r = TopKResult(query="q", k=5, results=results)
        assert r.product_ids == ["p1", "p2"]

    def test_to_dict_without_metrics(self):
        r = TopKResult(query="q", k=3, results=())
        d = r.to_dict()
        assert d["query"] == "q"
        assert d["k"] == 3
        assert d["num_results"] == 0
        assert "metrics" not in d

    def test_to_dict_with_metrics(self):
        m = {"precision_at_k": 0.8, "ndcg_at_k": 0.9}
        r = TopKResult(query="q", k=3, results=(), metrics=m)
        d = r.to_dict()
        assert d["metrics"] == m


class TestBuildTopKPayload:

    def test_basic_payload(self, scored_candidates, sample_catalog):
        payload = build_top_k_payload(
            scored_candidates, sample_catalog, query="test", k=3,
        )
        assert payload.query == "test"
        assert payload.k == 3
        assert payload.num_results == 3
        assert payload.product_ids == ["p1", "p4", "p2"]

    def test_truncation(self, scored_candidates, sample_catalog):
        payload = build_top_k_payload(
            scored_candidates, sample_catalog, query="q", k=2,
        )
        assert payload.num_results == 2

    def test_result_schema(self, scored_candidates, sample_catalog):
        payload = build_top_k_payload(
            scored_candidates, sample_catalog, query="q", k=1,
        )
        result = payload.results[0]
        assert "id" in result
        assert "score" in result
        assert "title" in result
        assert "price" in result
        assert "category" in result
        assert "seller_rating" in result
        assert "store" in result

    def test_scores_rounded(self, scored_candidates, sample_catalog):
        payload = build_top_k_payload(
            scored_candidates, sample_catalog, query="q", k=6,
        )
        for r in payload.results:
            score_str = str(r["score"])
            decimals = len(score_str.split(".")[-1]) if "." in score_str else 0
            assert decimals <= 4

    def test_empty_candidates(self, sample_catalog):
        payload = build_top_k_payload([], sample_catalog, query="q", k=5)
        assert payload.num_results == 0

    def test_missing_catalog_entry_skipped(self, sample_catalog):
        candidates = [("missing_id", 0.99), ("p1", 0.80)]
        payload = build_top_k_payload(
            candidates, sample_catalog, query="q", k=5,
        )
        assert payload.num_results == 1
        assert payload.product_ids == ["p1"]

    def test_metrics_attached(self, scored_candidates, sample_catalog):
        metrics = {"precision_at_k": 0.75}
        payload = build_top_k_payload(
            scored_candidates, sample_catalog, query="q", k=3,
            metrics=metrics,
        )
        assert payload.metrics == metrics

    def test_score_ordering_preserved(self, scored_candidates, sample_catalog):
        payload = build_top_k_payload(
            scored_candidates, sample_catalog, query="q", k=6,
        )
        scores = [r["score"] for r in payload.results]
        assert scores == sorted(scores, reverse=True)
