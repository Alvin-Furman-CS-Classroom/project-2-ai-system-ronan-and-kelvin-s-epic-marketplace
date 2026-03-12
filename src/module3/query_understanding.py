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
        raise NotImplementedError("Ronan: implement QueryUnderstanding.__init__")

    def understand(self, query: str) -> QueryResult:
        """Run the full pipeline on a query.

        Args:
            query: Raw user query text.

        Returns:
            QueryResult with keywords, embedding, and inferred category.
        """
        raise NotImplementedError("Ronan: implement QueryUnderstanding.understand")

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
        raise NotImplementedError("Ronan: implement QueryUnderstanding.search_by_text")
