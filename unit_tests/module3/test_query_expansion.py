"""Unit tests for the query expansion module."""

import pytest

from src.module3.query_expansion import QueryExpander


class TestSimilarTerms:
    def test_known_token_returns_neighbours(self, query_expander):
        results = query_expander.similar_terms("bluetooth", top_n=3, min_sim=0.0)
        assert isinstance(results, list)
        assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in results)

    def test_oov_token_returns_empty(self, query_expander):
        results = query_expander.similar_terms("xylophoneblaster", top_n=3)
        assert results == []

    def test_similarity_scores_are_floats(self, query_expander):
        results = query_expander.similar_terms("wireless", top_n=3, min_sim=0.0)
        for word, sim in results:
            assert isinstance(word, str)
            assert isinstance(sim, float)

    def test_results_respect_top_n(self, query_expander):
        results = query_expander.similar_terms("keyboard", top_n=2, min_sim=0.0)
        assert len(results) <= 2

    def test_min_sim_filters_low_scores(self, query_expander):
        results = query_expander.similar_terms("bluetooth", top_n=10, min_sim=0.99)
        for _, sim in results:
            assert sim >= 0.99


class TestExpand:
    def test_returns_original_tokens_and_expansions(self, query_expander):
        tokens, expansions = query_expander.expand("bluetooth headphones")
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert isinstance(expansions, list)

    def test_expansions_exclude_original_tokens(self, query_expander):
        tokens, expansions = query_expander.expand("wireless mouse")
        original_set = set(tokens)
        for word, _ in expansions:
            assert word not in original_set

    def test_expansions_sorted_descending(self, query_expander):
        _, expansions = query_expander.expand("bluetooth speaker", min_sim=0.0)
        if len(expansions) > 1:
            sims = [s for _, s in expansions]
            assert sims == sorted(sims, reverse=True)

    def test_empty_query_returns_empty(self, query_expander):
        tokens, expansions = query_expander.expand("")
        assert tokens == []
        assert expansions == []

    def test_whitespace_query_returns_empty(self, query_expander):
        tokens, expansions = query_expander.expand("   ")
        assert tokens == []
        assert expansions == []

    def test_expansion_words_are_strings(self, query_expander):
        _, expansions = query_expander.expand("laptop portable", min_sim=0.0)
        for word, sim in expansions:
            assert isinstance(word, str)
            assert isinstance(sim, float)

    def test_no_duplicates_in_expansions(self, query_expander):
        _, expansions = query_expander.expand("bluetooth wireless headphones", min_sim=0.0)
        words = [w for w, _ in expansions]
        assert len(words) == len(set(words))

    def test_high_min_sim_may_return_nothing(self, query_expander):
        _, expansions = query_expander.expand("keyboard", min_sim=0.9999)
        assert isinstance(expansions, list)


class TestQueryResultIntegration:
    def test_understand_includes_expanded_terms(self, query_understanding):
        result = query_understanding.understand("bluetooth headphones")
        assert hasattr(result, "expanded_terms")
        assert isinstance(result.expanded_terms, list)

    def test_expanded_terms_are_tuples(self, query_understanding):
        result = query_understanding.understand("wireless speaker")
        for item in result.expanded_terms:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_empty_query_no_expansions(self, query_understanding):
        result = query_understanding.understand("")
        assert result.expanded_terms == []
