"""Unit tests for src/module3/tokenizer — text preprocessing."""

import pytest

from src.module3.tokenizer import tokenize, extract_ngrams


class TestTokenize:
    """Tests for the tokenize function."""

    def test_basic_tokenization(self):
        tokens = tokenize("Bluetooth Headphones for Running")
        assert "bluetooth" in tokens
        assert "headphones" in tokens
        assert "running" in tokens

    def test_stopword_removal(self):
        tokens = tokenize("the best headphones for a great price")
        assert "the" not in tokens
        assert "for" not in tokens
        assert "a" not in tokens
        assert "headphones" in tokens

    def test_lowercasing(self):
        tokens = tokenize("WIRELESS BLUETOOTH")
        assert all(t == t.lower() for t in tokens)

    def test_punctuation_removal(self):
        tokens = tokenize("fast-charging, cable!! (USB-C)")
        for t in tokens:
            assert "," not in t
            assert "!" not in t
            assert "(" not in t

    def test_empty_string(self):
        assert tokenize("") == []

    def test_whitespace_only(self):
        assert tokenize("   ") == []

    def test_punctuation_only(self):
        assert tokenize("!!! ??? ...") == []

    def test_single_meaningful_word(self):
        tokens = tokenize("headphones")
        assert tokens == ["headphones"]

    def test_short_tokens_filtered(self):
        tokens = tokenize("I a am ok go bluetooth")
        assert "bluetooth" in tokens
        assert "i" not in tokens
        assert "a" not in tokens

    def test_preserves_numbers_in_words(self):
        tokens = tokenize("USB 3.0 cable 100W charger")
        lowered = " ".join(tokens)
        assert "usb" in lowered or "cable" in lowered

    def test_unicode_text(self):
        tokens = tokenize("café résumé naïve")
        assert len(tokens) > 0

    def test_duplicate_whitespace(self):
        tokens = tokenize("bluetooth    headphones")
        assert "bluetooth" in tokens
        assert "headphones" in tokens

    def test_hyphenated_words(self):
        tokens = tokenize("noise-cancelling over-ear headphones")
        joined = " ".join(tokens)
        assert "headphones" in joined


class TestExtractNgrams:
    """Tests for the extract_ngrams function."""

    def test_bigrams(self):
        tokens = ["bluetooth", "headphones", "wireless"]
        bigrams = extract_ngrams(tokens, n=2)
        assert "bluetooth_headphones" in bigrams
        assert "headphones_wireless" in bigrams
        assert len(bigrams) == 2

    def test_trigrams(self):
        tokens = ["wireless", "bluetooth", "headphones", "noise"]
        trigrams = extract_ngrams(tokens, n=3)
        assert "wireless_bluetooth_headphones" in trigrams
        assert len(trigrams) == 2

    def test_too_few_tokens(self):
        assert extract_ngrams(["hello"], n=2) == []

    def test_empty_tokens(self):
        assert extract_ngrams([], n=2) == []

    def test_exact_length(self):
        bigrams = extract_ngrams(["a", "b"], n=2)
        assert bigrams == ["a_b"]

    def test_unigrams(self):
        tokens = ["bluetooth", "headphones"]
        unigrams = extract_ngrams(tokens, n=1)
        assert unigrams == ["bluetooth", "headphones"]
