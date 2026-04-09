"""
Supervised quality–value ranker (Module 4).

Uses **binary classification** (default: logistic regression). Optional **model
selection** compares logistic regression, random forest, and gradient boosting
via stratified ROC AUC and keeps the best (see :mod:`src.module4.model_selection`).
Two training paths:

1. **Quality-only** (7 features) — :func:`~src.module4.features.compute_quality_value_features`
2. **Combined** (11 features) — product quality ∪ Module 3 query–product features via
   :func:`~src.module4.query_features.compute_combined_features`, matching
   :class:`~src.module4.training_data.TrainingDataGenerator` output.

Features are **standardized** by default (zero mean, unit variance on the training
set) before logistic regression, which improves accuracy when columns are on
different scales (e.g. cosine similarity vs. price norm). Hyperparameters
``C``, ``max_iter``, and ``tol`` were tuned via stratified cross-validation on
synthetic LTR batches; defaults favor **moderate regularization** (``C=2.0``).

``predict_proba`` for the positive class yields a ranking score in ``(0, 1)``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Tuple, Union

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.module1.catalog import Product
from src.module4.exceptions import InsufficientTrainingDataError, ModelNotFittedError
from src.module4.features import FEATURE_DIM, FEATURE_NAMES, compute_quality_value_features
from src.module4.query_features import (
    COMBINED_FEATURE_DIM,
    COMBINED_FEATURE_NAMES,
    compute_combined_features,
)

if TYPE_CHECKING:
    from src.module3.embeddings import ProductEmbedder
    from src.module3.query_understanding import QueryResult

logger = logging.getLogger(__name__)

# Tuned on stratified 5-fold CV over multiple TrainingDataGenerator seeds
# (combined 11-D features); ``C=2.0`` slightly edged 0.5–1.0 on mean accuracy.
_DEFAULT_C = 2.0
_DEFAULT_MAX_ITER = 5000
_DEFAULT_TOL = 1e-4

# Proxy label weights — quality-only (must match FEATURE_DIM)
_PROXY_WEIGHTS_QUALITY = np.array(
    [0.30, 0.22, 0.18, 0.12, 0.08, 0.06, 0.04], dtype=np.float64
)

# Combined: quality block + (cosine, keyword_overlap, category_match, confidence)
_RAW_COMBINED = np.concatenate(
    [
        _PROXY_WEIGHTS_QUALITY * 0.58,
        np.array([0.18, 0.12, 0.10, 0.02], dtype=np.float64),
    ]
)
_PROXY_WEIGHTS_COMBINED = _RAW_COMBINED / _RAW_COMBINED.sum()


def _weights_for_n_features(n: int) -> np.ndarray:
    if n == FEATURE_DIM:
        return _PROXY_WEIGHTS_QUALITY
    if n == COMBINED_FEATURE_DIM:
        return _PROXY_WEIGHTS_COMBINED
    raise InsufficientTrainingDataError(
        f"expected feature matrix width {FEATURE_DIM} or {COMBINED_FEATURE_DIM}, got {n}"
    )


def _proxy_labels(X: np.ndarray) -> np.ndarray:
    """Median split on weighted composite — top half = positive."""
    if X.shape[0] < 2:
        raise InsufficientTrainingDataError("need at least 2 rows to derive proxy labels")
    w = _weights_for_n_features(X.shape[1])
    composite = X @ w
    med = float(np.median(composite))
    return (composite >= med).astype(int)


def _heuristic_scores(X: np.ndarray) -> np.ndarray:
    """Deterministic scores in [0, 1] when the classifier is not used."""
    w = _weights_for_n_features(X.shape[1])
    raw = X @ w
    lo, hi = float(np.min(raw)), float(np.max(raw))
    if hi - lo < 1e-12:
        return np.full(X.shape[0], 0.5, dtype=np.float64)
    return (raw - lo) / (hi - lo)


def _classifier_step(
    estimator: Union[Pipeline, LogisticRegression],
) -> Any:
    if isinstance(estimator, Pipeline):
        return estimator.named_steps["clf"]
    return estimator


class QualityValueRanker:
    """Classifier over product-quality and/or combined LTR features (default: logistic regression)."""

    def __init__(
        self,
        *,
        random_state: int = 42,
        max_iter: int = _DEFAULT_MAX_ITER,
        C: float = _DEFAULT_C,
        tol: float = _DEFAULT_TOL,
        use_feature_scaling: bool = True,
    ) -> None:
        self._random_state = random_state
        self._max_iter = max_iter
        self._C = C
        self._tol = tol
        clf = LogisticRegression(
            random_state=random_state,
            max_iter=max_iter,
            C=C,
            class_weight="balanced",
            solver="lbfgs",
            tol=tol,
        )
        self._use_feature_scaling = use_feature_scaling
        if use_feature_scaling:
            self._estimator: Union[Pipeline, LogisticRegression] = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("clf", clf),
                ]
            )
        else:
            self._estimator = clf
        self._fitted = False
        self._price_band: Optional[Tuple[float, float]] = None
        self._n_features: Optional[int] = None
        self._selected_model_name: Optional[str] = None
        self._last_cv_mean_roc_auc: Optional[float] = None

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    @property
    def n_features(self) -> Optional[int]:
        """Feature width expected at ``score`` time (7 or 11). ``None`` if unfitted."""
        return self._n_features

    @property
    def selected_model_name(self) -> Optional[str]:
        """Set after ``fit`` — ``logistic_regression`` by default, or CV winner if ``select_best_model``."""
        return self._selected_model_name

    @property
    def cv_mean_roc_auc(self) -> Optional[float]:
        """Mean CV ROC AUC for the selected model when ``select_best_model`` was used; else ``None``."""
        return self._last_cv_mean_roc_auc

    def fit(
        self,
        products: Optional[Sequence[Product]] = None,
        *,
        X: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None,
        price_band: Optional[Tuple[float, float]] = None,
        query_result: Optional[QueryResult] = None,
        embedder: Optional[ProductEmbedder] = None,
        select_best_model: bool = False,
    ) -> "QualityValueRanker":
        """Train the classifier.

        Provide **one** of:

        - ``X``: precomputed feature matrix (e.g. from
          :meth:`TrainingDataGenerator.generate`) — shape ``(n, 7)`` or ``(n, 11)``.
        - ``query_result`` + ``embedder`` + ``products``: builds **combined** (11-dim) rows.
        - ``products`` only: builds **quality-only** (7-dim) rows.

        Args:
            products: Candidate products (required unless ``X`` is given).
            X: Optional precomputed design matrix.
            labels: Binary ``{0,1}``; if omitted, **proxy** median-split labels are used.
            price_band: Passed through to feature builders when ``X`` is not used.
            query_result: Module 3 output for combined features.
            embedder: Shared ``ProductEmbedder`` (must match training / inference).
            select_best_model: If ``True`` (only with ``X`` and explicit ``labels``), run
                stratified CV over several classifiers and refit the ROC-AUC winner.

        Raises:
            InsufficientTrainingDataError: Invalid shapes, too few rows, or one class only.
        """
        if X is not None:
            X_arr = np.asarray(X, dtype=np.float64)
            if X_arr.ndim != 2:
                raise InsufficientTrainingDataError("X must be 2-dimensional")
            if X_arr.shape[1] not in (FEATURE_DIM, COMBINED_FEATURE_DIM):
                raise InsufficientTrainingDataError(
                    f"X has {X_arr.shape[1]} columns; expected {FEATURE_DIM} or {COMBINED_FEATURE_DIM}"
                )
        elif query_result is not None and embedder is not None:
            if not products:
                raise InsufficientTrainingDataError(
                    "products required when using query_result + embedder"
                )
            X_arr = compute_combined_features(
                list(products), query_result, embedder, price_band=price_band
            )
        elif products is not None and len(list(products)) > 0:
            X_arr = compute_quality_value_features(list(products), price_band=price_band)
        else:
            raise InsufficientTrainingDataError(
                "provide X, or products, or products + query_result + embedder"
            )

        if X_arr.shape[0] < 2:
            raise InsufficientTrainingDataError(
                "need at least 2 training rows to fit QualityValueRanker"
            )

        if labels is None:
            y = _proxy_labels(X_arr)
        else:
            y = np.asarray(labels, dtype=np.int64).ravel()
            if y.shape[0] != X_arr.shape[0]:
                raise InsufficientTrainingDataError(
                    f"labels length {y.shape[0]} != rows {X_arr.shape[0]}"
                )
            if not np.isin(y, [0, 1]).all():
                raise InsufficientTrainingDataError("labels must be 0 or 1")

        if len(np.unique(y)) < 2:
            raise InsufficientTrainingDataError(
                "training labels have a single class — cannot fit logistic model"
            )

        if select_best_model:
            if X is None or labels is None:
                raise InsufficientTrainingDataError(
                    "select_best_model requires precomputed X and explicit labels"
                )
            from src.module4.model_selection import fit_best_pipeline

            name, cv_mean, pipe = fit_best_pipeline(
                X_arr,
                y,
                random_state=self._random_state,
                n_splits=5,
            )
            self._estimator = pipe
            self._selected_model_name = name
            self._last_cv_mean_roc_auc = float(cv_mean)
        else:
            self._estimator.fit(X_arr, y)
            self._selected_model_name = "logistic_regression"
            self._last_cv_mean_roc_auc = None
        self._fitted = True
        self._price_band = price_band
        self._n_features = int(X_arr.shape[1])
        logger.info(
            "QualityValueRanker fitted on %d examples, %d features (positive rate %.2f, model=%s)",
            X_arr.shape[0],
            self._n_features,
            float(np.mean(y)),
            self._selected_model_name or "?",
        )
        return self

    def score(
        self,
        products: Sequence[Product],
        *,
        price_band: Optional[Tuple[float, float]] = None,
        query_result: Optional[QueryResult] = None,
        embedder: Optional[ProductEmbedder] = None,
    ) -> List[Tuple[str, float]]:
        """Return ``(product_id, score)`` sorted by descending score.

        If the model was trained on **combined** features, pass the same
        ``query_result`` and ``embedder`` used at training time for that query.
        """
        products_list = list(products)
        if not products_list:
            return []

        band = price_band if price_band is not None else self._price_band

        if self._fitted and self._n_features == COMBINED_FEATURE_DIM:
            if query_result is None or embedder is None:
                raise ValueError(
                    "query_result and embedder are required when scoring a combined (11-feature) model"
                )
            X = compute_combined_features(
                products_list, query_result, embedder, price_band=band
            )
        elif self._fitted and self._n_features == FEATURE_DIM:
            X = compute_quality_value_features(products_list, price_band=band)
        else:
            # Unfitted: default to quality heuristic (7-dim); needs no query
            X = compute_quality_value_features(products_list, price_band=band)

        if not self._fitted:
            s = _heuristic_scores(X)
        else:
            if X.shape[1] != self._n_features:
                raise ValueError(
                    f"scoring matrix has {X.shape[1]} columns but model expects {self._n_features}"
                )
            s = self._estimator.predict_proba(X)[:, 1]

        order = np.argsort(-s)
        return [(products_list[i].id, float(s[i])) for i in order]

    def coef_as_dict(self) -> dict[str, float]:
        """Signed weights on **standardized** features (if scaling enabled).

        Interprets coefficients in z-score space when ``use_feature_scaling`` is True.
        """
        if not self._fitted or self._n_features is None:
            raise ModelNotFittedError("QualityValueRanker is not fitted")
        names = COMBINED_FEATURE_NAMES if self._n_features == COMBINED_FEATURE_DIM else FEATURE_NAMES
        clf = _classifier_step(self._estimator)
        if not hasattr(clf, "coef_"):
            raise ValueError(
                "coef_as_dict is only available for linear (logistic regression) models."
            )
        coef = clf.coef_.ravel()
        return {name: float(c) for name, c in zip(names, coef)}
