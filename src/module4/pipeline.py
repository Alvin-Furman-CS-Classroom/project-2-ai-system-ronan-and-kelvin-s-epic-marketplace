"""
End-to-end learning-to-rank pipeline (Module 4).

Fits a :class:`QualityValueRanker` on candidate products and exposes
``final_scores`` for integration with Module 1 retrieval and Module 2 heuristics.

Typical use:

1. Retrieve candidates with Module 1 (optionally filtered by price).
2. ``pipeline.fit(products, price_band=(min_price, max_price))`` using the same
   band as the user's search, or ``None`` to normalize only within candidates.
3. ``pipeline.rank(products, top_k=24)`` → ordered ``(id, score)`` for the UI.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Tuple

import numpy as np

from src.module1.catalog import Product
from src.module4.exceptions import InsufficientTrainingDataError
from src.module4.model import QualityValueRanker

logger = logging.getLogger(__name__)


class LearningToRankPipeline:
    """Orchestrates fit + rank for quality / value classification scoring."""

    def __init__(self, ranker: Optional[QualityValueRanker] = None) -> None:
        self._ranker = ranker or QualityValueRanker()

    @property
    def ranker(self) -> QualityValueRanker:
        return self._ranker

    def fit(
        self,
        products: Sequence[Product],
        *,
        labels: Optional[Sequence[int]] = None,
        price_band: Optional[Tuple[float, float]] = None,
    ) -> "LearningToRankPipeline":
        """Train the underlying classifier.

        See :meth:`QualityValueRanker.fit`. On ``InsufficientTrainingDataError``
        (e.g. only one candidate class), the ranker stays **unfitted** and
        :meth:`rank` falls back to heuristic scores.
        """
        try:
            y = None if labels is None else np.asarray(labels, dtype=np.int64)
            self._ranker.fit(products, labels=y, price_band=price_band)
        except InsufficientTrainingDataError as e:
            logger.warning("LTR fit skipped: %s — using heuristic scoring at rank time", e)
        return self

    def rank(
        self,
        products: Sequence[Product],
        *,
        top_k: Optional[int] = None,
        price_band: Optional[Tuple[float, float]] = None,
    ) -> List[Tuple[str, float]]:
        """Return ``final_scores`` as ``(product_id, score)`` descending.

        Args:
            products: Candidates to score (usually the same pool as fit).
            top_k: Optional cap on list length.
            price_band: Optional user price window; defaults to band used at fit.
        """
        scored = self._ranker.score(products, price_band=price_band)
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
    ) -> List[Tuple[str, float]]:
        """Convenience: ``fit`` then ``rank`` on the same candidate set."""
        self.fit(products, labels=labels, price_band=price_band)
        return self.rank(products, top_k=top_k, price_band=price_band)
