"""
Supervised quality–value ranker (Module 4).

Uses **binary classification** (logistic regression): the positive class
represents “prefer this listing” — trained either from supplied labels or
from a **proxy** target derived from rating, review volume, and description /
bullet richness among the current candidate set.

``predict_proba`` for the positive class yields a **ranking score** in ``(0, 1)``.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.module1.catalog import Product
from src.module4.exceptions import InsufficientTrainingDataError, ModelNotFittedError
from src.module4.features import FEATURE_DIM, compute_quality_value_features

logger = logging.getLogger(__name__)

# Weights for proxy label: emphasize rating & reviews, then listing depth
_PROXY_WEIGHTS = np.array([0.30, 0.22, 0.18, 0.12, 0.08, 0.06, 0.04], dtype=np.float64)


def _proxy_labels(X: np.ndarray) -> np.ndarray:
    """Median split on composite quality — top half = positive."""
    if X.shape[0] < 2:
        raise InsufficientTrainingDataError("need at least 2 products to derive proxy labels")
    composite = X @ _PROXY_WEIGHTS
    med = float(np.median(composite))
    return (composite >= med).astype(int)


def _heuristic_scores(X: np.ndarray) -> np.ndarray:
    """Deterministic scores in [0, 1] when the classifier is not used."""
    raw = X @ _PROXY_WEIGHTS
    lo, hi = float(np.min(raw)), float(np.max(raw))
    if hi - lo < 1e-12:
        return np.full(X.shape[0], 0.5, dtype=np.float64)
    return (raw - lo) / (hi - lo)


class QualityValueRanker:
    """Logistic regression over :func:`compute_quality_value_features`.

    Prioritizes seller rating, review counts, description and bullet depth,
    and price–performance hints. Use :meth:`score` to obtain ranking scores.
    """

    def __init__(
        self,
        *,
        random_state: int = 42,
        max_iter: int = 2000,
        C: float = 1.0,
    ) -> None:
        self._clf = LogisticRegression(
            random_state=random_state,
            max_iter=max_iter,
            C=C,
            class_weight="balanced",
            solver="lbfgs",
        )
        self._fitted = False
        self._price_band: Optional[Tuple[float, float]] = None

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def fit(
        self,
        products: Sequence[Product],
        *,
        labels: Optional[np.ndarray] = None,
        price_band: Optional[Tuple[float, float]] = None,
    ) -> "QualityValueRanker":
        """Train the classifier.

        Args:
            products: Labeled training products (same schema as at inference).
            labels: Optional ``(n,)`` binary ``{0,1}``. If omitted, labels are
                generated via a median split on a weighted quality composite.
            price_band: Optional user ``(price_min, price_max)`` for feature scaling.

        Raises:
            InsufficientTrainingDataError: Too few rows or a single class.
        """
        products_list = list(products)
        if len(products_list) < 2:
            raise InsufficientTrainingDataError(
                "need at least 2 products to fit QualityValueRanker"
            )

        X = compute_quality_value_features(products_list, price_band=price_band)
        if X.shape[1] != FEATURE_DIM:
            raise InsufficientTrainingDataError("unexpected feature dimension")

        if labels is None:
            y = _proxy_labels(X)
        else:
            y = np.asarray(labels, dtype=np.int64).ravel()
            if y.shape[0] != X.shape[0]:
                raise InsufficientTrainingDataError(
                    f"labels length {y.shape[0]} != products {X.shape[0]}"
                )
            if not np.isin(y, [0, 1]).all():
                raise InsufficientTrainingDataError("labels must be 0 or 1")

        if len(np.unique(y)) < 2:
            raise InsufficientTrainingDataError(
                "training labels have a single class — cannot fit logistic model"
            )

        self._clf.fit(X, y)
        self._fitted = True
        self._price_band = price_band
        logger.info(
            "QualityValueRanker fitted on %d examples (positive rate %.2f)",
            len(products_list),
            float(np.mean(y)),
        )
        return self

    def score(
        self,
        products: Sequence[Product],
        *,
        price_band: Optional[Tuple[float, float]] = None,
    ) -> List[Tuple[str, float]]:
        """Return ``(product_id, score)`` sorted by descending score.

        Uses ``predict_proba[:, 1]`` when fitted; otherwise :func:`_heuristic_scores`.

        Args:
            products: Candidates to score (non-empty).
            price_band: Price window for normalization; defaults to the band
                stored at fit time, else inferred from this batch.
        """
        products_list = list(products)
        if not products_list:
            return []

        band = price_band if price_band is not None else self._price_band
        X = compute_quality_value_features(products_list, price_band=band)

        if not self._fitted:
            s = _heuristic_scores(X)
        else:
            s = self._clf.predict_proba(X)[:, 1]

        order = np.argsort(-s)
        return [(products_list[i].id, float(s[i])) for i in order]

    def coef_as_dict(self) -> dict[str, float]:
        """Signed feature weights (interpretability). Requires fitted model."""
        if not self._fitted:
            raise ModelNotFittedError("QualityValueRanker is not fitted")
        from src.module4.features import FEATURE_NAMES

        coef = self._clf.coef_.ravel()
        return {name: float(c) for name, c in zip(FEATURE_NAMES, coef)}
