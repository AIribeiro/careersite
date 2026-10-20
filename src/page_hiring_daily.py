"""Owner-only calendar and evidence refresh diagnostics for hiring Analytics."""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st
from site_cms import _request_json, _rest_url

TABLE = "careersite_hiring_daily_rechecks"


def recheck_owner_now(token: str) -> dict:
    """Read/write only via strictly owner-guarded RPC; never use anon access."""
    if not token:
        raise PermissionError("Owner JWT required for hiring refresh.")
    result = _request_json("POST",_rest_url("rpc/careersite_hiring_daily_recheck_v1"),
                           token=token,payload={},timeout=30)
    if not isinstance(result,dict):
        raise RuntimeError("Hiring refresh RPC returned an invalid result.")
    return result


def read_daily_history(token: str, limit: int = 30) -> list[dict]:
    if not token:
        raise PermissionError("Owner JWT required for hiring snapshots.")
    n = max(1,min(60,int(limit)))
    rows = _request_json("GET",_rest_url(
        f"{TABLE}?select=forecast_day,trigger_reason,generated_at,"
        f"scenario,market_context&order=generated_at.desc&limit={n}"
    ),token=token,timeout=18)
    if not isinstance(rows,list):
        raise RuntimeError("Daily hiring recheck history unavailable.")
    return rows


def _days(v, today: date):
    try:
        return (date.fromisoformat(str(v)[:10])-today).days
    except (TypeError,ValueError):
        return None


def render_daily_recheck(history: list[dict], today: date,
                         latest_status: dict | None = None) -> None:
    """Separate clock effects, pipeline effects and external market changes."""
    st.subheader("Daily recalculation · calendar and evidence")
    st.caption("A daily run is scheduled independently of the website; new market "
               "or recruitment evidence is also checked hourly. When the Admin "
               "page is open, it checks immediately. Only changed input states "
               "produce a new audit snapshot.")
    if not history:
        st.warning("No confirmed daily snapshots are readable. "
                   "Do not interpret an absent refresh as an unchanged forecast.")
        return
    recent = history[0]
    report = recent.get("scenario") or {}
    scenario = report.get("leading_stage_scenario") or {}
    context = recent.get("market_context") or {}
    status = str(recent.get("trigger_reason") or "unavailable")
    reason_labels = {
        "initial_daily_baseline":"Initial verified baseline",
        "calendar_day":"Daily clock progression",
        "calendar_and_external_update":"Calendar and external evidence",
        "external_update":"New external observations",
        "recruitment_evidence_update":"Recruiting pipeline changed",
        "timing_window_update":"Timing window reassessed",
        "unchanged":"No material change",
    }
    generated = recent.get("generated_at")
    try:
        seen = datetime.fromisoformat(str(generated).replace("Z","+00:00"))
        local = seen.astimezone(ZoneInfo("Europe/Stockholm")).strftime("%d %b, %H:%M")
    except (TypeError,ValueError):
        local = str(recent.get("forecast_day") or "Unavailable")
    offer = _days(scenario.get("offer_central"),today)
    late = _days(scenario.get("offer_latest"),today)
    a,b,c = st.columns(3)
    a.metric("Days to conditional offer centre",
             str(offer) if offer is not None else "Not established")
    b.metric("Days to latest scenario date",
             str(late) if late is not None else "Not established")
    c.metric("Last recorded check",local)
    st.caption("Latest trigger: "+reason_labels.get(status,status.replace("_"," "))+
               ". Calendar state: "+str(scenario.get("window_state") or "unknown").replace("_"," ")+
               ". Shift from original milestone centre: "+
               str(scenario.get("calendar_shift_days",0))+
               " days. A shift is a planning-rule adjustment, not a measured offer likelihood.")
    if latest_status and latest_status.get("status")=="unchanged":
        st.caption("Most recent immediate recheck found no new evidence; "
                   "the existing audited scenario was retained.")
    if context.get("source_refresh_detected"):
        st.info("New external market observations were detected. They update risk "
                "context, not an uncalibrated numerical probability or offer date.")
    if scenario.get("window_state")=="overdue_reassessed_weekly":
        st.warning("The original central milestone is approaching or has elapsed. "
                   "The scenario was moved in bounded weekly increments; "
                   "no employer confirmation is implied.")
    if scenario.get("window_state")=="expired_requires_new_employer_evidence":
        st.error("The previously observed hiring process no longer supports a "
                 "defensible dated scenario. New verified employer progress is "
                 "needed before restoring a date.")
    with st.expander("Recalculation audit: calendar versus evidence",expanded=False):
        rows = []
        for item in history:
            inner = (item.get("scenario") or {}).get("leading_stage_scenario") or {}
            rows.append({
                "Evaluation day":item.get("forecast_day"),
                "Trigger":reason_labels.get(item.get("trigger_reason"),
                                             item.get("trigger_reason")),
                "Offer centre":inner.get("offer_central"),
                "Offer window latest":inner.get("offer_latest"),
                "Start centre":inner.get("start_central"),
                "Calendar shift (days)":inner.get("calendar_shift_days"),
                "External effect":"Context only, not scored",
            })
        st.dataframe(rows,hide_index=True,width="stretch")
        st.caption("The audit includes mid-day changes to source evidence as "
                   "separate states; date and time represent Stockholm calendar days. "
                   "A difference between daily estimates is not prediction accuracy.")
