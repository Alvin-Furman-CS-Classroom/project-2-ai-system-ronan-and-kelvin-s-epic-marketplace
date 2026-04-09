"""Tests for Module 4 model selection (CV over classifiers)."""

import numpy as np
import pytest

from src.module4.exceptions import InsufficientTrainingDataError
from src.module4.model import QualityValueRanker
from src.module4.model_selection import compare_models, fit_best_pipeline
from src.module4.query_features import COMBINED_FEATURE_DIM


def test_compare_models_returns_three_sorted_by_auc():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((200, COMBINED_FEATURE_DIM))
    z = X[:, 0] + 0.5 * X[:, 1]
    y = (z > np.median(z)).astype(np.int64)
    rows = compare_models(X, y, random_state=1, n_splits=3)
    assert len(rows) == 3
    names = [r["name"] for r in rows]
    assert set(names) == {"logistic_regression", "random_forest", "gradient_boosting"}
    means = [r["mean_roc_auc"] for r in rows]
    assert means == sorted(means, reverse=True)
    assert all(0.0 <= r["mean_roc_auc"] <= 1.0 for r in rows)


def test_fit_best_pipeline_is_fitted_and_predicts():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((120, COMBINED_FEATURE_DIM))
    y = np.concatenate([np.zeros(60), np.ones(60)]).astype(np.int64)
    name, auc, pipe = fit_best_pipeline(X, y, random_state=3, n_splits=3)
    assert name in ("logistic_regression", "random_forest", "gradient_boosting")
    assert 0.0 <= auc <= 1.0
    proba = pipe.predict_proba(X[:5])[:, 1]
    assert proba.shape == (5,)
    assert np.all((proba >= 0.0) & (proba <= 1.0))


def test_quality_value_ranker_select_best_requires_labels():
    rng = np.random.default_rng(4)
    X = rng.random((30, COMBINED_FEATURE_DIM))
    m = QualityValueRanker()
    with pytest.raises(InsufficientTrainingDataError, match="select_best_model"):
        m.fit(X=X, select_best_model=True)


def test_quality_value_ranker_select_best_sets_name():
    rng = np.random.default_rng(5)
    X = rng.standard_normal((180, COMBINED_FEATURE_DIM))
    y = np.concatenate([np.zeros(90), np.ones(90)]).astype(np.int64)
    m = QualityValueRanker(random_state=6)
    m.fit(X=X, labels=y, select_best_model=True)
    assert m.is_fitted
    assert m.selected_model_name in (
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
    )
    assert m.n_features == COMBINED_FEATURE_DIM
