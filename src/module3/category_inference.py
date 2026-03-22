"""
Category inference using TF-IDF + Logistic Regression.

Trains a text classifier on product titles/descriptions to predict
the most likely product category from a user query.

Owner: Ronan

Interface (agreed with Kelvin):
    CategoryClassifier(corpus_texts, labels) -> None
    .predict(query) -> (category, confidence)
"""

import logging
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

MAX_FEATURES = 10_000
MAX_DF = 0.95
MIN_DF = 1


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
        if len(corpus_texts) != len(labels):
            raise ValueError(
                f"corpus_texts and labels must have same length, got {len(corpus_texts)} and {len(labels)}"
            )
        if not corpus_texts:
            raise ValueError("corpus_texts must not be empty")

        # Clean empty texts — replace with placeholder to avoid fit failure
        texts = [t.strip() if t else "unknown" for t in corpus_texts]

        self._vectorizer = TfidfVectorizer(
            max_features=MAX_FEATURES,
            max_df=MAX_DF,
            min_df=MIN_DF,
            sublinear_tf=True,
        )
        try:
            X = self._vectorizer.fit_transform(texts)
        except ValueError:
            self._vectorizer = TfidfVectorizer(
                max_features=MAX_FEATURES,
                sublinear_tf=True,
            )
            X = self._vectorizer.fit_transform(texts)

        self._classifier = LogisticRegression(
            max_iter=500,
            random_state=42,
        )
        self._classifier.fit(X, labels)
        self._label_set: List[str] = sorted(set(labels))

        logger.info(
            "CategoryClassifier trained on %d docs (%d categories)",
            len(corpus_texts),
            len(self._label_set),
        )

    def predict(self, query: str) -> Tuple[str, float]:
        """Predict the most likely category for a query.

        Args:
            query: Raw user query text.

        Returns:
            (predicted_category, confidence) where confidence is in [0, 1].
        """
        if not query or not query.strip():
            if self._label_set:
                return self._label_set[0], 0.0
            return "unknown", 0.0

        X = self._vectorizer.transform([query])
        pred_label = self._classifier.predict(X)[0]
        proba = self._classifier.predict_proba(X)[0]
        confidence = float(max(proba))

        return pred_label, confidence
