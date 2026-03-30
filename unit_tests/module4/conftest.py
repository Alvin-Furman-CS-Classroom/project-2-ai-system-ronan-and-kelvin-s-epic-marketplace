"""Fixtures for Module 4 — products with varied quality signals."""

import pytest

from src.module1.catalog import Product


@pytest.fixture
def quality_products() -> list[Product]:
    """Five products: mix of ratings, review counts, and listing depth."""
    long_desc = "x" * 400
    return [
        Product(
            id="cheap_ok",
            title="Budget Gadget",
            price=10.0,
            category="Electronics",
            seller_rating=3.8,
            store="A",
            description="short",
            rating_number=50,
            features=["a"],
        ),
        Product(
            id="mid_strong",
            title="Mid Headphones",
            price=45.0,
            category="Electronics",
            seller_rating=4.6,
            store="B",
            description=long_desc,
            rating_number=2000,
            features=["f1", "f2", "f3", "f4"],
        ),
        Product(
            id="premium",
            title="Premium Headphones",
            price=120.0,
            category="Electronics",
            seller_rating=4.9,
            store="C",
            description=long_desc + "y" * 50,
            rating_number=8000,
            features=["f"] * 8,
        ),
        Product(
            id="bad_reviews",
            title="Noisy Earbuds",
            price=25.0,
            category="Electronics",
            seller_rating=3.2,
            store="D",
            description=long_desc,
            rating_number=40,
            features=["x", "y"],
        ),
        Product(
            id="value_pick",
            title="Value Earbuds",
            price=30.0,
            category="Electronics",
            seller_rating=4.7,
            store="E",
            description=long_desc,
            rating_number=3500,
            features=["a", "b", "c", "d", "e"],
        ),
    ]
