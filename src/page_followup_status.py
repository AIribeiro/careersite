"""Owner-only, reversible status controls for engaged recruiting processes."""
from __future__ import annotations

from datetime import date, datetime, timezone

import streamlit as st
from site_cms import _request_json, _rest_url

TABLE = "careersite_followup_process_status"
STATUS_LABELS = {
    "tracking": "Tracking / no change",
    "contacted": "I contacted recruiter",
    "recruiter_replied": "Recruiter replied",
    "interview_scheduled": "Interview arranged",
    "rejected": "Rejected by recruiter",
    "withdrawn": "Withdrawn by me",
    "ignored": "Ignore / archive",
    "cancelled": "Vacancy cancelled",
    "closed": "Process closed",
}
ARCHIVED = {"rejected", "withdrawn", "ignored", "cancelled", "closed"}


def save_status(token: str, row: dict, status: str, status_on: date, note: str) -> None:
    """Write a manual, sourced owner decision; do not change original evidence."""
    source_type = str(row.get("source_type") or "")
    source_ref = str(row.get("source_ref") or "")
    if source_type not in ("managed", "analytics", "jobwise", "evidence") or not source_ref:
        raise ValueError("The process needs a verified source identifier.")
    if status not in STATUS_LABELS:
        raise ValueError("Select a supported status.")
    if status_on > date.today():
        raise ValueError("The status date cannot be in the future.")
    _request_json(
        "POST",
        _rest_url(f"{TABLE}?on_conflict=source_type,source_ref"),
        token=token,
        payload={
            "source_type": source_type,
            "source_ref": source_ref,
            "status": status,
            "status_on": status_on.isoformat(),
            "status_note": note.strip()[:1000],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        prefer="resolution=merge-duplicates,return=minimal",
    )


def status_editor(token: str, row: dict, *, prefix: str = "managed") -> None:
    """Inline quick edit, deliberately separate from contact/evidence details."""
    source_type = str(row.get("source_type") or "")
    source_ref = str(row.get("source_ref") or "")
    key = f"{prefix}_{source_type}_{source_ref}"
    current = str(row.get("manual_status") or "tracking")
    if current not in STATUS_LABELS:
        current = "tracking"
    on = row.get("manual_status_on")
    try:
        existing_date = date.fromisoformat(str(on)[:10]) if on else date.today()
    except ValueError:
        existing_date = date.today()

    with st.form(f"fu_quick_status_{key}", border=False):
        c1, c2, c3 = st.columns([2.6, 1.25, 1.15], vertical_alignment="bottom")
        with c1:
            selected = st.selectbox(
                "Process status",
                options=list(STATUS_LABELS),
                index=list(STATUS_LABELS).index(current),
                format_func=lambda value: STATUS_LABELS[value],
                key=f"fu_status_{key}",
            )
        with c2:
            status_on = st.date_input(
                "Status date",
                value=existing_date,
                max_value=date.today(),
                format="DD/MM/YYYY",
                key=f"fu_date_{key}",
            )
        with c3:
            apply = st.form_submit_button("Save status", type="primary", use_container_width=True)
        note = st.text_input(
            "Note (optional)",
            value=str(row.get("manual_status_note") or ""),
            placeholder="e.g., recruiter confirmed rejection on LinkedIn",
            key=f"fu_note_{key}",
        )
    if apply:
        try:
            save_status(token, row, selected, status_on, note)
        except (RuntimeError, ValueError) as exc:
            st.error(f"Status not saved: {exc}")
        else:
            st.success("Status saved. The follow-up list has been updated.")
            st.rerun()
    if current in ARCHIVED:
        st.caption("Archived from follow-up actions. Select 'Tracking / no change' to restore.")
    elif current == "contacted":
        st.caption("Logged as candidate outreach. This does not imply a recruiter response or a sent status-chasing email.")
    elif current == "recruiter_replied":
        st.caption("Manual report of recruiter response; verify the message before updating recruiter evidence.")
    elif current == "interview_scheduled":
        st.caption("Scheduling noted. An invitation or calendar evidence is still needed to confirm the date.")
