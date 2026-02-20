from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List, Set, TypeVar, Dict, Tuple

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but",
    "is", "are", "was", "were", "be", "being", "been",
    "to", "of", "in", "on", "for", "with", "as", "at", "by", "from",
    "what", "why", "how", "when", "where", "who", "which",
    "i", "you", "we", "they", "he", "she", "it", "my", "your", "our", "their",
}

T = TypeVar("T")  # ConceptCard (or compatible object)


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> Set[str]:
    """Lowercase alphanumeric tokenization."""
    raw = _WORD_RE.findall((text or "").lower())
    return {t for t in raw if t not in _STOPWORDS}


def _stringify(value: Any) -> str:
    """Best-effort convert arbitrary field values to text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(x) for x in value if x is not None)
    return str(value)


def retrieve_candidates(query: str, cards: List[T]) -> List[T]:
    """
    Return *unsorted* candidate ConceptCards that match the query by simple
    token overlap against common fields (title/tags/summary).
    Preserves the original card order.
    """
    q = (query or "").strip()
    if not q:
        return []

    q_tokens = _tokens(q)
    if not q_tokens:
        return []

    candidates: List[T] = []

    for card in cards:
        title = _stringify(getattr(card, "title", ""))
        tags = _stringify(getattr(card, "tags", ""))
        summary = _stringify(getattr(card, "summary", ""))

        haystack = " ".join([title, tags, summary]).strip()
        if not haystack:
            continue

        card_tokens = _tokens(haystack)

        # Match rule: any overlap (baseline).
        if q_tokens & card_tokens:
            candidates.append(card)

    return candidates


@dataclass(frozen=True)
class RetrievalDebug:
    """
    Debug metadata for a retrieved card.
    Keep this lightweight; scoring breakdown comes in Phase 3.2.
    """
    matched_terms: Tuple[str, ...]
    matched_fields: Tuple[str, ...]


def _match_debug(query_tokens: Set[str], card: T) -> RetrievalDebug:
    """
    Explain which fields contributed overlap and which terms overlapped.
    """
    fields: Dict[str, str] = {
        "title": _stringify(getattr(card, "title", "")),
        "tags": _stringify(getattr(card, "tags", "")),
        "summary": _stringify(getattr(card, "summary", "")),
    }

    matched_fields: List[str] = []
    all_overlap: Set[str] = set()

    for name, text in fields.items():
        t = _tokens(text)
        overlap = query_tokens & t
        if overlap:
            matched_fields.append(name)
            all_overlap |= overlap

    return RetrievalDebug(
        matched_terms=tuple(sorted(all_overlap)),
        matched_fields=tuple(matched_fields),
    )


def retrieve(query: str, cards: List[T], *, top_k: int = 8, debug: bool = False):
    q = (query or "").strip()
    if not q or top_k <= 0:
        return ([], {}) if debug else []

    q_tokens = _tokens(q)
    candidates = retrieve_candidates(q, cards)

    scored: list[tuple[int, T]] = []
    for card in candidates:
        title = _stringify(getattr(card, "title", ""))
        tags = _stringify(getattr(card, "tags", ""))
        summary = _stringify(getattr(card, "summary", ""))

        haystack = " ".join([title, tags, summary]).strip()
        if not haystack:
            continue

        card_tokens = _tokens(haystack)
        matched_terms = q_tokens & card_tokens
        score = len(matched_terms)

        scored.append((score, card))

    scored = scored[:top_k]

    if not debug:
        return scored

    debug_map: Dict[int, RetrievalDebug] = {}
    for i in (score, card) in enumerate(scored):
        debug_map[i] = _match_debug(q_tokens, card)

    return scored, debug_map

