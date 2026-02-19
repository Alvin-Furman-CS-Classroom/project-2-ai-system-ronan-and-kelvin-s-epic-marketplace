"""
Simulated-annealing parameter tuning script.

Grid-searches over SA hyper-parameters (initial_temp, cooling_rate, min_temp)
using the working-set catalog and reports the best configuration by NDCG@k.

Usage:
    python -m src.module2.tune_sa

Runs CandidateRetrieval.search() to get candidates, scores them with the
heuristic, then calls the SA optimiser directly (since HeuristicRanker.rank()
does not expose SA parameters) over a parameter grid. Reports best params
and NDCG@k.
"""

import itertools
import logging
from pathlib import Path

from src.module1 import (
    CandidateRetrieval,
    ProductCatalog,
    SearchFilters,
    load_catalog_from_working_set,
)
from src.module2.ranker import _simulated_annealing, ndcg_at_k
from src.module2.scorer import ScoringConfig, compute_feature_ranges, compute_score

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _load_catalog(max_products: int | None = 500) -> ProductCatalog:
    """Load catalog from working set, or raise if unavailable."""
    repo_root = Path(__file__).resolve().parents[2]
    working_set = repo_root / "datasets" / "working_set"
    if not working_set.is_dir():
        raise FileNotFoundError(
            f"Working set not found at {working_set}. "
            "Ensure datasets/working_set/ exists with meta_Electronics_50000.jsonl.gz."
        )
    return load_catalog_from_working_set(
        working_set_dir=str(working_set), max_products=max_products
    )


def _get_scored_candidates(
    catalog: ProductCatalog,
    search_result,
    config: ScoringConfig,
    target_category: str | None = None,
) -> list[tuple[str, float]]:
    """Build (id, score) list from SearchResult using the heuristic scorer."""
    products = [
        catalog[pid]
        for pid in search_result.candidate_ids
        if catalog.get(pid) is not None
    ]
    if not products:
        return []

    feature_ranges = compute_feature_ranges(products)
    scored = [
        (p.id, compute_score(p, config, feature_ranges, target_category))
        for p in products
    ]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


def main() -> None:
    """Run SA parameter tuning and print best configuration."""
    logger.info("Loading catalog...")
    catalog = _load_catalog(max_products=500)
    retrieval = CandidateRetrieval(catalog)
    config = ScoringConfig()

    # Representative search to get candidates (mix of categories/filters)
    filters = SearchFilters(
        price_min=10,
        price_max=100,
        min_seller_rating=4.0,
    )
    search_result = retrieval.search(filters, strategy="linear")

    if search_result.count < 5:
        logger.warning(
            "Only %d candidates — consider relaxing filters or adding catalog data.",
            search_result.count,
        )

    scored = _get_scored_candidates(catalog, search_result, config)
    if not scored:
        logger.error("No scored candidates. Aborting.")
        return

    k = min(10, len(scored))
    seed = 42

    # Parameter grid for SA
    param_grid = {
        "initial_temp": [0.5, 1.0, 2.0, 5.0],
        "cooling_rate": [0.99, 0.995, 0.998],
        "min_temp": [0.001, 0.01, 0.1],
    }

    best_ndcg = -1.0
    best_params: dict | None = None
    n_combos = 0

    for initial_temp, cooling_rate, min_temp in itertools.product(
        param_grid["initial_temp"],
        param_grid["cooling_rate"],
        param_grid["min_temp"],
    ):
        n_combos += 1
        ordering, iterations, ndcg = _simulated_annealing(
            list(scored),
            k=k,
            initial_temp=initial_temp,
            cooling_rate=cooling_rate,
            min_temp=min_temp,
            seed=seed,
        )
        if ndcg > best_ndcg:
            best_ndcg = ndcg
            best_params = {
                "initial_temp": initial_temp,
                "cooling_rate": cooling_rate,
                "min_temp": min_temp,
            }

        if n_combos % 10 == 0:
            logger.info("  %d/%d combos evaluated...", n_combos, len(param_grid["initial_temp"]) * len(param_grid["cooling_rate"]) * len(param_grid["min_temp"]))

    baseline_ndcg = ndcg_at_k([s for _, s in scored], k)
    logger.info("")
    logger.info("Baseline (sorted by heuristic, no SA): NDCG@%d = %.4f", k, baseline_ndcg)
    logger.info("Best SA config: %s", best_params)
    logger.info("Best SA NDCG@%d = %.4f", k, best_ndcg)
    logger.info("Improvement: %.2f%%", 100 * (best_ndcg - baseline_ndcg) / max(baseline_ndcg, 1e-9))


if __name__ == "__main__":
    main()
