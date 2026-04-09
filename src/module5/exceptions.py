"""
Custom exceptions for the evaluation module (Module 5).

Raised when evaluation inputs are invalid, held-out data is missing,
or the evaluation pipeline encounters an unrecoverable error.
"""

from src.module1.exceptions import EpicMarketplaceError


class EvaluationError(EpicMarketplaceError):
    """Base exception for evaluation failures."""


class NoRelevantItemsError(EvaluationError):
    """Raised when a query has zero relevant items in the held-out set."""


class EmptyCandidateError(EvaluationError):
    """Raised when evaluation receives an empty candidate list."""


class HeldOutDataError(EvaluationError):
    """Raised when held-out data cannot be constructed or is invalid."""
