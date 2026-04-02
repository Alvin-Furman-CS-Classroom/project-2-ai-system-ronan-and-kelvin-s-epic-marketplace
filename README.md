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

### Module 3: Query Understanding (NLP before LLMs)

**Inputs:** `query_text` (free-text user query)  
Example: `"bluetooth headphones for running"`

**Outputs:** `QueryResult` dataclass with `keywords` (ranked TF-IDF terms), `query_embedding` (100-d Word2Vec average), `inferred_category` (Logistic Regression prediction), `confidence` (classifier probability)  
Example: `QueryResult(keywords=[("bluetooth", 0.72), ("headphones", 0.69)], query_embedding=array(shape=(100,)), inferred_category="Electronics", confidence=0.91)`

**Pipeline components:**
- `tokenizer.py` — Lowercase, punctuation removal, NLTK stopword filtering, n-gram extraction
- `keywords.py` — TF-IDF vectorizer fitted on product corpus, extracts top-k query keywords by score
- `embeddings.py` — Custom Word2Vec trained on product text (skip-gram, 100-d), optional GloVe loader, cosine similarity ranking
- `category_inference.py` — TF-IDF + Logistic Regression classifier trained on product text → category
- `query_understanding.py` — Orchestrator combining all components into a single `understand(query)` call
- `spell_correction.py` — Levenshtein edit-distance spell correction against Word2Vec vocabulary, suggests corrected queries for misspelled tokens (edit distance ≤ 2)
- NLP query cache — 256-entry LRU cache on `understand()` so repeated queries skip the full NLP pipeline

**API integration:**
- `/api/search?q=...` — When `q` is provided, Module 3 infers category (used if user didn't pick one), then re-ranks candidates by embedding cosine similarity
- `/api/query-understand?q=...` — Debug endpoint returning raw NLP pipeline output
- `/api/autocomplete?q=...` — Fast prefix-match autocomplete returning matching product titles and categories
- `/api/products/{id}/similar` — Returns 8 most similar products using Word2Vec embedding cosine similarity

**Frontend:**
- "Did you mean?" spell correction banner (amber banner with click-to-search)
- Search autocomplete typeahead dropdown with debounced suggestions (categories with purple icon, products with package icon, keyboard navigation)
- Search history + trending searches shown when search bar is focused (recent searches with clock icon, trending with trending icon, removable history items)
- "Recently Viewed" products section on homepage and search results (localStorage, up to 10 products, horizontal scrollable)
- "Customers Also Viewed" similar products grid on product detail page (lazy-loaded after main content)
- Skeleton loading cards on search results and product detail pages

**Dependencies:** NLP unit (NLTK tokenization, TF-IDF, Word2Vec, Logistic Regression)

**Tests:** 96 tests — tokenizer (19), keywords (12), embeddings (22), category inference (9), orchestrator (8), spell correction (22), integration with Modules 1-2 (4)

### Module 4: Learning-to-Rank (Supervised Learning)

**Inputs:** Candidate products from Module 1, product features, `QueryResult` from Module 3, optional user `price_band`, training labels (synthetic or explicit)  
Example: `pipeline.fit_rank(products, price_band=(10.0, 50.0), top_k=24)`

**Outputs:** `List[Tuple[product_id, score]]` sorted descending — final relevance scores in (0, 1)  
Example: `[("p89", 0.86), ("p12", 0.81), ("p45", 0.73)]`

**Pipeline components:**
- `features.py` — 7 product-quality features: rating_norm, review_strength, description_richness, bullet_richness, price_norm_in_band, value_core, perf_per_dollar_hint. Normalised to [0, 1], price band aware.
- `query_features.py` — 4 query-product features: cosine_similarity (Word2Vec query vs product embedding), keyword_overlap (TF-IDF keyword fraction in product text), category_match (NLP-inferred vs product category), category_confidence (classifier probability). `compute_combined_features()` horizontally concatenates both into an 11-column matrix.
- `model.py` — `QualityValueRanker` wrapping scikit-learn Logistic Regression (binary, balanced class weight, lbfgs solver). Supports proxy labels (median split on weighted composite) or explicit binary labels. Falls back to heuristic scoring when unfitted. Exposes `coef_as_dict()` for feature importance interpretability.
- `pipeline.py` — `LearningToRankPipeline` orchestrating feature extraction + model. Methods: `fit()`, `rank()`, `fit_rank()`. Graceful fallback on insufficient data.
- `training_data.py` — `TrainingDataGenerator` producing synthetic (X, y) training pairs. Uses 20 representative queries run through Module 3. Relevance labels computed from a weighted composite (30% cosine sim, 25% category match, 15% keyword overlap, 15% rating, 10% reviews, 5% noise) then median-split into binary labels. Deterministic via seed.
- `exceptions.py` — `LearningToRankError`, `InsufficientTrainingDataError`, `ModelNotFittedError`, `FeatureConstructionError`

**API integration:**
- `/api/search` — After Module 3 re-ranking, Module 4 LTR re-ranks candidates by learned quality-value scores when the model is fitted. Price band from user filters is passed for consistent feature scaling.

**Dependencies:** Supervised learning unit (Logistic Regression); Modules 1-3 (`Product`, `ProductCatalog`, `QueryResult`, `ProductEmbedder`)

**Tests:** 51 tests — exceptions (4), features (5), model (6), pipeline (4), query features (15), training data (13), integration (4)

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
- `nltk>=3.8.0` — Tokenization, stopwords (Module 3)
- `gensim>=4.3.0` — Word2Vec embeddings (Module 3)
- `numpy>=1.24.0` — Vector math (Module 3)
- `scikit-learn>=1.3.0` — TF-IDF, Logistic Regression (Module 3)

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

# Run Module 3: Query Understanding example
python -c "
from src.module3 import KeywordExtractor, ProductEmbedder, EMBEDDING_DIM
from src.module3.tokenizer import tokenize, extract_ngrams

# Tokenize a query
tokens = tokenize('bluetooth headphones for running')
print(f'Tokens: {tokens}')
print(f'Bigrams: {extract_ngrams(tokens)}')

# Keyword extraction from a small corpus
corpus = [
    'wireless bluetooth headphones noise cancelling',
    'running shoes lightweight breathable mesh',
    'portable bluetooth speaker waterproof outdoor',
]
kw = KeywordExtractor(corpus)
keywords = kw.extract('bluetooth headphones for running')
print(f'Keywords: {keywords}')

# Word embeddings and similarity
emb = ProductEmbedder(corpus)
vec = emb.embed_query('bluetooth headphones')
print(f'Embedding shape: {vec.shape}  (dim={EMBEDDING_DIM})')
sim = emb.similarity('bluetooth headphones', 'wireless bluetooth speaker')
print(f'Similarity: {sim:.4f}')

# Rank products by relevance
ranked = emb.rank_by_similarity('bluetooth headphones', {
    'headphones': 'wireless bluetooth headphones noise cancelling',
    'shoes': 'running shoes lightweight breathable mesh',
    'speaker': 'portable bluetooth speaker waterproof outdoor',
})
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

# Run Module 3 tests only
pytest unit_tests/module3/ -v

# Run integration tests
pytest integration_tests/ -v

# Run with coverage (optional, requires pytest-cov)
pytest unit_tests/ -v --cov=src
```

**Test Data:** Unit tests use fixtures defined in each test file. No external data files required for Module 1.

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 | Feb 11 | Module 1 | Complete | 182 tests (unit + integration), 4 search strategies over category tree, typed `SearchResult`, custom exceptions, structured logging, category index, BFS/DFS pruning — see [Evidence of Usage](#evidence-of-usage) |
| 2 | Feb 26 | Modules 1-2 | Complete | 327 tests (unit + integration). Module 2: 40 scorer + 49 ranker + 13 optimizer + 18 edge-case + 12 integration tests. 3 ranking strategies (baseline, hill climbing, simulated annealing), weighted scoring, NDCG@k, `/api/rerank`, SA tuning script (`tune_sa.py`), RerankComparison page (`/compare`) |
| 3 | Mar 19 | Modules 1-3 | Complete | 423 tests (unit + integration). Module 3: 19 tokenizer + 12 keyword + 22 embedding + 9 category + 8 orchestrator + 22 spell correction + 4 integration tests. NLP pipeline (tokenizer → TF-IDF keywords → Word2Vec embeddings → Logistic Regression category), spell correction, 256-entry NLP LRU cache, `/api/search?q=`, `/api/query-understand`, `/api/autocomplete`, `/api/products/{id}/similar`, inferred category chip, "Did you mean?" banner, autocomplete typeahead, search history + trending, recently viewed, customers also viewed (similar products), skeleton loading |
| 4 | Apr 2 | Modules 1-4 | Complete | 474 tests (unit + integration). Module 4: 4 exception + 5 feature + 6 model + 4 pipeline + 15 query feature + 13 training data + 4 integration tests. LTR pipeline (product-quality features + query-product features → Logistic Regression classifier), synthetic training data generator, `/api/search` Module 4 re-ranking, `coef_as_dict()` interpretability |

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

474 passed in 5.13s
```

| Suite | Location | Count | Focus |
| ----- | -------- | ----- | ----- |
| Catalog | `unit_tests/module1/test_catalog.py` | 44 | CRUD, validation, from_amazon_meta, category index |
| Filters | `unit_tests/module1/test_filters.py` | 18 | Range, defaults, from_dict, store, sort_by |
| Retrieval | `unit_tests/module1/test_retrieval.py` | 86 | Strategies, sorting, store filter, heuristic |
| Module 1 Edge Cases | `unit_tests/module1/test_edge_cases.py` | 22 | Boundaries, empty catalogs, exception hierarchy, search-tree, BFS/DFS pruning |
| Working Set | `unit_tests/data/test_working_set_builder.py` | 4 | Category classification, data pipeline |
| Scorer | `unit_tests/module2/test_scorer.py` | 24 | Price, rating, popularity, category match, richness scoring |
| Ranker | `unit_tests/module2/test_ranker.py` | 30 | Baseline, hill climbing, SA, NDCG, truncation |
| Deals | `unit_tests/module2/test_deals.py` | 13 | Category stats, deal detection, limits, edge cases |
| Module 2 Edge Cases | `unit_tests/module2/test_edge_cases.py` | 25 | Identical products, single weight, large k, null fields |
| Module 2 Optimizer | `unit_tests/module2/test_optimizer.py` | 17 | Convergence, temperature, cooling rate, HC vs SA |
| Integration Module 1 | `integration_tests/module1/test_module1_integration.py` | 9 | End-to-end pipeline, recall vs brute-force |
| Integration Module 2 | `integration_tests/module2/test_module2_integration.py` | 12 | Search→rerank pipeline, strategy agreement, NDCG, category targeting |
| Tokenizer | `unit_tests/module3/test_tokenizer.py` | 19 | Tokenization, stopwords, n-grams, punctuation, unicode, edge cases |
| Keywords | `unit_tests/module3/test_keywords.py` | 12 | TF-IDF extraction, ranking, OOV handling, deduplication |
| Embeddings | `unit_tests/module3/test_embeddings.py` | 22 | Embedding shape, dtype, cosine similarity, ranking, zero vectors |
| Category Inference | `unit_tests/module3/test_category_inference.py` | 9 | Classifier accuracy, confidence range, validation, empty queries |
| Query Understanding | `unit_tests/module3/test_query_understanding.py` | 8 | End-to-end pipeline, QueryResult fields, search_by_text |
| Integration Module 3 | `integration_tests/module3/test_module3_integration.py` | 4 | Full pipeline, category feeds Module 2, text relevance ranking |
| Spell Correction | `unit_tests/module3/test_spell_correction.py` | 22 | Levenshtein distance, token correction, query correction, edge cases |
| LTR Exceptions | `unit_tests/module4/test_exceptions.py` | 4 | Exception hierarchy, EpicMarketplaceError inheritance |
| LTR Features | `unit_tests/module4/test_features.py` | 5 | Feature dim, shape, bounds, price band normalization |
| LTR Model | `unit_tests/module4/test_model.py` | 6 | Fit/predict ordering, insufficient samples, single class, heuristic fallback, explicit labels |
| LTR Pipeline | `unit_tests/module4/test_pipeline.py` | 4 | End-to-end fit_rank, heuristic fallback, graceful degradation, numpy labels |
| Query Features | `unit_tests/module4/test_query_features.py` | 15 | Keyword overlap, cosine similarity bounds, category match, combined features |
| Training Data | `unit_tests/module4/test_training_data.py` | 13 | Label generation, binary labels, both classes, determinism, feature dimension |
| Integration Module 4 | `integration_tests/module4/test_module4_integration.py` | 4 | Package imports, pipeline with catalog, query features, training data |

**Total:** 474 tests

## Checkpoint 4 Reflection

Checkpoint 4 delivers Module 4 — Learning-to-Rank — a supervised classification
model that replaces hand-tuned heuristic weights with data-driven ranking. The
module trains a Logistic Regression classifier on product-quality and query-product
features to produce relevance scores in (0, 1).

**What changed from the initial plan:**

1. **Two-stage feature architecture** — The original plan called for a single feature
   vector. We split features into two independent files: `features.py` (7 product-quality
   features by Ronan) and `query_features.py` (4 query-product features by Kelvin).
   `compute_combined_features()` concatenates both into an 11-column matrix. This
   let the two developers work in parallel with zero merge conflicts.

2. **Proxy labels via median split** — Without real click data, the model uses a
   weighted quality composite (rating, reviews, richness, price position) and
   median-splits it into binary "prefer / don't prefer" labels. This bootstraps
   training without needing user interaction logs.

3. **Synthetic training data generator** — `TrainingDataGenerator` runs 20
   representative queries through Module 3, pairs each with sampled products,
   and computes relevance from a 6-signal weighted composite (cosine similarity,
   category match, keyword overlap, rating, review strength, noise). The noise
   term prevents perfect correlation with any single feature so the model learns
   a meaningful combination.

4. **Query-product features bridge Module 3 into LTR** — Ronan's initial
   implementation scored products by listing quality alone. Kelvin's
   `query_features.py` adds cosine similarity (Word2Vec), TF-IDF keyword overlap,
   NLP category match, and classifier confidence — so the model now answers
   "which product best matches this query" not just "which is the best listing."

5. **Graceful fallback** — If the model can't train (too few products, single class),
   the pipeline falls back to deterministic heuristic scores using the same weight
   vector as the proxy labels. The search API never crashes.

6. **API integration** — Module 4 trains at server startup on synthetic data and
   re-ranks search results after Module 3's embedding re-rank. The `price_band`
   from user filters is passed through for consistent feature scaling.

7. **Interpretability** — `coef_as_dict()` exposes the learned Logistic Regression
   coefficients mapped to human-readable feature names, showing which signals the
   model weighted most heavily.

8. **Test expansion** — 474 tests (up from 423 at Checkpoint 3). 51 Module 4 tests
   cover feature construction, model training/scoring, pipeline orchestration,
   query features, training data generation, and integration with the catalog.

## Checkpoint 3 Reflection

Checkpoint 3 delivers Module 3 — Query Understanding — an NLP pipeline that
transforms free-text search queries into structured signals (keywords, embeddings,
and inferred categories) using pre-LLM techniques.

**What changed from the initial plan:**

1. **Word2Vec over GloVe as default** — The plan called for loading pre-trained
   GloVe 100d vectors (~347MB). We made Word2Vec the default because it trains
   on the actual product corpus (learning domain-specific relationships like
   "bluetooth" ↔ "wireless") and avoids a large download. GloVe is still
   supported as an optional fallback via `use_glove=True`.

2. **TF-IDF keyword extraction** — Instead of a simple "keep all non-stopword
   tokens" approach, we fit a TF-IDF vectorizer on the full product corpus at
   startup. This means query keywords are scored by how discriminative they are
   across products, not just by their presence. Terms like "wireless" (common)
   score lower than "ergonomic" (specific).

3. **Category auto-inference in search** — The `/api/search` endpoint now uses
   Module 3's Logistic Regression classifier to automatically infer a product
   category when the user types a query but doesn't select a category. The
   inferred category is used to narrow results (confidence threshold ≥ 40%),
   and shown as a purple chip in the UI so the user knows what happened.

4. **Embedding-based re-ranking** — When a text query is provided, Module 1
   still finds candidates via filter matching, but Module 3 then re-ranks
   those candidates by cosine similarity between the query embedding and each
   product's text embedding. This means "bluetooth headphones" surfaces
   headphone products even within a large electronics category.

5. **Team task division** — Module 3 was split between two developers with zero
   file overlap. Kelvin built the NLP core (tokenizer, keywords, embeddings)
   and Ronan built the category inference, orchestrator, and integration tests.
   Clear interface contracts ensured both halves snapped together on first merge.

6. **Test expansion** — 423 tests (up from 327 at Checkpoint 2) now cover
   tokenization edge cases, TF-IDF scoring, embedding shapes and similarity,
   category classifier accuracy, end-to-end orchestration, spell correction
   (Levenshtein and SpellCorrector), and Module 3 feeding into Modules 1-2.

7. **Spell correction** — "Did you mean?" feature uses Levenshtein edit distance against the Word2Vec vocabulary to suggest corrections for misspelled query tokens, surfaced in the UI as a clickable amber banner.

8. **Search autocomplete** — As-you-type suggestions from a new `/api/autocomplete` endpoint showing matching categories and product titles, with full keyboard navigation support.

9. **Search history + trending** — Recent searches stored in localStorage appear in the search bar dropdown alongside hardcoded trending queries, with remove-from-history support.

10. **"Recently Viewed" products** — Tracks last 10 clicked products in localStorage via a `useSyncExternalStore` hook, displayed on the homepage and search results page.

11. **"Customers Also Viewed" similar products** — Product detail page shows 8 semantically similar products found via Word2Vec cosine similarity, lazy-loaded after the main content.

12. **Performance: skeleton loading + NLP cache** — Shimmer skeleton cards replace loading spinners, and a 256-entry LRU cache on `QueryUnderstanding.understand()` makes repeated queries instant.

## Checkpoint 2 Reflection

Checkpoint 2 delivers Module 2 — Heuristic Re-ranking — which takes the flat
candidate list from Module 1 and scores every product using a configurable
weighted formula, then optimises the ordering with hill climbing or simulated
annealing.

**What changed from the initial plan:**

1. **Five-signal scoring formula** — The original plan had three signals (price,
   rating, popularity). We added *category match* and *listing richness* (description
   length + feature count) to capture more facets of product quality. Each signal is
   normalised to [0, 1] so the configurable weights stay interpretable.

2. **NDCG@k as the optimisation objective** — Instead of the originally planned
   Precision@k, we use Normalised Discounted Cumulative Gain, which rewards
   placing the best items at the very top. This made the hill-climbing and SA
   optimisers more sensitive to rank positions.

3. **Simulated annealing hyper-parameter tuning** — `tune_sa.py` grid-searches over
   initial temperature, cooling rate, and minimum temperature, reporting the best
   combo by NDCG@k. This was not in the original plan but gives concrete evidence
   of parameter exploration.

4. **Deal Finder** — An additional feature that compares each product's quality-to-
   price ratio against its category average and surfaces "hidden gem" deals. This
   reuses the scoring infrastructure from Module 2 and feeds directly into the
   frontend.

5. **Full-stack integration** — The FastAPI backend exposes `/api/rerank` and
   `/api/deals` endpoints, and the React frontend now has a re-rank comparison
   page (`/compare`) and a "Top Deals" section on the homepage.

6. **Test expansion** — 327 tests (up from 182 at Checkpoint 1) now cover scorer
   logic, ranker strategies, optimiser behaviour, edge cases, deals, and Module 2
   integration with Module 1 candidates.

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
