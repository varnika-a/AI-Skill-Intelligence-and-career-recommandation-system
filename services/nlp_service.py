"""
NLP service: skill extraction from text using controlled vocabulary.

Features:
- tokenization and normalization
- substring matching
- fuzzy matching via difflib for minor variations
- returns list of (skill, confidence) tuples sorted by confidence
"""
from typing import List, Tuple
import re
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower())


def _ngrams(tokens: List[str], n: int):
    for i in range(len(tokens) - n + 1):
        yield ' '.join(tokens[i:i + n])


def extract_skills_from_text(text: str, vocabulary: List[str], fuzzy_threshold: float = 0.78) -> List[Tuple[str, float]]:
    """Extract skills from `text` using `vocabulary`.

    Returns a list of (skill_name, confidence) ordered descending by confidence.
    Confidence approx 0-1.
    """
    if not text or not vocabulary:
        return []
    norm = _normalize(text)
    tokens = [t for t in norm.split() if t]

    vocab_norm = {v: _normalize(v) for v in vocabulary}

    found = {}
    # first try direct substring / exact ngram matches
    for v, vn in vocab_norm.items():
        if vn and vn in norm:
            # confidence based on length
            conf = min(0.98, 0.6 + 0.01 * len(vn.split()))
            found[v] = max(found.get(v, 0), conf)

    # try fuzzy matching on ngrams (1-3)
    ngrams = set()
    for n in (3, 2, 1):
        for ng in _ngrams(tokens, n):
            ngrams.add(ng)

    for v, vn in vocab_norm.items():
        if v in found:
            continue
        best = 0.0
        for ng in ngrams:
            r = SequenceMatcher(None, vn, ng).ratio()
            if r > best:
                best = r
        if best >= fuzzy_threshold:
            # small adjustment based on match length
            conf = 0.45 + 0.5 * best
            found[v] = max(found.get(v, 0), conf)

    # produce sorted list
    results = sorted([(k, float(v)) for k, v in found.items()], key=lambda x: x[1], reverse=True)
    return results

