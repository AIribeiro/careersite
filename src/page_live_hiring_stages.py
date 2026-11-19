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



def _tone(stage: str) -> str:
    """Presentation-only treatment of documented statuses, not forecast progress."""
    value = stage.casefold()
    if "interview completed" in value or "interview held" in value:
        return "interview"
    if "video assessment completed" in value or "recruiter responded" in value:
        return "engaged"
    if "recruiter" in value or "representation authorized" in value:
        return "engaged"
    if "scheduled" in value or "introduction" in value:
        return "scheduled"
    return "applied"


_LIVE_BOARD_STYLE = """
<style>
/* Self-contained owner hiring board; does not change public portfolio styles. */
.hiring-board{color:#233044;margin:11px 0 13px;border:1px solid #e4e9ef;
 border-radius:15px;background:#fff;overflow:hidden;
 box-shadow:0 7px 22px rgba(27,42,59,.045);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Arial,sans-serif}
.hiring-board *{box-sizing:border-box}
.hiring-board__intro{display:flex;align-items:center;justify-content:space-between;
 gap:12px;padding:17px 20px 15px}
.hiring-board__title{margin:0!important;font-size:1.07rem!important;
 font-weight:770!important;letter-spacing:-.025em;color:#253043!important;line-height:1.2!important}
.hiring-board__subtitle{margin:5px 0 0!important;font-size:.76rem!important;
 line-height:1.45!important;color:#67778a!important}
.hiring-board__counter{white-space:nowrap;border-radius:999px;border:1px solid #e2e8ee;
 color:#57667b;background:#f6f8fa;padding:6px 11px;font-size:.72rem;font-weight:750}
.hiring-board__head,.hiring-board__item{
 display:grid;grid-template-columns:28px minmax(0,1.65fr) minmax(0,1.25fr)
 minmax(100px,.67fr) minmax(96px,.66fr);
 gap:11px;align-items:center;padding-left:18px;padding-right:18px}
.hiring-board__head{background:#f7f9fb;border-top:1px solid #edf0f4;
 border-bottom:1px solid #edf0f4;color:#748193;font-size:.62rem;
 font-weight:800;letter-spacing:.065em;text-transform:uppercase;min-height:35px}
.hiring-board__item{padding-top:12px;padding-bottom:12px;min-height:79px;
 border-bottom:1px solid #eef1f4}
.hiring-board__item:last-child{border-bottom:0}
.hiring-board__num{width:25px;height:25px;display:grid;place-items:center;
 font-size:.72rem;font-weight:760;color:#67768a;border-radius:50%;
 background:#f2f4f7}
.hiring-board__identity{display:flex;align-items:center;gap:10px;min-width:0}
.hiring-board__avatar{width:34px;height:34px;border-radius:9px;
 flex:0 0 34px;display:grid;place-items:center;color:#4f5f72;
 font-size:.72rem;font-weight:800;letter-spacing:-.025em;
 background:#f0f3f6;border:1px solid #e4e8ed}
.hiring-board__name{font-size:.82rem;font-weight:770;line-height:1.28;
 color:#253044;overflow-wrap:anywhere}
.hiring-board__role{font-size:.73rem;color:#748197;line-height:1.32;
 margin-top:3px;overflow-wrap:anywhere}
.hiring-board__minor{font-size:.65rem;color:#8b95a3;margin-top:4px;line-height:1.3}
.hiring-board__review{font-weight:700;color:#9f652f}
.hiring-board__stage{min-width:0}
.hiring-board__chip{display:inline-flex;align-items:flex-start;gap:7px;
 max-width:100%;border-radius:8px;border:1px solid #e7ebef;
 background:#f3f5f7;padding:7px 9px;color:#626e7b;
 font-size:.71rem;line-height:1.32;font-weight:690}
.hiring-board__dot{display:inline-block;flex:0 0 6px;width:6px;height:6px;
 border-radius:50%;background:currentColor;margin-top:4px}
.hiring-board__chip--engaged{color:#34618b;background:#edf4fa;border-color:#e0ebf5}
.hiring-board__chip--interview{color:#236b74;background:#eaf6f4;border-color:#d7eee9}
.hiring-board__chip--scheduled{color:#925d29;background:#fff5e9;border-color:#f6e6d2}
.hiring-board__meeting,.hiring-board__mto{min-width:0;color:#4b5b70;line-height:1.36}
.hiring-board__value{font-size:.83rem;font-weight:770;font-variant-numeric:tabular-nums}
.hiring-board__subvalue{font-size:.69rem;line-height:1.35;color:#8290a0;margin-top:3px}
.hiring-board__mto .hiring-board__value{font-size:.91rem}
.hiring-board__foot{padding:9px 20px 11px;border-top:1px solid #edf0f4;
 color:#8792a0;font-size:.67rem;line-height:1.45;background:#fbfcfd}
.hiring-board--small .hiring-board__intro{padding:13px 17px 12px}
.hiring-board--small .hiring-board__item{min-height:70px}
@media(max-width:920px){
 .hiring-board__head,.hiring-board__item{
 grid-template-columns:24px minmax(0,1.36fr) minmax(0,1.12fr)
 minmax(83px,.62fr) minmax(78px,.6fr);
 gap:8px;padding-left:12px;padding-right:12px}
 .hiring-board__intro{padding:15px 14px}
 .hiring-board__avatar{width:30px;height:30px;flex-basis:30px}
 .hiring-board__identity{gap:7px}
 .hiring-board__chip{padding:6px 7px}
}
@media(max-width:670px){
 .hiring-board__head{display:none}
 .hiring-board__item{
 grid-template-columns:minmax(0,1fr) auto;gap:9px 12px;
 padding:13px 14px;min-height:0}
 .hiring-board__num{display:none}
 .hiring-board__identity{grid-column:1;grid-row:1}
 .hiring-board__stage{grid-column:1 / -1;grid-row:2}
 .hiring-board__meeting{grid-column:1;grid-row:3;
 border-top:1px solid #edf0f4;padding-top:7px}
 .hiring-board__mto{grid-column:2;grid-row:3;
 text-align:right;border-top:1px solid #edf0f4;padding-top:7px}
 .hiring-board__chip{max-width:100%;width:auto}
 .hiring-board__minor{margin-top:2px}
 .hiring-board__foot{padding:9px 14px}
 .hiring-board__intro{padding:13px 14px}
}
@media(prefers-reduced-motion:reduce){.hiring-board *{transition:none!important}}
</style>
"""


def _initials(value: str) -> str:
    words = [word[0].upper() for word in value.split() if word and word[0].isalpha()]
    return "".join(words[:2]) or "•"


def _board_row_html(row: dict, number: int) -> str:
    """One compact, XSS-safe stage summary; no invented credibility percentage."""
    from html import escape
    safe = lambda value: escape(str(value if value is not None else ""), quote=True)
    tone = _tone(str(row.get("stage") or ""))
    review = ('<span class="hiring-board__review"> · priority review due</span>'
              if row.get("rank_needs_review") else "")
    screens = row.get("screens_held")
    interviews = row.get("interviews_held")
    if screens is None or interviews is None:
        evidence_main, evidence_sub = "Unverified", "Meeting ledger unavailable"
    elif screens or interviews:
        evidence_main = f"{screens} screen · {interviews} interview" if screens == 1 else f"{screens} screens · {interviews} interviews"
        evidence_sub = "Attended meetings only"
    else:
        evidence_main, evidence_sub = "None held", "No attended meetings recorded"
    mto = str(row.get("mto") or "—")
    remaining = str(row.get("remaining") or "Unknown")
    last_date = str(row.get("event_date") or "")
    date_line = ("Recorded " + safe(last_date[:10])) if last_date else "Date not verified"
    return (
        '<div class="hiring-board__item" role="listitem">'
        f'<span class="hiring-board__num">{number}</span>'
        '<div class="hiring-board__identity">'
        '<span class="hiring-board__avatar" aria-hidden="true">' + safe(_initials(str(row.get("employer") or ""))) + '</span>'
        '<div><div class="hiring-board__name">' + safe(row.get("employer")) + '</div>'
        '<div class="hiring-board__role">' + safe(row.get("role")) + '</div>'
        '<div class="hiring-board__minor">' + safe(row.get("band")) + review + '</div>'
        '</div></div>'
        '<div class="hiring-board__stage">'
        '<span class="hiring-board__chip hiring-board__chip--' + tone + '">'
        '<span class="hiring-board__dot" aria-hidden="true"></span>'
        + safe(row.get("stage") or "Not verified") + '</span>'
        '<div class="hiring-board__minor">' + date_line + '</div></div>'
        '<div class="hiring-board__meeting">'
        '<div class="hiring-board__value">' + safe(evidence_main) + '</div>'
        '<div class="hiring-board__subvalue">' + safe(evidence_sub) + '</div></div>'
        '<div class="hiring-board__mto">'
        '<div class="hiring-board__value">' + safe(mto) + '</div>'
        '<div class="hiring-board__subvalue">' + safe(remaining) + ' remaining</div></div>'
        '</div>'
    )


def stage_board_html(rows: list[dict], *, title: str = "Where current opportunities stand",
                     small: bool = False) -> str:
    """Original compact comparison aesthetic with current stage evidence."""
    from html import escape
    count = len(rows)
    header = (
        '<div class="hiring-board__intro"><div>'
        '<h3 class="hiring-board__title">' + escape(title, quote=True) + '</h3>'
        '<p class="hiring-board__subtitle">Verified stages, completed meetings and conditional MTO.</p>'
        '</div><span class="hiring-board__counter">' +
        f'{count} {"process" if count == 1 else "processes"}</span></div>'
    )
    columns = ('<div class="hiring-board__head" aria-hidden="true">'
               '<span>#</span><span>Company &amp; role</span><span>Current stage</span>'
               '<span>Meetings held</span><span>MTO</span></div>')
    label = escape(title, quote=True)
    return (
        _LIVE_BOARD_STYLE
        + '<section class="hiring-board' + (' hiring-board--small' if small else '') +
        '" aria-label="' + label + '">'
        + header + columns
        + '<div role="list" aria-label="' + label + '">'
        + "".join(_board_row_html(r, i) for i, r in enumerate(rows, 1))
        + '</div><div class="hiring-board__foot">'
        'MTO = estimated total meetings to a possible offer, not a likelihood. '
        'Recruiter screenings are identified separately from employer interviews.'
        '</div></section>'
    )


def render_stage_evidence(sources: dict, meetings: list[dict] | None,
                          keys: dict[str, str] | None = None,
                          focus: str = "") -> None:
    rows = stage_display_rows(sources, meetings, keys, focus)
    main = [r for r in rows if r["band"] == "P1"]
    lower = [r for r in rows if r["band"] != "P1"]
    heading, action = st.columns([5, 1.15], vertical_alignment="center")
    with heading:
        st.subheader("Hiring stages & meetings to offer")
    with action:
        st.button("Refresh", key="owner_live_stage_refresh",
                  help="Re-read Supabase records; does not scan email.",
                  use_container_width=True)
    health = freshness_status(sources)
    st.caption(
        "Current Supabase register · " +
        _stockholm_time(health["generated_at"]) +
        " · Stored evidence updated " + _stockholm_time(health["latest_source_change"])
    )
    if health["source_check_stale"]:
        st.caption(
            "External mailbox check is not recent; these are verified stored records, "
            "not a fresh email scan."
        )
    if keys is None and focus:
        st.caption("Exact requisition filtering unavailable; current active roles shown.")
    if focus and keys is not None and not rows:
        st.info("No active role matches this requisition.")
    elif main:
        st.markdown(stage_board_html(main), unsafe_allow_html=True)
    elif not rows:
        st.info("No active, evidence-backed recruitment processes recorded.")

    if lower:
        with st.expander(f"Other monitored applications · {len(lower)}", expanded=False):
            st.markdown(stage_board_html(lower, title="Other monitored applications", small=True),
                        unsafe_allow_html=True)

    strategic = strategic_rows(sources)
    if not focus and strategic:
        with st.container(border=True):
            st.markdown("**Strategic conversations**")
            for item in strategic:
                from html import escape
                employer = escape(str(item.get("employer") or ""), quote=True)
                contact = escape(str(item.get("contact_name") or "Contact unverified"), quote=True)
                st.markdown(
                    f'<span style="font-weight:700;font-size:.88rem;">{employer}</span>'
                    f'<span style="font-size:.79rem;color:#6f7c89;"> · {contact}'
                    ' · Exploratory contact, no confirmed vacancy or hiring interview</span>',
                    unsafe_allow_html=True,
                )
    if main:
        with st.expander("Meeting evidence and estimated MTO assumptions", expanded=False):
            for item in main:
                st.markdown(f"**{item['employer']} · {item['role']}**")
                st.caption(
                    f"{item['stage']} · {item.get('evidence') or 'No detailed evidence'}"
                )
                st.caption("MTO basis: " + item["mto_note"])
    st.caption(
        "A video assessment, invitation or networking introduction does not "
        "increase the number of completed hiring meetings."
    )


@st.fragment(run_every="5m")
def render_live_stage_board(token: str, focus: str = "") -> None:
    """Live owner reads on entry, manual action and five-minute open-tab refresh."""
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
