from __future__ import annotations

from dataclasses import dataclass
from typing import Set, Any

@dataclass(frozen=True)
class ScoreBreakdown:
    keyword_overlap: float
    field_boost: float
    total: float

def score_card(query: str, card: ConceptCard) -> ScoreBreakdown: 
    