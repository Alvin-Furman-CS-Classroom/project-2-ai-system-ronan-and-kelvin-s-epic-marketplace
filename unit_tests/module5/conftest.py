"""Fixtures for Module 5 — evaluation metrics, held-out data, payloads."""

import pytest

from src.module1.catalog import Product, ProductCatalog


@pytest.fixture
def sample_products() -> list[Product]:
    """Six products spanning two categories."""
    return [
        Product(id="p1", title="Bluetooth Headphones", price=45.0,
                category="Electronics", seller_rating=4.8, store="AudioCo",
                description="Wireless noise cancelling", rating_number=3000),
        Product(id="p2", title="USB-C Hub", price=30.0,
                category="Electronics", seller_rating=4.5, store="TechShop",
                description="7-port adapter", rating_number=1500),
        Product(id="p3", title="Phone Case", price=12.0,
                category="Cell Phones", seller_rating=4.2, store="CaseCo",
                description="Clear protective", rating_number=800),
        Product(id="p4", title="Webcam HD", price=55.0,
                category="Electronics", seller_rating=4.6, store="StreamCo",
                description="1080p streaming camera", rating_number=2200),
        Product(id="p5", title="HDMI Cable", price=10.0,
                category="Electronics", seller_rating=4.0, store="CableCo",
                description="4K high speed", rating_number=5000),
        Product(id="p6", title="Screen Protector", price=8.0,
                category="Cell Phones", seller_rating=3.9, store="ProtectCo",
                description="Tempered glass", rating_number=600),
    ]


@pytest.fixture
def sample_catalog(sample_products) -> ProductCatalog:
    return ProductCatalog(sample_products)


@pytest.fixture
def perfect_ranking() -> list[str]:
    """Ranked IDs where all top items are relevant."""
    return ["p1", "p2", "p4", "p3", "p5", "p6"]


@pytest.fixture
def relevant_set() -> set[str]:
    """Ground-truth relevant items."""
    return {"p1", "p2", "p4"}


@pytest.fixture
def scored_candidates() -> list[tuple[str, float]]:
    """Module 4 style scored output."""
    return [
        ("p1", 0.92),
        ("p4", 0.85),
        ("p2", 0.78),
        ("p3", 0.60),
        ("p5", 0.45),
        ("p6", 0.30),
    ]
