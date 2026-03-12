"""
Text preprocessing for the query understanding pipeline.

Handles tokenization, stopword removal, and n-gram extraction using NLTK.
"""

import re
import string
from typing import List

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

_STOPWORDS = set(stopwords.words("english"))

MIN_TOKEN_LENGTH = 2


def tokenize(text: str) -> List[str]:
    """Tokenize, lowercase, strip stopwords and short tokens.

    Args:
        text: Raw input text.

    Returns:
        Cleaned list of tokens.

    Example:
        >>> tokenize("Bluetooth Headphones for Running")
        ['bluetooth', 'headphones', 'running']
    """
    if not text or not text.strip():
        return []

    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = word_tokenize(text)

    return [
        t
        for t in tokens
        if t not in _STOPWORDS
        and len(t) >= MIN_TOKEN_LENGTH
        and not all(c in string.punctuation for c in t)
    ]


def extract_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Build underscore-joined n-grams from a token list.

    Args:
        tokens: Pre-tokenized word list.
        n: N-gram size (default: bigrams).

    Returns:
        List of n-gram strings.

    Example:
        >>> extract_ngrams(["bluetooth", "headphones"], n=2)
        ['bluetooth_headphones']
    """
    if len(tokens) < n:
        return []
    return ["_".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
