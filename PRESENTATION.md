# Epic Marketplace — Final Demo Presentation

## Team: Kelvin Bonsu & Ronan

## Presentation Plan (10:00 main + 1:30 Q&A)

---

## SLIDE 1 — Title (0:00–0:15)

**Epic Marketplace: AI-Powered Product Search**

- CSC-343 Spring 2026
- Kelvin Bonsu & Ronan
- 5-module AI search pipeline for electronics

---

## SLIDE 2 — Motivation & Problem (0:15–1:30)

**The Problem:**

- Amazon's Electronics catalog has 18,000+ products
- A shopper types "wireless headphones" — how do you return the *right* 10?
- Naive approach: filter by category, sort by rating. Result: popular items dominate, niche products disappear, relevance to the *query* is ignored.

**Our Goal:**

- Build an end-to-end search system that combines:
  - Classical retrieval (constraints)
  - NLP (understanding what the user *means*)
  - Machine learning (learning what users *prefer*)
  - Rigorous evaluation (measuring if it actually works)

**Who benefits:** Small marketplace vendors — their quality products surface alongside big brands when truly relevant.

**Talking points:**
- "Imagine you search 'charger' and the system shows you a Roku streaming stick because it has 5 stars. That's the problem we're solving."
- "Our system returns actual chargers — even if they have slightly lower ratings — because it understands the *query*, not just the *ratings*."

---

## SLIDE 3 — Solution Architecture (1:30–3:30)

**Show this data-flow diagram:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                    │
│              "wireless headphones" + filters                          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 1: Candidate Retrieval                                       │
│  ─────────────────────────────                                       │
│  Input: SearchFilters (price, category, store, rating)               │
│  AI technique: Informed search (BFS/DFS on category tree)            │
│  Output: ~6,000 candidate product IDs                                │
│  Key idea: Prune impossible subtrees, O(1) category index            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 2: Heuristic Re-ranking                                      │
│  ─────────────────────────────                                       │
│  Input: Candidate IDs + ProductCatalog                               │
│  AI technique: Hill climbing & simulated annealing                   │
│  Output: Ranked (product_id, score) pairs                            │
│  Key idea: 5-signal weighted formula optimised by NDCG@k             │
│  Signals: price, rating, popularity, category match, richness        │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 3: Query Understanding (NLP)                                 │
│  ─────────────────────────────────                                   │
│  Input: Raw query text ("wireless headphones")                       │
│  AI techniques: TF-IDF, Word2Vec, Logistic Regression                │
│  Output: keywords, 100-d embedding, inferred category, confidence    │
│  Key idea: Re-ranks candidates by semantic similarity to the query   │
│  Also: spell correction, autocomplete, category inference            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 4: Learning-to-Rank (Supervised ML)                          │
│  ──────────────────────────────────────────                          │
│  Input: Candidate products + product features + query features       │
│  AI technique: Logistic Regression on 13 features                    │
│  Output: Final relevance scores in (0, 1)                            │
│  Key idea: Learns which combination of quality + relevance signals   │
│            best predicts what users want. 7 product features +       │
│            6 query-product features blended together.                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 5: Evaluation & Output                                       │
│  ─────────────────────────────                                       │
│  Input: Final scores + held-out ground truth                         │
│  Metrics: P@k, Recall@k, F1@k, NDCG@k, MRR, MAP                    │
│  Output: Top-k payload + metric report + ablation comparison         │
│  Key idea: Hybrid ground truth (quality AND topicality) to fairly    │
│            measure whether the system answers the right question.     │
└─────────────────────────────────────────────────────────────────────┘
```

**Talking points:**
- "Each module has clear inputs and outputs — you can test them independently or as a pipeline."
- "The key integration decision: Module 3 feeds features INTO Module 4. The NLP doesn't just filter — it becomes a feature the ML model can weight."
- "We blend Module 3 (semantic relevance) and Module 4 (learned quality) with a 55/45 mix — so the system balances 'is this what you asked for?' with 'is this actually good?'"

---

## SLIDE 4 — AI Techniques Summary (quick reference during architecture)

| Module | AI Technique | Course Topic |
|--------|-------------|--------------|
| 1 | BFS/DFS tree search with pruning | Uninformed/Informed Search |
| 2 | Hill climbing, simulated annealing | Advanced Search / Optimization |
| 3 | TF-IDF, Word2Vec, Logistic Regression | NLP before LLMs |
| 4 | Supervised classification (LR on 13 features) | Supervised Learning |
| 5 | IR evaluation metrics, ablation studies | Evaluation Metrics |

---

## LIVE DEMO (3:30–8:00)

### Demo 1: Search Experience (3:30–5:00)

**Steps:**
1. Open http://localhost:5173
2. Type "wireles" in search bar → show autocomplete suggestions appearing
3. Show "Did you mean: wireless?" spell correction banner
4. Search "wireless headphones" → show results with ratings, prices
5. Click a product → show product detail page with "Customers Also Viewed" (similar products via Word2Vec)

**What this demonstrates:**
- Module 1 (retrieval), Module 2 (ranking), Module 3 (NLP: spell correction, autocomplete, embedding similarity)
- Full integration working end-to-end

**Say:** "This is the user-facing product. But how do we *know* it's good? That's Module 5."

### Demo 2: Evaluation & Ablation (5:00–7:30)

**Steps:**
1. Navigate to /evaluate page
2. Set query: "charger", category: "All Electronics", ground truth: "hybrid"
3. Click "Compare all variants"
4. Point out:
   - **LTR + QU**: P@k = 0.800, On-topic: 10/10 — returns actual chargers
   - **LTR only**: P@k = 0.100, On-topic: 1/10 — returns Roku sticks and flash drives
   - **Heuristic + QU**: P@k = 0.800, On-topic: 10/10 — NLP alone gets you most of the way
   - **Heuristic only**: P@k = 0.100, On-topic: 1/10 — just popular products

**Key talking point:**
- "The ablation proves that Module 3 (Query Understanding) is the single biggest contributor to topical relevance. Without it, the system returns popular but irrelevant items."

### Demo 3: The Limitation / Failure Case (7:30–8:00)

**Steps:**
1. Switch ground truth dropdown to "reviews"
2. Same query "charger" → now:
   - LTR only gets P@k = 1.000 (perfect!)
   - LTR + QU drops to P@k = 0.800

**Say:** "Wait — the dumb pipeline scores *higher*? That's the saturation problem. When 85% of products have a 4-star review, 'has a good review' isn't meaningful as ground truth. This is why we built the hybrid mode — to get honest metrics. This illustrates a real-world lesson: **your evaluation is only as good as your ground truth definition.**"

**This satisfies the rubric requirement: "Must include at least one limitation or failure case."**

---

## SLIDE 5 — Technical Evidence (can show during demo)

- **579 passing tests** (unit + integration across all 5 modules)
- **18,255 real products** from Amazon Reviews '23 — Electronics subset
- **Model performance**: LTR Logistic Regression, CV ROC AUC = 0.963
- **Ablation results** (from batch evaluation):

| Variant | P@10 (hybrid) | On-topic |
|---------|---------------|----------|
| LTR + Query Understanding | 0.800–0.900 | 10/10 |
| LTR only | 0.100–0.300 | 1/10 |
| Heuristic + QU | 0.800–0.900 | 10/10 |
| Heuristic only | 0.100–0.300 | 1/10 |

---

## SLIDE 6 — Conclusions & Reflection (8:00–9:30)

**What we built:**
- A complete 5-module AI search system from retrieval to evaluation
- Each module corresponds to a course topic (search → optimization → NLP → supervised learning → evaluation)
- Live web application demonstrating all modules working together

**What we learned:**
1. **Evaluation design matters as much as the model.** Review-based ground truth saturated our metrics and made bad pipelines look perfect. We had to invent a hybrid metric.
2. **NLP (Module 3) contributes more than ML (Module 4) for topical relevance.** The ablation proves it — turning QU off destroys on-topic rate from 10/10 to 1/10.
3. **Integration is harder than individual modules.** Getting the 55/45 blend right, passing features between modules, and handling edge cases (no candidates, unfitted model) required careful fallback logic.

**Honest limitations:**
- Ground truth is still a proxy (review ratings + keyword matching). Real user click data would be better.
- Word2Vec is trained on 18K products — a larger corpus would improve embedding quality.
- The LTR model uses synthetic training labels, not real user preference data.

**Future work (realistic):**
- Collect real user interaction data to replace synthetic labels
- A/B test Module 4 LTR against the heuristic baseline with real users
- Expand to multiple product categories beyond Electronics

---

## SLIDE 7 — Thank You / Questions (9:30–10:00)

**Epic Marketplace**
- 5 modules • 579 tests • 18,255 products • Live demo
- Kelvin Bonsu & Ronan
- Questions?

---

## Q&A PREPARATION (likely questions + answers)

### "How did you generate training data for Module 4?"

"We used a synthetic training data generator. It runs 20 representative queries through Module 3, pairs each with sampled products, and computes relevance from a 6-signal weighted composite — cosine similarity, category match, keyword overlap, rating, review strength, and a small noise term. We then median-split into binary labels. This isn't as good as real click data, but it lets the model learn a meaningful feature combination. Cross-validation ROC AUC was 0.963."

### "Why Logistic Regression instead of a neural network?"

"We did model selection — tested Logistic Regression, Random Forest, and Gradient Boosting with 5-fold CV. LR won (AUC 0.963 vs 0.952 for RF). For 13 features and 1000 training examples, LR is the right scale. It's also interpretable — we can inspect feature weights to see what the model learned."

### "What's the difference between Module 2 and Module 4?"

"Module 2 uses hand-crafted weights — we chose how much to weight price vs. rating vs. popularity. Module 4 *learns* those weights from data. The key addition is that Module 4 also gets query-product features from Module 3 (cosine similarity, keyword overlap), so it can answer 'is this product relevant to THIS query?' not just 'is this a good product in general?'"

### "Why do the QU-enabled variants have *lower* P@k under the 'reviews' ground truth?"

"Because review-based ground truth only checks 'does this product have a good review?' — not 'is it actually a charger?' The QU-enabled variants correctly return chargers, but some chargers have 3.5-star reviews, so they're marked 'not relevant.' The dumb variants return 5-star Rokus that happen to pass the threshold. This is the exact problem our hybrid ground truth solves."

### "How does the system handle a totally novel query it's never seen?"

"Module 3 tokenizes it, extracts TF-IDF keywords against the product corpus, and embeds it with Word2Vec (averaging word vectors). Even for unseen phrases, the individual words usually have embeddings. If a word is truly OOV, it's skipped and the embedding is based on the remaining tokens. The spell corrector also kicks in for typos. Module 4's features (cosine sim, keyword overlap) then propagate this signal to the ranker."

### "What would you do differently with more time?"

"Three things: (1) Real user labels instead of synthetic — even 20 queries hand-labeled would tighten the evaluation. (2) A larger embedding corpus — 18K products is small for Word2Vec. (3) Online learning — update the LTR model as users click, rather than training once at startup."

---

## DEMO CHECKLIST (do before presenting)

- [ ] Backend running: `uvicorn api.main:app --host 127.0.0.1 --port 8000`
- [ ] Frontend running: `cd web && npm run dev`
- [ ] Test query "wireless headphones" returns good results
- [ ] Test query "charger" on /evaluate with hybrid ground truth shows correct ablation
- [ ] Browser zoomed to ~125% for screen visibility
- [ ] Close all unrelated tabs/windows
- [ ] Have the terminal ready to show `pytest` output (579 passed) if asked

---

## TIME ALLOCATION SUMMARY

| Section | Duration | Cumulative |
|---------|----------|------------|
| Title | 0:15 | 0:15 |
| Motivation | 1:15 | 1:30 |
| Architecture | 2:00 | 3:30 |
| Demo 1: Search | 1:30 | 5:00 |
| Demo 2: Evaluation/Ablation | 2:30 | 7:30 |
| Demo 3: Limitation | 0:30 | 8:00 |
| Conclusions | 1:30 | 9:30 |
| Wrap/transition | 0:30 | 10:00 |
| Q&A | 1:30 | 11:30 |
| Buffer | 0:30 | 12:00 |

---

## WHO SAYS WHAT (suggested split)

| Section | Speaker | Why |
|---------|---------|-----|
| Motivation | Kelvin | Sets the scene, you know the user story |
| Architecture (Modules 1-2) | Ronan | He built the heuristic features |
| Architecture (Modules 3-5) | Kelvin | You built the NLP core and evaluation |
| Demo 1 (search) | Whoever is at the keyboard | |
| Demo 2 (evaluation) | Kelvin | You understand the metrics and ablation |
| Demo 3 (limitation) | Either | Short and impactful |
| Conclusions | Ronan | Wraps up the team's learning |
| Q&A | Both | Whoever knows the answer best |

---

## KEY PHRASES TO USE (sounds polished)

- "Our pipeline processes a query through five stages..."
- "The ablation study isolates the contribution of each module..."
- "Under hybrid ground truth — which requires both quality AND topicality..."
- "This exposes a fundamental limitation of review-based evaluation..."
- "The system degrades gracefully — if Module 4 can't train, it falls back to heuristic scores..."
- "579 tests give us confidence that each module works in isolation and in integration..."
