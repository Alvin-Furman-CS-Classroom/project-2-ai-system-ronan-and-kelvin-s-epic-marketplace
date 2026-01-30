# Epic Marketplace

## System Overview

Epic Marketplace is a small business marketplace search system that helps shoppers find the right product using search, NLP, and supervised learning. Users provide a free-text query plus structured filters (price range, category, seller rating, and location). The system first retrieves candidates with classic search, then applies heuristic re-ranking from advanced search techniques. It parses the query with NLP to extract keywords and embeddings that enrich product features. A learning-to-rank model trains on click or rating signals to produce final scores, and the system outputs a top-k ranked list with those scores. This theme is a natural fit for AI concepts because it combines constraint-based retrieval, query understanding, and data-driven ranking in a single, end-to-end workflow.

## Modules

### Module 1: Candidate Retrieval (Search)

**Topics:** Uninformed and informed search (BFS/DFS, Uniform Cost, A*)

**Input:** `filters` (price range, category, seller rating, location), product catalog  
Example: `filters={"price":[10,40],"category":"home","seller_rating":">=4.5","location":"Boston"}`

**Output:** `candidate_ids` (products satisfying hard constraints)  
Example: `candidate_ids=["p12","p89","p203"]`

**Integration:** Provides the initial candidate set for heuristic re-ranking and learning-to-rank.

**Prerequisites:** Search unit (uninformed/informed search).

**Success criterion:** At least 95% of catalog items that meet the filters are returned in `candidate_ids`.

---

### Module 2: Heuristic Re-ranking (Advanced Search)

**Topics:** Advanced search (optimization, hill climbing, simulated annealing)

**Input:** `candidate_ids`, product features (price, rating, distance, shipping time), query features (from Module 3)  
Example: `features={"p12":{"rating":4.8,"distance_miles":3.2,"price":18.0}}`

**Output:** `ranked_candidates` with heuristic scores (e.g., `[(id, score), ...]`)  
Example: `ranked_candidates=[("p89",0.73),("p12",0.70)]`

**Integration:** Produces a strong initial ranking that the learning-to-rank model can refine. Uses query features once Module 3 is completed; earlier checkpoints rely on catalog features only.

**Prerequisites:** Advanced search unit.

**Success criterion:** Heuristic ranking improves Precision@k over the unranked candidate set.

---

### Module 3: Query Understanding (NLP)

**Topics:** NLP before LLMs (n-grams, word embeddings)

**Input:** `query_text` (free-text user query)  
Example: `"handmade ceramic mug"`

**Output:** `keywords`, `query_embedding`, inferred category (if missing)  
Example: `keywords=["handmade","ceramic","mug"], inferred_category="home/kitchen"`

**Integration:** Adds query features used by the learning-to-rank model.

**Prerequisites:** NLP unit.

**Success criterion:** Extracted keywords match human-labeled keywords for at least 80% of test queries.

---

### Module 4: Learning-to-Rank (Supervised Learning)

**Topics:** Supervised learning (linear/logistic regression, evaluation basics)

**Input:** `ranked_candidates`, product features, query features, training data (clicks or ratings)  
Example: `training_label={"p89":1,"p12":0}`

**Output:** `final_scores` for each candidate  
Example: `final_scores=[("p89",0.86),("p12",0.81)]`

**Integration:** Produces the final scoring function used for the top-k results.

**Prerequisites:** Supervised learning unit.

**Success criterion:** Learning-to-rank improves NDCG@k over heuristic ranking on a held-out set.

---

### Module 5: Evaluation & Final Output

**Topics:** Evaluation metrics for supervised learning

**Input:** `final_scores`, held-out interaction data

**Output:** `top_k_results` with scores (user-facing payload), plus metrics (Precision@k, NDCG@k)  
Example: `top_k_results=[{"id":"p89","score":0.86,"price":22.0,"title":"Ceramic Mug"}]`

**Integration:** Final user-facing result and evidence the ranking is effective. Assembles the top-k payload in a fixed JSON schema and reports evaluation metrics for the checkpoint submission.

**Prerequisites:** Supervised learning evaluation metrics.

**Success criterion:** Metrics are reported in a reproducible table and meet or exceed the Module 4 baseline.

---

## Feasibility Study

_A timeline showing that each module's prerequisites align with the course schedule. Verify that you are not planning to implement content before it is taught._

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due |
| ------ | ----------------- | ---------------- | -------------- |
| 1      | Uninformed/Informed Search | Search unit (Weeks 1.5-3) | Checkpoint 1 — Feb 11 |
| 2      | Advanced Search | Advanced Search unit (Week 4) | Checkpoint 2 — Feb 26 |
| 3      | NLP before LLMs | NLP unit (Weeks 5.5-7) | Checkpoint 3 — Mar 19 |
| 4      | Supervised Learning | Intro SL/RL unit (Weeks 7-8.5) | Checkpoint 4 — Apr 2 |
| 5      | Evaluation Metrics | SL + evaluation metrics (Remaining weeks) | Checkpoint 5 — Apr 16 |

All modules are scheduled after their prerequisite topics are taught, and each checkpoint aligns with the course schedule dates listed for Project 2 (Feb 11, Feb 26, Mar 19, Apr 2, Apr 16).

## Coverage Rationale

Search is central to product discovery in a marketplace, so it anchors the system with candidate retrieval and heuristic re-ranking. NLP is needed to interpret free-text queries and map them to product features, and supervised learning enables data-driven ranking based on user interactions. This combination covers both symbolic and statistical approaches while staying focused on the single goal of “find the right product.”
