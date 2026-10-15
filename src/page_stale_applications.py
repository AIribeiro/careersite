"""Evidence-led stale application reporting.

Private employer-level records remain behind owner auth. Public components consume
only the aggregated, allowlisted Supabase RPC; never a private token or view.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from site_cms import _request_json, _rest_url

STATUS = [
    ("recent_awaiting_response", "Recent · awaiting response"),
    ("stale_21_44", "Stale · 21–44 days"),
    ("stale_45_59", "Elevated · 45–59 days"),
    ("stale_60_plus", "Long silent · 60+ days"),
    ("verified_dormant", "Verified dormant"),
    ("recruiter_engaged", "Recruiter engaged"),
    ("closed", "Closed / rejected"),
    ("date_unverified", "Date unverified"),
]
LABELS = dict(STATUS)
UNANSWERED = {"recent_awaiting_response", "stale_21_44", "stale_45_59",
              "stale_60_plus", "verified_dormant"}
STALE = UNANSWERED - {"recent_awaiting_response"}


def fetch_private_pipeline(access_token: str) -> list[dict]:
    """Owner-restricted security-invoker view. Never cache across sessions."""
    if not access_token:
        raise ValueError("Owner session required.")
    rows = []
    fields = ("process_key,employer,role,applied_on,days_since_application,"
              "health_segment,evidence_quality,first_response_on,last_response_on,"
              "next_step,exclude_from_active_forecast,review_expired_or_overridden,"
              "evidence_scope,verified_at,evidence_notes")
    for offset in range(0, 100000, 500):
        batch = _request_json(
            "GET", _rest_url("careersite_stale_application_pipeline_v2?"
                             f"select={fields}&order=applied_on.desc.nullslast&limit=500&offset={offset}"),
            token=access_token,
        )
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected staleness review response.")
        rows.extend(batch)
        if len(batch) < 500:
            return rows
    raise RuntimeError("The staleness review exceeded the allowed result limit.")


def private_summary(rows: list[dict]) -> dict:
    """Mutually exclusive counts. Does not turn silence into rejection."""
    unique = {r.get("process_key"): r for r in rows
              if r.get("process_key") and r.get("health_segment") != "identity_alias"}
    records = list(unique.values())
    counts = Counter(r.get("health_segment") for r in records)
    dated = [r for r in records if isinstance(r.get("days_since_application"), int)]
    matured = [r for r in dated if r["days_since_application"] >= 21]
    return {
        "as_of": datetime.now(ZoneInfo("Europe/Stockholm")).date().isoformat(),
        "status": [{"segment": k, "n": counts[k]} for k, _ in STATUS],
        "metrics": {
            "total_processes": len(records),
            "unanswered": sum(counts[k] for k in UNANSWERED),
            "stale": sum(counts[k] for k in STALE),
            "long_silent_unverified": counts["stale_60_plus"],
            "verified_dormant": counts["verified_dormant"],
            "verification_backlog": sum(counts[k] for k in
                ("stale_21_44", "stale_45_59", "stale_60_plus")) +
                sum(bool(r.get("review_expired_or_overridden")) for r in records),
            "active_forecast_dormant_exclusions": sum(
                r.get("health_segment") == "verified_dormant" and
                r.get("exclude_from_active_forecast") is True for r in records),
            "undated": counts["date_unverified"],
            "engaged": counts["recruiter_engaged"],
            "matured_denominator": len(matured),
            "matured_unanswered": sum(r.get("health_segment") in STALE for r in matured),
        },
    }


def _number(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _interpret(data: dict) -> str:
    metrics = data.get("metrics") or {}
    pending = _number(metrics.get("verification_backlog"))
    dormant = _number(metrics.get("active_forecast_dormant_exclusions"))
    engaged = _number(metrics.get("engaged"))
    if pending:
        return (
            f"{pending} ageing applications still need evidence review. "
            f"Only {dormant} verified dormant process(es) are removed from the active "
            f"forecast. {engaged} processes have documented recruiter engagement. "
            "Unanswered applications are not treated as rejections."
        )
    return (
        f"{dormant} verified dormant processes are excluded from the active forecast. "
        "No unverified stale processes remain in the current review queue."
    )


def render_pipeline_health(data: dict, *, compact: bool = False) -> None:
    if not data or not isinstance(data.get("metrics"), dict):
        st.info("Pipeline health needs current process-level evidence.")
        return
    m = data["metrics"]
    st.subheader("Pipeline Health")
    st.write(_interpret(data))
    denom = _number(m.get("matured_denominator"))
    unanswered = _number(m.get("matured_unanswered"))
    a, b, c = st.columns(3)
    a.metric("Unanswered applications", _number(m.get("unanswered")))
    b.metric("Verification backlog", _number(m.get("verification_backlog")))
    c.metric("Verified dormant exclusions",
             _number(m.get("active_forecast_dormant_exclusions")))
    st.caption(
        f"As of {data.get('as_of', 'current refresh')} · employer–role process unit · "
        f"{_number(m.get('total_processes'))} distinct process rows excluding aliases. "
        "Separate verified requisitions may still need reconciliation."
    )
    if denom:
        st.caption(
            f"Matured no-response share: {unanswered/denom:.0%} "
            f"({unanswered}/{denom}, dated applications at least 21 days old). "
            "An unresolved response is not a rejection, and a recent cohort has less observation time."
        )
    if _number(m.get("undated")):
        st.caption(
            f"{_number(m.get('undated'))} processes have unresolved application dates. "
            "They are excluded from age comparisons."
        )
    if compact:
        return

    chart_data = [
        {"Segment": LABELS.get(r.get("segment"), str(r.get("segment"))),
         "Processes": _number(r.get("n")), "Group": "Recorded processes",
         "order": i}
        for i, r in enumerate(
            [next((v for v in data.get("status") or []
                   if v.get("segment") == key), {"n": 0}) | {"segment": key}
             for key, _ in STATUS]
        )
    ]
    st.altair_chart(
        alt.Chart(alt.Data(values=chart_data)).mark_bar(size=32).encode(
            x=alt.X("Processes:Q", title="Canonical process count",
                    axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Group:N", title=None),
            color=alt.Color("Segment:N", sort=[x[1] for x in STATUS],
                            legend=alt.Legend(orient="bottom", columns=2)),
            order=alt.Order("order:Q"),
            tooltip=["Segment:N", "Processes:Q"],
        ).properties(height=150), width="stretch",
    )
    st.caption(
        "Segments are mutually exclusive. Verified dormant is separate from rejected "
        "and does not mean the employer has closed the vacancy."
    )

    cohorts = data.get("cohorts") or []
    if cohorts:
        st.markdown("**Application cohorts and response maturity**")
        points = [
            {"Month": r.get("cohort_month"), "Current state": label,
             "Processes": _number(r.get(key))}
            for r in cohorts
            for key, label in (("unanswered", "Unanswered"), ("closed", "Closed"),
                               ("remainder", "Recruiter engaged / other"))
            if key != "remainder" or
            _number(r.get("applications")) -
            _number(r.get("unanswered")) - _number(r.get("closed")) > 0
        ]
        for row in points:
            if row["Current state"] == "Recruiter engaged / other":
                source = next((r for r in cohorts if r.get("cohort_month")==row["Month"]), {})
                row["Processes"] = max(0, _number(source.get("applications")) -
                                     _number(source.get("unanswered")) -
                                     _number(source.get("closed")))
        st.altair_chart(
            alt.Chart(alt.Data(values=points)).mark_bar().encode(
                x=alt.X("Month:N", sort="ascending", title="Application month"),
                y=alt.Y("Processes:Q", title="Current outcome"),
                color="Current state:N",
                tooltip=["Month:N", "Current state:N", "Processes:Q"],
            ).properties(height=260), width="stretch",
        )
        st.dataframe([{
            "Cohort": r.get("cohort_month"),
            "Processes": _number(r.get("applications")),
            "Substantive response recorded": _number(r.get("responded")),
            "Response share": (
                f"{_number(r.get('responded')) / _number(r.get('applications')):.0%}"
                if _number(r.get("applications")) and r.get("matured_21d")
                else "Immature cohort"
            ),
            "21-day observation mature": bool(r.get("matured_21d")),
        } for r in cohorts], hide_index=True, width="stretch")
        st.caption(
            "Response share includes a recorded employer decision, so a closed case "
            "can also have received a substantive response. Month-level comparisons "
            "are only meaningful for cohorts with at least 21 days of observation."
        )
    latency = data.get("first_response") or {}
    if _number(latency.get("eligible")):
        st.markdown(
            f"**First substantive response:** median {latency.get('median_days')} "
            f"calendar days across {_number(latency.get('eligible'))} dated matches."
        )
        st.caption(
            "Application receipts, viewed notifications, generic acknowledgements "
            "and marketing messages are excluded from this measure. "
            "Unanswered applications are right-censored and not assigned a response time."
        )


def _role_priority(role: str) -> int:
    value = (role or "").casefold()
    if "ai" in value or "artificial intelligence" in value or "data" in value:
        return 0
    if "analytics" in value or "automation" in value:
        return 1
    return 2


def private_review_queue(rows: list[dict]) -> list[dict]:
    """Role-fit and actionability precede raw age; avoid a 60+ first bias."""
    queue = []
    for r in rows:
        segment = r.get("health_segment")
        if segment not in ("stale_21_44", "stale_45_59", "stale_60_plus",
                           "date_unverified"):
            continue
        age = r.get("days_since_application")
        action = ("Review follow-up" if segment == "stale_21_44"
                  else "Reconcile submission date" if segment == "date_unverified"
                  else "Verify recruiting evidence")
        queue.append({
            "Employer": r.get("employer"), "Role": r.get("role"),
            "Applied": r.get("applied_on"), "Days waiting": age,
            "Last employer signal": r.get("last_response_on"),
            "Classification": LABELS.get(segment, segment),
            "Evidence": r.get("evidence_quality") or "unverified",
            "Forecast": "Excluded" if r.get("exclude_from_active_forecast") else "Provisional",
            "Next action": action,
            "_rank": (_role_priority(r.get("role") or ""),
                      0 if segment == "stale_21_44" else 1 if segment == "stale_45_59"
                      else 2 if segment == "date_unverified" else 3,
                      -(age or 0)),
        })
    queue.sort(key=lambda item: item["_rank"])
    return [{k: v for k, v in r.items() if k != "_rank"} for r in queue]


def render_private_staleness(access_token: str, *, compact: bool = False) -> None:
    try:
        records = fetch_private_pipeline(access_token)
    except (RuntimeError, TimeoutError, ValueError):
        st.warning("The owner-only application review is temporarily unavailable.")
        return
    summary = private_summary(records)
    render_pipeline_health(summary, compact=compact)
    if compact:
        return
    st.subheader("Review queue · owner only")
    st.caption(
        "Role family and follow-up actionability take precedence over age. "
        "These are review suggestions, not evidence of an employer decision. "
        "This page reads the evidence ledger but does not mark any case verified."
    )
    queue = private_review_queue(records)
    if queue:
        st.dataframe(queue, hide_index=True, width="stretch")
    else:
        st.info("No records currently require verification or follow-up.")
    with st.expander("Evidence scope and review expiry"):
        st.dataframe([
            {"Employer":r.get("employer"), "Role":r.get("role"),
             "Review verified":r.get("verified_at"), "Sources":r.get("evidence_scope"),
             "Classification":r.get("health_segment"),
             "Review expired / overridden":r.get("review_expired_or_overridden"),
             "Notes":r.get("evidence_notes")}
            for r in records if r.get("verified_at") or r.get("evidence_scope")
        ], hide_index=True, width="stretch")
    st.caption(
        "Checking absence in a mailbox is not proof that no message exists. "
        "Verification requires fresh source reconciliation; expiry occurs after 30 days. "
        "Distinct requisitions with identical employer and role still require ID reconciliation."
    )
