"""
Query–product relationship features for learning-to-rank (Module 4).

Bridges Module 3 (query understanding) and Module 4 (LTR) by computing
signals that measure how well a specific product matches a given query:
    - Cosine similarity between query embedding and product text embedding
    - TF-IDF keyword overlap ratio
    - Category match (binary: NLP-inferred category vs. product category)
    - Classifier confidence for the inferred category

These features are concatenated with the product-quality features from
``features.py`` to form the full LTR feature vector.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from src.module1.catalog import Product
from src.module3.accessory_keywords import ACCESSORY_PRODUCT_WORDS
from src.module3.embeddings import ProductEmbedder, _cosine_similarity
from src.module3.query_understanding import QueryResult
from src.module3.tokenizer import tokenize
from src.module4.exceptions import FeatureConstructionError
from src.module4.features import FEATURE_DIM, FEATURE_NAMES

QUERY_FEATURE_NAMES: Tuple[str, ...] = (
    "cosine_similarity",
    "keyword_overlap",
    "category_match",
    "category_confidence",
    "module3_relevance_score",
    "title_relevance",
)

QUERY_FEATURE_DIM = len(QUERY_FEATURE_NAMES)

# Full LTR vector = product-quality (features.py) ∪ query–product signals (this module)
COMBINED_FEATURE_NAMES: Tuple[str, ...] = FEATURE_NAMES + QUERY_FEATURE_NAMES
COMBINED_FEATURE_DIM = len(COMBINED_FEATURE_NAMES)

assert COMBINED_FEATURE_DIM == FEATURE_DIM + QUERY_FEATURE_DIM


def _keyword_overlap(keywords: List[Tuple[str, float]], product: Product) -> float:
    """Fraction of top query keywords found in the product's title + description."""
    if not keywords:
        return 0.0
    product_text = f"{product.title} {product.description or ''}".lower()
    product_tokens = set(tokenize(product_text))
    matched = sum(1 for kw, _ in keywords if kw.lower() in product_tokens)
    return matched / len(keywords)


def _title_relevance(
    query_tokens: Set[str],
    query_embedding: np.ndarray,
    product: Product,
    embedder: ProductEmbedder,
) -> float:
    """How well the query matches the product's title specifically.

    Blends token coverage with embedding similarity against title-only
    text, and penalises titles that contain common accessory-type words
    (e.g. "Laptop **Bag**") so that the actual product ranks higher
    than accessories *for* that product.
    """
    title_tokens = tokenize(product.title)
    if not title_tokens or not query_tokens:
        return 0.0
    title_set = set(title_tokens)
    matched = sum(1 for qt in query_tokens if qt in title_set)
    coverage = matched / len(query_tokens)
    title_emb = embedder.embed_text(product.title)
    title_sim = max(0.0, float(_cosine_similarity(query_embedding, title_emb)))

    title_lower = product.title.lower()
    is_for_query = any(
        f"for {qt}" in title_lower
        or f"or {qt}" in title_lower
        or f"compatible {qt}" in title_lower
        for qt in query_tokens
    )
    non_query = title_set - query_tokens
    if (non_query & ACCESSORY_PRODUCT_WORDS) or is_for_query:
        return 0.25 * coverage + 0.15 * title_sim
    return 0.5 * coverage + 0.5 * title_sim


def compute_query_product_features(
    products: List[Product],
    query_result: QueryResult,
    embedder: ProductEmbedder,
    module3_scores: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """Build a query-product feature matrix.

    Each row corresponds to one product and contains signals measuring
    how well that product matches the query described by *query_result*.

    Columns match ``QUERY_FEATURE_NAMES`` and ``QUERY_FEATURE_DIM``.

    Args:
        products: Candidate products to score against the query.
        query_result: Output of ``QueryUnderstanding.understand()``.
        embedder: The trained ``ProductEmbedder`` used to embed product text.
        module3_scores: Optional mapping of ``product_id -> relevance_score``
            from Module 3's text-ranking pass.  When provided, the score is
            included as the ``module3_relevance_score`` feature so the LTR
            model can refine rather than replace Module 3's ordering.

    Returns:
        ``float64`` array of shape ``(len(products), QUERY_FEATURE_DIM)``.

    Raises:
        FeatureConstructionError: If products list is empty.
    """
    if not products:
        raise FeatureConstructionError("products must not be empty")

    q_emb = query_result.query_embedding
    inferred_cat = (query_result.inferred_category or "").lower()
    confidence = query_result.confidence
    query_tokens = set(kw.lower() for kw, _ in query_result.keywords)

    rows: List[List[float]] = []
    for p in products:
        product_text = f"{p.title} {p.description or ''}"
        p_emb = embedder.embed_text(product_text)

        cos_sim = float(_cosine_similarity(q_emb, p_emb))
        kw_overlap = _keyword_overlap(query_result.keywords, p)
        cat_match = 1.0 if inferred_cat and p.category.lower() == inferred_cat else 0.0
        m3_score = module3_scores.get(p.id, 0.0) if module3_scores else 0.0
        title_rel = _title_relevance(query_tokens, q_emb, p, embedder)

        rows.append([cos_sim, kw_overlap, cat_match, confidence, m3_score, title_rel])

    return np.asarray(rows, dtype=np.float64)


def compute_combined_features(
    products: List[Product],
    query_result: QueryResult,
    embedder: ProductEmbedder,
    price_band: Optional[Tuple[float, float]] = None,
    module3_scores: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """Build the full LTR feature matrix: product-quality + query-product.

    Horizontally concatenates the output of
    ``features.compute_quality_value_features`` and
    ``compute_query_product_features``.

    Args:
        products: Candidate products.
        query_result: Module 3 query analysis output.
        embedder: Trained product embedder for cosine similarity.
        price_band: Optional price window passed to quality features.
        module3_scores: Optional ``{product_id: relevance_score}`` from
            Module 3 text ranking, forwarded to query-product features.

    Returns:
        ``float64`` array of shape ``(len(products), COMBINED_FEATURE_DIM)``.
    """
    from src.module4.features import compute_quality_value_features

    X_quality = compute_quality_value_features(products, price_band=price_band)
    X_query = compute_query_product_features(
        products, query_result, embedder, module3_scores=module3_scores,
    )
    return np.hstack([X_quality, X_query])
