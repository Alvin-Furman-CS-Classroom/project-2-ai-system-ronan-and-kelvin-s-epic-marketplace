# Module 1: Candidate Retrieval
"""
Candidate retrieval using uninformed/informed search.
Filters products by hard constraints (price, category, seller rating, store).
Supports sorting results by price or rating.
"""

from .retrieval import CandidateRetrieval
from .filters import SearchFilters, SORT_OPTIONS
from .catalog import ProductCatalog, Product
from .loader import load_catalog_from_working_set, load_catalog, compute_seller_ratings

__all__ = [
    "CandidateRetrieval",
    "SearchFilters",
    "SORT_OPTIONS",
    "ProductCatalog",
    "Product",
    "load_catalog_from_working_set",
    "load_catalog",
    "compute_seller_ratings",
]
