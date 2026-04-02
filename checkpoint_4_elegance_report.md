# Checkpoint 4 — Code Elegance Report

**Module:** Module 4 — Learning-to-Rank (Supervised Learning)  
**Date:** April 2, 2026  
**Team:** Kelvin Bonsu & Ronan

---

## Source Files Reviewed

| File | Lines | Owner | Purpose |
|------|-------|-------|---------|
| `src/module4/features.py` | 122 | Ronan | Product-quality feature construction (7 features) |
| `src/module4/query_features.py` | 112 | Kelvin | Query-product feature construction (4 features) |
| `src/module4/model.py` | 168 | Ronan | QualityValueRanker (Logistic Regression classifier) |
| `src/module4/pipeline.py` | 89 | Ronan | LearningToRankPipeline orchestrator |
| `src/module4/training_data.py` | 167 | Kelvin | Synthetic training data generator |
| `src/module4/exceptions.py` | 25 | Ronan | Custom exception hierarchy |
| `src/module4/__init__.py` | 38 | Both | Public API exports |

---

## Criteria

### 1. Naming — 4/4

Variable, function, class, and module names are descriptive and consistent.

- **Functions:** `compute_quality_value_features`, `compute_query_product_features`, `compute_combined_features`, `_keyword_overlap`, `_band_limits`, `_proxy_labels`, `_heuristic_scores`, `_keyword_overlap_ratio`, `_compute_relevance_scores`. Verb phrases that describe the action. Private helpers prefixed with underscore.
- **Classes:** `QualityValueRanker`, `LearningToRankPipeline`, `TrainingDataGenerator`, `LearningToRankError`, `InsufficientTrainingDataError`, `ModelNotFittedError`, `FeatureConstructionError`. Noun phrases that describe the responsibility. Exception names describe the failure condition.
- **Constants:** `FEATURE_NAMES`, `FEATURE_DIM`, `QUERY_FEATURE_NAMES`, `QUERY_FEATURE_DIM`, `_MAX_DESC`, `_MAX_BULLETS`, `_LOG_REV_SCALE`, `_PROXY_WEIGHTS`, `_LABEL_WEIGHTS`, `SAMPLE_QUERIES`. Module-private constants prefixed with underscore. Public constants are UPPER_SNAKE.
- **Variables:** `rating_norm`, `review_strength`, `description_richness`, `bullet_richness`, `price_norm_in_band`, `value_core`, `perf_per_dollar_hint`, `cos_sim`, `kw_overlap`, `cat_match` — self-documenting, no abbreviation beyond standard conventions (`sim`, `kw`).

### 2. Function/Method Design — 4/4

Functions are focused, minimal, and have clear contracts.

- **Single responsibility:** `_price_score`, `_rating_score`, `_popularity_score`, `_category_match_score`, `_richness_score` each compute one normalized signal. `compute_quality_value_features` assembles them into a matrix. `compute_query_product_features` is independent and handles only query-product signals. `compute_combined_features` just concatenates the two.
- **Clear signatures:** Every function declares parameter types and return types. `Sequence[Product]` for read-only iteration, `List[Product]` for mutation. `Optional[Tuple[float, float]]` for price bands. `np.ndarray` for feature matrices.
- **Docstrings:** Google-style with Args, Returns, Raises sections. Examples where helpful. Module-level docstrings explain the file's role.
- **Method length:** Longest method is `TrainingDataGenerator.generate()` at ~40 lines, which is the natural size for orchestrating query iteration, sampling, feature building, and label computation.
- **`fit` / `score` / `rank` separation:** Model cleanly separates training (`fit`) from inference (`score`). Pipeline adds `rank` (with top_k) and `fit_rank` (convenience).

### 3. Abstraction — 4/4

Clear module boundaries with minimal coupling.

- **Feature / Model / Pipeline layering:** Features know nothing about the model. The model consumes numpy arrays without knowing how they were built. The pipeline connects the two without exposing internals.
- **Two-file feature architecture:** `features.py` depends only on `Product` and `FeatureConstructionError`. `query_features.py` depends on `Product`, `QueryResult`, `ProductEmbedder`, and the quality features function. Neither file imports the model or pipeline.
- **Training data generator:** Depends on Module 3 (`QueryUnderstanding`, `ProductEmbedder`) and Module 4 (`compute_combined_features`), but only through public APIs. No internal state leakage.
- **Exception hierarchy:** `LearningToRankError` inherits from `EpicMarketplaceError`, keeping the project's single exception tree. Subclasses are semantically distinct (`InsufficientTrainingDataError` vs `ModelNotFittedError` vs `FeatureConstructionError`).
- **`__init__.py` as public API:** Explicitly lists `__all__` with 15 exports. Consumers import from `src.module4` without needing to know internal file structure.

### 4. Style Consistency — 4/4

Uniform formatting and conventions across all files and both developers.

- **`from __future__ import annotations`** used consistently for forward references.
- **Import ordering:** stdlib → third-party (`numpy`, `sklearn`) → project (`src.module1`, `src.module3`, `src.module4`). Blank line between groups.
- **Docstring format:** Google style throughout. Module docstrings explain purpose and dependencies. Class docstrings explain lifecycle and usage.
- **Type hints:** Full annotations on all signatures. `Tuple[str, ...]` for named tuples, `Optional[...]` for nullable, `Sequence[...]` for read-only.
- **Consistent patterns between Ronan and Kelvin:** Both files use `List[List[float]]` → `np.asarray(..., dtype=np.float64)` for building matrices row by row. Both validate empty product lists with `FeatureConstructionError`. Both use module-level constants for dimensions and names.

### 5. Code Hygiene — 4/4

No dead code, no commented-out blocks, no debug prints.

- No `print()` statements — all output through `logging.getLogger(__name__)`.
- No commented-out code blocks.
- No unused imports (verified by linter).
- No TODO/FIXME markers left in production code.
- `.gitignore` excludes datasets, virtual environments, IDE files, and `__pycache__`.

### 6. Control Flow — 4/4

Branching is minimal and well-structured.

- **Guard clauses:** Empty product list → raise immediately. Unfitted model → return heuristic scores. Single class labels → raise before fitting.
- **No nested loops beyond necessity:** Feature construction iterates products once with a `zip` for pre-computed log-reviews. Training data iterates queries × products (necessary for cross-product feature matrix).
- **Exception handling:** Pipeline `fit()` catches `InsufficientTrainingDataError` specifically, logs a warning, and continues. API catches broad `Exception` at the LTR re-rank step to never crash the search endpoint.
- **No complex boolean expressions:** Category match is a clean ternary: `1.0 if inferred_cat and p.category.lower() == inferred_cat else 0.0`.

### 7. Pythonic Idioms — 4/4

Effective use of Python and library features.

- **numpy vectorization:** `X @ _PROXY_WEIGHTS` for matrix-vector dot product. `np.argsort(-s)` for descending sort indices. `np.clip`, `np.vstack`, `np.hstack`, `np.concatenate`.
- **List comprehensions:** Feature rows built in loops with `append` (appropriate for heterogeneous computation), but simple transforms use comprehensions: `[p.price for p in products]`.
- **`Sequence` vs `List`:** Read-only parameters typed as `Sequence[Product]` (duck typing), mutable results as `List`.
- **`@property`:** `is_fitted`, `ranker`, `feature_names` expose read-only attributes without setter methods.
- **`dataclass` for data containers:** `QueryResult` (Module 3) carries structured data between modules without boilerplate.
- **`random.Random(seed)`:** Instance-based RNG for deterministic training data generation without affecting global state.
- **Builder pattern:** `QualityValueRanker.fit()` returns `self` for method chaining: `model.fit(products).score(products)`.

### 8. Error Handling — 4/4

Custom exceptions with meaningful messages. Graceful degradation.

- **`FeatureConstructionError("products must not be empty")`** — raised by both `compute_quality_value_features` and `compute_query_product_features` with clear messages.
- **`FeatureConstructionError(f"price_band has min > max: {price_band}")`** — includes the offending value for debugging.
- **`InsufficientTrainingDataError("need at least 2 products to fit")`** — meaningful context. Also raised for label/product length mismatch and single-class labels.
- **`ModelNotFittedError`** — raised by `coef_as_dict()` before accessing `_clf.coef_` on an unfitted model.
- **Pipeline graceful fallback:** `fit()` catches `InsufficientTrainingDataError`, logs `logger.warning(...)`, and leaves the model unfitted. `score()` then returns heuristic scores instead of crashing.
- **API-level safety:** The search endpoint wraps the LTR re-rank step in `try/except Exception` so search never fails because of Module 4.

---

## Score Summary

| Criterion | Score |
|-----------|-------|
| Naming | 4/4 |
| Function/Method Design | 4/4 |
| Abstraction | 4/4 |
| Style Consistency | 4/4 |
| Code Hygiene | 4/4 |
| Control Flow | 4/4 |
| Pythonic Idioms | 4/4 |
| Error Handling | 4/4 |
| **Average** | **4.0/4.0** |
