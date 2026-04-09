"""
Held-out ground-truth data for evaluation (Module 5).

Wraps a mapping of ``{query_text -> set(relevant_product_ids)}`` and
provides a factory to derive binary relevance from the working-set
review data (e.g. rating >= 4 stars means relevant).
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import pandas as pd

from src.module5.exceptions import HeldOutDataError

logger = logging.getLogger(__name__)


@dataclass
class HeldOutSet:
    """Ground-truth relevance judgements for evaluation.

    Each key is a query string; each value is the set of product IDs
    considered relevant for that query.

    Attributes:
        relevance: Mapping of query text to relevant product IDs.
    """

    relevance: Dict[str, Set[str]] = field(default_factory=dict)

    @property
    def queries(self) -> List[str]:
        """All queries in the held-out set, sorted alphabetically."""
        return sorted(self.relevance.keys())

    @property
    def num_queries(self) -> int:
        return len(self.relevance)

    def get_relevant(self, query: str) -> Set[str]:
        """Return relevant product IDs for *query*, or empty set."""
        return self.relevance.get(query, set())

    def get_relevance(self, query: str, product_id: str) -> int:
        """Binary relevance: 1 if product is relevant for query, else 0."""
        return 1 if product_id in self.get_relevant(query) else 0

    def add(self, query: str, product_ids: Set[str]) -> None:
        """Add or replace relevance judgements for a query."""
        self.relevance[query] = set(product_ids)


def build_holdout_from_reviews(
    reviews_df: pd.DataFrame,
    query_product_mapping: Dict[str, List[str]],
    rating_threshold: float = 4.0,
    rating_column: str = "rating",
    product_id_column: str = "parent_asin",
) -> HeldOutSet:
    """Derive a held-out set from review ratings.

    For each query in *query_product_mapping*, a product is considered
    **relevant** if at least one review in *reviews_df* gives it a
    rating >= *rating_threshold*.

    Args:
        reviews_df: DataFrame of reviews with at least
            *rating_column* and *product_id_column*.
        query_product_mapping: ``{query_text: [candidate_product_ids]}``.
        rating_threshold: Minimum star rating for relevance.
        rating_column: Column name for the numeric rating.
        product_id_column: Column name for the product identifier.

    Returns:
        HeldOutSet with binary relevance derived from reviews.

    Raises:
        HeldOutDataError: If required columns are missing.
    """
    for col in (rating_column, product_id_column):
        if col not in reviews_df.columns:
            raise HeldOutDataError(
                f"reviews DataFrame missing required column '{col}'"
            )

    positive = reviews_df.loc[
        reviews_df[rating_column] >= rating_threshold, product_id_column
    ]
    positive_ids: Set[str] = set(positive.unique())

    holdout = HeldOutSet()
    for query, candidate_ids in query_product_mapping.items():
        relevant = {pid for pid in candidate_ids if pid in positive_ids}
        holdout.add(query, relevant)

    logger.info(
        "Built held-out set: %d queries, avg %.1f relevant items/query",
        holdout.num_queries,
        (
            sum(len(v) for v in holdout.relevance.values()) / max(holdout.num_queries, 1)
        ),
    )
    return holdout


def train_test_split_holdout(
    holdout: HeldOutSet,
    test_fraction: float = 0.3,
    seed: int = 42,
) -> Tuple[HeldOutSet, HeldOutSet]:
    """Split a held-out set into train and test partitions by query.

    Args:
        holdout: Full held-out set.
        test_fraction: Fraction of queries to reserve for testing.
        seed: Random seed for reproducibility.

    Returns:
        ``(train_holdout, test_holdout)`` tuple.
    """
    queries = holdout.queries
    rng = random.Random(seed)
    rng.shuffle(queries)

    split_idx = max(1, int(len(queries) * (1 - test_fraction)))
    train_queries = queries[:split_idx]
    test_queries = queries[split_idx:]

    train = HeldOutSet({q: holdout.get_relevant(q) for q in train_queries})
    test = HeldOutSet({q: holdout.get_relevant(q) for q in test_queries})
    return train, test
