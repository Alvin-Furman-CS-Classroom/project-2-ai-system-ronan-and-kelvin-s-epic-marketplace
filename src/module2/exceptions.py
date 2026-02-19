"""
Custom exceptions for the heuristic re-ranking module.

Inherits from the shared EpicMarketplaceError base so callers can catch
either module-specific or project-wide errors.
"""

from src.module1.exceptions import EpicMarketplaceError


class RankingError(EpicMarketplaceError):
    """Raised when the ranking pipeline encounters an unrecoverable error."""


class InvalidWeightsError(RankingError):
    """Raised when scoring weights are invalid (negative, all zero, etc.)."""


class EmptyCandidatesError(RankingError):
    """Raised when no candidate IDs are provided for re-ranking."""
