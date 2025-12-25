from dataclasses import dataclass
from enum import Enum
from typing import List

__all__ = [
    "Category",
    "Difficulty",
    "Intent",
    "ConceptExample",
    "ConceptCard",
]

class Category(Enum):
    BUDGETING = "budgeting"
    CREDIT = "credit"
    INVESTING = "investing"
    TAXES = "taxes"
    BANKING = "banking"
    INSURANCE = "insurance"
    DEBT = "debt"

class Difficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class Intent(Enum):
    EDUCATIONAL_EXPLANATION = "educational_explanation"
    DEFINITION_LOOKUP = "definition_lookup"
    PERSONAL_ADVICE = "personal_advice"
    SCORE_OPTIMIZATION = "score_optimization"
    PRODUCT_RECOMMENDATION = "product_recommendation"

@dataclass
class ConceptExample:
    scenario: str
    explanation: str

@dataclass
class ConceptCard:
    id: str
    title: str
    category: Category
    difficulty: Difficulty

    summary: List[str]
    core_mechanics: List[str]
    examples: List[ConceptExample]
    misconceptions: List[str]
    non_goals: List[str]

    allowed_intents: List[Intent]
    forbidden_intents: List[Intent]

    sources: List[str]
    last_updated: str
