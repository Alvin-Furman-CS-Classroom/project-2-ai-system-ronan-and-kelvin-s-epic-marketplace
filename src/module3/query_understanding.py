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

import logging
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from .accessory_keywords import ACCESSORY_PRODUCT_WORDS
from .category_inference import CategoryClassifier
from .embeddings import EMBEDDING_DIM, ProductEmbedder
from .keywords import KeywordExtractor
from .spell_correction import SpellCorrector
from .tokenizer import tokenize

logger = logging.getLogger(__name__)

QUERY_CACHE_SIZE = 256


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
    corrected_query: Optional[str] = None


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
        self._spell_corrector = SpellCorrector(self._embedder.vocabulary)
        self._cache: OrderedDict[str, QueryResult] = OrderedDict()

    def understand(self, query: str) -> QueryResult:
        """Run the full pipeline on a query.

        Args:
            query: Raw user query text.

        Returns:
            QueryResult with keywords, embedding, and inferred category.
        """
        cache_key = query.strip().lower()
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            logger.debug("Cache hit for query: %s", cache_key)
            return self._cache[cache_key]

        _, suggestion = self._spell_corrector.correct_query(query)

        keywords = self._keyword_extractor.extract(query, top_k=10)
        query_embedding = self._embedder.embed_query(query)

        inferred_category: Optional[str] = None
        confidence = 0.0
        if query and query.strip():
            cat, conf = self._classifier.predict(query)
            inferred_category = cat
            confidence = conf

        result = QueryResult(
            keywords=keywords,
            query_embedding=query_embedding,
            inferred_category=inferred_category,
            confidence=confidence,
            corrected_query=suggestion,
        )

        self._cache[cache_key] = result
        if len(self._cache) > QUERY_CACHE_SIZE:
            self._cache.popitem(last=False)

        return result

    def _expand_query(self, query_tokens: Set[str]) -> str:
        """Expand query with semantically related terms from Word2Vec.

        Adds the top-5 most-similar words for each query token (above a
        cosine threshold) to improve TF-IDF recall for short queries
        like "laptop" that match both products and accessories.
        """
        expanded = list(query_tokens)
        vectors = self._embedder._active_vectors
        vocab = self._keyword_extractor._vocabulary
        for token in query_tokens:
            if token not in vectors:
                continue
            try:
                for word, sim in vectors.most_similar(token, topn=5):
                    if sim > 0.55 and word in vocab:
                        expanded.append(word)
            except KeyError:
                pass
        return " ".join(expanded)

    def search_by_text(
        self,
        query: str,
        texts: Dict[str, str],
        top_k: int = 50,
        titles: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[str, float]]:
        """Rank items by text relevance to a query.

        Blends three signals so that products which *are* the queried
        item rank above accessories *for* that item:

        1. **Embedding cosine** — semantic relatedness (Word2Vec).
        2. **Expanded TF-IDF cosine** — lexical match after query
           expansion with similar Word2Vec terms.
        3. **Title relevance** — how well the query matches the product
           title specifically (when *titles* is provided).

        Args:
            query: Raw user query.
            texts: Mapping of item_id -> full item text (title + description).
            top_k: Maximum results to return.
            titles: Optional mapping of item_id -> title-only text.  When
                provided, a title-relevance signal is blended in to favour
                products whose title directly describes the queried item.

        Returns:
            List of (item_id, relevance_score) tuples, descending.
        """
        if not texts:
            return []

        query_tokens = set(tokenize(query))

        # Signal 1 — embedding cosine (semantic match)
        emb_scores = dict(self._embedder.rank_by_similarity(query, texts))

        # Signal 2 — expanded TF-IDF cosine (lexical match)
        expanded_query = self._expand_query(query_tokens) if query_tokens else query
        q_vec = self._keyword_extractor._vectorizer.transform([expanded_query])
        tfidf_scores: Dict[str, float] = {}
        for item_id, text in texts.items():
            t_vec = self._keyword_extractor._vectorizer.transform([text])
            tfidf_scores[item_id] = float((q_vec @ t_vec.T).toarray()[0, 0])

        # Signal 3 — title-specific relevance (penalises accessory titles)
        title_scores: Dict[str, float] = {}
        if titles and query_tokens:
            for item_id in texts:
                title = titles.get(item_id, "")
                if not title:
                    title_scores[item_id] = 0.0
                    continue
                title_toks = tokenize(title)
                if not title_toks:
                    title_scores[item_id] = 0.0
                    continue
                title_set = set(title_toks)
                matched = sum(1 for qt in query_tokens if qt in title_set)
                coverage = matched / len(query_tokens)
                if coverage == 0:
                    title_scores[item_id] = 0.0
                    continue
                t_vec = self._keyword_extractor._vectorizer.transform([title])
                title_tfidf = float((q_vec @ t_vec.T).toarray()[0, 0])
                # Detect "for/or/with <query>" patterns — accessory signal
                title_lower = title.lower()
                is_for_query = any(
                    f"for {qt}" in title_lower
                    or f"or {qt}" in title_lower
                    or f"compatible {qt}" in title_lower
                    for qt in query_tokens
                )
                non_query = title_set - query_tokens
                is_accessory = bool(non_query & ACCESSORY_PRODUCT_WORDS) or is_for_query
                if is_accessory:
                    title_scores[item_id] = 0.15 * coverage + 0.10 * title_tfidf
                else:
                    title_scores[item_id] = 0.5 * coverage + 0.5 * title_tfidf

        # Blend — title relevance acts as a multiplier so accessories
        # and non-matching products are demoted proportionally.
        combined: List[Tuple[str, float]] = []
        if title_scores:
            for item_id in texts:
                base = (
                    0.30 * emb_scores.get(item_id, 0.0)
                    + 0.70 * tfidf_scores.get(item_id, 0.0)
                )
                title = title_scores.get(item_id, 0.0)
                score = base * (0.03 + 0.97 * title)
                combined.append((item_id, score))
        else:
            for item_id in texts:
                score = (
                    0.35 * emb_scores.get(item_id, 0.0)
                    + 0.65 * tfidf_scores.get(item_id, 0.0)
                )
                combined.append((item_id, score))

        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:top_k]
