from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd

from src.data.working_set_builder import (
    TARGET_CATEGORIES,
    add_predicted_category,
    build_electronics_reviews_with_meta_df,
    filter_category_by_title,
    train_category_model,
)


def _choose_first_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _format_price(value: object) -> str:
    if value is None or value != value:
        return "N/A"
    return f"${value}"


def _format_rating(value: object) -> str:
    if value is None or value != value:
        return "N/A"
    return str(value)


def run_simple_search(
    *,
    review_filename: str = "Electronics_50000.jsonl.gz",
    meta_filename: str = "meta_Electronics_50000.jsonl.gz",
    max_results: int = 10,
) -> None:
    df = build_electronics_reviews_with_meta_df(
        review_filename=review_filename,
        meta_filename=meta_filename,
    )
    model = train_category_model(df)
    df = add_predicted_category(df, model)

    prompt = (
        "Enter a category search ("
        + ", ".join(TARGET_CATEGORIES)
        + "): "
    )
    query = input(prompt).strip().lower()
    if not query:
        print("No search provided.")
        return

    if "clean_main_category" not in df.columns:
        print("No clean_main_category column found.")
        return

    matches = df[df["clean_main_category"].str.lower() == query]
    if matches.empty:
        print(f"No results found for '{query}'.")
        return

    matches = filter_category_by_title(matches, query)
    if matches.empty:
        print(f"No results found for '{query}' after title filtering.")
        return

    id_col = _choose_first_column(matches, ["parent_asin", "asin"])
    title_col = _choose_first_column(matches, ["title_meta", "title_review", "title"])
    price_col = _choose_first_column(matches, ["price"])
    rating_col = _choose_first_column(matches, ["average_rating", "rating"])

    if id_col:
        matches = matches.drop_duplicates(subset=[id_col])

    print(f"Found {len(matches)} results. Showing up to {max_results}:")
    for _, row in matches.head(max_results).iterrows():
        product_id = row.get(id_col) if id_col else "unknown"
        title = row.get(title_col) if title_col else "unknown"
        price = _format_price(row.get(price_col)) if price_col else "N/A"
        rating = _format_rating(row.get(rating_col)) if rating_col else "N/A"
        print(f"{product_id} | {title} | {price} | rating {rating}")


if __name__ == "__main__":
    run_simple_search()
