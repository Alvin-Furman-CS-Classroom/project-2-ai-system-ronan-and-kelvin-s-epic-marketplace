# Checkpoint 1 — Module Rubric Report

**Module:** Module 1 — Candidate Retrieval  
**Date:** February 13, 2026  
**Team:** Kelvin Bonsu & Ronan  
**Total Tests:** 182 passing (0 failures)

---

## Summary

Module 1 is fully functional, comprehensively tested, and demonstrates deep engagement with uninformed and informed search algorithms. The catalog is modelled as a **Category → Store → Product search tree**, and BFS/DFS traverse that tree with branch-pruning — a genuine application of tree-search concepts. The module cleanly defines inputs (search filters + catalog) and outputs (ranked candidate IDs wrapped in an immutable SearchResult), with excellent documentation, a professional exception hierarchy, and strong GitHub collaboration practices. All 182 tests pass, covering core functionality, edge cases, error conditions, tree-structure validation, pruning efficiency, and cross-strategy integration.

---

## Findings

### 1. Functionality — **8/8**

All features work correctly with graceful edge-case handling:

- **Four search strategies implemented and working:** Linear scan, BFS (breadth-first traversal of Category→Store→Product tree with pruning), DFS (depth-first traversal of the same tree with pruning), Priority search (A*-style with min-heap and heuristic). All four return correct results for all test cases.
- **Five filter types:** price range (min/max), category (case-insensitive), minimum seller rating, store name (case-insensitive), sort order (price asc/desc, rating asc/desc). All enforce hard constraints correctly.
- **Sorting works correctly:** Applied after filtering, before max_results truncation — ensures sorted results respect limits.
- **Edge cases handled:**
  - Empty catalog → empty result (no crash)
  - Single-product catalog → correct match/no-match
  - Price exactly at boundary → correctly included
  - Price one cent below minimum → correctly excluded
  - Rating exactly at minimum → correctly included
  - `max_results=0` → empty result
  - No filters → returns entire catalog
  - Impossible filter combination → empty result (no crash)
- **Data loading works:** Reads gzipped Amazon JSONL, computes seller ratings from reviews, handles missing/malformed data gracefully (returns `None`, no crashes).
- **Real-world dataset:** Successfully loads and searches 18,255 Amazon products.
- **No crashes or unexpected behavior** across 182 test cases.

### 2. Code Elegance and Quality — **8/8**

See `checkpoint_1_elegance_report.md` for detailed assessment. Perfect score of **4.0/4.0** across all 8 code elegance criteria.

Key strengths:
- Clean separation across 5 source files plus `__init__.py`, each with a single responsibility (dead `simple_search.py` removed)
- Descriptive naming throughout (PEP 8 compliant)
- Custom exception hierarchy for precise error handling
- Dataclasses used idiomatically for data containers
- Pythonic dunder methods making `ProductCatalog` a native-feeling collection
- Category index for O(1) category lookups
- Consistent style, no dead code, effective use of Python idioms

### 3. Testing — **8/8**

Comprehensive test coverage with 182 tests across unit and integration test suites:

**Unit Tests (173 tests):**

| Test File | Count | What Is Tested |
|-----------|-------|----------------|
| `test_catalog.py` | 40 | Product creation, validation errors, `from_dict`/`to_dict` round-trips, Amazon meta conversion, missing fields, catalog CRUD, container protocol, category index |
| `test_filters.py` | 29 | Default values, valid ranges, validation errors (negative prices, inverted ranges, bad rating, bad sort), `from_dict` with lists/dicts/strings, `to_dict` round-trips |
| `test_retrieval.py` | 55 | Filter matching (12 scenarios), all 4 strategies return correct results, sorting (price/rating asc/desc), max_results enforcement, search recall, convenience methods, strategy equivalence, priority heuristic behavior |
| `test_edge_cases.py` | 35 | Boundary prices, empty/single catalog, search-result metadata, category index, strategy consistency, exception hierarchy, **search-tree structure** (root node, depths, category coverage, empty catalog), **BFS/DFS tree behaviour** (category/store pruning, scan counts), **pruning efficiency** (fewer scans with filters vs. without) |
| `test_loader.py` | 10 | Seller rating computation, catalog loading from meta, max_products, invalid product skipping, working set loading |
| `test_working_set_builder.py` | 4 | Category mapping rules, ML model training + prediction |

**Integration Tests (9 tests):**

| Test | What Is Tested |
|------|----------------|
| End-to-end pipeline | dict → SearchFilters → search → verify constraints + sorted output |
| Filter round-trip | `from_dict` → `to_dict` lossless |
| Category searchability | Every category in catalog can be searched |
| Store searchability | Every store in catalog can be searched |
| No false positives | Every returned product truly matches all filters |
| 100% recall | No matching product is missed (brute-force validation) |
| Strategy agreement | All 4 strategies produce identical candidate sets |
| Sorted output integrity | Exact price values verified for sorted Books results |
| max_results correctness | Returns exactly the 3 cheapest books ($35, $38, $42) |

**Test quality:**
- All tests verify behavior, not implementation details
- Tests are isolated (use fixtures, not shared mutable state)
- Clear distinction between unit tests and integration tests (separate directories)
- Descriptive test names and docstrings explain each test's purpose
- Tests grouped logically by class (`TestMatchesFilters`, `TestSearchStrategies`, `TestSorting`, `TestStrategyEquivalence`, `TestSearchTree`, `TestBFSTreeBehaviour`, `TestDFSTreeBehaviour`, `TestPruningEfficiency`, etc.)
- Shared fixtures in `conftest.py` (10 sample products, pre-built catalog and retrieval)
- Edge cases and error conditions thoroughly covered

### 4. Individual Participation — **6/6**

Commit history shows substantial, balanced contributions from both team members:

- **Kelvin's commits** include: module architecture and setup, dataset loading pipeline, feature implementation (filters, strategies, sorting), test suite development, production-readiness improvements (exceptions, logging, category index), API layer, frontend build.
- **Ronan's commits** include: data exploration and working set construction, category model training, merge coordination, and collaborative feature work.
- Commit messages are descriptive and meaningful: `"Module 1: remove location, add seller rating, store filter, sorting"`, `"creates a dataframe of our data"`, `"feat: full-stack marketplace UI with React + FastAPI + pagination"`, `"fix: back-to-results preserves search filters and page"`.
- Both members engaged with core functionality — neither relegated to cosmetic tasks.
- Logical progression of work visible in history: setup → data → features → tests → polish → API → frontend.

### 5. Documentation — **5/5**

Excellent documentation across the module:

- **Every public class and function has a docstring** with parameter descriptions, return types, and examples:
  - `Product` docstring lists all attributes with descriptions and usage example
  - `SearchFilters` docstring describes each field and valid values with example
  - `CandidateRetrieval` class docstring describes strategies and provides usage example
  - `search()` docstring includes Args, Returns, and Raises sections
  - `from_amazon_meta()` explains the parameters and return behavior
- **Type hints used consistently:** `Optional[float]`, `List[str]`, `Dict[str, float]`, `Optional[int]`, return types on all methods.
- **Module-level docstrings** on every file explain the file's purpose.
- **Inline comments** explain phases in `compute_seller_ratings()` (Step 1, Step 2, Step 3) and time/space complexity in search methods (`O(n)`, `O(n log n)`).
- **README.md** documents module usage, setup, running instructions, test commands, evidence of usage, and checkpoint reflection.
- **`__init__.py`** provides a clean public API with `__all__`.

### 6. I/O Clarity — **5/5**

Inputs and outputs are crystal clear and easy to verify:

**Inputs:**
- `SearchFilters` dataclass with 6 typed, validated, optional fields. Each field has a docstring. Validation raises `InvalidFilterError` with descriptive messages.
- `ProductCatalog` loaded from files or constructed from a product list. Contains typed `Product` objects.
- `strategy: str` parameter — constrained to `("linear", "bfs", "dfs", "priority")` with clear error on invalid input.
- `max_results: Optional[int]` — self-explanatory.

**Outputs:**
- `SearchResult` frozen dataclass with 4 fields: `candidate_ids` (the answer), `strategy` (which algorithm), `total_scanned` (how many products examined), `elapsed_ms` (performance).
- `SearchResult` is iterable and has `len()` — easy to consume.
- Convenience method `get_candidates_with_products()` returns full `Product` objects instead of just IDs.

**Next module feed:** Module 1's `SearchResult.candidate_ids` becomes the input to Module 2 (Heuristic Re-ranking), which will apply scoring and re-order them.

**Evidence of usage:** `demo_output.py` script runs 3 example searches and prints structured output. README includes sample output for verification.

### 7. Topic Engagement — **6/6**

Deep engagement with search algorithms and AI search concepts:

- **Search tree model:** The product catalog is modelled as a **Category → Store → Product tree** using `SearchNode` dataclasses. `_build_search_tree()` constructs the tree at initialization time. This gives BFS and DFS a genuine tree to traverse rather than a flat list — aligning directly with AI tree-search theory.
- **Uninformed search with pruning:** BFS (queue-based breadth-first) and DFS (stack-based depth-first) traverse the search tree with the canonical data structures (`deque` and `list`). `_can_prune_node()` skips entire category or store branches that cannot match the active filters — a direct application of branch pruning. Tests verify that pruning reduces `total_scanned` compared to unfiltered search.
- **Informed search:** Priority search uses a **min-heap** with a custom **heuristic function** (`_compute_priority`) that estimates how close a product is to matching the filters. This is an A*-style informed search where:
  - Priority 0 = perfect match candidate
  - Penalties accumulate for: wrong category (+100), wrong store (+75), price outside range (proportional distance), low rating (gap × 10)
  - The heuristic ensures best-matching products are evaluated first
- **Linear search** serves as the baseline for comparison — demonstrating the value of informed vs. uninformed approaches.
- **Strategy pattern:** All four strategies share the same interface (`search(filters, strategy)`) and produce the same output type, demonstrating the AI concept of comparing search algorithms under identical conditions.
- **Category index** in `ProductCatalog` demonstrates the concept of precomputed indexes for efficient retrieval — relevant to real search systems.
- **Filter system** models hard constraints, a concept that maps directly to constraint satisfaction in AI.
- **Integration tests verify strategy equivalence** — confirming that all algorithms produce identical results, which is a core correctness property in search.

The implementation reflects genuine understanding of how search algorithms work, why different strategies have different trade-offs (time vs. optimality vs. space), and how to apply them to a real-world product retrieval problem. The tree-based BFS/DFS with pruning goes beyond a textbook flat-list traversal and demonstrates how these algorithms work on hierarchical data in practice.

### 8. GitHub Practices — **4/4**

Excellent development practices throughout:

- **Meaningful commit messages** that explain what and why: `"feat: model catalog as Category→Store→Product search tree for BFS/DFS"`, `"test: add 12 search-tree structure and pruning tests"`, `"docs: add Args/Returns docstrings to all public methods"`, `"docs: fix stale 'location' references in README, update spec to use 'store'"`, `"fix: update test assertions for SearchResult return type"`
- **Commits are appropriately sized** — not too large, not trivially small. Each commit represents a logical unit of work.
- **Logical progression of work** is evident: initial setup → data loading → core features → tests → production polish → API layer → frontend → search-tree refactor → pruning tests.
- **Feature branch workflow:** Improvements developed on `fix/checkpoint1-rubric-improvements` branch with a pull request for review before merging to `main`.
- **Repository structure** follows the project specification exactly (`src/`, `unit_tests/`, `integration_tests/`, `AGENTS.md`, `README.md`).
- **`.gitignore`** properly configured for Python and Node.js artifacts.
- **Active pull requests** demonstrate use of GitHub's collaboration features and code review.
- **`pyproject.toml`** configures linting and testing tools for consistent development practices.
- **Dead code removed:** `simple_search.py` (unused legacy file importing pandas) deleted to keep the codebase clean.
- **Merge conflicts resolved** thoughtfully (visible in merge commits).

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
