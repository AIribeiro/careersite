"""AI Portfolio Renewal Challenge — deterministic, reviewable prospective decision rules.

Management decision aid, not a financial forecast, approval or risk certification.
The first pass excludes switching costs; the second includes them and human gates.
Past expenditure is deliberately absent from the financial model.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from math import isfinite

MODEL_VERSION = "renewal-v1.0.0"
ACTIONS = ("RENEW", "REPLACE", "TEST", "STOP", "HOLD", "COMPLETE INPUTS")
EVIDENCE = ("hypothesis", "pilot", "operational")
READINESS = ("not_ready", "partial", "ready")
CONTROLS = ("blocked", "mitigate", "clear")
ROUTES = ("another_ai", "smaller_ai", "process_redesign", "existing_system", "bounded_experiment", "release_resources")
STAGES = ("discovery", "pilot", "delivery", "operational", "scaling")
REQUIRED_CONTEXT = ("name", "function", "outcome", "baseline", "stage", "owner",
                    "authority", "currency", "horizon_months", "next_commitment")
REQUIRED_OPTION = ("name", "benefit", "remaining_cost", "specialist_days",
                   "evidence", "adoption", "operations", "data", "controls",
                   "operating_owner", "mandatory_meets")
NUMERIC_OPTION = ("benefit", "remaining_cost", "specialist_days", "transition_cost")
SCENARIO_VARIABLES = {
    "incumbent.benefit", "incumbent.remaining_cost", "incumbent.specialist_days",
    "alternative.benefit", "alternative.remaining_cost", "alternative.specialist_days",
    "alternative.transition_cost", "alternative.evidence", "alternative.adoption",
    "alternative.operations", "alternative.controls", "alternative.mandatory_meets",
    "context.opportunity_cost_day", "context.mandatory_obligation",
}
DEFAULT_MATERIALITY = 0.10  # editorial management default, not empirically calibrated


def _number(value: object, label: str, errors: list[str]) -> float:
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        errors.append(f"{label}: enter an amount covering the common horizon.")
        return 0.0
    try:
        v = float(value)
    except (ValueError, TypeError):
        errors.append(f"{label}: must be a finite numeric amount.")
        return 0.0
    if not isfinite(v) or v < 0 or v > 1e15:
        errors.append(f"{label}: must be between zero and 10^15.")
        return 0.0
    return v


def validate(raw: dict) -> tuple[dict, list[str]]:
    """Return normalized inputs and actionable errors; do not guess missing values."""
    if not isinstance(raw, dict):
        return {}, ["An assessment must contain context and both options."]
    data = deepcopy(raw)
    context = data.get("context")
    incumbent = data.get("incumbent")
    alternative = data.get("alternative")
    errors: list[str] = []
    if not all(isinstance(x, dict) for x in (context, incumbent, alternative)):
        return data, ["Context, incumbent and alternative are all required."]
    for field in REQUIRED_CONTEXT:
        if context.get(field) is None or str(context.get(field)).strip() == "":
            errors.append(f"Context: {field.replace('_',' ')} is required.")
    if context.get("stage") not in STAGES:
        errors.append("Select the incumbent lifecycle stage.")
    if context.get("currency") not in ("SEK", "EUR", "USD", "GBP", "BRL"):
        errors.append("Select one supported currency.")
    horizon = _number(context.get("horizon_months"), "Comparison horizon", errors)
    if horizon < 1 or horizon > 60 or not horizon.is_integer():
        errors.append("Comparison horizon must be an integer from 1 to 60 months.")
    for key in ("next_commitment", "opportunity_cost_day"):
        _number(context.get(key), "Context " + key.replace("_", " "), errors)
    threshold = context.get("materiality", DEFAULT_MATERIALITY)
    if isinstance(threshold, bool):
        errors.append("Materiality must be a fraction from 0.01 to 0.50.")
    else:
        try:
            threshold = float(threshold)
            if not isfinite(threshold) or not 0.01 <= threshold <= 0.50:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("Materiality must be a fraction from 0.01 to 0.50.")
    for flag in ("mandatory_obligation", "material_nonfinancial", "nonfinancial_reviewed"):
        if type(context.get(flag)) is not bool:
            errors.append("Context " + flag.replace("_"," ") + ": select Yes or No.")
    for label, option in (("Incumbent", incumbent), ("Alternative", alternative)):
        for field in REQUIRED_OPTION:
            if field not in option or option[field] is None or str(option[field]).strip() == "":
                errors.append(f"{label}: {field.replace('_',' ')} is required.")
        for field in NUMERIC_OPTION:
            _number(option.get(field), label + " " + field.replace("_", " "), errors)
        if option.get("evidence") not in EVIDENCE:
            errors.append(f"{label}: select evidence maturity.")
        for field in ("adoption", "operations", "data"):
            if option.get(field) not in READINESS:
                errors.append(f"{label}: select {field} readiness.")
        if option.get("controls") not in CONTROLS:
            errors.append(f"{label}: select control status.")
        for flag in ("operating_owner", "mandatory_meets"):
            if type(option.get(flag)) is not bool:
                errors.append(f"{label}: {flag.replace('_', ' ')} must be Yes or No.")
    if alternative.get("route") not in ROUTES:
        errors.append("Select a credible alternative route to the same outcome.")
    if context.get("mandatory_obligation") is False:
        # mandatory_meets is still explicitly recorded so future changes are testable.
        pass
    if str(incumbent.get("name","")).strip().casefold() == str(alternative.get("name","")).strip().casefold():
        errors.append("Name two distinct routes to the business outcome.")
    return data, list(dict.fromkeys(errors))


def _value(option: dict, day_cost: float, *, include_switching: bool) -> float:
    return (float(option["benefit"]) - float(option["remaining_cost"])
            - float(option["specialist_days"]) * day_cost
            - (float(option["transition_cost"]) if include_switching else 0.0))


def _direction(a: float, b: float, threshold: float) -> str:
    if a <= 0 and b <= 0:
        return "STOP_CANDIDATE"
    if abs(b - a) <= max(abs(a), abs(b), 1.0) * threshold:
        return "CLOSE"
    return "ALTERNATIVE" if b > a else "INCUMBENT"


def assess(raw: dict) -> dict:
    inputs, errors = validate(raw)
    if errors:
        return {"version": MODEL_VERSION, "recommendation": "COMPLETE INPUTS",
                "reasons": errors, "next_action": "Resolve the identified inputs before authorizing investment.",
                "pass_one": None, "pass_two": None, "missing": errors,
                "uncertainty": ["Incomplete or inconsistent assessment."]}
    ctx, inc, alt = (inputs[k] for k in ("context", "incumbent", "alternative"))
    day_cost = float(ctx["opportunity_cost_day"])
    threshold = float(ctx.get("materiality", DEFAULT_MATERIALITY))
    clean_inc = _value(inc, day_cost, include_switching=False)
    clean_alt = _value(alt, day_cost, include_switching=False)
    real_inc = _value(inc, day_cost, include_switching=True)
    real_alt = _value(alt, day_cost, include_switching=True)
    first = _direction(clean_inc, clean_alt, threshold)
    second = _direction(real_inc, real_alt, threshold)
    reasons: list[str] = []
    uncertainty: list[str] = []
    candidate = alt if second == "ALTERNATIVE" else inc
    selected = "Alternative" if second == "ALTERNATIVE" else "Incumbent"
    mandatory = ctx["mandatory_obligation"]
    gates = []
    if mandatory and second == "STOP_CANDIDATE":
        gates.append("A mandatory service, legal or contractual obligation prevents an automatic stop.")
    if mandatory and second == "ALTERNATIVE" and not alt["mandatory_meets"]:
        gates.append("The alternative does not meet the mandatory obligation; replacement cannot be authorized.")
    if mandatory and second == "INCUMBENT" and not inc["mandatory_meets"]:
        gates.append("The incumbent does not meet the mandatory obligation.")
    if mandatory and not inc["mandatory_meets"] and not alt["mandatory_meets"]:
        gates.append("Neither option demonstrates a compliant route for the mandatory obligation.")
    if ctx["material_nonfinancial"] and not ctx["nonfinancial_reviewed"]:
        gates.append("Material nonfinancial or avoided-risk value has not received human review.")
    if second not in ("CLOSE", "STOP_CANDIDATE"):
        if not candidate["operating_owner"]:
            gates.append(f"{selected}: operating accountability is not confirmed.")
        if candidate["controls"] == "blocked":
            gates.append(f"{selected}: an unresolved control blocker prevents commitment.")
    if gates:
        action = "HOLD"
        reasons.extend(gates)
        next_action = "Obtain documented duty, risk and ownership decisions before releasing the next commitment."
    elif second == "STOP_CANDIDATE":
        if any(o["evidence"] == "hypothesis" for o in (inc, alt)):
            action = "TEST"
            reasons.append("Neither option shows positive prospective value, but at least one case is hypothesis-based.")
            next_action = "Run a bounded evidence test or verify the negative case before stopping."
        else:
            action = "STOP"
            reasons.append("Neither route offers positive prospective monetary value over the chosen horizon.")
            next_action = "Plan an orderly withdrawal, retaining essential services, records and reusable assets."
    elif second == "CLOSE":
        action = "TEST"
        reasons.append("The prospective value difference is inside the chosen materiality band.")
        next_action = "Test the assumption most likely to separate the options, with a dated decision gate."
    else:
        unmet = []
        if candidate["evidence"] == "hypothesis":
            unmet.append("outcomes remain hypothesis-based")
        if candidate["controls"] == "mitigate":
            unmet.append("control mitigation is not complete")
        for key in ("adoption","operations","data"):
            if candidate[key] != "ready":
                unmet.append(key + " readiness is " + candidate[key].replace("_"," "))
        if unmet:
            action = "TEST"
            uncertainty.extend(unmet)
            reasons.append(f"{selected} is financially preferred, but " + "; ".join(unmet) + ".")
            next_action = "Authorize only a bounded proof with explicit evidence, risk owner and review date."
        else:
            action = "REPLACE" if second == "ALTERNATIVE" else "RENEW"
            reasons.append(
                ("The alternative" if action == "REPLACE" else "The incumbent")
                + " has the materially stronger forward-looking business case, with ownership, evidence, operating readiness and controls in place."
            )
            next_action = (
                "Authorize a transition gate; confirm release of incumbent capacity and continuity safeguards."
                if action == "REPLACE" else
                "Authorize a bounded continuation with a dated value and adoption checkpoint."
            )
    if first != second:
        reasons.append("The clean-sheet preference changes after switching and transition costs are included.")
    elif first == second:
        reasons.append("The clean-sheet direction survives the real-world financial adjustment.")
    if ctx["material_nonfinancial"] and ctx["nonfinancial_reviewed"]:
        reasons.append("Material unpriced considerations were marked for review; their judgment is not converted into a cash multiplier.")
    if any(o["evidence"] != "operational" for o in (inc, alt)):
        uncertainty.append("At least one option lacks evidence from sustained live operations.")
    return {
        "version": MODEL_VERSION, "recommendation": action, "reasons": reasons,
        "next_action": next_action, "missing": [], "uncertainty": uncertainty,
        "owner": ctx["owner"], "authority": ctx["authority"],
        "currency": ctx["currency"], "horizon_months": int(ctx["horizon_months"]),
        "materiality": threshold, "recommended_review": str(ctx.get("review_date") or ""),
        "pass_one": {"direction": first, "incumbent_net": round(clean_inc,2),
                     "alternative_net": round(clean_alt,2), "delta":round(clean_alt-clean_inc,2)},
        "pass_two": {"direction": second, "incumbent_net": round(real_inc,2),
                     "alternative_net": round(real_alt,2), "delta":round(real_alt-real_inc,2),
                     "incumbent_future_commitment": round(float(inc["remaining_cost"])+float(inc["specialist_days"])*day_cost+float(inc["transition_cost"]),2),
                     "alternative_future_commitment": round(float(alt["remaining_cost"])+float(alt["specialist_days"])*day_cost+float(alt["transition_cost"]),2),
                     "incumbent_specialist_days":float(inc["specialist_days"]),
                     "alternative_specialist_days":float(alt["specialist_days"])},
        "decision_sensitive_to": ["future benefits", "scarce capacity pricing",
                                  "switching costs", "evidence and readiness", "mandatory duties"],
        "warnings": ["No inflation, discounting, tax, option value or risk-adjusted forecast is assumed.",
                     "Management threshold, not a scientifically calibrated standard.",
                     "Sunk expenditure is excluded; amounts are future totals for the same horizon."]
    }


def scenario(base: dict, changes: dict) -> tuple[dict, dict]:
    """Whitelisted stress-test changes; never overwrite the signed base case."""
    if not isinstance(changes, dict) or not changes or set(changes) - SCENARIO_VARIABLES:
        raise ValueError("Scenario contains an unknown or empty assumption change.")
    data = deepcopy(base)
    for path,value in changes.items():
        section,key=path.split(".")
        if section not in data or key not in data[section]:
            raise ValueError("Scenario target is not part of this assessment.")
        data[section][key]=value
    return data, assess(data)
