"""
Integration tests for Module 1: Candidate Retrieval.

These tests verify end-to-end behaviour across the Module 1 components
(catalog loading, filter construction, search execution) working together,
rather than testing each class in isolation.

They use an in-memory catalog built from fixture data (no external files
required) and exercise the full search pipeline: filters -> retrieval -> result.
"""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module1.filters import SearchFilters
from src.module1.retrieval import CandidateRetrieval, SearchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def catalog() -> ProductCatalog:
    """
    A realistic 15-product catalog spanning three categories and four stores.
    
    Used to test the full pipeline without needing gzipped data files.
    """
    products = [
        # --- Home ---
        Product(id="H1", title="Ceramic Mug", price=18.00, category="Home & Kitchen", seller_rating=4.8, store="CraftCo"),
        Product(id="H2", title="Glass Vase", price=35.00, category="Home & Kitchen", seller_rating=4.5, store="CraftCo"),
        Product(id="H3", title="Wooden Bowl", price=45.00, category="Home & Kitchen", seller_rating=4.2, store="HomeGoods"),
        Product(id="H4", title="Metal Lamp", price=60.00, category="Home & Kitchen", seller_rating=4.9, store="CraftCo"),
        Product(id="H5", title="Plant Pot", price=22.00, category="Home & Kitchen", seller_rating=4.6, store="HomeGoods"),
        # --- Electronics ---
        Product(id="E1", title="Phone Case", price=15.00, category="Electronics", seller_rating=4.0, store="TechMart"),
        Product(id="E2", title="USB Cable", price=8.00, category="Electronics", seller_rating=3.8, store="TechMart"),
        Product(id="E3", title="Wireless Headphones", price=89.99, category="Electronics", seller_rating=4.7, store="AudioPlus"),
        Product(id="E4", title="Bluetooth Speaker", price=45.00, category="Electronics", seller_rating=4.3, store="AudioPlus"),
        Product(id="E5", title="Laptop Stand", price=32.00, category="Electronics", seller_rating=4.1, store="TechMart"),
        # --- Books ---
        Product(id="B1", title="Python Cookbook", price=42.00, category="Books", seller_rating=4.9, store="BookWorld"),
        Product(id="B2", title="AI Fundamentals", price=55.00, category="Books", seller_rating=4.6, store="BookWorld"),
        Product(id="B3", title="Data Structures", price=38.00, category="Books", seller_rating=4.4, store="BookWorld"),
        Product(id="B4", title="Clean Code", price=35.00, category="Books", seller_rating=4.8, store="BookWorld"),
        Product(id="B5", title="Design Patterns", price=48.00, category="Books", seller_rating=4.5, store="BookWorld"),
    ]
    return ProductCatalog(products)


@pytest.fixture
def retrieval(catalog) -> CandidateRetrieval:
    return CandidateRetrieval(catalog)


# ---------------------------------------------------------------------------
# End-to-end pipeline tests
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:
    """Full pipeline: dict filters -> SearchFilters -> search -> SearchResult."""

    def test_dict_to_search_result(self, retrieval):
        """User-facing dict -> SearchFilters -> search -> typed result."""
        raw_filters = {
            "price": [10, 50],
            "category": "Electronics",
            "seller_rating": ">=4.0",
            "sort_by": "price_asc",
        }
        filters = SearchFilters.from_dict(raw_filters)
        result = retrieval.search(filters)

        assert isinstance(result, SearchResult)
        assert result.count > 0
        # All returned products must actually match
        for pid in result:
            product = retrieval.catalog[pid]
            assert 10 <= product.price <= 50
            assert product.category.lower() == "electronics"
            assert product.seller_rating >= 4.0
        # Verify sort order
        prices = [retrieval.catalog[pid].price for pid in result]
        assert prices == sorted(prices)

    def test_roundtrip_filters_dict(self, retrieval):
        """SearchFilters.from_dict -> .to_dict should be lossless."""
        original = {
            "price": [10, 50],
            "category": "Books",
            "seller_rating": ">=4.5",
            "sort_by": "rating_desc",
        }
        filters = SearchFilters.from_dict(original)
        roundtrip = filters.to_dict()
        assert roundtrip["category"] == "Books"
        assert roundtrip["sort_by"] == "rating_desc"


class TestCrossComponentIntegration:
    """Verify that catalog + filters + retrieval work together correctly."""

    def test_category_filter_matches_catalog_categories(self, catalog, retrieval):
        """Every catalog category should be searchable."""
        for category in catalog.categories:
            result = retrieval.search(SearchFilters(category=category))
            assert result.count > 0, f"No results for category '{category}'"

    def test_store_filter_matches_catalog_stores(self, catalog, retrieval):
        """Every catalog store should be searchable."""
        for store in catalog.stores:
            result = retrieval.search(SearchFilters(store=store))
            assert result.count > 0, f"No results for store '{store}'"

    def test_no_false_positives(self, retrieval):
        """Every returned candidate must satisfy ALL filters."""
        filters = SearchFilters(
            price_min=20, price_max=50,
            category="Books",
            min_seller_rating=4.5,
        )
        result = retrieval.search(filters)
        for pid in result:
            p = retrieval.catalog[pid]
            assert p.price >= 20
            assert p.price <= 50
            assert p.category.lower() == "books"
            assert p.seller_rating >= 4.5

    def test_recall_against_brute_force(self, catalog, retrieval):
        """Search recall should be 100 % for an in-memory catalog."""
        filters = SearchFilters(price_min=30, price_max=60, min_seller_rating=4.4)
        result = retrieval.search(filters)

        # Brute-force expected set
        expected = {
            p.id for p in catalog
            if 30 <= p.price <= 60 and p.seller_rating >= 4.4
        }
        assert set(result.candidate_ids) == expected


class TestStrategiesAgreement:
    """All strategies must produce the same candidate set."""

    def test_all_strategies_same_set(self, retrieval):
        filters = SearchFilters(
            price_min=15, price_max=50, category="Electronics",
        )
        results = {
            strategy: set(retrieval.search(filters, strategy=strategy).candidate_ids)
            for strategy in CandidateRetrieval.STRATEGIES
        }
        reference = results["linear"]
        for strategy, ids in results.items():
            assert ids == reference, (
                f"{strategy} returned {ids}, expected {reference}"
            )


class TestSortedOutputIntegrity:
    """Sorted results should be consistent across strategies."""

    def test_price_asc_deterministic(self, retrieval):
        filters = SearchFilters(category="Books", sort_by="price_asc")
        result = retrieval.search(filters)
        prices = [retrieval.catalog[pid].price for pid in result]
        assert prices == sorted(prices)
        assert result.count == 5  # all five books

    def test_max_results_returns_cheapest(self, retrieval):
        """max_results=3 with price_asc should yield the 3 cheapest."""
        filters = SearchFilters(category="Books", sort_by="price_asc")
        result = retrieval.search(filters, max_results=3)
        assert result.count == 3
        prices = [retrieval.catalog[pid].price for pid in result]
        assert prices == sorted(prices)
        # The 3 cheapest books: 35, 38, 42
        assert prices == [35.0, 38.0, 42.0]
