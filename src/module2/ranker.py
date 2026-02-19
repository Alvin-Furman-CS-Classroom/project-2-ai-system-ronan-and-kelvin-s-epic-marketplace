"""
Heuristic re-ranking engine for the Epic Marketplace.

Takes Module 1's ``SearchResult`` (a list of candidate IDs) together with
the ``ProductCatalog`` and produces a **scored, re-ordered** list using one
of three strategies:

- **baseline** — sort candidates by weighted heuristic score.
- **hill_climbing** — steepest-ascent local search that iteratively swaps
  adjacent items to maximise a top-k ranking objective (NDCG@k).
- **simulated_annealing** — probabilistic optimisation that accepts worse
  swaps with decreasing probability, enabling escape from local optima.

The output is a ``RankedResult`` frozen dataclass containing
``(product_id, score)`` tuples in descending-score order, plus metadata
(strategy name, iterations, objective value, elapsed time).
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import SearchResult
from src.module2.exceptions import EmptyCandidatesError, RankingError
from src.module2.scorer import ScoringConfig, compute_feature_ranges, compute_score

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ranking strategies
# ---------------------------------------------------------------------------
RANKING_STRATEGIES = ("baseline", "hill_climbing", "simulated_annealing")


# ---------------------------------------------------------------------------
# Output container
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RankedResult:
    """Immutable container for re-ranking output.

    Attributes:
        ranked_candidates: ``(product_id, score)`` tuples in rank order
                           (highest score first).
        strategy: The re-ranking strategy that was used.
        iterations: Number of optimiser iterations (0 for baseline).
        objective_value: Final objective (NDCG@k) of the ranking.
        elapsed_ms: Wall-clock time of the re-ranking in milliseconds.

    Example:
        >>> result = RankedResult(
        ...     ranked_candidates=[("p89", 0.73), ("p12", 0.70)],
        ...     strategy="hill_climbing",
        ...     iterations=42,
        ...     objective_value=0.95,
        ...     elapsed_ms=1.2,
        ... )
        >>> len(result)
        2
    """

    ranked_candidates: List[Tuple[str, float]]
    strategy: str
    iterations: int
    objective_value: float
    elapsed_ms: float

    @property
    def count(self) -> int:
        """Number of ranked candidates."""
        return len(self.ranked_candidates)

    def __iter__(self):
        """Iterate over ``(product_id, score)`` tuples."""
        return iter(self.ranked_candidates)

    def __len__(self) -> int:
        return len(self.ranked_candidates)

    @property
    def ids(self) -> List[str]:
        """Just the product IDs in rank order."""
        return [pid for pid, _ in self.ranked_candidates]

    @property
    def scores(self) -> List[float]:
        """Just the scores in rank order."""
        return [s for _, s in self.ranked_candidates]


# ---------------------------------------------------------------------------
# NDCG@k objective
# ---------------------------------------------------------------------------

def _dcg(scores: List[float], k: int) -> float:
    """Discounted Cumulative Gain at position *k*.

    Args:
        scores: Relevance scores in rank order.
        k: Cut-off position.

    Returns:
        DCG@k value.
    """
    total = 0.0
    for i, s in enumerate(scores[:k]):
        total += s / math.log2(i + 2)  # i+2 because rank is 1-based
    return total


def ndcg_at_k(scores: List[float], k: int) -> float:
    """Normalised Discounted Cumulative Gain at position *k*.

    Measures how close the current ordering is to the ideal (sorted
    descending by score).  Returns 1.0 for a perfect ordering.

    Args:
        scores: Relevance scores in current rank order.
        k: Cut-off position.

    Returns:
        NDCG@k in [0, 1].  Returns 1.0 if all scores are zero.
    """
    if not scores or k <= 0:
        return 1.0
    ideal = sorted(scores, reverse=True)
    ideal_dcg = _dcg(ideal, k)
    if ideal_dcg == 0:
        return 1.0
    return _dcg(scores, k) / ideal_dcg


# ---------------------------------------------------------------------------
# Hill-climbing optimiser
# ---------------------------------------------------------------------------

def _hill_climb(
    ordering: List[Tuple[str, float]],
    k: int,
    max_iterations: int = 500,
    patience: int = 50,
) -> Tuple[List[Tuple[str, float]], int, float]:
    """Steepest-ascent hill climbing over adjacent swaps.

    At each iteration, the algorithm tries every adjacent-pair swap and
    keeps the one that maximises NDCG@k.  Stops when no swap improves the
    objective or after *patience* consecutive non-improving iterations.

    Args:
        ordering: Current ``(id, score)`` ranking.
        k: NDCG cut-off.
        max_iterations: Hard cap on iterations.
        patience: Stop after this many rounds with no improvement.

    Returns:
        ``(best_ordering, iterations, best_ndcg)``
    """
    best = list(ordering)
    best_ndcg = ndcg_at_k([s for _, s in best], k)
    stale = 0
    iterations = 0

    for _ in range(max_iterations):
        iterations += 1
        improved = False

        for i in range(len(best) - 1):
            candidate = list(best)
            candidate[i], candidate[i + 1] = candidate[i + 1], candidate[i]
            score = ndcg_at_k([s for _, s in candidate], k)
            if score > best_ndcg:
                best = candidate
                best_ndcg = score
                improved = True

        if improved:
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break

    return best, iterations, best_ndcg


# ---------------------------------------------------------------------------
# Simulated-annealing optimiser
# ---------------------------------------------------------------------------

def _simulated_annealing(
    ordering: List[Tuple[str, float]],
    k: int,
    initial_temp: float = 1.0,
    cooling_rate: float = 0.995,
    min_temp: float = 0.001,
    max_iterations: int = 2000,
    seed: Optional[int] = None,
) -> Tuple[List[Tuple[str, float]], int, float]:
    """Simulated annealing over random pair swaps.

    Accepts worse orderings with probability ``exp(-Δ / T)`` where *T*
    decreases geometrically.  This allows escaping local optima early.

    Args:
        ordering: Current ``(id, score)`` ranking.
        k: NDCG cut-off.
        initial_temp: Starting temperature.
        cooling_rate: Multiplicative decay per iteration (0 < α < 1).
        min_temp: Temperature at which to stop.
        max_iterations: Hard cap on iterations.
        seed: Optional RNG seed for reproducibility.

    Returns:
        ``(best_ordering, iterations, best_ndcg)``
    """
    rng = random.Random(seed)
    current = list(ordering)
    current_ndcg = ndcg_at_k([s for _, s in current], k)
    best = list(current)
    best_ndcg = current_ndcg
    temp = initial_temp
    iterations = 0

    for _ in range(max_iterations):
        if temp < min_temp:
            break
        iterations += 1

        # Pick two random distinct positions and swap
        n = len(current)
        if n < 2:
            break
        i, j = rng.sample(range(n), 2)
        candidate = list(current)
        candidate[i], candidate[j] = candidate[j], candidate[i]

        cand_ndcg = ndcg_at_k([s for _, s in candidate], k)
        delta = cand_ndcg - current_ndcg

        if delta > 0 or rng.random() < math.exp(delta / temp):
            current = candidate
            current_ndcg = cand_ndcg
            if current_ndcg > best_ndcg:
                best = list(current)
                best_ndcg = current_ndcg

        temp *= cooling_rate

    return best, iterations, best_ndcg


# ---------------------------------------------------------------------------
# Main ranker
# ---------------------------------------------------------------------------

class HeuristicRanker:
    """Re-ranks Module 1 candidates using a heuristic scoring function.

    The ranker scores each candidate product using a configurable weighted
    formula (see :class:`ScoringConfig`), then optionally optimises the
    ordering with hill climbing or simulated annealing.

    Args:
        catalog: The product catalog (used to look up product features).
        config: Scoring weight configuration.  Defaults to balanced weights.

    Example:
        >>> from src.module1 import ProductCatalog, Product, CandidateRetrieval, SearchFilters
        >>> products = [
        ...     Product(id="a", title="Mug", price=18, category="home",
        ...             seller_rating=4.8, store="S"),
        ...     Product(id="b", title="Vase", price=35, category="home",
        ...             seller_rating=4.5, store="S"),
        ... ]
        >>> catalog = ProductCatalog(products)
        >>> retrieval = CandidateRetrieval(catalog)
        >>> result = retrieval.search(SearchFilters(category="home"))
        >>> ranker = HeuristicRanker(catalog)
        >>> ranked = ranker.rank(result)
        >>> ranked.strategy
        'baseline'
    """

    def __init__(
        self,
        catalog: ProductCatalog,
        config: Optional[ScoringConfig] = None,
    ) -> None:
        self._catalog = catalog
        self._config = config or ScoringConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rank(
        self,
        search_result: SearchResult,
        strategy: str = "baseline",
        target_category: Optional[str] = None,
        max_results: Optional[int] = None,
        k: int = 10,
        seed: Optional[int] = None,
    ) -> RankedResult:
        """Re-rank candidates from a Module 1 ``SearchResult``.

        Args:
            search_result: Module 1 output containing ``candidate_ids``.
            strategy: One of ``"baseline"``, ``"hill_climbing"``,
                      ``"simulated_annealing"``.
            target_category: Optional category for the category-match
                             scoring component.
            max_results: Truncate the final ranking to this many items.
            k: NDCG cut-off for the optimiser objective.
            seed: Optional RNG seed (simulated annealing only).

        Returns:
            A :class:`RankedResult` with scored, re-ordered candidates.

        Raises:
            RankingError: If *strategy* is not recognised.
        """
        if strategy not in RANKING_STRATEGIES:
            raise RankingError(
                f"Unknown ranking strategy '{strategy}'. "
                f"Choose from: {RANKING_STRATEGIES}"
            )

        start = time.perf_counter()

        # --- resolve products ---
        products = self._resolve_products(search_result.candidate_ids)

        if not products:
            return RankedResult(
                ranked_candidates=[],
                strategy=strategy,
                iterations=0,
                objective_value=1.0,
                elapsed_ms=0.0,
            )

        # --- score every candidate ---
        feature_ranges = compute_feature_ranges(products)
        scored: List[Tuple[str, float]] = []
        for p in products:
            s = compute_score(p, self._config, feature_ranges, target_category)
            scored.append((p.id, s))

        # --- baseline: sort descending by score ---
        scored.sort(key=lambda t: t[1], reverse=True)
        baseline_ndcg = ndcg_at_k([s for _, s in scored], k)

        # --- apply optimiser ---
        iterations = 0
        objective = baseline_ndcg

        if strategy == "hill_climbing":
            scored, iterations, objective = _hill_climb(scored, k)
        elif strategy == "simulated_annealing":
            scored, iterations, objective = _simulated_annealing(
                scored, k, seed=seed
            )

        # --- truncate ---
        if max_results is not None and max_results >= 0:
            scored = scored[:max_results]

        elapsed = (time.perf_counter() - start) * 1000

        return RankedResult(
            ranked_candidates=scored,
            strategy=strategy,
            iterations=iterations,
            objective_value=objective,
            elapsed_ms=round(elapsed, 3),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_products(self, candidate_ids: List[str]) -> List[Product]:
        """Look up products from the catalog, skipping missing IDs.

        Args:
            candidate_ids: Product IDs from Module 1.

        Returns:
            List of :class:`Product` objects (order preserved).
        """
        products: List[Product] = []
        for pid in candidate_ids:
            product = self._catalog.get(pid)
            if product is not None:
                products.append(product)
            else:
                logger.warning("Product ID '%s' not found in catalog — skipping", pid)
        return products
