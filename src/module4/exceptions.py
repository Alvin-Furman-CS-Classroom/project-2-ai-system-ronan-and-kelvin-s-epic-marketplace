"""
Custom exceptions for the learning-to-rank module (Module 4).

Raised when training data is invalid, the model is unfitted, or feature
construction fails.
"""

from src.module1.exceptions import EpicMarketplaceError


class LearningToRankError(EpicMarketplaceError):
    """Base exception for learning-to-rank failures."""


class InsufficientTrainingDataError(LearningToRankError):
    """Raised when there are too few labeled examples to train."""


class ModelNotFittedError(LearningToRankError):
    """Raised when predict is called before fit."""


class FeatureConstructionError(LearningToRankError):
    """Raised when feature vectors cannot be built from inputs."""
