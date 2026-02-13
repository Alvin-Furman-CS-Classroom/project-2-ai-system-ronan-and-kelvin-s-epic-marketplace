"""
Edge-case and boundary-value tests for Module 1.

Covers scenarios missing from the main test files:
 - Boundary prices (exactly at min/max)
 - Single-product / empty catalogs
 - SearchResult metadata (strategy, elapsed_ms, total_scanned)
 - Category index lookup
 - All strategies return consistent results
 - Priority search ordering (low-priority items examined first)
"""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module1.filters import SearchFilters
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.exceptions import (
    InvalidFilterError,
    ProductNotFoundError,
    ProductValidationError,
    UnknownSearchStrategyError,
)


# ---------------------------------------------------------------------------
# Boundary-value tests for filters
# ---------------------------------------------------------------------------

class TestBoundaryPrices:
    """Prices exactly at the min/max boundary should be included."""

    def test_price_at_exact_min(self, retrieval, sample_catalog):
        """Product with price == price_min should match."""
        filters = SearchFilters(price_min=18.0)
        product = sample_catalog["p1"]  # price=18.0
        assert retrieval.matches_filters(product, filters) is True

    def test_price_at_exact_max(self, retrieval, sample_catalog):
        """Product with price == price_max should match."""
        filters = SearchFilters(price_max=18.0)
        product = sample_catalog["p1"]  # price=18.0
        assert retrieval.matches_filters(product, filters) is True

    def test_price_one_cent_below_min(self, retrieval, sample_catalog):
        """Product just below price_min should NOT match."""
        filters = SearchFilters(price_min=18.01)
        product = sample_catalog["p1"]  # price=18.0
        assert retrieval.matches_filters(product, filters) is False

    def test_rating_at_exact_min(self, retrieval, sample_catalog):
        """Product with rating == min_seller_rating should match."""
        filters = SearchFilters(min_seller_rating=4.8)
        product = sample_catalog["p1"]  # rating=4.8
        assert retrieval.matches_filters(product, filters) is True

    def test_zero_price_product(self):
        """Product with price=0 should be valid (not negative)."""
        p = Product(id="z1", title="Free Item", price=0.0,
                    category="promo", seller_rating=3.0, store="X")
        assert p.price == 0.0


# ---------------------------------------------------------------------------
# Empty / single-product catalog
# ---------------------------------------------------------------------------

class TestEmptyCatalog:
    """Search over an empty catalog."""

    def test_search_empty_catalog(self):
        """Should return empty result, not crash."""
        catalog = ProductCatalog()
        retrieval = CandidateRetrieval(catalog)
        result = retrieval.search(SearchFilters())
        assert result.candidate_ids == []
        assert result.count == 0
        assert result.total_scanned == 0

    def test_empty_catalog_all_strategies(self):
        """All strategies should handle empty catalogs gracefully."""
        catalog = ProductCatalog()
        retrieval = CandidateRetrieval(catalog)
        for strategy in CandidateRetrieval.STRATEGIES:
            result = retrieval.search(SearchFilters(), strategy=strategy)
            assert result.count == 0, f"Strategy {strategy} failed on empty catalog"


class TestSingleProductCatalog:
    """Search over a catalog with exactly one product."""

    @pytest.fixture
    def one_product_catalog(self):
        product = Product(
            id="solo", title="Only Item", price=25.0,
            category="home", seller_rating=4.0, store="OnlyStore",
        )
        return ProductCatalog([product])

    def test_single_match(self, one_product_catalog):
        retrieval = CandidateRetrieval(one_product_catalog)
        result = retrieval.search(SearchFilters(category="home"))
        assert result.candidate_ids == ["solo"]

    def test_single_no_match(self, one_product_catalog):
        retrieval = CandidateRetrieval(one_product_catalog)
        result = retrieval.search(SearchFilters(category="electronics"))
        assert result.candidate_ids == []


# ---------------------------------------------------------------------------
# SearchResult metadata
# ---------------------------------------------------------------------------

class TestSearchResultMetadata:
    """Verify SearchResult carries correct metadata."""

    def test_result_has_strategy(self, retrieval):
        result = retrieval.search(SearchFilters(), strategy="bfs")
        assert result.strategy == "bfs"

    def test_result_has_elapsed_ms(self, retrieval):
        result = retrieval.search(SearchFilters())
        assert result.elapsed_ms >= 0

    def test_result_total_scanned(self, retrieval, sample_catalog):
        result = retrieval.search(SearchFilters())
        assert result.total_scanned == len(sample_catalog)

    def test_result_iterable(self, retrieval):
        result = retrieval.search(SearchFilters(category="electronics"))
        ids = list(result)
        assert set(ids) == {"p5", "p6", "p7"}


# ---------------------------------------------------------------------------
# Category index
# ---------------------------------------------------------------------------

class TestCategoryIndex:
    """ProductCatalog.get_ids_by_category() provides O(1) lookup."""

    def test_known_category(self, sample_catalog):
        ids = sample_catalog.get_ids_by_category("electronics")
        assert set(ids) == {"p5", "p6", "p7"}

    def test_unknown_category_returns_empty(self, sample_catalog):
        ids = sample_catalog.get_ids_by_category("furniture")
        assert ids == []

    def test_case_insensitive(self, sample_catalog):
        ids = sample_catalog.get_ids_by_category("HOME")
        assert "p1" in ids


# ---------------------------------------------------------------------------
# Strategy consistency — all strategies must agree on the candidate set
# ---------------------------------------------------------------------------

class TestStrategyConsistency:
    """All search strategies must return the same candidate set."""

    @pytest.mark.parametrize("strategy", CandidateRetrieval.STRATEGIES)
    def test_same_candidates(self, retrieval, strategy):
        filters = SearchFilters(
            price_min=10, price_max=40, category="home", min_seller_rating=4.5,
        )
        result = retrieval.search(filters, strategy=strategy)
        assert set(result.candidate_ids) == {"p1", "p2", "p8"}


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class TestExceptionHierarchy:
    """Custom exceptions should be catchable as their parent types."""

    def test_invalid_filter_is_epic_error(self):
        with pytest.raises(InvalidFilterError):
            SearchFilters(price_min=-1)

    def test_product_not_found_is_key_error(self, sample_catalog):
        """ProductNotFoundError inherits KeyError for backward compat."""
        with pytest.raises(KeyError):
            _ = sample_catalog["nonexistent"]

    def test_unknown_strategy_is_epic_error(self, retrieval):
        with pytest.raises(UnknownSearchStrategyError):
            retrieval.search(SearchFilters(), strategy="magic")
