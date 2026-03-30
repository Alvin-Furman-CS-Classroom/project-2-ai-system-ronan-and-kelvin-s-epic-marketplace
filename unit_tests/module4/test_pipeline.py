"""Tests for LearningToRankPipeline (module4.pipeline)."""

import numpy as np
import pytest

from src.module1.catalog import Product
from src.module4.pipeline import LearningToRankPipeline


def test_fit_rank_end_to_end(quality_products):
    pipe = LearningToRankPipeline()
    out = pipe.fit_rank(quality_products, price_band=(10.0, 130.0), top_k=3)
    assert len(out) == 3
    scores = [s for _, s in out]
    assert scores == sorted(scores, reverse=True)


def test_rank_without_fit_uses_heuristic(quality_products):
    pipe = LearningToRankPipeline()
    assert not pipe.ranker.is_fitted
    full = pipe.rank(quality_products, price_band=(10.0, 130.0))
    assert len(full) == len(quality_products)


def test_fit_graceful_when_too_few_products():
    """Single product: fit skipped, rank still returns one row."""
    one = [
        Product(id="solo", title="x", price=15.0, category="c", seller_rating=4.2, store="s"),
    ]
    pipe = LearningToRankPipeline()
    pipe.fit(one, price_band=(10.0, 20.0))
    assert not pipe.ranker.is_fitted
    ranked = pipe.rank(one)
    assert len(ranked) == 1


def test_pipeline_accepts_numpy_labels(quality_products):
    pipe = LearningToRankPipeline()
    y = np.array([1, 0, 1, 0, 1], dtype=int)
    pipe.fit(quality_products, labels=y, price_band=(10.0, 130.0))
    assert pipe.ranker.is_fitted
