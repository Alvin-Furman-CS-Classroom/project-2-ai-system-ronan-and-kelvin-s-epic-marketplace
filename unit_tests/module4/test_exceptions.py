"""Tests for module4 exception classes."""

import pytest

from src.module4.exceptions import (
    FeatureConstructionError,
    InsufficientTrainingDataError,
    LearningToRankError,
    ModelNotFittedError,
)


@pytest.mark.parametrize(
    "exc",
    [
        LearningToRankError("x"),
        InsufficientTrainingDataError("x"),
        ModelNotFittedError("x"),
        FeatureConstructionError("x"),
    ],
)
def test_ltr_exceptions_are_epic_marketplace_errors(exc):
    from src.module1.exceptions import EpicMarketplaceError

    assert isinstance(exc, EpicMarketplaceError)
