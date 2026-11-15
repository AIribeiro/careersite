"""Deterministic, explainable one-opportunity AI investment advisory rules.

No remote LLM, implicit scoring, or invented facts: the output is a
conditional interpretation of the user's selections and explicit caveats.
"""
from __future__ import annotations

MODEL_VERSION = "investment-decision-v1"

FIELDS = {
    "objective": ("Reduce operating cost", "Improve quality or service",
                  "Increase revenue", "Manage business risk", "Improve employee work"),
    "stage": ("Concept", "Discovery", "Pilot", "Limited production"),
    "autonomy": ("Assists a person", "Recommends a decision",
                 "Executes actions with review", "Acts autonomously"),
    "non_ai": ("Compared; AI has a documented advantage",
               "Compared; non-AI alternative is stronger",
               "Not compared"),
    "value": ("Measured against a baseline", "Quantified estimate only",
              "Unquantified expectation", "No credible benefit"),
    "baseline": ("Verified baseline", "Partial baseline", "No baseline"),
    "data": ("Access, ownership and quality verified", "Known remediable gaps",
             "Not assessed", "No lawful or reliable access"),
    "feasibility": ("Demonstrated in relevant setting", "Plausible; untested dependencies",
                    "Critical dependencies unresolved"),
    "capacity": ("People and budget explicitly available",
                 "Capacity competing with other priorities", "No realistic capacity"),
    "owner": ("Named accountable business owner", "Sponsor proposed; ownership pending",
              "No accountable owner"),
    "adoption": ("Workflow and measures validated", "Adoption plan drafted",
                 "No adoption plan"),
    "control": ("Controls tested and recorded", "Control review pending",
                "Controls absent or ineffective"),
    "exposure": ("Limited internal consequence", "Material operational consequence",
                 "High impact on people, rights or safety"),
    "legal": ("Applicable obligations reviewed", "Specialist review outstanding",
              "Known prohibition or unmitigable breach"),
}
DEFAULTS = {k: None for k in FIELDS}
REQUIRED = tuple(FIELDS)
OPTIONAL_CONTEXT_LIMIT = 500

def validate(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Assessment must be a structured record.")
    name = str(raw.get("name") or "").strip()
    if not 5 <= len(name) <= 120:
        raise ValueError("Provide a short, non-confidential use-case name (5–120 characters).")
    context = str(raw.get("context") or "").strip()
    if len(context) > OPTIONAL_CONTEXT_LIMIT:
        raise ValueError("Shorten the optional context to 500 characters.")
    values = raw.get("choices")
    if not isinstance(values, dict):
        raise ValueError("Complete the decision selections.")
    missing = [k for k in REQUIRED if values.get(k) not in FIELDS[k]]
    if missing:
        raise ValueError("Complete all decision questions before requesting a recommendation.")
    return {"name": name, "context": context,
            "choices": {k: values[k] for k in REQUIRED}}

def assess(raw: dict) -> dict:
    data = validate(raw)
    a = data["choices"]
    blocks = []
    uncertainties = []
    strengths = []
    actions = []
    outcome_metric = {
        "Reduce operating cost": "cost per case, hours saved and rework",
        "Improve quality or service": "error rate, first-time resolution and service quality",
        "Increase revenue": "incremental conversion, revenue and attributable margin",
        "Manage business risk": "risk exposure, incidents and control exceptions",
        "Improve employee work": "time on task, workload and employee experience",
    }[a["objective"]]
    early_stage = a["stage"] in ("Concept", "Discovery")

    def task(text: str, owner: str, trigger: str) -> None:
        if text not in [x["text"] for x in actions]:
            actions.append({"text": text, "owner": owner, "trigger": trigger})

    if a["legal"] == FIELDS["legal"][2]:
        blocks.append("A known legal prohibition or unmitigable compliance issue has been reported.")
        task("Reject the current design and obtain an independent legal assessment before any redesign.",
             "Legal / risk owner", "A permitted alternative and its safeguards are documented.")
    elif a["legal"] == FIELDS["legal"][1]:
        uncertainties.append("Applicable legal and regulatory obligations have not been reviewed.")
        task("Complete the applicable legal, privacy and regulatory review.", "Legal / risk owner",
             "Documented specialist opinion and agreed controls.")

    if a["non_ai"] == FIELDS["non_ai"][1]:
        blocks.append("The non-AI alternative is reported as stronger for this business problem.")
        task("Compare the non-AI process option with the proposed AI use on common cost and quality measures.",
             "Business sponsor", "Evidence of a materially better AI outcome, if any.")
    elif a["non_ai"] == FIELDS["non_ai"][2]:
        uncertainties.append("A credible non-AI or process-improvement alternative has not been compared.")
        task("Compare simpler process changes with the AI proposal before making a funding commitment.",
             "Business owner", "A documented alternative assessment.")

    if a["data"] == FIELDS["data"][3]:
        blocks.append("Required data cannot presently be used lawfully or reliably.")
        task("Stop work using the affected data and resolve access, permission and quality constraints.",
             "Data / privacy owner", "Verified lawful access and fit-for-purpose data.")
    elif a["data"] in (FIELDS["data"][1], FIELDS["data"][2]):
        uncertainties.append("Data access, ownership or quality has unresolved gaps.")
        task("Validate data rights, ownership and quality using a bounded representative sample.",
             "Data owner", "Signed-off access and data quality findings.")

    high_impact = a["exposure"] == FIELDS["exposure"][2]
    autonomous = a["autonomy"] in FIELDS["autonomy"][2:]
    if a["control"] == FIELDS["control"][2]:
        uncertainties.append("Controls or oversight are absent or ineffective.")
        task("Define authorization limits, human escalation, logging and exception handling.",
             "Risk / system owner", "Controls verified by accountable specialists.")
    elif a["control"] == FIELDS["control"][1]:
        uncertainties.append("Control review and oversight evidence are incomplete.")
        task("Review human oversight, access, monitoring and incident response before live exposure.",
             "Risk / system owner", "Documented control acceptance.")
    if high_impact or autonomous:
        if a["control"] != FIELDS["control"][0] or a["legal"] != FIELDS["legal"][0]:
            uncertainties.append("The proposed autonomy or impact demands proven oversight and specialist review.")
        if high_impact:
            task("Complete an impact and rights assessment appropriate to the proposed use.",
                 "Accountable risk owner", "Independent review and documented authorization.")

    if a["owner"] == FIELDS["owner"][2]:
        uncertainties.append("No business owner is accountable for the outcome.")
        task("Nominate a business owner with authority over the affected process.",
             "Executive sponsor", "Named owner and decision rights confirmed.")
    elif a["owner"] == FIELDS["owner"][1]:
        uncertainties.append("Business accountability has been proposed but not confirmed.")
        task("Confirm accountable ownership and the operational success measures.",
             "Executive sponsor", "Owner accepts the mandate.")

    if a["value"] == FIELDS["value"][3]:
        uncertainties.append("No credible incremental business benefit has been established.")
        task("Reframe the problem, define the measurable outcome and compare the cost of alternatives.",
             "Finance / business owner", "A credible positive value case.")
    elif a["value"] != FIELDS["value"][0] or a["baseline"] != FIELDS["baseline"][0]:
        uncertainties.append("Value has not been demonstrated against a verified baseline.")
        task("Define and test the relevant outcome measures (" + outcome_metric + ") against an agreed baseline.",
             "Finance / process owner", "Observed outcome and documented benefit assumptions.")
    else:
        strengths.append("The value claim is supported by a measured baseline.")

    if early_stage:
        uncertainties.append("The opportunity is still at concept or discovery stage; operational performance has not been established at scale.")
        task("Conduct a limited evidence-gathering test before proposing a full investment commitment.",
             "Business / delivery owner", "Results from a bounded, controlled test.")

    if a["feasibility"] != FIELDS["feasibility"][0]:
        uncertainties.append("Delivery or operational dependencies remain unproven.")
        task("Test the critical technical and workflow dependencies on a bounded use case.",
             "Delivery / process owner", "Representative technical and operational results.")
    else:
        strengths.append("Feasibility has been demonstrated in a relevant environment.")

    if a["capacity"] == FIELDS["capacity"][2]:
        uncertainties.append("No realistic delivery or operating capacity is available.")
        task("Reassess scarce capacity, funding and the work that would be displaced.",
             "Portfolio sponsor", "A capacity and opportunity-cost decision.")
    elif a["capacity"] == FIELDS["capacity"][1]:
        uncertainties.append("The work competes for scarce delivery capacity.")
        task("Confirm capacity, investment ceiling and opportunity cost against the portfolio.",
             "Portfolio / finance owner", "Approved resource envelope.")

    if a["adoption"] == FIELDS["adoption"][2]:
        uncertainties.append("There is no credible plan for changed work or adoption.")
        task("Define the future workflow, human responsibilities and adoption measures.",
             "Business process owner", "Agreed operating design and adoption measures.")
    elif a["adoption"] == FIELDS["adoption"][1]:
        uncertainties.append("The future operating workflow has not been validated.")

    stop = bool(blocks)
    hold = (
        a["owner"] == FIELDS["owner"][2]
        or a["capacity"] == FIELDS["capacity"][2]
        or a["data"] in (FIELDS["data"][2], FIELDS["data"][3])
        or a["control"] == FIELDS["control"][2]
        or (high_impact and (a["legal"] != FIELDS["legal"][0] or a["control"] != FIELDS["control"][0]))
        or (autonomous and a["control"] != FIELDS["control"][0])
        or (a["value"] == FIELDS["value"][3])
    )
    demonstrated = all((
        a["value"] == FIELDS["value"][0], a["baseline"] == FIELDS["baseline"][0],
        a["data"] == FIELDS["data"][0], a["feasibility"] == FIELDS["feasibility"][0],
        a["capacity"] == FIELDS["capacity"][0], a["owner"] == FIELDS["owner"][0],
        a["adoption"] == FIELDS["adoption"][0], a["control"] == FIELDS["control"][0],
        a["legal"] == FIELDS["legal"][0], a["non_ai"] == FIELDS["non_ai"][0],
    ))
    if stop:
        label,headline = "STOP", "Do not proceed with the current proposal."
        reason = "The current option has a fundamental value, permission or comparative-case problem."
    elif hold:
        label,headline = "HOLD", "Resolve the critical prerequisites before committing."
        reason = "A material ownership, capacity, data, evidence or control condition prevents a defensible commitment."
    elif demonstrated and not early_stage:
        label,headline = "INVEST", "Advance to formal investment approval."
        reason = "Self-reported evidence supports the case across value, feasibility, ownership, capacity and controls."
    else:
        label,headline = "EXPERIMENT", "Test the remaining assumptions within defined limits."
        reason = "The opportunity may have merit, but the business case or operating readiness is not yet sufficiently demonstrated."

    if not actions:
        task("Complete an independent business and risk review before approving funds or deployment.",
             "Executive sponsor", "Required decision authorities have signed off.")
        task("Set operating metrics and release criteria for a phased commitment.",
             "Business owner", "Measurement and accountable review agreed.")
    if len(actions) < 3:
        task("Define the next executive review date and the evidence needed to change this decision.",
             "Executive sponsor", "A documented decision gate.")
    if len(actions) < 3:
        task("Capture the assumptions, owners and agreed boundaries in the decision record.",
             "Business owner", "Decision record accepted by the sponsor.")

    evidence_count = sum((
        a["value"] == FIELDS["value"][0],
        a["baseline"] == FIELDS["baseline"][0],
        a["data"] == FIELDS["data"][0],
        a["feasibility"] == FIELDS["feasibility"][0],
        a["owner"] == FIELDS["owner"][0],
        a["control"] == FIELDS["control"][0],
        a["legal"] == FIELDS["legal"][0],
    ))
    confidence = ("Higher (self-reported)" if evidence_count >= 6 and not blocks
                  else "Moderate (self-reported)" if evidence_count >= 3 and not blocks
                  else "Limited (self-reported)")
    return {
        "model_version": MODEL_VERSION, "verdict": label, "headline": headline,
        "decision_lens": outcome_metric, "stage": a["stage"],
        "reason": reason, "confidence": confidence,
        "primary_constraint": (blocks + uncertainties + ["No major weakness reported."])[0],
        "strengths": strengths[:3], "constraints": (blocks + uncertainties)[:6],
        "actions": actions[:3],
        "release_condition": (
            "A new decision requires documented evidence, named owners, verified controls "
            "and the relevant investment or deployment authorization."
        ),
        "review_trigger": (actions[0]["trigger"] if actions else "Next executive gate."),
    }
