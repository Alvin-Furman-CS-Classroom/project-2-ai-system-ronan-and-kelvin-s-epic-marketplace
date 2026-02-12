"""
Unit tests for SearchFilters.
"""

import pytest
from src.module1.filters import SearchFilters, SORT_OPTIONS
from src.module1.exceptions import InvalidFilterError


class TestSearchFilters:
    """Tests for SearchFilters class."""
    
    def test_default_filters(self):
        """Default filters should have all None values."""
        filters = SearchFilters()
        assert filters.price_min is None
        assert filters.price_max is None
        assert filters.category is None
        assert filters.min_seller_rating is None
        assert filters.store is None
        assert filters.sort_by is None
    
    def test_filter_with_price_range(self):
        """Should accept valid price range."""
        filters = SearchFilters(price_min=10.0, price_max=40.0)
        assert filters.price_min == 10.0
        assert filters.price_max == 40.0
    
    def test_filter_with_all_constraints(self):
        """Should accept all constraints."""
        filters = SearchFilters(
            price_min=10.0,
            price_max=40.0,
            category="Computers",
            min_seller_rating=4.0,
            store="Anker",
            sort_by="price_asc",
        )
        assert filters.price_min == 10.0
        assert filters.price_max == 40.0
        assert filters.category == "Computers"
        assert filters.min_seller_rating == 4.0
        assert filters.store == "Anker"
        assert filters.sort_by == "price_asc"
    
    def test_invalid_negative_price_min(self):
        """Should reject negative price_min."""
        with pytest.raises(InvalidFilterError, match="price_min cannot be negative"):
            SearchFilters(price_min=-5.0)
    
    def test_invalid_negative_price_max(self):
        """Should reject negative price_max."""
        with pytest.raises(InvalidFilterError, match="price_max cannot be negative"):
            SearchFilters(price_max=-10.0)
    
    def test_invalid_price_range(self):
        """Should reject price_min > price_max."""
        with pytest.raises(InvalidFilterError, match="price_min cannot exceed price_max"):
            SearchFilters(price_min=50.0, price_max=10.0)
    
    def test_invalid_seller_rating_too_high(self):
        """Should reject seller rating > 5."""
        with pytest.raises(InvalidFilterError, match="min_seller_rating must be between 0 and 5"):
            SearchFilters(min_seller_rating=5.5)
    
    def test_invalid_seller_rating_negative(self):
        """Should reject negative seller rating."""
        with pytest.raises(InvalidFilterError, match="min_seller_rating must be between 0 and 5"):
            SearchFilters(min_seller_rating=-1.0)
    
    def test_invalid_sort_by(self):
        """Should reject invalid sort_by value."""
        with pytest.raises(InvalidFilterError, match="sort_by must be one of"):
            SearchFilters(sort_by="invalid")
    
    def test_valid_sort_options(self):
        """All SORT_OPTIONS should be accepted."""
        for option in SORT_OPTIONS:
            filters = SearchFilters(sort_by=option)
            assert filters.sort_by == option


class TestSearchFiltersFromDict:
    """Tests for SearchFilters.from_dict()."""
    
    def test_from_dict_with_price_list(self):
        """Should parse price as [min, max] list."""
        filters = SearchFilters.from_dict({"price": [10, 40]})
        assert filters.price_min == 10
        assert filters.price_max == 40
    
    def test_from_dict_with_price_dict(self):
        """Should parse price as {"min": x, "max": y} dict."""
        filters = SearchFilters.from_dict({"price": {"min": 10, "max": 40}})
        assert filters.price_min == 10
        assert filters.price_max == 40
    
    def test_from_dict_with_seller_rating_string(self):
        """Should parse seller_rating as '>=X' string."""
        filters = SearchFilters.from_dict({"seller_rating": ">=4.5"})
        assert filters.min_seller_rating == 4.5
    
    def test_from_dict_with_seller_rating_number(self):
        """Should parse seller_rating as number."""
        filters = SearchFilters.from_dict({"seller_rating": 4.5})
        assert filters.min_seller_rating == 4.5
    
    def test_from_dict_with_store(self):
        """Should parse store filter."""
        filters = SearchFilters.from_dict({"store": "Anker"})
        assert filters.store == "Anker"
    
    def test_from_dict_with_sort_by(self):
        """Should parse sort_by."""
        filters = SearchFilters.from_dict({"sort_by": "rating_desc"})
        assert filters.sort_by == "rating_desc"
    
    def test_from_dict_full_example(self):
        """Should parse the full example from the spec."""
        data = {
            "price": [10, 40],
            "category": "Computers",
            "seller_rating": ">=4.0",
            "store": "Sony",
            "sort_by": "price_asc",
        }
        filters = SearchFilters.from_dict(data)
        assert filters.price_min == 10
        assert filters.price_max == 40
        assert filters.category == "Computers"
        assert filters.min_seller_rating == 4.0
        assert filters.store == "Sony"
        assert filters.sort_by == "price_asc"
    
    def test_from_dict_empty(self):
        """Should handle empty dict."""
        filters = SearchFilters.from_dict({})
        assert filters.price_min is None
        assert filters.price_max is None
        assert filters.category is None
        assert filters.min_seller_rating is None
        assert filters.store is None
        assert filters.sort_by is None


class TestSearchFiltersToDict:
    """Tests for SearchFilters.to_dict()."""
    
    def test_to_dict_with_all_values(self):
        """Should convert all values to dict."""
        filters = SearchFilters(
            price_min=10.0,
            price_max=40.0,
            category="Computers",
            min_seller_rating=4.0,
            store="Anker",
            sort_by="price_asc",
        )
        result = filters.to_dict()
        assert result["price"] == [10.0, 40.0]
        assert result["category"] == "Computers"
        assert result["seller_rating"] == ">=4.0"
        assert result["store"] == "Anker"
        assert result["sort_by"] == "price_asc"
    
    def test_to_dict_empty(self):
        """Should return empty dict for default filters."""
        filters = SearchFilters()
        result = filters.to_dict()
        assert result == {}
    
    def test_to_dict_partial(self):
        """Should only include non-None values."""
        filters = SearchFilters(category="electronics")
        result = filters.to_dict()
        assert "price" not in result
        assert "seller_rating" not in result
        assert "store" not in result
        assert "sort_by" not in result
        assert result["category"] == "electronics"
