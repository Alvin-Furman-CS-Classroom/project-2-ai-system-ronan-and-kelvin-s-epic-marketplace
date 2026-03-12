"""
Shared pytest fixtures for Module 3 tests.

Provides sample texts, pre-initialized NLP components, and helper data
so individual test files stay focused on behavior, not setup boilerplate.
"""

import pytest

from src.module3.keywords import KeywordExtractor
from src.module3.embeddings import ProductEmbedder

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


@pytest.fixture
def sample_corpus() -> list[str]:
    """Twelve product-like text strings for building test models."""
    return list(SAMPLE_CORPUS)


@pytest.fixture
def keyword_extractor(sample_corpus) -> KeywordExtractor:
    """KeywordExtractor fitted on the sample corpus."""
    return KeywordExtractor(sample_corpus)


@pytest.fixture
def product_embedder(sample_corpus) -> ProductEmbedder:
    """ProductEmbedder trained on the sample corpus (Word2Vec only)."""
    return ProductEmbedder(sample_corpus)
