from __future__ import annotations

from pathlib import Path

import pandas as pd


def _working_set_path(filename: str, working_set_dir: str | Path | None) -> Path:
    if working_set_dir is None:
        repo_root = Path(__file__).resolve().parents[2]
        working_set_dir = repo_root / "datasets" / "working_set"
    else:
        working_set_dir = Path(working_set_dir)

    return working_set_dir / filename


def build_electronics_reviews_df(
    working_set_dir: str | Path | None = None,
) -> pd.DataFrame:
    path = _working_set_path("Electronics.jsonl.gz", working_set_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Working set reviews not found at {path}. "
            "Ensure datasets/working_set/Electronics.jsonl.gz exists."
        )
    return pd.read_json(path, lines=True, compression="gzip")


def build_electronics_meta_df(
    working_set_dir: str | Path | None = None,
) -> pd.DataFrame:
    path = _working_set_path("meta_Electronics.jsonl.gz", working_set_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Working set metadata not found at {path}. "
            "Ensure datasets/working_set/meta_Electronics.jsonl.gz exists."
        )
    return pd.read_json(path, lines=True, compression="gzip")
