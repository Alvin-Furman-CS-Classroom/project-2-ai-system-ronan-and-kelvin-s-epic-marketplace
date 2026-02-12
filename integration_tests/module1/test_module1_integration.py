"""
Integration tests for Module 1: Candidate Retrieval.

Tests the full workflow: catalog -> filters -> retrieval -> candidate IDs.
"""

from pathlib import Path

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module1.filters import SearchFilters
from src.module1.retrieval import CandidateRetrieval
from src.module1.loader import load_catalog_from_working_set


class TestModule1FullWorkflow:
    """Full workflow: create catalog, apply filters, retrieve candidates."""

    def test_workflow_with_fixture_catalog(self):
        """Full flow with programmatic catalog."""
        products = [
            Product(id="p1", title="Laptop", price=599.0, category="Computers", seller_rating=4.5, store="TechStore"),
            Product(id="p2", title="Mouse", price=25.0, category="Accessories", seller_rating=4.8, store="TechStore"),
            Product(id="p3", title="Keyboard", price=89.0, category="Accessories", seller_rating=4.2, store="OfficeCo"),
            Product(id="p4", title="Monitor", price=199.0, category="Displays", seller_rating=4.6, store="TechStore"),
            Product(id="p5", title="USB Hub", price=15.0, category="Accessories", seller_rating=4.9, store="OfficeCo"),
        ]
        catalog = ProductCatalog(products)
        retrieval = CandidateRetrieval(catalog)

        filters = SearchFilters(
            price_min=20.0,
            price_max=200.0,
            category="Accessories",
            min_seller_rating=4.5,
            sort_by="price_asc",
        )
        candidates = retrieval.search(filters)

        # p2: 25, Accessories, 4.8 ✓. p5: 15 (below min 20) ✗. p3: rating 4.2 ✗.
        assert set(candidates) == {"p2"}
        assert candidates[0] == "p2"

    def test_workflow_with_dict_filters(self):
        """Filters from dict (README spec format)."""
        products = [
            Product(id="a1", title="Mug", price=18.0, category="home", seller_rating=4.8, store="StoreA"),
            Product(id="a2", title="Vase", price=35.0, category="home", seller_rating=4.5, store="StoreA"),
            Product(id="a3", title="Case", price=15.0, category="electronics", seller_rating=4.0, store="StoreB"),
        ]
        catalog = ProductCatalog(products)
        retrieval = CandidateRetrieval(catalog)

        filters = SearchFilters.from_dict({
            "price": [10, 40],
            "category": "home",
            "seller_rating": ">=4.5",
            "sort_by": "price_asc",
        })
        candidates = retrieval.search(filters)

        assert set(candidates) == {"a1", "a2"}
        assert candidates == ["a1", "a2"]  # 18 before 35

    def test_workflow_candidates_feed_next_module(self):
        """Candidate IDs structure matches Module 2 input spec."""
        products = [
            Product(id="p12", title="X", price=20.0, category="home", seller_rating=4.5, store="A"),
            Product(id="p89", title="Y", price=30.0, category="home", seller_rating=4.5, store="A"),
            Product(id="p203", title="Z", price=25.0, category="home", seller_rating=4.5, store="A"),
        ]
        catalog = ProductCatalog(products)
        retrieval = CandidateRetrieval(catalog)

        filters = SearchFilters(category="home", sort_by="price_asc")
        candidate_ids = retrieval.search(filters)

        assert isinstance(candidate_ids, list)
        assert all(isinstance(pid, str) for pid in candidate_ids)
        assert candidate_ids == ["p12", "p203", "p89"]


class TestModule1WithRealData:
    """Integration with real working set data (when available)."""

    def test_load_and_search_working_set(self):
        """Load catalog from working set and run search."""
        repo_root = Path(__file__).resolve().parents[2]
        working_set = repo_root / "datasets" / "working_set"
        if not (working_set / "meta_Electronics_50000.jsonl.gz").exists():
            pytest.skip("Working set not found")

        catalog = load_catalog_from_working_set(working_set_dir=working_set, max_products=100)
        assert len(catalog) > 0

        retrieval = CandidateRetrieval(catalog)

        # Filter by category if we have known categories
        categories = catalog.categories
        if categories:
            filters = SearchFilters(
                category=categories[0],
                price_max=1000.0,
                sort_by="price_asc",
            )
            candidates = retrieval.search(filters, max_results=5)
            assert isinstance(candidates, list)
            assert len(candidates) <= 5
            for pid in candidates:
                assert pid in catalog
