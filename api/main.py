"""
Epic Marketplace API — FastAPI wrapper for the AI search modules.

Exposes Module 1 (Candidate Retrieval) and Module 2 (Heuristic Re-ranking)
as REST endpoints.  New modules will add endpoints as they are completed.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Ensure project root is on the Python path so `src.module1` resolves.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.module1 import (
    CandidateRetrieval,
    Product,
    ProductCatalog,
    SearchFilters,
    SearchResult,
    load_catalog_from_working_set,
)
from src.module2 import HeuristicRanker, RankedResult, ScoringConfig
from src.module2.ranker import RANKING_STRATEGIES

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global state — populated at startup
# ---------------------------------------------------------------------------
catalog: Optional[ProductCatalog] = None
retrieval: Optional[CandidateRetrieval] = None
ranker: Optional[HeuristicRanker] = None


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------
class ProductResponse(BaseModel):
    """Serialisable representation of a Product."""

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

    @classmethod
    def from_product(cls, product: Product) -> "ProductResponse":
        return cls(
            id=product.id,
            title=product.title,
            price=product.price,
            category=product.category,
            seller_rating=product.seller_rating,
            store=product.store,
            description=product.description,
            tags=product.tags,
            image_url=product.image_url,
            rating_number=product.rating_number,
            features=product.features,
        )


class SearchMetadata(BaseModel):
    """Search performance & strategy metadata."""

    strategy: str
    total_scanned: int
    elapsed_ms: float
    count: int
    total: int          # total matching results (before pagination)
    page: int           # current page (1-based)
    page_size: int      # items per page
    total_pages: int    # total number of pages


class SearchResponse(BaseModel):
    """Payload returned by GET /api/search."""

    products: List[ProductResponse]
    metadata: SearchMetadata


class CategoryResponse(BaseModel):
    name: str
    count: int


class RerankItemResponse(BaseModel):
    """Single item in a re-ranked result set."""

    product: ProductResponse
    score: float
    rank: int


class RerankMetadata(BaseModel):
    """Metadata about the re-ranking pass."""

    strategy: str
    iterations: int
    objective_value: float
    elapsed_ms: float
    count: int


class RerankResponse(BaseModel):
    """Payload returned by GET /api/rerank."""

    items: List[RerankItemResponse]
    metadata: RerankMetadata


# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------
DEMO_PRODUCTS = [
    Product(id="B07BJ7ZZL7", title="Silicone Watch Band Compatible with Apple Watch",           price=14.89, category="Cell Phones & Accessories", seller_rating=4.4, store="QGHXO",       description="Premium silicone band for Apple Watch, soft and durable.", tags=["watch", "band", "silicone"], image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400", rating_number=1247),
    Product(id="B08GFTPQ5B", title="USB-C Hub Multiport Adapter 7-in-1",                        price=29.99, category="Computers",                  seller_rating=4.7, store="Anker",        description="7-in-1 USB-C hub with HDMI, USB 3.0, SD card reader.",     tags=["usb-c", "hub", "adapter"],     image_url="https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400", rating_number=3421),
    Product(id="B09XYZ1234", title="Wireless Bluetooth Earbuds with Noise Cancelling",           price=39.99, category="Electronics",                seller_rating=4.2, store="Sony",         description="True wireless earbuds with ANC and 24hr battery life.",    tags=["earbuds", "wireless", "anc"],   image_url="https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=400", rating_number=892),
    Product(id="B07ABC9876", title="Adjustable Laptop Stand for Desk – Ergonomic",               price=24.50, category="Computers",                  seller_rating=4.8, store="Anker",        description="Ergonomic aluminium laptop stand, adjustable height.",     tags=["laptop", "stand", "ergonomic"], image_url="https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400", rating_number=5103),
    Product(id="B06DEF5555", title="Clear Phone Case for iPhone 15 – Slim Protective",           price=9.99,  category="Cell Phones & Accessories", seller_rating=3.9, store="Spigen",       description="Ultra-slim clear case with shock-absorbing corners.",      tags=["phone", "case", "clear"],       image_url="https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400", rating_number=7892),
    Product(id="B05GHI7777", title="Mechanical Gaming Keyboard RGB Backlit",                     price=59.99, category="Computers",                  seller_rating=4.6, store="Logitech",     description="Full-size mechanical keyboard with Cherry MX switches.",   tags=["keyboard", "mechanical", "rgb"],image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400", rating_number=2341),
    Product(id="B04JKL3333", title="HDMI Cable 6ft High Speed 4K – Braided",                     price=8.49,  category="Electronics",                seller_rating=4.1, store="AmazonBasics", description="Premium braided HDMI 2.1 cable supporting 4K@120Hz.",     tags=["hdmi", "cable", "4k"],          image_url="https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400", rating_number=12034),
    Product(id="B03MNO8888", title="Webcam HD 1080p with Microphone for Streaming",              price=34.99, category="Computers",                  seller_rating=4.5, store="Logitech",     description="1080p webcam with built-in noise-reducing microphone.",    tags=["webcam", "1080p", "streaming"], image_url="https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=400", rating_number=4201),
    Product(id="B02PQR4444", title="Portable Bluetooth Speaker Waterproof – 20W",                price=45.00, category="Electronics",                seller_rating=4.3, store="JBL",          description="Waterproof portable speaker with 12hr battery and bass.", tags=["speaker", "bluetooth", "portable"], image_url="https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400", rating_number=6712),
    Product(id="B01STU2222", title="Wireless Charging Pad 15W Fast Charge – Slim",               price=19.99, category="Cell Phones & Accessories", seller_rating=4.0, store="Anker",        description="Qi-certified 15W wireless charger, slim design.",         tags=["charger", "wireless", "fast"],  image_url="https://images.unsplash.com/photo-1585338107529-13afc5f02586?w=400", rating_number=3098),
    Product(id="B00VWX1111", title="Noise Cancelling Over-Ear Headphones – Studio",              price=79.99, category="Electronics",                seller_rating=4.9, store="Sony",         description="Premium studio headphones with active noise cancelling.",  tags=["headphones", "anc", "studio"],  image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400", rating_number=9821),
    Product(id="B10ABC6666", title="External SSD 1TB USB 3.2 – Portable Storage",                price=89.99, category="Computers",                  seller_rating=4.7, store="Samsung",      description="1TB portable SSD with read speeds up to 1050MB/s.",       tags=["ssd", "storage", "portable"],   image_url="https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400", rating_number=4590),
    Product(id="B11DEF7777", title="Smart Watch Fitness Tracker – Heart Rate Monitor",            price=49.99, category="Cell Phones & Accessories", seller_rating=4.4, store="Fitbit",       description="Fitness smartwatch with heart rate, GPS, sleep tracking.", tags=["smartwatch", "fitness", "gps"], image_url="https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=400", rating_number=6234),
    Product(id="B12GHI8888", title="USB Desk Lamp LED with Wireless Charger",                    price=32.00, category="Electronics",                seller_rating=4.2, store="TaoTronics",   description="LED desk lamp with touch dimming and Qi wireless charger.",tags=["lamp", "led", "charger"],       image_url="https://images.unsplash.com/photo-1507473885765-e6ed057ab6fe?w=400", rating_number=1876),
    Product(id="B13JKL9999", title="Gaming Mouse Wireless – 25K DPI Sensor",                     price=69.99, category="Computers",                  seller_rating=4.6, store="Logitech",     description="Wireless gaming mouse with 25K DPI HERO sensor.",         tags=["mouse", "gaming", "wireless"],  image_url="https://images.unsplash.com/photo-1527814050087-3793815479db?w=400", rating_number=3456),
    Product(id="B14MNO0000", title="Camera Tripod 60-inch Lightweight Aluminium",                price=22.99, category="Electronics",                seller_rating=4.3, store="AmazonBasics", description="Lightweight aluminium tripod with quick-release plate.",   tags=["tripod", "camera", "aluminium"],image_url="https://images.unsplash.com/photo-1542567455-cd733f23fbb1?w=400", rating_number=2098),
    Product(id="B15PQR1111", title="Screen Protector Tempered Glass iPhone 15 (3-Pack)",          price=7.99,  category="Cell Phones & Accessories", seller_rating=3.8, store="Spigen",       description="9H hardness tempered glass screen protector, 3 pack.",    tags=["screen", "protector", "glass"], image_url="https://images.unsplash.com/photo-1605236453806-6ff36851218e?w=400", rating_number=15432),
    Product(id="B16STU2222", title="Monitor Stand Riser with USB Ports – Bamboo",                price=39.99, category="Computers",                  seller_rating=4.5, store="Huanuo",       description="Bamboo monitor riser with 4 USB ports and cable mgmt.",   tags=["monitor", "stand", "bamboo"],   image_url="https://images.unsplash.com/photo-1586210579191-33b45e38fa2c?w=400", rating_number=1345),
    Product(id="B17VWX3333", title="DSLR Camera Bag Backpack – Waterproof",                      price=54.99, category="Electronics",                seller_rating=4.4, store="Lowepro",      description="Waterproof camera backpack with laptop compartment.",     tags=["camera", "bag", "waterproof"],  image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400", rating_number=2567),
    Product(id="B18YZA4444", title="Wireless Keyboard and Mouse Combo – Slim",                   price=27.99, category="Computers",                  seller_rating=4.1, store="Logitech",     description="Slim wireless keyboard and mouse combo, quiet keys.",     tags=["keyboard", "mouse", "combo"],   image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400", rating_number=4321),
]


def _load_catalog() -> ProductCatalog:
    """Load the product catalog — prefer working-set data, fall back to demo."""
    try:
        working_set = os.path.join(PROJECT_ROOT, "datasets", "working_set")
        if os.path.isdir(working_set):
            cat = load_catalog_from_working_set(working_set)
            if len(cat) > 0:
                logger.info("Loaded %d products from working set", len(cat))
                return cat
    except Exception as exc:
        logger.warning("Could not load working set: %s — using demo catalog", exc)

    logger.info("Using demo catalog (%d products)", len(DEMO_PRODUCTS))
    return ProductCatalog(DEMO_PRODUCTS)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global catalog, retrieval, ranker
    catalog = _load_catalog()
    retrieval = CandidateRetrieval(catalog)
    ranker = HeuristicRanker(catalog)
    logger.info("API ready — %d products indexed", len(catalog))
    yield


app = FastAPI(
    title="Epic Marketplace API",
    description="Product search powered by AI — CSC-343",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "products": len(catalog) if catalog else 0}


@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories():
    """List all categories with product counts."""
    if not catalog:
        raise HTTPException(503, "Catalog not loaded")

    counts: dict[str, int] = {}
    for product in catalog:
        counts[product.category] = counts.get(product.category, 0) + 1

    return sorted(
        [CategoryResponse(name=name, count=count) for name, count in counts.items()],
        key=lambda c: c.count,
        reverse=True,
    )


@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a single product by ID."""
    if not catalog:
        raise HTTPException(503, "Catalog not loaded")
    try:
        product = catalog[product_id]
    except KeyError:
        raise HTTPException(404, f"Product not found: {product_id}")
    return ProductResponse.from_product(product)


@app.get("/api/products", response_model=List[ProductResponse])
async def list_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List products with pagination."""
    if not catalog:
        raise HTTPException(503, "Catalog not loaded")
    products = list(catalog)
    page = products[offset : offset + limit]
    return [ProductResponse.from_product(p) for p in page]


@app.get("/api/search", response_model=SearchResponse)
async def search(
    q: Optional[str] = Query(None, description="Free-text query (reserved for Module 3)"),
    category: Optional[str] = Query(None),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    store: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    strategy: str = Query("linear"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(24, ge=1, le=100, description="Products per page"),
):
    """
    Search for products matching filters.

    Returns matching products with search metadata (strategy, timing, etc.).
    """
    if not retrieval or not catalog:
        raise HTTPException(503, "Catalog not loaded")

    filters = SearchFilters(
        price_min=price_min,
        price_max=price_max,
        category=category,
        min_seller_rating=min_rating,
        store=store,
        sort_by=sort_by,
    )

    result: SearchResult = retrieval.search(filters, strategy=strategy)

    # Paginate the candidate IDs
    total = result.count
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_ids = result.candidate_ids[start:end]

    products = [
        ProductResponse.from_product(catalog[pid])
        for pid in page_ids
    ]

    return SearchResponse(
        products=products,
        metadata=SearchMetadata(
            strategy=result.strategy,
            total_scanned=result.total_scanned,
            elapsed_ms=result.elapsed_ms,
            count=len(page_ids),
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@app.get("/api/rerank", response_model=RerankResponse)
async def rerank(
    category: Optional[str] = Query(None, description="Category filter for candidate retrieval"),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    store: Optional[str] = Query(None),
    rerank_strategy: str = Query("baseline", description="Re-ranking strategy (baseline, hill_climbing, simulated_annealing)"),
    max_results: int = Query(20, ge=0, le=100, description="Max results to return"),
    k: int = Query(10, ge=1, le=100, description="NDCG@k cut-off for optimiser"),
    seed: Optional[int] = Query(None, description="RNG seed for simulated annealing"),
):
    """
    Re-rank Module 1 search results using a heuristic scoring function.

    Runs Module 1 candidate retrieval first, then applies a Module 2
    re-ranking strategy (baseline, hill_climbing, or simulated_annealing).
    """
    if not retrieval or not catalog or not ranker:
        raise HTTPException(503, "Catalog not loaded")

    if rerank_strategy not in RANKING_STRATEGIES:
        raise HTTPException(
            400,
            f"Invalid strategy '{rerank_strategy}'. "
            f"Choose from: {list(RANKING_STRATEGIES)}",
        )

    # Step 1: Module 1 candidate retrieval
    filters = SearchFilters(
        price_min=price_min,
        price_max=price_max,
        category=category,
        min_seller_rating=min_rating,
        store=store,
    )
    search_result: SearchResult = retrieval.search(filters)

    # Step 2: Module 2 heuristic re-ranking
    ranked: RankedResult = ranker.rank(
        search_result,
        strategy=rerank_strategy,
        target_category=category,
        max_results=max_results,
        k=k,
        seed=seed,
    )

    # Build response items with full product data
    items = [
        RerankItemResponse(
            product=ProductResponse.from_product(catalog[pid]),
            score=round(score, 4),
            rank=i + 1,
        )
        for i, (pid, score) in enumerate(ranked)
    ]

    return RerankResponse(
        items=items,
        metadata=RerankMetadata(
            strategy=ranked.strategy,
            iterations=ranked.iterations,
            objective_value=round(ranked.objective_value, 4),
            elapsed_ms=round(ranked.elapsed_ms, 3),
            count=len(items),
        ),
    )
