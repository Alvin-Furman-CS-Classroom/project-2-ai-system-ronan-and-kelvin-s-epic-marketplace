# Module 1: Candidate Retrieval
"""
Candidate retrieval using uninformed/informed search.
Filters products by hard constraints (price, category, seller rating, location).
"""

from .retrieval import CandidateRetrieval
from .filters import SearchFilters
from .catalog import ProductCatalog, Product

__all__ = ["CandidateRetrieval", "SearchFilters", "ProductCatalog", "Product"]
