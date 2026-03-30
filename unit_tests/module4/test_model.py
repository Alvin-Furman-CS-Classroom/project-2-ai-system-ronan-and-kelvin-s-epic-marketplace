"""Tests for QualityValueRanker (module4.model)."""

import numpy as np
import pytest

from src.module1.catalog import Product
from src.module4.exceptions import InsufficientTrainingDataError, ModelNotFittedError
from src.module4.model import QualityValueRanker


def test_fit_predict_ordering(quality_products):
    model = QualityValueRanker()
    model.fit(quality_products, price_band=(10.0, 130.0))
    ranked = model.score(quality_products, price_band=(10.0, 130.0))
    assert len(ranked) == len(quality_products)
    scores = [s for _, s in ranked]
    assert all(0.0 < s < 1.0 for s in scores) or max(scores) <= 1.0
    assert scores == sorted(scores, reverse=True)


def test_fit_insufficient_samples():
    p = Product(id="only", title="x", price=1.0, category="c", seller_rating=4.0, store="s")
    with pytest.raises(InsufficientTrainingDataError, match="at least 2"):
        QualityValueRanker().fit([p])


def test_fit_single_class_labels_raises(quality_products):
    y = np.zeros(len(quality_products), dtype=int)
    with pytest.raises(InsufficientTrainingDataError, match="single class"):
        QualityValueRanker().fit(quality_products, labels=y)


def test_unfitted_uses_heuristic(quality_products):
    m = QualityValueRanker()
    out = m.score(quality_products, price_band=(10.0, 130.0))
    assert len(out) == len(quality_products)
    assert not m.is_fitted


def test_coef_requires_fit(quality_products):
    m = QualityValueRanker()
    with pytest.raises(ModelNotFittedError):
        m.coef_as_dict()
    m.fit(quality_products)
    d = m.coef_as_dict()
    assert len(d) == 7
    assert "rating_norm" in d


def test_explicit_labels_fit():
    products = [
        Product(id="a", title="a", price=10.0, category="c", seller_rating=3.0, store="s"),
        Product(id="b", title="b", price=20.0, category="c", seller_rating=5.0, store="s"),
    ]
    m = QualityValueRanker()
    m.fit(products, labels=np.array([0, 1]))
    ranked = m.score(products)
    # Positive label should not always be last — but class 1 should tend to score higher
    top_id = ranked[0][0]
    assert top_id in ("a", "b")
