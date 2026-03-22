"""
Orchestrator for the query understanding pipeline.

Combines tokenization, keyword extraction, embeddings, and category
inference into a single QueryUnderstanding class with a unified API.

Owner: Ronan

Dependencies (from Kelvin's NLP core):
    - tokenizer.tokenize(text) -> List[str]
    - KeywordExtractor(corpus_texts).extract(query, top_k) -> List[Tuple[str, float]]
    - ProductEmbedder(corpus_texts).embed_query(query) -> np.ndarray shape (100,)
    - ProductEmbedder.similarity(query, text) -> float
    - ProductEmbedder.rank_by_similarity(query, texts) -> List[Tuple[str, float]]
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .category_inference import CategoryClassifier
from .embeddings import EMBEDDING_DIM, ProductEmbedder
from .keywords import KeywordExtractor


@dataclass
class QueryResult:
    """Output of the query understanding pipeline.

    Attributes:
        keywords: Ranked (keyword, score) pairs from TF-IDF extraction.
        query_embedding: Dense vector representation of the query.
        inferred_category: Predicted product category (or None).
        confidence: Classifier confidence for the inferred category.
    """

    keywords: List[Tuple[str, float]]
    query_embedding: np.ndarray
    inferred_category: Optional[str] = None
    confidence: float = 0.0


class QueryUnderstanding:
    """Orchestrates all query understanding components.

    Wire together:
      - tokenizer.tokenize
      - KeywordExtractor.extract
      - ProductEmbedder.embed_query
      - CategoryClassifier.predict

    Example:
        >>> qu = QueryUnderstanding(corpus_texts, labels)
        >>> result = qu.understand("bluetooth headphones for running")
        >>> result.keywords
        [('bluetooth', 0.72), ('headphones', 0.69), ('running', 0.43)]
        >>> result.query_embedding.shape
        (100,)
        >>> result.inferred_category
        'Portable Audio & Accessories'
    """

    def __init__(self, corpus_texts: List[str], labels: List[str]) -> None:
        """Initialize all pipeline components.

        Args:
            corpus_texts: Product text strings for fitting models.
            labels: Category labels for training the classifier.
        """
        self._keyword_extractor = KeywordExtractor(corpus_texts)
        self._embedder = ProductEmbedder(corpus_texts)
        self._classifier = CategoryClassifier(corpus_texts, labels)

    def understand(self, query: str) -> QueryResult:
        """Run the full pipeline on a query.

        Args:
            query: Raw user query text.

        Returns:
            QueryResult with keywords, embedding, and inferred category.
        """
        keywords = self._keyword_extractor.extract(query, top_k=10)
        query_embedding = self._embedder.embed_query(query)

        inferred_category: Optional[str] = None
        confidence = 0.0
        if query and query.strip():
            cat, conf = self._classifier.predict(query)
            inferred_category = cat
            confidence = conf

        return QueryResult(
            keywords=keywords,
            query_embedding=query_embedding,
            inferred_category=inferred_category,
            confidence=confidence,
        )

    def search_by_text(
        self,
        query: str,
        texts: Dict[str, str],
        top_k: int = 50,
    ) -> List[Tuple[str, float]]:
        """Rank items by text relevance to a query.

        Combines keyword matching and embedding similarity to produce
        a relevance-ranked list of item IDs.

        Args:
            query: Raw user query.
            texts: Mapping of item_id -> item text.
            top_k: Maximum results to return.

        Returns:
            List of (item_id, relevance_score) tuples.
        """
        if not texts:
            return []

        # Use embedding similarity as primary relevance signal
        ranked = self._embedder.rank_by_similarity(query, texts)
        return ranked[:top_k]
