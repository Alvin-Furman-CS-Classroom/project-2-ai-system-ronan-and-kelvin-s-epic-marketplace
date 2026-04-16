"""
Custom exceptions for the evaluation module (Module 5).

Raised when evaluation inputs are invalid, held-out data is missing,
or the evaluation pipeline encounters an unrecoverable error.
"""

from src.module1.exceptions import EpicMarketplaceError


class EvaluationError(EpicMarketplaceError):
    """Base exception for evaluation failures."""


class NoRelevantItemsError(EvaluationError):
    """Reserved for strict callers that require at least one relevant label.

    The default :class:`~src.module5.pipeline.EvaluationPipeline` does **not**
    raise this: IR metrics define sensible behaviour when the relevant set is
    empty (e.g. recall vacuous truth). Subclass or call sites may use this if
    they need to fail fast when labels are missing.
    """


class EmptyCandidateError(EvaluationError):
    """Raised when evaluation receives an empty candidate list."""


class HeldOutDataError(EvaluationError):
    """Raised when held-out data cannot be constructed or is invalid."""
