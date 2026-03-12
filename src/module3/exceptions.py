"""
Custom exceptions for the query understanding module.

Inherits from the shared EpicMarketplaceError base so callers can catch
either module-specific or project-wide errors.

Owner: Ronan
"""

from src.module1.exceptions import EpicMarketplaceError


class QueryUnderstandingError(EpicMarketplaceError):
    """Raised when the query understanding pipeline encounters an error."""


class CategoryInferenceError(QueryUnderstandingError):
    """Raised when category inference fails."""


class EmbeddingError(QueryUnderstandingError):
    """Raised when embedding generation fails."""
