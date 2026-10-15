"""Anonymous, read-only Supabase request headers for public Analytics.

Never use CMS credentials here or send private refresh/access tokens. The
Postgres EXECUTE grants apply only to aggregate reporting RPCs.
"""
from __future__ import annotations

import json
from urllib import error, request

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL


def public_analytics_rpc_headers() -> dict[str,str]:
    return {
        "apikey": ANALYTICS_PUBLISHABLE_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def fetch_public_analytics_rpc(name: str, payload: dict | None = None) -> dict:
    if name not in ("careersite_public_job_summary_v1",
                    "careersite_public_market_summary_v1",
                    "careersite_public_hiring_inputs_v1",
                    "careersite_public_market_history_v1",
                    "careersite_public_rejection_summary_v1",
                    "careersite_public_pipeline_health_v1"):
        raise ValueError("Not an approved public summary.")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{name}",
        data=json.dumps(payload or {}).encode("utf-8"),
        method="POST", headers=public_analytics_rpc_headers(),
    )
    try:
        with request.urlopen(req,timeout=18) as response:
            result=json.load(response)
    except (error.HTTPError,error.URLError,TimeoutError) as exc:
        raise RuntimeError(f"{name} is temporarily unavailable.") from exc
    if not isinstance(result,dict):
        raise RuntimeError("Unexpected anonymous reporting response.")
    if name == "careersite_public_job_summary_v1":
        # Both Swedish Market correlations and Job Search charts require
        # date+metric OBJECTS. An earlier SQL alias collision returned date
        # strings and crashed both dashboards.
        required=("applications","responses","interviews","rejections")
        for grain,date_key in (("daily","d"),("weekly","week")):
            rows=result.get(grain)
            if not isinstance(rows,list) or any(
                not isinstance(row,dict)
                or not isinstance(row.get(date_key),str)
                or any(
                    not isinstance(row.get(metric),(int,float))
                    or isinstance(row.get(metric),bool)
                    for metric in required
                )
                for row in rows
            ):
                raise RuntimeError(
                    f"Invalid public job-search {grain} response schema. "
                    "The source report is temporarily unavailable."
                )
    if name == "careersite_public_rejection_summary_v1":
        # Strict anonymous-data contract, updated alongside SQL aggregate v2.
        # Never allow recruiter correspondence, company names, individual
        # records, source identifiers or requisition details into public pages.
        baseline_counts = {
            "analyzed_processes", "unknown_causes", "confirmed_explanations",
            "employer_stated_explanations", "dated_decisions", "undated_decisions",
            "unknown_stages", "verified_jds",
        }
        v2_counts = {
            "comparative_selection_count", "employer_specific_reasons_count",
            "matched_cohort_application_pairs", "matched_cohort_negative_pairs",
            "previous_decisions_30d",
        }
        approved = baseline_counts | v2_counts | {
            "available", "method", "as_of", "notice", "recent_decisions_30d",
            "most_frequent_explained_category", "cohort_since",
            "minimum_documented_rejection_share_pct", "rejection_share_method",
        }
        if set(result) - approved:
            raise RuntimeError("Unexpected public rejection-summary fields.")
        if result.get("available") is True:
            if not (baseline_counts | {"method", "as_of"}).issubset(result):
                raise RuntimeError("Incomplete public rejection-summary schema.")
            if any(type(result[k]) is not int or result[k] < 0
                   for k in baseline_counts):
                raise RuntimeError("Invalid public rejection-summary counts.")
            n = result["analyzed_processes"]
            if n < 20 or any(result[k] > n for k in baseline_counts - {"analyzed_processes"}):
                raise RuntimeError("Invalid public rejection aggregation.")
            if result["dated_decisions"] + result["undated_decisions"] != n:
                raise RuntimeError("Inconsistent public rejection-date coverage.")
            for key in v2_counts | {"recent_decisions_30d"}:
                value = result.get(key)
                if value is not None and (type(value) is not int or value < 0):
                    raise RuntimeError("Invalid public rejection metric.")
            for key in ("recent_decisions_30d", "previous_decisions_30d",
                        "comparative_selection_count"):
                value = result.get(key)
                if value is not None and not 10 <= value <= n:
                    raise RuntimeError("Invalid privacy-thresholded rejection count.")
            if result.get("matched_cohort_application_pairs") is not None and (
                    result["matched_cohort_application_pairs"] < 20):
                raise RuntimeError("Invalid cohort privacy threshold.")
            if result.get("matched_cohort_negative_pairs") is not None and (
                    result["matched_cohort_negative_pairs"] < 10 or
                    result["matched_cohort_negative_pairs"] >
                    (result.get("matched_cohort_application_pairs") or 0)):
                raise RuntimeError("Invalid cohort outcome count.")
            if result.get("employer_specific_reasons_count") is not None and (
                    result["employer_specific_reasons_count"] !=
                    result["employer_stated_explanations"]):
                raise RuntimeError("Inconsistent employer-reason aggregate.")
            if result.get("most_frequent_explained_category") not in (
                    None, "Comparative selection (underlying differentiator unverified)"):
                raise RuntimeError("Unexpected public rejection category.")
            if result.get("cohort_since") not in (None, "2026-06-01"):
                raise RuntimeError("Unexpected cohort reporting period.")
            if result.get("rejection_share_method") not in (
                    None, "lower-bound-exact-employer-role-match-not-final-outcome-rate"):
                raise RuntimeError("Unexpected cohort reporting method.")
            rate = result.get("minimum_documented_rejection_share_pct")
            if rate is not None:
                if (type(rate) not in (int, float) or not 0 <= rate <= 100 or
                        result.get("matched_cohort_negative_pairs") is None or
                        result.get("matched_cohort_application_pairs") is None):
                    raise RuntimeError("Invalid public rejection-cohort rate.")
        elif result.get("available") is not False:
            raise RuntimeError("Invalid public rejection-summary availability flag.")
    return result
