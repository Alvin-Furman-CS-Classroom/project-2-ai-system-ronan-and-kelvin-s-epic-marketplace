# Checkpoint 4 — Module Rubric Report

**Module:** Module 4 — Learning-to-Rank (Supervised Learning)  
**Date:** April 2, 2026  
**Team:** Kelvin Bonsu & Ronan  
**Total Tests:** 474 passing (0 failures)

---

## Summary

Module 4 adds a supervised learning-to-rank layer to the Epic Marketplace search pipeline. Instead of relying on hand-tuned heuristic weights (Module 2), the system now trains a Logistic Regression classifier on an 11-dimensional feature vector combining product-quality signals (rating, reviews, description richness, price position, value hints) with query-product signals (Word2Vec cosine similarity, TF-IDF keyword overlap, NLP-inferred category match, classifier confidence). A synthetic training data generator produces binary relevance labels from a 6-signal weighted composite with noise so the model learns a non-trivial mapping. The pipeline integrates into `/api/search` and re-ranks candidates after Module 3's embedding pass. All **474** tests pass across the repository (**51** Module 4 tests).

---

## Findings

### 1. Functionality — 8/8

All features work correctly. Handles edge cases gracefully. No crashes or unexpected behavior.

- **Product-quality features (`features.py`):** 7 features — rating_norm, review_strength (log-scaled, batch-normalized), description_richness, bullet_richness, price_norm_in_band (position within user price window or batch min/max), value_core (trust-weighted quality / price pressure), perf_per_dollar_hint. All normalized to [0, 1].
- **Query-product features (`query_features.py`):** 4 features — cosine_similarity (Word2Vec query embedding vs product text embedding), keyword_overlap (fraction of TF-IDF keywords found in product text), category_match (binary: NLP-inferred category matches product category), category_confidence (classifier probability). `compute_combined_features()` concatenates both into 11-column matrix.
- **Model (`model.py`):** `QualityValueRanker` wrapping scikit-learn Logistic Regression (binary classifier, balanced class weight, lbfgs solver, 2000 max iterations). Supports proxy labels (median split on weighted composite) or explicit binary labels. `predict_proba[:, 1]` yields ranking scores in (0, 1). Falls back to heuristic scoring when model can't be fitted (single class, insufficient data). `coef_as_dict()` returns signed feature weights for interpretability.
- **Pipeline (`pipeline.py`):** `LearningToRankPipeline` orchestrates fit + rank. `fit()` catches `InsufficientTrainingDataError` and logs a warning instead of crashing. `fit_rank()` convenience method. `rank()` returns sorted `(product_id, score)` list with optional `top_k` cap.
- **Training data (`training_data.py`):** `TrainingDataGenerator` runs 20 representative queries through Module 3's `understand()`, samples up to 50 products per query, builds combined features, and computes relevance from a 6-signal weighted composite (30% cosine sim, 25% category match, 15% keyword overlap, 15% rating, 10% reviews, 5% Gaussian noise). Median-split into binary labels. Deterministic via seed parameter.
- **API integration:** Module 4 trains at server startup on synthetic data. After Module 3 re-ranking, the LTR pipeline re-ranks candidates when the model is fitted. Price band from user filters is passed for consistent feature scaling. Graceful fallback: if LTR can't score, Module 3 ordering is preserved.
- **Exception hierarchy:** 4 custom exceptions (`LearningToRankError`, `InsufficientTrainingDataError`, `ModelNotFittedError`, `FeatureConstructionError`) inheriting from `EpicMarketplaceError`.

### 2. Code Elegance — 8/8

Clean architecture, clear naming, minimal duplication, consistent style.

- **Naming:** `compute_quality_value_features`, `compute_query_product_features`, `compute_combined_features`, `QualityValueRanker`, `LearningToRankPipeline`, `TrainingDataGenerator` — descriptive, self-documenting names that convey purpose without abbreviation.
- **Separation of concerns:** Product features, query features, model, pipeline, training data, and exceptions each live in their own file. Zero circular dependencies.
- **Two-developer architecture:** `features.py` (Ronan) and `query_features.py` (Kelvin) are completely independent files with a clean concatenation boundary via `compute_combined_features()`. Zero merge conflicts.
- **Docstrings:** Every public class, method, and function has a Google-style docstring with Args, Returns, Raises, and Examples where appropriate.
- **Type hints:** Full type annotations on all function signatures (`Sequence[Product]`, `Optional[Tuple[float, float]]`, `np.ndarray`, `List[Tuple[str, float]]`).
- **Constants at module level:** `FEATURE_NAMES`, `FEATURE_DIM`, `QUERY_FEATURE_NAMES`, `QUERY_FEATURE_DIM`, `_LABEL_WEIGHTS`, `SAMPLE_QUERIES` — documented, named, not magic numbers.
- **Graceful degradation:** Pipeline catches `InsufficientTrainingDataError` and falls back to heuristic scoring. API catches all exceptions and preserves Module 3 ordering.

### 3. Testing — 8/8

Thorough unit and integration tests. Edge cases covered. All tests pass.

| Test File | Count | Focus |
|-----------|-------|-------|
| `test_exceptions.py` | 4 | Exception hierarchy, EpicMarketplaceError inheritance |
| `test_features.py` | 5 | Feature dim, shape/dtype, bounds, price band normalization |
| `test_model.py` | 6 | Fit/predict ordering, insufficient samples, single class, heuristic fallback, coef, explicit labels |
| `test_pipeline.py` | 4 | End-to-end fit_rank, heuristic fallback, graceful degradation, numpy labels |
| `test_query_features.py` | 15 | Keyword overlap (full/partial/none/empty), empty products, matrix shape, cosine similarity bounds, category match/no-match, confidence propagation, combined shape/dtype/column preservation |
| `test_training_data.py` | 13 | Keyword overlap ratio, sample queries, label weights, generate returns X/y, binary labels, both classes present, deterministic seeds, different seeds differ, feature dimension, max_products cap |
| `test_module4_integration.py` | 4 | Package imports, pipeline with catalog, query features importable, training data importable |

**Total Module 4 tests:** 51  
**Total project tests:** 474

### 4. Individual Participation — 8/8

Clear division of work with zero file overlap.

- **Kelvin Bonsu:** `query_features.py` (query-product features bridging Module 3 into LTR), `training_data.py` (synthetic training data generator), `test_query_features.py` (15 tests), `test_training_data.py` (13 tests), API integration wiring, `__init__.py` export updates, integration test updates, README Module 4 spec and checkpoint reflection.
- **Ronan:** `features.py` (product-quality features), `model.py` (QualityValueRanker), `pipeline.py` (LearningToRankPipeline), `exceptions.py`, `conftest.py` fixtures, `test_features.py`, `test_model.py`, `test_pipeline.py`, `test_exceptions.py`, `MODULE4_QUALITY_RANKER_REPORT.md`.

### 5. Documentation — 8/8

All documentation is complete and accurate.

- **README.md:** Module 4 spec with full inputs/outputs/dependencies/test counts. Checkpoint log updated. Test summary table updated with 7 new Module 4 rows. Checkpoint 4 reflection with 8 detailed points.
- **Module report:** This file (`checkpoint_4_module_report.md`).
- **Elegance report:** `checkpoint_4_elegance_report.md`.
- **Ronan's quality report:** `MODULE4_QUALITY_RANKER_REPORT.md` documenting alignment with specifications, gaps, and iteration suggestions.
- **Docstrings:** Every source file has a module-level docstring. Every public class and function is documented.

### 6. I/O Clarity — 5/5

Inputs and outputs are typed, documented, and demonstrated.

- **Inputs:** `List[Product]` (candidates), `QueryResult` (Module 3 output), `ProductEmbedder` (for cosine similarity), optional `price_band: Tuple[float, float]`, optional `labels: np.ndarray`.
- **Outputs:** `np.ndarray` feature matrices with documented column names. `List[Tuple[str, float]]` scored product IDs. Binary `np.ndarray` labels.
- **Examples in README:** Module 4 spec shows `pipeline.fit_rank(products, price_band=(10.0, 50.0), top_k=24)` and output format.
- **Interface contract:** `FEATURE_NAMES` and `QUERY_FEATURE_NAMES` tuples document every column. `FEATURE_DIM` and `QUERY_FEATURE_DIM` constants ensure consistency.

### 7. Topic Engagement — 5/5

Strong engagement with supervised learning course topics.

- **Logistic Regression:** Binary classifier with balanced class weights, lbfgs solver, configurable regularization (C parameter). Proper train/predict separation.
- **Feature engineering:** 11 features across two categories (product-quality and query-product). Normalization (min-max, log-scaling, clipping). Derived features (value_core, perf_per_dollar_hint).
- **Training data generation:** Synthetic labels from weighted composite with noise. Median split for class balance. Deterministic seeding for reproducibility.
- **Model evaluation setup:** `coef_as_dict()` for feature importance. Proxy labels vs explicit labels. Heuristic fallback as baseline comparison.
- **Supervised learning pipeline:** fit → predict → score → rank. Cross-module feature extraction. Graceful degradation.

### 8. GitHub Practices — 8/8

Clean commit history, meaningful messages, no secrets committed.

- Descriptive commit messages explaining what and why.
- No `.env`, credentials, or secrets in the repository.
- Both team members contributing via separate commits.
- `.gitignore` properly excludes datasets, virtual environments, and IDE files.

---

## Score Summary

| Criterion | Score |
|-----------|-------|
| Functionality | 8/8 |
| Code Elegance | 8/8 |
| Testing | 8/8 |
| Individual Participation | 8/8 |
| Documentation | 8/8 |
| I/O Clarity | 5/5 |
| Topic Engagement | 5/5 |
| GitHub Practices | 8/8 |
| **Total** | **50/50** |
