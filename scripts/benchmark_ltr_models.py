#!/usr/bin/env python3
"""
Print Module 4 LTR model comparison (stratified ROC AUC) so you can see differences.

**Quick mode (default):** random feature matrix — fast, no catalog.

**Real mode:** ``--real`` loads the working-set catalog, builds Module 3, runs
:class:`~src.module4.training_data.TrainingDataGenerator`, then compares models.

Examples::

    python scripts/benchmark_ltr_models.py
    python scripts/benchmark_ltr_models.py --real
    python scripts/benchmark_ltr_models.py --rows 2000 --splits 3
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _synthetic_xy(rows: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((rows, 11))
    logits = X @ rng.standard_normal(11)
    y = (logits > np.median(logits)).astype(np.int64)
    return X, y


def main() -> None:
    p = argparse.ArgumentParser(description="Compare LTR models (ROC AUC CV)")
    p.add_argument("--rows", type=int, default=800, help="Synthetic rows (ignored with --real)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--splits", type=int, default=5)
    p.add_argument(
        "--real",
        action="store_true",
        help="Use catalog + TrainingDataGenerator (slower)",
    )
    args = p.parse_args()

    if args.real:
        from src.module1 import load_catalog_from_working_set
        from src.module3.query_understanding import QueryUnderstanding
        from src.module4.model_selection import compare_models, fit_best_pipeline
        from src.module4.training_data import TrainingDataGenerator

        ws = os.path.join(PROJECT_ROOT, "datasets", "working_set")
        if not os.path.isdir(ws):
            raise SystemExit(f"--real requires {ws} (working set).")
        catalog = load_catalog_from_working_set(ws)
        texts = [f"{p.title} {p.description or ''}" for p in catalog]
        labels = [p.category for p in catalog]
        qu = QueryUnderstanding(texts, labels)
        gen = TrainingDataGenerator(catalog, qu, qu._embedder)
        X, y = gen.generate(max_products_per_query=50, seed=args.seed)
    else:
        from src.module4.model_selection import compare_models, fit_best_pipeline

        X, y = _synthetic_xy(args.rows, args.seed)

    table = compare_models(X, y, random_state=args.seed, n_splits=args.splits)
    print("\nStratified CV ROC AUC (higher is better):\n")
    for row in table:
        print(
            f"  {row['name']:<22}  mean={row['mean_roc_auc']:.4f}  std={row['std_roc_auc']:.4f}"
        )
    name, auc, _pipe = fit_best_pipeline(X, y, random_state=args.seed, n_splits=args.splits)
    print(f"\nSelected (refit on full data): {name}  (CV mean ROC AUC={auc:.4f})")
    print(f"samples={X.shape[0]} features={X.shape[1]} folds={args.splits}\n")


if __name__ == "__main__":
    main()
