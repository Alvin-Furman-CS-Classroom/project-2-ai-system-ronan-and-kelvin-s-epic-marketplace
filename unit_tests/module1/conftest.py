"""
Shared pytest fixtures for Module 1 tests.

Provides reusable catalogs and retrieval instances so individual test
files stay focused on behaviour, not setup boilerplate.
"""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import CandidateRetrieval


@pytest.fixture
def sample_products() -> list[Product]:
    """Ten products spanning two categories and three stores."""
    return [
        Product(id="p1", title="Ceramic Mug", price=18.0, category="home", seller_rating=4.8, store="StoreA"),
        Product(id="p2", title="Glass Vase", price=35.0, category="home", seller_rating=4.5, store="StoreA"),
        Product(id="p3", title="Wooden Bowl", price=45.0, category="home", seller_rating=4.2, store="StoreB"),
        Product(id="p4", title="Metal Lamp", price=60.0, category="home", seller_rating=4.9, store="StoreA"),
        Product(id="p5", title="Phone Case", price=15.0, category="electronics", seller_rating=4.0, store="StoreC"),
        Product(id="p6", title="USB Cable", price=8.0, category="electronics", seller_rating=3.8, store="StoreA"),
        Product(id="p7", title="Headphones", price=50.0, category="electronics", seller_rating=4.7, store="StoreB"),
        Product(id="p8", title="Plant Pot", price=22.0, category="home", seller_rating=4.6, store="StoreA"),
        Product(id="p9", title="Candle Set", price=28.0, category="home", seller_rating=4.4, store="StoreC"),
        Product(id="p10", title="Picture Frame", price=12.0, category="home", seller_rating=4.1, store="StoreA"),
    ]


@pytest.fixture
def sample_catalog(sample_products) -> ProductCatalog:
    """ProductCatalog populated with the ten sample products."""
    return ProductCatalog(sample_products)


@pytest.fixture
def retrieval(sample_catalog) -> CandidateRetrieval:
    """CandidateRetrieval wired to the sample catalog."""
    return CandidateRetrieval(sample_catalog)
