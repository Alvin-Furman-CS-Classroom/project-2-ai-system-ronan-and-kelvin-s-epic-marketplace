# Module 4 — Quality / Value Ranker: Specification Fit Report

This document summarizes how the implemented **classification-based ranker** (`QualityValueRanker` + `LearningToRankPipeline`) aligns with your stated goals and where to iterate next.

## What you asked for

1. **Classification** to prioritize **reviews** (volume), **description** (depth), and **rating** (seller rating + review count as social proof).
2. Rankings that favor **high-quality listings** while respecting the user’s **price range**.
3. A **balance of price vs. performance** (value), not only “cheapest” or only “highest rated.”

## What the implementation does

### Features (`compute_quality_value_features`)

| Signal | Source | Role |
|--------|--------|------|
| **Rating** | `seller_rating / 5` | Direct quality signal |
| **Reviews** | `log1p(rating_number)`, batch-normalized | Prioritizes products with more review evidence |
| **Description** | Length vs. cap (500 chars) | Listing depth |
| **Feature bullets** | Count vs. cap (10) | Structured product detail |
| **Price in band** | User `price_band` or batch min/max | Position inside the affordable window |
| **Value / perf hints** | Derived from rating × trust × richness, adjusted by price position | Encourages **price–performance** tradeoffs the learner can reweight |

### Model (`QualityValueRanker`)

- **Logistic regression** (binary classifier), `class_weight="balanced"`.
- **Training labels**
  - **Default:** *proxy labels* — median split on a weighted composite of the same features (no click data required).
  - **Optional:** you pass **explicit** `0/1` labels (e.g. from future click/impression logs).
- **Scores:** `predict_proba[:, 1]` → ranking score in **(0, 1)** (endpoints possible in degenerate cases).
- **Fallback:** if `fit` cannot run (e.g. &lt;2 products, single class), **heuristic** scores use the same weight vector as the proxy — still deterministic and quality-oriented.

### Pipeline (`LearningToRankPipeline`)

- `fit` / `fit_rank` with optional `price_band=(min_price, max_price)` aligned with Module 1 filters.
- `rank` → `List[(product_id, score)]` for top-k UI/API.

## How well this meets your specifications

### Strong alignment

- **Rating + reviews + description** are explicit dimensions; the classifier can up-weight them via learned coefficients (`coef_as_dict()` after fit).
- **Price range** is wired via **`price_band`**: features know where a product sits inside the user’s window, so the model can prefer **strong listings that still fit the budget**, not global cheapest.
- **Price–performance:** engineered `value_core` and `perf_per_dollar_hint` give the learner hooks for “good product for the money”; logistic regression combines them with review and text depth.

### Gaps and limitations (iteration list)

1. **Query / search relevance (Module 3)**  
   Current features are **listing-quality and value** on the candidate set. They do **not** yet include query embedding, keywords, or category match. So the model answers “**which of these candidates is the best listing?**” more than “**which matches the query text?**”  
   **Next step:** Concatenate Module 3 features (e.g. cosine similarity to title/description, category match flag) into `compute_quality_value_features` or a second stage.

2. **Proxy labels vs. real outcomes**  
   Default labels are a **median split on hand-weighted quality** — useful for bootstrapping, but **not** the same as clicks or conversions.  
   **Next step:** Log `product_id` + query + implicit feedback; train with real labels.

3. **“Reviews” = `rating_number`**  
   The dataset exposes **review counts**, not full review text sentiment. If you later have review bodies, add NLP features.

4. **Single-class / tiny candidate sets**  
   With 1 product or identical proxy scores, the classifier cannot train; **heuristic fallback** runs. Document this in the API so UX stays stable.

5. **Evaluation (Module 5)**  
   You still need **NDCG@k / Precision@k** vs. Module 2 baseline on held-out queries to prove improvement — not implemented in this module.

## Suggested iteration order

1. Add **Module 3 query features** to the feature vector + retrain.
2. Replace proxy labels with **logged relevance** when available.
3. Run **offline eval** (Module 5) comparing heuristic-only vs. LTR.

## Tests

- `unit_tests/module4/test_features.py`, `test_model.py`, `test_pipeline.py`
- `integration_tests/module4/test_module4_integration.py`

All should pass with: `pytest unit_tests/module4 integration_tests/module4`.
