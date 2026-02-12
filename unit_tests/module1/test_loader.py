"""
Unit tests for the dataset loader.
"""

import gzip
import json
import tempfile
from pathlib import Path

import pytest

from src.module1.loader import compute_seller_ratings, load_catalog
from src.module1.catalog import ProductCatalog, Product


def _write_gzipped_jsonl(path: Path, records: list) -> None:
    """Helper to write records as gzipped JSONL."""
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


class TestComputeSellerRatings:
    """Tests for compute_seller_ratings."""

    def test_computes_average_by_store(self, tmp_path):
        """Should compute average rating per store from reviews."""
        meta_records = [
            {"parent_asin": "A1", "title": "P1", "price": 10.0, "store": "StoreX"},
            {"parent_asin": "A2", "title": "P2", "price": 20.0, "store": "StoreX"},
            {"parent_asin": "A3", "title": "P3", "price": 30.0, "store": "StoreY"},
        ]
        review_records = [
            {"parent_asin": "A1", "rating": 4.0},
            {"parent_asin": "A1", "rating": 5.0},
            {"parent_asin": "A2", "rating": 3.0},
            {"parent_asin": "A3", "rating": 5.0},
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        reviews_path = tmp_path / "reviews.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)
        _write_gzipped_jsonl(reviews_path, review_records)

        ratings = compute_seller_ratings(reviews_path, meta_path)
        assert "StoreX" in ratings
        assert "StoreY" in ratings
        # StoreX: A1 reviews [4, 5], A2 reviews [3] -> all StoreX ratings [4, 5, 3] -> avg 4.0
        # StoreY: A3 reviews [5] -> avg 5.0
        assert ratings["StoreY"] == 5.0
        assert ratings["StoreX"] == 4.0

    def test_ignores_reviews_without_asin_in_meta(self, tmp_path):
        """Should ignore reviews for products not in metadata."""
        meta_records = [
            {"parent_asin": "A1", "title": "P1", "price": 10.0, "store": "StoreX"},
        ]
        review_records = [
            {"parent_asin": "A1", "rating": 5.0},
            {"parent_asin": "A999", "rating": 5.0},  # not in meta
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        reviews_path = tmp_path / "reviews.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)
        _write_gzipped_jsonl(reviews_path, review_records)

        ratings = compute_seller_ratings(reviews_path, meta_path)
        assert "StoreX" in ratings
        assert ratings["StoreX"] == 5.0

    def test_ignores_reviews_without_rating(self, tmp_path):
        """Should ignore reviews missing rating."""
        meta_records = [
            {"parent_asin": "A1", "title": "P1", "price": 10.0, "store": "StoreX"},
        ]
        review_records = [
            {"parent_asin": "A1"},
            {"parent_asin": "A1", "rating": 4.0},
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        reviews_path = tmp_path / "reviews.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)
        _write_gzipped_jsonl(reviews_path, review_records)

        ratings = compute_seller_ratings(reviews_path, meta_path)
        assert ratings["StoreX"] == 4.0

    def test_empty_meta_returns_empty_ratings(self, tmp_path):
        """Should return empty dict when meta has no store/asin pairs."""
        meta_records = []
        review_records = [{"parent_asin": "A1", "rating": 5.0}]
        meta_path = tmp_path / "meta.jsonl.gz"
        reviews_path = tmp_path / "reviews.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)
        _write_gzipped_jsonl(reviews_path, review_records)

        ratings = compute_seller_ratings(reviews_path, meta_path)
        assert ratings == {}


class TestLoadCatalog:
    """Tests for load_catalog."""

    def test_loads_products_from_meta(self, tmp_path):
        """Should load valid products from metadata."""
        meta_records = [
            {
                "parent_asin": "B1",
                "title": "Product 1",
                "price": 19.99,
                "main_category": "Electronics",
                "store": "StoreA",
            },
            {
                "parent_asin": "B2",
                "title": "Product 2",
                "price": 29.99,
                "main_category": "Home",
                "store": "StoreB",
            },
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)

        catalog = load_catalog(meta_path)
        assert len(catalog) == 2
        assert "B1" in catalog
        assert "B2" in catalog
        assert catalog["B1"].title == "Product 1"
        assert catalog["B2"].price == 29.99

    def test_respects_max_products(self, tmp_path):
        """Should stop loading after max_products."""
        meta_records = [
            {"parent_asin": f"B{i}", "title": f"P{i}", "price": 10.0, "main_category": "X", "store": "Y"}
            for i in range(10)
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)

        catalog = load_catalog(meta_path, max_products=3)
        assert len(catalog) == 3

    def test_uses_seller_ratings_when_provided(self, tmp_path):
        """Should use provided seller_ratings over metadata average_rating."""
        meta_records = [
            {
                "parent_asin": "B1",
                "title": "P1",
                "price": 10.0,
                "main_category": "X",
                "store": "MyStore",
                "average_rating": 3.0,
            },
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)

        catalog = load_catalog(meta_path, seller_ratings={"MyStore": 4.8})
        assert catalog["B1"].seller_rating == 4.8

    def test_skips_invalid_products(self, tmp_path):
        """Should skip products missing required fields."""
        meta_records = [
            {"parent_asin": "B1", "title": "P1", "price": 10.0, "main_category": "X", "store": "Y"},
            {"parent_asin": "B2", "title": "P2"},  # missing price
            {"parent_asin": "B3", "title": "P3", "price": 0, "main_category": "X", "store": "Y"},  # invalid
        ]
        meta_path = tmp_path / "meta.jsonl.gz"
        _write_gzipped_jsonl(meta_path, meta_records)

        catalog = load_catalog(meta_path)
        assert len(catalog) == 1
        assert "B1" in catalog


class TestLoadCatalogFromWorkingSet:
    """Tests for load_catalog_from_working_set (requires datasets)."""

    def test_raises_when_meta_not_found(self):
        """Should raise FileNotFoundError when metadata file missing."""
        from src.module1.loader import load_catalog_from_working_set
        with pytest.raises(FileNotFoundError, match="Metadata file not found"):
            load_catalog_from_working_set(working_set_dir="/nonexistent/path")

    def test_loads_from_working_set(self):
        """Should load catalog from datasets/working_set when it exists."""
        from pathlib import Path
        from src.module1.loader import load_catalog_from_working_set

        repo_root = Path(__file__).resolve().parents[2]
        working_set = repo_root / "datasets" / "working_set"
        if not (working_set / "meta_Electronics_50000.jsonl.gz").exists():
            pytest.skip("Working set metadata not found")

        catalog = load_catalog_from_working_set(working_set_dir=working_set, max_products=10)
        assert isinstance(catalog, ProductCatalog)
        assert len(catalog) <= 10
        assert len(catalog) > 0