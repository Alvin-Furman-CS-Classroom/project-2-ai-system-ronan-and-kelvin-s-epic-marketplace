"""
Search filters for candidate retrieval.

Defines the hard constraints that products must satisfy to be candidates.
"""

from dataclasses import dataclass
from typing import List, Optional

from .exceptions import InvalidFilterError


# Valid sort options for search results
SORT_OPTIONS = ("price_asc", "price_desc", "rating_desc", "rating_asc")


@dataclass
class SearchFilters:
    """
    Hard constraints for filtering products.
    
    Attributes:
        price_min: Minimum price (inclusive). None means no lower bound.
        price_max: Maximum price (inclusive). None means no upper bound.
        category: Product category to match. None means any category.
        min_seller_rating: Minimum seller rating (inclusive). None means no minimum.
        store: Store/brand name to match. None means any store.
        sort_by: Sort order for results. One of:
                 "price_asc", "price_desc", "rating_desc", "rating_asc".
                 None means no sorting (return in search order).
    
    Example:
        >>> filters = SearchFilters(
        ...     price_min=10.0,
        ...     price_max=40.0,
        ...     category="Computers",
        ...     min_seller_rating=4.0,
        ...     store="Anker",
        ...     sort_by="price_asc"
        ... )
    """
    
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    category: Optional[str] = None
    min_seller_rating: Optional[float] = None
    store: Optional[str] = None
    sort_by: Optional[str] = None
    
    def __post_init__(self):
        """Validate filter values."""
        if self.price_min is not None and self.price_min < 0:
            raise InvalidFilterError("price_min cannot be negative")
        if self.price_max is not None and self.price_max < 0:
            raise InvalidFilterError("price_max cannot be negative")
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise InvalidFilterError("price_min cannot exceed price_max")
        if self.min_seller_rating is not None:
            if not (0 <= self.min_seller_rating <= 5):
                raise InvalidFilterError(
                    "min_seller_rating must be between 0 and 5"
                )
        if self.sort_by is not None:
            if self.sort_by not in SORT_OPTIONS:
                raise InvalidFilterError(
                    f"sort_by must be one of {SORT_OPTIONS}, got '{self.sort_by}'"
                )
    
    @classmethod
    def from_dict(cls, data: dict) -> "SearchFilters":
        """
        Create SearchFilters from a dictionary.
        
        Args:
            data: Dictionary with filter values. Supports:
                - "price": [min, max] or {"min": x, "max": y}
                - "category": string
                - "seller_rating": ">=X" or float
                - "store": string
                - "sort_by": string
        
        Returns:
            SearchFilters instance.
        
        Example:
            >>> filters = SearchFilters.from_dict({
            ...     "price": [10, 40],
            ...     "category": "Computers",
            ...     "seller_rating": ">=4.0",
            ...     "store": "Anker",
            ...     "sort_by": "price_asc"
            ... })
        """
        price_min = None
        price_max = None
        
        if "price" in data:
            price = data["price"]
            if isinstance(price, list) and len(price) == 2:
                price_min, price_max = price
            elif isinstance(price, dict):
                price_min = price.get("min")
                price_max = price.get("max")
        
        min_seller_rating = None
        if "seller_rating" in data:
            rating = data["seller_rating"]
            if isinstance(rating, str) and rating.startswith(">="):
                min_seller_rating = float(rating[2:])
            elif isinstance(rating, (int, float)):
                min_seller_rating = float(rating)
        
        return cls(
            price_min=price_min,
            price_max=price_max,
            category=data.get("category"),
            min_seller_rating=min_seller_rating,
            store=data.get("store"),
            sort_by=data.get("sort_by"),
        )
    
    def to_dict(self) -> dict:
        """Convert filters to dictionary representation.

        Returns:
            Dictionary with non-None filter values. Price is
            represented as ``[min, max]`` and seller_rating
            as ``">=value"``.
        """
        result = {}
        if self.price_min is not None or self.price_max is not None:
            result["price"] = [self.price_min, self.price_max]
        if self.category is not None:
            result["category"] = self.category
        if self.min_seller_rating is not None:
            result["seller_rating"] = f">={self.min_seller_rating}"
        if self.store is not None:
            result["store"] = self.store
        if self.sort_by is not None:
            result["sort_by"] = self.sort_by
        return result
