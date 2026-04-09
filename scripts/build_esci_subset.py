#!/usr/bin/env python3
"""
Build a small ESCI examples subset for fast local work (no multi‑GB load).

Reads Amazon Science ESCI ``shopping_queries_dataset_examples.parquet`` and writes
a stratified sample (balanced across E/S/C/I) so training smoke tests stay quick.

Usage (from repo root)::

    python scripts/build_esci_subset.py
    python scripts/build_esci_subset.py --rows 5000 --seed 7
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _default_paths(repo_root: Path) -> tuple[Path, Path]:
    src = (
        repo_root
        / "datasets"
        / "esci"
        / "shopping_queries_dataset"
        / "shopping_queries_dataset_examples.parquet"
    )
    out = repo_root / "datasets" / "esci_subset_10k.parquet"
    return src, out


def build_subset(
    src: Path,
    out: Path,
    *,
    rows: int,
    seed: int,
    locale: str,
    split: str,
) -> None:
    if not src.is_file():
        raise SystemExit(
            f"Missing source parquet: {src}\n"
            "Clone amazon-science/esci-data and git lfs pull the examples file, "
            "or place the file at that path."
        )

    cols = [
        "example_id",
        "query",
        "query_id",
        "product_id",
        "product_locale",
        "esci_label",
        "small_version",
        "large_version",
        "split",
    ]
    df = pd.read_parquet(src, columns=cols)
    df = df[(df["product_locale"] == locale) & (df["split"] == split)]
    if df.empty:
        raise SystemExit(f"No rows after filter locale={locale!r} split={split!r}")

    labels = sorted(df["esci_label"].unique())
    per = max(1, rows // len(labels))
    parts: list[pd.DataFrame] = []
    for lab in labels:
        bucket = df[df["esci_label"] == lab]
        k = min(per, len(bucket))
        parts.append(bucket.sample(n=k, random_state=seed))
    sub = pd.concat(parts, ignore_index=True)
    if len(sub) > rows:
        sub = sub.sample(n=rows, random_state=seed).reset_index(drop=True)

    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_parquet(out, index=False)
    print(f"Wrote {len(sub)} rows ({sub['esci_label'].value_counts().to_dict()}) -> {out}")


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    default_src, default_out = _default_paths(repo)
    p = argparse.ArgumentParser(description="Build small ESCI examples subset")
    p.add_argument("--src", type=Path, default=default_src)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument("--rows", type=int, default=10_000, help="Target rows (approx, stratified)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--locale", default="us")
    p.add_argument("--split", default="train")
    args = p.parse_args()
    build_subset(
        args.src,
        args.out,
        rows=args.rows,
        seed=args.seed,
        locale=args.locale,
        split=args.split,
    )


if __name__ == "__main__":
    main()
