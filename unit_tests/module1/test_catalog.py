"""
Unit tests for Product and ProductCatalog.
"""

import pytest
from src.module1.catalog import Product, ProductCatalog


class TestProduct:
    """Tests for Product class."""
    
    def test_create_product(self):
        """Should create a product with required fields."""
        product = Product(
            id="p12",
            title="Handmade Ceramic Mug",
            price=18.0,
            category="home",
            seller_rating=4.8,
            location="Boston"
        )
        assert product.id == "p12"
        assert product.title == "Handmade Ceramic Mug"
        assert product.price == 18.0
        assert product.category == "home"
        assert product.seller_rating == 4.8
        assert product.location == "Boston"
        assert product.description is None
        assert product.tags is None
    
    def test_create_product_with_optional_fields(self):
        """Should accept optional description and tags."""
        product = Product(
            id="p1",
            title="Test Product",
            price=10.0,
            category="test",
            seller_rating=4.0,
            location="NYC",
            description="A test product",
            tags=["test", "sample"]
        )
        assert product.description == "A test product"
        assert product.tags == ["test", "sample"]
    
    def test_invalid_negative_price(self):
        """Should reject negative price."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Product(
                id="p1",
                title="Test",
                price=-5.0,
                category="test",
                seller_rating=4.0,
                location="NYC"
            )
    
    def test_invalid_seller_rating_too_high(self):
        """Should reject seller rating > 5."""
        with pytest.raises(ValueError, match="Seller rating must be 0-5"):
            Product(
                id="p1",
                title="Test",
                price=10.0,
                category="test",
                seller_rating=5.5,
                location="NYC"
            )
    
    def test_invalid_seller_rating_negative(self):
        """Should reject negative seller rating."""
        with pytest.raises(ValueError, match="Seller rating must be 0-5"):
            Product(
                id="p1",
                title="Test",
                price=10.0,
                category="test",
                seller_rating=-1.0,
                location="NYC"
            )
    
    def test_product_from_dict(self):
        """Should create product from dictionary."""
        data = {
            "id": "p1",
            "title": "Test Product",
            "price": 25.0,
            "category": "electronics",
            "seller_rating": 4.5,
            "location": "LA",
            "description": "Great product",
            "tags": ["electronic", "gadget"]
        }
        product = Product.from_dict(data)
        assert product.id == "p1"
        assert product.title == "Test Product"
        assert product.price == 25.0
        assert product.category == "electronics"
        assert product.seller_rating == 4.5
        assert product.location == "LA"
        assert product.description == "Great product"
        assert product.tags == ["electronic", "gadget"]
    
    def test_product_to_dict(self):
        """Should convert product to dictionary."""
        product = Product(
            id="p1",
            title="Test",
            price=10.0,
            category="test",
            seller_rating=4.0,
            location="NYC",
            description="A test",
            tags=["t1"]
        )
        result = product.to_dict()
        assert result["id"] == "p1"
        assert result["title"] == "Test"
        assert result["price"] == 10.0
        assert result["category"] == "test"
        assert result["seller_rating"] == 4.0
        assert result["location"] == "NYC"
        assert result["description"] == "A test"
        assert result["tags"] == ["t1"]
    
    def test_product_to_dict_without_optional(self):
        """Should omit None optional fields in to_dict."""
        product = Product(
            id="p1",
            title="Test",
            price=10.0,
            category="test",
            seller_rating=4.0,
            location="NYC"
        )
        result = product.to_dict()
        assert "description" not in result
        assert "tags" not in result


class TestProductCatalog:
    """Tests for ProductCatalog class."""
    
    @pytest.fixture
    def sample_products(self):
        """Sample products for testing."""
        return [
            Product(id="p1", title="Mug", price=15.0, category="home", seller_rating=4.5, location="Boston"),
            Product(id="p2", title="Plate", price=25.0, category="home", seller_rating=4.2, location="NYC"),
            Product(id="p3", title="Phone", price=500.0, category="electronics", seller_rating=4.8, location="LA"),
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
        product = Product(id="p1", title="Test", price=10.0, category="test", seller_rating=4.0, location="NYC")
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
        """Should raise KeyError for missing product with bracket access."""
        catalog = ProductCatalog(sample_products)
        with pytest.raises(KeyError):
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
    
    def test_from_list(self):
        """Should create catalog from list of dicts."""
        data = [
            {"id": "p1", "title": "A", "price": 10, "category": "x", "seller_rating": 4.0, "location": "Y"},
            {"id": "p2", "title": "B", "price": 20, "category": "x", "seller_rating": 4.5, "location": "Z"},
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
