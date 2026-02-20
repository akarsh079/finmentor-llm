from dataclasses import dataclass
from typing import List

from finmentor.retrieval.retriever import retrieve


@dataclass
class FakeCard:
    title: str
    tags: List[str]
    summary: str


def test_retrieve_debug_title_match():
    cards = [
        FakeCard(title="Compound Interest Basics", tags=["interest", "math"], summary="How growth works."),
        FakeCard(title="Budgeting 101", tags=["budget"], summary="Track spending."),
    ]

    results, debug_map = retrieve("compound", cards, top_k=10, debug=True)

    assert len(results) == 1
    assert results[0].title == "Compound Interest Basics"

    # debug_map uses index keys (0, 1, ...)
    dbg0 = debug_map[0]
    assert "title" in dbg0.matched_fields
    assert "compound" in dbg0.matched_terms


def test_retrieve_debug_tags_match():
    cards = [
        FakeCard(title="Emergency Fund", tags=["cash", "savings"], summary="Liquidity matters."),
        FakeCard(title="Credit Scores", tags=["credit"], summary="What affects your score."),
    ]

    results, debug_map = retrieve("savings", cards, top_k=10, debug=True)

    assert len(results) == 1
    dbg0 = debug_map[0]
    assert "tags" in dbg0.matched_fields
    assert "savings" in dbg0.matched_terms


def test_retrieve_empty_query_returns_empty_and_debug_empty():
    cards = [FakeCard(title="X", tags=["y"], summary="z")]

    results, debug_map = retrieve("   ", cards, debug=True)

    assert results == []
    assert debug_map == {}
