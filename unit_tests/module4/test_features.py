"""Tests for LTR feature construction (module4.features)."""

import numpy as np
import pytest

from src.module1.catalog import Product
from src.module4.exceptions import FeatureConstructionError
from src.module4.features import (
    FEATURE_DIM,
    FEATURE_NAMES,
    compute_quality_value_features,
)


def test_feature_dim_matches_names():
    assert len(FEATURE_NAMES) == FEATURE_DIM


def test_empty_products_raises():
    with pytest.raises(FeatureConstructionError, match="empty"):
        compute_quality_value_features([])


def test_invalid_price_band_raises():
    p = Product(
        id="p",
        title="t",
        price=10.0,
        category="c",
        seller_rating=4.0,
        store="s",
    )
    with pytest.raises(FeatureConstructionError, match="min > max"):
        compute_quality_value_features([p], price_band=(100.0, 10.0))


def test_matrix_shape_and_bounds(quality_products):
    X = compute_quality_value_features(quality_products, price_band=(10.0, 130.0))
    assert X.shape == (len(quality_products), FEATURE_DIM)
    assert X.dtype == np.float64
    assert np.all(X[:, 0] >= 0) and np.all(X[:, 0] <= 1.0)  # rating_norm
    assert np.all(X[:, 4] >= 0) and np.all(X[:, 4] <= 1.0)  # price_norm_in_band


def test_price_band_vs_batch_normalization():
    products = [
        Product(id="a", title="a", price=20.0, category="c", seller_rating=4.5, store="s"),
        Product(id="b", title="b", price=80.0, category="c", seller_rating=4.5, store="s"),
    ]
    X_batch = compute_quality_value_features(products, price_band=None)
    X_band = compute_quality_value_features(products, price_band=(0.0, 100.0))
    # Same two prices: band 0–100 gives different spread than batch min-max only
    assert not np.allclose(X_batch[:, 4], X_band[:, 4])
