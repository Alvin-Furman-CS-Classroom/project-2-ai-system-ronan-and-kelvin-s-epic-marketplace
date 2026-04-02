"""
Integration tests: Module 4 LTR with catalog-like products.
"""

import numpy as np

from src.module1.catalog import Product, ProductCatalog
from src.module4.pipeline import LearningToRankPipeline


def test_module4_package_importable():
    import src.module4 as m4

    assert m4.__doc__
    assert "QualityValueRanker" in m4.__all__
    assert "TrainingDataGenerator" in m4.__all__
    assert "compute_combined_features" in m4.__all__
    assert "COMBINED_FEATURE_DIM" in m4.__all__


def test_pipeline_with_small_catalog():
    """End-to-end: build products → fit_rank with price band from filters."""
    products = [
        Product(
            id="p1",
            title="USB Cable",
            price=12.0,
            category="Electronics",
            seller_rating=4.1,
            store="A",
            description="x" * 100,
            rating_number=500,
            features=["a", "b"],
        ),
        Product(
            id="p2",
            title="USB-C Hub",
            price=35.0,
            category="Electronics",
            seller_rating=4.8,
            store="B",
            description="x" * 400,
            rating_number=6000,
            features=["a", "b", "c", "d"],
        ),
    ]
    catalog = ProductCatalog(products)
    pipe = LearningToRankPipeline()
    ranked = pipe.fit_rank(list(catalog), price_band=(10.0, 40.0), top_k=2)
    assert ranked[0][0] == "p2"
    assert len(ranked) == 2


def test_query_features_importable():
    from src.module4.query_features import (
        QUERY_FEATURE_DIM,
        QUERY_FEATURE_NAMES,
        compute_query_product_features,
        compute_combined_features,
    )
    assert QUERY_FEATURE_DIM == len(QUERY_FEATURE_NAMES)
    assert QUERY_FEATURE_DIM == 4


def test_training_data_importable():
    from src.module4.training_data import (
        SAMPLE_QUERIES,
        TrainingDataGenerator,
    )
    assert len(SAMPLE_QUERIES) >= 10
