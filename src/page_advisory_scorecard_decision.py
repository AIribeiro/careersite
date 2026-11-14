"""Deterministic, transparent executive portfolio decision engine.

No AI-generated facts, no automatic investment approval. A prioritization
recommendation is a proposal to perform business-case or scoped-test work.
For up to 17 candidates selection is exhaustive; otherwise a bounded beam
search supplies a labelled heuristic result in reasonable interactive time.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any


def _number(value: Any) -> float:
    try:
        num = float(value)
        return num if isfinite(num) and num >= 0 else 0.0
    except (ValueError, TypeError, OverflowError):
        return 0.0


def assess(row: dict, settings: dict) -> tuple[int | None, str]:
    """Same seven-dimension model and hard gates as the original Scorecard."""
    scores = row.get("scores") or []
    if not str(row.get("name") or "").strip():
        return None, "NAME REQUIRED"
    if not str(row.get("owner") or "").strip():
        return None, "OWNER REQUIRED"
    if len(scores) != 7 or any(type(v) is not int or v < 1 or v > 5 for v in scores):
        return None, "NOT SCORED"
    weights = settings.get("weights") or [15, 20, 15, 15, 15, 10, 10]
    score = int(sum(a * b for a, b in zip(scores, weights)) / 5 + 0.5)
    if row.get("evidence") in ("Not assessed", None, ""):
        return score, "EVIDENCE NEEDED"
    if row.get("gate") == "Block":
        return score, "STOP / REDESIGN"
    if row.get("gate") != "Pass":
        return score, "CONTROL REVIEW"
    if row.get("evidence") == "Low":
        return score, "VALIDATE EVIDENCE"
    if score >= float(settings.get("advance", 78)):
        return score, "ADVANCE TO CASE"
    if score >= float(settings.get("test", 62)):
        return score, "TEST / PROVE"
    return score, "DEFER / STOP"


def _weighted_strength(candidate: dict) -> float:
    # High-confidence evidence modestly breaks score ties. Estimated monetary
    # benefits are displayed but do not drive the primary recommendation.
    return float(candidate["score"]) + (2.0 if candidate["evidence"] == "High" else 0.0)


def _choose(items: list[dict], available_fte: float, available_sek: float,
            max_items: int | None = None) -> tuple[list[dict], str]:
    """Select strongest feasible subset; tie-break on leaner commitments.

    Estimates are treated as simultaneous planning constraints, not approved
    allocations. Never select unknown (zero) demand estimates as free work.
    """
    if not items or available_fte <= 0 or available_sek <= 0 or max_items == 0:
        return [], "exact"
    ordered = sorted(items, key=lambda r: (
        -_weighted_strength(r),
        r["investment_sek"], r["fte_months"], r["id"],
    ))
    if len(ordered) <= 17:
        best_indices: tuple[int, ...] = ()
        best_key: tuple = (0.0, 0, 0.0, 0.0, ())
        # Size <= 17, so exhaustive is bounded by 131,072 subsets.
        for mask in range(1, 1 << len(ordered)):
            if max_items is not None and mask.bit_count() > max_items:
                continue
            fte = investment = priority = 0.0
            chosen = []
            for idx, item in enumerate(ordered):
                if mask & (1 << idx):
                    fte += item["fte_months"]
                    investment += item["investment_sek"]
                    if fte > available_fte + 1e-7 or investment > available_sek + 1e-5:
                        break
                    priority += _weighted_strength(item)
                    chosen.append(idx)
            else:
                key = (
                    round(priority, 6), len(chosen), -round(investment, 2),
                    -round(fte, 4), tuple(-i for i in chosen),
                )
                if key > best_key:
                    best_key, best_indices = key, tuple(chosen)
        return [ordered[i] for i in best_indices], "exact"

    # 30 candidates can imply 2**30 subsets; bound work to avoid freezing the
    # client page. This is a heuristic; do not assert globally optimal.
    states: list[tuple[float, float, float, tuple[int, ...]]] = [(0, 0, 0, ())]
    for i, item in enumerate(ordered):
        extended = list(states)
        for value, fte, sek, indices in states:
            if max_items is not None and len(indices) >= max_items:
                continue
            nf, ns = fte + item["fte_months"], sek + item["investment_sek"]
            if nf <= available_fte + 1e-7 and ns <= available_sek + 1e-5:
                extended.append((value + _weighted_strength(item), nf, ns, indices + (i,)))
        extended.sort(key=lambda x: (
            -round(x[0], 6), -len(x[3]), x[2], x[1], x[3],
        ))
        states = extended[:3000]
    winner = states[0][3]
    return [ordered[i] for i in winner], "heuristic"


def _summary(selected: list[dict], settings: dict) -> dict:
    fte = sum(x["fte_months"] for x in selected)
    investment = sum(x["investment_sek"] for x in selected)
    annual = sum(x["annual_net_sek"] for x in selected)
    return {
        "count": len(selected),
        "fte_months": round(fte, 3),
        "investment_sek": round(investment, 2),
        "annual_net_sek": round(annual, 2),
        "fte_headroom": round(_number(settings.get("capacity_fte_months")) - fte, 3),
        "budget_headroom": round(_number(settings.get("budget_sek")) - investment, 2),
        "fits": fte <= _number(settings.get("capacity_fte_months")) + 1e-7
                and investment <= _number(settings.get("budget_sek")) + 1e-5,
    }


def _explanation(record: dict, status: str, *, constrained: bool = False) -> tuple[str, str]:
    score = record["score"]
    evidence = record["evidence"]
    gate = record["gate"]
    proof = str(record.get("next_proof") or "").strip()
    if status == "Advance to business case":
        reason = (f"Score {score}/100, {evidence.lower()} evidence and passed control gate; "
                  "included within both planning limits.")
        action = proof or "Confirm accountable sponsor, quantified baseline and approval conditions."
    elif status == "Time-boxed test":
        reason = (f"Score {score}/100 supports a limited evidence-building test, "
                  "not immediate scale or full investment approval.")
        action = proof or "Define test scope, success criteria and a new go/no-go decision."
    elif status == "Hold - control review":
        reason = (f"Control gate is {gate.lower()}; a score of {score}/100 cannot "
                  "override outstanding review.")
        action = proof or "Complete mandatory risk, legal and operating control review."
    elif status == "Stop / redesign":
        reason = "Blocked control gate takes precedence over value and priority scores."
        action = proof or "Do not proceed until an authorized review changes the gate."
    elif status == "Validate evidence":
        reason = "Low or missing evidence confidence prevents a defensible commitment."
        action = proof or "Build the business baseline and verify key assumptions."
    elif status == "Defer - constrained":
        reason = ("Eligible on current evidence, but the constrained portfolio "
                  "favors other candidates under limited money and delivery capacity.")
        action = "Reconsider when resource capacity changes or a higher priority is removed."
    elif status == "Queue for a test":
        reason = ("Eligible for a scoped test but was not chosen within the remaining "
                  "planning envelope and test allocation.")
        action = proof or "Revisit after higher-priority evidence and capacity decisions."
    elif status == "Complete assessment":
        reason = "A named business owner, seven complete scores and credible resource estimates are required."
        action = "Complete missing input and confirm evidence and estimated demand."
    else:
        reason = f"Score {score}/100 is below the configured test threshold."
        action = proof or "Defer until the business need or supporting evidence changes."
    return reason, action


def recommend(payload: dict, *, revision: int | None = None,
              generated_at: str | None = None) -> dict:
    """Build a reviewable decision from existing user inputs; mutate nothing."""
    settings = dict(payload.get("settings") or {})
    settings.setdefault("weights", [15,20,15,15,15,10,10])
    settings.setdefault("advance", 78)
    settings.setdefault("test", 62)
    settings.setdefault("capacity_fte_months", 12.0)
    settings.setdefault("budget_sek", 1200000.0)
    try:
        max_tests = max(0, min(int(settings.get("max_tests", 1)), 5))
    except (ValueError, TypeError):
        max_tests = 1

    records: list[dict] = []
    for index, item in enumerate(payload.get("initiatives") or []):
        if not isinstance(item, dict):
            continue
        score, action = assess(item, settings)
        fte = _number(item.get("fte_months"))
        investment = _number(item.get("investment_sek"))
        eligible = action in ("ADVANCE TO CASE", "TEST / PROVE")
        ready = eligible and fte > 0 and investment > 0
        records.append({
            "id": str(item.get("id") or f"item-{index}"),
            "name": str(item.get("name") or "Untitled"),
            "sponsor": str(item.get("sponsor") or ""),
            "owner": str(item.get("owner") or ""),
            "score": score,
            "action": action,
            "stage": str(item.get("stage") or ""),
            "evidence": str(item.get("evidence") or ""),
            "gate": str(item.get("gate") or "Not checked"),
            "fte_months": fte,
            "investment_sek": investment,
            "annual_net_sek": _number(item.get("gross_benefit_sek")) - _number(item.get("run_cost_sek")),
            "ready": ready,
            "resource_estimate_missing": eligible and not ready,
            "selected_by_client": bool(item.get("selected")),
            "sponsor_signed": bool(item.get("sponsor_signed")),
            "capacity_signed": bool(item.get("capacity_signed")),
            "next_proof": str(item.get("next_proof") or "")[:1100],
            "evidence_ref": str(item.get("evidence_ref") or "")[:400],
        })
    advances = [r for r in records if r["ready"] and r["action"] == "ADVANCE TO CASE"]
    tests = [r for r in records if r["ready"] and r["action"] == "TEST / PROVE"]
    cap = _number(settings.get("capacity_fte_months"))
    budget = _number(settings.get("budget_sek"))
    picked_advances, method_a = _choose(advances, cap, budget)
    used = _summary(picked_advances, settings)
    picked_tests, method_b = _choose(
        tests, max(0.0, used["fte_headroom"]),
        max(0.0, used["budget_headroom"]), max_tests,
    )
    chosen = picked_advances + picked_tests
    chosen_ids = {r["id"] for r in chosen}
    advance_ids = {r["id"] for r in picked_advances}
    test_ids = {r["id"] for r in picked_tests}
    conservative = _summary(picked_advances, settings)
    proposed = _summary([r for r in records if r["selected_by_client"]], settings)
    recommended = _summary(chosen, settings)
    outcomes = []
    for r in records:
        if r["id"] in advance_ids:
            status = "Advance to business case"
        elif r["id"] in test_ids:
            status = "Time-boxed test"
        elif r["gate"] == "Block":
            status = "Stop / redesign"
        elif r["gate"] != "Pass" and r["score"] is not None:
            status = "Hold - control review"
        elif r["resource_estimate_missing"]:
            status = "Complete assessment"
        elif r["action"] in ("EVIDENCE NEEDED", "VALIDATE EVIDENCE"):
            status = "Validate evidence"
        elif r["action"] == "ADVANCE TO CASE":
            status = "Defer - constrained"
        elif r["action"] == "TEST / PROVE":
            status = "Queue for a test"
        elif r["action"] in ("NAME REQUIRED", "OWNER REQUIRED", "NOT SCORED"):
            status = "Complete assessment"
        else:
            status = "Defer / stop"
        reason, next_action = _explanation(r, status)
        outcomes.append({
            **r, "recommendation": status, "rationale": reason, "next_action": next_action,
            "included_in_proposal": r["id"] in chosen_ids,
        })
    categories: dict[str, list[dict]] = {}
    for item in outcomes:
        categories.setdefault(item["recommendation"], []).append(item)
    for items in categories.values():
        items.sort(key=lambda x: (-(x["score"] or 0), x["name"].casefold()))
    deltas = {
        "added": [r["name"] for r in outcomes if r["included_in_proposal"] and not r["selected_by_client"]],
        "removed": [r["name"] for r in outcomes if r["selected_by_client"] and not r["included_in_proposal"]],
    }
    caveats = []
    if not records:
        caveats.append("No initiatives have been assessed. The recommendation cannot yet be generated.")
    if not chosen:
        caveats.append("No qualifying initiative fits the current evidence, controls and resource limits.")
    if any(x["resource_estimate_missing"] for x in records):
        caveats.append("Some candidates lack positive resource estimates and were excluded from selection.")
    if not recommended["fits"]:
        caveats.append("Selected proposal exceeds configured planning limits; no approval should follow.")
    if any(not x["sponsor_signed"] or not x["capacity_signed"] for x in chosen):
        caveats.append("Sponsor and/or capacity confirmations are outstanding.")
    if method_a == "heuristic" or method_b == "heuristic":
        caveats.append("The constrained selection uses a bounded heuristic rather than an exhaustive search.")
    if cap == 12.0 and budget == 1200000.0:
        caveats.append("Budget and capacity match template defaults; confirm real limits before acting.")
    if any("DEMO" in x["name"].upper() for x in records):
        caveats.insert(0, "DEMONSTRATION ONLY: one or more initiatives contain fictional test data.")
    if chosen:
        advances_n = len(picked_advances)
        tests_n = len(picked_tests)
        verdict = (
            f"Advance {advances_n} initiative{'s' if advances_n != 1 else ''} "
            f"to business-case review"
            + (f"; scope {tests_n} evidence-building test{'s' if tests_n != 1 else ''}" if tests_n else "")
            + ". Do not treat the proposal as funding or deployment approval."
        )
    else:
        verdict = "Hold portfolio approval until evidence, controls and planning constraints support a feasible option."
    return {
        "generated_at": generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "revision": revision,
        "settings": settings,
        "selection_method": "exhaustive" if method_a == method_b == "exact" else "bounded heuristic",
        "verdict": verdict,
        "rows": outcomes,
        "categories": categories,
        "recommended": recommended,
        "current_selection": proposed,
        "conservative": conservative,
        "advanced_count": len(picked_advances),
        "test_count": len(picked_tests),
        "changes": deltas,
        "caveats": caveats,
    }
