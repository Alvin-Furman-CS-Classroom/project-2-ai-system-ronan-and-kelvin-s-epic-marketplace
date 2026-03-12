"""
Word embedding module for the query understanding pipeline.

Provides two embedding sources:
  1. Custom Word2Vec — trained on the product corpus at init time.
  2. Pre-trained GloVe — loaded from disk if available (optional).

Query/product embeddings are produced by averaging the word vectors
for all tokens in the text, then ranked via cosine similarity.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from gensim.models import Word2Vec, KeyedVectors

from .tokenizer import tokenize

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 100

W2V_WINDOW = 5
W2V_MIN_COUNT = 2
W2V_EPOCHS = 10
W2V_WORKERS = 4
W2V_SG = 1  # skip-gram

GLOVE_DIR = Path(__file__).resolve().parent.parent.parent / "datasets" / "ignored"
GLOVE_FILENAME = "glove.6B.100d.txt"


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors, safe against zero-norm."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class ProductEmbedder:
    """Generates and compares embeddings for queries and product text.

    Trains a Word2Vec model on the product corpus and optionally loads
    pre-trained GloVe vectors.  Embeddings are produced by averaging
    the word vectors for every in-vocabulary token in the input.

    Example:
        >>> emb = ProductEmbedder(["wireless bluetooth headphones", "running shoes"])
        >>> emb.embed_query("bluetooth earbuds").shape
        (100,)
        >>> emb.similarity("bluetooth earbuds", "wireless headphones")
        0.87
    """

    def __init__(
        self,
        corpus_texts: List[str],
        glove_path: Optional[str] = None,
        use_glove: bool = False,
    ) -> None:
        """Train Word2Vec on the corpus and optionally load GloVe.

        Args:
            corpus_texts: Product text strings for Word2Vec training.
            glove_path: Path to glove.6B.100d.txt (None = default location).
            use_glove: If True and GloVe file exists, prefer GloVe vectors.
        """
        tokenized_corpus = [tokenize(text) for text in corpus_texts]
        tokenized_corpus = [t for t in tokenized_corpus if t]

        logger.info("Training Word2Vec on %d documents...", len(tokenized_corpus))
        self._w2v_model = Word2Vec(
            sentences=tokenized_corpus,
            vector_size=EMBEDDING_DIM,
            window=W2V_WINDOW,
            min_count=W2V_MIN_COUNT,
            epochs=W2V_EPOCHS,
            workers=W2V_WORKERS,
            sg=W2V_SG,
        )
        self._w2v_vectors: KeyedVectors = self._w2v_model.wv
        logger.info("Word2Vec trained — vocab size: %d", len(self._w2v_vectors))

        self._glove_vectors: Optional[KeyedVectors] = None
        if use_glove:
            self._glove_vectors = self._load_glove(glove_path)

        self._active_vectors: KeyedVectors = (
            self._glove_vectors if self._glove_vectors is not None else self._w2v_vectors
        )

    # ------------------------------------------------------------------
    # GloVe loader
    # ------------------------------------------------------------------

    def _load_glove(self, path: Optional[str]) -> Optional[KeyedVectors]:
        """Try to load GloVe vectors from disk; return None on failure."""
        if path is None:
            path = str(GLOVE_DIR / GLOVE_FILENAME)

        if not os.path.isfile(path):
            logger.warning("GloVe not found at %s — using Word2Vec only", path)
            return None

        logger.info("Loading GloVe from %s ...", path)
        vectors = KeyedVectors.load_word2vec_format(
            path, binary=False, no_header=True,
        )
        logger.info("GloVe loaded — vocab size: %d", len(vectors))
        return vectors

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def vocabulary_size(self) -> int:
        """Number of words in the active embedding vocabulary."""
        return len(self._active_vectors)

    @property
    def using_glove(self) -> bool:
        """Whether the active vectors are GloVe (True) or Word2Vec (False)."""
        return (
            self._glove_vectors is not None
            and self._active_vectors is self._glove_vectors
        )

    # ------------------------------------------------------------------
    # Core embedding helpers
    # ------------------------------------------------------------------

    def _average_embedding(self, tokens: List[str]) -> np.ndarray:
        """Average word vectors for a list of tokens.

        Out-of-vocabulary tokens are silently skipped.
        Returns a zero vector if no tokens are found.
        """
        vectors = [
            self._active_vectors[t]
            for t in tokens
            if t in self._active_vectors
        ]
        if not vectors:
            return np.zeros(EMBEDDING_DIM, dtype=np.float32)
        return np.mean(vectors, axis=0).astype(np.float32)

    # ------------------------------------------------------------------
    # Public API (matches the Interface Contract in the plan)
    # ------------------------------------------------------------------

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a raw query string into a fixed-size vector.

        Args:
            query: Raw user query text.

        Returns:
            numpy array of shape (EMBEDDING_DIM,).
        """
        return self._average_embedding(tokenize(query))

    def embed_text(self, text: str) -> np.ndarray:
        """Embed arbitrary text into a fixed-size vector.

        Args:
            text: Any text string (product title, description, etc.).

        Returns:
            numpy array of shape (EMBEDDING_DIM,).
        """
        return self._average_embedding(tokenize(text))

    def similarity(self, query: str, text: str) -> float:
        """Cosine similarity between a query and a text string.

        Returns 0 if either embedding is a zero vector.
        """
        return _cosine_similarity(self.embed_query(query), self.embed_text(text))

    def rank_by_similarity(
        self,
        query: str,
        texts: Dict[str, str],
    ) -> List[Tuple[str, float]]:
        """Rank texts by cosine similarity to the query.

        Args:
            query: Raw user query.
            texts: Mapping of ID -> text to rank.

        Returns:
            List of (id, similarity) sorted descending.
        """
        q_vec = self.embed_query(query)
        scored: List[Tuple[str, float]] = [
            (item_id, _cosine_similarity(q_vec, self.embed_text(text)))
            for item_id, text in texts.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
