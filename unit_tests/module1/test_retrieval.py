"""
Unit tests for CandidateRetrieval.
"""

import pytest
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.filters import SearchFilters
from src.module1.catalog import Product, ProductCatalog
from src.module1.exceptions import UnknownSearchStrategyError


class TestCandidateRetrieval:
    """Tests for CandidateRetrieval class."""
    
    @pytest.fixture
    def sample_catalog(self):
        """Sample product catalog for testing."""
        products = [
            Product(id="p1", title="Ceramic Mug", price=18.0, category="home", seller_rating=4.8, store="StoreA"),
            Product(id="p2", title="Glass Vase", price=35.0, category="home", seller_rating=4.5, store="StoreA"),
            Product(id="p3", title="Wooden Bowl", price=45.0, category="home", seller_rating=4.2, store="StoreB"),
            Product(id="p4", title="Metal Lamp", price=60.0, category="home", seller_rating=4.9, store="StoreA"),
            Product(id="p5", title="Phone Case", price=15.0, category="electronics", seller_rating=4.0, store="StoreC"),
            Product(id="p6", title="USB Cable", price=8.0, category="electronics", seller_rating=3.8, store="StoreA"),
            Product(id="p7", title="Headphones", price=50.0, category="electronics", seller_rating=4.7, store="StoreB"),
            Product(id="p8", title="Plant Pot", price=22.0, category="home", seller_rating=4.6, store="StoreA"),
            Product(id="p9", title="Candle Set", price=28.0, category="home", seller_rating=4.4, store="StoreC"),
            Product(id="p10", title="Picture Frame", price=12.0, category="home", seller_rating=4.1, store="StoreA"),
        ]
        return ProductCatalog(products)
    
    @pytest.fixture
    def retrieval(self, sample_catalog):
        """CandidateRetrieval instance for testing."""
        return CandidateRetrieval(sample_catalog)


class TestMatchesFilters(TestCandidateRetrieval):
    """Tests for matches_filters method."""
    
    def test_matches_no_filters(self, retrieval, sample_catalog):
        """Product should match when no filters are set."""
        filters = SearchFilters()
        product = sample_catalog["p1"]
        assert retrieval.matches_filters(product, filters) is True
    
    def test_matches_price_in_range(self, retrieval, sample_catalog):
        """Product should match when price is in range."""
        filters = SearchFilters(price_min=10.0, price_max=40.0)
        product = sample_catalog["p1"]  # price=18.0
        assert retrieval.matches_filters(product, filters) is True
    
    def test_not_matches_price_below_min(self, retrieval, sample_catalog):
        """Product should not match when price is below min."""
        filters = SearchFilters(price_min=20.0)
        product = sample_catalog["p1"]  # price=18.0
        assert retrieval.matches_filters(product, filters) is False
    
    def test_not_matches_price_above_max(self, retrieval, sample_catalog):
        """Product should not match when price is above max."""
        filters = SearchFilters(price_max=15.0)
        product = sample_catalog["p1"]  # price=18.0
        assert retrieval.matches_filters(product, filters) is False
    
    def test_matches_category(self, retrieval, sample_catalog):
        """Product should match when category matches."""
        filters = SearchFilters(category="home")
        product = sample_catalog["p1"]  # category="home"
        assert retrieval.matches_filters(product, filters) is True
    
    def test_not_matches_category(self, retrieval, sample_catalog):
        """Product should not match when category differs."""
        filters = SearchFilters(category="electronics")
        product = sample_catalog["p1"]  # category="home"
        assert retrieval.matches_filters(product, filters) is False
    
    def test_matches_category_case_insensitive(self, retrieval, sample_catalog):
        """Category matching should be case-insensitive."""
        filters = SearchFilters(category="HOME")
        product = sample_catalog["p1"]  # category="home"
        assert retrieval.matches_filters(product, filters) is True
    
    def test_matches_seller_rating(self, retrieval, sample_catalog):
        """Product should match when seller rating meets minimum."""
        filters = SearchFilters(min_seller_rating=4.5)
        product = sample_catalog["p1"]  # rating=4.8
        assert retrieval.matches_filters(product, filters) is True
    
    def test_not_matches_seller_rating(self, retrieval, sample_catalog):
        """Product should not match when seller rating is below minimum."""
        filters = SearchFilters(min_seller_rating=4.9)
        product = sample_catalog["p1"]  # rating=4.8
        assert retrieval.matches_filters(product, filters) is False
    
    def test_matches_store(self, retrieval, sample_catalog):
        """Product should match when store matches."""
        filters = SearchFilters(store="StoreA")
        product = sample_catalog["p1"]  # store="StoreA"
        assert retrieval.matches_filters(product, filters) is True
    
    def test_not_matches_store(self, retrieval, sample_catalog):
        """Product should not match when store differs."""
        filters = SearchFilters(store="StoreB")
        product = sample_catalog["p1"]  # store="StoreA"
        assert retrieval.matches_filters(product, filters) is False
    
    def test_matches_store_case_insensitive(self, retrieval, sample_catalog):
        """Store matching should be case-insensitive."""
        filters = SearchFilters(store="storea")
        product = sample_catalog["p1"]  # store="StoreA"
        assert retrieval.matches_filters(product, filters) is True
    
    def test_matches_all_filters(self, retrieval, sample_catalog):
        """Product should match when all filters are satisfied."""
        filters = SearchFilters(
            price_min=10.0,
            price_max=40.0,
            category="home",
            min_seller_rating=4.5,
            store="StoreA",
        )
        product = sample_catalog["p1"]  # price=18, home, 4.8, StoreA
        assert retrieval.matches_filters(product, filters) is True
    
    def test_not_matches_one_filter_fails(self, retrieval, sample_catalog):
        """Product should not match if any filter fails."""
        filters = SearchFilters(
            price_min=10.0,
            price_max=40.0,
            category="electronics",  # p1 is home
            min_seller_rating=4.5,
        )
        product = sample_catalog["p1"]
        assert retrieval.matches_filters(product, filters) is False


class TestSearchStrategies(TestCandidateRetrieval):
    """Tests for different search strategies."""
    
    def test_linear_search(self, retrieval):
        """Linear search should find all matching products."""
        filters = SearchFilters(category="home", min_seller_rating=4.5)
        candidates = retrieval.search(filters, strategy="linear")
        assert set(candidates) == {"p1", "p2", "p4", "p8"}
    
    def test_bfs_search(self, retrieval):
        """BFS search should find all matching products."""
        filters = SearchFilters(category="home", min_seller_rating=4.5)
        candidates = retrieval.search(filters, strategy="bfs")
        assert set(candidates) == {"p1", "p2", "p4", "p8"}
    
    def test_dfs_search(self, retrieval):
        """DFS search should find all matching products."""
        filters = SearchFilters(category="home", min_seller_rating=4.5)
        candidates = retrieval.search(filters, strategy="dfs")
        assert set(candidates) == {"p1", "p2", "p4", "p8"}
    
    def test_priority_search(self, retrieval):
        """Priority search should find all matching products."""
        filters = SearchFilters(category="home", min_seller_rating=4.5)
        candidates = retrieval.search(filters, strategy="priority")
        assert set(candidates) == {"p1", "p2", "p4", "p8"}
    
    def test_invalid_strategy(self, retrieval):
        """Should raise UnknownSearchStrategyError for unknown strategy."""
        filters = SearchFilters()
        with pytest.raises(UnknownSearchStrategyError, match="Unknown search strategy"):
            retrieval.search(filters, strategy="invalid")
    
    def test_store_filter(self, retrieval):
        """Should filter by store."""
        filters = SearchFilters(store="StoreB")
        candidates = retrieval.search(filters)
        assert set(candidates) == {"p3", "p7"}
    
    def test_store_and_category_filter(self, retrieval):
        """Should combine store + category filters."""
        filters = SearchFilters(store="StoreA", category="electronics")
        candidates = retrieval.search(filters)
        assert set(candidates) == {"p6"}


class TestSorting(TestCandidateRetrieval):
    """Tests for search result sorting."""
    
    def test_sort_price_asc(self, retrieval):
        """Should sort results by price ascending."""
        filters = SearchFilters(category="home", sort_by="price_asc")
        candidates = retrieval.search(filters)
        prices = [retrieval.catalog[pid].price for pid in candidates]
        assert prices == sorted(prices)
    
    def test_sort_price_desc(self, retrieval):
        """Should sort results by price descending."""
        filters = SearchFilters(category="home", sort_by="price_desc")
        candidates = retrieval.search(filters)
        prices = [retrieval.catalog[pid].price for pid in candidates]
        assert prices == sorted(prices, reverse=True)
    
    def test_sort_rating_desc(self, retrieval):
        """Should sort results by seller rating descending."""
        filters = SearchFilters(category="home", sort_by="rating_desc")
        candidates = retrieval.search(filters)
        ratings = [retrieval.catalog[pid].seller_rating for pid in candidates]
        assert ratings == sorted(ratings, reverse=True)
    
    def test_sort_rating_asc(self, retrieval):
        """Should sort results by seller rating ascending."""
        filters = SearchFilters(category="home", sort_by="rating_asc")
        candidates = retrieval.search(filters)
        ratings = [retrieval.catalog[pid].seller_rating for pid in candidates]
        assert ratings == sorted(ratings)
    
    def test_sort_with_max_results(self, retrieval):
        """Sorting + max_results should return top N sorted results."""
        filters = SearchFilters(category="home", sort_by="price_asc")
        result = retrieval.search(filters, max_results=3)
        assert len(result) == 3
        prices = [retrieval.catalog[pid].price for pid in result]
        # Should be the 3 cheapest home products
        assert prices == sorted(prices)
        assert prices[-1] <= 28.0  # 3rd cheapest home product
    
    def test_sort_price_asc_values(self, retrieval):
        """Verify exact sort order for price_asc on electronics."""
        filters = SearchFilters(category="electronics", sort_by="price_asc")
        candidates = retrieval.search(filters)
        prices = [retrieval.catalog[pid].price for pid in candidates]
        assert prices == [8.0, 15.0, 50.0]
    
    def test_sort_rating_desc_values(self, retrieval):
        """Verify exact sort order for rating_desc on electronics."""
        filters = SearchFilters(category="electronics", sort_by="rating_desc")
        candidates = retrieval.search(filters)
        ratings = [retrieval.catalog[pid].seller_rating for pid in candidates]
        assert ratings == [4.7, 4.0, 3.8]
    
    def test_no_sort_returns_search_order(self, retrieval):
        """Without sort_by, results should come in search order."""
        filters = SearchFilters(category="electronics")
        candidates = retrieval.search(filters)
        # Just check we get the right set (order depends on strategy)
        assert set(candidates) == {"p5", "p6", "p7"}


class TestSearchWithMaxResults(TestCandidateRetrieval):
    """Tests for max_results parameter."""
    
    def test_max_results_linear(self, retrieval):
        """Linear search should respect max_results."""
        filters = SearchFilters(category="home")
        candidates = retrieval.search(filters, strategy="linear", max_results=3)
        assert len(candidates) == 3
    
    def test_max_results_bfs(self, retrieval):
        """BFS search should respect max_results."""
        filters = SearchFilters(category="home")
        candidates = retrieval.search(filters, strategy="bfs", max_results=3)
        assert len(candidates) == 3
    
    def test_max_results_dfs(self, retrieval):
        """DFS search should respect max_results."""
        filters = SearchFilters(category="home")
        candidates = retrieval.search(filters, strategy="dfs", max_results=3)
        assert len(candidates) == 3
    
    def test_max_results_priority(self, retrieval):
        """Priority search should respect max_results."""
        filters = SearchFilters(category="home")
        candidates = retrieval.search(filters, strategy="priority", max_results=3)
        assert len(candidates) == 3


class TestSearchRecall(TestCandidateRetrieval):
    """Tests for search recall (success criterion: >=95% recall)."""
    
    def test_full_recall_no_filters(self, retrieval, sample_catalog):
        """Should return all products when no filters."""
        filters = SearchFilters()
        candidates = retrieval.search(filters)
        assert len(candidates) == len(sample_catalog)
    
    def test_full_recall_price_filter(self, retrieval):
        """Should return all products in price range."""
        filters = SearchFilters(price_min=10.0, price_max=30.0)
        candidates = retrieval.search(filters)
        # p1=18, p5=15, p8=22, p9=28, p10=12 are in range
        expected = {"p1", "p5", "p8", "p9", "p10"}
        assert set(candidates) == expected
    
    def test_full_recall_complex_filters(self, retrieval):
        """Should return all matching products for complex filters."""
        filters = SearchFilters(
            price_min=10.0,
            price_max=40.0,
            category="home",
            min_seller_rating=4.5,
        )
        candidates = retrieval.search(filters)
        # p1: 18, home, 4.8 ✓
        # p2: 35, home, 4.5 ✓
        # p8: 22, home, 4.6 ✓
        expected = {"p1", "p2", "p8"}
        assert set(candidates) == expected
    
    def test_empty_result_when_no_matches(self, retrieval):
        """Should return empty result when no products match."""
        filters = SearchFilters(category="furniture")
        result = retrieval.search(filters)
        assert result.candidate_ids == []
        assert result.count == 0


class TestGetCandidatesWithProducts(TestCandidateRetrieval):
    """Tests for get_candidates_with_products convenience method."""
    
    def test_returns_product_objects(self, retrieval):
        """Should return Product objects, not just IDs."""
        filters = SearchFilters(category="electronics")
        products = retrieval.get_candidates_with_products(filters)
        assert all(isinstance(p, Product) for p in products)
        assert {p.id for p in products} == {"p5", "p6", "p7"}
    
    def test_products_match_filters(self, retrieval):
        """Returned products should all match filters."""
        filters = SearchFilters(min_seller_rating=4.5)
        products = retrieval.get_candidates_with_products(filters)
        for product in products:
            assert product.seller_rating >= 4.5
