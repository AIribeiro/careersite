"""Engaged hiring process shortlist for the private follow-up manager.

Requires a positive human recruiter/hiring-team contact or interview evidence.
No email is sent and no records are reclassified here.
"""
from __future__ import annotations

from datetime import date

import streamlit as st
from site_cms import _request_json, _rest_url

_VIEW = "careersite_followup_engaged_status_v1"
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


def fetch_engaged(token: str) -> list[dict]:
    fields = (
        "source_type,source_ref,opportunity_id,employer,role_title,source_status,"
        "application_date,interview_date,next_interview_date,action,due_date,"
        "decision_reason,evidence_sources,engagement_basis,engagement_confidence,"
        "engagement_source,last_engagement_on,manual_status,manual_status_on,"
        "manual_status_note,is_archived,effective_action,effective_reason,"
        "unanswered_followups,last_recruiter_reply_on,last_recorded_followup_on"
    )
    result = _request_json(
        "GET",
        _rest_url(f"{_VIEW}?select={fields}&order=application_date.desc.nullslast&limit=1000"),
        token=token,
    )
    if not isinstance(result, list):
        raise RuntimeError("Engaged hiring-process shortlist did not return a list.")
    return [row for row in result if isinstance(row, dict)]


def render_application_coverage(token: str, rows: list[dict] | None = None,
                                timeline: dict[tuple[str, str], list[dict]] | None = None,
                                role_contacts: dict[tuple[str, str], list[dict]] | None = None) -> None:
    st.subheader("Engaged hiring processes")
    st.caption(
        "Only vacancies with at least one substantive positive recruiter/hiring-manager "
        "reply or a recorded interview invitation/meeting. Applications alone, automated "
        "receipts and profile views are excluded. Rejected, cancelled and withdrawn "
        "processes are also excluded. Some older engagement evidence needs rechecking."
    )
    if rows is None:
        try:
            rows = fetch_engaged(token)
        except (RuntimeError, ValueError) as exc:
            st.warning(f"Could not load engaged hiring-process shortlist: {exc}")
            return
    active = [r for r in rows if not r.get("is_archived")]
    extra = [r for r in active if r.get("source_type") != "managed"]
    review_due = sum(r.get("effective_action") == "review_due" for r in extra)
    upcoming = sum(r.get("effective_action") == "review_upcoming" for r in extra)
    evidence = sum(r.get("effective_action") in {"stale_review", "verify_date"} for r in extra)
    cols = st.columns(4)
    for col, title, value in zip(
        cols,
        ("Engaged processes", "Review checkpoints due", "Upcoming checkpoints", "Older / missing evidence"),
        (len(active), review_due, upcoming, evidence),
    ):
        col.metric(title, value)
    st.caption(
        f"{sum(r.get('source_type') == 'managed' for r in active)} managed recruiting records "
        f"and {len(extra)} additional human-engaged processes. "
        f"{len(rows) - len(active)} archived. Review-due does not mean a message should be sent."
    )
    needle = st.text_input(
        "Search engaged processes", placeholder="Employer or role", key="fu_all_search"
    ).strip().casefold()
    options = {
        "All": None, "Review due": "review_due",
        "Upcoming review": "review_upcoming", "Older / stale": "stale_review",
        "Missing dates": "verify_date", "Managed": "managed",
        "Follow-ups exhausted": "exhausted",
    }
    view = st.selectbox("Review filter", list(options), key="fu_all_filter")
    show_archived = st.checkbox(
        "Show archived / ignored processes", value=False, key="fu_show_archived_coverage"
    )
    filtered = [
        r for r in rows
        if (show_archived or not r.get("is_archived"))
        and (not needle or needle in
            (str(r.get("employer") or "") + " " + str(r.get("role_title") or "")).casefold())
        and (view == "All"
             or (view == "Managed" and r.get("source_type") == "managed")
             or (view == "Follow-ups exhausted" and
                 int(r.get("unanswered_followups") or 0) >= 2)
             or r.get("effective_action") == options[view])
    ]
    filtered.sort(
        key=lambda r: (
            _PRIORITY.get(r.get("effective_action"), 9),
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
                    "My status": str(r.get("manual_status") or "tracking").replace("_", " "),
                    "Qualifying contact": str(r.get("engagement_basis") or "").replace("_", " "),
                    "Evidence quality": r.get("engagement_confidence") or "—",
                    "Last contact": _day(r.get("last_engagement_on")),
                    "Unanswered chasers": r.get("unanswered_followups") or 0,
                    "Applied": _day(r.get("application_date")),
                    "Checkpoint": _day(r.get("due_date")),
                    "Action": str(r.get("effective_action") or "").replace("_", " ").capitalize(),
                    "Reason": r.get("effective_reason") or "",
                }
                for r in filtered
            ],
            width="stretch", hide_index=True, height=460,
        )
    else:
        st.info("No matching engaged processes.")
    external = [r for r in rows if r.get("source_type") != "managed"]
    if external:
        st.markdown("**Update a recruiter-contact process outside the interview register**")
        st.caption("Managed processes can be updated directly on their cards above.")
        options_by_source = {(str(r.get("source_type")), str(r.get("source_ref"))): r for r in external}
        choices = list(options_by_source)
        chosen = st.selectbox(
            "Select employer and role",
            options=choices,
            format_func=lambda k: (
                f"{options_by_source[k].get('employer')} · {options_by_source[k].get('role_title')}"
                + (" (archived)" if options_by_source[k].get("is_archived") else "")
            ),
            key="fu_external_status_selector",
        )
        from page_followup_status import status_editor
        from page_followup_history import history_editor, contacts_panel
        status_editor(token, options_by_source[chosen], prefix="external")
        contacts_panel(options_by_source[chosen], role_contacts or {})
        history_editor(token, options_by_source[chosen], prefix="external", timeline=timeline)

    st.caption(
        "Positive engagement qualifies a role for follow-up tracking, not for immediate "
        "outreach. Older replies, unverified attendance, missing recipient details "
        "and provisional cross-role referrals remain review-only. "
        "Copyable emails appear only when a separately verified send checkpoint is due."
    )
