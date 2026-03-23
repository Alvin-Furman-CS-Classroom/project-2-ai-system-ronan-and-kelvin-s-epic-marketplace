# Checkpoint 3 — Module Rubric Report

**Module:** Module 3 — Query Understanding (NLP before LLMs)  
**Date:** March 23, 2026  
**Team:** Kelvin Bonsu & Ronan  
**Total Tests:** 423 passing (0 failures)

---

## Summary

Module 3 adds a query understanding layer to the Epic Marketplace pipeline. It transforms free-text search queries (e.g., "bluetooth headphones for running") into structured signals — TF-IDF keywords, Word2Vec embeddings, a Logistic Regression category prediction, and optional spell correction — using pre-LLM NLP techniques. The module is wired into `/api/search` and supporting endpoints so search behaves like a product marketplace: category inference, embedding-based re-ranking, query metadata in responses, fast repeated queries via an LRU cache, autocomplete over titles and categories, and similar-product recommendations from Word2Vec cosine similarity. The frontend surfaces inferred categories and keywords, a "Did you mean?" suggestion when corrections apply, shared search UX (typeahead, history, trending), recently viewed items, related products on detail pages, and skeleton loading states. After the initial checkpoint submission, the team added spell correction (22 new unit tests), the query cache, two API endpoints, and the frontend enhancements above. All **423** tests pass across the repository (**96** Module 3 unit tests, **4** Module 3 integration tests).

---

## Findings

### 1. Functionality — **8/8**

All features work correctly. Handles edge cases gracefully. No crashes or unexpected behavior.

- **Tokenizer:** Lowercasing, punctuation removal, NLTK tokenization, stopword filtering, minimum token length, n-gram extraction (bigrams/trigrams). Handles empty strings, whitespace-only, punctuation-only, unicode, and single-word queries.
- **TF-IDF keyword extraction:** Vectorizer fitted on product corpus with configurable `max_df`, `min_df`, `max_features`, and `sublinear_tf`. Returns ranked (keyword, score) tuples. Gracefully handles tiny/homogeneous corpora by relaxing df thresholds. Deduplicates repeated tokens. OOV tokens appear with score 0.
- **Word2Vec embeddings:** Skip-gram model trained on product corpus (100-d, window=5, min_count=2, 10 epochs). Average-of-word-vectors for query/product embeddings. Optional GloVe loader with automatic fallback to Word2Vec if file not found.
- **Cosine similarity:** Safe against zero-norm vectors (returns 0.0). `rank_by_similarity` produces descending-sorted (id, score) lists.
- **Category inference:** TF-IDF + Logistic Regression classifier trained on product text → category labels. Returns (category, confidence) with confidence in [0, 1]. Empty/whitespace queries return first label with 0 confidence. Input validation: mismatched corpus/label lengths and empty corpus raise `ValueError`.
- **Orchestrator:** `QueryUnderstanding` wires tokenizer, keywords, embeddings, category inference, and spell correction. `understand(query)` returns `QueryResult` with keywords, embedding, inferred category, confidence, and **`corrected_query`** when tokens are fixed within edit distance 2 against the Word2Vec vocabulary.
- **Spell correction (`spell_correction.py`):** Levenshtein edit distance against the trained Word2Vec vocabulary; corrects misspelled tokens within distance ≤ 2; produces a full-query suggestion without altering known-good tokens unnecessarily. Integrated into the pipeline so search and metadata can expose corrections.
- **NLP query cache:** 256-entry LRU cache (`OrderedDict`) on `understand()` so identical repeated queries skip tokenizer, TF-IDF, embedding, classifier, and spell-correction work after the first hit.
- **API integration:** `/api/search?q=` uses Module 3 to auto-infer category (threshold ≥ 40%), re-rank candidates by cosine similarity, return `query_understanding` metadata (including `corrected_query` when applicable), and **`/api/query-understand?q=`** returns full pipeline output for debugging (embedding shape, norm, etc.).
- **`/api/autocomplete`:** Substring matching against product **titles** and **categories** for typeahead suggestions.
- **`/api/products/{id}/similar`:** Returns the **8** most similar products by Word2Vec embedding cosine similarity to the requested product’s text representation.
- **Frontend:** Shared **`SearchBar`** component across entry points; amber **"Did you mean?"** banner when a correction is returned; **autocomplete** dropdown with typeahead; **search history** and **trending** queries in the dropdown; **`useSearchHistory`** and **`useRecentlyViewed`** hooks; **"Recently Viewed"** on the homepage and search results; **"Customers Also Viewed"** grid on the product detail page (backed by similar-product API); **skeleton** loading cards for async product lists.
- **Edge cases handled:**
  - Empty query → empty keywords, zero embedding, no category
  - OOV words → zero embedding vector
  - Stopwords-only query → empty keywords
  - Tiny corpus → relaxed TF-IDF thresholds
  - GloVe file missing → automatic Word2Vec fallback
  - No explicit category filter → auto-infer from query
  - Tokens too far from vocabulary for spell correction → left unchanged; short tokens handled conservatively

### 2. Code Elegance and Quality — **8/8**

Exemplary code quality. Clear structure, excellent naming, appropriate abstraction. See `checkpoint_3_elegance_report.md` for detailed 8-criteria assessment (average: 4.0/4.0).

Key strengths:
- Clean separation across **8** source files in `src/module3/`: `tokenizer.py`, `keywords.py`, `embeddings.py`, `category_inference.py`, `query_understanding.py`, **`spell_correction.py`**, `exceptions.py`, `__init__.py` — each with a focused responsibility
- Tokenizer remains a pure function; `KeywordExtractor` and `ProductEmbedder` are stateful but immutable after init; spell correction reuses the embedder’s vocabulary for a single source of truth
- LRU cache on `understand()` is bounded (256 entries), predictable, and avoids redundant heavy work
- Named constants for training and vectorization (`EMBEDDING_DIM`, `W2V_*`, `MAX_FEATURES`, `MAX_DF`, `MIN_DF`, `MIN_TOKEN_LENGTH`, etc.) keep magic numbers out of call sites
- Consistent Google-style docstrings, PEP 8 naming, type hints throughout
- Stable interface contracts: `tokenize()`, `KeywordExtractor.extract()`, `ProductEmbedder.embed_query()`, spell-correction hooks feeding `QueryResult`
- Exception hierarchy extends Module 1’s `EpicMarketplaceError`
- Frontend: centralized **`SearchBar`**, dedicated hooks (`useRecentlyViewed.ts`, `useSearchHistory.ts`) keep pages thin and behavior consistent

### 3. Testing — **8/8**

Comprehensive test coverage. Tests are well-designed, test meaningful behavior, and all pass.

**Unit Tests (92 Module 3 tests):**

| Test File | Count | Focus |
|-----------|-------|-------|
| `test_tokenizer.py` | 19 | Tokenization, stopwords, n-grams, punctuation, unicode |
| `test_keywords.py` | 12 | TF-IDF extraction, ranking, OOV, deduplication, small corpus |
| `test_embeddings.py` | 26 | Standalone cosine helper, embedding shape/dtype, similarity, ranking, zero vectors, edge cases |
| `test_category_inference.py` | 9 | Classifier accuracy, confidence, validation |
| `test_query_understanding.py` | 8 | End-to-end pipeline, `QueryResult` fields (including integration with orchestration), `search_by_text` |
| **`test_spell_correction.py`** | **22** | **Levenshtein distance (9); `SpellCorrector` token/query behavior (13)** |

**`test_spell_correction.py` (22 tests) — evidence:**

- **9 Levenshtein distance tests:** identical strings; single **insertion**; single **deletion**; single **substitution**; **empty** string pairings; **completely different** strings; **transposition**-style distance behavior — ensuring the distance primitive matches expectations before it drives vocabulary search.
- **13 SpellCorrector tests:** vocabulary size / setup; **known** tokens pass through; **misspelled** tokens corrected when within distance 2 of a vocab word; tokens **too far** from any vocab entry unchanged; **short** tokens handled safely; **query-level** correction strings; **empty** and **whitespace-only** input; **mixed** correct and incorrect tokens in one query.

**Integration Tests (4 Module 3 tests):**

| Test | What Is Tested |
|------|----------------|
| Full pipeline | `query` → `understand()` → valid `QueryResult` with keywords, embedding, category |
| Category labels | Inferred category is from the training label set |
| Text relevance | `search_by_text` ranks "bluetooth headphones" text above "running shoes" |
| Module 3 → Module 2 | Inferred category feeds into `HeuristicRanker` as `target_category` |

**Modules 1–2 and the rest of the suite (323 tests outside these 100 Module 3-focused tests) all still pass** — no regressions introduced.

**Test quality:**
- All **423** tests pass with **zero** failures
- Shared fixtures in `conftest.py` provide reusable corpus, extractor, embedder, classifier (and spell-correction tests use consistent vocabulary/fixtures)
- Embedding tests verify shape, dtype, and relative ordering (not brittle exact floats)
- Integration tests verify the cross-module pipeline: Module 3 → Module 1 → Module 2
- Spell-correction tests separate **algorithm** (Levenshtein) from **policy** (`SpellCorrector` + vocabulary), making failures easy to localize

### 4. Individual Participation — **6/6**

All team members show substantial, balanced contributions with clear ownership and minimal friction.

- **Kelvin’s work:** Tokenizer (preprocessing, stopwords, n-grams), TF-IDF keyword extraction, Word2Vec embeddings with cosine similarity, `__init__.py` exports, core NLP unit tests (tokenizer, keywords, embeddings), shared `conftest` fixtures.
- **Ronan’s work:** Category inference (TF-IDF + Logistic Regression), `QueryUnderstanding` orchestrator, exception hierarchy, category and orchestrator tests, integration tests (Module 3 → Module 2 pipeline), integration `conftest`.
- **Post–initial submission enhancements (shared / iterative):** Spell correction module and its **22** focused unit tests; LRU query cache on `understand()`; **`/api/autocomplete`** and **`/api/products/{id}/similar`**; frontend **`SearchBar`**, **"Did you mean?"**, typeahead, **search history** / **trending**, **recently viewed** and **customers also viewed**, skeleton loaders, and hooks **`useRecentlyViewed`**, **`useSearchHistory`**.
- Task division kept interfaces explicit (`tokenize`, `extract`, `embed_query`, `QueryResult`) so NLP core and classification/orchestration layers could evolve in parallel with few merge conflicts.

### 5. Documentation — **5/5**

Excellent documentation across backend and user-facing behavior.

- **Every public class and function has a docstring** with Args, Returns, and (where helpful) Examples
- **Type hints used consistently:** `List[str]`, `List[Tuple[str, float]]`, `np.ndarray`, `Optional[str]`, `Dict[str, str]`, etc.
- **Module-level docstrings** on each `src/module3/` file explain purpose, approach, and ownership
- **Interface contract** documented and stable: `tokenize()`, `KeywordExtractor.extract()`, `ProductEmbedder.embed_query()` / similarity helpers, **`SpellCorrector`** behavior and **`QueryResult.corrected_query`**
- **README.md** reflects Module 3 scope, how to run the app, checkpoint reflection, and updated test counts
- **`__init__.py`** exports a clean public API via `__all__`
- New **HTTP** surfaces (`/api/autocomplete`, `/api/products/{id}/similar`) follow the same JSON response conventions as existing routes

### 6. I/O Clarity — **5/5**

Inputs and outputs are crystal clear and well-typed.

**Inputs:**
- `tokenize(text: str)` → raw text
- `KeywordExtractor(corpus_texts: List[str])` → product text corpus
- `ProductEmbedder(corpus_texts: List[str])` → product text corpus
- `CategoryClassifier(corpus_texts: List[str], labels: List[str])` → text + labels
- `QueryUnderstanding(corpus_texts, labels)` → unified init (embedder vocabulary also feeds spell correction)
- **`SpellCorrector(vocabulary)`** → iterable of known tokens (e.g., from Word2Vec)
- `/api/search?q=…` → free-text query via URL param
- **`GET /api/autocomplete?q=…`** → partial query string for substring suggestions
- **`GET /api/products/{id}/similar`** → product id for top-8 similar items

**Outputs:**
- `tokenize()` → `List[str]` (cleaned tokens)
- `KeywordExtractor.extract()` → `List[Tuple[str, float]]` (ranked keywords)
- `ProductEmbedder.embed_query()` → `np.ndarray` shape `(100,)`
- `CategoryClassifier.predict()` → `Tuple[str, float]` (category, confidence)
- **`QueryResult`** dataclass → keywords, query_embedding, inferred_category, confidence, **`corrected_query`** (`Optional[str]`)
- **`understand()`** → cached per exact query string up to **256** LRU entries
- `/api/search` response includes `query_understanding` metadata (keywords, inferred category, **correction** when present)
- `/api/query-understand` returns full debug output (embedding shape, norm, pipeline fields)
- **`/api/autocomplete`** → suggestions derived from **titles** and **categories**
- **`/api/products/{id}/similar`** → **8** similar products by embedding cosine similarity

### 7. Topic Engagement — **6/6**

Deep engagement with NLP before LLMs and classic IR/ML adjacent techniques.

- **Text preprocessing:** NLTK tokenization with stopword removal — the foundational step in any NLP pipeline. N-grams (bigrams) capture multi-word concepts like `bluetooth_headphones`.
- **TF-IDF:** Fitted on the product corpus; discriminative terms for queries and classifier features. `sublinear_tf=True` limits raw frequency dominance.
- **Word2Vec (skip-gram):** Gensim skip-gram on catalog text; average-of-word-vectors for fixed-size query/product embeddings — the pre-transformer workhorse for semantic similarity.
- **Cosine similarity:** Standard metric for comparing embeddings; drives candidate re-ranking and **similar products** (`/similar`).
- **Logistic Regression:** Multinomial classification over TF-IDF features for category prediction with calibrated confidence.
- **Edit distance (Levenshtein):** Classical string metric for **spell correction** against a **closed vocabulary** from the same embedding model — tying lexicon and semantics together.
- **Caching:** Practical systems topic — **LRU** cap on `understand()` for repeated queries under load.
- **Substring / lexical retrieval:** **Autocomplete** implements a lightweight inverted-style UX over **titles** and **categories** without LLMs.
- **End-to-end pipeline:** Raw text → tokens → keywords + embedding + category + optional correction — complete feature extraction feeding search, ranking, and discovery UI.

### 8. GitHub Practices — **4/4**

Excellent practices. Clear commit messages, disciplined branching/file ownership, logical progression including follow-up enhancement commits.

- **Meaningful commit messages** for Module 3 landing and subsequent feature commits (spell correction, cache, API routes, frontend SearchBar and UX)
- **Low-conflict workflow:** File-level ownership and agreed interfaces reduced parallel-edit collisions
- **Skeleton-first approach** (earlier checkpoint): interface stubs enabled parallel implementation
- **Repository structure** matches the spec: `src/module3/`, `unit_tests/module3/`, `integration_tests/module3/`
- **Both team members’ commits** visible across initial Module 3 work and enhancements
- **Dependencies** remain explicit in `requirements.txt` (e.g., `nltk`, `gensim`, `numpy`) for reproducible NLP stack

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
