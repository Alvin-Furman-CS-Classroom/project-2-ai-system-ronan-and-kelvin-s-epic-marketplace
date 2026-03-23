"""
Query expansion using Word2Vec nearest neighbours.

For each meaningful token in the user's query, finds semantically
similar words from the embedding vocabulary and adds them.  This
broadens recall — e.g. "laptop" also matches products mentioning
"notebook" or "computer".
"""

import logging
from typing import Dict, List, Set, Tuple

from gensim.models import KeyedVectors

from .tokenizer import tokenize

logger = logging.getLogger(__name__)

DEFAULT_TOP_N = 3
MIN_SIMILARITY = 0.45


class QueryExpander:
    """Expands a query with semantically related terms from the embedding space.

    Example:
        >>> qe = QueryExpander(keyed_vectors)
        >>> qe.expand("laptop stand")
        (['laptop', 'stand'], [('notebook', 0.82), ('computer', 0.78), ('holder', 0.71)])
    """

    def __init__(self, vectors: KeyedVectors) -> None:
        """Bind to an existing KeyedVectors instance.

        Args:
            vectors: Trained Word2Vec (or GloVe) KeyedVectors.
        """
        self._vectors = vectors
        logger.info("QueryExpander initialised with %d-word vocabulary", len(vectors))

    def similar_terms(
        self,
        token: str,
        top_n: int = DEFAULT_TOP_N,
        min_sim: float = MIN_SIMILARITY,
    ) -> List[Tuple[str, float]]:
        """Return the most similar vocabulary words to *token*.

        Args:
            token: A single lowercased token.
            top_n: Maximum neighbours to return per token.
            min_sim: Minimum cosine similarity threshold.

        Returns:
            List of (word, similarity) pairs above the threshold.
        """
        if token not in self._vectors:
            return []

        try:
            neighbours = self._vectors.most_similar(token, topn=top_n)
        except KeyError:
            return []

        return [(word, round(sim, 4)) for word, sim in neighbours if sim >= min_sim]

    def expand(
        self,
        query: str,
        top_n: int = DEFAULT_TOP_N,
        min_sim: float = MIN_SIMILARITY,
    ) -> Tuple[List[str], List[Tuple[str, float]]]:
        """Expand a full query with related terms.

        Tokenizes the query, finds neighbours for each token, and
        returns them de-duplicated (excluding the original tokens).

        Args:
            query: Raw user query text.
            top_n: Max neighbours per token.
            min_sim: Minimum cosine similarity to include.

        Returns:
            (original_tokens, expansion_terms) where expansion_terms
            is a list of (word, similarity) pairs sorted by score.
        """
        tokens = tokenize(query)
        if not tokens:
            return [], []

        original_set: Set[str] = set(tokens)
        seen: Dict[str, float] = {}

        for token in tokens:
            for word, sim in self.similar_terms(token, top_n=top_n, min_sim=min_sim):
                if word in original_set:
                    continue
                if word not in seen or sim > seen[word]:
                    seen[word] = sim

        expansions = sorted(seen.items(), key=lambda x: x[1], reverse=True)
        return tokens, expansions
