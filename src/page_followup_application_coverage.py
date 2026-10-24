"""Full non-rejected job application register for the private follow-up manager.

Combines authenticated recruiting journeys, job_search_analytics evidence and
Jobwise applications. No email is sent and no records are reclassified here.
"""
from __future__ import annotations

from datetime import date

import streamlit as st
from site_cms import _request_json, _rest_url

_VIEW = "careersite_followup_application_coverage_v1"
_PRIORITY = {
    "follow_up_now": 0, "review_due": 1, "upcoming": 2,
    "review_upcoming": 3, "wait": 4, "verify_date": 5,
    "hold": 6, "stale_review": 7,
}


def _day(value: object) -> str:
    if not value:
        return "—"
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d %b %Y")
    except ValueError:
        return str(value)[:10]


def _fetch(token: str) -> list[dict]:
    fields = (
        "source_type,source_ref,opportunity_id,employer,role_title,source_status,"
        "application_date,interview_date,next_interview_date,action,due_date,"
        "decision_reason,evidence_sources"
    )
    result = _request_json(
        "GET",
        _rest_url(f"{_VIEW}?select={fields}&order=application_date.desc.nullslast&limit=1000"),
        token=token,
    )
    if not isinstance(result, list):
        raise RuntimeError("Full application coverage did not return a list.")
    return [row for row in result if isinstance(row, dict)]


def render_application_coverage(token: str) -> None:
    st.subheader("Full application coverage")
    st.caption(
        "All submitted or interviewed processes, except rejected, cancelled or "
        "withdrawn records. Evidence is consolidated from the recruiting register, "
        "Job Search Analytics, Jobwise and verified submission evidence. Entries "
        "for the same employer and role are deduplicated; distinct requisitions "
        "with identical titles may need review."
    )
    try:
        rows = _fetch(token)
    except (RuntimeError, ValueError) as exc:
        st.warning(f"Could not load full application coverage: {exc}")
        return
    extra = [r for r in rows if r.get("source_type") != "managed"]
    review_due = sum(r.get("action") == "review_due" for r in extra)
    upcoming = sum(r.get("action") == "review_upcoming" for r in extra)
    evidence = sum(r.get("action") in {"stale_review", "verify_date"} for r in extra)
    cols = st.columns(4)
    for col, title, value in zip(
        cols,
        ("All processes", "Application reviews due", "Upcoming reviews", "Evidence reviews"),
        (len(rows), review_due, upcoming, evidence),
    ):
        col.metric(title, value)
    st.caption(
        f"{len(rows) - len(extra)} managed recruiting records and {len(extra)} additional "
        "application records. Review-due does not mean a message should be sent."
    )
    needle = st.text_input(
        "Search applications", placeholder="Employer or role", key="fu_all_search"
    ).strip().casefold()
    options = {
        "All": None, "Review due": "review_due",
        "Upcoming review": "review_upcoming", "Older / stale": "stale_review",
        "Missing dates": "verify_date", "Managed": "managed",
    }
    view = st.selectbox("Review filter", list(options), key="fu_all_filter")
    filtered = [
        r for r in rows
        if (not needle or needle in
            (str(r.get("employer") or "") + " " + str(r.get("role_title") or "")).casefold())
        and (view == "All"
             or (view == "Managed" and r.get("source_type") == "managed")
             or r.get("action") == options[view])
    ]
    filtered.sort(
        key=lambda r: (
            _PRIORITY.get(r.get("action"), 9),
            r.get("due_date") or "9999-12-31",
            str(r.get("employer") or "").casefold(),
        )
    )
    if filtered:
        st.dataframe(
            [
                {
                    "Employer": r.get("employer") or "",
                    "Role": r.get("role_title") or "",
                    "Source": r.get("source_type") or "",
                    "Recorded status": r.get("source_status") or "Unknown",
                    "Applied": _day(r.get("application_date")),
                    "Checkpoint": _day(r.get("due_date")),
                    "Action": str(r.get("action") or "").replace("_", " ").capitalize(),
                    "Reason": r.get("decision_reason") or "",
                }
                for r in filtered
            ],
            width="stretch", hide_index=True, height=460,
        )
    else:
        st.info("No matching application records.")
    st.caption(
        "Application-only records are review tasks until a named recruiter/contact, "
        "current communication and the relevant vacancy are verified. "
        "Use the managed section above for eligible, copyable email drafts."
    )
