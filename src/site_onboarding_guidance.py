"""Contextual first-use guidance without behavioral profiling or fabricated claims.

Reader suggestions draw only from actually published content and explicit
editorial interests. Executive Advisory routing maps a named decision need to
an existing service; a suggestion never alters access or approval entitlements.
"""
from __future__ import annotations

import re
from typing import Any

ADVISORY_NEEDS = (
    "Evaluate one AI opportunity",
    "Prioritize several AI initiatives",
    "Decide whether a pilot can scale",
    "Discuss a complex leadership decision",
)

ADVISORY_SERVICES = {
    ADVISORY_NEEDS[0]: {
        "view": "decision",
        "title": "AI Investment Decision Advisor",
        "why": "You are evaluating one AI opportunity rather than comparing a portfolio.",
        "outcome": "A reasoned Invest / Experiment / Hold / Stop position and three priority actions.",
        "approval": False,
    },
    ADVISORY_NEEDS[1]: {
        "view": "scorecard",
        "title": "AI Portfolio Prioritization Scorecard",
        "why": "You need a consistent basis for comparing multiple AI initiatives and competing capacity.",
        "outcome": "A ranked portfolio, evidence gaps and a documented investment discussion.",
        "approval": True,
    },
    ADVISORY_NEEDS[2]: {
        "view": "rollout",
        "title": "Enterprise AI Rollout Readiness Advisor",
        "why": "The central question is whether a pilot can move safely into wider operation.",
        "outcome": "A readiness verdict, scaling conditions and prioritized executive actions.",
        "approval": True,
    },
    ADVISORY_NEEDS[3]: {
        "view": "requests",
        "title": "Private Executive Advisory",
        "why": "Your question needs an individual discussion rather than a fixed assessment.",
        "outcome": "A privately reviewed request and, if selected, an agreed advisory next step.",
        "approval": False,
    },
}

# Specific signals first. Ambiguous business language is not treated as a
# definitive preference: users always see and can change the suggested need.
_NEED_SIGNALS = (
    (ADVISORY_NEEDS[1],
     ("portfolio", "multiple initiatives", "several initiatives", "prioritiz",
      "prioritis", "competing projects", "investment priorities")),
    (ADVISORY_NEEDS[2],
     ("pilot", "rollout", "roll-out", "scale", "scaling", "deployment readiness",
      "adoption readiness")),
    (ADVISORY_NEEDS[3],
     ("operating model", "ownership", "leadership", "culture",
      "organization design", "organisational", "data governance", "stewardship")),
    (ADVISORY_NEEDS[0],
     ("single opportunity", "one ai opportunity", "one use case", "invest",
      "business case", "roi", "opportunity evaluation")),
)


def suggested_decision_need(profile: dict[str, Any] | None) -> tuple[str, str]:
    """Return an editable suggestion and an accurate explanation of its origin."""
    profile = profile if isinstance(profile, dict) else {}
    context = str(profile.get("decision_context") or "").lower()[:1200]
    focus = str(profile.get("advisory_focus") or "").lower()[:120]
    for need, signals in _NEED_SIGNALS:
        if any(signal in context for signal in signals):
            return need, "Based on the decision context saved in your Advisory profile."
    for need, signals in _NEED_SIGNALS:
        if any(signal in focus for signal in signals):
            return need, "Based on the advisory focus saved in your profile."
    return ADVISORY_NEEDS[0], (
        "A practical starting point when you have not yet selected a decision type."
    )


def advisor_for_need(need: str) -> dict[str, Any]:
    """Only return a defined service, with no permission implications."""
    if need not in ADVISORY_SERVICES:
        raise ValueError("Select one of the existing advisory decision needs.")
    return dict(ADVISORY_SERVICES[need])


def _item_text(item: object) -> str:
    return " ".join(
        str(getattr(item, key, "") or "")
        for key in ("title", "category", "subtitle", "excerpt")
    ).casefold()


def _topic_signals(topic: str) -> tuple[str, ...]:
    words = tuple(re.findall(r"[a-z0-9]+", topic.casefold()))
    # Generic words alone such as "ai", "and", "data" or "leadership"
    # are too broad to imply a relevant piece of editorial analysis.
    meaningful = tuple(w for w in words if w not in {
        "ai", "and", "the", "of", "for", "in", "to", "data", "leadership"
    } and len(w) >= 4)
    return meaningful


def select_reader_first_read(
    published: list[object],
    profile: dict[str, Any] | None,
    *,
    requested_slug: str = "",
    selected_topic: str = "",
) -> tuple[object | None, str]:
    """Select from real, published items only; never invent a reading result.

    Priority: user-chosen topic > explicit source edition > saved editorial
    interests > latest published executive briefing. The caller supplies the
    trusted published catalogue in descending chronological order.
    """
    items = [
        x for x in published
        if re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", str(getattr(x, "slug", "") or "")
        )
    ]
    if not items:
        return None, ""
    topic = str(selected_topic or "").strip()
    if topic:
        signals = _topic_signals(topic)
        matches = [
            item for item in items
            if signals and any(s in _item_text(item) for s in signals)
        ]
        if matches:
            return matches[0], "Related to the topic you selected just now."
        # A topic without a real match never produces a false recommendation.
        return None, "No published edition currently matches that topic."

    slug = str(requested_slug or "").strip().lower()
    for item in items:
        if str(getattr(item, "slug", "")) == slug:
            return item, "Continue the publication you selected before opening the library."

    profile = profile if isinstance(profile, dict) else {}
    interests = profile.get("interests")
    if isinstance(interests, (list, tuple)):
        for interest in interests:
            signals = _topic_signals(str(interest))
            if signals:
                for item in items:
                    if any(s in _item_text(item) for s in signals):
                        return item, "Related to an editorial interest you chose in your profile."

    for item in items:
        if str(getattr(item, "kind", "") or "").casefold() == "executive briefing":
            return item, "A recently published executive briefing to begin with."
    return items[0], "A recently published perspective to begin with."
