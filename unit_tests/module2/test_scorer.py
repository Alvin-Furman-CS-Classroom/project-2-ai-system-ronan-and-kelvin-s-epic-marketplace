"""
Unit tests for the heuristic scoring functions (src/module2/scorer.py).

Tests cover:
- ScoringConfig validation and normalisation
- Individual feature-score components
- End-to-end compute_score with known inputs
- Edge cases (zero prices, missing descriptions, no reviews)
"""

import math
import pytest

from src.module1.catalog import Product
from src.module2.scorer import (
    ScoringConfig,
    compute_feature_ranges,
    compute_score,
    normalize,
    _price_score,
    _rating_score,
    _popularity_score,
    _category_match_score,
    _richness_score,
)
from src.module2.exceptions import InvalidWeightsError


# ===================================================================
# ScoringConfig
# ===================================================================

class TestScoringConfig:
    """Tests for ScoringConfig dataclass."""

    def test_default_weights(self):
        """Default weights sum to 1."""
        cfg = ScoringConfig()
        assert abs(sum(cfg._as_list()) - 1.0) < 1e-9

    def test_custom_weights(self):
        """Custom weights are stored correctly."""
        cfg = ScoringConfig(price=1.0, rating=2.0, popularity=3.0,
                            category_match=4.0, richness=0.0)
        assert cfg.price == 1.0
        assert cfg.rating == 2.0

    def test_negative_weight_raises(self):
        """Negative weights raise InvalidWeightsError."""
        with pytest.raises(InvalidWeightsError):
            ScoringConfig(price=-0.1)

    def test_all_zero_weights_raises(self):
        """All-zero weights raise InvalidWeightsError."""
        with pytest.raises(InvalidWeightsError):
            ScoringConfig(price=0, rating=0, popularity=0,
                          category_match=0, richness=0)

    def test_normalized_sums_to_one(self):
        """Normalised weights always sum to 1."""
        cfg = ScoringConfig(price=3, rating=1, popularity=1,
                            category_match=0, richness=0)
        normed = cfg.normalized()
        assert abs(sum(normed) - 1.0) < 1e-9

    def test_normalized_preserves_ratios(self):
        """Normalisation preserves relative ratios."""
        cfg = ScoringConfig(price=2, rating=1, popularity=0,
                            category_match=0, richness=0)
        normed = cfg.normalized()
        assert abs(normed[0] / normed[1] - 2.0) < 1e-9

    def test_single_nonzero_weight(self):
        """A single non-zero weight normalises to [0,...,1,...,0]."""
        cfg = ScoringConfig(price=0, rating=5.0, popularity=0,
                            category_match=0, richness=0)
        normed = cfg.normalized()
        assert normed[1] == pytest.approx(1.0)
        assert normed[0] == pytest.approx(0.0)


# ===================================================================
# normalize()
# ===================================================================

class TestNormalize:
    """Tests for the min-max normalize function."""

    def test_middle_value(self):
        """Value in the middle of range maps to ~0.5."""
        assert normalize(50, 0, 100) == pytest.approx(0.5)

    def test_at_minimum(self):
        """Minimum value maps to 0."""
        assert normalize(0, 0, 100) == pytest.approx(0.0)

    def test_at_maximum(self):
        """Maximum value maps to 1."""
        assert normalize(100, 0, 100) == pytest.approx(1.0)

    def test_equal_range(self):
        """Equal lo/hi returns 0.5."""
        assert normalize(42, 42, 42) == pytest.approx(0.5)

    def test_clamped_below(self):
        """Value below range is clamped to 0."""
        assert normalize(-10, 0, 100) == pytest.approx(0.0)

    def test_clamped_above(self):
        """Value above range is clamped to 1."""
        assert normalize(200, 0, 100) == pytest.approx(1.0)


# ===================================================================
# Individual feature scores
# ===================================================================

class TestPriceScore:
    """Tests for _price_score (inverted — lower is better)."""

    def test_cheapest_scores_highest(self):
        """The cheapest product gets score 1.0."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S")
        assert _price_score(p, (10, 100)) == pytest.approx(1.0)

    def test_most_expensive_scores_lowest(self):
        """The most expensive product gets score 0.0."""
        p = Product(id="x", title="T", price=100, category="c",
                    seller_rating=3, store="S")
        assert _price_score(p, (10, 100)) == pytest.approx(0.0)

    def test_mid_price(self):
        """Mid price gets ~0.5."""
        p = Product(id="x", title="T", price=55, category="c",
                    seller_rating=3, store="S")
        assert _price_score(p, (10, 100)) == pytest.approx(0.5)

    def test_same_price_range(self):
        """All products same price → 0.5."""
        p = Product(id="x", title="T", price=42, category="c",
                    seller_rating=3, store="S")
        assert _price_score(p, (42, 42)) == pytest.approx(0.5)


class TestRatingScore:
    """Tests for _rating_score."""

    def test_perfect_rating(self):
        """5.0 rating → 1.0 score."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=5.0, store="S")
        assert _rating_score(p) == pytest.approx(1.0)

    def test_zero_rating(self):
        """0.0 rating → 0.0 score."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=0.0, store="S")
        assert _rating_score(p) == pytest.approx(0.0)

    def test_mid_rating(self):
        """2.5 rating → 0.5 score."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=2.5, store="S")
        assert _rating_score(p) == pytest.approx(0.5)


class TestPopularityScore:
    """Tests for _popularity_score (log-scaled review count)."""

    def test_zero_reviews(self):
        """Product with 0 reviews → lowest popularity."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S", rating_number=0)
        lo = math.log1p(0)
        hi = math.log1p(10000)
        assert _popularity_score(p, (lo, hi)) == pytest.approx(0.0)

    def test_max_reviews(self):
        """Product with max reviews → score 1.0."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S", rating_number=10000)
        lo = math.log1p(0)
        hi = math.log1p(10000)
        assert _popularity_score(p, (lo, hi)) == pytest.approx(1.0)

    def test_none_rating_number(self):
        """rating_number=None treated as 0."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S", rating_number=None)
        lo = math.log1p(0)
        hi = math.log1p(1000)
        assert _popularity_score(p, (lo, hi)) == pytest.approx(0.0)


class TestCategoryMatchScore:
    """Tests for _category_match_score."""

    def test_exact_match(self):
        """Matching category → 1.0."""
        p = Product(id="x", title="T", price=10, category="electronics",
                    seller_rating=3, store="S")
        assert _category_match_score(p, "electronics") == pytest.approx(1.0)

    def test_case_insensitive_match(self):
        """Category match is case-insensitive."""
        p = Product(id="x", title="T", price=10, category="Electronics",
                    seller_rating=3, store="S")
        assert _category_match_score(p, "electronics") == pytest.approx(1.0)

    def test_no_match(self):
        """Non-matching category → 0.0."""
        p = Product(id="x", title="T", price=10, category="home",
                    seller_rating=3, store="S")
        assert _category_match_score(p, "electronics") == pytest.approx(0.0)

    def test_no_target(self):
        """No target category → 0.5 (neutral)."""
        p = Product(id="x", title="T", price=10, category="home",
                    seller_rating=3, store="S")
        assert _category_match_score(p, None) == pytest.approx(0.5)


class TestRichnessScore:
    """Tests for _richness_score (description + features)."""

    def test_no_description_no_features(self):
        """Empty listing → 0.0."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S", description=None, features=None)
        assert _richness_score(p) == pytest.approx(0.0)

    def test_long_description(self):
        """500+ char description → description component maxes out."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S",
                    description="x" * 600, features=None)
        # 0.6 * 1.0 + 0.4 * 0.0 = 0.6
        assert _richness_score(p) == pytest.approx(0.6)

    def test_many_features(self):
        """10+ features → features component maxes out."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S",
                    description=None,
                    features=[f"f{i}" for i in range(15)])
        # 0.6 * 0.0 + 0.4 * 1.0 = 0.4
        assert _richness_score(p) == pytest.approx(0.4)

    def test_rich_listing(self):
        """Full description + many features → ~1.0."""
        p = Product(id="x", title="T", price=10, category="c",
                    seller_rating=3, store="S",
                    description="x" * 500,
                    features=[f"f{i}" for i in range(10)])
        assert _richness_score(p) == pytest.approx(1.0)


# ===================================================================
# compute_feature_ranges
# ===================================================================

class TestComputeFeatureRanges:
    """Tests for compute_feature_ranges."""

    def test_empty_products(self):
        """Empty list → zero ranges."""
        ranges = compute_feature_ranges([])
        assert ranges["price"] == (0.0, 0.0)
        assert ranges["popularity"] == (0.0, 0.0)

    def test_single_product(self):
        """Single product → min == max."""
        p = Product(id="x", title="T", price=42, category="c",
                    seller_rating=3, store="S", rating_number=100)
        ranges = compute_feature_ranges([p])
        assert ranges["price"][0] == ranges["price"][1] == 42.0

    def test_range_computation(self, ranking_products):
        """Ranges span the full set of products."""
        ranges = compute_feature_ranges(ranking_products)
        prices = [p.price for p in ranking_products]
        assert ranges["price"] == (min(prices), max(prices))


# ===================================================================
# compute_score (end-to-end)
# ===================================================================

class TestComputeScore:
    """Tests for the full scoring pipeline."""

    def test_score_in_unit_range(self, ranking_products):
        """All scores are in [0, 1]."""
        cfg = ScoringConfig()
        ranges = compute_feature_ranges(ranking_products)
        for p in ranking_products:
            s = compute_score(p, cfg, ranges)
            assert 0.0 <= s <= 1.0, f"{p.id} scored {s}"

    def test_high_rated_cheap_scores_well(self):
        """A cheap, highly-rated product with reviews should score high."""
        good = Product(id="g", title="G", price=10, category="electronics",
                       seller_rating=5.0, store="S", rating_number=10000,
                       description="x" * 500, features=["a"] * 10)
        bad = Product(id="b", title="B", price=100, category="electronics",
                      seller_rating=1.0, store="S", rating_number=0,
                      description=None, features=None)
        cfg = ScoringConfig()
        ranges = compute_feature_ranges([good, bad])
        assert compute_score(good, cfg, ranges) > compute_score(bad, cfg, ranges)

    def test_category_match_boosts_score(self):
        """Matching category should increase score vs. non-matching."""
        p = Product(id="x", title="T", price=30, category="electronics",
                    seller_rating=4.0, store="S", rating_number=1000)
        cfg = ScoringConfig()
        ranges = compute_feature_ranges([p])
        with_match = compute_score(p, cfg, ranges, target_category="electronics")
        without_match = compute_score(p, cfg, ranges, target_category="other")
        assert with_match > without_match

    def test_only_price_weight(self):
        """When only price weight is non-zero, cheapest always wins."""
        cheap = Product(id="c", title="C", price=5, category="c",
                        seller_rating=1.0, store="S")
        expensive = Product(id="e", title="E", price=100, category="c",
                            seller_rating=5.0, store="S")
        cfg = ScoringConfig(price=1, rating=0, popularity=0,
                            category_match=0, richness=0)
        ranges = compute_feature_ranges([cheap, expensive])
        assert compute_score(cheap, cfg, ranges) > compute_score(expensive, cfg, ranges)

    def test_only_rating_weight(self):
        """When only rating weight is non-zero, highest rating wins."""
        good = Product(id="g", title="G", price=100, category="c",
                       seller_rating=5.0, store="S")
        bad = Product(id="b", title="B", price=5, category="c",
                      seller_rating=1.0, store="S")
        cfg = ScoringConfig(price=0, rating=1, popularity=0,
                            category_match=0, richness=0)
        ranges = compute_feature_ranges([good, bad])
        assert compute_score(good, cfg, ranges) > compute_score(bad, cfg, ranges)

    def test_deterministic(self, ranking_products):
        """Same inputs always produce same scores."""
        cfg = ScoringConfig()
        ranges = compute_feature_ranges(ranking_products)
        scores_a = [compute_score(p, cfg, ranges) for p in ranking_products]
        scores_b = [compute_score(p, cfg, ranges) for p in ranking_products]
        assert scores_a == scores_b
