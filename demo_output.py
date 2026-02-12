"""Generate sample output evidence for Checkpoint 1 README."""
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

from src.module1 import CandidateRetrieval, SearchFilters, ProductCatalog, Product

# Build a small demo catalog
products = [
    Product(id="B07BJ7ZZL7", title="Silicone Watch Band",    price=14.89, category="Cell Phones & Accessories", seller_rating=4.4, store="QGHXO"),
    Product(id="B08GFTPQ5B", title="USB-C Hub Adapter",      price=29.99, category="Computers",                 seller_rating=4.7, store="Anker"),
    Product(id="B09XYZ1234", title="Wireless Earbuds",        price=39.99, category="Electronics",               seller_rating=4.2, store="Sony"),
    Product(id="B07ABC9876", title="Laptop Stand Adjustable", price=24.50, category="Computers",                 seller_rating=4.8, store="Anker"),
    Product(id="B06DEF5555", title="Phone Case Clear",        price=9.99,  category="Cell Phones & Accessories", seller_rating=3.9, store="Spigen"),
    Product(id="B05GHI7777", title="Mechanical Keyboard",     price=59.99, category="Computers",                 seller_rating=4.6, store="Logitech"),
    Product(id="B04JKL3333", title="HDMI Cable 6ft",          price=8.49,  category="Electronics",               seller_rating=4.1, store="AmazonBasics"),
    Product(id="B03MNO8888", title="Webcam HD 1080p",         price=34.99, category="Computers",                 seller_rating=4.5, store="Logitech"),
]

catalog = ProductCatalog(products)
retrieval = CandidateRetrieval(catalog)

# Example 1: Filter by category + price
print("--- Example 1: Computers under $35 sorted by price ---")
filters = SearchFilters.from_dict({
    "price": [10, 35],
    "category": "Computers",
    "sort_by": "price_asc",
})
result = retrieval.search(filters)
print(f"Candidates: {result.candidate_ids}")
print(f"Count: {result.count}  Strategy: {result.strategy}  Scanned: {result.total_scanned}  Elapsed: {result.elapsed_ms:.2f}ms")
for pid in result:
    p = catalog[pid]
    print(f"  {p.id} | {p.title:30s} | ${p.price:<7.2f} | rating {p.seller_rating}")

# Example 2: High-rated products across all categories
print()
print("--- Example 2: All categories, rating >= 4.5, sorted by rating ---")
filters2 = SearchFilters(min_seller_rating=4.5, sort_by="rating_desc")
result2 = retrieval.search(filters2, strategy="priority")
print(f"Candidates: {result2.candidate_ids}")
print(f"Count: {result2.count}  Strategy: {result2.strategy}  Scanned: {result2.total_scanned}  Elapsed: {result2.elapsed_ms:.2f}ms")
for pid in result2:
    p = catalog[pid]
    print(f"  {p.id} | {p.title:30s} | ${p.price:<7.2f} | rating {p.seller_rating}")

# Example 3: No matches
print()
print("--- Example 3: No matches (non-existent category) ---")
result3 = retrieval.search(SearchFilters(category="Furniture"))
print(f"Candidates: {result3.candidate_ids}")
print(f"Count: {result3.count}")
