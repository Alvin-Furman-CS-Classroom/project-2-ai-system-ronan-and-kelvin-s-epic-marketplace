# Module 3: Query Understanding
"""
NLP pipeline for query understanding (pre-LLM techniques).

Processes free-text queries through tokenization, keyword extraction,
and word embeddings to produce structured search signals.

Components (Kelvin — NLP Core):
  - tokenizer: text preprocessing, stopword removal, n-gram extraction
  - keywords: TF-IDF keyword extraction against the product corpus
  - embeddings: Word2Vec / GloVe word embeddings and cosine similarity

Components (Ronan — Category Inference + Orchestrator):
  - category_inference: TF-IDF + Logistic Regression category classifier
  - query_understanding: orchestrator combining all components
  - exceptions: module-specific exception types
"""

from .tokenizer import tokenize, extract_ngrams
from .keywords import KeywordExtractor
from .embeddings import ProductEmbedder, EMBEDDING_DIM

__all__ = [
    # Tokenizer
    "tokenize",
    "extract_ngrams",
    # Keywords
    "KeywordExtractor",
    # Embeddings
    "ProductEmbedder",
    "EMBEDDING_DIM",
]
