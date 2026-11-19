"""Current-stage and MTO board based on the canonical owner recruiting ledger.

A snapshot from the legacy hiring forecast is never a live stage source.
A stage, a recruiter screening, a video assessment and a networking chat
have different evidence meanings and never imply an employer decision.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import streamlit as st

from site_cms import _request_json, _rest_url
from current_hiring_pipeline import (
    current_rows, strategic_rows, fetch_current_pipeline, freshness_status,
    _stockholm_time,
)
from meeting_to_offer import estimate_mto

ATTENDED_HIRING = {"interview", "hiring_manager", "recruiter_screening"}
TERMINAL = {"rejected", "closed", "withdrawn", "offer_accepted", "hired"}


def fetch_stage_meetings(token: str) -> list[dict]:
    """An authenticated ledger read; do not infer attendance from appointments."""
    if not token:
        raise ValueError("Owner authorization required")
    response = _request_json(
        "GET",
        _rest_url(
            "careersite_recruiter_meetings?"
            "select=id,opportunity_id,meeting_type,attendance,scheduled_date,"
            "interviewer_role,decision_authority,source_event_id"
            "&order=scheduled_date.desc,id.desc&limit=300"
        ),
        token=token,
        timeout=15,
    )
    if not isinstance(response, list):
        raise RuntimeError("Current recruiting meeting ledger unavailable")
    return response


def fetch_stage_keys(token: str) -> dict[str, str]:
    response = _request_json(
        "GET",
        _rest_url(
            "careersite_recruiting_opportunities?"
            "select=id,process_key&order=updated_at.desc&limit=200"
        ),
        token=token, timeout=15,
    )
    if not isinstance(response, list):
        raise RuntimeError("Exact requisition keys unavailable")
    return {str(x.get("id")): str(x.get("process_key") or "")
            for x in response if isinstance(x, dict)}


def meeting_summary(rows: list[dict], meetings: list[dict] | None) -> list[dict]:
    """Derive a separate count for screening versus employer interviews."""
    if meetings is None:
        return [{**r, "screens_held": None, "interviews_held": None,
                 "mto": "—", "remaining": "Unknown", "mto_note":
                 "Meeting ledger unavailable; MTO cannot be reconciled."}
                for r in rows]
    by_opportunity = defaultdict(list)
    for m in meetings:
        if not isinstance(m, dict) or m.get("opportunity_id") is None:
            continue
        if (m.get("attendance") == "attended"
                and m.get("meeting_type") in ATTENDED_HIRING):
            by_opportunity[str(m["opportunity_id"])].append(m)

    out = []
    for row in rows:
        raw = by_opportunity.get(str(row["id"]), [])
        seen = set()
        unique = []
        for m in raw:
            key = str(m.get("source_event_id") or m.get("id"))
            if key not in seen:
                seen.add(key)
                unique.append(m)
        screens = sum(m["meeting_type"] == "recruiter_screening" for m in unique)
        interviews = sum(m["meeting_type"] in ("interview", "hiring_manager") for m in unique)
        est = estimate_mto({"role": row["role"]}, completed=len(unique), meetings=unique)
        out.append({
            **row,
            "screens_held": screens,
            "interviews_held": interviews,
            "mto": f"~{est.total_low}–{est.total_high}",
            "remaining": f"~{est.remaining_low}–{est.remaining_high}",
            "mto_note": est.explanation,
        })
    return out


def stage_display_rows(sources: dict, meetings: list[dict] | None,
                       process_keys: dict[str, str] | None = None,
                       focus: str = "") -> list[dict]:
    rows = current_rows(sources)
    if focus and process_keys is not None:
        rows = [r for r in rows
                if str(process_keys.get(str(r["id"])) or "").casefold() == focus.casefold()]
    return meeting_summary(rows, meetings)


def _table_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "Employer / role": r["employer"] + " · " + r["role"],
            "Priority": r["band"] + (" · review" if r.get("rank_needs_review") else ""),
            "Verified status": r["stage"],
            "Recruiter screens held": (
                r.get("screens_held") if r.get("screens_held") is not None else "Unverified"
            ),
            "Other hiring interviews held": (
                r.get("interviews_held") if r.get("interviews_held") is not None else "Unverified"
            ),
            "MTO (estimate)": r["mto"],
            "Remaining (estimate)": r["remaining"],
            "Recorded status": str(r.get("event_date") or "Undated"),
        }
        for r in rows
    ]


def render_stage_evidence(sources: dict, meetings: list[dict] | None,
                          keys: dict[str, str] | None = None,
                          focus: str = "") -> None:
    rows = stage_display_rows(sources, meetings, keys, focus)
    main = [r for r in rows if r["band"] == "P1"]
    lower = [r for r in rows if r["band"] != "P1"]
    st.subheader("Hiring stages & meetings to offer")
    st.caption("Status view: live recruiting ledger · release 2026-11-19.2")
    st.caption(
        "Current owner records, not the historical forecast shortlist. "
        "MTO is a role-based planning range conditional on further selection, "
        "not a probability or an employer-confirmed number of rounds."
    )
    health = freshness_status(sources)
    st.caption(
        "Supabase checked: " + _stockholm_time(health["generated_at"]) +
        " · Latest stored change: " + _stockholm_time(health["latest_source_change"])
    )
    if health["source_check_stale"]:
        st.warning("Mailbox verification is missing or older than 36 hours. "
                   "Current stored stages are not a fresh inbox check.")
    if keys is None and focus:
        st.warning("Exact requisition filtering is unavailable; showing current active rows.")
    if focus and keys is not None and not rows:
        st.info("No live active record matches the selected exact requisition.")
    elif main:
        st.markdown(f"**Current priorities · {len(main)}**")
        st.dataframe(_table_rows(main), hide_index=True, width="stretch")
    elif not rows:
        st.info("No active, evidence-backed recruitment processes are recorded.")
    if lower:
        with st.expander(f"Other monitored applications · {len(lower)}"):
            st.dataframe(_table_rows(lower), hide_index=True, width="stretch")
    strategic = strategic_rows(sources)
    if not focus and strategic:
        st.markdown("**Strategic conversations · not applications**")
        for item in strategic:
            st.caption(
                f"{item.get('employer')} · {item.get('contact_name') or 'Contact unverified'}"
                " · exploratory discussion; no confirmed vacancy or hiring-stage interview."
            )
    if main:
        with st.expander("Meeting and MTO evidence per opportunity"):
            for item in main:
                st.markdown(f"**{item['employer']} · {item['role']}**")
                st.caption(
                    f"{item['stage']} · {item.get('evidence') or 'No detailed evidence'}"
                )
                st.caption("MTO basis: " + item["mto_note"])
    st.caption(
        "Recruiter screens, attended employer interviews, online assessments and "
        "networking introductions remain distinct. An assessment or scheduled "
        "introductory conversation does not increase completed-meeting counts."
    )


@st.fragment(run_every="5m")
def render_live_stage_board(token: str, focus: str = "") -> None:
    """Live owner reads on entry, manual action and five-minute open-tab refresh."""
    st.button(
        "Refresh hiring stages",
        key="owner_live_stage_refresh",
        help="Recheck saved Supabase recruiting records, not external mailboxes.",
    )
    try:
        sources = fetch_current_pipeline(token)
    except (RuntimeError, TimeoutError, ValueError, PermissionError):
        st.error("Current recruiting records could not be loaded. Old stages are not shown as live.")
        return
    try:
        meetings = fetch_stage_meetings(token)
    except (RuntimeError, TimeoutError, ValueError, PermissionError):
        meetings = None
        st.warning("Meeting attendance could not be verified; counts remain unknown.")
    try:
        keys = fetch_stage_keys(token) if focus else None
    except (RuntimeError, TimeoutError, ValueError, PermissionError):
        keys = None
    render_stage_evidence(sources, meetings, keys, focus)
    st.caption("This section rereads Supabase every five minutes while open.")
