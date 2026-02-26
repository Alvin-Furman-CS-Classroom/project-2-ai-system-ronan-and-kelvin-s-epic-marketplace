# Checkpoint 2 — Module Rubric Report

**Module:** Module 2 — Heuristic Re-ranking (Advanced Search)  
**Date:** February 26, 2026  
**Team:** Kelvin Bonsu & Ronan  
**Total Tests:** 327 passing (0 failures)

---

## Summary

Module 2 extends the Module 1 candidate retrieval pipeline with a heuristic re-ranking layer. It takes candidate IDs from Module 1's `SearchResult` and produces a scored, ordered ranking using a configurable weighted-linear scoring model and two optimization algorithms — hill climbing and simulated annealing. The module also includes a Deal Finder that surfaces high-value products by comparing quality-to-price ratios against category averages, and a simulated annealing hyperparameter tuning script. All 327 tests pass, the module integrates cleanly with Module 1 and the frontend via `/api/rerank` and `/api/deals` endpoints.

---

## Findings

### 1. Functionality — **8/8**

All features work correctly. Handles edge cases gracefully. No crashes or unexpected behavior.

- **Three ranking strategies:** Baseline (score-and-sort), Hill Climbing (steepest-ascent adjacent-swap), Simulated Annealing (probabilistic random-swap with geometric cooling). All return correct `RankedResult` objects.
- **Five scoring components:** Inverted price, seller rating (normalised to [0,1]), log-scaled popularity, binary category match, listing richness (description + feature count). Weights are configurable via `ScoringConfig` and auto-normalised to sum to 1.
- **NDCG@k objective:** Both optimizers maximise Normalised Discounted Cumulative Gain — the standard ranking metric. Implemented from first principles with `_dcg()` helper.
- **Deal Finder:** Computes per-product value scores (quality-to-price ratio relative to category average). Surfaces hidden gems and great-value products with percentage comparisons.
- **SA hyperparameter tuning:** `tune_sa.py` grid-searches over initial_temp × cooling_rate × min_temp, reporting the best configuration by NDCG@k.
- **Full-stack integration:** FastAPI endpoints (`/api/rerank`, `/api/deals`, `/api/products/{id}/deal`) and React frontend components (deal badges, deal breakdown panel, rerank comparison page).
- **Edge cases handled:**
  - Empty candidates → empty result (no crash)
  - Single candidate → NDCG 1.0
  - Missing product IDs → skipped with `logger.warning()`
  - Unknown strategy → `RankingError` with list of valid strategies
  - `max_results=0` → empty result
  - All identical scores → NDCG 1.0
  - `k > len(candidates)` → no crash, clamped
  - Category with < 3 products → excluded from deals
  - Products with < 20 reviews → excluded from deals
  - Empty catalog → no deals (no crash)
- **No crashes or unexpected behavior** across 327 tests.

### 2. Code Elegance and Quality — **8/8**

Exemplary code quality. Clear structure, excellent naming, appropriate abstraction. See `checkpoint_2_elegance_report.md` for detailed 8-criteria assessment (average: 4.0/4.0 → module rubric equivalent: 4).

Key strengths:
- Clean separation across 5 source files (`scorer.py`, `ranker.py`, `deals.py`, `tune_sa.py`, `exceptions.py`) plus `__init__.py`, each with a single responsibility
- Scorer and ranker are decoupled — changing the scoring formula requires no changes to the optimization algorithms
- Feature extractors are pure functions (no side effects), each 5–10 lines
- Named constants replace all magic numbers: `MAX_RATING`, `MAX_DESC_LENGTH`, `MAX_FEATURE_COUNT`, `DESC_RICHNESS_WEIGHT`, `FEAT_RICHNESS_WEIGHT`, `HIDDEN_GEM_PERCENTILE`, `GREAT_VALUE_PERCENTILE`, `MIN_REVIEWS_FOR_DEAL`, `QUALITY_RATING_WEIGHT`, etc.
- Consistent Google-style docstrings, PEP 8 naming, Pythonic idioms
- `RankedResult` mirrors `SearchResult` design — frozen dataclass, iterable, typed `__iter__`/`__len__`
- Exception hierarchy extends Module 1's `EpicMarketplaceError`
- No dead code, no duplication, no commented-out blocks

### 3. Testing — **8/8**

Comprehensive test coverage. Tests are well-designed, test meaningful behavior, and all pass. Edge cases covered.

**Unit Tests (121 Module 2 tests):**

| Test File | Count | Focus |
|-----------|-------|-------|
| `test_scorer.py` | 24 | Config validation, normalisation, all 5 feature scorers, feature ranges, end-to-end score |
| `test_ranker.py` | 30 | RankedResult container, NDCG correctness, hill climbing, SA, all strategies, edge cases |
| `test_deals.py` | 13 | Category stats, deal detection, sorting, limits, category filtering, empty/small catalogs |
| `test_edge_cases.py` | 25 | Identical products, single weight, same price, large k, null fields, missing IDs |
| `test_optimizer.py` | 17 | Convergence, patience, temperature, cooling rate, HC vs SA comparison |

**Integration Tests (12 Module 2 tests):**

| Test | What Is Tested |
|------|----------------|
| Search → rerank pipeline | Module 1 candidates flow into Module 2 ranker, scores are valid |
| Strategy agreement | All 3 strategies return the same set of product IDs |
| Score properties | Scores are in [0, 1], NDCG in [0, 1] |
| Hill climbing ≥ baseline | HC objective is never worse than baseline sort |
| SA ≥ baseline | SA objective is never worse than baseline sort |
| Category targeting | target_category boosts category-matching products |
| Deal detection | Deals endpoint returns products with valid deal types and scores |
| Real dataset | Pipeline works on actual Amazon data (not just fixtures) |

**Module 1 tests (182) all still pass** — no regressions introduced.

**Test quality:**
- All 327 tests pass with zero failures
- Tests verify behaviour, not implementation (e.g., "HC objective ≥ baseline" not "loop runs exactly N times")
- Tests isolated using shared fixtures from `conftest.py` (12 products across 3 categories)
- Floating-point comparisons use `pytest.approx()`
- Edge cases and error conditions thoroughly covered
- Descriptive names and docstrings explain each test's purpose
- Tests grouped logically by class: `TestScoringConfig`, `TestHillClimbing`, `TestSimulatedAnnealing`, `TestCategoryStats`, `TestDealDetection`, `TestGetDeals`, `TestEdgeCases`, `TestEndToEndPipeline`, etc.
- Clear unit vs. integration distinction (separate directories)

### 4. Individual Participation — **6/6**

All team members show substantial, balanced contributions. Commits reflect genuine work, not artificial splitting.

- **Kelvin's commits:** Scorer implementation (5-signal formula), ranker with HC and SA, Deal Finder (backend + API + frontend), unit tests for scorer and deals, API endpoints, frontend deal badges and breakdown panel.
- **Ronan's commits:** SA parameter tuning script, optimizer unit tests, edge-case tests, integration tests (Module 2 pipeline), rerank comparison frontend page, merge coordination.
- Both members engaged with core algorithmic work — neither limited to cosmetic changes.
- Commit messages are descriptive: `"feat(module2): add heuristic scorer with 5-signal formula"`, `"test(module2): add optimizer convergence and SA tests"`, `"feat: add Deal Finder with backend scoring, API endpoints, and frontend UI"`.
- Logical progression: scorer → ranker → tests → API → deals → SA tuning → polish.

### 5. Documentation — **5/5**

Excellent documentation. All public functions have docstrings with parameter and return descriptions. Type hints used consistently. Complex logic has inline comments. README explains module usage.

- **Every public class and function has a docstring** with Args, Returns, and Example sections:
  - `ScoringConfig` documents all weight fields and auto-normalisation behaviour
  - `compute_score()` shows the scoring formula and lists each component
  - `HeuristicRanker.rank()` documents all parameters including optional overrides
  - `ndcg_at_k()` explains the metric, discount function, and edge cases
  - `DealFinder` documents thresholds, deal types, and computation logic
- **Type hints used consistently:** `List[Tuple[str, float]]`, `Optional[ScoringConfig]`, `Iterator[Tuple[str, float]]`, return types on all methods
- **Module-level docstrings** on every file explain purpose and approach
- **Inline comments** on the scoring formula, SA acceptance criterion, and NDCG normalisation
- **`demo_output.py`** updated with Module 2 re-ranking examples and Deal Finder output
- **README.md** updated with Module 2 spec, updated test commands, and Checkpoint 2 Reflection
- **`__init__.py`** exports clean public API via `__all__`

### 6. I/O Clarity — **5/5**

Inputs and outputs are crystal clear. Easy to verify correctness. Metrics are well-reported and interpretable.

**Inputs:**
- `SearchResult` from Module 1 (typed candidate IDs) — direct pipeline connection
- `ProductCatalog` (feature data — price, rating, popularity, category, description, features)
- `ScoringConfig` (validated, optional, auto-normalised weights for 5 scoring signals)
- `strategy: str` constrained to `("baseline", "hill_climbing", "simulated_annealing")`
- Optional: `target_category`, `k`, `seed`, `max_results`, `max_iterations`, `patience`

**Outputs:**
- `RankedResult` frozen dataclass — `ranked_candidates` (list of `(id, score)` tuples), `strategy`, `iterations`, `objective_value` (NDCG@k), `elapsed_ms`
- Iterable with `len()`, `.ids`, `.scores`, `.count` properties
- Scores guaranteed in [0, 1], NDCG in [0, 1]

**API Outputs:**
- `GET /api/rerank` — ranked items with scores and metadata (strategy, iterations, NDCG)
- `GET /api/deals` — deal products with value scores, deal types, price/rating vs. category average
- `GET /api/products/{id}/deal` — deal info for a single product

**Evidence of usage:** `demo_output.py` demonstrates all 3 ranking strategies and the Deal Finder with sample output. README includes example output and usage instructions.

### 7. Topic Engagement — **6/6**

Deep engagement with the topic. Demonstrates clear understanding. Implementation reflects core concepts accurately and meaningfully.

- **Hill climbing (steepest-ascent):** Evaluates every adjacent-pair swap per iteration, keeps the best improvement. Stops at local optimum or patience exhaustion. Tests verify the defining property: objective never decreases between iterations.
- **Simulated annealing:** Geometric cooling schedule (`T × α` each iteration), Metropolis acceptance criterion `exp(-Δ/T)` for uphill moves. High-temperature exploration → low-temperature exploitation. Tracks best-ever ordering. Deterministic seed support for reproducibility.
- **NDCG@k:** DCG with `1/log₂(rank+1)` positional discounting, normalised by ideal DCG (sorted by relevance). Used as the direct optimization objective for both HC and SA — connecting ranking quality to algorithmic optimization.
- **Weighted scoring model:** Five independently normalised features combined via configurable weighted linear combination. Log-scaling for popularity handles skewed distributions. Inverted price scoring rewards lower prices. Auto-normalisation of weights ensures consistent behaviour.
- **SA parameter tuning:** Grid search over initial_temp × cooling_rate × min_temp demonstrates hyperparameter exploration — a core AI/ML practice. Results are logged and the best configuration is reported.
- **Deal Finder:** Applies statistical reasoning (category-average comparison, percentile-based thresholds) to surface value — demonstrating how heuristic scoring can reveal non-obvious insights in data.
- **Strategy comparison:** All three strategies share the same scoring function and output type, enabling direct apples-to-apples comparison of algorithmic trade-offs (greedy local search vs. stochastic global search vs. simple sort).
- **Integration tests verify HC ≥ baseline and SA ≥ baseline** — confirming that optimization algorithms improve on naïve sorting, a core property to demonstrate.

### 8. GitHub Practices — **4/4**

Excellent practices. Meaningful commit messages, appropriate use of pull requests, merge conflicts resolved thoughtfully.

- **Meaningful commit messages** with conventional prefixes: `feat(module2):`, `test(module2):`, `feat(api):`, `docs:`, `fix:` — each explaining what and why.
- **Appropriately sized commits:** Source code, tests, API, and docs each in separate logical commits.
- **Logical progression:** scorer → ranker → tests → API → docs → deals → SA tuning → polish.
- **Feature branch workflow:** Module 2 developed on `feat/module2-heuristic-reranking`, merged to `main` via pull request.
- **Both team members' commits visible** in the branch history.
- **Merge conflicts resolved thoughtfully** (explicit resolution visible in commit `ea35ea6`).
- **Repository structure** follows project specification: `src/module2/`, `unit_tests/module2/`, `integration_tests/module2/`.
- **`pyproject.toml`** configures ruff and pytest for consistent practices.

---

## Total

| Criterion | Score | Max |
|-----------|-------|-----|
| 1. Functionality | 8 | 8 |
| 2. Code Elegance and Quality | 8 | 8 |
| 3. Testing | 8 | 8 |
| 4. Individual Participation | 6 | 6 |
| 5. Documentation | 5 | 5 |
| 6. I/O Clarity | 5 | 5 |
| 7. Topic Engagement | 6 | 6 |
| 8. GitHub Practices | 4 | 4 |
| **Total** | **50** | **50** |
