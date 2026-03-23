"""
Spell correction using Levenshtein edit distance against a known vocabulary.

Compares each query token to the Word2Vec vocabulary.  When a token is
out-of-vocabulary and a close match exists (edit distance <= 2), the
corrected form is suggested.  The corrected query is returned alongside
the original so the frontend can show "Did you mean: ...?"
"""

import logging
from typing import Dict, List, Optional, Tuple

from .tokenizer import tokenize

logger = logging.getLogger(__name__)

MAX_EDIT_DISTANCE = 2
MIN_WORD_LENGTH = 3


def _levenshtein(a: str, b: str) -> int:
    """Classic dynamic-programming Levenshtein distance."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            temp = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = temp
    return dp[m]


class SpellCorrector:
    """Suggests spelling corrections for out-of-vocabulary query tokens.

    Uses the Word2Vec model's vocabulary as the "dictionary" and
    Levenshtein edit distance to find the closest known word.

    Example:
        >>> sc = SpellCorrector(vocab_words)
        >>> sc.correct_query("bluetoth headphons")
        ('bluetooth headphones', True)
    """

    def __init__(self, vocabulary: List[str]) -> None:
        """Build a correction index from a word vocabulary.

        Args:
            vocabulary: List of known words (typically from Word2Vec).
        """
        self._vocab_set = set(vocabulary)
        self._vocab_by_length: Dict[int, List[str]] = {}
        for word in vocabulary:
            length = len(word)
            self._vocab_by_length.setdefault(length, []).append(word)
        logger.info("SpellCorrector built with %d vocabulary words", len(self._vocab_set))

    @property
    def vocabulary_size(self) -> int:
        """Number of words in the correction dictionary."""
        return len(self._vocab_set)

    def correct_token(self, token: str) -> Tuple[str, bool]:
        """Correct a single token if it's out-of-vocabulary.

        Args:
            token: A lowercased token.

        Returns:
            (corrected_token, was_corrected) tuple.
        """
        if token in self._vocab_set:
            return token, False

        if len(token) < MIN_WORD_LENGTH:
            return token, False

        best_word = token
        best_dist = MAX_EDIT_DISTANCE + 1

        for length in range(len(token) - MAX_EDIT_DISTANCE, len(token) + MAX_EDIT_DISTANCE + 1):
            for candidate in self._vocab_by_length.get(length, []):
                dist = _levenshtein(token, candidate)
                if dist < best_dist:
                    best_dist = dist
                    best_word = candidate

        corrected = best_dist <= MAX_EDIT_DISTANCE
        return best_word, corrected

    def correct_query(self, query: str) -> Tuple[str, Optional[str]]:
        """Correct an entire query string.

        Tokenizes the query, corrects each OOV token, and reconstructs
        the corrected query.

        Args:
            query: Raw user query text.

        Returns:
            (corrected_query, suggestion) where suggestion is the
            human-readable corrected string if any tokens were fixed,
            or None if no corrections were needed.
        """
        if not query or not query.strip():
            return query, None

        tokens = tokenize(query)
        if not tokens:
            return query, None

        corrected_tokens: List[str] = []
        any_corrected = False

        for token in tokens:
            fixed, was_fixed = self.correct_token(token)
            corrected_tokens.append(fixed)
            if was_fixed:
                any_corrected = True

        if not any_corrected:
            return query, None

        suggestion = " ".join(corrected_tokens)
        return suggestion, suggestion
