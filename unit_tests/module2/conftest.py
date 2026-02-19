"""
Shared pytest fixtures for Module 2 tests.

Provides reusable products, catalogs, search results, and scoring configs
so individual test files stay focused on behaviour, not setup boilerplate.
"""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.filters import SearchFilters
from src.module2.scorer import ScoringConfig
from src.module2.ranker import HeuristicRanker


# ---------------------------------------------------------------------------
# Products with varied features for meaningful scoring differentiation
# ---------------------------------------------------------------------------

@pytest.fixture
def ranking_products() -> list[Product]:
    """Twelve products across 3 categories, 4 stores, with diverse features."""
    return [
        Product(
            id="cheap-good", title="Budget Gem", price=10.0,
            category="electronics", seller_rating=4.8, store="ValueShop",
            description="An affordable product with great reviews.",
            rating_number=5000, features=["fast", "reliable"],
        ),
        Product(
            id="expensive-great", title="Premium Pro", price=99.0,
            category="electronics", seller_rating=5.0, store="LuxuryTech",
            description="Top-of-the-line product with every feature you need." * 3,
            rating_number=12000, features=["premium", "warranty", "fast", "durable"],
        ),
        Product(
            id="mid-ok", title="Average Joe", price=45.0,
            category="electronics", seller_rating=3.5, store="ValueShop",
            description="Gets the job done.",
            rating_number=200,
        ),
        Product(
            id="cheap-bad", title="Bargain Bin", price=5.0,
            category="electronics", seller_rating=2.0, store="CheapCo",
            description=None, rating_number=10,
        ),
        Product(
            id="home-star", title="Cozy Blanket", price=30.0,
            category="home", seller_rating=4.9, store="HomeHaven",
            description="Ultra-soft blanket, perfect for winter evenings.",
            rating_number=8000, features=["soft", "warm", "washable"],
        ),
        Product(
            id="home-mid", title="Desk Lamp", price=25.0,
            category="home", seller_rating=4.2, store="HomeHaven",
            description="LED desk lamp with adjustable brightness.",
            rating_number=3000, features=["LED", "dimmable"],
        ),
        Product(
            id="home-cheap", title="Paper Clips", price=3.0,
            category="home", seller_rating=3.0, store="CheapCo",
            description=None, rating_number=50,
        ),
        Product(
            id="book-best", title="AI Textbook", price=55.0,
            category="books", seller_rating=4.7, store="BookWorld",
            description="Comprehensive guide to artificial intelligence." * 4,
            rating_number=1500, features=["hardcover", "index", "exercises"],
        ),
        Product(
            id="book-ok", title="Python Intro", price=20.0,
            category="books", seller_rating=4.0, store="BookWorld",
            description="Beginner-friendly Python tutorial.",
            rating_number=900,
        ),
        Product(
            id="no-reviews", title="Mystery Gadget", price=40.0,
            category="electronics", seller_rating=3.0, store="ValueShop",
            description="Brand new product, no reviews yet.",
            rating_number=0,
        ),
        Product(
            id="no-desc", title="Plain Widget", price=15.0,
            category="electronics", seller_rating=4.0, store="ValueShop",
            description=None, rating_number=500,
        ),
        Product(
            id="identical-1", title="Clone A", price=25.0,
            category="home", seller_rating=4.0, store="HomeHaven",
            description="Standard product.", rating_number=1000,
        ),
    ]


@pytest.fixture
def ranking_catalog(ranking_products) -> ProductCatalog:
    """ProductCatalog populated with the twelve ranking products."""
    return ProductCatalog(ranking_products)


@pytest.fixture
def ranking_retrieval(ranking_catalog) -> CandidateRetrieval:
    """CandidateRetrieval wired to the ranking catalog."""
    return CandidateRetrieval(ranking_catalog)


@pytest.fixture
def electronics_result(ranking_retrieval) -> SearchResult:
    """SearchResult containing only electronics products."""
    return ranking_retrieval.search(SearchFilters(category="electronics"))


@pytest.fixture
def all_result(ranking_retrieval) -> SearchResult:
    """SearchResult containing all products (no filters)."""
    return ranking_retrieval.search(SearchFilters())


@pytest.fixture
def default_config() -> ScoringConfig:
    """Default scoring configuration."""
    return ScoringConfig()


@pytest.fixture
def ranker(ranking_catalog) -> HeuristicRanker:
    """HeuristicRanker wired to the ranking catalog with default config."""
    return HeuristicRanker(ranking_catalog)
