"""Unit tests for src/module3/embeddings — word embeddings and similarity."""

import numpy as np
import pytest

from src.module3.embeddings import ProductEmbedder, EMBEDDING_DIM, _cosine_similarity


class TestCosineSimilarity:
    """Tests for the standalone _cosine_similarity helper."""

    def test_identical_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert _cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector(self):
        assert _cosine_similarity(np.zeros(3), np.array([1.0, 2.0, 3.0])) == 0.0

    def test_both_zero(self):
        assert _cosine_similarity(np.zeros(3), np.zeros(3)) == 0.0


class TestProductEmbedder:
    """Tests for the ProductEmbedder class."""

    def test_embed_query_shape(self, product_embedder):
        vec = product_embedder.embed_query("bluetooth headphones")
        assert vec.shape == (EMBEDDING_DIM,)

    def test_embed_text_shape(self, product_embedder):
        vec = product_embedder.embed_text("wireless speaker portable")
        assert vec.shape == (EMBEDDING_DIM,)

    def test_embed_query_dtype(self, product_embedder):
        vec = product_embedder.embed_query("laptop stand")
        assert vec.dtype == np.float32

    def test_empty_query_returns_zero(self, product_embedder):
        vec = product_embedder.embed_query("")
        assert np.allclose(vec, 0.0)

    def test_oov_returns_zero(self, product_embedder):
        vec = product_embedder.embed_query("xyzzyfoobarbaz quxwaldo")
        assert np.allclose(vec, 0.0)

    def test_vocabulary_size_positive(self, product_embedder):
        assert product_embedder.vocabulary_size > 0

    def test_using_word2vec_by_default(self, product_embedder):
        assert not product_embedder.using_glove

    def test_similarity_in_range(self, product_embedder):
        sim = product_embedder.similarity(
            "bluetooth headphones", "wireless speaker",
        )
        assert -1.0 <= sim <= 1.0

    def test_identical_text_high_similarity(self, product_embedder):
        text = "wireless bluetooth headphones"
        sim = product_embedder.similarity(text, text)
        assert sim > 0.99

    def test_similar_higher_than_dissimilar(self, product_embedder):
        sim_close = product_embedder.similarity(
            "bluetooth wireless noise",
            "bluetooth wireless cancelling noise",
        )
        sim_far = product_embedder.similarity(
            "bluetooth wireless noise",
            "gaming rgb adjustable",
        )
        assert sim_close > sim_far

    def test_rank_by_similarity_order(self, product_embedder):
        ranked = product_embedder.rank_by_similarity(
            "bluetooth speaker",
            {
                "speaker": "portable bluetooth speaker waterproof",
                "shoes": "running shoes lightweight breathable",
                "keyboard": "mechanical keyboard rgb gaming",
            },
        )
        assert ranked[0][0] == "speaker"

    def test_rank_by_similarity_returns_all(self, product_embedder):
        texts = {"a": "headphones", "b": "speaker", "c": "cable"}
        ranked = product_embedder.rank_by_similarity("headphones", texts)
        assert len(ranked) == 3

    def test_rank_by_similarity_descending(self, product_embedder):
        texts = {"a": "headphones", "b": "speaker", "c": "cable"}
        ranked = product_embedder.rank_by_similarity("headphones", texts)
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)


class TestProductEmbedderEdgeCases:
    """Edge case and robustness tests."""

    def test_single_word_embedding(self, product_embedder):
        vec = product_embedder.embed_query("bluetooth")
        assert vec.shape == (EMBEDDING_DIM,)

    def test_long_text_embedding(self, product_embedder):
        long_text = " ".join(["bluetooth headphones wireless"] * 50)
        vec = product_embedder.embed_text(long_text)
        assert vec.shape == (EMBEDDING_DIM,)

    def test_similarity_with_empty_text(self, product_embedder):
        assert product_embedder.similarity("bluetooth", "") == 0.0

    def test_rank_empty_texts(self, product_embedder):
        assert product_embedder.rank_by_similarity("bluetooth", {}) == []
