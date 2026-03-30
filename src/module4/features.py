"""
Feature construction for learning-to-rank (Module 4).

Builds dense vectors that emphasize **rating**, **review volume**, **listing
richness** (description + feature bullets), and **price–performance** within
an optional user price band (from Module 1 filters).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np

from src.module1.catalog import Product
from src.module4.exceptions import FeatureConstructionError

# Fixed layout — keep in sync with model / tests
FEATURE_NAMES: Tuple[str, ...] = (
    "rating_norm",  # seller_rating / 5
    "review_strength",  # log-scaled review count
    "description_richness",  # normalized description length
    "bullet_richness",  # normalized feature-bullet count
    "price_norm_in_band",  # position within [min, max] price window
    "value_core",  # rating × review trust × richness blend / price pressure
    "perf_per_dollar_hint",  # higher when rating is strong vs. price position
)

FEATURE_DIM = len(FEATURE_NAMES)

_MAX_DESC = 500.0
_MAX_BULLETS = 10.0
_LOG_REV_SCALE = 12.0  # ~log1p(160000) upper-ish scale for normalization


def _band_limits(
    products: Sequence[Product],
    price_band: Optional[Tuple[float, float]],
) -> Tuple[float, float]:
    """Resolve (min, max) price for normalizing ``price_norm_in_band``."""
    prices = [float(p.price) for p in products]
    if not prices:
        raise FeatureConstructionError("empty product list")
    if price_band is not None:
        lo, hi = float(price_band[0]), float(price_band[1])
        if lo > hi:
            raise FeatureConstructionError(f"price_band has min > max: {price_band}")
        return lo, hi
    return min(prices), max(prices)


def compute_quality_value_features(
    products: List[Product],
    price_band: Optional[Tuple[float, float]] = None,
) -> np.ndarray:
    """Build a feature matrix for quality / value-oriented ranking.

    Columns match ``FEATURE_NAMES`` and ``FEATURE_DIM``.

    Args:
        products: Candidate products (e.g. from Module 1 retrieval).
        price_band: Optional ``(price_min, price_max)`` from user filters.
            When omitted, the min/max **within this candidate batch** are used
            so relative price position is still meaningful.

    Returns:
        ``float64`` array of shape ``(len(products), FEATURE_DIM)``.

    Raises:
        FeatureConstructionError: Empty list or invalid band.
    """
    if not products:
        raise FeatureConstructionError("products must not be empty")

    p_lo, p_hi = _band_limits(products, price_band)
    span = p_hi - p_lo + 1e-9

    # Batch max for relative review strength (avoid divide-by-zero on single item)
    log_revs = np.array([np.log1p(float(p.rating_number or 0)) for p in products])
    max_log_rev = float(np.max(log_revs)) + 1e-9

    rows: List[List[float]] = []
    for p, lr in zip(products, log_revs):
        rating_norm = float(p.seller_rating) / 5.0

        review_strength = float(lr) / max_log_rev

        desc_len = len(p.description or "")
        description_richness = min(desc_len / _MAX_DESC, 1.0)

        n_bullets = len(p.features or [])
        bullet_richness = min(float(n_bullets) / _MAX_BULLETS, 1.0)

        price = float(p.price)
        price_norm_in_band = (price - p_lo) / span
        price_norm_in_band = float(np.clip(price_norm_in_band, 0.0, 1.0))

        # Trust-weighted "listing quality" (reviews + text) — classification inputs
        trust = 0.5 + 0.5 * review_strength
        richness = 0.55 * description_richness + 0.45 * bullet_richness
        value_core = rating_norm * trust * (0.4 + 0.6 * richness)
        # Price pressure: not always "cheapest wins" — let the learner balance
        denom = 0.35 + 0.65 * price_norm_in_band
        value_core = value_core / denom

        # Performance per dollar hint: strong rating when price position is low in band
        perf_per_dollar_hint = rating_norm * (1.0 - 0.5 * price_norm_in_band)

        rows.append(
            [
                rating_norm,
                review_strength,
                description_richness,
                bullet_richness,
                price_norm_in_band,
                value_core,
                perf_per_dollar_hint,
            ]
        )

    return np.asarray(rows, dtype=np.float64)
