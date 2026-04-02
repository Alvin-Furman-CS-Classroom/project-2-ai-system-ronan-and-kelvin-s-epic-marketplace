"""
Synthetic training data generator for learning-to-rank (Module 4).

Since we don't have real click-through or conversion data, this module
generates relevance labels by combining multiple independent signals:
cosine similarity, category match, keyword overlap, rating, and review
volume.  A weighted composite with added noise produces realistic
(features, label) pairs for training the LTR classifier.

The label formula intentionally differs from the feature set so the
model learns a non-trivial mapping rather than copying a single column.
"""

from __future__ import annotations

import logging
import random
from typing import List, Optional, Tuple

import numpy as np

from src.module1.catalog import Product, ProductCatalog
from src.module3.embeddings import ProductEmbedder, _cosine_similarity
from src.module3.query_understanding import QueryUnderstanding, QueryResult
from src.module3.tokenizer import tokenize
from src.module4.exceptions import InsufficientTrainingDataError

logger = logging.getLogger(__name__)

SAMPLE_QUERIES = [
    "bluetooth headphones noise cancelling",
    "usb c hub adapter laptop",
    "gaming keyboard mechanical rgb",
    "wireless mouse ergonomic",
    "phone case protective clear",
    "laptop stand adjustable desk",
    "portable speaker waterproof",
    "webcam hd streaming",
    "fitness tracker heart rate",
    "external ssd portable storage",
    "screen protector tempered glass",
    "charging cable fast charge",
    "monitor stand desk organizer",
    "camera tripod lightweight",
    "smart watch fitness",
    "desk lamp led wireless",
    "earbuds wireless budget",
    "hdmi cable 4k",
    "keyboard mouse combo wireless",
    "camera bag backpack waterproof",
]

_LABEL_WEIGHTS = {
    "cosine_sim": 0.30,
    "category_match": 0.25,
    "keyword_overlap": 0.15,
    "rating_norm": 0.15,
    "review_strength": 0.10,
    "noise": 0.05,
}


def _keyword_overlap_ratio(
    keywords: List[Tuple[str, float]], product: Product
) -> float:
    """Fraction of query keywords appearing in product text."""
    if not keywords:
        return 0.0
    text_tokens = set(tokenize(f"{product.title} {product.description or ''}"))
    matched = sum(1 for kw, _ in keywords if kw.lower() in text_tokens)
    return matched / len(keywords)


class TrainingDataGenerator:
    """Generates synthetic (features, labels) pairs for LTR training.

    Uses a set of representative queries, runs them through Module 3,
    and scores each (query, product) pair to produce a relevance label.
    The feature matrix is built with the combined quality + query features.

    Args:
        catalog: Product catalog to sample candidates from.
        query_understanding: Trained Module 3 orchestrator.
        embedder: Trained product embedder (for cosine similarity).
        sample_queries: Optional custom query list; defaults to built-in set.
    """

    def __init__(
        self,
        catalog: ProductCatalog,
        query_understanding: QueryUnderstanding,
        embedder: ProductEmbedder,
        sample_queries: Optional[List[str]] = None,
    ) -> None:
        self._catalog = catalog
        self._qu = query_understanding
        self._embedder = embedder
        self._queries = sample_queries or SAMPLE_QUERIES

    def generate(
        self,
        max_products_per_query: int = 50,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate the full training dataset.

        For each sample query, selects up to *max_products_per_query*
        products, builds combined features, and computes a binary
        relevance label via a weighted composite + noise.

        Args:
            max_products_per_query: Cap on products scored per query.
            seed: Random seed for reproducibility.

        Returns:
            ``(X, y)`` where ``X`` has shape ``(n_samples, feature_dim)``
            and ``y`` has shape ``(n_samples,)`` with binary ``{0, 1}``.

        Raises:
            InsufficientTrainingDataError: If fewer than 4 examples
                are generated (need at least 2 per class for fitting).
        """
        from src.module4.query_features import compute_combined_features

        rng = random.Random(seed)
        all_products = list(self._catalog)

        X_parts: List[np.ndarray] = []
        y_parts: List[np.ndarray] = []

        for query in self._queries:
            qr: QueryResult = self._qu.understand(query)

            if max_products_per_query < len(all_products):
                sample = rng.sample(all_products, max_products_per_query)
            else:
                sample = list(all_products)

            if len(sample) < 2:
                continue

            X_batch = compute_combined_features(
                sample, qr, self._embedder, price_band=None,
            )

            scores = self._compute_relevance_scores(qr, sample, rng)
            median = float(np.median(scores))
            y_batch = (scores >= median).astype(np.int64)

            X_parts.append(X_batch)
            y_parts.append(y_batch)

        if not X_parts:
            raise InsufficientTrainingDataError(
                "no training examples generated — check catalog and queries"
            )

        X = np.vstack(X_parts)
        y = np.concatenate(y_parts)

        if X.shape[0] < 4:
            raise InsufficientTrainingDataError(
                f"only {X.shape[0]} examples generated — need at least 4"
            )

        logger.info(
            "Training data: %d examples, %d features, positive rate %.2f",
            X.shape[0], X.shape[1], float(np.mean(y)),
        )
        return X, y

    def _compute_relevance_scores(
        self,
        qr: QueryResult,
        products: List[Product],
        rng: random.Random,
    ) -> np.ndarray:
        """Weighted composite relevance score for each product."""
        q_emb = qr.query_embedding
        inferred_cat = (qr.inferred_category or "").lower()

        scores = np.zeros(len(products), dtype=np.float64)
        for i, p in enumerate(products):
            p_text = f"{p.title} {p.description or ''}"
            p_emb = self._embedder.embed_text(p_text)

            cos_sim = float(_cosine_similarity(q_emb, p_emb))
            cat_match = 1.0 if inferred_cat and p.category.lower() == inferred_cat else 0.0
            kw_overlap = _keyword_overlap_ratio(qr.keywords, p)
            rating_norm = p.seller_rating / 5.0
            review_strength = float(np.log1p(p.rating_number or 0)) / 12.0
            noise = rng.gauss(0, 0.1)

            scores[i] = (
                _LABEL_WEIGHTS["cosine_sim"] * cos_sim
                + _LABEL_WEIGHTS["category_match"] * cat_match
                + _LABEL_WEIGHTS["keyword_overlap"] * kw_overlap
                + _LABEL_WEIGHTS["rating_norm"] * rating_norm
                + _LABEL_WEIGHTS["review_strength"] * review_strength
                + _LABEL_WEIGHTS["noise"] * noise
            )

        return scores
