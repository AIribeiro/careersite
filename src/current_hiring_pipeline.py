"""Owner-only current recruiting status, independent of the legacy forecast snapshot.

The source tables distinguish formal applications from exploratory employer access.
No networking interaction is promoted to an interview, vacancy or offer.
"""
from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from site_cms import _request_json, _rest_url


def fetch_current_pipeline(token: str) -> dict:
    """One owner-gated RPC: private priority/map tables are never read via REST."""
    if not token:
        raise ValueError("Owner access required")
    response = _request_json(
        "POST",
        _rest_url("rpc/careersite_owner_current_hiring_pipeline_v1"),
        token=token,
        payload={},
        timeout=20,
    )
    if not isinstance(response, dict) or not all(
        isinstance(response.get(key), list)
        for key in ("opportunities", "priorities", "statuses", "strategic")
    ):
        raise RuntimeError("Current owner-only hiring summary is unavailable")
    return response


STAGE_LABELS = {
    "video_assessment_completed": "Video assessment completed",
    "intro_meeting_scheduled": "Introduction scheduled · not yet held",
    "ats_received": "Application received",
    "applied_no_interview": "Application · no interview confirmed",
    "qualified_recruiter_client_status_unknown": "Recruiter qualified · client decision unverified",
    "representation_authorized_client_submission_unknown": "Representation authorized · submission unverified",
    "exploratory_recruiter_outreach": "Exploratory recruiter outreach",
    "applied_geography_mismatch": "Application · location constraint",
    "application_dormant": "Application · no recent response",
    "application_eligibility_unknown": "Application · eligibility unverified",
}


def current_rows(sources: dict) -> list[dict]:
    """Select the newest review per exact requisition; exclude dormant and closed."""
    opportunities = {str(row.get("id")): row for row in sources["opportunities"]}
    statuses = {
        str(row.get("source_ref")): row for row in sources["statuses"]
        if row.get("source_type") == "managed"
    }
    seen = set()
    rows = []
    for review in sources["priorities"]:
        key = str(review.get("opportunity_id"))
        if key in seen:
            continue
        seen.add(key)
        op = opportunities.get(key)
        if not op or str(op.get("outcome") or "").lower() in {
            "rejected", "closed", "withdrawn", "offer_accepted", "hired"
        }:
            continue
        band = str(review.get("priority_band") or "")
        if band not in {"P1", "P2", "P3"} or review.get("rank_position") is None:
            continue
        status = statuses.get(key, {})
        if str(status.get("status") or "").lower() in {
            "ignored", "rejected", "withdrawn", "closed"
        }:
            continue
        stage_key = str(review.get("pipeline_state") or "")
        stage = STAGE_LABELS.get(stage_key, stage_key.replace("_", " ").capitalize())
        if status.get("status") == "recruiter_replied" and stage_key in {
            "ats_received", "applied_no_interview"
        }:
            stage = "Recruiter replied · no interview confirmed"
        if status.get("status") == "recruiter_replied" and stage_key == "video_assessment_completed":
            stage = "Video assessment completed · recruiter responded"
        rows.append({
            "id": key,
            "employer": str(op.get("employer") or ""),
            "role": str(op.get("role_title") or ""),
            "band": band,
            "rank": int(review["rank_position"]),
            "stage": stage,
            "evidence": str(status.get("status_note") or review.get("evidence_note") or ""),
            "event_date": str(status.get("status_on") or op.get("application_date") or ""),
            "next_action": str(review.get("next_action") or ""),
        })
    return sorted(rows, key=lambda row: (
        {"P1": 0, "P2": 1, "P3": 2}.get(row["band"], 3),
        row["rank"],
    ))


def strategic_rows(sources: dict) -> list[dict]:
    """Real executive contact with no verified vacancy stays outside hiring counts."""
    return [
        row for row in sources["strategic"]
        if row.get("access_status") == "direct_executive_conversation"
        and row.get("hiring_signal") == "exploratory_executive_interest_no_open_role"
    ]


_STYLE = """
<style>
.current-pipeline{display:grid;gap:8px;margin:12px 0 16px}
.current-pipeline__row{display:grid;grid-template-columns:1.4fr 1.2fr 1.7fr;gap:14px;
padding:13px 15px;border:1px solid rgba(120,136,155,.22);border-radius:12px;
background:rgba(130,150,170,.035);align-items:start}
.current-pipeline__name{font-weight:750;font-size:.91rem;line-height:1.25}
.current-pipeline__role{font-size:.78rem;opacity:.8;margin-top:3px}
.current-pipeline__stage{font-weight:650;font-size:.8rem;line-height:1.35}
.current-pipeline__meta{font-size:.72rem;opacity:.72;margin-top:5px}
.current-pipeline__evidence{font-size:.76rem;opacity:.85;line-height:1.42}
.current-pipeline__next{font-size:.75rem;line-height:1.4;margin-top:6px;opacity:.8}
.current-pipeline__tag{font-size:.69rem;font-weight:700;letter-spacing:.04em;opacity:.75}
@media(max-width:760px){
.current-pipeline__row{grid-template-columns:minmax(0,1fr);gap:8px;padding:12px}
.current-pipeline__evidence{max-width:100%;overflow-wrap:anywhere}
}
</style>
"""


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _short(value: object, size: int = 185) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= size else text[:size - 1].rsplit(" ", 1)[0] + "…"


def _row_html(row: dict) -> str:
    when = _safe(row.get("event_date"))
    meta = ("Recorded " + when) if when else "Date unverified"
    return (
        '<div class="current-pipeline__row">'
        '<div><div class="current-pipeline__name">' + _safe(row["employer"]) +
        '</div><div class="current-pipeline__role">' + _safe(row["role"]) +
        '</div><div class="current-pipeline__meta">' + _safe(row["band"]) + " priority</div></div>"
        '<div><div class="current-pipeline__stage">' + _safe(row["stage"]) +
        '</div><div class="current-pipeline__meta">' + meta + '</div></div>'
        '<div><div class="current-pipeline__evidence">' + _safe(_short(row["evidence"])) +
        '</div><div class="current-pipeline__next"><strong>Next:</strong> ' +
        _safe(_short(row["next_action"], 170)) + '</div></div></div>'
    )


def _render_rows(rows: list[dict]) -> None:
    if rows:
        st.markdown(
            _STYLE + '<div class="current-pipeline">' +
            "".join(_row_html(row) for row in rows) + '</div>',
            unsafe_allow_html=True,
        )


def render_current_pipeline(sources: dict) -> bool:
    """Return True when at least one current pipeline or strategic row exists."""
    rows = current_rows(sources)
    strategic = strategic_rows(sources)
    st.subheader("Current opportunities and conversations")
    st.caption(
        "Live owner-only Supabase records. Stages follow recorded employer evidence; "
        "priority is a planning judgement, not an offer probability. "
        "Exploratory contacts do not count as applications or interviews."
    )
    if strategic:
        st.markdown("**Strategic conversations · no advertised vacancy confirmed**")
        for entry in strategic:
            st.markdown(
                '<div class="current-pipeline__row" style="display:block">'
                '<div class="current-pipeline__name">' + _safe(entry.get("employer")) +
                ' · exploratory executive discussion</div>'
                '<div class="current-pipeline__meta">Contact: ' +
                _safe(entry.get("contact_name") or "Unverified") +
                ' · Conversation proposed, booking not verified</div>'
                '<div class="current-pipeline__evidence" style="margin-top:8px">' +
                _safe(_short(entry.get("activity_status"), 290)) + '</div>'
                '<div class="current-pipeline__next"><strong>Next:</strong> ' +
                _safe(_short(entry.get("next_action"), 230)) +
                '</div></div>',
                unsafe_allow_html=True,
            )
    p1 = [row for row in rows if row["band"] == "P1"]
    if p1:
        st.markdown(f"**Active priorities · {len(p1)} P1 processes**")
        _render_rows(p1)
    other = [row for row in rows if row["band"] in {"P2", "P3"}]
    if other:
        with st.expander(f"Other monitored applications · {len(other)}"):
            _render_rows(other)
    if not rows and not strategic:
        st.info("No recent, evidence-backed active opportunity was found in the current review.")
    return bool(rows or strategic)
