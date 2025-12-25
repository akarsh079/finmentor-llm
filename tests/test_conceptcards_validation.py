import pytest

from finmentor.domain.concepts.loader import load_raw_conceptcards
from finmentor.domain.concepts.validator import (
    ConceptValidationError,
    validate_all_conceptcards,
    validate_conceptcard,
)


def test_load_and_validate_real_conceptcards():
    raw = load_raw_conceptcards()
    cards = validate_all_conceptcards(raw)
    assert len(cards) >= 1
    assert any(c.id == "credit_score" for c in cards)


def test_reject_missing_non_goals():
    bad = {
        "id": "bad_card",
        "title": "Bad Card",
        "category": "credit",
        "difficulty": "beginner",
        "summary": ["ok"],
        "core_mechanics": ["ok"],
        "examples": [],
        "misconceptions": ["ok"],
        # non_goals missing
        "safety": {
            "allowed_intents": ["educational_explanation"],
            "forbidden_intents": ["personal_advice", "product_recommendation"],
        },
        "metadata": {
            "sources": ["https://example.com"],
            "last_updated": "2025-12-25",
        },
    }
    with pytest.raises(ConceptValidationError):
        validate_conceptcard(bad)


def test_reject_placeholders_anywhere():
    bad = {
        "id": "placeholder_card",
        "title": "Placeholder Card",
        "category": "credit",
        "difficulty": "beginner",
        "summary": ["<todo>"],
        "core_mechanics": ["ok"],
        "examples": [],
        "misconceptions": ["ok"],
        "non_goals": ["ok"],
        "safety": {
            "allowed_intents": ["educational_explanation"],
            "forbidden_intents": ["personal_advice", "product_recommendation"],
        },
        "metadata": {
            "sources": ["https://example.com"],
            "last_updated": "2025-12-25",
        },
    }
    with pytest.raises(ConceptValidationError):
        validate_conceptcard(bad)


def test_reject_invalid_enum_values():
    bad = {
        "id": "enum_card",
        "title": "Enum Card",
        "category": "not_a_category",
        "difficulty": "beginner",
        "summary": ["ok"],
        "core_mechanics": ["ok"],
        "examples": [],
        "misconceptions": ["ok"],
        "non_goals": ["ok"],
        "safety": {
            "allowed_intents": ["educational_explanation"],
            "forbidden_intents": ["personal_advice", "product_recommendation"],
        },
        "metadata": {
            "sources": ["https://example.com"],
            "last_updated": "2025-12-25",
        },
    }
    with pytest.raises(ConceptValidationError):
        validate_conceptcard(bad)


def test_reject_empty_sources():
    bad = {
        "id": "nosource_card",
        "title": "No Source Card",
        "category": "credit",
        "difficulty": "beginner",
        "summary": ["ok"],
        "core_mechanics": ["ok"],
        "examples": [],
        "misconceptions": ["ok"],
        "non_goals": ["ok"],
        "safety": {
            "allowed_intents": ["educational_explanation"],
            "forbidden_intents": ["personal_advice", "product_recommendation"],
        },
        "metadata": {
            "sources": [],
            "last_updated": "2025-12-25",
        },
    }
    with pytest.raises(ConceptValidationError):
        validate_conceptcard(bad)


def test_require_forbidden_intents_include_baseline():
    bad = {
        "id": "forbidden_card",
        "title": "Forbidden Card",
        "category": "credit",
        "difficulty": "beginner",
        "summary": ["ok"],
        "core_mechanics": ["ok"],
        "examples": [],
        "misconceptions": ["ok"],
        "non_goals": ["blocks advice and recommendations"],
        "safety": {
            "allowed_intents": ["educational_explanation"],
            # missing product_recommendation
            "forbidden_intents": ["personal_advice"],
        },
        "metadata": {
            "sources": ["https://example.com"],
            "last_updated": "2025-12-25",
        },
    }
    with pytest.raises(ConceptValidationError):
        validate_conceptcard(bad)
