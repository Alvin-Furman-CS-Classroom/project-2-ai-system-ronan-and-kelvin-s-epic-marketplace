"""
Integration tests for Module 3 — query understanding pipeline.

Owner: Ronan

Tests:
  - Full pipeline: query -> Module 3 understand() -> valid output
  - Inferred category is from training labels
  - Text-based search returns relevant results
  - Query understanding output can feed Module 2 (target_category)
"""

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import CandidateRetrieval
from src.module1.filters import SearchFilters
from src.module2.ranker import HeuristicRanker
from src.module3.query_understanding import QueryUnderstanding


class TestModule3Integration:
    """Integration tests for Module 3 pipeline."""

    def test_full_pipeline_query_to_result(self, integration_query_understanding):
        """Full pipeline: query -> understand() -> valid QueryResult."""
        result = integration_query_understanding.understand("bluetooth headphones wireless")
        assert result.keywords
        assert result.query_embedding.shape == (100,)
        assert result.inferred_category in {
            "Electronics",
            "Computers",
            "Cell Phones & Accessories",
            "Sports",
        }
        assert 0 <= result.confidence <= 1

    def test_inferred_category_from_training_labels(self, integration_query_understanding):
        """Inferred category is one of the training labels."""
        valid = {"Electronics", "Computers", "Cell Phones & Accessories", "Sports"}
        result = integration_query_understanding.understand("mechanical keyboard gaming")
        assert result.inferred_category in valid

    def test_search_by_text_returns_relevant_order(self, integration_query_understanding):
        """search_by_text returns items ranked by relevance."""
        texts = {
            "headphones": "Wireless Bluetooth Headphones Noise cancelling",
            "shoes": "Running Shoes Lightweight Breathable",
            "keyboard": "Mechanical Keyboard RGB Gaming",
        }
        ranked = integration_query_understanding.search_by_text("bluetooth headphones", texts, top_k=5)
        assert ranked[0][0] == "headphones"
        assert len(ranked) == 3


class TestModule3FeedsModule2:
    """Verify Module 3 output feeds into Module 2 (target_category)."""

    @pytest.fixture
    def catalog_with_categories(self) -> ProductCatalog:
        """Catalog with products in Electronics, Computers, home."""
        products = [
            Product(id="e1", title="Bluetooth Headphones", price=50, category="Electronics", seller_rating=4.5, store="S"),
            Product(id="e2", title="Wireless Speaker", price=40, category="Electronics", seller_rating=4.3, store="S"),
            Product(id="c1", title="Laptop Stand", price=35, category="Computers", seller_rating=4.8, store="S"),
            Product(id="h1", title="Desk Lamp", price=25, category="home", seller_rating=4.2, store="S"),
        ]
        return ProductCatalog(products)

    def test_inferred_category_feeds_ranker(
        self, catalog_with_categories, integration_corpus_and_labels
    ):
        """Inferred category from Module 3 can be passed to Module 2 ranker."""
        corpus, labels = integration_corpus_and_labels
        qu = QueryUnderstanding(corpus, labels)
        result = qu.understand("bluetooth headphones")
        inferred = result.inferred_category

        retrieval = CandidateRetrieval(catalog_with_categories)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(catalog_with_categories)
        ranked = ranker.rank(
            search_result,
            strategy="baseline",
            target_category=inferred,
            k=5,
        )
        assert len(ranked) > 0
        assert ranked.strategy == "baseline"
