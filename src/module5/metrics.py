"""
Evaluation metrics for information retrieval ranking (Module 5).

All functions accept a ranked list of product IDs and a set of
ground-truth relevant IDs.  The interface differs from Module 2's
score-based ``ndcg_at_k`` — here we operate on *identifiers* and
*binary relevance*, which is the standard IR evaluation convention.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Set, Union


def precision_at_k(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int,
) -> float:
    """Fraction of the top-k results that are relevant.

    Args:
        ranked_ids: Product IDs in rank order (best first).
        relevant_ids: Ground-truth relevant product IDs.
        k: Cut-off position (must be >= 1).

    Returns:
        Precision@k in [0, 1].  Returns 0.0 when k <= 0.
    """
    if k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for pid in top_k if pid in relevant_ids)
    return hits / k


def recall_at_k(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int,
) -> float:
    """Fraction of all relevant items that appear in the top-k.

    Args:
        ranked_ids: Product IDs in rank order (best first).
        relevant_ids: Ground-truth relevant product IDs.
        k: Cut-off position.

    Returns:
        Recall@k in [0, 1].  Returns 1.0 when there are no relevant items
        (vacuous truth — nothing to miss).
    """
    if not relevant_ids:
        return 1.0
    if k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    hits = sum(1 for pid in top_k if pid in relevant_ids)
    return hits / len(relevant_ids)


def _dcg(relevances: List[float], k: int) -> float:
    """Discounted Cumulative Gain at position *k*."""
    total = 0.0
    for i, rel in enumerate(relevances[:k]):
        total += rel / math.log2(i + 2)
    return total


def ndcg_at_k(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int,
    relevance_scores: Optional[Dict[str, float]] = None,
) -> float:
    """Normalized Discounted Cumulative Gain at position *k*.

    Supports binary relevance (default) or graded relevance when
    *relevance_scores* is provided.

    Args:
        ranked_ids: Product IDs in rank order (best first).
        relevant_ids: Ground-truth relevant product IDs.
        k: Cut-off position.
        relevance_scores: Optional mapping of product ID to graded
            relevance (e.g. 0–5).  When ``None``, binary relevance
            (1 if in *relevant_ids*, else 0) is used.

    Returns:
        NDCG@k in [0, 1].  Returns 1.0 for empty inputs.
    """
    if k <= 0 or not ranked_ids:
        return 1.0

    def _rel(pid: str) -> float:
        if relevance_scores is not None:
            return relevance_scores.get(pid, 0.0)
        return 1.0 if pid in relevant_ids else 0.0

    actual = [_rel(pid) for pid in ranked_ids[:k]]
    ideal = sorted(actual, reverse=True)

    ideal_dcg = _dcg(ideal, k)
    if ideal_dcg == 0.0:
        return 1.0
    return _dcg(actual, k) / ideal_dcg


def reciprocal_rank(
    ranked_ids: List[str],
    relevant_ids: Set[str],
) -> float:
    """Reciprocal of the rank of the first relevant item.

    Args:
        ranked_ids: Product IDs in rank order.
        relevant_ids: Ground-truth relevant product IDs.

    Returns:
        1 / rank (1-based) of the first hit, or 0.0 if no hit.
    """
    for i, pid in enumerate(ranked_ids):
        if pid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def average_precision(
    ranked_ids: List[str],
    relevant_ids: Set[str],
) -> float:
    """Average Precision for a single query.

    Computes the mean of precision values at each position where
    a relevant item is found.  This is the area under the
    precision–recall curve.

    Args:
        ranked_ids: Product IDs in rank order.
        relevant_ids: Ground-truth relevant product IDs.

    Returns:
        AP in [0, 1].  Returns 0.0 when there are no relevant items.
    """
    if not relevant_ids:
        return 0.0
    hits = 0
    total_precision = 0.0
    for i, pid in enumerate(ranked_ids):
        if pid in relevant_ids:
            hits += 1
            total_precision += hits / (i + 1)
    if hits == 0:
        return 0.0
    return total_precision / len(relevant_ids)


def compute_all_metrics(
    ranked_ids: List[str],
    relevant_ids: Set[str],
    k: int,
    relevance_scores: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Compute all evaluation metrics for a single query.

    Convenience function that returns a dictionary of all metrics.

    Args:
        ranked_ids: Product IDs in rank order.
        relevant_ids: Ground-truth relevant product IDs.
        k: Cut-off position for Precision/Recall/NDCG.
        relevance_scores: Optional graded relevance mapping.

    Returns:
        Dictionary with keys ``precision_at_k``, ``recall_at_k``,
        ``ndcg_at_k``, ``reciprocal_rank``, ``average_precision``.
    """
    return {
        "precision_at_k": precision_at_k(ranked_ids, relevant_ids, k),
        "recall_at_k": recall_at_k(ranked_ids, relevant_ids, k),
        "ndcg_at_k": ndcg_at_k(ranked_ids, relevant_ids, k, relevance_scores),
        "reciprocal_rank": reciprocal_rank(ranked_ids, relevant_ids),
        "average_precision": average_precision(ranked_ids, relevant_ids),
    }
