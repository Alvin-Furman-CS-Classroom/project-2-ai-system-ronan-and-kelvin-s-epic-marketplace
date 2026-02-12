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
| 1 | Feb 11 | Module 1 | Complete | 86+ unit tests, integration tests, 4 search strategies (linear/BFS/DFS/priority), typed `SearchResult`, custom exceptions, logging, category index |
| 2 | Feb 26 | Modules 1-2 |  |  |
| 3 | Mar 19 | Modules 1-3 |  |  |
| 4 | Apr 2 | Modules 1-4 |  |  |

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
