# Epic Marketplace

## Overview

Epic Marketplace is a small business marketplace search system that helps shoppers
find the right product using search, NLP, and supervised learning. Users
provide a free-text query plus structured filters (price range, category,
seller rating, and store). The system first retrieves candidates with
classic search, then applies heuristic re-ranking from advanced search
techniques. It parses the query with NLP to extract keywords and embeddings
that enrich product features. A learning-to-rank model trains on click or
rating signals to produce final scores, and the system outputs a top-k ranked
list with those scores. This theme is a natural fit for AI concepts because it
combines constraint-based retrieval, query understanding, and data-driven
ranking in a single, end-to-end workflow.

## Team

- Kelvin Bonsu
- Ronan

## Proposal

See `PROPOSAL.md` for the approved Project 1 proposal.

## Module Plan

Your system must include 5-6 modules. Fill in the table below as you plan each module.

| Module | Topic(s) | Inputs | Outputs | Depends On | Checkpoint |
| ------ | -------- | ------ | ------- | ---------- | ---------- |
| 1: Candidate Retrieval | Uninformed/Informed Search | Filters, catalog | Candidate IDs | Search unit | Checkpoint 1 — Feb 11 |
| 2: Heuristic Re-ranking | Advanced Search | Candidate IDs, product/query features | Ranked candidates | Module 1 | Checkpoint 2 — Feb 26 |
| 3: Query Understanding | NLP before LLMs | Query text | Keywords, embedding, inferred category | Module 1 | Checkpoint 3 — Mar 19 |
| 4: Learning-to-Rank | Supervised Learning | Ranked candidates, features, labels | Final scores | Modules 2-3 | Checkpoint 4 — Apr 2 |
| 5: Evaluation & Output | Evaluation Metrics | Final scores, held-out data | Top-k payload, metrics | Module 4 | Checkpoint 5 — Apr 16 |
| 6 (optional) |  |  |  |  |  |

## Module Specs

### Module 1: Candidate Retrieval (Search)

**Inputs:** `SearchFilters` (price range, category, seller rating, store), `ProductCatalog`  
Example: `filters={"price":[10,40],"category":"Computers","seller_rating":">=4.5","store":"Anker"}`

**Outputs:** `SearchResult` (frozen dataclass with `candidate_ids`, `strategy`, `total_scanned`, `elapsed_ms`)  
Example: `SearchResult(candidate_ids=["B07ABC9876","B08GFTPQ5B"], strategy="linear", total_scanned=8, elapsed_ms=0.01)`

**Dependencies:** Search unit (uninformed/informed search)

**Tests:** Unit tests for filter satisfaction and recall; integration test with Module 2 once available

### Module 2: Heuristic Re-ranking (Advanced Search)

**Inputs:** `SearchResult` from Module 1 (candidate IDs), `ProductCatalog`, optional `ScoringConfig` (weight tuning), `target_category`, `strategy`  
Example: `ranker.rank(search_result, strategy="hill_climbing", target_category="electronics", k=10)`

**Outputs:** `RankedResult` (frozen dataclass with `ranked_candidates` list of `(product_id, score)` tuples, `strategy`, `iterations`, `objective_value`, `elapsed_ms`)  
Example: `RankedResult(ranked_candidates=[("p89", 0.73), ("p12", 0.70)], strategy="hill_climbing", iterations=42, objective_value=0.95, elapsed_ms=1.2)`

**Strategies:**
- `baseline` — Score each candidate with the weighted formula, sort descending. Zero optimiser iterations.
- `hill_climbing` — Steepest-ascent local search that tries adjacent swaps each round to maximise NDCG@k. Stops when no swap improves or patience exceeded.
- `simulated_annealing` — Probabilistic optimiser with geometric cooling that accepts worse swaps early (exploration) and converges later (exploitation).

**Scoring formula:** `score = w_price × invert(price) + w_rating × (rating/5) + w_pop × log_popularity + w_cat × category_match + w_rich × richness`

**Dependencies:** Advanced search unit (hill climbing, simulated annealing); Module 1 (`SearchResult`, `ProductCatalog`)

**Tests:** Unit tests for scoring logic (`test_scorer.py`) and ranker behaviour (`test_ranker.py`); integration test with Module 1 candidate output

### Module 3: Query Understanding (NLP)

**Inputs:** `query_text` (free-text user query)  
Example: `"handmade ceramic mug"`

**Outputs:** `keywords`, `query_embedding`, inferred category  
Example: `keywords=["handmade","ceramic","mug"], inferred_category="home/kitchen"`

**Dependencies:** NLP unit

**Tests:** Unit tests for keyword extraction and embedding shape; integration test feeding Module 2

### Module 4: Learning-to-Rank (Supervised Learning)

**Inputs:** `ranked_candidates`, product features, query features, training data  
Example: `training_label={"p89":1,"p12":0}`

**Outputs:** `final_scores` for each candidate  
Example: `final_scores=[("p89",0.86),("p12",0.81)]`

**Dependencies:** Supervised learning unit; Modules 2-3

**Tests:** Unit tests for model training and scoring; integration test with Modules 2-3

### Module 5: Evaluation & Final Output

**Inputs:** `final_scores`, held-out interaction data

**Outputs:** `top_k_results` with scores plus metrics (Precision@k, NDCG@k)  
Example: `top_k_results=[{"id":"p89","score":0.86,"price":22.0,"title":"Ceramic Mug"}]`

**Dependencies:** Supervised learning evaluation metrics; Module 4

**Tests:** Unit tests for metrics; integration test for full pipeline output

## Repository Layout

```
your-repo/
├── src/                              # main system source code
├── unit_tests/                       # unit tests (parallel structure to src/)
├── integration_tests/                # integration tests (new folder for each module)
├── .claude/skills/code-review/SKILL.md  # rubric-based agent review
├── AGENTS.md                         # instructions for your LLM agent
└── README.md                         # system overview and checkpoints
```

## Setup

**Requirements:** Python 3.9+

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `pytest>=7.0.0` — Testing framework

## Data Source

This project uses the Amazon Reviews'23 dataset (Electronics subset) for local development.
Full Electronics files live in `datasets/active/` and are ignored by git:
- `Electronics.jsonl.gz`
- `meta_Electronics.jsonl.gz`

A smaller, commit-friendly sample lives in `datasets/working_set/`:
- `Electronics.jsonl.gz`
- `meta_Electronics.jsonl.gz`

Other category files can be stored in `datasets/ignored/` and are excluded from git.

Source: https://amazon-reviews-2023.github.io/

## Running

```bash
# Run Module 1: Candidate Retrieval example
python -c "
from src.module1 import CandidateRetrieval, SearchFilters, ProductCatalog, Product

# Create sample catalog
products = [
    Product(id='p1', title='Ceramic Mug', price=18.0, category='home', seller_rating=4.8, store='MugShop'),
    Product(id='p2', title='Glass Vase', price=35.0, category='home', seller_rating=4.5, store='MugShop'),
    Product(id='p3', title='Phone Case', price=15.0, category='electronics', seller_rating=4.0, store='TechCo'),
]
catalog = ProductCatalog(products)

# Search with filters
retrieval = CandidateRetrieval(catalog)
filters = SearchFilters(price_min=10, price_max=40, category='home', store='MugShop')
result = retrieval.search(filters)
print(f'Candidates: {result.candidate_ids}')  # ['p1', 'p2']
print(f'Strategy: {result.strategy}, Scanned: {result.total_scanned}')
"

# Run Module 2: Heuristic Re-ranking example
python -c "
from src.module1 import CandidateRetrieval, SearchFilters, ProductCatalog, Product
from src.module2 import HeuristicRanker, ScoringConfig

products = [
    Product(id='p1', title='Ceramic Mug', price=18.0, category='home', seller_rating=4.8, store='MugShop',
            description='Handcrafted ceramic mug', rating_number=5000),
    Product(id='p2', title='Glass Vase', price=35.0, category='home', seller_rating=4.5, store='MugShop',
            description='Elegant glass vase for flowers', rating_number=2000, features=['hand-blown']),
    Product(id='p3', title='Phone Case', price=15.0, category='electronics', seller_rating=4.0, store='TechCo',
            description='Slim protective case', rating_number=8000),
]
catalog = ProductCatalog(products)
retrieval = CandidateRetrieval(catalog)

# Retrieve candidates
result = retrieval.search(SearchFilters(category='home'))

# Re-rank with hill climbing
ranker = HeuristicRanker(catalog)
ranked = ranker.rank(result, strategy='hill_climbing', target_category='home', k=5)
print(f'Strategy: {ranked.strategy}  Iterations: {ranked.iterations}  NDCG: {ranked.objective_value:.3f}')
for pid, score in ranked:
    print(f'  {pid}: {score:.4f}')
"
```

## Testing

**Unit Tests** (`unit_tests/`): Mirror the structure of `src/`. Each module has corresponding unit tests.

**Integration Tests** (`integration_tests/`): New subfolder for each module beyond the first.

```bash
# Run all unit tests
pytest unit_tests/ -v

# Run Module 1 tests only
pytest unit_tests/module1/ -v

# Run Module 2 tests only
pytest unit_tests/module2/ -v

# Run with coverage (optional, requires pytest-cov)
pytest unit_tests/ -v --cov=src
```

**Test Data:** Unit tests use fixtures defined in each test file. No external data files required for Module 1.

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 | Feb 11 | Module 1 | Complete | 182 tests (unit + integration), 4 search strategies over category tree, typed `SearchResult`, custom exceptions, structured logging, category index, BFS/DFS pruning — see [Evidence of Usage](#evidence-of-usage) |
| 2 | Feb 26 | Modules 1-2 | In Progress | 89 Module 2 tests (40 scorer + 49 ranker), 3 ranking strategies (baseline, hill climbing, simulated annealing), weighted scoring with 5 features, NDCG@k objective, `/api/rerank` endpoint, 271 total tests passing |
| 3 | Mar 19 | Modules 1-3 |  |  |
| 4 | Apr 2 | Modules 1-4 |  |  |

## Evidence of Usage

### Sample Search Session

```
$ python demo_output.py

src.module1.catalog | Catalog initialized with 8 products

--- Example 1: Computers under $35 sorted by price ---
src.module1.retrieval | strategy=linear filters={'price': [10, 35], 'category': 'Computers', 'sort_by': 'price_asc'} candidates=3 scanned=8 elapsed=0.01ms
Candidates: ['B07ABC9876', 'B08GFTPQ5B', 'B03MNO8888']
Count: 3  Strategy: linear  Scanned: 8  Elapsed: 0.01ms
  B07ABC9876 | Laptop Stand Adjustable        | $24.50   | rating 4.8
  B08GFTPQ5B | USB-C Hub Adapter              | $29.99   | rating 4.7
  B03MNO8888 | Webcam HD 1080p                | $34.99   | rating 4.5

--- Example 2: All categories, rating >= 4.5, sorted by rating ---
src.module1.retrieval | strategy=priority filters={'seller_rating': '>=4.5', 'sort_by': 'rating_desc'} candidates=4 scanned=8 elapsed=0.01ms
Candidates: ['B07ABC9876', 'B08GFTPQ5B', 'B05GHI7777', 'B03MNO8888']
Count: 4  Strategy: priority  Scanned: 8  Elapsed: 0.01ms
  B07ABC9876 | Laptop Stand Adjustable        | $24.50   | rating 4.8
  B08GFTPQ5B | USB-C Hub Adapter              | $29.99   | rating 4.7
  B05GHI7777 | Mechanical Keyboard            | $59.99   | rating 4.6
  B03MNO8888 | Webcam HD 1080p                | $34.99   | rating 4.5

--- Example 3: No matches (non-existent category) ---
src.module1.retrieval | strategy=linear filters={'category': 'Furniture'} candidates=0 scanned=8 elapsed=0.00ms
Candidates: []
Count: 0
```

### Key Observations

- **Structured logging** emits strategy, filter summary, hit/scan counts, and wall-time for every search call — ready for production monitoring.
- **`SearchResult` dataclass** packages `candidate_ids`, `strategy`, `total_scanned`, and `elapsed_ms`, making downstream consumption explicit and type-safe.
- **Four strategies** (linear, BFS, DFS, priority) are selectable per query and all produce identical candidate sets on the same filters.
- **Search-tree model** — The catalog is structured as a Category → Store → Product tree. BFS explores breadth-first (all categories, then stores, then products). DFS dives deep into one branch before backtracking. Both prune non-matching category/store subtrees for efficiency.
- **Custom exception hierarchy** (`InvalidFilterError`, `ProductNotFoundError`, …) replaces generic exceptions, simplifying error handling throughout the system.
- **Category index** provides O(1) lookup by category, avoiding full scans when the caller already knows the target category.

### Test Summary

```
$ pytest --tb=no -q

182 passed in 2.64s
```

| Suite | Location | Count | Focus |
| ----- | -------- | ----- | ----- |
| Catalog | `unit_tests/module1/test_catalog.py` | 14 | CRUD, validation, category index |
| Filters | `unit_tests/module1/test_filters.py` | 23 | Range, defaults, from_dict, errors |
| Retrieval | `unit_tests/module1/test_retrieval.py` | 55 | Strategies, sorting, edge filters, heuristic |
| Edge Cases | `unit_tests/module1/test_edge_cases.py` | 35 | Boundaries, empty catalogs, exception hierarchy, search-tree structure, BFS/DFS pruning |
| Loader | `unit_tests/module1/test_loader.py` | 10 | Seller ratings, load catalog, max_products |
| Working Set | `unit_tests/data/test_working_set_builder.py` | 4 | Category classification, data pipeline |
| Integration | `integration_tests/module1/test_module1_integration.py` | 9 | End-to-end pipeline, recall vs brute-force |

## Checkpoint 1 Reflection

Checkpoint 1 delivers Module 1 — Candidate Retrieval — the foundation that every
later module builds on. The module accepts structured filters (price range,
category, seller rating, store) plus a strategy selector and returns a typed
`SearchResult` containing the matching product IDs along with search metadata.

**What changed from the initial plan:**

1. **Search-tree model** — Originally BFS and DFS operated on a flat product
   list. The catalog is now modelled as a three-level tree
   (Category → Store → Product). BFS explores level-by-level (all categories
   first) while DFS dives deep into one branch before backtracking. Both
   strategies prune subtrees that cannot match the active filters, so
   category-filtered searches scan only the relevant products.

2. **Typed outputs** — Originally `search()` returned a plain `List[str]`.
   Wrapping results in a frozen `SearchResult` dataclass makes the contract
   explicit and lets downstream modules access metadata (strategy used, scan
   count, elapsed time) without extra bookkeeping.

3. **Custom exceptions** — Generic `ValueError` / `KeyError` raises were
   replaced with a domain exception hierarchy rooted at `EpicMarketplaceError`.
   This gives callers fine-grained `except` clauses and keeps error semantics
   consistent as more modules are added.

4. **Structured logging** — Every search call now emits a single structured log
   line with strategy, filters, candidate count, scanned count, and wall-time.
   This feeds directly into the evaluation work planned for Module 5.

5. **Category index** — `ProductCatalog` now maintains an internal
   `_category_index` (`defaultdict(list)`) that enables O(1) category lookups,
   eliminating full-scan overhead when a category filter is present.

6. **Comprehensive testing** — 182 tests (up from ~30 in the initial draft)
   cover unit, edge-case, search-tree structure, pruning behaviour, and
   integration scenarios, including parametrized strategy-agreement checks that
   verify all four strategies return the same candidate set.

## Required Workflow (Agent-Guided)

Before each module:

1. Write a short module spec in this README (inputs, outputs, dependencies, tests).
2. Ask the agent to propose a plan in "Plan" mode.
3. Review and edit the plan. You must understand and approve the approach.
4. Implement the module in `src/`.
5. Unit test the module, placing tests in `unit_tests/` (parallel structure to `src/`).
6. For modules beyond the first, add integration tests in `integration_tests/` (new subfolder per module).
7. Run a rubric review using the code-review skill at `.claude/skills/code-review/SKILL.md`.

Keep `AGENTS.md` updated with your module plan, constraints, and links to APIs/data sources.

## References

- [pytest documentation](https://docs.pytest.org/)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Project Instructions](https://csc-343.path.app/projects/project-2-ai-system/ai-system.project.md)
- [Code Elegance Rubric](https://csc-343.path.app/rubrics/code-elegance.rubric.md)
