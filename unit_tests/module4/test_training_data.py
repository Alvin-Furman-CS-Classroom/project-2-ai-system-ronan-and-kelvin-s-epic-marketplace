"""Tests for synthetic training data generation (module4.training_data)."""

import numpy as np
import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module3.query_understanding import QueryResult
from src.module4.exceptions import InsufficientTrainingDataError
from src.module4.training_data import (
    SAMPLE_QUERIES,
    TrainingDataGenerator,
    _keyword_overlap_ratio,
    _LABEL_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight fakes to avoid training real NLP models
# ---------------------------------------------------------------------------

class _FakeEmbedder:
    """Stand-in that returns deterministic embeddings based on text content."""

    def embed_text(self, text: str) -> np.ndarray:
        np.random.seed(hash(text[:20]) % 2**31)
        return np.random.rand(100).astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_text(query)

    @property
    def vocabulary(self):
        return ["bluetooth", "headphones", "wireless", "keyboard", "mouse"]


class _FakeQU:
    """Stand-in for QueryUnderstanding that returns canned results."""

    def __init__(self, embedder):
        self._embedder = embedder

    def understand(self, query: str) -> QueryResult:
        return QueryResult(
            keywords=[("bluetooth", 0.7), ("headphones", 0.6)],
            query_embedding=self._embedder.embed_query(query),
            inferred_category="Electronics",
            confidence=0.85,
        )


def _small_catalog() -> ProductCatalog:
    products = [
        Product(
            id=f"p{i}",
            title=f"Product {i} bluetooth headphones",
            price=10.0 + i * 15,
            category="Electronics" if i % 2 == 0 else "Kitchen",
            seller_rating=3.5 + (i % 5) * 0.3,
            store="Store",
            description=f"Description for product {i} with some details." * 3,
            rating_number=100 * (i + 1),
            features=[f"feat{j}" for j in range(i % 5)],
        )
        for i in range(20)
    ]
    return ProductCatalog(products)


# ---------------------------------------------------------------------------
# _keyword_overlap_ratio
# ---------------------------------------------------------------------------

def test_keyword_overlap_ratio_full():
    kw = [("bluetooth", 0.7), ("headphones", 0.6)]
    p = Product(
        id="x", title="Bluetooth Headphones", price=10,
        category="E", seller_rating=4.0, store="S",
        description="bluetooth headphones",
    )
    assert _keyword_overlap_ratio(kw, p) == 1.0


def test_keyword_overlap_ratio_empty_keywords():
    p = Product(id="x", title="T", price=10, category="E", seller_rating=4.0, store="S")
    assert _keyword_overlap_ratio([], p) == 0.0


# ---------------------------------------------------------------------------
# SAMPLE_QUERIES
# ---------------------------------------------------------------------------

def test_sample_queries_not_empty():
    assert len(SAMPLE_QUERIES) >= 10


def test_sample_queries_are_strings():
    assert all(isinstance(q, str) and len(q) > 3 for q in SAMPLE_QUERIES)


# ---------------------------------------------------------------------------
# _LABEL_WEIGHTS
# ---------------------------------------------------------------------------

def test_label_weights_sum_roughly_one():
    assert abs(sum(_LABEL_WEIGHTS.values()) - 1.0) < 0.01


def test_label_weights_all_positive():
    assert all(v > 0 for v in _LABEL_WEIGHTS.values())


# ---------------------------------------------------------------------------
# TrainingDataGenerator
# ---------------------------------------------------------------------------

def test_generate_returns_X_y():
    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones", "kitchen blender"],
    )
    X, y = gen.generate(max_products_per_query=10, seed=42)

    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.ndim == 2
    assert y.ndim == 1
    assert X.shape[0] == y.shape[0]
    assert X.shape[0] > 0


def test_generate_labels_are_binary():
    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones"],
    )
    _, y = gen.generate(max_products_per_query=10, seed=42)

    assert set(np.unique(y)).issubset({0, 1})


def test_generate_has_both_classes():
    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones", "wireless mouse", "laptop stand"],
    )
    _, y = gen.generate(max_products_per_query=15, seed=42)

    assert 0 in y and 1 in y


def test_generate_deterministic_with_same_seed():
    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones"],
    )
    X1, y1 = gen.generate(max_products_per_query=10, seed=99)
    X2, y2 = gen.generate(max_products_per_query=10, seed=99)

    np.testing.assert_array_equal(X1, X2)
    np.testing.assert_array_equal(y1, y2)


def test_generate_different_seeds_differ():
    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones"],
    )
    _, y1 = gen.generate(max_products_per_query=15, seed=1)
    _, y2 = gen.generate(max_products_per_query=15, seed=999)

    assert not np.array_equal(y1, y2)


def test_generate_feature_dimension():
    """Feature matrix should have quality features + query features."""
    from src.module4.features import FEATURE_DIM
    from src.module4.query_features import QUERY_FEATURE_DIM

    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones"],
    )
    X, _ = gen.generate(max_products_per_query=10, seed=42)

    assert X.shape[1] == FEATURE_DIM + QUERY_FEATURE_DIM


def test_generate_max_products_caps_samples():
    catalog = _small_catalog()
    embedder = _FakeEmbedder()
    qu = _FakeQU(embedder)

    gen = TrainingDataGenerator(
        catalog=catalog,
        query_understanding=qu,
        embedder=embedder,
        sample_queries=["bluetooth headphones"],
    )
    X, _ = gen.generate(max_products_per_query=5, seed=42)

    assert X.shape[0] == 5
