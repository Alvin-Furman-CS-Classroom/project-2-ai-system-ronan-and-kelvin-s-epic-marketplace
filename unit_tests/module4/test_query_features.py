"""Tests for query–product feature construction (module4.query_features)."""

import numpy as np
import pytest

from src.module1.catalog import Product
from src.module3.query_understanding import QueryResult
from src.module4.exceptions import FeatureConstructionError
from src.module4.query_features import (
    QUERY_FEATURE_DIM,
    QUERY_FEATURE_NAMES,
    _keyword_overlap,
    _title_relevance,
    compute_query_product_features,
    compute_combined_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeEmbedder:
    """Minimal stand-in for ProductEmbedder to avoid training Word2Vec."""

    def __init__(self, mapping: dict[str, np.ndarray] | None = None):
        self._map = mapping or {}

    def embed_text(self, text: str) -> np.ndarray:
        for key, vec in self._map.items():
            if key in text.lower():
                return vec
        return np.zeros(100, dtype=np.float32)


def _make_qr(
    keywords=None,
    embedding=None,
    category="Electronics",
    confidence=0.85,
) -> QueryResult:
    return QueryResult(
        keywords=keywords or [("bluetooth", 0.7), ("headphones", 0.6)],
        query_embedding=embedding if embedding is not None else np.random.rand(100).astype(np.float32),
        inferred_category=category,
        confidence=confidence,
    )


def _make_product(**overrides) -> Product:
    defaults = dict(
        id="p1",
        title="Bluetooth Headphones Wireless",
        price=30.0,
        category="Electronics",
        seller_rating=4.5,
        store="S",
        description="Great bluetooth headphones with noise cancelling.",
        rating_number=500,
        features=["a", "b"],
    )
    defaults.update(overrides)
    return Product(**defaults)


# ---------------------------------------------------------------------------
# QUERY_FEATURE_NAMES / dim
# ---------------------------------------------------------------------------

def test_query_feature_dim_matches_names():
    assert len(QUERY_FEATURE_NAMES) == QUERY_FEATURE_DIM


def test_query_feature_names_are_strings():
    assert all(isinstance(n, str) for n in QUERY_FEATURE_NAMES)


# ---------------------------------------------------------------------------
# _keyword_overlap
# ---------------------------------------------------------------------------

def test_keyword_overlap_full_match():
    kw = [("bluetooth", 0.7), ("headphones", 0.6)]
    p = _make_product(title="Bluetooth Headphones", description="wireless bluetooth headphones")
    assert _keyword_overlap(kw, p) == 1.0


def test_keyword_overlap_partial_match():
    kw = [("bluetooth", 0.7), ("headphones", 0.6), ("gaming", 0.3)]
    p = _make_product(title="Bluetooth Speaker", description="portable speaker")
    overlap = _keyword_overlap(kw, p)
    assert 0.0 < overlap < 1.0


def test_keyword_overlap_no_match():
    kw = [("kitchen", 0.8), ("blender", 0.7)]
    p = _make_product(title="Bluetooth Headphones", description="wireless headphones")
    assert _keyword_overlap(kw, p) == 0.0


def test_keyword_overlap_empty_keywords():
    p = _make_product()
    assert _keyword_overlap([], p) == 0.0


# ---------------------------------------------------------------------------
# _title_relevance
# ---------------------------------------------------------------------------

def test_title_relevance_high_for_direct_match():
    vec = np.random.rand(100).astype(np.float32)
    vec /= np.linalg.norm(vec)
    embedder = _FakeEmbedder({"bluetooth": vec})
    p = _make_product(title="Bluetooth Headphones Wireless")
    score = _title_relevance({"bluetooth", "headphones"}, vec, p, embedder)
    assert score > 0.0


def test_title_relevance_zero_for_no_query_tokens():
    embedder = _FakeEmbedder()
    p = _make_product()
    score = _title_relevance(set(), np.zeros(100, dtype=np.float32), p, embedder)
    assert score == 0.0


def test_title_relevance_zero_for_empty_title():
    embedder = _FakeEmbedder()
    p = _make_product(title="")
    score = _title_relevance({"laptop"}, np.ones(100, dtype=np.float32), p, embedder)
    assert score == 0.0


# ---------------------------------------------------------------------------
# compute_query_product_features
# ---------------------------------------------------------------------------

def test_empty_products_raises():
    qr = _make_qr()
    embedder = _FakeEmbedder()
    with pytest.raises(FeatureConstructionError, match="empty"):
        compute_query_product_features([], qr, embedder)


def test_matrix_shape():
    products = [_make_product(id=f"p{i}") for i in range(5)]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    X = compute_query_product_features(products, qr, embedder)
    assert X.shape == (5, QUERY_FEATURE_DIM)
    assert X.dtype == np.float64


def test_cosine_similarity_column_bounded():
    vec = np.random.rand(100).astype(np.float32)
    vec /= np.linalg.norm(vec)
    embedder = _FakeEmbedder({"bluetooth": vec})
    qr = _make_qr(embedding=vec)
    products = [_make_product()]
    X = compute_query_product_features(products, qr, embedder)
    assert -1.0 - 1e-6 <= X[0, 0] <= 1.0 + 1e-6


def test_category_match_column():
    qr = _make_qr(category="Electronics")
    products = [
        _make_product(id="match", category="Electronics"),
        _make_product(id="miss", category="Kitchen"),
    ]
    embedder = _FakeEmbedder()
    X = compute_query_product_features(products, qr, embedder)
    assert X[0, 2] == 1.0  # category_match
    assert X[1, 2] == 0.0


def test_confidence_column_same_for_all():
    qr = _make_qr(confidence=0.92)
    products = [_make_product(id="a"), _make_product(id="b")]
    embedder = _FakeEmbedder()
    X = compute_query_product_features(products, qr, embedder)
    assert X[0, 3] == pytest.approx(0.92)
    assert X[1, 3] == pytest.approx(0.92)


def test_no_inferred_category_gives_zero_match():
    qr = _make_qr(category=None, confidence=0.0)
    products = [_make_product()]
    embedder = _FakeEmbedder()
    X = compute_query_product_features(products, qr, embedder)
    assert X[0, 2] == 0.0


# ---------------------------------------------------------------------------
# module3_relevance_score column
# ---------------------------------------------------------------------------

def test_module3_score_default_zero():
    products = [_make_product()]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    X = compute_query_product_features(products, qr, embedder)
    assert X[0, 4] == 0.0


def test_module3_score_from_dict():
    products = [_make_product(id="p1"), _make_product(id="p2", title="Other Thing")]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    m3 = {"p1": 0.95, "p2": 0.42}
    X = compute_query_product_features(products, qr, embedder, module3_scores=m3)
    assert X[0, 4] == pytest.approx(0.95)
    assert X[1, 4] == pytest.approx(0.42)


def test_module3_score_missing_product_defaults_zero():
    products = [_make_product(id="p1")]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    m3 = {"other_id": 0.9}
    X = compute_query_product_features(products, qr, embedder, module3_scores=m3)
    assert X[0, 4] == 0.0


# ---------------------------------------------------------------------------
# compute_combined_features
# ---------------------------------------------------------------------------

def test_combined_shape():
    from src.module4.features import FEATURE_DIM

    products = [_make_product(id=f"p{i}") for i in range(3)]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    X = compute_combined_features(products, qr, embedder, price_band=(10.0, 100.0))
    assert X.shape == (3, FEATURE_DIM + QUERY_FEATURE_DIM)


def test_combined_dtype():
    products = [_make_product()]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    X = compute_combined_features(products, qr, embedder)
    assert X.dtype == np.float64


def test_combined_quality_columns_preserved():
    """First columns should match standalone quality features."""
    from src.module4.features import FEATURE_DIM, compute_quality_value_features

    products = [_make_product(id="a"), _make_product(id="b", price=60.0)]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    X_combined = compute_combined_features(products, qr, embedder, price_band=(10.0, 100.0))
    X_quality = compute_quality_value_features(products, price_band=(10.0, 100.0))
    np.testing.assert_array_almost_equal(X_combined[:, :FEATURE_DIM], X_quality)


def test_combined_with_module3_scores():
    """Module 3 scores should appear in the module3_relevance_score column."""
    from src.module4.features import FEATURE_DIM
    from src.module4.query_features import COMBINED_FEATURE_DIM

    products = [_make_product(id="a"), _make_product(id="b", price=60.0)]
    qr = _make_qr()
    embedder = _FakeEmbedder()
    m3 = {"a": 0.88, "b": 0.33}
    X = compute_combined_features(products, qr, embedder, module3_scores=m3)
    assert X.shape == (2, COMBINED_FEATURE_DIM)
    m3_col = FEATURE_DIM + QUERY_FEATURE_NAMES.index("module3_relevance_score")
    assert X[0, m3_col] == pytest.approx(0.88)
    assert X[1, m3_col] == pytest.approx(0.33)
