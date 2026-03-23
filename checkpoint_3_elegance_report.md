# Checkpoint 3 — Code Elegance Report

**Module:** Module 3 — Query Understanding (NLP before LLMs)  
**Date:** March 19, 2026  
**Reviewed files:** `src/module3/tokenizer.py`, `src/module3/keywords.py`, `src/module3/embeddings.py`, `src/module3/category_inference.py`, `src/module3/query_understanding.py`, `src/module3/exceptions.py`, `src/module3/__init__.py`

---

## Summary

Module 3 continues the high code quality established in Modules 1–2. The NLP pipeline is cleanly organized across six source files, each with a single responsibility. Public APIs follow the interface contract agreed between team members, with pure functions where possible (tokenizer), stateful-but-immutable classes elsewhere (KeywordExtractor, ProductEmbedder, CategoryClassifier), and a thin orchestrator (QueryUnderstanding) that composes them. Named constants, type hints, docstrings, and Pythonic idioms are consistent throughout.

---

## Findings

### 1. Naming Conventions — **4/4**

Names are descriptive, consistent, and follow PEP 8 throughout:

- **Classes:** `KeywordExtractor`, `ProductEmbedder`, `CategoryClassifier`, `QueryUnderstanding`, `QueryResult` — clear, intention-revealing nouns.
- **Functions:** `tokenize()`, `extract_ngrams()`, `_cosine_similarity()`, `_average_embedding()` — action-oriented verbs/nouns.
- **Constants:** `EMBEDDING_DIM`, `W2V_WINDOW`, `W2V_MIN_COUNT`, `W2V_EPOCHS`, `W2V_WORKERS`, `W2V_SG`, `MAX_FEATURES`, `MAX_DF`, `MIN_DF`, `MIN_TOKEN_LENGTH`, `GLOVE_DIR`, `GLOVE_FILENAME` — uppercase with clear meaning.
- **Variables:** `corpus_texts`, `token_scores`, `ranked_pairs`, `active_vectors`, `tokenized_corpus` — no ambiguity.
- **Parameters:** `top_k`, `use_glove`, `glove_path`, `corpus_texts`, `labels` — self-documenting.
- No single-letter variables outside tight comprehensions. No misleading names.

### 2. Function and Method Design — **4/4**

Functions are concise, focused, and each does one thing well:

- **`tokenize()`** is a pure function: text in, tokens out. ~15 lines including regex cleanup, NLTK tokenization, and stopword filtering.
- **`extract_ngrams()`** is a 3-line pure function generating underscore-joined n-grams.
- **`KeywordExtractor.extract()`** is ~15 lines: tokenize → transform → score → rank → truncate.
- **`_cosine_similarity()`** is a standalone 5-line utility with zero-norm safety.
- **`_average_embedding()`** is a 6-line method: filter in-vocab tokens → stack vectors → mean.
- **`ProductEmbedder.embed_query/embed_text/similarity/rank_by_similarity`** form a clean public API, each 2–5 lines, composing the internal helpers.
- **`CategoryClassifier.predict()`** is 8 lines: empty check → transform → predict → extract confidence.
- **`QueryUnderstanding.understand()`** is 10 lines: extract keywords → embed → classify → wrap in QueryResult.
- No function exceeds reasonable length. No god methods.

### 3. Abstraction and Modularity — **4/4**

Abstraction is well-judged:

- **Clear file boundaries:** tokenizer (text preprocessing), keywords (TF-IDF), embeddings (Word2Vec/GloVe), category_inference (classification), query_understanding (orchestration), exceptions (error types).
- **Components are independently testable:** Each can be instantiated and tested without the others. Unit tests do exactly this.
- **Orchestrator is thin:** `QueryUnderstanding.__init__` creates the three components; `understand()` calls each one and wraps results. No business logic duplicated.
- **Interface contract honored:** Kelvin's `tokenize()`, `KeywordExtractor`, `ProductEmbedder` exactly match the signatures Ronan's code imports and calls.
- **Exception hierarchy extends Module 1:** `QueryUnderstandingError` → `EpicMarketplaceError`.
- **`__init__.py`** exports only the public API via `__all__`.
- No over-engineering. The optional GloVe support is cleanly isolated in `_load_glove()`.

### 4. Style Consistency — **4/4**

Code style is consistent across all files and with Modules 1–2:

- PEP 8 followed throughout: 4-space indentation, snake_case, PascalCase for classes.
- Consistent Google-style docstrings with Args, Returns, and Example sections.
- Import ordering: stdlib → third-party (numpy, gensim, sklearn, nltk) → local.
- Blank line spacing between methods is uniform.
- All files start with module-level docstrings explaining purpose and owner.
- Section dividers (`# ---`) separate logical groups (same pattern as Modules 1–2).
- Type hints match project conventions: `List[str]`, `List[Tuple[str, float]]`, `Optional[str]`, `np.ndarray`.
- Trailing commas in multi-line calls.

### 5. Code Hygiene — **4/4**

The codebase is clean:

- **No dead code** — every function, class, and import is used.
- **No duplication** — `tokenize()` is called by both `KeywordExtractor` and `ProductEmbedder` (DRY). `_cosine_similarity()` is shared across all similarity computations.
- **Named constants throughout:** All hyperparameters (`EMBEDDING_DIM`, `W2V_WINDOW`, `MAX_FEATURES`, `MIN_DF`, etc.) are named constants, not magic numbers.
- **TF-IDF fallback** for small corpora is cleanly handled with a try/except that relaxes df constraints.
- **No leftover imports**, no unused variables, no commented-out blocks.
- **Logging:** Uses `logger.info()` for training progress and `logger.warning()` for missing GloVe — consistent with Modules 1–2.

### 6. Control Flow Clarity — **4/4**

Control flow is clear and linear:

- **Early returns** in `tokenize()` (empty/whitespace text), `extract()` (empty tokens), `predict()` (empty query), `search_by_text()` (empty texts).
- **`_average_embedding()`** returns zero vector if no in-vocab tokens — no exception, clean fallback.
- **GloVe loading** uses `Optional` pattern: try to load → return None on failure → fallback to Word2Vec. No deeply nested conditionals.
- **`understand()`** is a straight-line pipeline: extract keywords → embed → classify → wrap. Only one conditional (skip classification for empty queries).
- **Nesting** never exceeds 2 levels.
- **No complex branching.** Strategy dispatch is not needed here — the pipeline is linear.

### 7. Pythonic Idioms — **4/4**

Code leverages Python idioms effectively:

- **Dataclass** for `QueryResult` with optional fields and defaults.
- **List comprehensions** for tokenized corpus, vector collection, scored pairs.
- **`np.mean(vectors, axis=0)`** for average embedding — idiomatic numpy.
- **`np.linalg.norm()`** for vector norms.
- **Properties** (`.vocabulary_size`, `.using_glove`) for computed attributes.
- **Module-level `_STOPWORDS = set(...)`** for O(1) lookup — frozenset-like pattern.
- **`re.sub()`** for regex-based text cleaning.
- **`word_tokenize()`** from NLTK — using the standard library for tokenization.
- **`TfidfVectorizer`** and `LogisticRegression` from scikit-learn — standard ML toolkit.
- **`KeyedVectors`** from Gensim for embedding access.
- **`Dict[str, int]`** type annotation for vocabulary mapping.

### 8. Error Handling — **4/4**

Errors are handled thoughtfully:

- **`QueryUnderstandingError`** inherits from `EpicMarketplaceError` — consistent hierarchy.
- **`CategoryInferenceError`** and `EmbeddingError`** available for specific failure modes.
- **`CategoryClassifier.__init__`** validates inputs: mismatched corpus/labels raises `ValueError` with descriptive message; empty corpus raises `ValueError`.
- **TF-IDF fallback:** `KeywordExtractor.__init__` catches `ValueError` from sklearn when df pruning removes all terms, and retries with relaxed settings.
- **GloVe not found:** `_load_glove()` returns `None` with a warning — no crash, clean fallback.
- **Zero-vector safety:** `_cosine_similarity()` returns 0.0 for zero-norm vectors — no division by zero.
- **Empty query handling:** `predict()` returns (first_label, 0.0); `understand()` returns empty keywords and zero embedding.
- **No bare `except:` clauses.** No silenced errors.

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
