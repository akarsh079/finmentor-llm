"""
Reminder: This module enforces FinMentor's safety/scope guardrails.
It does NOT do retrieval. It does NOT answer finance questions.
It only decides: ALLOW vs TRANSFORM vs REFUSE (+ reason tag + safe rewrite).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    TRANSFORM = "TRANSFORM"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class PolicyDecision:
    action: PolicyAction
    reason: str
    rewrite: Optional[str] = None


# -------------------------
# Reason tags (stable contract for eval/tests)
# -------------------------
REASON_GENERAL_EDU = "general_education"
REASON_PERSONALIZED_ADVICE = "personalized_advice"
REASON_ASSET_RECOMMENDATION = "asset_recommendation"
REASON_TIMING_REQUEST = "timing_request"
REASON_PORTFOLIO_ALLOCATION = "portfolio_allocation"
REASON_ILLEGAL_FINANCIAL = "illegal_financial"
REASON_AMBIGUOUS = "ambiguous"


# -------------------------
# Patterns (v1 heuristics)
# -------------------------

# Requests that are typically illegal/harmful (REFUSE)
_ILLEGAL_PATTERNS = [
    r"\bmoney\s+launder(ing|)\b", # money laundering
    r"\blaunder(ing|)\b.*\bmoney\b", # laundering money
    r"\binsider\s+trad(ing|e)\b", # insider trading
    r"\bfront[-\s]?run(ning|)\b", # front running 
    r"\bevade\s+tax(es|)\b", # evade taxes 
    r"\btax\s+evasion\b", # tax evasion
    r"\bfake\s+(receipt|invoic)e(s|)\b", # fake receipt invoices 
    r"\bforg(e|ing)\s+(a|an)\s+(receipt|invoice|statement)\b", # forging receipt / invoice / statement 
    r"\bcommit\s+fraud\b", # commit fraud 
    r"\bponzi\b", # ponzi 
]

# Advice-seeking / recommendation phrasing (TRANSFORM)
_ADVICE_PATTERNS = [
    r"\bwhat\s+should\s+i\s+(invest|buy|do)\b", # what should I (invest / buy / do)
    r"\bshould\s+i\s+(buy|sell|invest)\b", # should I (buy / sell / invest)
    r"\bis\s+.+\s+a\s+good\s+(buy|investment)\b", # is ____ a good (buy / investment)
    r"\b(best|top)\s+(stock|etf|crypto|investment)\b", # (best / top) (stock / etf/ crypto / investment)
    r"\bwhich\s+(stock|etf|crypto)\s+should\s+i\s+(buy|pick)\b", # which (stock / etf / crypto) should I (buy / pick)
    r"\b(rate|rank)\s+.+\s+(stock|etf|crypto)\b", # (rate / rank) ____ (stock / etc/ crypto)
    r"\bbest\s+way\s+to\s+invest\b", # best way to invest
    r"\binvest\s+my\s+money\b", # invest my money
    r"\bwhat'?s\s+the\s+best\s+way\s+to\s+invest\b", # what's the best way to invest
]

# Portfolio allocation / dollar amounts / personal plan (TRANSFORM)
_ALLOCATION_PATTERNS = [
    r"\ballocat(e|ion)\b", # allocate (e / ion)
    r"\bmy\s+portfolio\b", # my portfolio
    r"\bdiversif(y|ication)\s+my\s+portfolio\b", # diversif(y / ication) my portfolio
    r"\bI\s+have\s+\$?\d", # I have __$
    r"\bwith\s+\$?\d", # With __$
    r"\bhow\s+should\s+i\s+invest\s+\$?\d", # How should I invest __$
    r"\bretirement\s+plan\b", # Retirement plans
    r"\bbuild\s+me\s+(a|an)\s+(portfolio|plan)\b", # Build me (a/an) (portfolio/plan)
]

# Timing requests (TRANSFORM)
_TIMING_PATTERNS = [
    r"\bwhen\s+should\s+i\s+(buy|sell)\b", # When should I (buy / sell)
    r"\btime\s+the\s+market\b", # Time the market
    r"\bshould\s+i\s+sell\s+now\b", # SHould I sell now
]


_TICKER_LIKE = re.compile(r"\b[A-Z]{1,5}\b")  # used only as a safety check in rewrites


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _safe_rewrite_for_advice(original: str) -> str:
    """
    Convert advice-seeking questions into an educational, non-actionable question.
    Must not mention specific assets/tickers or amounts.
    """
    # Generic, safe reframes. Pick based on detected type.
    t = original.strip().lower()

    if _matches_any(_TIMING_PATTERNS, t):
        return (
            "What are the common factors and risks people consider when deciding whether to hold or sell an investment, "
            "and why is market timing difficult in general?"
        )

    if _matches_any(_ALLOCATION_PATTERNS, t):
        return (
            "What are general frameworks people use to think about diversification, time horizon, liquidity needs, "
            "and risk tolerance when building a long-term investment plan (conceptually)?"
        )

    # Default advice-to-education rewrite
    return (
        "What are general frameworks to evaluate investment options based on goals, time horizon, and risk tolerance, "
        "and what tradeoffs typically matter?"
    )


def route(user_text: str) -> PolicyDecision:
    """
    Route a user request according to FinMentor guardrails.
    - ALLOW: educational/general info
    - TRANSFORM: advice-seeking -> rewrite into educational framing
    - REFUSE: illegal/harmful financial wrongdoing
    """
    text = (user_text or "").strip()
    if not text:
        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason=REASON_GENERAL_EDU,
            rewrite=None,
        )

    # 1) REFUSE: illegal/harmful
    if _matches_any(_ILLEGAL_PATTERNS, text):
        return PolicyDecision(
            action=PolicyAction.REFUSE,
            reason=REASON_ILLEGAL_FINANCIAL,
            rewrite=None,
        )

    # 2) TRANSFORM: explicit advice / recommendation / timing / allocation
    if _matches_any(_ADVICE_PATTERNS, text):
        rw = _safe_rewrite_for_advice(text)
        return PolicyDecision(
            action=PolicyAction.TRANSFORM,
            reason=REASON_ASSET_RECOMMENDATION,
            rewrite=_sanitize_rewrite(rw),
        )

    if _matches_any(_ALLOCATION_PATTERNS, text):
        rw = _safe_rewrite_for_advice(text)
        return PolicyDecision(
            action=PolicyAction.TRANSFORM,
            reason=REASON_PORTFOLIO_ALLOCATION,
            rewrite=_sanitize_rewrite(rw),
        )

    if _matches_any(_TIMING_PATTERNS, text):
        rw = _safe_rewrite_for_advice(text)
        return PolicyDecision(
            action=PolicyAction.TRANSFORM,
            reason=REASON_TIMING_REQUEST,
            rewrite=_sanitize_rewrite(rw),
        )

    # 3) Default allow
    return PolicyDecision(
        action=PolicyAction.ALLOW,
        reason=REASON_GENERAL_EDU,
        rewrite=None,
    )


def _sanitize_rewrite(rewrite: str) -> str:
    """
    Final safety scrub: ensure rewrites are not actionable.
    - Remove ticker-like tokens (AAPL, TSLA) if any slip in.
    - Remove dollar amounts.
    """
    out = rewrite

    # Remove $ amounts
    out = re.sub(r"\$?\d[\d,]*(\.\d+)?", "[amount]", out)

    # Remove ticker-like tokens (very conservative)
    out = _TICKER_LIKE.sub("[asset]", out)

    # Avoid buy/sell verbs in rewrites
    out = re.sub(r"\b(buy|sell)\b", "trade", out, flags=re.IGNORECASE)

    return out.strip()
