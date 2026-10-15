"""Opportunity-specific geography policy for Hiring Predictor Beta.

Advertised vacancy location describes *demand*, not a candidate's acceptance
feasibility. Sweden is the addressable market; Gothenburg is a preference.
All classifications are descriptive and deliberately have ZERO effect on the
uncalibrated offer-date curve. Only explicitly documented constraints can make
an opportunity geographically impractical. Do not infer work arrangements from
a company's office location.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from job_search_metrics import canonical_events, day, process_key

GEOGRAPHY_POLICY_VERSION = "se-national-flexible-v1"
HOME_PREFERENCE = "Gothenburg"
PRIMARY_MARKET = "Sweden"
EFFECT_ON_OFFER_PROBABILITY = 0.0

# Only explicit structured vacancy attributes, never free-text job titles,
# apply geography-specific feasibility screening.
LOCATION_KEYS = ("advertised_location", "job_location", "office_location", "location", "city")
FIELD_KEYS = (
    *LOCATION_KEYS, "country", "country_code", "work_model", "remote_in_sweden",
    "multi_office_employer", "gothenburg_office_option", "travel_required",
    "travel_frequency", "travel_feasible", "relocation_required",
    "relocation_feasible", "mandate_quality", "compensation_fit",
    "executive_sponsorship", "family_feasibility",
)
SWEDISH_AREAS = (
    "stockholm", "gothenburg", "göteborg", "vastra gotaland",
    "västra götaland", "malmö", "malmo", "uppsala", "lund",
    "skåne", "skane", "linköping", "linkoping", "umeå", "umea",
    "örebro", "orebro", "västerås", "vasteras", "sweden", "sverige",
)
CONFIRMED_TRUE = (True, "true", "yes", "confirmed", "feasible", "possible")
CONFIRMED_FALSE = (False, "false", "no", "infeasible", "not_feasible", "impractical")
FAVORABLE = ("strong", "high", "competitive", "confirmed", "suitable",
             "acceptable", "yes", "feasible", "approved", "excellent")


def _value(row: dict, field: str) -> Any:
    # Top-level normalized attributes have priority. Historical raw payloads
    # may use the same documented field names. No natural-language guessing.
    if field in row and row[field] not in (None, ""):
        return row[field]
    raw = row.get("raw_data")
    if isinstance(raw, dict) and raw.get(field) not in (None, ""):
        return raw[field]
    return None


def _string(value: Any) -> str:
    return str(value or "").strip().casefold()


def _yes(value: Any) -> bool:
    return value is True or _string(value) in ("true", "yes", "confirmed", "feasible")


def _no(value: Any) -> bool:
    return value is False or _string(value) in ("false", "no", "impractical",
                                                  "infeasible", "not_feasible")


def _location_context(fields: dict) -> tuple[str | None, bool]:
    advertised = next((_string(fields[k]) for k in LOCATION_KEYS if fields.get(k)), "")
    country = _string(fields.get("country_code") or fields.get("country"))
    in_sweden = country in ("se", "swe", "sweden", "sverige") or any(
        word in advertised for word in SWEDISH_AREAS
    )
    return advertised or None, in_sweden


def assess_opportunity(fields: dict) -> dict:
    """Classify evidence, not eligibility from the advert's city name.

    status: compatible, conditional, needs_verification, impractical.
    No status alters the forecast unless a future empirically validated model
    explicitly adds an independently tested conversion feature.
    """
    loc, swedish = _location_context(fields)
    country = _string(fields.get("country_code") or fields.get("country"))
    model = _string(fields.get("work_model")).replace("-", "_").replace(" ", "_")
    remote = model in ("remote", "fully_remote", "remote_first") or _yes(
        fields.get("remote_in_sweden")
    )
    multi_office = _yes(fields.get("multi_office_employer"))
    gothenburg_option = _yes(fields.get("gothenburg_office_option"))
    travel = _string(fields.get("travel_required"))
    relocation_required = _yes(fields.get("relocation_required"))
    relocation_feasible = _yes(fields.get("relocation_feasible"))
    family = _string(fields.get("family_feasibility"))
    relocation_checks = {
        "mandate": _string(fields.get("mandate_quality")) in FAVORABLE,
        "compensation": _string(fields.get("compensation_fit")) in FAVORABLE,
        "sponsorship": _string(fields.get("executive_sponsorship")) in FAVORABLE,
        "family": family in FAVORABLE,
    }
    relocation_ready = relocation_feasible and all(relocation_checks.values())
    details = {
        "advertised_location": loc,
        "advertised_in_sweden": swedish,
        "work_model": model or None,
        "remote_in_sweden": bool(remote and (swedish or _yes(fields.get("remote_in_sweden")))),
        "multi_office_employer": multi_office,
        "gothenburg_office_option": gothenburg_option,
        "relocation_required": relocation_required,
        "relocation_readiness": relocation_checks,
        "travel_requirement": fields.get("travel_required"),
        "probability_effect": EFFECT_ON_OFFER_PROBABILITY,
    }

    if _yes(fields.get("travel_required")) and _no(fields.get("travel_feasible")):
        return {**details, "status": "impractical",
                "reason": "Required travel explicitly marked impractical"}
    if relocation_required and (
        _no(fields.get("relocation_feasible")) or family in ("no", "impractical", "infeasible")
    ):
        return {**details, "status": "impractical",
                "reason": "Mandatory relocation explicitly incompatible"}
    if country and country not in ("se", "swe", "sweden", "sverige") and not swedish and not _yes(
        fields.get("remote_in_sweden")
    ):
        return {**details, "status": "needs_verification",
                "reason": "Outside Sweden; Sweden work eligibility not documented"}
    if relocation_required:
        return {**details, "status": "conditional",
                "reason": ("Relocation conditions documented; final decision remains opportunity-specific"
                           if relocation_ready else
                           "Check mandate, compensation, sponsorship and family before relocation")}
    if remote and (swedish or _yes(fields.get("remote_in_sweden"))):
        return {**details, "status": "compatible",
                "reason": "Remote working from Sweden is explicitly supported"}
    if gothenburg_option:
        return {**details, "status": "compatible",
                "reason": "Gothenburg office option explicitly documented"}
    if loc and ("gothenburg" in loc or "göteborg" in loc):
        return {**details, "status": "compatible",
                "reason": "Advertised location matches home preference"}
    if swedish and multi_office:
        return {**details, "status": "needs_verification",
                "reason": "Sweden-wide leadership option; confirm office flexibility"}
    if swedish:
        return {**details, "status": "conditional",
                "reason": "Sweden-wide opportunity; verify travel/work model or relocation terms"}
    return {**details, "status": "needs_verification",
            "reason": "Advertised office, work pattern and location flexibility not verified"}


def assess_geographic_pipeline(jobs: list[dict], as_of: date) -> dict:
    """Assess once per active documented or unresolved opportunity, not event.

    Geographic evidence is taken from the latest explicitly annotated row
    within each canonical, date-eligible process. Missing rows stay unknown.
    """
    from job_search_metrics import analyze
    events = [
        r for r in canonical_events(jobs)
        if day(r.get("event_date")) and day(r["event_date"]) <= as_of
    ]
    report = analyze(jobs, min(
        (day(r["event_date"]) for r in events), default=as_of
    ), as_of, False)
    live = {
        process_key({"employer": p["Employer"], "role": p["Role"]})
        for p in report["processes"] if p["State"] != "Closed / paused"
    }
    rows_by_process = defaultdict(list)
    for row in events:
        key = process_key(row)
        if key and key in live:
            rows_by_process[key].append(row)
    findings = []
    for key, history in sorted(rows_by_process.items()):
        values = {}
        for row in sorted(history, key=lambda r: (
            str(r.get("event_date") or ""), str(r.get("updated_at") or ""),
            int(r.get("id") or 0),
        )):
            for field in FIELD_KEYS:
                value = _value(row, field)
                if value is not None and value != "":
                    values[field] = value
        classified = assess_opportunity(values)
        findings.append({"employer": key[0], "role": key[1],
                         "has_explicit_geography": bool(values), **classified})
    counts = Counter(item["status"] for item in findings)
    reviewed = sum(row["has_explicit_geography"] for row in findings)
    return {
        "policy_version": GEOGRAPHY_POLICY_VERSION,
        "primary_market": PRIMARY_MARKET,
        "home_preference": HOME_PREFERENCE,
        "travel": "Available unless explicit evidence shows impractical requirements",
        "relocation": "Conditional on mandate, pay, sponsorship and family",
        "automatic_stockholm_penalty": False,
        "numeric_effect": EFFECT_ON_OFFER_PROBABILITY,
        "total_live_processes": len(findings),
        "explicitly_assessed": reviewed,
        "without_location_evidence": len(findings) - reviewed,
        "counts": {status: counts[status] for status in (
            "compatible", "conditional", "needs_verification", "impractical"
        )},
        "opportunities": findings,
        "policy": (
            "Advertisement geography measures demand, not acceptability. "
            "City, travel and relocation only change descriptive feasibility. "
            "Offer odds and dates remain unchanged without candidate-specific "
            "conversion evidence."
        ),
    }
