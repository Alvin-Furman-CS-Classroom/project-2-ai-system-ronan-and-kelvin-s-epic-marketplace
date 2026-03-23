# Checkpoint 3 — Code Elegance Report

**Module:** Module 3 — Query Understanding (NLP before LLMs)  
**Date:** March 19, 2026  
**Reviewed files:** `src/module3/tokenizer.py`, `src/module3/keywords.py`, `src/module3/embeddings.py`, `src/module3/category_inference.py`, `src/module3/query_understanding.py`, `src/module3/spell_correction.py`, `src/module3/exceptions.py`, `src/module3/__init__.py`

---

## Summary

Module 3 continues the high code quality established in Modules 1–2. The NLP pipeline is organized across eight source files with clear boundaries: text preprocessing and n-grams, TF-IDF keywords, Word2Vec/GloVe embeddings with cosine ranking, TF-IDF + logistic category classification, Levenshtein spell correction against the embedding vocabulary, and a thin orchestrator with LRU caching. Public APIs stay predictable—pure helpers where appropriate, stateful components with focused methods elsewhere, and `QueryUnderstanding` composing them without duplicating their logic. Named constants, type hints, docstrings, and Pythonic patterns remain consistent; new work (spell correction, `vocabulary` on the embedder, cache and `corrected_query` on results) fits the existing style rather than introducing a second dialect.

---

## Findings

### 1. Naming Conventions — **4/4**

Names are descriptive, consistent, and follow PEP 8 throughout:

- **Classes:** `KeywordExtractor`, `ProductEmbedder`, `CategoryClassifier`, `SpellCorrector`, `QueryUnderstanding`, `QueryResult` — clear, intention-revealing nouns.
- **Functions:** `tokenize()`, `extract_ngrams()`, `_levenshtein()`, `_cosine_similarity()`, `_average_embedding()` — action-oriented verbs and well-scoped private helpers.
- **Constants:** `EMBEDDING_DIM`, `W2V_*`, `MAX_FEATURES`, `MAX_DF`, `MIN_DF`, `MIN_TOKEN_LENGTH`, `GLOVE_DIR`, `GLOVE_FILENAME`, `MAX_EDIT_DISTANCE`, `MIN_WORD_LENGTH`, `QUERY_CACHE_SIZE` — uppercase with unambiguous meaning.
- **Variables:** `corpus_texts`, `token_scores`, `ranked_pairs`, `active_vectors`, `tokenized_corpus`, `_vocab_by_length`, `cache_key` — readable and specific.
- **Parameters:** `top_k`, `use_glove`, `glove_path`, `vocabulary` — self-documenting.
- No single-letter variables outside tight loops. No misleading names.

### 2. Function and Method Design — **4/4**

Functions are concise, focused, and each does one thing well:

- **`tokenize()`** remains a pure function: text in, tokens out, with regex cleanup, NLTK tokenization, and stopword filtering.
- **`extract_ngrams()`** is a short pure function producing underscore-joined n-grams.
- **`KeywordExtractor.extract()`** follows tokenize → transform → score → rank → truncate without sprawl.
- **`_levenshtein()`** is a compact dynamic-programming implementation (~15 lines), space-optimized to a single row of length \(O(m)\).
- **`SpellCorrector.correct_token()`** encapsulates OOV detection, length-pruned candidate search, and distance minimization; returns `(corrected, was_corrected)` so callers get an explicit boolean.
- **`SpellCorrector.correct_query()`** is a straight pipeline: tokenize → correct each token → rejoin; empty or whitespace queries short-circuit cleanly.
- **`_cosine_similarity()`** and **`_average_embedding()`** stay small helpers with clear contracts.
- **`ProductEmbedder`** methods (`embed_query`, `embed_text`, `similarity`, `rank_by_similarity`) compose internals in two to a handful of lines each.
- **`CategoryClassifier.predict()`** keeps the empty-check → transform → predict → confidence path linear.
- **`QueryUnderstanding.understand()`** orders work as cache lookup → spell suggestion → keywords → embedding → optional classification → `QueryResult`, plus cache eviction—still readable end-to-end.
- No function grows into a “god method.”

### 3. Abstraction and Modularity — **4/4**

Abstraction is well-judged:

- **Clear file boundaries:** tokenizer (preprocessing, stopwords, n-grams), keywords (TF-IDF), embeddings (Word2Vec/GloVe, similarity), category_inference (classifier), spell_correction (dictionary + edit distance), query_understanding (orchestration + cache), exceptions (types), `__init__.py` (exports).
- **Components are independently testable:** Each major type can be constructed and exercised on its own; unit tests mirror that separation.
- **Orchestrator stays thin:** It wires `KeywordExtractor`, `ProductEmbedder`, `CategoryClassifier`, and `SpellCorrector`; `understand()` delegates behavior instead of reimplementing token or vector logic.
- **Spell correction is decoupled:** `SpellCorrector` depends on a vocabulary list and shared `tokenize()`, not on the full embedder API—yet the orchestrator naturally supplies `ProductEmbedder.vocabulary` so the “dictionary” matches the active vectors.
- **Interface contract:** Documented expectations for `tokenize`, `KeywordExtractor`, and `ProductEmbedder` remain aligned with how the orchestrator calls them.
- **Exception hierarchy:** `QueryUnderstandingError` extends `EpicMarketplaceError`; specialized types remain available for embedding and category failures.
- **`__init__.py`** exports a minimal public surface via `__all__`, now including `SpellCorrector`.
- Optional GloVe loading stays isolated in `_load_glove()` without complicating the rest of the embedder.

### 4. Style Consistency — **4/4**

Code style matches across files and with earlier modules:

- PEP 8: 4-space indentation, `snake_case`, PascalCase for classes.
- Google-style docstrings with Args, Returns, and examples where they add value.
- Import order: stdlib → third-party → local; `OrderedDict` alongside other stdlib imports in the orchestrator.
- Uniform spacing between methods; module docstrings at file top.
- Section dividers (`# ---` / `# -----`) group related blocks the same way as Modules 1–2.
- Type hints follow project habits: `List`, `Tuple`, `Optional`, `Dict`, `np.ndarray`.
- Multi-line calls use trailing commas consistently.

### 5. Code Hygiene — **4/4**

The codebase stays clean:

- **No dead code** in reviewed paths—each import and member supports the pipeline or tests.
- **DRY:** `tokenize()` is shared by keywords, embeddings, and spell correction; `_cosine_similarity()` centralizes similarity math; vocabulary is obtained once from the embedder for the corrector.
- **Named constants:** Embedding hyperparameters, TF-IDF bounds, `MAX_EDIT_DISTANCE`, `MIN_WORD_LENGTH`, and `QUERY_CACHE_SIZE` avoid magic numbers.
- **TF-IDF small-corpus fallback** in `KeywordExtractor` remains a focused retry rather than scattered conditionals.
- **SpellCorrector index:** `_vocab_by_length` is built once at construction—no repeated full-vocab scans for every token length.
- **No stray commented-out blocks**, no unused imports in the reviewed module set.
- **Logging:** `logger.info` / `logger.warning` / `logger.debug` for training, missing GloVe, corrector build, and cache hits—consistent with the rest of the project.

### 6. Control Flow Clarity — **4/4**

Control flow reads linearly:

- **Early returns** in `tokenize()`, keyword `extract()`, classifier `predict()`, `rank_by_similarity` inputs, and `correct_query()` for empty input.
- **`_average_embedding()`** returns a zero vector when nothing is in vocabulary—no exceptions for the common empty case.
- **GloVe path:** try load → `None` + warning → Word2Vec as active vectors; shallow branching.
- **`understand()`:** cache hit updates LRU order and returns; miss runs spell correction then the rest, stores result, evicts oldest when over capacity.
- **`correct_token()`:** in-vocab and short-token guards exit immediately; candidate loops only over lengths in `[len(token) ± MAX_EDIT_DISTANCE]`.
- Nesting stays shallow; no switch-style maze for the main pipeline.

### 7. Pythonic Idioms — **4/4**

The code uses Python’s strengths naturally:

- **`@dataclass`** for `QueryResult`, including optional `corrected_query` for “Did you mean?” style UIs.
- **`OrderedDict`** LRU: `move_to_end` on hit, `popitem(last=False)` on overflow—standard pattern for bounded caches.
- **Cache key** `query.strip().lower()` gives case-insensitive deduplication without normalizing stored display text.
- **List comprehensions** for corpora, scored pairs, and vector gathering where they improve clarity.
- **`np.mean` / `np.linalg.norm`** for aggregation and cosine safety.
- **Properties:** `ProductEmbedder.vocabulary`, `vocabulary_size`, `using_glove`; `SpellCorrector.vocabulary_size`—computed state exposed read-only.
- **`setdefault`** when grouping vocabulary by length in `SpellCorrector.__init__`.
- **Module-level `_STOPWORDS`** (or equivalent) for O(1) membership checks in tokenization.
- **scikit-learn** `TfidfVectorizer` / `LogisticRegression`, **gensim** `Word2Vec` / `KeyedVectors`, **NLTK** `word_tokenize`—idiomatic stack choices.

### 8. Error Handling — **4/4**

Failures and edge cases are handled deliberately:

- **Custom hierarchy:** `QueryUnderstandingError` → `EpicMarketplaceError`; `CategoryInferenceError` and `EmbeddingError` for narrower failures.
- **`CategoryClassifier.__init__`** validates corpus/label alignment and non-empty training data with clear `ValueError` messages.
- **TF-IDF init:** catches sklearn `ValueError` when document frequency pruning is too aggressive and retries with relaxed `min_df` / `max_df`.
- **Missing GloVe:** `_load_glove()` returns `None` and logs—training and query paths keep working on Word2Vec.
- **`_cosine_similarity()`** guards zero norms—no divide-by-zero.
- **Empty queries:** classifier and keyword paths behave predictably; spell correction returns the original string and `None` suggestion when there is nothing to fix.
- **No bare `except:`** and no swallowed exceptions in the reviewed code.

---

## Scores

| Criterion | Score | Max |
|-----------|-------|-----|
| 1. Naming Conventions | 4 | 4 |
| 2. Function & Method Design | 4 | 4 |
| 3. Abstraction & Modularity | 4 | 4 |
| 4. Style Consistency | 4 | 4 |
| 5. Code Hygiene | 4 | 4 |
| 6. Control Flow Clarity | 4 | 4 |
| 7. Pythonic Idioms | 4 | 4 |
| 8. Error Handling | 4 | 4 |
| **Average** | **4.0** | **4.0** |

**Overall Code Elegance Score: 4** (Average 4.0 → score 4 per rubric: 3.5–4.0 → 4)
