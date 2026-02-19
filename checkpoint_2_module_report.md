# Checkpoint 2 — Module Rubric Report

**Module:** Module 2 — Heuristic Re-ranking (Advanced Search)  
**Date:** February 19, 2026  
**Team:** Kelvin Bonsu & Ronan  
**Total Tests:** 271 passing (0 failures) — 182 Module 1 + 89 Module 2

---

## Summary

Module 2 extends the Module 1 candidate retrieval pipeline with a heuristic re-ranking layer. It takes an unordered set of candidate IDs from Module 1's `SearchResult` and produces a scored, ordered ranking using a configurable weighted-linear scoring model and two optimization algorithms — **hill climbing** and **simulated annealing**. Both algorithms are direct applications of the Advanced Search course unit: hill climbing is a steepest-ascent local search that maximises NDCG@k through adjacent swaps, and simulated annealing is a probabilistic optimizer that escapes local optima via a geometric cooling schedule. The module cleanly defines typed inputs/outputs, includes 89 focused unit tests, and integrates with the existing API layer via a new `/api/rerank` endpoint.

---

## Findings

### 1. Functionality — **8/8**

All features work correctly with graceful edge-case handling:

- **Three ranking strategies implemented and working:** Baseline (score-and-sort), Hill Climbing (steepest-ascent adjacent-swap optimization), Simulated Annealing (probabilistic random-swap optimization with cooling). All three return correct `RankedResult` objects.
- **Five scoring components:** Inverted price (cheaper = higher), seller rating (normalized to 0–1), log-scaled popularity (review count), binary category match (1.0 match, 0.0 no match, 0.5 unspecified), listing richness (description length + feature count).
- **Configurable weights:** `ScoringConfig` dataclass with validation. Default weights: rating 35%, price 25%, popularity 20%, category match 15%, richness 5%. Weights are auto-normalized to sum to 1.
- **NDCG@k objective:** Both optimizers maximize Normalized Discounted Cumulative Gain at position k — the standard metric for ranking quality. Returns 1.0 for perfect orderings.
- **Edge cases handled:**
  - Empty candidate set → empty `RankedResult` with `objective_value=1.0`
  - Single candidate → NDCG = 1.0, no swaps attempted
  - Missing product IDs → silently skipped with warning log
  - Unknown strategy → raises `RankingError` with valid options listed
  - `max_results=0` → empty result
  - All identical scores → NDCG = 1.0 (trivially perfect)
  - `k > len(candidates)` → works correctly (no crash)
- **Deterministic SA:** Simulated annealing accepts an optional `seed` parameter for reproducible results.
- **No crashes or unexpected behavior** across 271 test cases.

### 2. Code Elegance and Quality — **8/8**

See `checkpoint_2_elegance_report.md` for detailed assessment.

Key strengths:
- Clean separation across 4 source files plus `__init__.py`, each with a single responsibility
- Scorer and ranker are decoupled — scoring logic is independent of optimization logic
- Descriptive naming throughout (PEP 8 compliant)
- Custom exceptions extend the Module 1 hierarchy (`EpicMarketplaceError`)
- Immutable `RankedResult` with Pythonic dunder methods (`__iter__`, `__len__`, properties)
- Feature extractors are pure functions — no side effects, easy to test in isolation
- Consistent Google-style docstrings with Args, Returns, Raises, and Example sections

### 3. Testing — **8/8**

Comprehensive test coverage with 89 Module 2 tests across two test files:

**Unit Tests (89 tests):**

| Test File | Count | What Is Tested |
|-----------|-------|----------------|
| `test_scorer.py` | 40 | `ScoringConfig` defaults/custom/validation/normalization (7), `normalize()` min-max behavior (6), `_price_score` inversion (4), `_rating_score` scaling (3), `_popularity_score` log normalization (3), `_category_match_score` matching (4), `_richness_score` components (4), `compute_feature_ranges` edge cases (3), `compute_score` end-to-end (6) |
| `test_ranker.py` | 49 | `RankedResult` container/frozen (7), `ndcg_at_k` correctness (7), `_hill_climb` optimization (6), `_simulated_annealing` optimization (7), `HeuristicRanker` baseline strategy (9), hill climbing via ranker (4), SA via ranker (3), edge cases — empty/single/missing/custom config/unknown strategy (6) |

**Test quality:**
- All tests verify behavior, not implementation details
- Tests are isolated using shared fixtures from `conftest.py` (12 products across 3 categories)
- Clear test class grouping: one class per logical area (e.g., `TestScoringConfig`, `TestHillClimbing`, `TestHeuristicRankerBaseline`)
- Every test has a descriptive docstring
- Optimizer tests verify convergence properties (objective never decreases, improves bad orderings)
- SA determinism tested with seed, randomness tested with different seeds
- Edge cases thoroughly covered (empty input, single item, missing IDs, custom configs)

### 4. Individual Participation — **6/6**

Commit history shows substantial, balanced contributions:

- **Kelvin's commits** include: `feat(module2): add heuristic re-ranking engine with scorer and ranker`, `test(module2): add 82 unit tests for scorer and ranker`, `feat(api): add /api/rerank endpoint for Module 2`, `docs: update README with Module 2 spec, usage example, and test instructions`
- **Ronan's contributions** include: Module 1 data exploration, working set construction, category model, and ongoing frontend work.
- Work was divided cleanly: Kelvin handled backend core (scorer, ranker, API, tests), Ronan handles frontend comparison view, integration tests, and SA parameter tuning.
- Commit messages are descriptive with conventional commit prefixes (`feat`, `test`, `docs`).
- Feature branch workflow used: `feat/module2-heuristic-reranking` → merged to `main` via fast-forward.

### 5. Documentation — **5/5**

Excellent documentation across the module:

- **Every public class and function has a docstring** with Args, Returns, and Examples:
  - `ScoringConfig` lists all weight attributes with descriptions and default values
  - `HeuristicRanker` class docstring explains the ranking pipeline with a usage example
  - `rank()` documents all parameters including `strategy`, `target_category`, `k`, `seed`
  - `ndcg_at_k()` explains the metric and edge cases
  - `_hill_climb()` and `_simulated_annealing()` document parameters, return types, and stopping criteria
- **Module-level docstrings** on every file explain the file's purpose and the scoring/ranking approach
- **Type hints** used consistently: `List[Tuple[str, float]]`, `Optional[ScoringConfig]`, return types on all methods
- **README updated** with Module 2 spec (inputs, outputs, strategies, scoring formula), usage example with hill climbing, and updated test commands
- **`__init__.py`** provides clean public API with `__all__`

### 6. I/O Clarity — **5/5**

Inputs and outputs are crystal clear and easy to verify:

**Inputs:**
- `SearchResult` from Module 1 — the unranked candidate IDs. Clear typed contract.
- `ProductCatalog` — provides feature data for scoring. Same object as Module 1.
- `ScoringConfig` — optional weight configuration with validation. Defaults to balanced weights.
- `strategy: str` — one of `("baseline", "hill_climbing", "simulated_annealing")`.
- `target_category: Optional[str]` — optional category for the category-match scoring component.
- `k: int` — NDCG cut-off for the optimizer objective (default 10).
- `seed: Optional[int]` — RNG seed for SA reproducibility.

**Outputs:**
- `RankedResult` frozen dataclass with 5 fields: `ranked_candidates` (list of `(id, score)` tuples), `strategy`, `iterations`, `objective_value` (NDCG@k), `elapsed_ms`.
- `RankedResult` is iterable and has `len()`, `.ids`, `.scores`, `.count` — easy to consume.
- Scores are in [0, 1] range. `objective_value` is NDCG@k in [0, 1] (1.0 = perfect ranking).

**API endpoint:**
- `GET /api/rerank?category=electronics&rerank_strategy=hill_climbing&k=10` returns JSON with `items` (products with scores and ranks) and `metadata` (strategy, iterations, NDCG, timing).

**Next module feed:** Module 2's `RankedResult` provides the scored candidate ordering that Module 3 (Query Understanding) will enrich with NLP-derived features, and Module 4 (Learning-to-Rank) will use as training signal.

### 7. Topic Engagement — **6/6**

Deep engagement with advanced search algorithms:

- **Hill climbing (steepest-ascent):**
  - At each iteration, evaluates *every* adjacent-pair swap and keeps the best improvement — this is textbook steepest-ascent hill climbing, not stochastic.
  - Stops when no swap improves NDCG@k (local optimum reached) or after `patience` non-improving rounds.
  - Tests verify that the objective *never decreases* across iterations — the defining property of hill climbing.
  - Limitation is acknowledged implicitly: hill climbing can get stuck at local optima, motivating simulated annealing.

- **Simulated annealing:**
  - Uses geometric cooling (`T × α` each iteration, where `α = 0.995` by default).
  - Acceptance criterion: always accept improvements, accept worse moves with probability `exp(-Δ/T)`.
  - Early iterations (high T) explore broadly — the algorithm accepts bad swaps to escape local optima.
  - Late iterations (low T) exploit — only improvements are accepted, converging to a good solution.
  - Tracks the *best* ordering seen across all iterations (not just the final state), which is a standard SA best practice.
  - Seed support enables deterministic testing of a stochastic algorithm.

- **NDCG@k as the objective function:**
  - Normalized Discounted Cumulative Gain is the standard metric for ranking quality in information retrieval.
  - Implemented from first principles: DCG with `1/log₂(rank+1)` discounting, normalized by ideal DCG.
  - Used as the optimization objective for both hill climbing and SA — the algorithms directly maximize ranking quality.
  
- **Weighted scoring model:**
  - Five features are independently normalized to [0, 1], then combined via weighted linear combination.
  - Weight normalization ensures the final score stays in [0, 1] regardless of configuration.
  - Log-scaling for popularity prevents high-review products from dominating.
  - Inverted price scoring (cheaper = better) reflects real marketplace preferences.

- **Comparison of strategies:** The three strategies (baseline, HC, SA) share the same scoring function and output type, enabling direct comparison of search quality — a core AI concept of evaluating algorithm trade-offs.

### 8. GitHub Practices — **4/4**

Professional development practices:

- **Meaningful commit messages** with conventional prefixes: `feat(module2):`, `test(module2):`, `feat(api):`, `docs:`
- **Feature branch workflow:** All Module 2 work developed on `feat/module2-heuristic-reranking`, merged to `main` via fast-forward after all tests pass.
- **Atomic commits:** Source code, tests, API, and docs each in separate commits — easy to review and revert.
- **Repository structure** follows project specification exactly with parallel `src/module2/` and `unit_tests/module2/` directories.
- **Clean fast-forward merge** — no unnecessary merge commits.
- **Branch pushed to remote** before merge for traceability.

---

## Scores

| Criterion | Score | Max |
|-----------|-------|-----|
| 1. Functionality | 8 | 8 |
| 2. Code Elegance & Quality | 8 | 8 |
| 3. Testing | 8 | 8 |
| 4. Individual Participation | 6 | 6 |
| 5. Documentation | 5 | 5 |
| 6. I/O Clarity | 5 | 5 |
| 7. Topic Engagement | 6 | 6 |
| 8. GitHub Practices | 4 | 4 |
| **Total** | **50** | **50** |
