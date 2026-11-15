"""Deterministic leadership-workshop assessment; no external model calls.

All conclusions reflect unverified participant selections. Leadership decisions
and legal, financial or deployment approvals remain with accountable executives.
"""
from __future__ import annotations

MODEL_VERSION = "leadership-workshop-v1"
RESPONSES = (
    "Not established",
    "Planned, not demonstrated",
    "Partially demonstrated",
    "Demonstrated in practice",
)
EVIDENCE = ("Not assessed", "No supporting record", "Documented internally", "Observed in practice")
CONTEXT = {
    "mode": ("individual", "team"),
    "stage": ("Exploring AI", "Pilots underway", "Limited production", "Enterprise adoption"),
    "priority": ("Business value", "Governance & trust", "Adoption & people", "Operational readiness"),
    "timeframe": ("Within 30 days", "Next quarter", "Next 6 months", "Exploratory"),
    "scope": ("One business function", "Several functions", "Enterprise-wide"),
}
# id, question, why, suggested leadership action, accountable function
DIMENSIONS = (
    ("strategy", "Strategy and priorities", 15, (
        ("strategy_priorities", "Are major AI initiatives explicitly tied to business priorities?",
         "Use a named organizational priority rather than a technology ambition.",
         "Agree which enterprise outcomes each priority AI initiative serves.", "Executive sponsor"),
        ("strategy_tradeoffs", "Are investment choices made using consistent criteria?",
         "Look for documented selection and opportunity-cost decisions.",
         "Establish one portfolio decision standard with explicit capacity constraints.", "Portfolio sponsor"),
        ("strategy_stop", "Can leaders stop or redirect low-value AI work?",
         "A working portfolio process changes or ends commitments when evidence changes.",
         "Review low-value initiatives and exercise stop or redirect authority.", "Executive committee"),
    )),
    ("governance", "Governance and risk", 15, (
        ("governance_authority", "Are AI authority limits and decision rights established?",
         "Decision rights include who can approve, restrict, override and halt use.",
         "Define AI use boundaries, human authority and decision ownership.", "Risk / business owner"),
        ("governance_controls", "Are proportionate risk and control reviews completed before live use?",
         "Review legal applicability, privacy, security and the consequence of failure.",
         "Complete necessary specialist reviews before any expanded live exposure.", "Risk / legal owner"),
        ("governance_stop", "Are escalation, intervention and stop responsibilities understood?",
         "Operational governance must work when something goes wrong.",
         "Test incident escalation and stop authority in a realistic scenario.", "Accountable AI owner"),
    )),
    ("accountability", "Leadership accountability", 20, (
        ("accountability_owner", "Does each major initiative have an accountable business owner?",
         "An owner has authority over resources, changed work and the result.",
         "Assign an empowered business owner to each priority AI-enabled process.", "Executive sponsor"),
        ("accountability_rights", "Do business and technology leaders agree who owns the outcome?",
         "Joint involvement must not obscure who accepts business accountability.",
         "Confirm business/technology decision rights and escalation boundaries.", "Business & technology leads"),
        ("accountability_review", "Do executives regularly review realized value and unresolved decisions?",
         "Review what changed in the work, not merely deployments or attendance.",
         "Introduce a leadership review of actual outcomes, constraints and stop decisions.", "Executive committee"),
    )),
    ("data", "Data readiness", 10, (
        ("data_owners", "Are critical data assets owned and available for permitted AI uses?",
         "Access, provenance and lawful purpose matter as much as the dataset existing.",
         "Confirm critical data ownership, purpose and authorized access.", "Data owner"),
        ("data_quality", "Is data quality tested against its intended business use?",
         "A platform score does not replace fitness-for-purpose testing.",
         "Run data quality checks using representative workflow cases.", "Data steward"),
        ("data_remediation", "Are data monitoring and remediation responsibilities established?",
         "Problems need named responders and repeatable correction.",
         "Set data monitoring, incident ownership and remediation triggers.", "Data governance lead"),
    )),
    ("adoption", "Adoption and people", 20, (
        ("adoption_workflow", "Have affected workflows and responsibilities been redesigned?",
         "Adoption means changed work and accountability, not installing a tool.",
         "Redesign the target process with accountable operational owners.", "Process owner"),
        ("adoption_employee", "Are employees involved in testing and challenging the change?",
         "Concerns may expose quality, workload, trust or accountability problems.",
         "Test the future workflow with representative affected employees.", "Operations / people lead"),
        ("adoption_measures", "Do leaders measure sustained use and business outcomes?",
         "Usage and training attendance are not sufficient proof of value.",
         "Define sustained workflow and outcome measures with a baseline.", "Business owner"),
    )),
    ("operations", "Operational readiness", 10, (
        ("operations_capacity", "Are delivery and operating capacities available?",
         "Consider staffing, budget, dependencies and displaced commitments.",
         "Confirm delivery capacity and the work this investment would displace.", "Portfolio / finance owner"),
        ("operations_fallback", "Are support, exception and fallback processes defined?",
         "A credible operating model includes manual alternatives and escalation.",
         "Define incident, support, human review and fallback ownership.", "Operations lead"),
        ("operations_tests", "Have solutions been tested in realistic business conditions?",
         "Demo performance is not operational proof.",
         "Test the service under representative operating and failure conditions.", "Operations / technology lead"),
    )),
    ("value", "Business value", 10, (
        ("value_baseline", "Is there a credible baseline for the intended outcome?",
         "There must be a measurable before state or valid comparator.",
         "Agree and verify the operational baseline before claiming benefit.", "Finance / business owner"),
        ("value_alternative", "Have non-AI alternatives been compared?",
         "Process improvement or simpler automation may solve the problem better.",
         "Compare AI with process improvement and non-AI options.", "Process / finance owner"),
        ("value_realized", "Does a business owner measure value after deployment?",
         "Attribution, run costs, exceptions and actual results should be reviewed.",
         "Review incremental benefits and lifecycle costs with the business owner.", "Business owner"),
    )),
)
QUESTION_INDEX = {q[0]: (key, title, weight, *q[1:])
                  for key, title, weight, questions in DIMENSIONS for q in questions}
CRITICAL = ("governance_controls", "governance_stop", "accountability_owner")

EXERCISES = {
    "pilot": {
        "title": "The pilot works, but employees do not use it",
        "scenario": "A GenAI pilot meets technical targets. Leadership plans a five-function rollout, but employees still follow the old workflow and nobody owns the process change.",
        "choices": (
            "Scale to more users to improve usage",
            "Increase communication and general training",
            "Confirm business ownership, redesign work and test adoption outcomes before expansion",
            "Replace the tool with a more capable model",
        ),
        "preferred": 2,
        "interpretation": "The decision should address ownership and changed work before committing to scale.",
        "tradeoff": "Time to redesign the process versus the risk of paying for unused capability.",
    },
    "priorities": {
        "title": "Every executive has a priority AI initiative",
        "scenario": "Four sponsors want their AI ideas funded. All need the same small delivery team, and no opportunity-cost decision has been taken.",
        "choices": (
            "Fund all projects and ask the team to work faster",
            "Rank proposals by expected benefit, evidence and scarce capacity; explicitly pause some work",
            "Split resources equally between all sponsors",
            "Defer all AI investment until capacity doubles",
        ),
        "preferred": 1,
        "interpretation": "A defensible portfolio decision includes what will not be funded.",
        "tradeoff": "Stakeholder preferences versus enterprise-level opportunity cost.",
    },
    "governance": {
        "title": "A policy exists, but nobody can stop a harmful use",
        "scenario": "A business-critical AI system has a governance policy and review committee. A serious operational exception occurs and no one can authorize immediate suspension.",
        "choices": (
            "Wait for the next committee meeting",
            "Ask the technical vendor to decide",
            "Continue operating until legal guidance is final",
            "Invoke proportionate containment, assign stop authority and document specialist review",
        ),
        "preferred": 3,
        "interpretation": "Effective governance includes operational authority to intervene and escalate.",
        "tradeoff": "Continuity of service versus a controlled and accountable stop.",
    },
    "resistance": {
        "title": "Are people resistant, or telling us something?",
        "scenario": "Employees question an AI rollout because of inconsistent answers, increased checking work and uncertainty about who is accountable for errors.",
        "choices": (
            "Label the issue as resistance and mandate adoption",
            "Separate reliability, workload, trust and ownership concerns; redesign the workflow with users",
            "Introduce an incentive for higher login counts",
            "Ignore the concerns until the next model version",
        ),
        "preferred": 1,
        "interpretation": "Employee concerns may be evidence of a genuine operating-model problem.",
        "tradeoff": "Rapid deployment versus trust, workload and service quality.",
    },
}
SCENARIO_FOR = {
    "strategy": "priorities", "value": "priorities",
    "governance": "governance", "accountability": "governance",
    "adoption": "resistance", "data": "pilot", "operations": "pilot",
}


def clean_answers(raw: dict | None) -> dict[str, int | None]:
    if not isinstance(raw, dict):
        raise ValueError("Assessment answers must be a structured object.")
    if set(raw) - set(QUESTION_INDEX):
        raise ValueError("Unexpected assessment field.")
    result = {}
    for key, value in raw.items():
        if value is not None and (type(value) is not int or value not in range(4)):
            raise ValueError("Unsupported assessment answer.")
        result[key] = value
    return result


def clean_exercises(raw: dict | None) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise ValueError("Exercise answers must be a structured object.")
    if set(raw) - set(EXERCISES):
        raise ValueError("Unexpected exercise.")
    for key, value in raw.items():
        if type(value) is not int or value not in range(len(EXERCISES[key]["choices"])):
            raise ValueError("Unsupported exercise choice.")
    return dict(raw)


def assess(raw: dict | None) -> dict:
    answers = clean_answers(raw or {})
    scores: dict[str, float | None] = {}
    counts: dict[str, int] = {}
    gaps = []
    for key, title, weight, questions in DIMENSIONS:
        rated = [answers[q[0]] for q in questions if answers.get(q[0]) is not None]
        counts[key] = len(rated)
        scores[key] = round(sum(rated) / (3 * len(rated)) * 100) if rated else None
        for q in questions:
            if answers.get(q[0]) is not None and answers[q[0]] < 2:
                gaps.append((answers[q[0]], -weight, key, q))
    answered = sum(counts.values())
    coverage = round(100 * answered / len(QUESTION_INDEX))
    gates = [QUESTION_INDEX[key][3] for key in CRITICAL if answers.get(key) in (0, 1)]
    complete = answered == len(QUESTION_INDEX)
    enough = answered >= 18 and all(counts[k] >= 2 for k, _, _, _ in DIMENSIONS)
    overall = None
    if enough:
        overall = round(sum((scores[k] or 0) * weight for k, _, weight, _ in DIMENSIONS) / 100)
    if not enough:
        label = "EVIDENCE INCOMPLETE"
        reason = "The responses do not yet cover enough of the leadership conditions for a defensible overall assessment."
    elif gates:
        label = "LEADERSHIP RESET REQUIRED"
        reason = "A critical leadership ownership or control condition overrides the overall readiness score."
    elif overall is not None and overall >= 75 and all((scores[k] or 0) >= 60 for k, _, _, _ in DIMENSIONS):
        label = "FOUNDATIONS ESTABLISHED"
        reason = "Reported conditions indicate a generally functioning leadership approach, subject to verification and formal decisions."
    elif overall is not None and overall < 50:
        label = "LEADERSHIP RESET REQUIRED"
        reason = "Material weaknesses suggest that organizational leadership conditions need redesign before wider commitment."
    else:
        label = "TARGETED CHANGES REQUIRED"
        reason = "The reported foundation is uneven; specific ownership, adoption or control gaps require leadership attention."
    prioritized = sorted(gaps, key=lambda x: (x[0], x[1], x[2]))
    actions = []
    for _, _, key, q in prioritized:
        if len(actions) >= 3:
            break
        if any(a["dimension"] == key for a in actions):
            continue
        actions.append({"dimension": key, "question": q[1], "action": q[3],
                        "owner": q[4], "evidence": q[2],
                        "review": "At the next accountable leadership review"})
    if not actions:
        actions = [{"dimension": "leadership", "question": "Evidence review",
                    "action": "Verify the reported evidence and confirm the next leadership review.",
                    "owner": "Executive sponsor", "evidence": "Accepted decision record",
                    "review": "Next executive review"}]
    weakest = sorted(((scores[k] if scores[k] is not None else -1, k)
                      for k, _, _, _ in DIMENSIONS), key=lambda x: x[0])
    scenarios = []
    for _, key in weakest:
        scenario = SCENARIO_FOR[key]
        if scenario not in scenarios:
            scenarios.append(scenario)
        if len(scenarios) == 2:
            break
    return {
        "model_version": MODEL_VERSION, "coverage": coverage, "answered": answered,
        "complete": complete, "enough_evidence": enough, "overall": overall,
        "label": label, "reason": reason, "scores": scores, "counts": counts,
        "critical_gates": gates, "actions": actions[:3], "scenarios": scenarios,
        "confidence": "Self-reported; supporting evidence has not been independently reviewed",
    }


def interpret_exercise(scenario: str, choice: int) -> dict:
    if scenario not in EXERCISES or type(choice) is not int or choice not in range(4):
        raise ValueError("Invalid scenario response")
    item = EXERCISES[scenario]
    return {"preferred": choice == item["preferred"],
            "message": item["interpretation"],
            "tradeoff": item["tradeoff"],
            "selection": item["choices"][choice]}


def aggregate_team(answer_sets: list[dict], *, minimum: int = 3) -> dict:
    """Aggregate opted-in responses only; never describe them as anonymous."""
    if len(answer_sets) < minimum:
        return {"available": False, "count": len(answer_sets),
                "reason": f"At least {minimum} explicitly shared responses are needed."}
    cleaned = [clean_answers(raw) for raw in answer_sets]
    dimensions = {}
    for key, title, _, questions in DIMENSIONS:
        vals = [round(sum(raw[q[0]] for q in questions) / 9 * 100)
                for raw in cleaned if all(type(raw.get(q[0])) is int for q in questions)]
        dimensions[key] = {"responses": len(vals),
                           "average": round(sum(vals) / len(vals)) if vals else None,
                           "spread": max(vals) - min(vals) if len(vals) >= minimum else None}
    return {"available": True, "count": len(answer_sets), "dimensions": dimensions,
            "note": "Aggregated from expressly shared, self-reported responses. Small teams may still permit inference; this is not anonymous."}
