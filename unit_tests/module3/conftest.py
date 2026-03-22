"""
Shared pytest fixtures for Module 3 tests.

Provides sample texts, pre-initialized NLP components, and helper data
so individual test files stay focused on behavior, not setup boilerplate.
"""

import nltk
import pytest

# Ensure NLTK data is available for tokenizer
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from src.module3.category_inference import CategoryClassifier
from src.module3.embeddings import ProductEmbedder
from src.module3.keywords import KeywordExtractor
from src.module3.query_understanding import QueryUnderstanding

SAMPLE_CORPUS = [
    "wireless bluetooth headphones noise cancelling over ear",
    "running shoes lightweight breathable mesh trail",
    "laptop stand adjustable aluminum portable ergonomic",
    "mechanical keyboard rgb backlit gaming cherry switches",
    "usb c charging cable fast charge braided nylon",
    "portable bluetooth speaker waterproof outdoor bass",
    "phone case protective shockproof clear slim fit",
    "wireless mouse ergonomic silent click rechargeable",
    "monitor arm desk mount adjustable single dual",
    "external hard drive portable storage usb backup",
    "noise cancelling earbuds wireless bluetooth premium",
    "gaming headset surround sound microphone rgb",
]

# Labels for category classification (one per corpus item)
SAMPLE_LABELS = [
    "audio",
    "footwear",
    "accessories",
    "electronics",
    "accessories",
    "audio",
    "accessories",
    "electronics",
    "accessories",
    "electronics",
    "audio",
    "audio",
]


@pytest.fixture
def sample_corpus() -> list[str]:
    """Twelve product-like text strings for building test models."""
    return list(SAMPLE_CORPUS)


@pytest.fixture
def sample_labels() -> list[str]:
    """Category labels for the sample corpus."""
    return list(SAMPLE_LABELS)


@pytest.fixture
def keyword_extractor(sample_corpus) -> KeywordExtractor:
    """KeywordExtractor fitted on the sample corpus."""
    return KeywordExtractor(sample_corpus)


@pytest.fixture
def product_embedder(sample_corpus) -> ProductEmbedder:
    """ProductEmbedder trained on the sample corpus (Word2Vec only)."""
    return ProductEmbedder(sample_corpus)


@pytest.fixture
def category_classifier(sample_corpus, sample_labels) -> CategoryClassifier:
    """CategoryClassifier trained on the sample corpus."""
    return CategoryClassifier(sample_corpus, sample_labels)


@pytest.fixture
def query_understanding(sample_corpus, sample_labels) -> QueryUnderstanding:
    """QueryUnderstanding with all components initialized."""
    return QueryUnderstanding(sample_corpus, sample_labels)
