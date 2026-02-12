from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

TARGET_CATEGORIES: Tuple[str, ...] = (
    "laptop",
    "phone",
    "headphones",
    "mouse",
    "keyboard",
    "monitor",
    "printer",
    "router",
    "speaker",
    "camera",
    "other",
)

_KEYWORD_MAP = {
    "laptop": ["laptop", "notebook", "chromebook", "macbook", "thinkpad"],
    "phone": ["phone", "smartphone", "iphone", "android", "galaxy"],
    "headphones": ["headphone", "earbud", "earbuds", "earphone", "headset"],
    "mouse": ["mouse", "trackball"],
    "keyboard": ["keyboard", "keypad"],
    "monitor": ["monitor", "display", "screen"],
    "printer": ["printer", "printing"],
    "router": ["router", "modem", "wi-fi", "wifi"],
    "speaker": ["speaker", "speakers", "soundbar", "sound bar", "subwoofer"],
    "camera": ["camera", "camcorder", "dslr", "mirrorless", "webcam"],
}

_CATEGORY_TITLE_REQUIREMENTS = {
    "laptop": ["laptop", "notebook", "chromebook", "macbook", "thinkpad"],
    "phone": ["phone", "smartphone", "iphone", "android", "galaxy"],
    "headphones": ["headphone", "headphones", "earbud", "earbuds", "earphone", "headset"],
    "mouse": ["mouse", "trackball"],
    "keyboard": ["keyboard", "keypad"],
    "monitor": ["monitor", "display", "screen"],
    "printer": ["printer"],
    "router": ["router", "modem"],
    "speaker": ["speaker", "speakers", "soundbar", "subwoofer"],
    "camera": ["camera", "camcorder", "dslr", "mirrorless", "webcam"],
}

_CATEGORY_TITLE_EXCLUSIONS = {
    "laptop": [
        "adapter",
        "adaptor",
        "battery",
        "bag",
        "backpack",
        "case",
        "charger",
        "cooler",
        "cooling",
        "cover",
        "dock",
        "docking",
        "holder",
        "keyboard",
        "mouse",
        "pad",
        "screen protector",
        "skin",
        "sleeve",
        "stand",
        "stylus",
        "tablet",
        "usb",
    ],
    "phone": [
        "case",
        "cover",
        "charger",
        "adapter",
        "adaptor",
        "screen protector",
        "stand",
        "mount",
        "cable",
        "earbuds",
        "headphones",
    ],
}


@dataclass
class CategoryModel:
    vectorizer: TfidfVectorizer
    classifier: LogisticRegression
    label_set: List[str]


def _working_set_path(filename: str, working_set_dir: str | Path | None) -> Path:
    if working_set_dir is None:
        repo_root = Path(__file__).resolve().parents[2]
        working_set_dir = repo_root / "datasets" / "working_set"
    else:
        working_set_dir = Path(working_set_dir)

    return working_set_dir / filename


def build_electronics_reviews_df(
    working_set_dir: str | Path | None = None,
    filename: str = "Electronics.jsonl.gz",
) -> pd.DataFrame:
    path = _working_set_path(filename, working_set_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Working set reviews not found at {path}. "
            "Ensure the working set reviews file exists."
        )
    return pd.read_json(path, lines=True, compression="gzip")


def build_electronics_meta_df(
    working_set_dir: str | Path | None = None,
    filename: str = "meta_Electronics.jsonl.gz",
) -> pd.DataFrame:
    path = _working_set_path(filename, working_set_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"Working set metadata not found at {path}. "
            "Ensure the working set metadata file exists."
        )
    return pd.read_json(path, lines=True, compression="gzip")


def build_electronics_reviews_with_meta_df(
    working_set_dir: str | Path | None = None,
    review_filename: str = "Electronics.jsonl.gz",
    meta_filename: str = "meta_Electronics.jsonl.gz",
    add_clean_category: bool = False,
    clean_category_column: str = "clean_main_category",
) -> pd.DataFrame:
    reviews_df = build_electronics_reviews_df(working_set_dir, review_filename)
    meta_df = build_electronics_meta_df(working_set_dir, meta_filename)

    if "parent_asin" in reviews_df.columns and "parent_asin" in meta_df.columns:
        key = "parent_asin"
    elif "asin" in reviews_df.columns and "asin" in meta_df.columns:
        key = "asin"
    else:
        raise KeyError(
            "No shared join key found between reviews and metadata. "
            "Expected 'parent_asin' or 'asin'."
        )

    merged = reviews_df.merge(meta_df, on=key, how="inner", suffixes=("_review", "_meta"))

    if add_clean_category:
        model = train_category_model(merged)
        merged = add_predicted_category(merged, model, column_name=clean_category_column)

    return merged


def build_electronics_reviews_with_meta_and_clean_df(
    working_set_dir: str | Path | None = None,
    review_filename: str = "Electronics.jsonl.gz",
    meta_filename: str = "meta_Electronics.jsonl.gz",
    clean_category_column: str = "clean_main_category",
) -> pd.DataFrame:
    """
    Convenience wrapper to merge reviews + metadata and add clean category labels.
    """
    return build_electronics_reviews_with_meta_df(
        working_set_dir=working_set_dir,
        review_filename=review_filename,
        meta_filename=meta_filename,
        add_clean_category=True,
        clean_category_column=clean_category_column,
    )


def map_main_category(raw_category: Optional[str], categories: Optional[Iterable[str]]) -> str:
    """
    Map dataset category values to a fixed target set.

    Args:
        raw_category: Dataset main_category value.
        categories: Dataset categories list (if available).

    Returns:
        Target category label.
    """
    tokens = _collect_category_tokens(raw_category, categories)
    for target, keywords in _KEYWORD_MAP.items():
        if any(keyword in tokens for keyword in keywords):
            return target
    return "other"


def _build_search_text_vectorized(df: pd.DataFrame) -> pd.Series:
    """Build combined searchable text from category and title columns (vectorized)."""
    parts: List[pd.Series] = []
    for col in ("main_category", "title_meta", "title_review"):
        if col in df.columns:
            parts.append(df[col].fillna("").astype(str))
        else:
            parts.append(pd.Series([""] * len(df), index=df.index))
    if "categories" in df.columns:
        cat_str = df["categories"].apply(
            lambda x: " ".join(str(i) for i in x) if isinstance(x, list) else str(x) if x else ""
        )
        parts.append(cat_str)
    combined = pd.concat(parts, axis=1).fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return combined


def add_category_by_keywords(
    df: pd.DataFrame,
    *,
    column_name: str = "clean_main_category",
) -> pd.DataFrame:
    """
    Add a category column using vectorized keyword matching on title and category fields.
    Fast alternative to train_category_model + add_predicted_category for simple search.
    """
    combined = _build_search_text_vectorized(df)
    result = df.copy()
    result[column_name] = "other"
    # Apply categories in order so earlier matches take precedence
    for target in TARGET_CATEGORIES:
        if target == "other":
            continue
        keywords = _KEYWORD_MAP[target]
        pattern = "|".join(re.escape(k) for k in keywords)
        mask = combined.str.contains(pattern, regex=True, na=False) & (result[column_name] == "other")
        result.loc[mask, column_name] = target
    return result


def build_text_features(row: pd.Series) -> str:
    """Join title, description, and review text fields into one string."""
    parts: List[str] = []
    for key in ("title_meta", "title_review", "description", "text"):
        value = row.get(key)
        if isinstance(value, list):
            parts.extend([str(item) for item in value if item])
        elif value:
            parts.append(str(value))
    return " ".join(parts).strip().lower()


def train_category_model(df: pd.DataFrame) -> CategoryModel:
    """
    Train a TF-IDF + linear classifier for product categories.

    Labels are derived by mapping the dataset's category values to TARGET_CATEGORIES.
    """
    labels = [
        map_main_category(
            row.get("main_category"),
            row.get("categories") if isinstance(row.get("categories"), list) else None,
        )
        for _, row in df.iterrows()
    ]
    texts = [build_text_features(row) for _, row in df.iterrows()]

    vectorizer = TfidfVectorizer(stop_words="english", min_df=2)
    features = vectorizer.fit_transform(texts)
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(features, labels)
    return CategoryModel(vectorizer=vectorizer, classifier=classifier, label_set=list(TARGET_CATEGORIES))


def add_predicted_category(
    df: pd.DataFrame,
    model: CategoryModel,
    *,
    column_name: str = "clean_main_category",
) -> pd.DataFrame:
    """
    Add a predicted category column to a dataframe.
    """
    texts = [build_text_features(row) for _, row in df.iterrows()]
    features = model.vectorizer.transform(texts)
    predictions = model.classifier.predict(features)
    updated = df.copy()
    updated[column_name] = predictions
    return updated


def filter_category_by_title(
    df: pd.DataFrame,
    category: str,
    *,
    title_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Filter category rows to titles that match required terms and avoid exclusions.
    """
    normalized = category.strip().lower()
    required = _CATEGORY_TITLE_REQUIREMENTS.get(normalized, [])
    excluded = _CATEGORY_TITLE_EXCLUSIONS.get(normalized, [])
    if not required:
        return df

    if title_columns is None:
        title_columns = ["title_meta", "title_review", "title"]

    title_columns = [col for col in title_columns if col in df.columns]
    if not title_columns:
        return df

    combined = (
        df[title_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
    )

    required_mask = combined.str.contains("|".join(required), regex=True)
    if excluded:
        excluded_mask = combined.str.contains("|".join(excluded), regex=True)
        return df[required_mask & ~excluded_mask]

    return df[required_mask]


def _collect_category_tokens(
    raw_category: Optional[str],
    categories: Optional[Iterable[str]],
) -> List[str]:
    tokens: List[str] = []
    if raw_category:
        tokens.extend(str(raw_category).lower().split())
    if categories:
        for item in categories:
            if item:
                tokens.extend(str(item).lower().split())
    return tokens
