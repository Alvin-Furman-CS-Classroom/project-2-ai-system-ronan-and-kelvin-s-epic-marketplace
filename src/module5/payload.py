"""
Top-k result payload for user-facing output (Module 5).

Packages scored candidates from Module 4 into a JSON-ready
result list enriched with product metadata from the catalog.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.module1.catalog import Product, ProductCatalog
from src.module5.exceptions import EmptyCandidateError


@dataclass(frozen=True)
class TopKResult:
    """Immutable user-facing search result payload.

    Attributes:
        query: The original query text.
        k: Number of results requested.
        results: List of result dicts, each containing at minimum
            ``id``, ``score``, ``title``, ``price``, ``category``.
        metrics: Optional evaluation metrics attached after scoring.
    """

    query: str
    k: int
    results: Tuple[Dict[str, Any], ...] = ()
    metrics: Optional[Dict[str, float]] = None

    @property
    def num_results(self) -> int:
        return len(self.results)

    @property
    def product_ids(self) -> List[str]:
        """Product IDs in result order."""
        return [r["id"] for r in self.results]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary (JSON-ready)."""
        out: Dict[str, Any] = {
            "query": self.query,
            "k": self.k,
            "num_results": self.num_results,
            "results": list(self.results),
        }
        if self.metrics is not None:
            out["metrics"] = self.metrics
        return out


def build_top_k_payload(
    scored_candidates: List[Tuple[str, float]],
    catalog: ProductCatalog,
    query: str,
    k: int = 10,
    metrics: Optional[Dict[str, float]] = None,
) -> TopKResult:
    """Assemble a top-k payload from Module 4 scores and the catalog.

    Args:
        scored_candidates: ``(product_id, score)`` pairs in descending
            score order (as returned by :meth:`LearningToRankPipeline.rank`).
        catalog: Product catalog for metadata lookup.
        query: The original search query text.
        k: Maximum number of results to include.
        metrics: Optional pre-computed evaluation metrics to attach.

    Returns:
        Frozen :class:`TopKResult` with up to *k* enriched results.
    """
    top = scored_candidates[:k]

    results = []
    for product_id, score in top:
        product = catalog.get(product_id)
        if product is None:
            continue
        results.append(_product_to_result_dict(product, score))

    return TopKResult(
        query=query,
        k=k,
        results=tuple(results),
        metrics=metrics,
    )


def _product_to_result_dict(product: Product, score: float) -> Dict[str, Any]:
    """Convert a Product + score into a result dictionary."""
    entry: Dict[str, Any] = {
        "id": product.id,
        "score": round(score, 4),
        "title": product.title,
        "price": product.price,
        "category": product.category,
        "seller_rating": product.seller_rating,
        "store": product.store,
    }
    if product.image_url is not None:
        entry["image_url"] = product.image_url
    return entry
