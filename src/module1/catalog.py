"""
Product catalog for the marketplace.

Defines Product and ProductCatalog classes for storing and accessing products.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Iterator


@dataclass
class Product:
    """
    A product in the marketplace catalog.
    
    Attributes:
        id: Unique product identifier (e.g., "p12").
        title: Product title/name.
        price: Product price in dollars.
        category: Product category (e.g., "home", "electronics").
        seller_rating: Seller's rating (0-5 scale).
        location: Seller's location (e.g., "Boston").
        description: Optional product description.
        tags: Optional list of product tags.
    
    Example:
        >>> product = Product(
        ...     id="p12",
        ...     title="Handmade Ceramic Mug",
        ...     price=18.0,
        ...     category="home",
        ...     seller_rating=4.8,
        ...     location="Boston"
        ... )
    """
    
    id: str
    title: str
    price: float
    category: str
    seller_rating: float
    location: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
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
            location=data["location"],
            description=data.get("description"),
            tags=data.get("tags")
        )
    
    def to_dict(self) -> dict:
        """Convert product to dictionary."""
        result = {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "category": self.category,
            "seller_rating": self.seller_rating,
            "location": self.location
        }
        if self.description is not None:
            result["description"] = self.description
        if self.tags is not None:
            result["tags"] = self.tags
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
