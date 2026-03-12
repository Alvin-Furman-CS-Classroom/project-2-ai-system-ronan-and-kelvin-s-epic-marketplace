"""
Category inference using TF-IDF + Logistic Regression.

Trains a text classifier on product titles/descriptions to predict
the most likely product category from a user query.

Owner: Ronan

Interface (agreed with Kelvin):
    CategoryClassifier(corpus_texts, labels) -> None
    .predict(query) -> (category, confidence)
"""

from typing import List, Tuple


class CategoryClassifier:
    """Predicts product category from query text.

    Uses TF-IDF features + Logistic Regression, trained on the product
    corpus with known category labels.

    Example:
        >>> clf = CategoryClassifier(corpus_texts, labels)
        >>> clf.predict("bluetooth headphones")
        ('Portable Audio & Accessories', 0.87)
    """

    def __init__(self, corpus_texts: List[str], labels: List[str]) -> None:
        """Train the classifier on labeled product text.

        Args:
            corpus_texts: Product text strings (title + description).
            labels: Corresponding category label for each text.
        """
        raise NotImplementedError("Ronan: implement CategoryClassifier.__init__")

    def predict(self, query: str) -> Tuple[str, float]:
        """Predict the most likely category for a query.

        Args:
            query: Raw user query text.

        Returns:
            (predicted_category, confidence) where confidence is in [0, 1].
        """
        raise NotImplementedError("Ronan: implement CategoryClassifier.predict")
