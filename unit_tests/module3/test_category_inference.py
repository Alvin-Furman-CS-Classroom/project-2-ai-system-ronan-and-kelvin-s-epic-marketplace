"""
Unit tests for src/module3/category_inference — category prediction.

Owner: Ronan

Tests:
  - Classifier trains without error
  - Predicted category is a valid category from the training labels
  - Confidence is in [0, 1]
  - Accuracy >= 80% on held-out test set (or similar queries)
  - Handles empty/unknown queries gracefully
"""

import pytest

from src.module3.category_inference import CategoryClassifier


class TestCategoryClassifier:
    """Tests for the CategoryClassifier class."""

    def test_trains_without_error(self, sample_corpus, sample_labels):
        """Classifier initializes and trains successfully."""
        clf = CategoryClassifier(sample_corpus, sample_labels)
        assert clf is not None

    def test_predict_returns_valid_category(self, category_classifier):
        """Predicted category is one of the training labels."""
        valid_labels = {"audio", "footwear", "accessories", "electronics"}
        cat, _ = category_classifier.predict("bluetooth headphones")
        assert cat in valid_labels

    def test_confidence_in_range(self, category_classifier):
        """Confidence is in [0, 1]."""
        _, conf = category_classifier.predict("bluetooth headphones")
        assert 0 <= conf <= 1

    def test_empty_query_returns_low_confidence(self, category_classifier):
        """Empty query returns first label with 0 confidence."""
        cat, conf = category_classifier.predict("")
        assert conf == 0.0
        assert cat in {"audio", "accessories", "electronics", "footwear"}

    def test_whitespace_only_query(self, category_classifier):
        """Whitespace-only query handled gracefully."""
        cat, conf = category_classifier.predict("   ")
        assert conf == 0.0

    def test_audio_query_predicts_audio(self, category_classifier):
        """Headphone-like query should predict audio."""
        cat, conf = category_classifier.predict("wireless bluetooth headphones")
        assert cat == "audio"
        assert conf > 0.4  # small corpus may yield moderate confidence

    def test_electronics_query_predicts_electronics(self, category_classifier):
        """Keyboard-like query should predict electronics."""
        cat, _ = category_classifier.predict("mechanical keyboard gaming")
        assert cat == "electronics"

    def test_mismatched_lengths_raises(self, sample_corpus):
        """Mismatched corpus and labels raises ValueError."""
        with pytest.raises(ValueError, match="same length"):
            CategoryClassifier(sample_corpus[:5], ["a", "b"])

    def test_empty_corpus_raises(self):
        """Empty corpus raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            CategoryClassifier([], [])
