# Module 1: Candidate Retrieval
"""
Candidate retrieval using uninformed/informed search.
Filters products by hard constraints (price, category, seller rating, store).
Supports sorting results by price or rating.
"""

from .catalog import Product, ProductCatalog
from .exceptions import (
    DataLoadError,
    EpicMarketplaceError,
    InvalidFilterError,
    ProductNotFoundError,
    ProductValidationError,
    UnknownSearchStrategyError,
)
from .filters import SORT_OPTIONS, SearchFilters
from .loader import compute_seller_ratings, load_catalog, load_catalog_from_working_set
from .retrieval import CandidateRetrieval, SearchResult

__all__ = [
    # Core classes
    "CandidateRetrieval",
    "SearchResult",
    "SearchFilters",
    "SORT_OPTIONS",
    "ProductCatalog",
    "Product",
    # Data loading
    "load_catalog_from_working_set",
    "load_catalog",
    "compute_seller_ratings",
    # Exceptions
    "EpicMarketplaceError",
    "InvalidFilterError",
    "ProductValidationError",
    "ProductNotFoundError",
    "UnknownSearchStrategyError",
    "DataLoadError",
]
