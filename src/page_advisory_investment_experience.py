"""Executive presentation of a single recorded AI investment assessment.

All claims come from the validated selections and deterministic verdict. This
module never treats optional context text as verified or scoring evidence.
"""
from __future__ import annotations

from page_advisory_investment_logic import assess, validate


DECISION_BOUNDARIES = {
    "INVEST": (
        "Submit for formal investment approval.",
        "Investment readiness is indicated by self-reported evidence. Neither spending nor deployment is authorized by this report.",
    ),
    "EXPERIMENT": (
        "Authorize only a bounded evidence-gathering step, subject to necessary controls.",
        "Do not commit to a full rollout. If controls are pending, limit work to controlled, non-live validation until approval.",
    ),
    "HOLD": (
        "Suspend new investment or live-use commitments.",
        "Resolve the stated blocking prerequisites and return for a decision with documented evidence.",
    ),
    "STOP": (
        "Reject the current AI proposal.",
        "Only a materially different, lawful and economically credible option warrants fresh review.",
    ),
}

KEY_EVIDENCE = (
    ("Business benefit", "value"),
    ("Operating baseline", "baseline"),
    ("Comparison with non-AI", "non_ai"),
    ("Data readiness", "data"),
    ("Control status", "control"),
    ("Business owner", "owner"),
)

BUSINESS_LABELS = (
    ("Intended outcome", "objective"),
    ("Current stage", "stage"),
    ("Authority given to AI", "autonomy"),
    ("Comparison with process alternatives", "non_ai"),
    ("Expected business benefit", "value"),
    ("Existing operating baseline", "baseline"),
)
READINESS_LABELS = (
    ("Data access, ownership and quality", "data"),
    ("Feasibility", "feasibility"),
    ("People and budget", "capacity"),
    ("Accountable business owner", "owner"),
    ("Adoption approach", "adoption"),
)
GOVERNANCE_LABELS = (
    ("Oversight and controls", "control"),
    ("Consequence of incorrect AI output", "exposure"),
    ("Legal and regulatory review", "legal"),
)


def present_assessment(raw: dict) -> dict:
    """Return validated, grounded executive presentation metadata."""
    data = validate(raw)
    result = assess(data)
    verdict = result["verdict"]
    next_step, boundary = DECISION_BOUNDARIES[verdict]
    choices = data["choices"]

    measured = (
        choices["value"] == "Measured against a baseline"
        and choices["baseline"] == "Verified baseline"
    )
    if measured:
        value_statement = "Measured benefit reported; underlying figures were not independently checked."
    elif choices["value"] == "Quantified estimate only":
        value_statement = "Estimated benefit only; actual incremental impact is unproven."
    elif choices["value"] == "Unquantified expectation":
        value_statement = "Benefit not quantified against an operational baseline."
    else:
        value_statement = "No credible incremental benefit reported."

    risk_statement = (
        "Controls recorded as tested." if choices["control"] == "Controls tested and recorded"
        else "Formal control review remains open." if choices["control"] == "Control review pending"
        else "Required controls are absent or ineffective."
    )
    confidence = result["confidence"].replace(" (self-reported)", "")
    facts = [(label, choices[key]) for label, key in KEY_EVIDENCE]
    return {
        "data": data,
        "result": result,
        "name": data["name"],
        "verdict": verdict,
        "confidence": confidence,
        "next_step": next_step,
        "boundary": boundary,
        "why": result["primary_constraint"],
        "value_statement": value_statement,
        "risk_statement": risk_statement,
        "evidence": facts,
        "actions": result["actions"],
        "scope": f"{choices['stage']} · {choices['objective']} · {choices['autonomy']}",
        "review_trigger": result["review_trigger"],
    }


def categorize_evidence(raw: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    data = validate(raw)
    a = data["choices"]
    return [
        ("Business case", [(label, a[key]) for label, key in BUSINESS_LABELS]),
        ("Operational readiness", [(label, a[key]) for label, key in READINESS_LABELS]),
        ("Governance and authority", [(label, a[key]) for label, key in GOVERNANCE_LABELS]),
    ]
