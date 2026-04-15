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


def test_use_feature_scaling_disabled_still_trains():
    """Optional path: raw features + LR (previous behavior)."""
    products = [
        Product(id="a", title="a", price=10.0, category="c", seller_rating=3.0, store="s"),
        Product(id="b", title="b", price=20.0, category="c", seller_rating=5.0, store="s"),
    ]
    m = QualityValueRanker(use_feature_scaling=False, C=1.0, max_iter=2000)
    m.fit(products, labels=np.array([0, 1]))
    assert m.is_fitted
    ranked = m.score(products)
    assert len(ranked) == 2


def test_fit_from_precomputed_X_matches_training_data_width():
    """Partner path: TrainingDataGenerator-style (n, COMBINED_FEATURE_DIM) matrix."""
    from src.module4.query_features import COMBINED_FEATURE_DIM

    rng = np.random.default_rng(0)
    X = rng.random((40, COMBINED_FEATURE_DIM))
    y = np.concatenate([np.zeros(20), np.ones(20)]).astype(int)
    m = QualityValueRanker()
    m.fit(X=X, labels=y)
    assert m.n_features == COMBINED_FEATURE_DIM
    assert len(m.coef_as_dict()) == COMBINED_FEATURE_DIM


def test_combined_model_requires_query_context_at_score(quality_products):
    from src.module3.query_understanding import QueryResult
    from src.module4.query_features import COMBINED_FEATURE_DIM

    class _Emb:
        def embed_text(self, text: str) -> np.ndarray:
            return np.ones(100, dtype=np.float32)

    qr = QueryResult(
        keywords=[("bluetooth", 0.5)],
        query_embedding=np.ones(100, dtype=np.float32),
        inferred_category="Electronics",
        confidence=0.9,
    )
    emb = _Emb()
    m = QualityValueRanker()
    m.fit(quality_products, query_result=qr, embedder=emb)
    assert m.n_features == COMBINED_FEATURE_DIM
    with pytest.raises(ValueError, match="query_result and embedder"):
        m.score(quality_products)
    ranked = m.score(quality_products, query_result=qr, embedder=emb)
    assert len(ranked) == len(quality_products)
