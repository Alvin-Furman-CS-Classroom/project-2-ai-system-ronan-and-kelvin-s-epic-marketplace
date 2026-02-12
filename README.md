# Epic Marketplace

## Overview

Epic Marketplace is a small business marketplace search system that helps shoppers
find the right product using search, NLP, and supervised learning. Users
provide a free-text query plus structured filters (price range, category,
seller rating, and location). The system first retrieves candidates with
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

**Inputs:** `filters` (price range, category, seller rating, location), product catalog  
Example: `filters={"price":[10,40],"category":"home","seller_rating":">=4.5","location":"Boston"}`

**Outputs:** `candidate_ids` (products satisfying hard constraints)  
Example: `candidate_ids=["p12","p89","p203"]`

**Dependencies:** Search unit (uninformed/informed search)

**Tests:** Unit tests for filter satisfaction and recall; integration test with Module 2 once available

### Module 2: Heuristic Re-ranking (Advanced Search)

**Inputs:** `candidate_ids`, product features (price, rating, distance, shipping time), query features  
Example: `features={"p12":{"rating":4.8,"distance_miles":3.2,"price":18.0}}`

**Outputs:** `ranked_candidates` with heuristic scores  
Example: `ranked_candidates=[("p89",0.73),("p12",0.70)]`

**Dependencies:** Advanced search unit; Module 1

**Tests:** Unit tests for scoring logic; integration test with Module 1 candidate output

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
    Product(id='p1', title='Ceramic Mug', price=18.0, category='home', seller_rating=4.8, location='Boston'),
    Product(id='p2', title='Glass Vase', price=35.0, category='home', seller_rating=4.5, location='Boston'),
    Product(id='p3', title='Phone Case', price=15.0, category='electronics', seller_rating=4.0, location='LA'),
]
catalog = ProductCatalog(products)

# Search with filters
retrieval = CandidateRetrieval(catalog)
filters = SearchFilters(price_min=10, price_max=40, category='home', location='Boston')
candidates = retrieval.search(filters)
print(f'Candidates: {candidates}')
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

# Run with coverage (optional, requires pytest-cov)
pytest unit_tests/ -v --cov=src
```

**Test Data:** Unit tests use fixtures defined in each test file. No external data files required for Module 1.

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 | Feb 11 | Module 1 | Complete | 122 tests (unit + integration), 4 search strategies, typed `SearchResult`, custom exceptions, structured logging, category index — see [Evidence of Usage](#evidence-of-usage) |
| 2 | Feb 26 | Modules 1-2 |  |  |
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
- **Custom exception hierarchy** (`InvalidFilterError`, `ProductNotFoundError`, …) replaces generic exceptions, simplifying error handling throughout the system.
- **Category index** provides O(1) lookup by category, avoiding full scans when the caller already knows the target category.

### Test Summary

```
$ pytest --tb=no -q

122 passed in 1.66s
```

| Suite | Location | Count | Focus |
| ----- | -------- | ----- | ----- |
| Catalog | `unit_tests/module1/test_catalog.py` | 14 | CRUD, validation, category index |
| Filters | `unit_tests/module1/test_filters.py` | 23 | Range, defaults, from_dict, errors |
| Retrieval | `unit_tests/module1/test_retrieval.py` | 39 | Strategies, sorting, edge filters |
| Edge Cases | `unit_tests/module1/test_edge_cases.py` | 23 | Boundary prices, empty catalogs, exception hierarchy |
| Working Set | `unit_tests/data/test_working_set_builder.py` | 14 | Category classification, data pipeline |
| Integration | `integration_tests/module1/test_module1_integration.py` | 9 | End-to-end pipeline, recall vs brute-force |

## Checkpoint 1 Reflection

Checkpoint 1 delivers Module 1 — Candidate Retrieval — the foundation that every
later module builds on. The module accepts structured filters (price range,
category, seller rating, location) plus a strategy selector and returns a typed
`SearchResult` containing the matching product IDs along with search metadata.

**What changed from the initial plan:**

1. **Typed outputs** — Originally `search()` returned a plain `List[str]`.
   Wrapping results in a frozen `SearchResult` dataclass makes the contract
   explicit and lets downstream modules access metadata (strategy used, scan
   count, elapsed time) without extra bookkeeping.

2. **Custom exceptions** — Generic `ValueError` / `KeyError` raises were
   replaced with a domain exception hierarchy rooted at `EpicMarketplaceError`.
   This gives callers fine-grained `except` clauses and keeps error semantics
   consistent as more modules are added.

3. **Structured logging** — Every search call now emits a single structured log
   line with strategy, filters, candidate count, scanned count, and wall-time.
   This feeds directly into the evaluation work planned for Module 5.

4. **Category index** — `ProductCatalog` now maintains an internal
   `_category_index` (`defaultdict(list)`) that enables O(1) category lookups,
   eliminating full-scan overhead when a category filter is present.

5. **Comprehensive testing** — 122 tests (up from ~30 in the initial draft)
   cover unit, edge-case, and integration scenarios, including parametrized
   strategy-agreement checks that verify all four strategies return the same set.

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
