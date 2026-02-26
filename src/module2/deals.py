"""
Deal Finder — surfaces products with unusually high value relative to their category.

Computes a *deal score* for every product by comparing its quality (rating,
popularity) against its price relative to the category average.  Products
in the top percentiles are tagged as deals.

Deal types:
    - **hidden_gem** — top 5% deal score within category.
    - **great_value** — top 15% (but not top 5%).
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.module1.catalog import Product, ProductCatalog


# ── thresholds ────────────────────────────────────────────────────────
HIDDEN_GEM_PERCENTILE = 0.05
GREAT_VALUE_PERCENTILE = 0.15
MIN_REVIEWS_FOR_DEAL = 20
MIN_PRODUCTS_PER_CATEGORY = 3
MAX_RATING = 5.0
QUALITY_RATING_WEIGHT = 0.6
QUALITY_POPULARITY_WEIGHT = 0.4
MIN_RELATIVE_PRICE = 0.01


@dataclass(frozen=True)
class CategoryStats:
    """Aggregate statistics for a single category."""

    avg_price: float
    avg_rating: float
    avg_log_popularity: float
    count: int


@dataclass(frozen=True)
class DealInfo:
    """Deal metadata attached to a single product."""

    deal_score: float
    deal_type: str  # "hidden_gem" | "great_value"
    price_vs_avg: float  # percentage, negative = cheaper
    rating_vs_avg: float  # percentage, positive = better
    category_avg_price: float


class DealFinder:
    """Identifies deals across the catalog by comparing products to category peers.

    Args:
        catalog: The product catalog to analyse.
    """

    def __init__(self, catalog: ProductCatalog) -> None:
        self._catalog = catalog
        self._category_stats: Dict[str, CategoryStats] = {}
        self._deal_map: Dict[str, DealInfo] = {}
        self._compute()

    # ── public API ────────────────────────────────────────────────────

    def get_deal(self, product_id: str) -> Optional[DealInfo]:
        """Return deal info for a product, or ``None`` if it's not a deal."""
        return self._deal_map.get(product_id)

    def get_deals(
        self,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[tuple]:
        """Return top deals as ``(product_id, DealInfo)`` pairs.

        Args:
            category: Optional filter to a single category.
            limit: Max results.

        Returns:
            List of ``(product_id, DealInfo)`` sorted by deal_score descending.
        """
        items = list(self._deal_map.items())
        if category:
            cat_lower = category.lower()
            items = [
                (pid, info)
                for pid, info in items
                if self._catalog.get(pid) is not None
                and self._catalog[pid].category.lower() == cat_lower
            ]
        items.sort(key=lambda t: t[1].deal_score, reverse=True)
        return items[:limit]

    def category_stats(self, category: str) -> Optional[CategoryStats]:
        """Return aggregate stats for a category (case-insensitive)."""
        return self._category_stats.get(category.lower())

    # ── internals ─────────────────────────────────────────────────────

    def _compute(self) -> None:
        """Build category stats and tag deals."""
        by_cat: Dict[str, List[Product]] = {}
        for product in self._catalog:
            key = product.category.lower()
            by_cat.setdefault(key, []).append(product)

        for cat_key, products in by_cat.items():
            if len(products) < MIN_PRODUCTS_PER_CATEGORY:
                continue

            avg_price = sum(p.price for p in products) / len(products)
            avg_rating = sum(p.seller_rating for p in products) / len(products)
            log_pops = [math.log1p(p.rating_number or 0) for p in products]
            avg_log_pop = sum(log_pops) / len(log_pops)

            self._category_stats[cat_key] = CategoryStats(
                avg_price=avg_price,
                avg_rating=avg_rating,
                avg_log_popularity=avg_log_pop,
                count=len(products),
            )

            scores: List[tuple] = []
            for p in products:
                reviews = p.rating_number or 0
                if reviews < MIN_REVIEWS_FOR_DEAL or p.price <= 0:
                    continue

                quality = (
                    QUALITY_RATING_WEIGHT * (p.seller_rating / MAX_RATING)
                    + QUALITY_POPULARITY_WEIGHT * self._popularity_percentile(p, products)
                )
                relative_price = p.price / avg_price if avg_price > 0 else 1.0
                deal_score = quality / max(relative_price, MIN_RELATIVE_PRICE)
                scores.append((p.id, deal_score))

            if not scores:
                continue

            scores.sort(key=lambda t: t[1], reverse=True)
            n = len(scores)
            gem_cutoff = max(1, int(n * HIDDEN_GEM_PERCENTILE))
            value_cutoff = max(gem_cutoff + 1, int(n * GREAT_VALUE_PERCENTILE))

            for rank, (pid, dscore) in enumerate(scores):
                if rank < gem_cutoff:
                    deal_type = "hidden_gem"
                elif rank < value_cutoff:
                    deal_type = "great_value"
                else:
                    continue

                product = self._catalog[pid]
                price_vs = (
                    ((product.price - avg_price) / avg_price) * 100
                    if avg_price > 0
                    else 0.0
                )
                rating_vs = (
                    ((product.seller_rating - avg_rating) / avg_rating) * 100
                    if avg_rating > 0
                    else 0.0
                )

                self._deal_map[pid] = DealInfo(
                    deal_score=round(dscore, 4),
                    deal_type=deal_type,
                    price_vs_avg=round(price_vs, 1),
                    rating_vs_avg=round(rating_vs, 1),
                    category_avg_price=round(avg_price, 2),
                )

    @staticmethod
    def _popularity_percentile(product: Product, peers: List[Product]) -> float:
        """Fraction of peers this product's review count exceeds."""
        count = product.rating_number or 0
        below = sum(1 for p in peers if (p.rating_number or 0) < count)
        return below / max(len(peers) - 1, 1)
