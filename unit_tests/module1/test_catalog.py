"""
Unit tests for Product and ProductCatalog.
"""

import pytest
from src.module1.catalog import Product, ProductCatalog
from src.module1.exceptions import ProductValidationError, ProductNotFoundError


class TestProduct:
    """Tests for Product class."""
    
    def test_create_product(self):
        """Should create a product with required fields."""
        product = Product(
            id="B07BJ7ZZL7",
            title="Silicone Watch Band",
            price=14.89,
            category="Cell Phones & Accessories",
            seller_rating=4.4,
            store="QGHXO"
        )
        assert product.id == "B07BJ7ZZL7"
        assert product.title == "Silicone Watch Band"
        assert product.price == 14.89
        assert product.category == "Cell Phones & Accessories"
        assert product.seller_rating == 4.4
        assert product.store == "QGHXO"
        assert product.description is None
        assert product.tags is None
        assert product.image_url is None
    
    def test_create_product_with_optional_fields(self):
        """Should accept optional description, tags, image_url, etc."""
        product = Product(
            id="p1",
            title="Test Product",
            price=10.0,
            category="Electronics",
            seller_rating=4.0,
            store="TestStore",
            description="A test product",
            tags=["Electronics", "Gadgets"],
            image_url="https://example.com/img.jpg",
            rating_number=500,
            features=["Feature 1", "Feature 2"]
        )
        assert product.description == "A test product"
        assert product.tags == ["Electronics", "Gadgets"]
        assert product.image_url == "https://example.com/img.jpg"
        assert product.rating_number == 500
        assert product.features == ["Feature 1", "Feature 2"]
    
    def test_invalid_negative_price(self):
        """Should reject negative price."""
        with pytest.raises(ProductValidationError, match="Price cannot be negative"):
            Product(
                id="p1", title="Test", price=-5.0,
                category="test", seller_rating=4.0, store="X"
            )
    
    def test_invalid_seller_rating_too_high(self):
        """Should reject seller rating > 5."""
        with pytest.raises(ProductValidationError, match="Seller rating must be 0-5"):
            Product(
                id="p1", title="Test", price=10.0,
                category="test", seller_rating=5.5, store="X"
            )
    
    def test_invalid_seller_rating_negative(self):
        """Should reject negative seller rating."""
        with pytest.raises(ProductValidationError, match="Seller rating must be 0-5"):
            Product(
                id="p1", title="Test", price=10.0,
                category="test", seller_rating=-1.0, store="X"
            )
    
    def test_product_from_dict(self):
        """Should create product from dictionary."""
        data = {
            "id": "p1",
            "title": "Test Product",
            "price": 25.0,
            "category": "Computers",
            "seller_rating": 4.5,
            "store": "Anker",
            "description": "Great product",
            "tags": ["Electronics", "Gadgets"],
            "image_url": "https://example.com/img.jpg",
            "rating_number": 100,
            "features": ["Fast charging"],
        }
        product = Product.from_dict(data)
        assert product.id == "p1"
        assert product.store == "Anker"
        assert product.image_url == "https://example.com/img.jpg"
        assert product.rating_number == 100
        assert product.features == ["Fast charging"]
    
    def test_product_to_dict(self):
        """Should convert product to dictionary."""
        product = Product(
            id="p1", title="Test", price=10.0,
            category="test", seller_rating=4.0, store="X",
            description="A test", tags=["t1"]
        )
        result = product.to_dict()
        assert result["id"] == "p1"
        assert result["title"] == "Test"
        assert result["price"] == 10.0
        assert result["category"] == "test"
        assert result["seller_rating"] == 4.0
        assert result["store"] == "X"
        assert result["description"] == "A test"
        assert result["tags"] == ["t1"]
    
    def test_product_to_dict_without_optional(self):
        """Should omit None optional fields in to_dict."""
        product = Product(
            id="p1", title="Test", price=10.0,
            category="test", seller_rating=4.0, store="X"
        )
        result = product.to_dict()
        assert "description" not in result
        assert "tags" not in result
        assert "image_url" not in result
        assert "rating_number" not in result
        assert "features" not in result


class TestProductFromAmazonMeta:
    """Tests for Product.from_amazon_meta()."""
    
    def test_from_amazon_meta_basic(self):
        """Should create product from Amazon metadata."""
        meta = {
            "parent_asin": "B07BJ7ZZL7",
            "title": "Watch Band",
            "price": 14.89,
            "main_category": "Cell Phones & Accessories",
            "average_rating": 4.4,
            "store": "QGHXO",
            "rating_number": 707,
            "categories": ["Electronics", "Wearable Technology"],
            "description": ["Great band", "for your watch"],
            "features": ["Soft silicone", "Easy install"],
            "images": [{"large": "https://example.com/img.jpg"}],
        }
        product = Product.from_amazon_meta(meta)
        assert product is not None
        assert product.id == "B07BJ7ZZL7"
        assert product.title == "Watch Band"
        assert product.price == 14.89
        assert product.category == "Cell Phones & Accessories"
        assert product.seller_rating == 4.4
        assert product.store == "QGHXO"
        assert product.image_url == "https://example.com/img.jpg"
        assert product.tags == ["Electronics", "Wearable Technology"]
        assert product.description == "Great band for your watch"
        assert product.features == ["Soft silicone", "Easy install"]
    
    def test_from_amazon_meta_with_seller_rating(self):
        """Should use provided seller_rating over average_rating."""
        meta = {
            "parent_asin": "B123",
            "title": "Test",
            "price": 10.0,
            "main_category": "Electronics",
            "average_rating": 3.0,
            "store": "TestStore",
        }
        product = Product.from_amazon_meta(meta, seller_rating=4.5)
        assert product.seller_rating == 4.5
    
    def test_from_amazon_meta_missing_price(self):
        """Should return None when price is missing."""
        meta = {"parent_asin": "B123", "title": "Test", "store": "X"}
        product = Product.from_amazon_meta(meta)
        assert product is None
    
    def test_from_amazon_meta_zero_price(self):
        """Should return None when price is zero."""
        meta = {"parent_asin": "B123", "title": "Test", "price": 0, "store": "X"}
        product = Product.from_amazon_meta(meta)
        assert product is None
    
    def test_from_amazon_meta_missing_title(self):
        """Should return None when title is missing."""
        meta = {"parent_asin": "B123", "price": 10.0, "store": "X"}
        product = Product.from_amazon_meta(meta)
        assert product is None


class TestProductCatalog:
    """Tests for ProductCatalog class."""
    
    @pytest.fixture
    def sample_products(self):
        """Sample products for testing."""
        return [
            Product(id="p1", title="Mug", price=15.0, category="home", seller_rating=4.5, store="StoreA"),
            Product(id="p2", title="Plate", price=25.0, category="home", seller_rating=4.2, store="StoreB"),
            Product(id="p3", title="Phone", price=500.0, category="electronics", seller_rating=4.8, store="StoreC"),
        ]
    
    def test_empty_catalog(self):
        """Should create empty catalog."""
        catalog = ProductCatalog()
        assert len(catalog) == 0
    
    def test_catalog_with_products(self, sample_products):
        """Should create catalog with initial products."""
        catalog = ProductCatalog(sample_products)
        assert len(catalog) == 3
    
    def test_add_product(self):
        """Should add product to catalog."""
        catalog = ProductCatalog()
        product = Product(id="p1", title="Test", price=10.0, category="test", seller_rating=4.0, store="X")
        catalog.add_product(product)
        assert len(catalog) == 1
        assert "p1" in catalog
    
    def test_get_product(self, sample_products):
        """Should get product by ID."""
        catalog = ProductCatalog(sample_products)
        product = catalog.get("p1")
        assert product is not None
        assert product.title == "Mug"
    
    def test_get_nonexistent_product(self, sample_products):
        """Should return None for nonexistent product."""
        catalog = ProductCatalog(sample_products)
        product = catalog.get("p999")
        assert product is None
    
    def test_getitem(self, sample_products):
        """Should support bracket access."""
        catalog = ProductCatalog(sample_products)
        product = catalog["p2"]
        assert product.title == "Plate"
    
    def test_getitem_keyerror(self, sample_products):
        """Should raise ProductNotFoundError for missing product with bracket access."""
        catalog = ProductCatalog(sample_products)
        with pytest.raises(ProductNotFoundError):
            _ = catalog["p999"]
    
    def test_contains(self, sample_products):
        """Should support 'in' operator."""
        catalog = ProductCatalog(sample_products)
        assert "p1" in catalog
        assert "p999" not in catalog
    
    def test_iterate(self, sample_products):
        """Should support iteration."""
        catalog = ProductCatalog(sample_products)
        products = list(catalog)
        assert len(products) == 3
        ids = {p.id for p in products}
        assert ids == {"p1", "p2", "p3"}
    
    def test_product_ids(self, sample_products):
        """Should return list of product IDs."""
        catalog = ProductCatalog(sample_products)
        ids = catalog.product_ids
        assert set(ids) == {"p1", "p2", "p3"}
    
    def test_categories(self, sample_products):
        """Should return sorted unique categories."""
        catalog = ProductCatalog(sample_products)
        assert catalog.categories == ["electronics", "home"]
    
    def test_from_list(self):
        """Should create catalog from list of dicts."""
        data = [
            {"id": "p1", "title": "A", "price": 10, "category": "x", "seller_rating": 4.0, "store": "Y"},
            {"id": "p2", "title": "B", "price": 20, "category": "x", "seller_rating": 4.5, "store": "Z"},
        ]
        catalog = ProductCatalog.from_list(data)
        assert len(catalog) == 2
        assert catalog["p1"].title == "A"
        assert catalog["p2"].title == "B"
    
    def test_to_list(self, sample_products):
        """Should convert catalog to list of dicts."""
        catalog = ProductCatalog(sample_products)
        result = catalog.to_list()
        assert len(result) == 3
        ids = {p["id"] for p in result}
        assert ids == {"p1", "p2", "p3"}

    def test_add_product_overwrites_duplicate_id(self):
        """Adding product with same id should overwrite existing."""
        catalog = ProductCatalog()
        p1a = Product(id="p1", title="First", price=10.0, category="x", seller_rating=4.0, store="A")
        p1b = Product(id="p1", title="Second", price=20.0, category="y", seller_rating=3.0, store="B")
        catalog.add_product(p1a)
        catalog.add_product(p1b)
        assert len(catalog) == 1
        assert catalog["p1"].title == "Second"
        assert catalog["p1"].price == 20.0

    def test_categories_sorted_unique(self):
        """Categories should be sorted unique values (case-sensitive)."""
        products = [
            Product(id="p1", title="A", price=10.0, category="Zebra", seller_rating=4.0, store="X"),
            Product(id="p2", title="B", price=20.0, category="alpha", seller_rating=4.0, store="Y"),
            Product(id="p3", title="C", price=30.0, category="Zebra", seller_rating=4.0, store="Z"),
        ]
        catalog = ProductCatalog(products)
        assert catalog.categories == ["Zebra", "alpha"]

    def test_stores_sorted(self):
        """Stores should be sorted alphabetically."""
        products = [
            Product(id="p1", title="A", price=10.0, category="x", seller_rating=4.0, store="Charlie"),
            Product(id="p2", title="B", price=20.0, category="x", seller_rating=4.0, store="Alpha"),
            Product(id="p3", title="C", price=30.0, category="x", seller_rating=4.0, store="Bravo"),
        ]
        catalog = ProductCatalog(products)
        assert catalog.stores == ["Alpha", "Bravo", "Charlie"]

    def test_product_ids_order_stable(self):
        """product_ids should return list (order may vary but should be consistent within run)."""
        catalog = ProductCatalog([
            Product(id="c", title="C", price=10.0, category="x", seller_rating=4.0, store="X"),
            Product(id="a", title="A", price=10.0, category="x", seller_rating=4.0, store="Y"),
            Product(id="b", title="B", price=10.0, category="x", seller_rating=4.0, store="Z"),
        ])
        ids = catalog.product_ids
        assert set(ids) == {"a", "b", "c"}
        assert len(ids) == 3


class TestProductBoundaryValues:
    """Tests for Product at boundary values."""

    def test_seller_rating_zero(self):
        """Should accept seller_rating of 0."""
        product = Product(id="p1", title="Test", price=10.0, category="x", seller_rating=0.0, store="X")
        assert product.seller_rating == 0.0

    def test_seller_rating_five(self):
        """Should accept seller_rating of 5.0."""
        product = Product(id="p1", title="Test", price=10.0, category="x", seller_rating=5.0, store="X")
        assert product.seller_rating == 5.0

    def test_price_zero_rejected_by_from_amazon_meta(self):
        """from_amazon_meta rejects price 0."""
        meta = {"parent_asin": "B123", "title": "Test", "price": 0, "main_category": "X", "store": "Y"}
        assert Product.from_amazon_meta(meta) is None

    def test_price_negative_rejected_by_from_amazon_meta(self):
        """from_amazon_meta rejects negative price."""
        meta = {"parent_asin": "B123", "title": "Test", "price": -5.0, "main_category": "X", "store": "Y"}
        assert Product.from_amazon_meta(meta) is None


class TestProductFromAmazonMetaEdgeCases:
    """Additional edge cases for Product.from_amazon_meta()."""

    def test_from_amazon_meta_missing_parent_asin(self):
        """Should return None when parent_asin is missing."""
        meta = {"title": "Test", "price": 10.0, "main_category": "X", "store": "Y"}
        product = Product.from_amazon_meta(meta)
        assert product is None

    def test_from_amazon_meta_invalid_price_string(self):
        """Should return None when price is non-numeric string."""
        meta = {"parent_asin": "B123", "title": "Test", "price": "free", "main_category": "X", "store": "Y"}
        product = Product.from_amazon_meta(meta)
        assert product is None

    def test_from_amazon_meta_images_empty_list(self):
        """Should handle empty images list."""
        meta = {
            "parent_asin": "B123",
            "title": "Test",
            "price": 10.0,
            "main_category": "X",
            "store": "Y",
            "images": [],
        }
        product = Product.from_amazon_meta(meta)
        assert product is not None
        assert product.image_url is None

    def test_from_amazon_meta_images_thumb_fallback(self):
        """Should use thumb if large/hi_res not present."""
        meta = {
            "parent_asin": "B123",
            "title": "Test",
            "price": 10.0,
            "main_category": "X",
            "store": "Y",
            "images": [{"thumb": "https://example.com/thumb.jpg"}],
        }
        product = Product.from_amazon_meta(meta)
        assert product is not None
        assert product.image_url == "https://example.com/thumb.jpg"

    def test_from_amazon_meta_hi_res_precedence(self):
        """Should prefer large over hi_res over thumb."""
        meta = {
            "parent_asin": "B123",
            "title": "Test",
            "price": 10.0,
            "main_category": "X",
            "store": "Y",
            "images": [
                {"large": "https://large.jpg", "hi_res": "https://hires.jpg", "thumb": "https://thumb.jpg"}
            ],
        }
        product = Product.from_amazon_meta(meta)
        assert product.image_url == "https://large.jpg"

    def test_from_amazon_meta_description_non_list(self):
        """Should handle description as non-list (gracefully)."""
        meta = {
            "parent_asin": "B123",
            "title": "Test",
            "price": 10.0,
            "main_category": "X",
            "store": "Y",
            "description": "plain string",
        }
        product = Product.from_amazon_meta(meta)
        assert product is not None
        assert product.description is None  # expects list, may not join
