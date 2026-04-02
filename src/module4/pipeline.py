"""
End-to-end learning-to-rank pipeline (Module 4).

Fits a :class:`QualityValueRanker` on candidate products and exposes
``final_scores`` for integration with Module 1 retrieval and Module 2 heuristics.

Typical use:

1. Retrieve candidates with Module 1 (optionally filtered by price).
2. **Quality-only:** ``pipeline.fit(products, price_band=...)`` then ``rank(products)``.
3. **With Module 3:** ``fit_rank(..., query_result=qr, embedder=emb)`` so features match
   :func:`~src.module4.query_features.compute_combined_features`.
4. **Offline training:** ``fit(X=features, labels=y)`` from :class:`TrainingDataGenerator`,
   then ``rank(products, query_result=..., embedder=...)`` at inference when the model
   is 11-dimensional.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple

import numpy as np

from src.module1.catalog import Product
from src.module4.exceptions import InsufficientTrainingDataError
from src.module4.model import QualityValueRanker

if TYPE_CHECKING:
    from src.module3.embeddings import ProductEmbedder
    from src.module3.query_understanding import QueryResult

logger = logging.getLogger(__name__)


class LearningToRankPipeline:
    """Orchestrates fit + rank for quality / value (+ optional query) LTR."""

    def __init__(self, ranker: Optional[QualityValueRanker] = None) -> None:
        self._ranker = ranker or QualityValueRanker()

    @property
    def ranker(self) -> QualityValueRanker:
        return self._ranker

    def fit(
        self,
        products: Optional[Sequence[Product]] = None,
        *,
        X: Optional[np.ndarray] = None,
        labels: Optional[Sequence[int]] = None,
        price_band: Optional[Tuple[float, float]] = None,
        query_result: Optional[QueryResult] = None,
        embedder: Optional[ProductEmbedder] = None,
    ) -> "LearningToRankPipeline":
        """Train the underlying classifier.

        Supply ``X`` for :class:`TrainingDataGenerator` matrices, or ``products``
        + optional ``query_result`` / ``embedder`` for on-the-fly combined features.
        """
        try:
            y = None if labels is None else np.asarray(labels, dtype=np.int64)
            self._ranker.fit(
                products,
                X=X,
                labels=y,
                price_band=price_band,
                query_result=query_result,
                embedder=embedder,
            )
        except InsufficientTrainingDataError as e:
            logger.warning("LTR fit skipped: %s — using heuristic scoring at rank time", e)
        return self

    def rank(
        self,
        products: Sequence[Product],
        *,
        top_k: Optional[int] = None,
        price_band: Optional[Tuple[float, float]] = None,
        query_result: Optional[QueryResult] = None,
        embedder: Optional[ProductEmbedder] = None,
    ) -> List[Tuple[str, float]]:
        """Return ``final_scores`` as ``(product_id, score)`` descending."""
        scored = self._ranker.score(
            products,
            price_band=price_band,
            query_result=query_result,
            embedder=embedder,
        )
        if top_k is not None:
            return scored[: max(0, top_k)]
        return scored

    def fit_rank(
        self,
        products: Sequence[Product],
        *,
        labels: Optional[Sequence[int]] = None,
        price_band: Optional[Tuple[float, float]] = None,
        top_k: Optional[int] = None,
        query_result: Optional[QueryResult] = None,
        embedder: Optional[ProductEmbedder] = None,
    ) -> List[Tuple[str, float]]:
        """Convenience: ``fit`` then ``rank`` on the same candidate set."""
        self.fit(
            products,
            labels=labels,
            price_band=price_band,
            query_result=query_result,
            embedder=embedder,
        )
        return self.rank(
            products,
            top_k=top_k,
            price_band=price_band,
            query_result=query_result,
            embedder=embedder,
        )
