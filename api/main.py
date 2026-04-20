"""
Epic Marketplace API — FastAPI wrapper for the AI search modules.

Exposes Module 1 (Candidate Retrieval), Module 2 (Heuristic Re-ranking),
Module 3 (Query Understanding), and Module 4 (Learning-to-Rank) as REST endpoints.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from functools import partial
from typing import List, Optional, Sequence

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
from src.module2 import HeuristicRanker, RankedResult, ScoringConfig, DealFinder
from src.module2.ranker import RANKING_STRATEGIES
from src.module3.query_understanding import QueryUnderstanding, QueryResult
from src.module3.embeddings import ProductEmbedder
from src.module4.pipeline import LearningToRankPipeline
from src.module4.training_data import TrainingDataGenerator
from src.module5.holdout import HeldOutSet
from src.module5.pipeline import EvaluationPipeline

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global state — populated at startup
# ---------------------------------------------------------------------------
catalog: Optional[ProductCatalog] = None
retrieval: Optional[CandidateRetrieval] = None
ranker: Optional[HeuristicRanker] = None
deal_finder: Optional[DealFinder] = None
query_understanding: Optional[QueryUnderstanding] = None
product_embedder: Optional[ProductEmbedder] = None
ltr_pipeline: Optional[LearningToRankPipeline] = None
# Cache of highly-rated product IDs keyed by rating threshold. Lazily
# populated the first time a given threshold is requested by /api/evaluate
# so startup stays fast.
highly_rated_ids_by_threshold: dict[float, frozenset[str]] = {}


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


class QueryUnderstandingInfo(BaseModel):
    """Module 3 query understanding results embedded in search response."""

    keywords: List[List] = Field(default_factory=list)
    inferred_category: Optional[str] = None
    confidence: float = 0.0
    corrected_query: Optional[str] = None


class SearchMetadata(BaseModel):
    """Search performance & strategy metadata."""

    strategy: str
    total_scanned: int
    elapsed_ms: float
    count: int
    total: int
    page: int
    page_size: int
    total_pages: int
    query_understanding: Optional[QueryUnderstandingInfo] = None
    # Module 4 (LTR) — lets the UI show whether learning-to-rank changed the order
    module4_ltr_requested: bool = True
    module4_ltr_applied: bool = False
    module4_trained_model: Optional[str] = None
    module4_training_cv_roc_auc: Optional[float] = None


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


class DealProductResponse(BaseModel):
    """A product with deal metadata."""

    product: ProductResponse
    deal_score: float
    deal_type: str
    price_vs_avg: float
    rating_vs_avg: float
    category_avg_price: float


class DealsResponse(BaseModel):
    """Payload returned by GET /api/deals."""

    deals: List[DealProductResponse]
    count: int


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
    global catalog, retrieval, ranker, deal_finder, query_understanding
    global product_embedder, ltr_pipeline
    catalog = _load_catalog()
    retrieval = CandidateRetrieval(catalog)
    ranker = HeuristicRanker(catalog)
    deal_finder = DealFinder(catalog)

    # Module 3: build NLP corpus from catalog and train models
    corpus_texts = [
        f"{p.title} {p.description or ''}" for p in catalog
    ]
    corpus_labels = [p.category for p in catalog]
    query_understanding = QueryUnderstanding(corpus_texts, corpus_labels)

    # Keep a reference to the embedder for Module 4
    product_embedder = query_understanding._embedder

    # Module 4: train LTR model on synthetic data (13 combined features)
    ltr_pipeline = LearningToRankPipeline()
    try:
        gen = TrainingDataGenerator(
            catalog=catalog,
            query_understanding=query_understanding,
            embedder=product_embedder,
        )
        X_train, y_train = gen.generate(max_products_per_query=50, seed=42)
        use_select = os.environ.get("LTR_MODEL_SELECT", "1").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        ltr_pipeline.fit(
            X=X_train,
            labels=list(y_train),
            select_best_model=use_select,
        )
        logger.info(
            "Module 4 LTR trained on %d examples (%d features), model=%s",
            X_train.shape[0],
            X_train.shape[1],
            ltr_pipeline.ranker.selected_model_name or "logistic_regression",
        )
    except Exception as exc:
        logger.warning("Module 4 LTR training skipped: %s", exc)

    logger.info(
        "API ready — %d products indexed, %d deals, Module 3 NLP + Module 4 LTR loaded",
        len(catalog),
        len(deal_finder.get_deals(limit=99999)),
    )
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
    out: dict = {"status": "ok", "products": len(catalog) if catalog else 0}
    if ltr_pipeline and ltr_pipeline.ranker.is_fitted:
        out["ltr"] = {
            "fitted": True,
            "model": ltr_pipeline.ranker.selected_model_name,
            "training_cv_mean_roc_auc": ltr_pipeline.ranker.cv_mean_roc_auc,
        }
    else:
        out["ltr"] = {"fitted": False}
    return out


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


@app.get("/api/products/{product_id}/similar", response_model=List[ProductResponse])
async def get_similar_products(
    product_id: str,
    limit: int = Query(8, ge=1, le=20),
):
    """
    Find products similar to the given product using Word2Vec embeddings.
    Uses the product's title + description as the query and ranks all
    other products by cosine similarity.
    """
    if not catalog or not query_understanding:
        raise HTTPException(503, "Catalog not loaded")
    try:
        product = catalog[product_id]
    except KeyError:
        raise HTTPException(404, f"Product not found: {product_id}")

    query_text = f"{product.title} {product.description or ''}"

    texts = {
        p.id: f"{p.title} {p.description or ''}"
        for p in catalog
        if p.id != product_id
    }
    titles = {p.id: p.title for p in catalog if p.id != product_id}

    ranked = query_understanding.search_by_text(
        query_text, texts, top_k=limit, titles=titles,
    )

    return [
        ProductResponse.from_product(catalog[pid])
        for pid, _ in ranked
    ]


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
    use_ltr: bool = Query(
        True,
        description="If true, apply Module 4 learning-to-rank after Module 3 (when fitted).",
    ),
):
    """
    Search for products matching filters.

    When `q` is provided, Module 3 (Query Understanding) extracts keywords,
    infers a category, and re-ranks candidates by embedding similarity.
    Set ``use_ltr=false`` to skip Module 4 and compare ranking with vs. without LTR.
    """
    if not retrieval or not catalog:
        raise HTTPException(503, "Catalog not loaded")

    qu_info: Optional[QueryUnderstandingInfo] = None
    qr: Optional[QueryResult] = None

    # --- Module 3: understand the query if provided ---
    effective_category = category
    if q and q.strip() and query_understanding:
        qr = query_understanding.understand(q)
        qu_info = QueryUnderstandingInfo(
            keywords=[[kw, round(sc, 4)] for kw, sc in qr.keywords],
            inferred_category=qr.inferred_category,
            confidence=round(qr.confidence, 4),
            corrected_query=qr.corrected_query,
        )
        # Use inferred category when user didn't pick one explicitly
        CATEGORY_CONFIDENCE_THRESHOLD = 0.4
        if not category and qr.inferred_category and qr.confidence >= CATEGORY_CONFIDENCE_THRESHOLD:
            effective_category = qr.inferred_category

    filters = SearchFilters(
        price_min=price_min,
        price_max=price_max,
        category=effective_category,
        min_seller_rating=min_rating,
        store=store,
        sort_by=sort_by,
    )

    result: SearchResult = retrieval.search(filters, strategy=strategy)

    # --- Module 3: re-rank by text relevance when q is present ---
    candidate_ids = result.candidate_ids
    module3_scores: Optional[dict[str, float]] = None
    if q and q.strip() and query_understanding and candidate_ids:
        texts = {
            pid: f"{catalog[pid].title} {catalog[pid].description or ''}"
            for pid in candidate_ids
        }
        titles = {pid: catalog[pid].title for pid in candidate_ids}
        ranked_pairs = query_understanding.search_by_text(
            q, texts, top_k=len(candidate_ids), titles=titles,
        )
        candidate_ids = [pid for pid, _ in ranked_pairs]
        module3_scores = {pid: score for pid, score in ranked_pairs}

    trained_model: Optional[str] = None
    training_cv_auc: Optional[float] = None
    if ltr_pipeline and ltr_pipeline.ranker.is_fitted:
        trained_model = ltr_pipeline.ranker.selected_model_name
        training_cv_auc = ltr_pipeline.ranker.cv_mean_roc_auc

    module4_applied = False
    # --- Module 4: LTR re-rank — refines Module 3's ordering ---
    if (
        use_ltr
        and ltr_pipeline
        and ltr_pipeline.ranker.is_fitted
        and candidate_ids
    ):
        try:
            ltr_products = [catalog[pid] for pid in candidate_ids]
            price_band = (price_min, price_max) if price_min is not None and price_max is not None else None
            ltr_scored = ltr_pipeline.rank(
                ltr_products,
                price_band=price_band,
                query_result=qr,
                embedder=product_embedder if qr else None,
                module3_scores=module3_scores,
            )
            # Blend Module 3 relevance with Module 4 quality so LTR
            # refines the text-relevance ordering rather than replacing it.
            if module3_scores:
                ltr_dict = {pid: score for pid, score in ltr_scored}
                blended = []
                for pid in ltr_dict:
                    m3 = module3_scores.get(pid, 0.0)
                    m4 = ltr_dict[pid]
                    blended.append((pid, 0.55 * m3 + 0.45 * m4))
                blended.sort(key=lambda x: x[1], reverse=True)
                candidate_ids = [pid for pid, _ in blended]
            else:
                candidate_ids = [pid for pid, _ in ltr_scored]
            module4_applied = True
        except Exception as exc:
            logger.warning("Module 4 LTR re-rank skipped: %s", exc)

    # Paginate
    total = len(candidate_ids)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_ids = candidate_ids[start:end]

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
            query_understanding=qu_info,
            module4_ltr_requested=use_ltr,
            module4_ltr_applied=module4_applied,
            module4_trained_model=trained_model,
            module4_training_cv_roc_auc=training_cv_auc,
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
    MAX_RERANK_CANDIDATES = 200
    search_result: SearchResult = retrieval.search(
        filters, max_results=MAX_RERANK_CANDIDATES,
    )

    # Step 2: Module 2 heuristic re-ranking (run in thread to avoid blocking)
    loop = asyncio.get_event_loop()
    ranked: RankedResult = await loop.run_in_executor(
        None,
        partial(
            ranker.rank,
            search_result,
            strategy=rerank_strategy,
            target_category=category,
            max_results=max_results,
            k=k,
            seed=seed,
        ),
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


@app.get("/api/deals", response_model=DealsResponse)
async def get_deals(
    category: Optional[str] = Query(None, description="Filter deals to one category"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Return top deals — products with unusually high value relative to
    their category peers.
    """
    if not deal_finder or not catalog:
        raise HTTPException(503, "Catalog not loaded")

    raw = deal_finder.get_deals(category=category, limit=limit)
    deals = [
        DealProductResponse(
            product=ProductResponse.from_product(catalog[pid]),
            deal_score=info.deal_score,
            deal_type=info.deal_type,
            price_vs_avg=info.price_vs_avg,
            rating_vs_avg=info.rating_vs_avg,
            category_avg_price=info.category_avg_price,
        )
        for pid, info in raw
    ]
    return DealsResponse(deals=deals, count=len(deals))


@app.get("/api/products/{product_id}/deal")
async def get_product_deal(product_id: str):
    """Return deal info for a specific product, or 404 if it's not a deal."""
    if not deal_finder:
        raise HTTPException(503, "Catalog not loaded")

    info = deal_finder.get_deal(product_id)
    if info is None:
        raise HTTPException(404, "This product is not currently flagged as a deal")

    return {
        "deal_score": info.deal_score,
        "deal_type": info.deal_type,
        "price_vs_avg": info.price_vs_avg,
        "rating_vs_avg": info.rating_vs_avg,
        "category_avg_price": info.category_avg_price,
    }


# ---------------------------------------------------------------------------
# Autocomplete
# ---------------------------------------------------------------------------
@app.get("/api/autocomplete")
async def autocomplete(
    q: str = Query("", description="Partial query text"),
    limit: int = Query(8, ge=1, le=20),
):
    """
    Fast prefix-match autocomplete against product titles and categories.
    Returns up to `limit` suggestions grouped by type.
    """
    if not catalog:
        raise HTTPException(503, "Catalog not loaded")

    needle = q.strip().lower()
    if not needle:
        return {"suggestions": []}

    seen: set[str] = set()
    suggestions: list[dict] = []

    categories = sorted({p.category for p in catalog})
    for cat in categories:
        if needle in cat.lower() and cat not in seen:
            suggestions.append({"text": cat, "type": "category"})
            seen.add(cat)
            if len(suggestions) >= limit:
                return {"suggestions": suggestions}

    for product in catalog:
        if len(suggestions) >= limit:
            break
        title = product.title
        if needle in title.lower() and title not in seen:
            display = title if len(title) <= 60 else title[:57] + "..."
            suggestions.append({"text": display, "type": "product", "id": product.id})
            seen.add(title)

    return {"suggestions": suggestions}


# ---------------------------------------------------------------------------
# Module 3: Query Understanding debug endpoint
# ---------------------------------------------------------------------------
@app.get("/api/query-understand")
async def query_understand(
    q: str = Query(..., description="Free-text query to analyze"),
):
    """
    Debug endpoint: run Module 3 NLP pipeline on a query and return
    keywords, embedding shape, inferred category, and confidence.
    """
    if not query_understanding:
        raise HTTPException(503, "Query understanding not loaded")

    qr: QueryResult = query_understanding.understand(q)

    return {
        "query": q,
        "keywords": [[kw, round(sc, 4)] for kw, sc in qr.keywords],
        "embedding_shape": list(qr.query_embedding.shape),
        "embedding_norm": round(float(qr.query_embedding.dot(qr.query_embedding) ** 0.5), 4),
        "inferred_category": qr.inferred_category,
        "confidence": round(qr.confidence, 4),
    }


# ---------------------------------------------------------------------------
# Module 5: Evaluation endpoint
# ---------------------------------------------------------------------------
class EvaluateRankedItem(BaseModel):
    """One item in the evaluated top-k list."""

    rank: int
    product: ProductResponse
    score: float
    relevant: bool


class EvaluateVariantResult(BaseModel):
    """A single ablation variant (use_ltr × use_query_understanding)."""

    label: str
    use_ltr: bool
    use_query_understanding: bool
    metrics: dict
    items: List[EvaluateRankedItem]


class EvaluateResponse(BaseModel):
    """Payload returned by GET /api/evaluate."""

    query: str
    category: Optional[str]
    k: int
    rating_threshold: float
    ground_truth: str
    candidate_pool_size: int
    relevant_count: int
    variants: List[EvaluateVariantResult]


def _query_tokens(q: str) -> List[str]:
    """Break a query into lower-cased alphanumeric tokens of length ≥ 3."""
    import re

    tokens = re.findall(r"[a-z0-9]+", q.lower())
    return [t for t in tokens if len(t) >= 3]


def _expand_tokens_via_module3(q: str) -> List[str]:
    """Return query tokens plus any Module 3 keywords / corrected spellings.

    Using Module 3 here lets the *hybrid* ground truth recognise synonyms and
    misspellings — e.g. "chargr" → ``charger`` — keeping the topicality check
    consistent with how the production search route interprets the query.
    """
    tokens = set(_query_tokens(q))
    if query_understanding is None:
        return sorted(tokens)
    try:
        qr = query_understanding.understand(q)
    except Exception:  # pragma: no cover
        return sorted(tokens)
    for kw in qr.keywords:
        word = kw[0] if isinstance(kw, (list, tuple)) else kw
        tokens.update(_query_tokens(str(word)))
    if qr.corrected_query:
        tokens.update(_query_tokens(qr.corrected_query))
    return sorted(tokens)


def _product_is_on_topic(
    product_id: str, tokens: Sequence[str],
) -> bool:
    """True if the product's title or description contains any query token."""
    if not tokens or catalog is None or product_id not in catalog:
        return False
    p = catalog[product_id]
    haystack = f"{p.title} {p.description or ''}".lower()
    return any(tok in haystack for tok in tokens)


def _load_highly_rated_ids(threshold: float) -> frozenset[str]:
    """Lazily parse the working-set reviews file and cache highly-rated IDs.

    A product is considered *positive* if at least one of its reviews has a
    rating >= ``threshold``. This is the same definition
    :func:`build_holdout_from_reviews` uses, kept as a cheap lookup set so
    per-request evaluation doesn't re-parse 50k reviews.
    """
    reviews_path = os.path.join(
        PROJECT_ROOT, "datasets", "working_set", "Electronics_50000.jsonl.gz",
    )
    if not os.path.isfile(reviews_path):
        raise HTTPException(
            503,
            f"Reviews file not found at {reviews_path}; cannot build holdout.",
        )
    import pandas as pd  # local import — pandas is heavy and only needed here

    df = pd.read_json(reviews_path, lines=True, compression="infer")
    df = df[["parent_asin", "rating"]].dropna()
    df["rating"] = df["rating"].astype(float)
    positive = df.loc[df["rating"] >= threshold, "parent_asin"].astype(str)
    ids = frozenset(positive.unique().tolist())
    logger.info(
        "Loaded %d highly-rated product IDs (rating >= %.1f) from reviews",
        len(ids),
        threshold,
    )
    return ids


@app.get("/api/evaluate", response_model=EvaluateResponse)
async def evaluate(
    q: str = Query(..., min_length=1, description="Free-text query to evaluate"),
    category: Optional[str] = Query(None, description="Category filter for the candidate pool"),
    k: int = Query(10, ge=1, le=50, description="Top-k cut-off for ranking + metrics"),
    use_ltr: bool = Query(True, description="Apply Module 4 LTR re-rank"),
    use_query_understanding: bool = Query(True, description="Include Module 3 features"),
    compare: bool = Query(False, description="Also run the other 3 ablation variants for comparison"),
    rating_threshold: float = Query(4.0, ge=1.0, le=5.0, description="Review rating ≥ threshold counts as relevant"),
    ground_truth: str = Query(
        "reviews",
        pattern="^(reviews|hybrid)$",
        description=(
            "Ground-truth definition. 'reviews' = any product with a review "
            ">= rating_threshold (quality only). 'hybrid' = that AND the "
            "product's title/description contains a query keyword "
            "(quality AND topicality)."
        ),
    ),
):
    """Run Module 5 evaluation for a single query and return metrics + top-k.

    Ground truth is derived from the working-set reviews: any product with at
    least one review at ``rating >= rating_threshold`` is considered relevant
    (capped to the retrieved candidate pool for this query/category). When
    ``ground_truth='hybrid'`` the relevant set is further narrowed to products
    whose title or description actually contains a query keyword — this is
    the recommended mode for demonstrating topical ranking quality because it
    closes the "high-rated but off-topic" loophole present in pure-review
    ground truth.

    When ``compare=True`` the endpoint also runs the three other ablation
    variants so the UI can show a side-by-side table.
    """
    if not (catalog and retrieval and ranker and ltr_pipeline):
        raise HTTPException(503, "Pipeline not ready")

    key = round(float(rating_threshold), 2)
    highly_rated_ids = highly_rated_ids_by_threshold.get(key)
    if highly_rated_ids is None:
        highly_rated_ids = await asyncio.to_thread(
            _load_highly_rated_ids, rating_threshold,
        )
        highly_rated_ids_by_threshold[key] = highly_rated_ids

    try:
        filters = SearchFilters(category=category) if category else SearchFilters()
    except Exception as exc:
        raise HTTPException(400, f"Invalid filters: {exc}")

    search_result = retrieval.search(filters)
    if search_result.count == 0:
        raise HTTPException(404, f"No candidates for category={category!r}")

    pool_ids = list(search_result.candidate_ids)
    quality_in_pool = {pid for pid in pool_ids if pid in highly_rated_ids}

    if ground_truth == "hybrid":
        tokens = _expand_tokens_via_module3(q)
        relevant_in_pool = {
            pid for pid in quality_in_pool if _product_is_on_topic(pid, tokens)
        }
    else:
        relevant_in_pool = quality_in_pool

    holdout = HeldOutSet()
    holdout.add(q, relevant_in_pool)

    pipeline = EvaluationPipeline(
        catalog=catalog,
        retrieval=retrieval,
        ranker=ranker,
        ltr_pipeline=ltr_pipeline,
        query_understanding=query_understanding,
        embedder=product_embedder,
    )

    if compare:
        combos = [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]
    else:
        combos = [(use_ltr, use_query_understanding)]

    def _label(u_ltr: bool, u_qu: bool) -> str:
        if u_ltr and u_qu:
            return "LTR + Query Understanding"
        if u_ltr and not u_qu:
            return "LTR only (quality features)"
        if not u_ltr and u_qu:
            return "Heuristic + Query Understanding"
        return "Heuristic only (Modules 1+2)"

    variants: List[EvaluateVariantResult] = []
    for u_ltr, u_qu in combos:
        result = await asyncio.to_thread(
            pipeline.evaluate,
            q,
            filters,
            holdout,
            k,
            "baseline",
            use_ltr=u_ltr,
            use_query_understanding=u_qu,
        )
        items: List[EvaluateRankedItem] = []
        for idx, res in enumerate(result.payload.results, start=1):
            pid = res["id"]
            product = catalog.get(pid) if catalog else None
            if product is None:
                continue
            items.append(
                EvaluateRankedItem(
                    rank=idx,
                    product=ProductResponse.from_product(product),
                    score=float(res["score"]),
                    relevant=pid in relevant_in_pool,
                )
            )
        variants.append(
            EvaluateVariantResult(
                label=_label(u_ltr, u_qu),
                use_ltr=u_ltr,
                use_query_understanding=u_qu,
                metrics={k_: round(float(v), 4) for k_, v in result.metrics.items()},
                items=items,
            )
        )

    return EvaluateResponse(
        query=q,
        category=category,
        k=k,
        rating_threshold=rating_threshold,
        ground_truth=ground_truth,
        candidate_pool_size=len(pool_ids),
        relevant_count=len(relevant_in_pool),
        variants=variants,
    )
