"""
TF-IDF keyword extraction for the query understanding pipeline.

Builds a TF-IDF vocabulary from the product corpus and scores
query tokens against it to surface the most discriminative terms.
"""

import logging
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer

from .tokenizer import tokenize

logger = logging.getLogger(__name__)

MAX_FEATURES = 20_000
MAX_DF = 0.85
MIN_DF = 2


class KeywordExtractor:
    """Extracts ranked keywords from a query using a corpus-fitted TF-IDF model.

    The vectorizer is fitted once on a product corpus, then used at
    query time to score each query token's importance.

    Example:
        >>> kw = KeywordExtractor(["wireless bluetooth headphones", "running shoes"])
        >>> kw.extract("bluetooth headphones for running")
        [('bluetooth', 0.72), ('headphones', 0.69), ('running', 0.43)]
    """

    def __init__(self, corpus_texts: List[str]) -> None:
        """Fit a TF-IDF vectorizer on the product corpus.

        Args:
            corpus_texts: Product text strings (title + description).
        """
        self._vectorizer = TfidfVectorizer(
            max_features=MAX_FEATURES,
            max_df=MAX_DF,
            min_df=MIN_DF,
            sublinear_tf=True,
        )
        try:
            self._vectorizer.fit(corpus_texts)
        except ValueError:
            # Corpus too small/homogeneous for the df thresholds — relax them
            self._vectorizer = TfidfVectorizer(
                max_features=MAX_FEATURES, sublinear_tf=True,
            )
            self._vectorizer.fit(corpus_texts)
        self._vocabulary: Dict[str, int] = self._vectorizer.vocabulary_
        logger.info(
            "KeywordExtractor fitted on %d docs (%d features)",
            len(corpus_texts),
            len(self._vocabulary),
        )

    @property
    def vocabulary_size(self) -> int:
        """Number of terms in the fitted vocabulary."""
        return len(self._vocabulary)

    def extract(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Extract top-k keywords from a query ranked by TF-IDF score.

        Args:
            query: Raw user query string.
            top_k: Maximum keywords to return.

        Returns:
            List of (keyword, score) tuples, descending by score.
            Out-of-vocabulary tokens appear with score 0.
        """
        tokens = tokenize(query)
        if not tokens:
            return []

        tfidf_vec = self._vectorizer.transform([query])
        scores = tfidf_vec.toarray().flatten()

        token_scores: Dict[str, float] = {}
        for token in tokens:
            if token in token_scores:
                continue
            if token in self._vocabulary:
                idx = self._vocabulary[token]
                token_scores[token] = float(scores[idx])
            else:
                token_scores[token] = 0.0

        ranked = sorted(token_scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:top_k]
