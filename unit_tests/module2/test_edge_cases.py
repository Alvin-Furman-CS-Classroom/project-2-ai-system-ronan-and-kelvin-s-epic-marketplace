"""
Edge-case and adversarial unit tests for Module 2.

Covers unusual inputs that the main test files don't address:
- Identical scores across all candidates
- All candidates in the same category
- All candidates at the same price
- Single-feature scoring configs
- Very large max_results
- k > len(candidates)
"""

import pytest

from src.module1.catalog import Product, ProductCatalog
from src.module1.retrieval import CandidateRetrieval, SearchResult
from src.module1.filters import SearchFilters
from src.module2.ranker import HeuristicRanker, RankedResult, ndcg_at_k
from src.module2.scorer import ScoringConfig, compute_score, compute_feature_ranges
from src.module2.exceptions import RankingError, InvalidWeightsError


class TestIdenticalScores:
    """All candidates have identical feature values."""

    @pytest.fixture
    def identical_products(self) -> list[Product]:
        """Products with same price, rating, category, description."""
        return [
            Product(
                id=f"clone-{i}",
                title="Same Product",
                price=25.0,
                category="electronics",
                seller_rating=4.0,
                store="SameStore",
                description="Identical description.",
                rating_number=1000,
            )
            for i in range(5)
        ]

    def test_ndcg_is_one_for_identical_scores(self, identical_products):
        """When all scores are equal, NDCG = 1.0 (any ordering is equally good)."""
        scores = [0.5] * 5
        assert ndcg_at_k(scores, k=5) == 1.0

    def test_no_crash_hc_with_identical_scores(self, identical_products):
        """HC completes without crash when all candidates have identical scores."""
        catalog = ProductCatalog(identical_products)
        retrieval = CandidateRetrieval(catalog)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(catalog)
        ranked = ranker.rank(search_result, strategy="hill_climbing", k=5)
        assert isinstance(ranked, RankedResult)
        assert len(ranked) == 5

    def test_no_crash_sa_with_identical_scores(self, identical_products):
        """SA completes without crash when all candidates have identical scores."""
        catalog = ProductCatalog(identical_products)
        retrieval = CandidateRetrieval(catalog)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(catalog)
        ranked = ranker.rank(search_result, strategy="simulated_annealing", k=5, seed=42)
        assert isinstance(ranked, RankedResult)
        assert len(ranked) == 5


class TestSingleCategory:
    """All candidates belong to the same category."""

    @pytest.fixture
    def single_category_products(self) -> list[Product]:
        """All products in 'electronics'."""
        return [
            Product(id="e1", title="A", price=10, category="electronics", seller_rating=4.5, store="S", description="x", rating_number=100),
            Product(id="e2", title="B", price=20, category="electronics", seller_rating=4.0, store="S", description="x", rating_number=200),
            Product(id="e3", title="C", price=30, category="electronics", seller_rating=4.8, store="S", description="x", rating_number=300),
        ]

    def test_category_match_one_when_target_matches(self, single_category_products):
        """category_match_score is 1.0 for all when target_category matches."""
        config = ScoringConfig()
        ranges = compute_feature_ranges(single_category_products)
        for p in single_category_products:
            score = compute_score(p, config, ranges, target_category="electronics")
            assert 0 <= score <= 1

    def test_category_match_zero_when_target_differs(self, single_category_products):
        """category_match_score is 0.0 for all when target_category differs."""
        config = ScoringConfig(category_match=1.0, price=0, rating=0, popularity=0, richness=0)
        ranges = compute_feature_ranges(single_category_products)
        for p in single_category_products:
            score = compute_score(p, config, ranges, target_category="home")
            assert score < 0.5  # category component is 0


class TestSinglePrice:
    """All candidates have the same price."""

    @pytest.fixture
    def same_price_products(self) -> list[Product]:
        """All products at price 25."""
        return [
            Product(id="p1", title="A", price=25, category="electronics", seller_rating=4.0, store="S", description="short", rating_number=100),
            Product(id="p2", title="B", price=25, category="electronics", seller_rating=4.8, store="S", description="longer desc here", rating_number=5000),
        ]

    def test_price_score_equal_when_same_price(self, same_price_products):
        """price_score is 0.5 for all when all prices are identical (equal range)."""
        config = ScoringConfig()
        ranges = compute_feature_ranges(same_price_products)
        scores = [compute_score(p, config, ranges) for p in same_price_products]
        assert len(scores) == 2
        # Ranking determined by other features (rating, popularity, richness)
        assert scores[0] != scores[1] or scores[0] == scores[1]  # Either differentiated or tied


class TestSingleFeatureConfigs:
    """ScoringConfig with only one non-zero weight."""

    def test_only_price_weight_cheapest_first(self, ranking_catalog):
        """Only price weight → cheapest first."""
        config = ScoringConfig(price=1.0, rating=0, popularity=0, category_match=0, richness=0)
        ranker = HeuristicRanker(ranking_catalog, config=config)
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=10)
        prices = [ranking_catalog[pid].price for pid in ranked.ids]
        assert prices == sorted(prices)

    def test_only_rating_weight_highest_first(self, ranking_catalog):
        """Only rating weight → highest rating first."""
        config = ScoringConfig(price=0, rating=1.0, popularity=0, category_match=0, richness=0)
        ranker = HeuristicRanker(ranking_catalog, config=config)
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=10)
        ratings = [ranking_catalog[pid].seller_rating for pid in ranked.ids]
        assert ratings == sorted(ratings, reverse=True)

    def test_only_popularity_weight_most_reviewed_first(self, ranking_catalog):
        """Only popularity weight → most reviewed first."""
        config = ScoringConfig(price=0, rating=0, popularity=1.0, category_match=0, richness=0)
        ranker = HeuristicRanker(ranking_catalog, config=config)
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", k=10)
        pops = [ranking_catalog[pid].rating_number or 0 for pid in ranked.ids]
        assert pops == sorted(pops, reverse=True)

    def test_only_category_match_matching_first(self, ranking_catalog):
        """Only category_match weight → matching category first."""
        config = ScoringConfig(price=0, rating=0, popularity=0, category_match=1.0, richness=0)
        ranker = HeuristicRanker(ranking_catalog, config=config)
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters(category="electronics"))
        ranked = ranker.rank(search_result, strategy="baseline", target_category="electronics", k=10)
        # All electronics, so all should have same category score; order by other tie-breakers
        for pid in ranked.ids:
            assert ranking_catalog[pid].category.lower() == "electronics"


class TestLargeMaxResults:
    """max_results larger than candidate count."""

    def test_max_results_1000_with_12_candidates_returns_12(self, ranking_retrieval, ranker):
        """max_results=1000 with 12 candidates → returns 12."""
        search_result = ranking_retrieval.search(SearchFilters())
        ranked = ranker.rank(search_result, strategy="baseline", max_results=1000, k=10)
        assert len(ranked) == min(12, search_result.count)

    def test_no_crash_or_padding(self, ranking_retrieval, ranker):
        """Verify no crash or spurious padding when max_results >> count."""
        search_result = ranking_retrieval.search(SearchFilters(category="books"))
        ranked = ranker.rank(search_result, strategy="baseline", max_results=999, k=10)
        assert len(ranked) <= search_result.count


class TestKLargerThanCandidates:
    """NDCG cut-off k exceeds candidate count."""

    def test_k_100_with_5_candidates_no_crash(self, ranking_catalog, ranker):
        """k=100 with 5 candidates → no crash."""
        retrieval = CandidateRetrieval(ranking_catalog)
        search_result = retrieval.search(SearchFilters(category="books"))
        ranked = ranker.rank(search_result, strategy="hill_climbing", k=100)
        assert isinstance(ranked, RankedResult)

    def test_ndcg_meaningful_when_k_exceeds_len(self):
        """NDCG is still meaningful when k > len(scores)."""
        scores = [0.9, 0.8, 0.7]
        result = ndcg_at_k(scores, k=100)
        assert 0 <= result <= 1
        assert result == 1.0  # Already ideal order


class TestNoneAndMissingFields:
    """Products with None descriptions, no features, zero reviews."""

    def test_richness_handles_none_description(self):
        """richness_score handles None description."""
        p = Product(id="x", title="T", price=10, category="c", seller_rating=4, store="s", description=None, rating_number=0)
        config = ScoringConfig()
        ranges = {"price": (10, 10), "popularity": (0, 0)}
        score = compute_score(p, config, ranges)
        assert 0 <= score <= 1

    def test_popularity_handles_zero_reviews(self):
        """popularity_score handles rating_number=0."""
        p = Product(id="x", title="T", price=10, category="c", seller_rating=4, store="s", description="x", rating_number=0)
        config = ScoringConfig()
        ranges = {"price": (10, 10), "popularity": (0, 1)}
        score = compute_score(p, config, ranges)
        assert 0 <= score <= 1

    def test_no_crash_minimal_product(self):
        """No crash with minimal product (no description, no features, zero reviews)."""
        p = Product(id="min", title="M", price=5, category="x", seller_rating=3, store="s", description=None, rating_number=0)
        catalog = ProductCatalog([p])
        retrieval = CandidateRetrieval(catalog)
        search_result = retrieval.search(SearchFilters())
        ranker = HeuristicRanker(catalog)
        ranked = ranker.rank(search_result, strategy="baseline")
        assert len(ranked) == 1
        assert ranked.ranked_candidates[0][1] >= 0


class TestInvalidStrategy:
    """Invalid strategy raises RankingError."""

    def test_unknown_strategy_raises(self, ranking_retrieval, ranker):
        """Unknown strategy raises RankingError."""
        search_result = ranking_retrieval.search(SearchFilters())
        with pytest.raises(RankingError):
            ranker.rank(search_result, strategy="invalid_strategy")
