"""
Candidate retrieval using search algorithms.

Implements uninformed (BFS/DFS) and informed (A*-style priority) search
to find products matching hard constraints, with optional result sorting.

Search-Space Formulation
------------------------
The product catalog is modelled as a three-level tree:

    root
    ├── Category A
    │   ├── Store X  →  [product1, product2, …]
    │   └── Store Y  →  [product3, …]
    └── Category B
        └── Store Z  →  [product4, …]

*BFS* explores the tree **level-by-level** (all categories, then all stores,
then all products), which guarantees the *shallowest* matches are found first.

*DFS* dives **deep** into a single category/store branch before backtracking,
which uses less memory on wide catalogs and can find a match faster when items
cluster in one branch.

*Priority search* (A*-style) pushes every product onto a min-heap scored by a
heuristic that estimates how far the product is from satisfying the filters.
Products closer to matching are popped first, so early results tend to be the
best candidates.

*Linear scan* serves as the baseline — it iterates over every product in
insertion order with no pruning.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import heapq

from .exceptions import UnknownSearchStrategyError
from .filters import SearchFilters
from .catalog import ProductCatalog, Product

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    """Immutable container for search output.

    Attributes:
        candidate_ids: Product IDs matching the filters.
        strategy: The search strategy that was used.
        total_scanned: How many products were examined.
        elapsed_ms: Wall-clock time of the search in milliseconds.
    """

    candidate_ids: List[str]
    strategy: str
    total_scanned: int
    elapsed_ms: float

    @property
    def count(self) -> int:
        """Number of candidates returned."""
        return len(self.candidate_ids)

    def __iter__(self):
        """Allow unpacking / iteration over candidate IDs."""
        return iter(self.candidate_ids)

    def __len__(self) -> int:
        return len(self.candidate_ids)


# ---------------------------------------------------------------------------
# Search-tree node
# ---------------------------------------------------------------------------

@dataclass
class SearchNode:
    """A node in the catalog search tree.

    The tree has three levels::

        root  (depth 0)
         └── category  (depth 1)
              └── store  (depth 2)
                   └── product  (depth 3, leaf)

    Attributes:
        name: Human-readable label (category name, store name, or product ID).
        depth: Level in the tree (0 = root, 3 = product leaf).
        children: Ordered child node names.  Populated by
                  :meth:`CandidateRetrieval._build_search_tree`.
        product_id: Set only for leaf nodes — the actual product ID.
    """

    name: str
    depth: int = 0
    children: List[str] = field(default_factory=list)
    product_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Catalog search tree builder & retrieval engine
# ---------------------------------------------------------------------------

CatalogTree = Dict[str, SearchNode]


class CandidateRetrieval:
    """Retrieves candidate products that match search filters.

    Implements multiple search strategies over a **catalog search tree**
    (Category → Store → Product):

    - **linear** — flat O(n) scan (baseline).
    - **bfs** — breadth-first tree traversal; explores all categories before
      diving into stores, then products.
    - **dfs** — depth-first tree traversal; fully explores one
      category/store branch before backtracking.
    - **priority** — A*-style informed search using a heuristic that
      estimates filter-distance.

    All strategies return the **same candidate set** for identical filters
    (recall equivalence), only the *traversal order* differs.

    Example::

        >>> catalog = ProductCatalog(products)
        >>> retrieval = CandidateRetrieval(catalog)
        >>> filters = SearchFilters(price_min=10, price_max=40,
        ...                         category="Computers", sort_by="price_asc")
        >>> result = retrieval.search(filters)
        >>> print(result.candidate_ids)
    """

    STRATEGIES = ("linear", "bfs", "dfs", "priority")

    def __init__(self, catalog: ProductCatalog):
        """Initialize the retrieval system.

        Args:
            catalog: The product catalog to search.
        """
        self.catalog = catalog
        self._tree: CatalogTree = {}
        self._build_search_tree()

    # ------------------------------------------------------------------
    # Tree construction
    # ------------------------------------------------------------------

    def _build_search_tree(self) -> None:
        """Build a Category → Store → Product search tree from the catalog.

        The resulting tree is stored in ``self._tree`` as a flat dict of
        :class:`SearchNode` objects keyed by node name.  The root node is
        always ``"root"``.
        """
        # Group products by (category, store)
        cat_store: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for product in self.catalog:
            cat_key = product.category.lower()
            store_key = product.store.lower() if product.store else "unknown"
            cat_store[cat_key][store_key].append(product.id)

        root = SearchNode(name="root", depth=0)
        self._tree = {"root": root}

        for cat_name in sorted(cat_store):
            cat_node_name = f"cat:{cat_name}"
            cat_node = SearchNode(name=cat_node_name, depth=1)
            root.children.append(cat_node_name)
            self._tree[cat_node_name] = cat_node

            for store_name in sorted(cat_store[cat_name]):
                store_node_name = f"store:{cat_name}/{store_name}"
                store_node = SearchNode(name=store_node_name, depth=2)
                cat_node.children.append(store_node_name)
                self._tree[store_node_name] = store_node

                for pid in cat_store[cat_name][store_name]:
                    leaf_name = f"product:{pid}"
                    leaf = SearchNode(
                        name=leaf_name, depth=3, product_id=pid
                    )
                    store_node.children.append(leaf_name)
                    self._tree[leaf_name] = leaf

    # ------------------------------------------------------------------
    # Filter helpers
    # ------------------------------------------------------------------

    def matches_filters(self, product: Product, filters: SearchFilters) -> bool:
        """Check if a product satisfies all filter constraints.

        Args:
            product: The product to check.
            filters: The filter constraints.

        Returns:
            True if the product matches all filters, False otherwise.
        """
        if filters.price_min is not None and product.price < filters.price_min:
            return False
        if filters.price_max is not None and product.price > filters.price_max:
            return False
        if filters.category is not None:
            if product.category.lower() != filters.category.lower():
                return False
        if filters.min_seller_rating is not None:
            if product.seller_rating < filters.min_seller_rating:
                return False
        if filters.store is not None:
            if product.store.lower() != filters.store.lower():
                return False
        return True

    def _can_prune_node(self, node: SearchNode, filters: SearchFilters) -> bool:
        """Return True if the subtree rooted at *node* cannot contain matches.

        Category-level and store-level nodes can be pruned when the filter
        is known to exclude them, avoiding unnecessary expansion.

        Args:
            node: A search-tree node.
            filters: Active search filters.

        Returns:
            True if the subtree should be skipped.
        """
        if node.depth == 1 and filters.category is not None:
            # cat:electronics  →  extract "electronics"
            cat_label = node.name.split(":", 1)[1]
            if cat_label != filters.category.lower():
                return True
        if node.depth == 2 and filters.store is not None:
            # store:electronics/anker  →  extract "anker"
            store_label = node.name.rsplit("/", 1)[1]
            if store_label != filters.store.lower():
                return True
        return False

    def _sort_candidates(self, candidate_ids: List[str], sort_by: str) -> List[str]:
        """Sort candidate IDs by the given sort criterion.

        Args:
            candidate_ids: List of product IDs to sort.
            sort_by: Sort key — ``"price_asc"``, ``"price_desc"``,
                     ``"rating_desc"``, or ``"rating_asc"``.

        Returns:
            Sorted list of product IDs.
        """
        if sort_by == "price_asc":
            return sorted(candidate_ids, key=lambda pid: self.catalog[pid].price)
        elif sort_by == "price_desc":
            return sorted(candidate_ids, key=lambda pid: self.catalog[pid].price, reverse=True)
        elif sort_by == "rating_desc":
            return sorted(candidate_ids, key=lambda pid: self.catalog[pid].seller_rating, reverse=True)
        elif sort_by == "rating_asc":
            return sorted(candidate_ids, key=lambda pid: self.catalog[pid].seller_rating)
        return candidate_ids

    # ------------------------------------------------------------------
    # Public search entry-point
    # ------------------------------------------------------------------

    def search(
        self,
        filters: SearchFilters,
        strategy: str = "linear",
        max_results: Optional[int] = None,
    ) -> SearchResult:
        """Search for candidate products matching filters.

        Args:
            filters: The search filters (hard constraints + optional sort).
            strategy: Search strategy — ``"linear"``, ``"bfs"``, ``"dfs"``,
                      or ``"priority"``.
            max_results: Maximum number of results to return. None for all.

        Returns:
            SearchResult containing matching product IDs and metadata.

        Raises:
            UnknownSearchStrategyError: If strategy is not recognized.
        """
        start = time.perf_counter()

        if strategy == "linear":
            candidates, scanned = self._linear_search(filters)
        elif strategy == "bfs":
            candidates, scanned = self._bfs_search(filters)
        elif strategy == "dfs":
            candidates, scanned = self._dfs_search(filters)
        elif strategy == "priority":
            candidates, scanned = self._priority_search(filters)
        else:
            raise UnknownSearchStrategyError(
                f"Unknown search strategy: {strategy}. "
                f"Choose from {self.STRATEGIES}"
            )

        # Apply sorting if requested
        if filters.sort_by is not None:
            candidates = self._sort_candidates(candidates, filters.sort_by)

        # Apply max_results after sorting
        if max_results is not None:
            candidates = candidates[:max_results]

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "strategy=%s filters=%s candidates=%d scanned=%d elapsed=%.2fms",
            strategy,
            filters.to_dict(),
            len(candidates),
            scanned,
            elapsed_ms,
        )
        return SearchResult(
            candidate_ids=candidates,
            strategy=strategy,
            total_scanned=scanned,
            elapsed_ms=elapsed_ms,
        )

    # ------------------------------------------------------------------
    # Strategy: linear scan (baseline)
    # ------------------------------------------------------------------

    def _linear_search(self, filters: SearchFilters) -> tuple[List[str], int]:
        """Linear scan through all products (baseline).

        Time: O(n) where n = catalog size.
        Space: O(k) where k = number of matches.

        Returns:
            Tuple of (candidate IDs, total products scanned).
        """
        candidates: List[str] = []
        scanned = 0
        for product in self.catalog:
            scanned += 1
            if self.matches_filters(product, filters):
                candidates.append(product.id)
        return candidates, scanned

    # ------------------------------------------------------------------
    # Strategy: BFS (breadth-first tree traversal)
    # ------------------------------------------------------------------

    def _bfs_search(self, filters: SearchFilters) -> tuple[List[str], int]:
        """Breadth-first search over the catalog tree.

        Explores **level-by-level**: all category nodes first, then all
        store nodes, then all product leaves.  Category- and store-level
        pruning skips entire subtrees that cannot match the filters.

        Time: O(n) worst-case, often less when pruning is effective.
        Space: O(w) where w = max tree width at any level.

        Returns:
            Tuple of (candidate IDs, total products scanned).
        """
        candidates: List[str] = []
        scanned = 0
        queue: deque[str] = deque(["root"])
        visited: Set[str] = set()

        while queue:
            node_name = queue.popleft()
            if node_name in visited:
                continue
            visited.add(node_name)

            node = self._tree.get(node_name)
            if node is None:
                continue

            # Prune non-matching category / store branches
            if self._can_prune_node(node, filters):
                continue

            # Leaf node → check the actual product
            if node.product_id is not None:
                scanned += 1
                product = self.catalog.get(node.product_id)
                if product and self.matches_filters(product, filters):
                    candidates.append(node.product_id)
            else:
                # Internal node → enqueue children (breadth-first)
                for child_name in node.children:
                    if child_name not in visited:
                        queue.append(child_name)

        return candidates, scanned

    # ------------------------------------------------------------------
    # Strategy: DFS (depth-first tree traversal)
    # ------------------------------------------------------------------

    def _dfs_search(self, filters: SearchFilters) -> tuple[List[str], int]:
        """Depth-first search over the catalog tree.

        Dives **deep** into one category/store branch and checks all its
        products before backtracking to the next branch.  Category- and
        store-level pruning avoids expanding irrelevant subtrees.

        Time: O(n) worst-case, often less when pruning is effective.
        Space: O(d) where d = tree depth (always 4 levels).

        Returns:
            Tuple of (candidate IDs, total products scanned).
        """
        candidates: List[str] = []
        scanned = 0
        stack: List[str] = ["root"]
        visited: Set[str] = set()

        while stack:
            node_name = stack.pop()
            if node_name in visited:
                continue
            visited.add(node_name)

            node = self._tree.get(node_name)
            if node is None:
                continue

            # Prune non-matching category / store branches
            if self._can_prune_node(node, filters):
                continue

            # Leaf node → check the actual product
            if node.product_id is not None:
                scanned += 1
                product = self.catalog.get(node.product_id)
                if product and self.matches_filters(product, filters):
                    candidates.append(node.product_id)
            else:
                # Internal node → push children in reverse so first child
                # is popped first (preserves left-to-right DFS order)
                for child_name in reversed(node.children):
                    if child_name not in visited:
                        stack.append(child_name)

        return candidates, scanned

    # ------------------------------------------------------------------
    # Strategy: priority / A*-style informed search
    # ------------------------------------------------------------------

    def _priority_search(self, filters: SearchFilters) -> tuple[List[str], int]:
        """Priority-based informed search (A*-style).

        Uses a heuristic to prioritize products more likely to match.
        The heuristic estimates how "close" a product is to satisfying filters.

        Time: O(n log n) due to heap operations.
        Space: O(n) for priority queue.

        Returns:
            Tuple of (candidate IDs, total products scanned).
        """
        candidates: List[str] = []
        scanned = 0
        visited: Set[str] = set()
        pq: List[tuple[float, str]] = []

        for product_id in self.catalog.product_ids:
            product = self.catalog.get(product_id)
            if product:
                priority = self._compute_priority(product, filters)
                heapq.heappush(pq, (priority, product_id))

        while pq:
            _, product_id = heapq.heappop(pq)
            if product_id in visited:
                continue
            visited.add(product_id)
            scanned += 1

            product = self.catalog.get(product_id)
            if product and self.matches_filters(product, filters):
                candidates.append(product_id)

        return candidates, scanned

    def _compute_priority(self, product: Product, filters: SearchFilters) -> float:
        """Compute priority score for a product (lower = better).

        This is the heuristic function for informed search.
        It estimates how likely a product is to match the filters.

        Args:
            product: The product to evaluate.
            filters: The search filters.

        Returns:
            Priority score (0 = perfect match candidate, higher = worse).
        """
        priority = 0.0

        if filters.price_min is not None and product.price < filters.price_min:
            priority += filters.price_min - product.price
        if filters.price_max is not None and product.price > filters.price_max:
            priority += product.price - filters.price_max

        if filters.category is not None:
            if product.category.lower() != filters.category.lower():
                priority += 100  # Large penalty for wrong category

        if filters.min_seller_rating is not None:
            if product.seller_rating < filters.min_seller_rating:
                priority += (filters.min_seller_rating - product.seller_rating) * 10

        if filters.store is not None:
            if product.store.lower() != filters.store.lower():
                priority += 75  # Significant penalty for wrong store

        return priority

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def get_candidates_with_products(
        self,
        filters: SearchFilters,
        strategy: str = "linear",
    ) -> List[Product]:
        """Get full Product objects for candidates (convenience method).

        Args:
            filters: The search filters.
            strategy: Search strategy to use.

        Returns:
            List of Product objects that match the filters.
        """
        result = self.search(filters, strategy)
        return [self.catalog[pid] for pid in result.candidate_ids]
