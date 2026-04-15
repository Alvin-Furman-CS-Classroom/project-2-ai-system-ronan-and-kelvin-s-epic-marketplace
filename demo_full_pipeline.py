"""
Full pipeline demo: Modules 1-5 on real working_set data.

Query: "wireless noise cancelling headphones"
"""

import logging
import time
import sys

logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s | %(message)s",
)

print("=" * 72)
print("  Epic Marketplace -- Full Pipeline Demo (Modules 1-5)")
print("=" * 72)

# Ensure stdout handles all characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- Step 0: Load catalog from working_set ---------------------------------
print("\n[Step 0] Loading catalog from working_set...")
t0 = time.perf_counter()

from src.module1.loader import load_catalog_from_working_set
catalog = load_catalog_from_working_set(max_products=2000)

print(f"  Catalog: {len(catalog)} products loaded in {time.perf_counter() - t0:.1f}s")
print(f"  Categories: {catalog.categories[:8]}...")

# -- Step 1: Module 1 -- Candidate Retrieval --------------------------------
print("\n[Step 1] Module 1 -- Candidate Retrieval")

from src.module1.retrieval import CandidateRetrieval
from src.module1.filters import SearchFilters

retrieval = CandidateRetrieval(catalog)
# Use no category filter so we search across the full catalog
filters = SearchFilters()
search_result = retrieval.search(filters)

print(f"  Strategy: {search_result.strategy}")
print(f"  Candidates: {search_result.count}  Scanned: {search_result.total_scanned}")

# ── Step 2: Module 2 — Heuristic Re-ranking ───────────────────────────
print("\n[Step 2] Module 2 — Heuristic Re-ranking (hill climbing)")

from src.module2.ranker import HeuristicRanker

ranker = HeuristicRanker(catalog)
ranked_result = ranker.rank(
    search_result, strategy="hill_climbing",
    target_category="Electronics", k=10,
)

print(f"  Strategy: {ranked_result.strategy}")
print(f"  Iterations: {ranked_result.iterations}  NDCG: {ranked_result.objective_value:.4f}")
print(f"  Top 5 (heuristic):")
for pid, score in ranked_result.ranked_candidates[:5]:
    p = catalog[pid]
    print(f"    {pid:15s} | {p.title[:40]:40s} | ${p.price:<8.2f} | rating {p.seller_rating}")

# ── Step 3: Module 3 — Query Understanding ────────────────────────────
print("\n[Step 3] Module 3 — Query Understanding")

from src.module3 import QueryUnderstanding, ProductEmbedder

corpus_texts = [
    f"{p.title} {p.description or ''}" for p in catalog
]
labels = [p.category for p in catalog]

t3 = time.perf_counter()
qu = QueryUnderstanding(corpus_texts, labels)
embedder = qu._embedder

query = "wireless noise cancelling headphones"
query_result = qu.understand(query)
print(f"  NLP trained in {time.perf_counter() - t3:.1f}s")
print(f"  Query: \"{query}\"")
print(f"  Keywords: {query_result.keywords[:5]}")
print(f"  Inferred category: {query_result.inferred_category} (conf={query_result.confidence:.2f})")
if query_result.corrected_query:
    print(f"  Spell correction: \"{query_result.corrected_query}\"")
print(f"  Embedding shape: {query_result.query_embedding.shape}")

# ── Step 4: Module 4 — Learning-to-Rank ───────────────────────────────
print("\n[Step 4] Module 4 — Learning-to-Rank")

from src.module4.pipeline import LearningToRankPipeline
from src.module4.training_data import TrainingDataGenerator

t4 = time.perf_counter()
gen = TrainingDataGenerator(catalog, qu, embedder)
X_train, y_train = gen.generate(max_products_per_query=50, seed=42)
print(f"  Training data: {X_train.shape[0]} examples, {X_train.shape[1]} features")

ltr = LearningToRankPipeline()
ltr.fit(X=X_train, labels=y_train)
print(f"  Model fitted: {ltr.ranker.selected_model_name}")

candidate_products = [
    catalog[pid] for pid, _ in ranked_result.ranked_candidates
    if pid in catalog
]

final_scores = ltr.rank(
    candidate_products, top_k=10,
    query_result=query_result, embedder=embedder,
)
print(f"  LTR trained + scored in {time.perf_counter() - t4:.1f}s")

print(f"\n  Top 10 (LTR-scored):")
for i, (pid, score) in enumerate(final_scores[:10], 1):
    p = catalog[pid]
    print(f"    {i:2d}. {pid:15s} | {p.title[:40]:40s} | ${p.price:<8.2f} | score {score:.4f}")

# ── Step 5: Module 5 — Evaluation & Final Output ─────────────────────
print("\n[Step 5] Module 5 — Evaluation & Final Output")

from src.module5.pipeline import EvaluationPipeline
from src.module5.holdout import HeldOutSet
from src.module5.metrics import compute_all_metrics

# Build a simple held-out set: products with "headphone" or "noise cancelling"
# in title and rating >= 4 are relevant for this query
relevant_ids = set()
for p in catalog:
    title_lower = p.title.lower()
    if ("headphone" in title_lower or "noise cancelling" in title_lower
            or "earbuds" in title_lower or "earphone" in title_lower):
        if p.seller_rating >= 4.0:
            relevant_ids.add(p.id)

holdout = HeldOutSet({query: relevant_ids})
print(f"  Held-out: {len(relevant_ids)} relevant products for query")

pipeline = EvaluationPipeline(
    catalog=catalog,
    retrieval=retrieval,
    ranker=ranker,
    ltr_pipeline=ltr,
    query_understanding=qu,
    embedder=embedder,
)

result = pipeline.evaluate(
    query, filters, holdout, k=10, ranking_strategy="hill_climbing",
)

print(f"\n  +---------------------------------------------------+")
print(f"  |           Evaluation Metrics (k=10)              |")
print(f"  +---------------------------------------------------+")
print(f"  |  Precision@10:      {result.metrics['precision_at_k']:.4f}                       |")
print(f"  |  Recall@10:         {result.metrics['recall_at_k']:.4f}                       |")
print(f"  |  NDCG@10:           {result.metrics['ndcg_at_k']:.4f}                       |")
print(f"  |  MRR:               {result.metrics['reciprocal_rank']:.4f}                       |")
print(f"  |  Average Precision: {result.metrics['average_precision']:.4f}                       |")
print(f"  +---------------------------------------------------+")

print(f"\n  Top-K Payload:")
payload = result.payload
print(f"  Query: \"{payload.query}\"  k={payload.k}  results={payload.num_results}")
print()
for i, item in enumerate(payload.results, 1):
    print(f"    {i:2d}. [{item['id']}] {item['title'][:45]}")
    print(f"        score={item['score']:.4f}  price=${item['price']:.2f}  "
          f"rating={item['seller_rating']}  store={item['store']}")
    relevant_tag = " * RELEVANT" if item['id'] in relevant_ids else ""
    print(f"        category={item['category']}{relevant_tag}")
    print()

print("=" * 72)
print("  Pipeline complete.")
print("=" * 72)
