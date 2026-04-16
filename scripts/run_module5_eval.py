#!/usr/bin/env python3
"""
Run Module 5 evaluation on the real working-set catalog (offline).

Plain-language summary
----------------------
We already have a search stack (find candidates, re-rank, understand the query,
learn-to-rank). Module 5 scores *how good* the top results are.

We do not have human judges for “this exact query → these relevant products.”
So we use a simple rule from the review file: if a product was reviewed at
**4 stars or higher** at least once, we treat it as **relevant** inside a fixed
pool of candidate IDs (here: everything Module 1 returns for the same category
filter as the API-style eval). Then we measure whether our ranked top‑k
overlaps those “liked” products (precision, recall, NDCG, etc.).

That proxy is imperfect (a high star count does not mean it matches the query
text), but it is transparent and reproducible on the Amazon slice you have.

Examples::

    python scripts/run_module5_eval.py
    python scripts/run_module5_eval.py --max-products 3000 --max-queries 8
    python scripts/run_module5_eval.py --no-ltr-train   # faster; unfitted LTR
    python scripts/run_module5_eval.py --ablation       # compare M2-only vs LTR variants
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("run_module5_eval")


def _load_reviews_dataframe(reviews_path: str):
    import pandas as pd

    df = pd.read_json(reviews_path, lines=True, compression="infer")
    df = df[["parent_asin", "rating"]].dropna()
    df["parent_asin"] = df["parent_asin"].astype(str)
    df["rating"] = df["rating"].astype(float)
    return df


def _run_ablation_table(
    *,
    catalog: Any,
    retrieval: Any,
    ranker: Any,
    qu: Any,
    embedder: Any,
    holdout: Any,
    queries_and_filters: List[Tuple[str, Any]],
    k: int,
    ranking_strategy: str,
    train_ltr: bool,
    json_out: str,
) -> None:
    """Compare mean metrics across evaluation ablations (offline)."""
    from src.module4.pipeline import LearningToRankPipeline
    from src.module4.training_data import TrainingDataGenerator
    from src.module5.pipeline import EvaluationPipeline

    ltr_unfitted = LearningToRankPipeline()
    ltr_fitted: Optional[Any] = None
    if train_ltr:
        gen = TrainingDataGenerator(
            catalog=catalog,
            query_understanding=qu,
            embedder=embedder,
        )
        X_train, y_train = gen.generate(max_products_per_query=50, seed=42)
        use_select = os.environ.get("LTR_MODEL_SELECT", "1").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        ltr_fitted = LearningToRankPipeline()
        ltr_fitted.fit(X=X_train, labels=list(y_train), select_best_model=use_select)
        logger.info(
            "Ablation: trained LTR once (%d examples) for fitted rows",
            X_train.shape[0],
        )

    rows: List[Tuple[str, Dict[str, float]]] = []

    p0 = EvaluationPipeline(
        catalog,
        retrieval,
        ranker,
        ltr_unfitted,
        query_understanding=qu,
        embedder=embedder,
    )
    b0 = p0.batch_evaluate(
        queries_and_filters,
        holdout,
        k=k,
        ranking_strategy=ranking_strategy,
        use_ltr=False,
    )
    rows.append(("M1+M2 only (no LTR)", b0.aggregate))

    p1 = EvaluationPipeline(
        catalog,
        retrieval,
        ranker,
        ltr_unfitted,
        query_understanding=qu,
        embedder=embedder,
    )
    b1 = p1.batch_evaluate(
        queries_and_filters,
        holdout,
        k=k,
        ranking_strategy=ranking_strategy,
        use_ltr=True,
        use_query_understanding=True,
    )
    rows.append(("+M3 + LTR unfitted", b1.aggregate))

    p2 = EvaluationPipeline(
        catalog,
        retrieval,
        ranker,
        ltr_unfitted,
        query_understanding=qu,
        embedder=embedder,
    )
    b2 = p2.batch_evaluate(
        queries_and_filters,
        holdout,
        k=k,
        ranking_strategy=ranking_strategy,
        use_ltr=True,
        use_query_understanding=False,
    )
    rows.append(("+LTR unfitted (quality-only @ inference)", b2.aggregate))

    if train_ltr and ltr_fitted is not None:
        p3 = EvaluationPipeline(
            catalog,
            retrieval,
            ranker,
            ltr_fitted,
            query_understanding=qu,
            embedder=embedder,
        )
        b3 = p3.batch_evaluate(
            queries_and_filters,
            holdout,
            k=k,
            ranking_strategy=ranking_strategy,
            use_ltr=True,
            use_query_understanding=True,
        )
        rows.append(("+M3 + LTR trained", b3.aggregate))

        p4 = EvaluationPipeline(
            catalog,
            retrieval,
            ranker,
            ltr_fitted,
            query_understanding=qu,
            embedder=embedder,
        )
        b4 = p4.batch_evaluate(
            queries_and_filters,
            holdout,
            k=k,
            ranking_strategy=ranking_strategy,
            use_ltr=True,
            use_query_understanding=False,
        )
        rows.append(("+LTR trained (quality-only @ inference)", b4.aggregate))
    else:
        logger.info(
            "Ablation: skipped LTR-trained rows (--no-ltr-train). "
            "Omit that flag to include trained LTR in the table.",
        )

    print()
    print("=== Ablation: mean metrics (same holdout & queries) ===")
    metric_keys = sorted(rows[0][1].keys()) if rows else []
    label_w = min(52, max(len(r[0]) for r in rows) + 2)
    header = f"{'Setting':<{label_w}}" + "".join(f"{k:>22}" for k in metric_keys)
    print(header)
    print("-" * len(header))
    for label, agg in rows:
        line = f"{label:<{label_w}}"
        for key in metric_keys:
            line += f"{agg.get(key, float('nan')):>22.4f}"
        print(line)
    print()

    if json_out:
        out_path = os.path.abspath(json_out)
        serial = [{"setting": lab, **agg} for lab, agg in rows]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(serial, f, indent=2)
        logger.info("Wrote %s", out_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Module 5 batch eval: working set + review-derived relevance",
    )
    parser.add_argument(
        "--working-set",
        default=os.path.join(PROJECT_ROOT, "datasets", "working_set"),
        help="Directory with meta_Electronics_50000.jsonl.gz and Electronics_50000.jsonl.gz",
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=None,
        help="Cap catalog size for faster runs (default: load all)",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=12,
        help="How many SAMPLE_QUERIES to evaluate (from Module 4 training list)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Top-k for metrics and payload",
    )
    parser.add_argument(
        "--category",
        default="All Electronics",
        help=(
            "SearchFilters.category for Module 1 (same for all eval queries). "
            "Working-set metadata uses e.g. 'All Electronics', not 'Electronics'."
        ),
    )
    parser.add_argument(
        "--ranking-strategy",
        default="baseline",
        help="Module 2 strategy (baseline, hill_climbing, simulated_annealing)",
    )
    parser.add_argument(
        "--rating-threshold",
        type=float,
        default=4.0,
        help="Review rating >= this counts as relevant",
    )
    parser.add_argument(
        "--no-ltr-train",
        action="store_true",
        help="Skip LTR fit (uses unfitted Module 4; much faster)",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="If set, write aggregate metrics to this JSON file",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help=(
            "Run several evaluation settings and print a comparison table: "
            "M1+M2 only; LTR unfitted (+QU); optionally LTR trained (+QU); "
            "LTR trained without query features. Skips training rows if --no-ltr-train."
        ),
    )
    args = parser.parse_args()

    ws = os.path.abspath(args.working_set)
    if not os.path.isdir(ws):
        raise SystemExit(f"Working set directory not found: {ws}")

    from src.module1 import SearchFilters, load_catalog_from_working_set
    from src.module1.retrieval import CandidateRetrieval
    from src.module2.ranker import HeuristicRanker
    from src.module3.query_understanding import QueryUnderstanding
    from src.module4.pipeline import LearningToRankPipeline
    from src.module4.training_data import SAMPLE_QUERIES, TrainingDataGenerator
    from src.module5.holdout import build_holdout_from_reviews
    from src.module5.pipeline import EvaluationPipeline

    reviews_path = os.path.join(ws, "Electronics_50000.jsonl.gz")
    if not os.path.isfile(reviews_path):
        raise SystemExit(f"Reviews file missing: {reviews_path}")

    logger.info("Loading catalog from %s …", ws)
    catalog = load_catalog_from_working_set(ws, max_products=args.max_products)
    if len(catalog) == 0:
        raise SystemExit("Catalog is empty.")

    logger.info("Loading reviews (for relevance labels) …")
    reviews_df = _load_reviews_dataframe(reviews_path)

    retrieval = CandidateRetrieval(catalog)
    ranker = HeuristicRanker(catalog)
    filters = SearchFilters(category=args.category)
    search_result = retrieval.search(filters)
    if search_result.count == 0:
        raise SystemExit(
            f"No candidates for SearchFilters(category={args.category!r}). "
            "Try another --category."
        )
    pool_ids = list(search_result.candidate_ids)

    queries = SAMPLE_QUERIES[: max(1, args.max_queries)]
    mapping: Dict[str, List[str]] = {q: pool_ids for q in queries}
    holdout = build_holdout_from_reviews(
        reviews_df,
        mapping,
        rating_threshold=args.rating_threshold,
    )

    n_rel = [len(holdout.get_relevant(q)) for q in queries]
    logger.info(
        "Holdout: %d queries, relevant counts (min/median/max) = %d / %d / %d",
        len(queries),
        min(n_rel),
        sorted(n_rel)[len(n_rel) // 2],
        max(n_rel),
    )

    corpus_texts = [f"{p.title} {p.description or ''}" for p in catalog]
    corpus_labels = [p.category for p in catalog]
    qu = QueryUnderstanding(corpus_texts, corpus_labels)
    embedder = qu._embedder

    queries_and_filters: List[Tuple[str, SearchFilters]] = [
        (q, filters) for q in queries
    ]

    if args.ablation:
        _run_ablation_table(
            catalog=catalog,
            retrieval=retrieval,
            ranker=ranker,
            qu=qu,
            embedder=embedder,
            holdout=holdout,
            queries_and_filters=queries_and_filters,
            k=args.k,
            ranking_strategy=args.ranking_strategy,
            train_ltr=not args.no_ltr_train,
            json_out=args.json_out or "",
        )
    else:
        ltr = LearningToRankPipeline()
        if not args.no_ltr_train:
            gen = TrainingDataGenerator(
                catalog=catalog,
                query_understanding=qu,
                embedder=embedder,
            )
            X_train, y_train = gen.generate(max_products_per_query=50, seed=42)
            use_select = os.environ.get("LTR_MODEL_SELECT", "1").strip().lower() in (
                "1",
                "true",
                "yes",
            )
            ltr.fit(X=X_train, labels=list(y_train), select_best_model=use_select)
            logger.info(
                "LTR trained: %d rows, %d features, model=%s",
                X_train.shape[0],
                X_train.shape[1],
                ltr.ranker.selected_model_name or "logistic_regression",
            )
        else:
            logger.info("Skipping LTR training (--no-ltr-train).")

        pipeline = EvaluationPipeline(
            catalog=catalog,
            retrieval=retrieval,
            ranker=ranker,
            ltr_pipeline=ltr,
            query_understanding=qu,
            embedder=embedder,
        )

        batch = pipeline.batch_evaluate(
            queries_and_filters,
            holdout,
            k=args.k,
            ranking_strategy=args.ranking_strategy,
        )

        agg = batch.aggregate
        print()
        print("=== Module 5 batch metrics (mean over queries) ===")
        for key in sorted(agg.keys()):
            print(f"  {key}: {agg[key]:.4f}")
        print(
            f"  (queries={batch.num_queries}, k={args.k}, category={args.category!r})"
        )
        print()

        if args.json_out:
            out_path = os.path.abspath(args.json_out)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(agg, f, indent=2)
            logger.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
