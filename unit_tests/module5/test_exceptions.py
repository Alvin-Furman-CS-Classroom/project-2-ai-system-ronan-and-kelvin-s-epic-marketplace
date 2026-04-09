"""Tests for Module 5 exception classes."""

import pytest

from src.module1.exceptions import EpicMarketplaceError
from src.module5.exceptions import (
    EmptyCandidateError,
    EvaluationError,
    HeldOutDataError,
    NoRelevantItemsError,
)


@pytest.mark.parametrize(
    "exc",
    [
        EvaluationError("test"),
        NoRelevantItemsError("test"),
        EmptyCandidateError("test"),
        HeldOutDataError("test"),
    ],
)
def test_evaluation_exceptions_are_epic_marketplace_errors(exc):
    assert isinstance(exc, EpicMarketplaceError)


def test_evaluation_error_is_base():
    exc = NoRelevantItemsError("no items")
    assert isinstance(exc, EvaluationError)


def test_exception_messages():
    exc = HeldOutDataError("missing column")
    assert "missing column" in str(exc)
