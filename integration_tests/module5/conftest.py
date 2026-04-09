"""Fixtures for Module 5 integration tests (full pipeline evaluation)."""

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module1.filters import SearchFilters
from src.module1.retrieval import CandidateRetrieval
from src.module2.ranker import HeuristicRanker
from src.module4.pipeline import LearningToRankPipeline
from src.module5.holdout import HeldOutSet


@pytest.fixture
def integration_products() -> list[Product]:
    """Eight products for end-to-end integration testing."""
    desc = "x" * 200
    return [
        Product(id="p1", title="Bluetooth Headphones", price=45.0,
                category="Electronics", seller_rating=4.8, store="AudioCo",
                description=desc, rating_number=3000, features=["wireless", "anc"]),
        Product(id="p2", title="USB-C Hub Adapter", price=30.0,
                category="Electronics", seller_rating=4.5, store="TechShop",
                description=desc, rating_number=1500, features=["7-port"]),
        Product(id="p3", title="Phone Case Clear", price=12.0,
                category="Cell Phones", seller_rating=4.2, store="CaseCo",
                description=desc, rating_number=800, features=["clear"]),
        Product(id="p4", title="Webcam HD 1080p", price=55.0,
                category="Electronics", seller_rating=4.6, store="StreamCo",
                description=desc, rating_number=2200, features=["hd", "autofocus"]),
        Product(id="p5", title="HDMI Cable 4K", price=10.0,
                category="Electronics", seller_rating=4.0, store="CableCo",
                description=desc, rating_number=5000, features=["4k"]),
        Product(id="p6", title="Screen Protector Glass", price=8.0,
                category="Cell Phones", seller_rating=3.9, store="ProtectCo",
                description=desc, rating_number=600, features=["tempered"]),
        Product(id="p7", title="Wireless Mouse Ergonomic", price=25.0,
                category="Electronics", seller_rating=4.4, store="ClickCo",
                description=desc, rating_number=1800, features=["ergonomic"]),
        Product(id="p8", title="Laptop Stand Adjustable", price=35.0,
                category="Electronics", seller_rating=4.7, store="DeskCo",
                description=desc, rating_number=2500, features=["adjustable"]),
    ]


@pytest.fixture
def integration_catalog(integration_products) -> ProductCatalog:
    return ProductCatalog(integration_products)


@pytest.fixture
def integration_holdout() -> HeldOutSet:
    return HeldOutSet({
        "bluetooth headphones": {"p1"},
        "usb hub adapter": {"p2"},
        "webcam streaming": {"p4"},
        "general electronics": {"p1", "p2", "p4", "p5", "p7", "p8"},
    })
