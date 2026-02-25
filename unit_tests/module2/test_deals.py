"""Tests for the Deal Finder (src.module2.deals)."""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module2.deals import DealFinder, DealInfo, CategoryStats


# ── helpers ───────────────────────────────────────────────────────────

def _make_product(pid, price, rating, reviews, category="electronics"):
    return Product(
        id=pid, title=f"Product {pid}", price=price,
        category=category, seller_rating=rating, store="TestStore",
        rating_number=reviews,
    )


@pytest.fixture
def diverse_catalog() -> ProductCatalog:
    """30 electronics products with varied price/rating/reviews."""
    products = [
        _make_product("gem", 15.0, 4.9, 8000),
        _make_product("value", 20.0, 4.5, 5000),
        _make_product("premium", 200.0, 4.8, 10000),
        _make_product("avg1", 60.0, 3.5, 300),
        _make_product("avg2", 70.0, 3.6, 400),
        _make_product("avg3", 55.0, 3.4, 250),
        _make_product("avg4", 65.0, 3.7, 350),
        _make_product("avg5", 80.0, 3.3, 200),
        _make_product("avg6", 90.0, 3.2, 150),
        _make_product("avg7", 50.0, 3.8, 500),
        _make_product("avg8", 45.0, 3.0, 100),
        _make_product("avg9", 75.0, 3.1, 120),
        _make_product("avg10", 85.0, 3.9, 600),
        _make_product("avg11", 95.0, 3.5, 300),
        _make_product("avg12", 40.0, 3.6, 400),
        _make_product("avg13", 35.0, 3.4, 250),
        _make_product("avg14", 100.0, 3.7, 350),
        _make_product("avg15", 110.0, 3.3, 200),
        _make_product("avg16", 120.0, 3.2, 50),
        _make_product("avg17", 30.0, 3.8, 500),
    ]
    return ProductCatalog(products)


@pytest.fixture
def deal_finder(diverse_catalog) -> DealFinder:
    return DealFinder(diverse_catalog)


# ── category stats ────────────────────────────────────────────────────

class TestCategoryStats:
    def test_stats_computed(self, deal_finder):
        stats = deal_finder.category_stats("electronics")
        assert stats is not None
        assert stats.count == 20
        assert stats.avg_price > 0

    def test_stats_case_insensitive(self, deal_finder):
        assert deal_finder.category_stats("Electronics") is not None
        assert deal_finder.category_stats("ELECTRONICS") is not None

    def test_missing_category_returns_none(self, deal_finder):
        assert deal_finder.category_stats("nonexistent") is None


# ── deal detection ────────────────────────────────────────────────────

class TestDealDetection:
    def test_gem_is_flagged(self, deal_finder):
        """The cheap, high-rated, popular product should be a deal."""
        deal = deal_finder.get_deal("gem")
        assert deal is not None
        assert deal.deal_type in ("hidden_gem", "great_value")
        assert deal.deal_score > 0

    def test_premium_not_a_deal(self, deal_finder):
        """Expensive products should not be deals even with great ratings."""
        deal = deal_finder.get_deal("premium")
        assert deal is None

    def test_deal_info_fields(self, deal_finder):
        deal = deal_finder.get_deal("gem")
        assert deal is not None
        assert deal.price_vs_avg < 0  # cheaper than average
        assert deal.rating_vs_avg > 0  # better than average
        assert deal.category_avg_price > 0


# ── get_deals ─────────────────────────────────────────────────────────

class TestGetDeals:
    def test_returns_list(self, deal_finder):
        deals = deal_finder.get_deals()
        assert isinstance(deals, list)
        assert len(deals) > 0

    def test_sorted_by_score(self, deal_finder):
        deals = deal_finder.get_deals()
        scores = [info.deal_score for _, info in deals]
        assert scores == sorted(scores, reverse=True)

    def test_limit(self, deal_finder):
        deals = deal_finder.get_deals(limit=2)
        assert len(deals) <= 2

    def test_category_filter(self, deal_finder):
        deals = deal_finder.get_deals(category="electronics")
        assert len(deals) > 0
        deals_none = deal_finder.get_deals(category="nonexistent")
        assert len(deals_none) == 0


# ── edge cases ────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_too_few_products_in_category(self):
        """Categories with < 3 products produce no deals."""
        catalog = ProductCatalog([
            _make_product("only1", 10.0, 5.0, 1000, category="tiny"),
        ])
        finder = DealFinder(catalog)
        assert finder.get_deals(category="tiny") == []

    def test_low_review_products_excluded(self):
        """Products with very few reviews are not flagged as deals."""
        products = [_make_product(f"p{i}", 50.0, 3.5, 5) for i in range(10)]
        catalog = ProductCatalog(products)
        finder = DealFinder(catalog)
        assert finder.get_deals() == []

    def test_empty_catalog(self):
        finder = DealFinder(ProductCatalog())
        assert finder.get_deals() == []
        assert finder.get_deal("anything") is None
