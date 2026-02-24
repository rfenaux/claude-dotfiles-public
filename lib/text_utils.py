"""
Unified Text Utilities for Claude Code

Provides shared text processing functions used across:
- intent_predictor.py (pattern learning)
- topic_clusters.py (document clustering)
- chunk_classifier.py (content classification)
- bm25.py (keyword search)

Consolidates duplicate implementations for:
- Stopword filtering
- Keyword extraction (TF-IDF style)
- Text tokenization
"""

import math
import re
from collections import Counter
from typing import List, Dict, Optional, Set


# =============================================================================
# UNIFIED STOPWORDS
# =============================================================================
# Merged from all implementations - comprehensive list for technical content

STOPWORDS: Set[str] = {
    # Articles & Determiners
    'the', 'a', 'an', 'this', 'that', 'these', 'those',

    # Conjunctions & Prepositions
    'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'from', 'as', 'about', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'under', 'again', 'further', 'out', 'up',
    'down', 'off', 'over', 'if', 'than', 'so',

    # Be verbs & Auxiliaries
    'is', 'was', 'are', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',

    # Pronouns
    'it', 'its', 'i', 'we', 'you', 'he', 'she', 'they',
    'what', 'which', 'who', 'when', 'where', 'why', 'how',
    'any', 'own', 'your', 'our', 'their', 'my',

    # Quantifiers & Modifiers
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'not', 'only', 'same', 'too', 'very', 'just', 'also',

    # Time & Place
    'now', 'here', 'there', 'then', 'once', 'first', 'last', 'new', 'old',

    # Generic document terms (often not meaningful for topic extraction)
    'file', 'document', 'page', 'section', 'chapter', 'part',
    'see', 'use', 'using', 'used', 'example', 'following',
    'based', 'need', 'like', 'make', 'get', 'set',
}


# =============================================================================
# TOKENIZATION
# =============================================================================

def tokenize(
    text: str,
    min_length: int = 3,
    remove_stopwords: bool = True,
    lowercase: bool = True,
    alphanumeric_only: bool = True
) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Input text to tokenize
        min_length: Minimum word length (default: 3)
        remove_stopwords: Whether to filter stopwords (default: True)
        lowercase: Whether to lowercase tokens (default: True)
        alphanumeric_only: Only keep alphanumeric words (default: True)

    Returns:
        List of tokens
    """
    if not text:
        return []

    if lowercase:
        text = text.lower()

    # Extract words based on pattern
    if alphanumeric_only:
        pattern = rf'\b[a-zA-Z0-9]{{{min_length},}}\b'
    else:
        pattern = rf'\b\w{{{min_length},}}\b'

    words = re.findall(pattern, text)

    if remove_stopwords:
        words = [w for w in words if w.lower() not in STOPWORDS]

    return words


def tokenize_unique(
    text: str,
    min_length: int = 3,
    remove_stopwords: bool = True,
    max_tokens: int = 0
) -> List[str]:
    """
    Tokenize text and return unique tokens (preserving order).

    Args:
        text: Input text
        min_length: Minimum word length
        remove_stopwords: Filter stopwords
        max_tokens: Maximum tokens to return (0 = unlimited)

    Returns:
        List of unique tokens in order of first appearance
    """
    tokens = tokenize(text, min_length, remove_stopwords)
    # Preserve order while deduplicating
    seen = set()
    unique = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique.append(token)

    if max_tokens > 0:
        return unique[:max_tokens]
    return unique


# =============================================================================
# KEYWORD EXTRACTION (TF-IDF STYLE)
# =============================================================================

def extract_keywords(
    text: str,
    top_k: int = 5,
    method: str = 'frequency',
    min_length: int = 3
) -> List[str]:
    """
    Extract top keywords from a single text.

    Args:
        text: Input text
        top_k: Number of keywords to return
        method: 'frequency' (simple count) or 'tfidf' (requires corpus)
        min_length: Minimum word length

    Returns:
        List of top keywords
    """
    tokens = tokenize(text, min_length=min_length, remove_stopwords=True)

    if not tokens:
        return []

    if method == 'frequency':
        # Simple frequency-based extraction
        counter = Counter(tokens)
        return [word for word, _ in counter.most_common(top_k)]

    # For single-text TF-IDF, just use term frequency
    counter = Counter(tokens)
    total = sum(counter.values())
    scored = [(word, count / total) for word, count in counter.items()]
    scored.sort(key=lambda x: -x[1])
    return [word for word, _ in scored[:top_k]]


def extract_keywords_tfidf(
    texts: List[str],
    top_k: int = 5,
    min_length: int = 3
) -> List[str]:
    """
    Extract top keywords from multiple texts using TF-IDF scoring.

    This is useful for finding distinguishing keywords in a corpus
    (e.g., for cluster labeling).

    Args:
        texts: List of texts (corpus)
        top_k: Number of keywords to return
        min_length: Minimum word length

    Returns:
        List of top keywords by TF-IDF score
    """
    if not texts:
        return []

    # Count: how many docs contain each word
    word_doc_counts: Counter = Counter()
    # Count: total occurrences of each word
    word_total_counts: Counter = Counter()

    for text in texts:
        tokens = tokenize(text, min_length=min_length, remove_stopwords=True)
        unique_tokens = set(tokens)

        # Document frequency
        for word in unique_tokens:
            word_doc_counts[word] += 1

        # Term frequency
        for word in tokens:
            word_total_counts[word] += 1

    if not word_doc_counts:
        return []

    # Calculate TF-IDF
    num_docs = len(texts)
    total_terms = sum(word_total_counts.values()) or 1
    scores = {}

    for word, doc_count in word_doc_counts.items():
        # TF: term frequency (normalized)
        tf = word_total_counts[word] / total_terms
        # IDF: inverse document frequency (with smoothing)
        idf = math.log(num_docs / doc_count) + 1
        scores[word] = tf * idf

    # Sort by score descending
    sorted_words = sorted(scores.items(), key=lambda x: -x[1])
    return [word for word, _ in sorted_words[:top_k]]


def extract_keywords_for_context(
    context: str,
    max_keywords: int = 5
) -> List[str]:
    """
    Extract keywords from context string (optimized for short text).

    Used by intent_predictor for extracting context keywords.

    Args:
        context: Short context string
        max_keywords: Maximum keywords to return

    Returns:
        List of unique keywords (preserving order)
    """
    return tokenize_unique(
        context,
        min_length=3,
        remove_stopwords=True,
        max_tokens=max_keywords
    )


# =============================================================================
# LABEL GENERATION
# =============================================================================

def generate_label_from_keywords(
    keywords: List[str],
    max_words: int = 3,
    separator: str = '-'
) -> str:
    """
    Generate a human-readable label from keywords.

    Used for cluster labels, topic tags, etc.

    Args:
        keywords: List of keywords
        max_words: Maximum words in label
        separator: Word separator

    Returns:
        Label string (e.g., "hubspot-api-auth")
    """
    if not keywords:
        return "misc"

    label_words = keywords[:max_words]
    return separator.join(label_words)


# =============================================================================
# TEXT SIMILARITY (Simple)
# =============================================================================

def keyword_overlap(text1: str, text2: str) -> float:
    """
    Calculate keyword overlap between two texts.

    Returns Jaccard similarity of keyword sets.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Overlap score 0.0 to 1.0
    """
    kw1 = set(tokenize(text1, remove_stopwords=True))
    kw2 = set(tokenize(text2, remove_stopwords=True))

    if not kw1 or not kw2:
        return 0.0

    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)

    return intersection / union if union > 0 else 0.0


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'STOPWORDS',
    'tokenize',
    'tokenize_unique',
    'extract_keywords',
    'extract_keywords_tfidf',
    'extract_keywords_for_context',
    'generate_label_from_keywords',
    'keyword_overlap',
]
