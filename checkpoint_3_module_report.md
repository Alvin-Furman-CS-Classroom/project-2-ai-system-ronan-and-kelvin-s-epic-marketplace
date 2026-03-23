# Checkpoint 3 — Module Rubric Report

**Module:** Module 3 — Query Understanding (NLP before LLMs)  
**Date:** March 19, 2026  
**Team:** Kelvin Bonsu & Ronan  
**Total Tests:** 397 passing (0 failures)

---

## Summary

Module 3 adds a query understanding layer to the Epic Marketplace pipeline. It transforms free-text search queries (e.g., "bluetooth headphones for running") into structured signals — TF-IDF keywords, Word2Vec embeddings, and a Logistic Regression category prediction — using pre-LLM NLP techniques. The module is wired into the `/api/search` endpoint so the search bar actually works: typing a query now infers the product category, re-ranks candidates by embedding cosine similarity, and displays keyword chips and inferred category in the frontend. All 397 tests pass across Modules 1–3.

---

## Findings

### 1. Functionality — **8/8**

All features work correctly. Handles edge cases gracefully. No crashes or unexpected behavior.

- **Tokenizer:** Lowercasing, punctuation removal, NLTK tokenization, stopword filtering, minimum token length, n-gram extraction (bigrams/trigrams). Handles empty strings, whitespace-only, punctuation-only, unicode, and single-word queries.
- **TF-IDF keyword extraction:** Vectorizer fitted on product corpus with configurable `max_df`, `min_df`, `max_features`, and `sublinear_tf`. Returns ranked (keyword, score) tuples. Gracefully handles tiny/homogeneous corpora by relaxing df thresholds. Deduplicates repeated tokens. OOV tokens appear with score 0.
- **Word2Vec embeddings:** Skip-gram model trained on product corpus (100-d, window=5, min_count=2, 10 epochs). Average-of-word-vectors for query/product embeddings. Optional GloVe loader with automatic fallback to Word2Vec if file not found.
- **Cosine similarity:** Safe against zero-norm vectors (returns 0.0). `rank_by_similarity` produces descending-sorted (id, score) lists.
- **Category inference:** TF-IDF + Logistic Regression classifier trained on product text → category labels. Returns (category, confidence) with confidence in [0, 1]. Empty/whitespace queries return first label with 0 confidence. Input validation: mismatched corpus/label lengths and empty corpus raise `ValueError`.
- **Orchestrator:** `QueryUnderstanding` wires all components. `understand(query)` returns `QueryResult` with keywords, embedding, inferred category, confidence. `search_by_text(query, texts)` ranks items by embedding similarity.
- **API integration:** `/api/search?q=` uses Module 3 to auto-infer category (threshold ≥ 40%), re-rank candidates by cosine similarity, and return `query_understanding` metadata. `/api/query-understand?q=` debug endpoint returns full pipeline output including embedding shape and norm.
- **Frontend:** Search results page shows purple "inferred category" chip with confidence percentage, and blue keyword chips with TF-IDF scores.
- **Edge cases handled:**
  - Empty query → empty keywords, zero embedding, no category
  - OOV words → zero embedding vector
  - Stopwords-only query → empty keywords
  - Tiny corpus → relaxed TF-IDF thresholds
  - GloVe file missing → automatic Word2Vec fallback
  - No explicit category filter → auto-infer from query

### 2. Code Elegance and Quality — **8/8**

Exemplary code quality. Clear structure, excellent naming, appropriate abstraction. See `checkpoint_3_elegance_report.md` for detailed 8-criteria assessment (average: 4.0/4.0).

Key strengths:
- Clean separation across 6 source files (`tokenizer.py`, `keywords.py`, `embeddings.py`, `category_inference.py`, `query_understanding.py`, `exceptions.py`) — each with a single responsibility
- Tokenizer is a pure function; KeywordExtractor and ProductEmbedder are stateful but immutable after init
- Named constants: `EMBEDDING_DIM`, `W2V_WINDOW`, `W2V_MIN_COUNT`, `W2V_EPOCHS`, `MAX_FEATURES`, `MAX_DF`, `MIN_DF`, `MIN_TOKEN_LENGTH`
- Consistent Google-style docstrings, PEP 8 naming, type hints throughout
- Interface contract between Kelvin's and Ronan's files: `tokenize()`, `KeywordExtractor.extract()`, `ProductEmbedder.embed_query()`
- Exception hierarchy extends Module 1's `EpicMarketplaceError`

### 3. Testing — **8/8**

Comprehensive test coverage. Tests are well-designed, test meaningful behavior, and all pass.

**Unit Tests (70 Module 3 tests):**

| Test File | Count | Focus |
|-----------|-------|-------|
| `test_tokenizer.py` | 19 | Tokenization, stopwords, n-grams, punctuation, unicode, edge cases |
| `test_keywords.py` | 12 | TF-IDF extraction, ranking, OOV, deduplication, small corpus |
| `test_embeddings.py` | 22 | Embedding shape/dtype, cosine similarity, ranking order, zero vectors |
| `test_category_inference.py` | 9 | Training, prediction validity, confidence range, accuracy, validation |
| `test_query_understanding.py` | 8 | End-to-end pipeline, QueryResult fields, search_by_text |

**Integration Tests (4 Module 3 tests):**

| Test | What Is Tested |
|------|----------------|
| Full pipeline | query → understand() → valid QueryResult with keywords, embedding, category |
| Category labels | Inferred category is from the training label set |
| Text relevance | search_by_text ranks "bluetooth headphones" text above "running shoes" |
| Module 3 → Module 2 | Inferred category feeds into HeuristicRanker as target_category |

**Modules 1–2 tests (323) all still pass** — no regressions introduced.

**Test quality:**
- All 397 tests pass with zero failures
- Shared fixtures in `conftest.py` provide reusable corpus, extractor, embedder, classifier
- Embedding tests verify shape, dtype, and relative ordering (not exact values)
- Integration tests verify the cross-module pipeline: Module 3 → Module 1 → Module 2

### 4. Individual Participation — **6/6**

All team members show substantial, balanced contributions with zero file overlap.

- **Kelvin's work:** Tokenizer (preprocessing, stopwords, n-grams), TF-IDF keyword extraction, Word2Vec embeddings with cosine similarity, `__init__.py` exports, all NLP core unit tests (53 tests), conftest fixtures.
- **Ronan's work:** Category inference (TF-IDF + Logistic Regression), QueryUnderstanding orchestrator, exception hierarchy, category inference tests, orchestrator tests, integration tests (Module 3 → Module 2 pipeline), integration conftest.
- Task division ensured zero merge conflicts — Kelvin's NLP core and Ronan's integration layer had clear interface contracts agreed before coding.
- Both members engaged with core NLP/ML work: Kelvin on embeddings and TF-IDF, Ronan on classification and end-to-end wiring.

### 5. Documentation — **5/5**

Excellent documentation across all files.

- **Every public class and function has a docstring** with Args, Returns, and Example sections
- **Type hints used consistently:** `List[str]`, `List[Tuple[str, float]]`, `np.ndarray`, `Optional[str]`, `Dict[str, str]`
- **Module-level docstrings** on every file explain purpose, approach, and owner
- **Interface contract** documented in the plan: `tokenize()`, `KeywordExtractor.extract()`, `ProductEmbedder.embed_query/similarity/rank_by_similarity`
- **README.md** updated with Module 3 spec, running example, Checkpoint 3 reflection, and updated test counts
- **`__init__.py`** exports clean public API via `__all__`

### 6. I/O Clarity — **5/5**

Inputs and outputs are crystal clear and well-typed.

**Inputs:**
- `tokenize(text: str)` → raw text
- `KeywordExtractor(corpus_texts: List[str])` → product text corpus
- `ProductEmbedder(corpus_texts: List[str])` → product text corpus
- `CategoryClassifier(corpus_texts: List[str], labels: List[str])` → text + labels
- `QueryUnderstanding(corpus_texts, labels)` → unified init
- `/api/search?q=bluetooth+headphones` → free-text query via URL param

**Outputs:**
- `tokenize()` → `List[str]` (cleaned tokens)
- `KeywordExtractor.extract()` → `List[Tuple[str, float]]` (ranked keywords)
- `ProductEmbedder.embed_query()` → `np.ndarray` shape (100,)
- `CategoryClassifier.predict()` → `Tuple[str, float]` (category, confidence)
- `QueryResult` dataclass → keywords, query_embedding, inferred_category, confidence
- `/api/search` response includes `query_understanding` metadata with keywords and inferred category
- `/api/query-understand` returns full debug output including embedding shape and norm

### 7. Topic Engagement — **6/6**

Deep engagement with NLP before LLMs. All core techniques implemented from scratch.

- **Text preprocessing:** NLTK tokenization with stopword removal — the foundational step in any NLP pipeline. N-gram extraction (bigrams) captures multi-word concepts like "bluetooth_headphones".
- **TF-IDF:** Term Frequency–Inverse Document Frequency fitted on the product corpus. Captures how discriminative a query term is across the product catalog. `sublinear_tf=True` applies logarithmic TF scaling to prevent common terms from dominating.
- **Word2Vec (skip-gram):** Custom-trained on product text using Gensim. Skip-gram architecture learns word co-occurrence patterns in the domain. Average-of-word-vectors produces fixed-size query/product embeddings — the same approach used before transformer models.
- **Cosine similarity:** The standard metric for comparing embedding vectors. Used to rank products by semantic relevance to the query, not just keyword overlap.
- **Logistic Regression classifier:** TF-IDF features fed into a multinomial classifier to predict product category from query text. Returns calibrated probabilities as confidence scores.
- **GloVe support:** Optional pre-trained embeddings (transfer learning) with automatic fallback — demonstrates the tradeoff between domain-specific training and general pre-trained representations.
- **End-to-end pipeline:** Raw text → tokens → keywords + embedding + category — a complete NLP feature extraction pipeline feeding into downstream search and ranking modules.

### 8. GitHub Practices — **4/4**

Excellent practices. Clear commit messages, no merge conflicts, logical progression.

- **Meaningful commit messages:** `"feat: add Module 3 NLP core pipeline and skeleton files"`, `"module 3 changes"` (Ronan's implementation)
- **Zero-conflict workflow:** Task division by file ownership ensured parallel development with no merge conflicts
- **Skeleton-first approach:** Kelvin created skeleton files with interface contracts for Ronan's files before implementing, enabling parallel work
- **Repository structure** follows specification: `src/module3/`, `unit_tests/module3/`, `integration_tests/module3/`
- **Both team members' commits visible** in the history
- **Dependencies updated:** `requirements.txt` uncommented and versioned for nltk, gensim, numpy

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
