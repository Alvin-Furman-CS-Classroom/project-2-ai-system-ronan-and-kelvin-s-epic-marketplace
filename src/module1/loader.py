"""
Dataset loader for building ProductCatalog from Amazon data.

Reads the Amazon Reviews'23 metadata and reviews files to build
a ProductCatalog with computed seller ratings.
"""

import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional

from .catalog import Product, ProductCatalog


def compute_seller_ratings(
    reviews_path: str | Path,
    meta_path: str | Path,
) -> Dict[str, float]:
    """
    Compute average seller (store) rating from reviews.
    
    Maps each review's ASIN to its store via metadata, then averages
    all review ratings per store.
    
    Args:
        reviews_path: Path to reviews JSONL (gzipped).
        meta_path: Path to metadata JSONL (gzipped).
    
    Returns:
        Dictionary mapping store name -> average rating (0-5).
    """
    # Step 1: Map parent_asin -> store from metadata
    asin_to_store: Dict[str, str] = {}
    with gzip.open(str(meta_path), "rt", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            store = obj.get("store")
            asin = obj.get("parent_asin")
            if store and asin:
                asin_to_store[asin] = store
    
    # Step 2: Aggregate review ratings by store
    store_ratings: Dict[str, list] = defaultdict(list)
    with gzip.open(str(reviews_path), "rt", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            asin = obj.get("parent_asin")
            rating = obj.get("rating")
            if asin in asin_to_store and rating is not None:
                store_ratings[asin_to_store[asin]].append(float(rating))
    
    # Step 3: Compute averages
    return {
        store: sum(ratings) / len(ratings)
        for store, ratings in store_ratings.items()
        if ratings
    }


def load_catalog(
    meta_path: str | Path,
    seller_ratings: Optional[Dict[str, float]] = None,
    max_products: Optional[int] = None,
) -> ProductCatalog:
    """
    Load a ProductCatalog from Amazon metadata JSONL.
    
    Args:
        meta_path: Path to metadata JSONL (gzipped).
        seller_ratings: Pre-computed seller ratings (store -> rating).
                        If None, uses average_rating from metadata.
        max_products: Maximum products to load. None for all.
    
    Returns:
        ProductCatalog instance.
    """
    catalog = ProductCatalog()
    count = 0
    
    with gzip.open(str(meta_path), "rt", encoding="utf-8") as f:
        for line in f:
            if max_products is not None and count >= max_products:
                break
            
            obj = json.loads(line)
            
            # Look up seller rating by store name
            store = obj.get("store", "")
            rating = None
            if seller_ratings and store in seller_ratings:
                rating = seller_ratings[store]
            
            product = Product.from_amazon_meta(obj, seller_rating=rating)
            if product is not None:
                catalog.add_product(product)
                count += 1
    
    return catalog


def load_catalog_from_working_set(
    working_set_dir: Optional[str | Path] = None,
    max_products: Optional[int] = None,
) -> ProductCatalog:
    """
    Convenience function to load catalog from the working_set directory.
    
    Args:
        working_set_dir: Path to working_set directory. Defaults to
                         datasets/working_set/ relative to repo root.
        max_products: Maximum products to load.
    
    Returns:
        ProductCatalog instance with seller ratings computed from reviews.
    """
    if working_set_dir is None:
        repo_root = Path(__file__).resolve().parents[2]
        working_set_dir = repo_root / "datasets" / "working_set"
    else:
        working_set_dir = Path(working_set_dir)
    
    meta_path = working_set_dir / "meta_Electronics_50000.jsonl.gz"
    reviews_path = working_set_dir / "Electronics_50000.jsonl.gz"
    
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    
    # Compute seller ratings from reviews if available
    seller_ratings = None
    if reviews_path.exists():
        seller_ratings = compute_seller_ratings(reviews_path, meta_path)
    
    return load_catalog(meta_path, seller_ratings, max_products)
