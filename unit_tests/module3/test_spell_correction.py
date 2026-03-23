"""Unit tests for the spell correction module."""

import pytest

from src.module3.spell_correction import SpellCorrector, _levenshtein


# ── Levenshtein distance tests ──────────────────────────────────────

class TestLevenshtein:
    def test_identical_strings(self):
        assert _levenshtein("bluetooth", "bluetooth") == 0

    def test_single_insertion(self):
        assert _levenshtein("blueto", "bluetoo") == 1

    def test_single_deletion(self):
        assert _levenshtein("bluetooth", "bluetoth") == 1

    def test_single_substitution(self):
        assert _levenshtein("bluetooth", "bluetooph") == 1

    def test_empty_first(self):
        assert _levenshtein("", "abc") == 3

    def test_empty_second(self):
        assert _levenshtein("abc", "") == 3

    def test_both_empty(self):
        assert _levenshtein("", "") == 0

    def test_completely_different(self):
        assert _levenshtein("abc", "xyz") == 3

    def test_transposition_counts_as_two(self):
        assert _levenshtein("ab", "ba") == 2


# ── SpellCorrector tests ────────────────────────────────────────────

VOCAB = [
    "bluetooth", "headphones", "wireless", "laptop", "keyboard",
    "mouse", "speaker", "camera", "monitor", "charger",
    "gaming", "stand", "portable", "adapter", "cable",
]


@pytest.fixture
def corrector():
    return SpellCorrector(VOCAB)


class TestSpellCorrector:
    def test_vocabulary_size(self, corrector):
        assert corrector.vocabulary_size == len(VOCAB)

    def test_known_token_unchanged(self, corrector):
        token, was_fixed = corrector.correct_token("bluetooth")
        assert token == "bluetooth"
        assert was_fixed is False

    def test_misspelled_token_corrected(self, corrector):
        token, was_fixed = corrector.correct_token("bluetoth")
        assert token == "bluetooth"
        assert was_fixed is True

    def test_misspelled_headphones(self, corrector):
        token, was_fixed = corrector.correct_token("headphons")
        assert token == "headphones"
        assert was_fixed is True

    def test_too_far_from_vocab(self, corrector):
        """Completely unrelated word should not be "corrected"."""
        token, was_fixed = corrector.correct_token("xylophone")
        assert was_fixed is False

    def test_short_token_skipped(self, corrector):
        """Tokens shorter than MIN_WORD_LENGTH are left alone."""
        token, was_fixed = corrector.correct_token("ab")
        assert token == "ab"
        assert was_fixed is False

    def test_correct_query_no_correction(self, corrector):
        _, suggestion = corrector.correct_query("bluetooth headphones")
        assert suggestion is None

    def test_correct_query_with_correction(self, corrector):
        corrected, suggestion = corrector.correct_query("bluetoth headphons")
        assert suggestion is not None
        assert "bluetooth" in suggestion
        assert "headphones" in suggestion

    def test_empty_query(self, corrector):
        result, suggestion = corrector.correct_query("")
        assert result == ""
        assert suggestion is None

    def test_whitespace_query(self, corrector):
        result, suggestion = corrector.correct_query("   ")
        assert suggestion is None

    def test_single_misspelled_word(self, corrector):
        _, suggestion = corrector.correct_query("wireles speaker")
        assert suggestion is not None
        assert "wireless" in suggestion

    def test_correct_single_word(self, corrector):
        _, suggestion = corrector.correct_query("laptop")
        assert suggestion is None

    def test_mixed_correct_and_wrong(self, corrector):
        _, suggestion = corrector.correct_query("gaming keybord")
        assert suggestion is not None
        assert "keyboard" in suggestion
        assert "gaming" in suggestion
