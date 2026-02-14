"""
Candidate retrieval using search algorithms.

Implements uninformed (BFS/DFS) and informed (A*-style priority) search
to find products matching hard constraints, with optional result sorting.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Set
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


@dataclass
class SearchState:
    """
    A state in the search space.
    
    Attributes:
        product_id: The product being evaluated.
        depth: Search depth (for BFS/DFS tracking).
    """
    product_id: str
    depth: int = 0


class CandidateRetrieval:
    """
    Retrieves candidate products that match search filters.
    
    Implements multiple search strategies:
    - Linear scan (baseline)
    - BFS-style breadth-first filtering
    - DFS-style depth-first filtering  
    - Priority-based informed search (A*-style with heuristics)
    
    Supports sorting results by price or seller rating.
    
    Example:
        >>> catalog = ProductCatalog(products)
        >>> retrieval = CandidateRetrieval(catalog)
        >>> filters = SearchFilters(price_min=10, price_max=40, category="Computers", sort_by="price_asc")
        >>> candidates = retrieval.search(filters)
        >>> print(candidates)  # ["B08GFTPQ5B", "B07BJ7ZZL7"]  (sorted by price)
    """
    
    STRATEGIES = ("linear", "bfs", "dfs", "priority")

    def __init__(self, catalog: ProductCatalog):
        """
        Initialize the retrieval system.
        
        Args:
            catalog: The product catalog to search.
        """
        self.catalog = catalog
    
    def matches_filters(self, product: Product, filters: SearchFilters) -> bool:
        """
        Check if a product satisfies all filter constraints.
        
        Args:
            product: The product to check.
            filters: The filter constraints.
        
        Returns:
            True if the product matches all filters, False otherwise.
        """
        # Price range check
        if filters.price_min is not None and product.price < filters.price_min:
            return False
        if filters.price_max is not None and product.price > filters.price_max:
            return False
        
        # Category check (case-insensitive)
        if filters.category is not None:
            if product.category.lower() != filters.category.lower():
                return False
        
        # Seller rating check
        if filters.min_seller_rating is not None:
            if product.seller_rating < filters.min_seller_rating:
                return False
        
        # Store check (case-insensitive)
        if filters.store is not None:
            if product.store.lower() != filters.store.lower():
                return False
        
        return True
    
    def _sort_candidates(self, candidate_ids: List[str], sort_by: str) -> List[str]:
        """
        Sort candidate IDs by the given sort criterion.
        
        Args:
            candidate_ids: List of product IDs to sort.
            sort_by: Sort key — "price_asc", "price_desc",
                     "rating_desc", or "rating_asc".
        
        Returns:
            Sorted list of product IDs.
        """
        if sort_by == "price_asc":
            return sorted(
                candidate_ids,
                key=lambda pid: self.catalog[pid].price,
            )
        elif sort_by == "price_desc":
            return sorted(
                candidate_ids,
                key=lambda pid: self.catalog[pid].price,
                reverse=True,
            )
        elif sort_by == "rating_desc":
            return sorted(
                candidate_ids,
                key=lambda pid: self.catalog[pid].seller_rating,
                reverse=True,
            )
        elif sort_by == "rating_asc":
            return sorted(
                candidate_ids,
                key=lambda pid: self.catalog[pid].seller_rating,
            )
        return candidate_ids
    
    def search(
        self,
        filters: SearchFilters,
        strategy: str = "linear",
        max_results: Optional[int] = None
    ) -> SearchResult:
        """
        Search for candidate products matching filters.
        
        Args:
            filters: The search filters (hard constraints + optional sort).
            strategy: Search strategy - "linear", "bfs", "dfs", or "priority".
            max_results: Maximum number of results to return. None for all.
        
        Returns:
            SearchResult containing matching product IDs and metadata.
        
        Raises:
            UnknownSearchStrategyError: If strategy is not recognized.
        """
        start = time.perf_counter()

        if strategy == "linear":
            candidates = self._linear_search(filters, max_results=None)
        elif strategy == "bfs":
            candidates = self._bfs_search(filters, max_results=None)
        elif strategy == "dfs":
            candidates = self._dfs_search(filters, max_results=None)
        elif strategy == "priority":
            candidates = self._priority_search(filters, max_results=None)
        else:
            raise UnknownSearchStrategyError(
                f"Unknown search strategy: {strategy}. "
                f"Choose from {self.STRATEGIES}"
            )
        
        total_scanned = len(self.catalog)

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
            total_scanned,
            elapsed_ms,
        )
        return SearchResult(
            candidate_ids=candidates,
            strategy=strategy,
            total_scanned=total_scanned,
            elapsed_ms=elapsed_ms,
        )
    
    def _linear_search(
        self,
        filters: SearchFilters,
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        Linear scan through all products (baseline).
        
        Time: O(n) where n = catalog size
        Space: O(k) where k = number of matches
        """
        candidates = []
        for product in self.catalog:
            if self.matches_filters(product, filters):
                candidates.append(product.id)
                if max_results and len(candidates) >= max_results:
                    break
        return candidates
    
    def _bfs_search(
        self,
        filters: SearchFilters,
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        BFS-style search through products.
        
        Uses a queue to process products level by level.
        Useful when catalog has hierarchical structure (e.g., by category).
        
        Time: O(n)
        Space: O(n) for queue
        """
        candidates = []
        visited: Set[str] = set()
        queue = deque(self.catalog.product_ids)
        
        while queue:
            product_id = queue.popleft()
            
            if product_id in visited:
                continue
            visited.add(product_id)
            
            product = self.catalog.get(product_id)
            if product and self.matches_filters(product, filters):
                candidates.append(product_id)
                if max_results and len(candidates) >= max_results:
                    break
        
        return candidates
    
    def _dfs_search(
        self,
        filters: SearchFilters,
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        DFS-style search through products.
        
        Uses a stack for depth-first traversal.
        Can find results faster when matching products cluster together.
        
        Time: O(n)
        Space: O(n) for stack
        """
        candidates = []
        visited: Set[str] = set()
        stack = list(self.catalog.product_ids)
        
        while stack:
            product_id = stack.pop()
            
            if product_id in visited:
                continue
            visited.add(product_id)
            
            product = self.catalog.get(product_id)
            if product and self.matches_filters(product, filters):
                candidates.append(product_id)
                if max_results and len(candidates) >= max_results:
                    break
        
        return candidates
    
    def _priority_search(
        self,
        filters: SearchFilters,
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        Priority-based informed search (A*-style).
        
        Uses a heuristic to prioritize products more likely to match.
        The heuristic estimates how "close" a product is to satisfying filters.
        
        Time: O(n log n) due to heap operations
        Space: O(n) for priority queue
        """
        candidates = []
        visited: Set[str] = set()
        
        # Priority queue: (priority, product_id)
        # Lower priority = more likely to match
        pq = []
        
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
            
            product = self.catalog.get(product_id)
            if product and self.matches_filters(product, filters):
                candidates.append(product_id)
                if max_results and len(candidates) >= max_results:
                    break
        
        return candidates
    
    def _compute_priority(self, product: Product, filters: SearchFilters) -> float:
        """
        Compute priority score for a product (lower = better).
        
        This is the heuristic function for informed search.
        It estimates how likely a product is to match the filters.
        
        Args:
            product: The product to evaluate.
            filters: The search filters.
        
        Returns:
            Priority score (0 = perfect match candidate, higher = worse).
        """
        priority = 0.0
        
        # Penalize if price is outside range
        if filters.price_min is not None and product.price < filters.price_min:
            priority += (filters.price_min - product.price)
        if filters.price_max is not None and product.price > filters.price_max:
            priority += (product.price - filters.price_max)
        
        # Penalize if category doesn't match
        if filters.category is not None:
            if product.category.lower() != filters.category.lower():
                priority += 100  # Large penalty for wrong category
        
        # Penalize if rating is below minimum
        if filters.min_seller_rating is not None:
            if product.seller_rating < filters.min_seller_rating:
                priority += (filters.min_seller_rating - product.seller_rating) * 10
        
        # Penalize if store doesn't match
        if filters.store is not None:
            if product.store.lower() != filters.store.lower():
                priority += 75  # Significant penalty for wrong store
        
        return priority
    
    def get_candidates_with_products(
        self,
        filters: SearchFilters,
        strategy: str = "linear"
    ) -> List[Product]:
        """
        Get full Product objects for candidates (convenience method).
        
        Args:
            filters: The search filters.
            strategy: Search strategy to use.
        
        Returns:
            List of Product objects that match the filters.
        """
        result = self.search(filters, strategy)
        return [self.catalog[pid] for pid in result.candidate_ids]
