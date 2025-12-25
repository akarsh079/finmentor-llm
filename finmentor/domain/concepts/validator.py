from __future__ import annotations

import re
from typing import Any, Dict, List

from .types import Category, ConceptCard, ConceptExample, Difficulty, Intent


class ConceptValidationError(ValueError):
    """Raised when a ConceptCard YAML dict fails validation."""
    pass


# --- heuristics / hard checks ---
_PLACEHOLDER_RE = re.compile(r"<[^>]+>")
_SECOND_PERSON_RE = re.compile(r"\b(you|your|yours|yourself)\b", flags=re.IGNORECASE)


def _card_id_for_errors(raw: Dict[str, Any]) -> str:
    cid = raw.get("id")
    return cid if isinstance(cid, str) and cid.strip() else "<missing-id>"


def _raise(card_id: str, field: str, msg: str) -> None:
    raise ConceptValidationError(f"[ConceptCard id={card_id}] {field}: {msg}")


def _require_key(raw: Dict[str, Any], card_id: str, key: str) -> Any:
    if key not in raw:
        _raise(card_id, key, "missing required field")
    return raw[key]


def _require_str(raw: Dict[str, Any], card_id: str, key: str) -> str:
    v = _require_key(raw, card_id, key)
    if not isinstance(v, str) or not v.strip():
        _raise(card_id, key, "must be a non-empty string")
    if _PLACEHOLDER_RE.search(v):
        _raise(card_id, key, "contains placeholder text like <...>")
    return v.strip()


def _require_list_of_str(raw: Dict[str, Any], card_id: str, key: str, min_len: int = 1) -> List[str]:
    v = _require_key(raw, card_id, key)
    if not isinstance(v, list):
        _raise(card_id, key, "must be a list of strings")
    out: List[str] = []
    for i, item in enumerate(v):
        if not isinstance(item, str) or not item.strip():
            _raise(card_id, f"{key}[{i}]", "must be a non-empty string")
        if _PLACEHOLDER_RE.search(item):
            _raise(card_id, f"{key}[{i}]", "contains placeholder text like <...>")
        out.append(item.strip())
    if len(out) < min_len:
        _raise(card_id, key, f"must contain at least {min_len} item(s)")
    return out


def _to_enum(card_id: str, field: str, enum_cls: Any, value: str):
    try:
        return enum_cls(value)
    except Exception:
        allowed = ", ".join([e.value for e in enum_cls])
        _raise(card_id, field, f"invalid value '{value}'. Allowed: {allowed}")


def _require_enum(raw: Dict[str, Any], card_id: str, key: str, enum_cls: Any):
    s = _require_str(raw, card_id, key)
    return _to_enum(card_id, key, enum_cls, s)


def _require_examples(raw: Dict[str, Any], card_id: str) -> List[ConceptExample]:
    examples_raw = _require_key(raw, card_id, "examples")
    if not isinstance(examples_raw, list):
        _raise(card_id, "examples", "must be a list of example objects")
    examples: List[ConceptExample] = []
    for i, ex in enumerate(examples_raw):
        if not isinstance(ex, dict):
            _raise(card_id, f"examples[{i}]", "must be a mapping with scenario/explanation")
        scenario = ex.get("scenario")
        explanation = ex.get("explanation")
        if not isinstance(scenario, str) or not scenario.strip():
            _raise(card_id, f"examples[{i}].scenario", "must be a non-empty string")
        if not isinstance(explanation, str) or not explanation.strip():
            _raise(card_id, f"examples[{i}].explanation", "must be a non-empty string")
        if _PLACEHOLDER_RE.search(scenario):
            _raise(card_id, f"examples[{i}].scenario", "contains placeholder text like <...>")
        if _PLACEHOLDER_RE.search(explanation):
            _raise(card_id, f"examples[{i}].explanation", "contains placeholder text like <...>")
        examples.append(ConceptExample(scenario=scenario.strip(), explanation=explanation.strip()))
    # examples can be empty early, but shouldn't contain placeholders if present
    return examples


def _require_safety(raw: Dict[str, Any], card_id: str) -> tuple[List[Intent], List[Intent]]:
    safety = _require_key(raw, card_id, "safety")
    if not isinstance(safety, dict):
        _raise(card_id, "safety", "must be a mapping with allowed_intents/forbidden_intents")

    allowed_raw = safety.get("allowed_intents")
    forbidden_raw = safety.get("forbidden_intents")

    if not isinstance(allowed_raw, list) or not all(isinstance(x, str) for x in allowed_raw):
        _raise(card_id, "safety.allowed_intents", "must be a list of strings")
    if not isinstance(forbidden_raw, list) or not all(isinstance(x, str) for x in forbidden_raw):
        _raise(card_id, "safety.forbidden_intents", "must be a list of strings")

    allowed: List[Intent] = []
    for i, s in enumerate(allowed_raw):
        s2 = s.strip()
        if not s2:
            _raise(card_id, f"safety.allowed_intents[{i}]", "must be a non-empty string")
        if _PLACEHOLDER_RE.search(s2):
            _raise(card_id, f"safety.allowed_intents[{i}]", "contains placeholder text like <...>")
        allowed.append(_to_enum(card_id, f"safety.allowed_intents[{i}]", Intent, s2))

    forbidden: List[Intent] = []
    for i, s in enumerate(forbidden_raw):
        s2 = s.strip()
        if not s2:
            _raise(card_id, f"safety.forbidden_intents[{i}]", "must be a non-empty string")
        if _PLACEHOLDER_RE.search(s2):
            _raise(card_id, f"safety.forbidden_intents[{i}]", "contains placeholder text like <...>")
        forbidden.append(_to_enum(card_id, f"safety.forbidden_intents[{i}]", Intent, s2))

    # Hard safety requirements for Phase 2 (education-only baseline)
    must_forbid = {Intent.PERSONAL_ADVICE, Intent.PRODUCT_RECOMMENDATION}
    forbidden_set = set(forbidden)
    missing = must_forbid - forbidden_set
    if missing:
        missing_str = ", ".join([m.value for m in sorted(missing, key=lambda x: x.value)])
        _raise(card_id, "safety.forbidden_intents", f"must include: {missing_str}")

    # Ensure no overlaps
    overlap = set(allowed) & set(forbidden)
    if overlap:
        overlap_str = ", ".join([o.value for o in sorted(overlap, key=lambda x: x.value)])
        _raise(card_id, "safety", f"allowed_intents and forbidden_intents overlap: {overlap_str}")

    return allowed, forbidden


def _require_metadata(raw: Dict[str, Any], card_id: str) -> tuple[List[str], str]:
    meta = _require_key(raw, card_id, "metadata")
    if not isinstance(meta, dict):
        _raise(card_id, "metadata", "must be a mapping with sources/last_updated")

    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        _raise(card_id, "metadata.sources", "must be a non-empty list of strings")
    clean_sources: List[str] = []
    for i, s in enumerate(sources):
        if not isinstance(s, str) or not s.strip():
            _raise(card_id, f"metadata.sources[{i}]", "must be a non-empty string")
        if _PLACEHOLDER_RE.search(s):
            _raise(card_id, f"metadata.sources[{i}]", "contains placeholder text like <...>")
        clean_sources.append(s.strip())

    last_updated = meta.get("last_updated")
    if not isinstance(last_updated, str) or not last_updated.strip():
        _raise(card_id, "metadata.last_updated", "must be a non-empty string in YYYY-MM-DD format")
    last_updated = last_updated.strip()
    if _PLACEHOLDER_RE.search(last_updated):
        _raise(card_id, "metadata.last_updated", "contains placeholder text like <...>")

    # Light date-format check (YYYY-MM-DD)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", last_updated):
        _raise(card_id, "metadata.last_updated", "must match YYYY-MM-DD")

    return clean_sources, last_updated


def _education_only_heuristics(card_id: str, raw: Dict[str, Any]) -> None:
    """
    Optional hard-ish checks to keep ConceptCards educational and non-personal.
    Keep these lightweight; deeper checks belong in guardrails/router.
    """
    # Summaries should not use 2nd person phrasing
    summary_list = raw.get("summary", [])
    if isinstance(summary_list, list):
        for i, s in enumerate(summary_list):
            if isinstance(s, str) and _SECOND_PERSON_RE.search(s):
                _raise(card_id, f"summary[{i}]", "should avoid second-person phrasing (you/your)")

    # Ensure non_goals exists and is meaningful (blocks advice creep)
    non_goals = raw.get("non_goals")
    if isinstance(non_goals, list):
        joined = " ".join([x for x in non_goals if isinstance(x, str)]).lower()
        # Require some advice-blocking intent in non_goals text
        if not any(term in joined for term in ["advice", "recommend", "optimiz", "personal", "product"]):
            _raise(card_id, "non_goals", "must explicitly block advice/recommendation/optimization scope")

    # Placeholders anywhere in top-level string/list fields are caught elsewhere;
    # this is just extra guard for future fields.
    for key, value in raw.items():
        if isinstance(value, str) and _PLACEHOLDER_RE.search(value):
            _raise(card_id, key, "contains placeholder text like <...>")


def validate_conceptcard(raw: Dict[str, Any]) -> ConceptCard:
    """
    Validate a raw YAML dict and return a ConceptCard domain object.
    Raises ConceptValidationError on failure.
    """
    if not isinstance(raw, dict):
        raise ConceptValidationError("ConceptCard raw value must be a dict")

    card_id = _card_id_for_errors(raw)

    # Required base fields
    cid = _require_str(raw, card_id, "id")
    title = _require_str(raw, card_id, "title")
    category = _require_enum(raw, card_id, "category", Category)
    difficulty = _require_enum(raw, card_id, "difficulty", Difficulty)

    summary = _require_list_of_str(raw, card_id, "summary", min_len=1)
    core_mechanics = _require_list_of_str(raw, card_id, "core_mechanics", min_len=1)
    misconceptions = _require_list_of_str(raw, card_id, "misconceptions", min_len=1)
    non_goals = _require_list_of_str(raw, card_id, "non_goals", min_len=1)

    examples = _require_examples(raw, card_id)
    allowed_intents, forbidden_intents = _require_safety(raw, card_id)
    sources, last_updated = _require_metadata(raw, card_id)

    # Education-only heuristics
    _education_only_heuristics(card_id, raw)

    # One more structural sanity check: id must match snake_case-ish
    if not re.fullmatch(r"[a-z][a-z0-9_]*", cid):
        _raise(card_id, "id", "must be snake_case (lowercase letters, digits, underscores)")

    return ConceptCard(
        id=cid,
        title=title,
        category=category,
        difficulty=difficulty,
        summary=summary,
        core_mechanics=core_mechanics,
        examples=examples,
        misconceptions=misconceptions,
        non_goals=non_goals,
        allowed_intents=allowed_intents,
        forbidden_intents=forbidden_intents,
        sources=sources,
        last_updated=last_updated,
    )


def validate_all_conceptcards(raw_cards: List[Dict[str, Any]]) -> List[ConceptCard]:
    """
    Validate a list of raw ConceptCard dicts. Also enforces uniqueness of ids.
    """
    cards: List[ConceptCard] = []
    seen_ids: set[str] = set()

    for raw in raw_cards:
        card = validate_conceptcard(raw)
        if card.id in seen_ids:
            raise ConceptValidationError(f"Duplicate ConceptCard id detected: {card.id}")
        seen_ids.add(card.id)
        cards.append(card)

    return cards
