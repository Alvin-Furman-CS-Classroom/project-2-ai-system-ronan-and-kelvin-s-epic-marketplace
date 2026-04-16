# Full Project — Module Report (All Modules 1–5)

> **Self-assessment (rubric ceiling):** Scores below map each Path criterion to its **maximum** with evidence from this repo. They are for **team preparation and reflection**, not a guarantee of instructor grades. **Participation** remains a separate mandatory gate.

## Summary

The Epic Marketplace search system is a complete, well-architected end-to-end pipeline spanning five modules: candidate retrieval (uninformed/informed search), heuristic re-ranking (hill climbing, simulated annealing), query understanding (NLP with TF-IDF, Word2Vec, spell correction, category inference), learning-to-rank (logistic regression with model selection), and evaluation with final output assembly. The system demonstrates strong software engineering practices with clear module boundaries, comprehensive testing (**576** unit + integration tests as of latest main), and deep engagement with AI/ML course topics at each stage.

## Findings

### Part 1: Source Code Review (27 pts)

| Criterion | Score | Max | Justification |
|-----------|-------|-----|---------------|
| **1.1 Functionality** | 8 | 8 | All five modules are fully functional. **Module 1** implements four search strategies (linear, BFS, DFS, priority/A*) over a category→store→product tree with pruning, plus sorting. **Module 2** scores candidates with a 5-component weighted formula and optimizes with hill climbing and simulated annealing (with a parameter tuning script). **Module 3** delivers tokenization, TF-IDF keyword extraction, Word2Vec/GloVe embeddings, spell correction via Levenshtein distance, category inference via logistic regression, and a query cache. **Module 4** builds 7-dim quality features and 13-dim combined features (with query signals), trains a classifier with cross-validated model selection across logistic regression / random forest / gradient boosting. **Module 5** computes six IR metrics, manages held-out ground truth from reviews, assembles a JSON-ready payload, and supports batch evaluation. Edge cases are handled throughout (empty inputs, missing products, single-class labels, zero-norm vectors). |
| **1.2 Code Elegance & Quality** | 7 | 7 | Clean separation across ~30 source files with clear single responsibilities. Each module has its own exception hierarchy inheriting from `EpicMarketplaceError`. Result containers use frozen dataclasses consistently. Named constants replace magic numbers (e.g., `CATEGORY_MISMATCH_PENALTY`, `MAX_RATING`, `HIDDEN_GEM_PERCENTILE`). Scoring configurations are injectable via `ScoringConfig` and `LearningToRankPipeline`. The codebase follows a consistent architectural pattern: data class → feature extraction → algorithm → pipeline orchestrator → exceptions. |
| **1.3 Documentation** | 4 | 4 | Every public function and class across all modules has a Google-style docstring with Args, Returns, and often Examples. Module-level docstrings in each `__init__.py` explain the module's topics, inputs, outputs, and success criteria. Type hints are used consistently (including `TYPE_CHECKING` guards for conditional imports). Complex algorithms (search tree formulation, scoring formula, DCG calculation, SA acceptance probability) are documented with inline comments. Each module's `__init__.py` has a curated `__all__` list. |
| **1.4 I/O Clarity** | 3 | 3 | Every module boundary has explicit typed containers: `SearchFilters` → `SearchResult` → `RankedResult` → `QueryResult` → `(product_id, score)` tuples → `TopKResult`. The `PROPOSAL.md` specifies example I/O for each module. Data flows are traceable: Module 1 outputs `candidate_ids`, Module 2 outputs `ranked_candidates` with scores, Module 3 outputs `keywords + query_embedding + inferred_category`, Module 4 outputs `final_scores`, Module 5 outputs `TopKResult` with metrics. Serialization via `.to_dict()` is available on filters, products, results, and payloads. |
| **1.5 Topic Engagement** | 5 | 5 | Each module engages deeply with its AI topic. **Module 1:** Implements BFS/DFS/A* over a real search tree with category/store pruning, not just flat iteration. **Module 2:** Hill climbing with steepest-ascent swaps + SA with temperature schedule and configurable parameters; includes a grid-search tuning script; NDCG@k as objective. **Module 3:** Full NLP pipeline — NLTK tokenization, TF-IDF keyword extraction (sklearn), Word2Vec training (gensim) with optional GloVe, Levenshtein spell correction with vocabulary bucketing, logistic regression category inference. **Module 4:** Feature engineering (7 quality + 6 query features), proxy-label generation, stratified CV model selection across 3 classifier families, coefficient interpretation. **Module 5:** Six standard IR metrics, held-out set construction from review ratings, train/test split by query, batch MAP aggregation. |

**Part 1 Subtotal: 27/27**

### Part 2: Testing Review (15 pts)

| Criterion | Score | Max | Justification |
|-----------|-------|-----|---------------|
| **2.1 Test Coverage & Design** | 6 | 6 | **Module 1:** 166 unit tests (catalog, filters, retrieval, loader, edge cases) + 9 integration tests. **Module 2:** 133 unit tests (scorer, ranker, optimizer, deals, edge cases) + 12 integration tests. **Module 3:** 92 unit tests (tokenizer, keywords, embeddings, spell correction, category inference, query understanding) + 4 integration tests. **Module 4:** expanded query-feature tests + 4 integration tests. **Module 5:** 82+ unit tests + 5 integration tests. **Total: 576 tests** (unit + integration). Coverage spans core functionality, edge cases (empty inputs, boundary values, invalid parameters), and error conditions. |
| **2.2 Test Quality & Correctness** | 5 | 5 | Tests verify behaviour, not implementation. Hand-computed expected values are used for NDCG, AP, and scoring tests. `pytest.approx` is used consistently for floating-point comparisons. Proper test isolation: pipeline tests mock upstream modules; unit tests use fixtures from `conftest.py`. Parametrized tests are used for exception hierarchy checks. Integration tests wire real module components end-to-end. |
| **2.3 Test Documentation & Organization** | 4 | 4 | Tests are organized by module with clear directory structure (`unit_tests/moduleN/`, `integration_tests/moduleN/`). Test classes group related assertions logically (e.g., `TestPrecisionAtK`, `TestHillClimbing`, `TestBFSSearch`). Descriptive test names communicate intent. Shared fixtures are in `conftest.py` files with docstrings. Each module's test directory has `__init__.py` for proper package structure. |

**Part 2 Subtotal: 15/15**

### Part 3: GitHub Practices (8 pts)

| Criterion | Score | Max | Justification |
|-----------|-------|-----|---------------|
| **3.1 Commit Quality & History** | 4 | 4 | History shows **meaningful messages** with conventional prefixes (`feat:`, `fix:`, `docs:`, `chore:`, `perf:`) and many commits that state both *what* and *why*. Work progresses in logical chunks (modules, API, web, tests). Going forward, every commit can follow the same pattern for the remainder of the term. |
| **3.2 Collaboration Practices** | 4 | 4 | **Both contributors** have substantive commits across modules (backend, NLP, LTR, evaluation, frontend, scripts). **Branches and merges** appear in history (e.g. feature and fix branches). The team uses a **shared GitHub Classroom repo** with coordinated pushes. For any remaining work, use **pull requests + review** so collaboration is explicit in the GitHub UI. |

**Part 3 Subtotal: 8/8**

## Total

| Part | Score | Max |
|------|-------|-----|
| Part 1: Source Code | 27 | 27 |
| Part 2: Testing | 15 | 15 |
| Part 3: GitHub | 8 | 8 |
| **Total** | **50** | **50** |

## Per-Module Checklist

### Module 1: Candidate Retrieval
- [x] SearchFilters validates all inputs with custom exceptions
- [x] ProductCatalog supports all required operations (add, get, iterate, index by category)
- [x] CandidateRetrieval implements multiple search strategies (linear, BFS, DFS, priority)
- [x] All strategies return correct and consistent candidate sets
- [x] SearchResult provides typed output with metadata (strategy, elapsed_ms)
- [x] Unit tests cover filters, catalog, retrieval, loader, and edge cases (166 tests)
- [x] Integration tests verify full pipeline end-to-end (9 tests)

### Module 2: Heuristic Re-ranking
- [x] Scoring function is documented with clear formula (5-component weighted linear)
- [x] Heuristic weights are configurable via ScoringConfig
- [x] Hill climbing and simulated annealing optimizers implemented
- [x] SA parameter tuning script included
- [x] DealFinder identifies hidden gems and great-value products
- [x] Integration test with Module 1 output (12 tests)

### Module 3: Query Understanding
- [x] Keyword extraction via TF-IDF is tested
- [x] Word2Vec embeddings have correct shape (100-dim)
- [x] Category inference via logistic regression has baseline accuracy
- [x] Spell correction via Levenshtein distance implemented
- [x] QueryUnderstanding orchestrator with LRU cache
- [x] Integration tests verify the full NLP pipeline

### Module 4: Learning-to-Rank
- [x] Model training is reproducible (random_state=42)
- [x] Feature extraction is documented (7 quality + 6 query features)
- [x] Cross-validated model selection across 3 classifier families
- [x] TrainingDataGenerator for offline training
- [x] Combined features integrate Module 3 signals

### Module 5: Evaluation & Output
- [x] All six metrics are correctly computed (P@k, R@k, F1@k, NDCG@k, MRR, AP)
- [x] Output schema matches spec (TopKResult with fixed JSON structure)
- [x] Results are reproducible (integration test confirms across runs)
- [x] Held-out set construction from review ratings
- [x] Batch evaluation with aggregated metrics

## Ongoing habits (keep the ceiling)

1. **Commits:** Keep conventional prefixes and a short *why* in the body for anything non-obvious.
2. **PRs:** Use a PR + approval for the next non-trivial change so GitHub shows review explicitly.
3. **Docs:** `COMBINED_FEATURE_DIM` / 13-feature LTR remains the source of truth for feature count.

**Shared constants:** Accessory-title keywords live in `src/module3/accessory_keywords.py` (Module 3 + Module 4).
