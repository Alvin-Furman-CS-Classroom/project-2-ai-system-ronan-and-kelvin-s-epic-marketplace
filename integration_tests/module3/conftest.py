"""
Fixtures for Module 3 integration tests.

Builds corpus and labels from product catalog for end-to-end testing.
"""

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module3.query_understanding import QueryUnderstanding


@pytest.fixture
def integration_corpus_and_labels() -> tuple[list[str], list[str]]:
    """Build corpus texts and labels from sample products for integration tests."""
    products = [
        Product(id="p1", title="Wireless Bluetooth Headphones", price=50, category="Electronics", seller_rating=4.5, store="S", description="Noise cancelling over ear"),
        Product(id="p2", title="Running Shoes Lightweight", price=80, category="Sports", seller_rating=4.2, store="S", description="Breathable mesh trail"),
        Product(id="p3", title="Laptop Stand Adjustable", price=35, category="Computers", seller_rating=4.8, store="S", description="Aluminum portable ergonomic"),
        Product(id="p4", title="Mechanical Keyboard RGB", price=120, category="Computers", seller_rating=4.6, store="S", description="Gaming cherry switches"),
        Product(id="p5", title="USB-C Charging Cable", price=12, category="Electronics", seller_rating=4.0, store="S", description="Fast charge braided"),
        Product(id="p6", title="Portable Bluetooth Speaker", price=45, category="Electronics", seller_rating=4.7, store="S", description="Waterproof outdoor bass"),
        Product(id="p7", title="Phone Case Protective", price=15, category="Cell Phones & Accessories", seller_rating=4.1, store="S", description="Shockproof clear slim"),
        Product(id="p8", title="Wireless Mouse Ergonomic", price=30, category="Computers", seller_rating=4.5, store="S", description="Silent click rechargeable"),
        Product(id="p9", title="Monitor Arm Desk Mount", price=60, category="Computers", seller_rating=4.4, store="S", description="Adjustable single dual"),
        Product(id="p10", title="External Hard Drive 1TB", price=90, category="Computers", seller_rating=4.6, store="S", description="Portable storage USB backup"),
    ]
    corpus = []
    labels = []
    for p in products:
        text = f"{p.title} {p.description or ''}".strip()
        corpus.append(text)
        labels.append(p.category)
    return corpus, labels


@pytest.fixture
def integration_query_understanding(integration_corpus_and_labels) -> QueryUnderstanding:
    """QueryUnderstanding built from catalog-like data."""
    corpus, labels = integration_corpus_and_labels
    return QueryUnderstanding(corpus, labels)
