"""Unit tests for src/module3/keywords — TF-IDF keyword extraction."""

import pytest

from src.module3.keywords import KeywordExtractor


class TestKeywordExtractor:
    """Tests for the KeywordExtractor class."""

    def test_init_builds_vocabulary(self, keyword_extractor):
        assert keyword_extractor.vocabulary_size > 0

    def test_extract_returns_tuples(self, keyword_extractor):
        results = keyword_extractor.extract("bluetooth headphones")
        assert isinstance(results, list)
        assert all(isinstance(kw, tuple) and len(kw) == 2 for kw in results)

    def test_extract_scores_descending(self, keyword_extractor):
        results = keyword_extractor.extract("wireless bluetooth speaker")
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_extract_top_k_limits_results(self, keyword_extractor):
        results = keyword_extractor.extract(
            "wireless bluetooth headphones speaker cable", top_k=2,
        )
        assert len(results) <= 2

    def test_extract_relevant_keywords(self, keyword_extractor):
        results = keyword_extractor.extract("bluetooth headphones")
        keywords = [kw for kw, _ in results]
        assert "bluetooth" in keywords or "headphones" in keywords

    def test_extract_empty_query(self, keyword_extractor):
        assert keyword_extractor.extract("") == []

    def test_extract_stopwords_only(self, keyword_extractor):
        assert keyword_extractor.extract("the a an") == []

    def test_extract_unknown_word(self, keyword_extractor):
        results = keyword_extractor.extract("xyzzyfoobarbaz")
        if results:
            assert results[0][1] == 0.0

    def test_scores_are_non_negative(self, keyword_extractor):
        results = keyword_extractor.extract("wireless charging cable")
        assert all(score >= 0 for _, score in results)

    def test_duplicate_tokens_deduplicated(self, keyword_extractor):
        results = keyword_extractor.extract("bluetooth bluetooth bluetooth")
        keywords = [kw for kw, _ in results]
        assert len(keywords) == len(set(keywords))


class TestKeywordExtractorEdgeCases:
    """Edge case tests."""

    def test_small_corpus(self):
        kw = KeywordExtractor(["hello world"] * 5)
        results = kw.extract("hello")
        assert isinstance(results, list)

    def test_vocabulary_bounded(self, sample_corpus):
        extractor = KeywordExtractor(sample_corpus)
        assert extractor.vocabulary_size <= 20_000
