"""
Cross-validated model selection for Module 4 LTR.

Trains several sklearn pipelines (scaled features + classifier), scores each with
stratified ROC AUC, refits the winner on the full matrix. Used when you want the
**best-performing** model instead of a fixed logistic regression baseline.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

EstimatorFactory = Callable[[], Any]


def _lr_pipeline(random_state: int) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    random_state=random_state,
                    max_iter=5000,
                    C=2.0,
                    class_weight="balanced",
                    solver="lbfgs",
                    tol=1e-4,
                ),
            ),
        ]
    )


def _rf_pipeline(random_state: int) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=120,
                    max_depth=14,
                    random_state=random_state,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )


def _gb_pipeline(random_state: int) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    random_state=random_state,
                    n_estimators=80,
                    max_depth=3,
                    learning_rate=0.08,
                    subsample=0.9,
                ),
            ),
        ]
    )


def _candidate_factories(random_state: int) -> List[Tuple[str, EstimatorFactory]]:
    return [
        ("logistic_regression", lambda: _lr_pipeline(random_state)),
        ("random_forest", lambda: _rf_pipeline(random_state)),
        ("gradient_boosting", lambda: _gb_pipeline(random_state)),
    ]


def _cv_splits(y: np.ndarray, requested: int, random_state: int) -> StratifiedKFold:
    counts = np.bincount(y.astype(np.int64, copy=False))
    min_class = int(counts.min())
    if min_class < 2:
        raise ValueError("need at least 2 samples in each class for model selection")
    n_splits = min(requested, min_class)
    n_splits = max(2, n_splits)
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)


def compare_models(
    X: np.ndarray,
    y: np.ndarray,
    *,
    random_state: int = 42,
    n_splits: int = 5,
) -> List[Dict[str, float]]:
    """Return one dict per candidate: ``name``, ``mean_roc_auc``, ``std_roc_auc``."""
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.int64).ravel()
    cv = _cv_splits(y, n_splits, random_state)
    rows: List[Dict[str, float]] = []
    for name, factory in _candidate_factories(random_state):
        est = factory()
        scores = cross_val_score(
            est,
            X,
            y,
            cv=cv,
            scoring="roc_auc",
            n_jobs=-1,
        )
        rows.append(
            {
                "name": name,
                "mean_roc_auc": float(np.mean(scores)),
                "std_roc_auc": float(np.std(scores)),
            }
        )
    rows.sort(key=lambda r: r["mean_roc_auc"], reverse=True)
    return rows


def fit_best_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    *,
    random_state: int = 42,
    n_splits: int = 5,
) -> Tuple[str, float, Pipeline]:
    """Pick the highest mean ROC AUC under stratified CV, then refit on all data.

    Returns:
        ``(winner_name, mean_cv_roc_auc, fitted_pipeline)``
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.int64).ravel()
    cv = _cv_splits(y, n_splits, random_state)

    best_name = "logistic_regression"
    best_mean = -1.0
    best_factory: EstimatorFactory = lambda: _lr_pipeline(random_state)

    for name, factory in _candidate_factories(random_state):
        est = factory()
        scores = cross_val_score(
            est,
            X,
            y,
            cv=cv,
            scoring="roc_auc",
            n_jobs=-1,
        )
        mean_auc = float(np.mean(scores))
        logger.info(
            "LTR model selection: %s mean ROC AUC=%.4f (+/- %.4f)",
            name,
            mean_auc,
            float(np.std(scores)),
        )
        if mean_auc > best_mean:
            best_mean = mean_auc
            best_name = name
            best_factory = factory

    final = best_factory()
    final.fit(X, y)
    logger.info("LTR selected model: %s (CV mean ROC AUC=%.4f)", best_name, best_mean)
    return best_name, best_mean, final
