"""
Scoring functions for heuristic re-ranking.

Provides a configurable weighted-linear scoring model that maps raw product
features (price, seller rating, popularity, category match, listing quality)
into a single [0, 1] heuristic score.  Higher is better.

The scoring formula is::

    score = w_price   × price_score
          + w_rating  × rating_score
          + w_pop     × popularity_score
          + w_cat     × category_match_score
          + w_rich    × richness_score

Each component is normalised to [0, 1] before weighting, and the weights
themselves are normalised to sum to 1 so the final score stays in [0, 1].
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Optional

from src.module1.catalog import Product
from src.module2.exceptions import InvalidWeightsError


# ---------------------------------------------------------------------------
# Scoring configuration
# ---------------------------------------------------------------------------

@dataclass
class ScoringConfig:
    """Configurable weights for the heuristic scoring function.

    All weights must be non-negative.  They are automatically normalised to
    sum to 1, so the absolute values only matter *relative* to each other.

    Attributes:
        price: Weight for the inverted-price signal (lower price → higher score).
        rating: Weight for the seller-rating signal.
        popularity: Weight for the review-count popularity signal.
        category_match: Weight for exact category match with the query.
        richness: Weight for listing-quality / description-richness.

    Example:
        >>> cfg = ScoringConfig(price=0.25, rating=0.35, popularity=0.20,
        ...                     category_match=0.15, richness=0.05)
    """

    price: float = 0.25
    rating: float = 0.35
    popularity: float = 0.20
    category_match: float = 0.15
    richness: float = 0.05

    def __post_init__(self) -> None:
        """Validate that weights are non-negative and not all zero."""
        weights = self._as_list()
        if any(w < 0 for w in weights):
            raise InvalidWeightsError(
                f"All weights must be non-negative, got: {weights}"
            )
        if sum(weights) == 0:
            raise InvalidWeightsError("At least one weight must be positive.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _as_list(self) -> list[float]:
        """Return weights as an ordered list.

        Returns:
            List of [price, rating, popularity, category_match, richness].
        """
        return [self.price, self.rating, self.popularity,
                self.category_match, self.richness]

    def normalized(self) -> list[float]:
        """Return weights normalised to sum to 1.

        Returns:
            List of normalised floats in the same order as ``_as_list``.
        """
        raw = self._as_list()
        total = sum(raw)
        return [w / total for w in raw]


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalize(value: float, lo: float, hi: float) -> float:
    """Min-max normalise *value* into [0, 1].

    Args:
        value: The raw value.
        lo: Minimum of the observed range.
        hi: Maximum of the observed range.

    Returns:
        Normalised float in [0, 1].  Returns 0.5 if lo == hi
        (all values identical).
    """
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _price_score(product: Product, price_range: tuple[float, float]) -> float:
    """Inverted price score — cheaper products score higher.

    Args:
        product: The product to score.
        price_range: (min_price, max_price) across all candidates.

    Returns:
        Float in [0, 1] — 1.0 for the cheapest, 0.0 for the most expensive.
    """
    return 1.0 - normalize(product.price, price_range[0], price_range[1])


def _rating_score(product: Product) -> float:
    """Seller-rating score normalised to [0, 1].

    Args:
        product: The product to score.

    Returns:
        ``seller_rating / 5.0``, clamped to [0, 1].
    """
    return min(1.0, max(0.0, product.seller_rating / 5.0))


def _popularity_score(
    product: Product, pop_range: tuple[float, float]
) -> float:
    """Popularity score based on log-scaled review count.

    Args:
        product: The product to score.
        pop_range: (min_log_count, max_log_count) across candidates.

    Returns:
        Float in [0, 1] — 1.0 for the most-reviewed product.
    """
    count = product.rating_number or 0
    log_count = math.log1p(count)
    return normalize(log_count, pop_range[0], pop_range[1])


def _category_match_score(product: Product, target_category: Optional[str]) -> float:
    """Binary category-match score.

    Args:
        product: The product to score.
        target_category: The category to match (case-insensitive).

    Returns:
        1.0 if the product's category matches, else 0.0.
        Returns 0.5 if no target category is specified.
    """
    if target_category is None:
        return 0.5
    return 1.0 if product.category.lower() == target_category.lower() else 0.0


def _richness_score(product: Product) -> float:
    """Listing-quality score based on description length and features.

    A proxy for how complete / professional the product listing is.

    Args:
        product: The product to score.

    Returns:
        Float in [0, 1].
    """
    desc_len = len(product.description or "")
    desc_component = min(desc_len / 500.0, 1.0)

    feature_count = len(product.features or [])
    feat_component = min(feature_count / 10.0, 1.0)

    return 0.6 * desc_component + 0.4 * feat_component


# ---------------------------------------------------------------------------
# Public scoring API
# ---------------------------------------------------------------------------

def compute_feature_ranges(products: list[Product]) -> Dict[str, tuple[float, float]]:
    """Compute min/max ranges for normalisation across a candidate set.

    Args:
        products: List of candidate products.

    Returns:
        Dict with keys ``"price"`` and ``"popularity"``, each mapping to
        a ``(min, max)`` tuple.
    """
    if not products:
        return {"price": (0.0, 0.0), "popularity": (0.0, 0.0)}

    prices = [p.price for p in products]
    pops = [math.log1p(p.rating_number or 0) for p in products]

    return {
        "price": (min(prices), max(prices)),
        "popularity": (min(pops), max(pops)),
    }


def compute_score(
    product: Product,
    config: ScoringConfig,
    feature_ranges: Dict[str, tuple[float, float]],
    target_category: Optional[str] = None,
) -> float:
    """Compute the heuristic relevance score for a single product.

    The score is a weighted linear combination of normalised features.
    Higher is better.  The result is in [0, 1].

    Args:
        product: The product to score.
        config: Weight configuration.
        feature_ranges: Precomputed ``{"price": (lo, hi), "popularity": (lo, hi)}``.
        target_category: Optional category for the category-match component.

    Returns:
        Heuristic score in [0, 1].

    Example:
        >>> from src.module1.catalog import Product
        >>> p = Product(id="x", title="T", price=20, category="home",
        ...             seller_rating=4.5, store="S")
        >>> ranges = {"price": (10, 50), "popularity": (0, 5)}
        >>> compute_score(p, ScoringConfig(), ranges)  # doctest: +SKIP
        0.72...
    """
    w = config.normalized()

    components = [
        _price_score(product, feature_ranges["price"]),
        _rating_score(product),
        _popularity_score(product, feature_ranges["popularity"]),
        _category_match_score(product, target_category),
        _richness_score(product),
    ]

    return sum(wi * ci for wi, ci in zip(w, components))
