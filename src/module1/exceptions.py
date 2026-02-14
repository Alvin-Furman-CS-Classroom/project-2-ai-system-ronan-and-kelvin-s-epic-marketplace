"""
Custom exceptions for the candidate retrieval module.

Provides specific, descriptive exception classes so callers can handle
errors precisely rather than catching broad ValueError/KeyError.
"""


class EpicMarketplaceError(Exception):
    """Base exception for all Epic Marketplace errors."""


class InvalidFilterError(EpicMarketplaceError):
    """Raised when a search filter has invalid or contradictory values."""


class ProductValidationError(EpicMarketplaceError):
    """Raised when a product has invalid attributes (e.g., negative price)."""


class ProductNotFoundError(EpicMarketplaceError, KeyError):
    """Raised when a product ID does not exist in the catalog."""


class UnknownSearchStrategyError(EpicMarketplaceError):
    """Raised when an unrecognized search strategy is requested."""


class DataLoadError(EpicMarketplaceError):
    """Raised when data files cannot be loaded or parsed."""
