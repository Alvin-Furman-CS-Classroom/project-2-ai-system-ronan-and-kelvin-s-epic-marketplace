"""
Shared fixtures for Module 2 integration tests.

Defines catalog, retrieval, and ranker fixtures for end-to-end pipeline tests.
"""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import CandidateRetrieval
from src.module1.filters import SearchFilters
from src.module2.ranker import HeuristicRanker


@pytest.fixture
def ranking_products() -> list[Product]:
    """Products across 3 categories for integration testing."""
    return [
        Product(id="cheap-good", title="Budget Gem", price=10.0, category="electronics", seller_rating=4.8, store="ValueShop", description="x", rating_number=5000, features=["fast"]),
        Product(id="expensive-great", title="Premium Pro", price=99.0, category="electronics", seller_rating=5.0, store="LuxuryTech", description="x" * 50, rating_number=12000, features=["premium"]),
        Product(id="mid-ok", title="Average Joe", price=45.0, category="electronics", seller_rating=3.5, store="ValueShop", description="x", rating_number=200),
        Product(id="cheap-bad", title="Bargain Bin", price=5.0, category="electronics", seller_rating=2.0, store="CheapCo", description=None, rating_number=10),
        Product(id="home-star", title="Cozy Blanket", price=30.0, category="home", seller_rating=4.9, store="HomeHaven", description="x" * 30, rating_number=8000, features=["soft"]),
        Product(id="home-mid", title="Desk Lamp", price=25.0, category="home", seller_rating=4.2, store="HomeHaven", description="x", rating_number=3000),
        Product(id="home-cheap", title="Paper Clips", price=3.0, category="home", seller_rating=3.0, store="CheapCo", description=None, rating_number=50),
        Product(id="book-best", title="AI Textbook", price=55.0, category="books", seller_rating=4.7, store="BookWorld", description="x" * 60, rating_number=1500, features=["hardcover"]),
        Product(id="book-ok", title="Python Intro", price=20.0, category="books", seller_rating=4.0, store="BookWorld", description="x", rating_number=900),
        Product(id="no-reviews", title="Mystery Gadget", price=40.0, category="electronics", seller_rating=3.0, store="ValueShop", description="x", rating_number=0),
        Product(id="no-desc", title="Plain Widget", price=15.0, category="electronics", seller_rating=4.0, store="ValueShop", description=None, rating_number=500),
        Product(id="identical-1", title="Clone A", price=25.0, category="home", seller_rating=4.0, store="HomeHaven", description="x", rating_number=1000),
    ]


@pytest.fixture
def ranking_catalog(ranking_products) -> ProductCatalog:
    """ProductCatalog for integration tests."""
    return ProductCatalog(ranking_products)


@pytest.fixture
def ranking_retrieval(ranking_catalog) -> CandidateRetrieval:
    """CandidateRetrieval wired to the ranking catalog."""
    return CandidateRetrieval(ranking_catalog)


@pytest.fixture
def ranker(ranking_catalog) -> HeuristicRanker:
    """HeuristicRanker wired to the ranking catalog."""
    return HeuristicRanker(ranking_catalog)
