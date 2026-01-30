"""
Candidate retrieval using search algorithms.

Implements uninformed (BFS/DFS) and informed (A*-style priority) search
to find products matching hard constraints.
"""

from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Set, Callable
import heapq

from .filters import SearchFilters
from .catalog import ProductCatalog, Product


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
    
    Example:
        >>> catalog = ProductCatalog(products)
        >>> retrieval = CandidateRetrieval(catalog)
        >>> filters = SearchFilters(price_min=10, price_max=40, category="home")
        >>> candidates = retrieval.search(filters)
        >>> print(candidates)  # ["p12", "p89", "p203"]
    """
    
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
        
        # Location check (case-insensitive)
        if filters.location is not None:
            if product.location.lower() != filters.location.lower():
                return False
        
        return True
    
    def search(
        self,
        filters: SearchFilters,
        strategy: str = "linear",
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        Search for candidate products matching filters.
        
        Args:
            filters: The search filters (hard constraints).
            strategy: Search strategy - "linear", "bfs", "dfs", or "priority".
            max_results: Maximum number of results to return. None for all.
        
        Returns:
            List of product IDs that match the filters.
        
        Raises:
            ValueError: If strategy is not recognized.
        """
        if strategy == "linear":
            return self._linear_search(filters, max_results)
        elif strategy == "bfs":
            return self._bfs_search(filters, max_results)
        elif strategy == "dfs":
            return self._dfs_search(filters, max_results)
        elif strategy == "priority":
            return self._priority_search(filters, max_results)
        else:
            raise ValueError(f"Unknown search strategy: {strategy}")
    
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
        
        # Penalize if location doesn't match
        if filters.location is not None:
            if product.location.lower() != filters.location.lower():
                priority += 50  # Moderate penalty for wrong location
        
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
        candidate_ids = self.search(filters, strategy)
        return [self.catalog[pid] for pid in candidate_ids]
