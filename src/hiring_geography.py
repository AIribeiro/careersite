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
import re

from job_search_metrics import canonical_events, day, norm, process_key

GEOGRAPHY_POLICY_VERSION = "se-national-evidence-v2"
HOME_PREFERENCE = "Gothenburg"
PRIMARY_MARKET = "Sweden"
EFFECT_ON_OFFER_PROBABILITY = 0.0

# Only explicit structured vacancy attributes, never free-text job titles,
# apply geography-specific feasibility screening.
LOCATION_KEYS = ("advertised_location", "job_location", "office_location", "location", "city", "region")
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
FAVORABLE = ("true", "strong", "high", "competitive", "confirmed", "suitable",
             "acceptable", "yes", "feasible", "approved", "excellent")


def _value(row: dict, field: str) -> Any:
    """Read explicit vacancy metadata, including legacy capitalization.

    Never interpret a company name, job title, or candidate's nationality as a
    vacancy-location source. Raw data is private and is fetched only for the
    authenticated portfolio owner.
    """
    aliases = {
        "advertised_location": ("advertised_location", "job_location",
                                "location", "Location", "Job Location",
                                "office_location", "officeLocation"),
        "work_model": ("work_model", "work_arrangement", "workplace_type",
                       "workplaceType", "remote_type", "Remote type"),
        "country": ("country", "Country", "country_name", "countryName"),
        "country_code": ("country_code", "countryCode"),
    }
    for obj in (row, row.get("raw_data")):
        if not isinstance(obj, dict):
            continue
        for key in aliases.get(field, (field,)):
            if obj.get(key) not in (None, ""):
                return obj[key]
    return None


def _parse_advertised_location(fields: dict) -> tuple[str | None, str | None]:
    """Preserve the text and extract *explicit* (Remote/Hybrid/On-site) suffix."""
    loc = next((_string(fields[k]) for k in LOCATION_KEYS if fields.get(k)), "")
    work = _string(fields.get("work_model")).replace("-", "_").replace(" ", "_")
    if loc and not work:
        match = re.search(r"\(\s*(remote|hybrid|on[\s-]?site)\s*\)\s*$", loc)
        if match:
            work = match.group(1).replace("-", "_").replace(" ", "_")
    return loc or None, work or None


def _string(value: Any) -> str:
    return str(value or "").strip().casefold()


def _yes(value: Any) -> bool:
    return value is True or _string(value) in ("true", "yes", "confirmed", "feasible")


def _no(value: Any) -> bool:
    return value is False or _string(value) in ("false", "no", "impractical",
                                                  "infeasible", "not_feasible")


def _location_context(fields: dict) -> tuple[str | None, bool]:
    advertised, _ = _parse_advertised_location(fields)
    country = _string(fields.get("country_code") or fields.get("country"))
    # Record locality separately from work eligibility. A remote Polish ad
    # does not by itself mean a contract could be performed from Sweden.
    in_sweden = country in ("se", "swe", "sweden", "sverige") or any(
        re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", advertised or "")
        for word in SWEDISH_AREAS
    )
    return advertised, bool(in_sweden)


def assess_opportunity(fields: dict) -> dict:
    """Classify evidence, not eligibility from the advert's city name.

    status: compatible, conditional, needs_verification, impractical.
    No status alters the forecast unless a future empirically validated model
    explicitly adds an independently tested conversion feature.
    """
    loc, swedish = _location_context(fields)
    country = _string(fields.get("country_code") or fields.get("country"))
    _, inferred_model = _parse_advertised_location(fields)
    model = inferred_model or ""
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

    if (fields.get("travel_required") not in (None, False, "", "none", "no")
            and _no(fields.get("travel_feasible"))):
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


def assess_geographic_pipeline(
    jobs: list[dict], as_of: date, *,
    additional_locations: dict | None = None,
) -> dict:
    """Join trusted source locations across a *process*, then assess feasibility.

    The canonical event table counts hiring processes; geography enrichment
    independently inspects all dated owner-visible evidence for those SAME
    employer+role keys. Metadata is not a new application, interview or lead.
    The optional Jobwise match is owner-only, exact company+role, unique
    vacancy location. It is a fallback, never overrides source evidence.
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
    # Include non-primary corroborating source rows; they cannot increment the
    # number of live processes, whose keys come exclusively from canonical
    # non-closed event histories.
    for row in jobs:
        if row.get("record_type") not in (
            "evidence_event", "history_event", "activity_summary"
        ):
            continue
        event_day = day(row.get("event_date"))
        if not event_day or event_day > as_of:
            continue
        key = process_key(row)
        if key and key in live:
            rows_by_process[key].append(row)
    extra = {}
    if additional_locations and additional_locations.get("method") == (
        "linked_user_workspace_exact_company_title"
    ):
        for r in additional_locations.get("unique_locations") or []:
            if r.get("quality") != "exact_company_role_unique_location":
                continue
            key = (norm(r.get("employer_key")), norm(r.get("role_key")))
            if key not in live or not r.get("advertised_location"):
                continue
            # Ignore ambiguous input duplicate keys instead of choosing one.
            if key in extra:
                extra[key] = None
            else:
                extra[key] = r

    findings = []
    for key in sorted(live):
        if key is None:
            continue
        history = rows_by_process.get(key, [])
        values = {}
        explicitly_found = set()
        for row in sorted(history, key=lambda r: (
            str(r.get("event_date") or ""), str(r.get("updated_at") or ""),
            int(r.get("id") or 0),
        )):
            for field in FIELD_KEYS:
                value = _value(row, field)
                if value is not None and value != "":
                    values[field] = value
                    explicitly_found.add(field)
        location = next((values.get(k) for k in LOCATION_KEYS
                         if values.get(k)), None)
        source = "job_search_source" if location else None
        fallback = extra.get(key)
        if not location and fallback:
            values["advertised_location"] = fallback["advertised_location"]
            if fallback.get("country"):
                values["country"] = fallback["country"]
            source = "matched_jobwise_application"
        classification = assess_opportunity(values)
        arrangement_recorded = bool(
            values.get("work_model") or values.get("remote_in_sweden") is not None
            or (classification.get("advertised_location")
                and re.search(r"\(\s*(remote|hybrid|on[\s-]?site)\s*\)\s*$",
                              classification["advertised_location"]))
        )
        known = bool(classification["advertised_location"])
        findings.append({
            "employer": key[0], "role": key[1],
            "has_explicit_geography": known or arrangement_recorded,
            "advertised_location_recorded": known,
            "arrangement_recorded": arrangement_recorded,
            "location_evidence_source": source,
            **classification,
        })
    counts = Counter(item["status"] for item in findings)
    source_counts = Counter(item["location_evidence_source"] for item in findings
                            if item.get("advertised_location_recorded"))
    location_count = sum(item["advertised_location_recorded"] for item in findings)
    arrangement_count = sum(item["arrangement_recorded"] for item in findings)
    return {
        "policy_version": GEOGRAPHY_POLICY_VERSION,
        "primary_market": PRIMARY_MARKET,
        "home_preference": HOME_PREFERENCE,
        "travel": "Available unless explicit evidence shows impractical requirements",
        "relocation": "Conditional on mandate, pay, sponsorship and family",
        "automatic_stockholm_penalty": False,
        "numeric_effect": EFFECT_ON_OFFER_PROBABILITY,
        "total_live_processes": len(findings),
        "explicitly_assessed": sum(r["has_explicit_geography"] for r in findings),
        "advertised_locations_recorded": location_count,
        "work_arrangements_recorded": arrangement_count,
        "without_location_evidence": len(findings) - location_count,
        "source_counts": dict(source_counts),
        "counts": {status: counts[status] for status in (
            "compatible", "conditional", "needs_verification", "impractical"
        )},
        "opportunities": findings,
        "policy": (
            "Advertisement geography measures demand, not acceptability. "
            "Source city/country alone does not establish working arrangements. "
            "City, travel and relocation only change descriptive feasibility; "
            "they never change offer probabilities without verified recruitment "
            "outcome evidence."
        ),
    }
