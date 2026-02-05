"""
Product catalog for the marketplace.

Defines Product and ProductCatalog classes for storing and accessing products.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterator


@dataclass
class Product:
    """
    A product in the marketplace catalog.
    
    Attributes:
        id: Unique product identifier (ASIN from Amazon dataset).
        title: Product title/name.
        price: Product price in dollars.
        category: Product main category (e.g., "Computers", "Cell Phones & Accessories").
        seller_rating: Seller's average rating (0-5 scale), computed from reviews.
        store: Seller/store name (e.g., "Anker", "Amazon Basics").
        description: Optional product description.
        tags: Optional list of product tags/categories.
        image_url: Optional product image URL.
        rating_number: Optional number of ratings the product has.
        features: Optional list of product feature bullet points.
    
    Example:
        >>> product = Product(
        ...     id="B07BJ7ZZL7",
        ...     title="Silicone Watch Band",
        ...     price=14.89,
        ...     category="Cell Phones & Accessories",
        ...     seller_rating=4.4,
        ...     store="QGHXO"
        ... )
    """
    
    id: str
    title: str
    price: float
    category: str
    seller_rating: float
    store: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    rating_number: Optional[int] = None
    features: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate product attributes."""
        if self.price < 0:
            raise ValueError(f"Price cannot be negative: {self.price}")
        if not (0 <= self.seller_rating <= 5):
            raise ValueError(f"Seller rating must be 0-5: {self.seller_rating}")
    
    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Create a Product from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            price=float(data["price"]),
            category=data["category"],
            seller_rating=float(data["seller_rating"]),
            store=data["store"],
            description=data.get("description"),
            tags=data.get("tags"),
            image_url=data.get("image_url"),
            rating_number=data.get("rating_number"),
            features=data.get("features"),
        )
    
    @classmethod
    def from_amazon_meta(
        cls,
        meta: dict,
        seller_rating: Optional[float] = None
    ) -> Optional["Product"]:
        """
        Create a Product from an Amazon metadata record.
        
        Args:
            meta: Raw metadata dict from meta_Electronics JSONL.
            seller_rating: Pre-computed seller rating (from reviews).
                           Falls back to average_rating if not provided.
        
        Returns:
            Product instance, or None if required fields are missing.
        """
        price = meta.get("price")
        title = meta.get("title")
        parent_asin = meta.get("parent_asin")
        
        # Skip if missing required fields
        if price is None or title is None or parent_asin is None:
            return None
        
        try:
            price = float(price)
        except (ValueError, TypeError):
            return None
        
        if price <= 0:
            return None
        
        # Use seller_rating if provided, else fall back to average_rating
        rating = seller_rating if seller_rating is not None else meta.get("average_rating", 0)
        try:
            rating = float(rating)
            rating = max(0.0, min(5.0, rating))
        except (ValueError, TypeError):
            rating = 0.0
        
        # Extract first image URL
        images = meta.get("images", [])
        image_url = None
        if images and isinstance(images, list) and len(images) > 0:
            first_img = images[0]
            image_url = (
                first_img.get("large")
                or first_img.get("hi_res")
                or first_img.get("thumb")
            )
        
        # Build description from description list
        desc_parts = meta.get("description", [])
        description = " ".join(desc_parts) if isinstance(desc_parts, list) and desc_parts else None
        
        # Categories as tags
        categories = meta.get("categories", [])
        tags = categories if isinstance(categories, list) else None
        
        # Features
        features = meta.get("features", [])
        features = features if isinstance(features, list) and features else None
        
        return cls(
            id=parent_asin,
            title=title,
            price=price,
            category=meta.get("main_category") or "Unknown",
            seller_rating=rating,
            store=meta.get("store", "Unknown"),
            description=description,
            tags=tags,
            image_url=image_url,
            rating_number=meta.get("rating_number"),
            features=features,
        )
    
    def to_dict(self) -> dict:
        """Convert product to dictionary."""
        result = {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "category": self.category,
            "seller_rating": self.seller_rating,
            "store": self.store,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.tags is not None:
            result["tags"] = self.tags
        if self.image_url is not None:
            result["image_url"] = self.image_url
        if self.rating_number is not None:
            result["rating_number"] = self.rating_number
        if self.features is not None:
            result["features"] = self.features
        return result


class ProductCatalog:
    """
    A catalog of products in the marketplace.
    
    Provides efficient access to products by ID and supports iteration.
    
    Example:
        >>> catalog = ProductCatalog()
        >>> catalog.add_product(Product(id="p1", title="Mug", ...))
        >>> product = catalog.get("p1")
        >>> for product in catalog:
        ...     print(product.title)
    """
    
    def __init__(self, products: Optional[List[Product]] = None):
        """
        Initialize the catalog.
        
        Args:
            products: Optional list of products to add initially.
        """
        self._products: Dict[str, Product] = {}
        if products:
            for product in products:
                self.add_product(product)
    
    def add_product(self, product: Product) -> None:
        """Add a product to the catalog."""
        self._products[product.id] = product
    
    def get(self, product_id: str) -> Optional[Product]:
        """Get a product by ID, or None if not found."""
        return self._products.get(product_id)
    
    def __getitem__(self, product_id: str) -> Product:
        """Get a product by ID, raising KeyError if not found."""
        return self._products[product_id]
    
    def __contains__(self, product_id: str) -> bool:
        """Check if a product ID exists in the catalog."""
        return product_id in self._products
    
    def __len__(self) -> int:
        """Return the number of products in the catalog."""
        return len(self._products)
    
    def __iter__(self) -> Iterator[Product]:
        """Iterate over all products in the catalog."""
        return iter(self._products.values())
    
    @property
    def product_ids(self) -> List[str]:
        """Return a list of all product IDs."""
        return list(self._products.keys())
    
    @property
    def categories(self) -> List[str]:
        """Return sorted list of unique categories in the catalog."""
        return sorted({p.category for p in self._products.values() if p.category})
    
    @property
    def stores(self) -> List[str]:
        """Return sorted list of unique store names in the catalog."""
        return sorted({p.store for p in self._products.values() if p.store})
    
    @classmethod
    def from_list(cls, products_data: List[dict]) -> "ProductCatalog":
        """
        Create a ProductCatalog from a list of dictionaries.
        
        Args:
            products_data: List of product dictionaries.
        
        Returns:
            ProductCatalog instance.
        """
        products = [Product.from_dict(p) for p in products_data]
        return cls(products)
    
    def to_list(self) -> List[dict]:
        """Convert catalog to list of dictionaries."""
        return [p.to_dict() for p in self._products.values()]
