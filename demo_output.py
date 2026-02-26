"""Generate sample output evidence for Checkpoints 1 and 2."""
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

from src.module1 import CandidateRetrieval, SearchFilters, ProductCatalog, Product
from src.module2 import HeuristicRanker, ScoringConfig, DealFinder

# ── Demo catalog ──────────────────────────────────────────────────────
products = [
    Product(id="B07BJ7ZZL7", title="Silicone Watch Band",    price=14.89, category="Cell Phones & Accessories", seller_rating=4.4, store="QGHXO",       description="Premium silicone band.", rating_number=1247),
    Product(id="B08GFTPQ5B", title="USB-C Hub Adapter",      price=29.99, category="Computers",                 seller_rating=4.7, store="Anker",        description="7-in-1 USB-C hub with HDMI.", rating_number=3421, features=["HDMI", "USB 3.0", "SD"]),
    Product(id="B09XYZ1234", title="Wireless Earbuds",        price=39.99, category="Electronics",               seller_rating=4.2, store="Sony",         description="True wireless earbuds with ANC.", rating_number=892),
    Product(id="B07ABC9876", title="Laptop Stand Adjustable", price=24.50, category="Computers",                 seller_rating=4.8, store="Anker",        description="Ergonomic aluminium laptop stand.", rating_number=5103, features=["adjustable", "aluminium"]),
    Product(id="B06DEF5555", title="Phone Case Clear",        price=9.99,  category="Cell Phones & Accessories", seller_rating=3.9, store="Spigen",       description="Ultra-slim clear case.", rating_number=7892),
    Product(id="B05GHI7777", title="Mechanical Keyboard",     price=59.99, category="Computers",                 seller_rating=4.6, store="Logitech",     description="Full-size mechanical keyboard with Cherry MX switches." * 2, rating_number=2341, features=["Cherry MX", "RGB", "full-size"]),
    Product(id="B04JKL3333", title="HDMI Cable 6ft",          price=8.49,  category="Electronics",               seller_rating=4.1, store="AmazonBasics", description="4K HDMI 2.1 cable.", rating_number=12034),
    Product(id="B03MNO8888", title="Webcam HD 1080p",         price=34.99, category="Computers",                 seller_rating=4.5, store="Logitech",     description="1080p webcam with noise-reducing mic.", rating_number=4201, features=["1080p", "mic"]),
]

catalog = ProductCatalog(products)
retrieval = CandidateRetrieval(catalog)

# ══════════════════════════════════════════════════════════════════════
#  MODULE 1 — Candidate Retrieval
# ══════════════════════════════════════════════════════════════════════

print("=" * 65)
print("  MODULE 1: Candidate Retrieval")
print("=" * 65)

print("\n--- Example 1: Computers under $35 sorted by price ---")
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

print("\n--- Example 2: All categories, rating >= 4.5, sorted by rating ---")
filters2 = SearchFilters(min_seller_rating=4.5, sort_by="rating_desc")
result2 = retrieval.search(filters2, strategy="priority")
print(f"Candidates: {result2.candidate_ids}")
print(f"Count: {result2.count}  Strategy: {result2.strategy}  Scanned: {result2.total_scanned}  Elapsed: {result2.elapsed_ms:.2f}ms")
for pid in result2:
    p = catalog[pid]
    print(f"  {p.id} | {p.title:30s} | ${p.price:<7.2f} | rating {p.seller_rating}")

print("\n--- Example 3: No matches (non-existent category) ---")
result3 = retrieval.search(SearchFilters(category="Furniture"))
print(f"Candidates: {result3.candidate_ids}")
print(f"Count: {result3.count}")

# ══════════════════════════════════════════════════════════════════════
#  MODULE 2 — Heuristic Re-ranking
# ══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  MODULE 2: Heuristic Re-ranking")
print("=" * 65)

ranker = HeuristicRanker(catalog)

# Get Computers candidates for re-ranking
search_result = retrieval.search(SearchFilters(category="Computers"))
print(f"\nModule 1 candidates for 'Computers': {search_result.candidate_ids}")

for strategy in ("baseline", "hill_climbing", "simulated_annealing"):
    ranked = ranker.rank(
        search_result,
        strategy=strategy,
        target_category="Computers",
        k=5,
        seed=42,
    )
    print(f"\n--- Strategy: {strategy} ---")
    print(f"Iterations: {ranked.iterations}  NDCG@5: {ranked.objective_value:.4f}  Elapsed: {ranked.elapsed_ms:.3f}ms")
    for pid, score in ranked:
        p = catalog[pid]
        print(f"  {pid} | {p.title:30s} | ${p.price:<7.2f} | score {score:.4f}")

# ── Deal Finder ───────────────────────────────────────────────────────

print("\n" + "-" * 65)
print("  DEAL FINDER")
print("-" * 65)

finder = DealFinder(catalog)
deals = finder.get_deals(limit=5)

if deals:
    for pid, info in deals:
        p = catalog[pid]
        print(f"  {info.deal_type:12s} | {p.title:30s} | ${p.price:<7.2f} | "
              f"price {info.price_vs_avg:+.0f}% vs avg  rating {info.rating_vs_avg:+.0f}% vs avg")
else:
    print("  (No deals detected in demo catalog — requires more products per category)")
