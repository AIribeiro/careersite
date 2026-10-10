"""Owner-only, non-additive CV source / role attribution reconciliation."""
from __future__ import annotations

import json
from urllib import error, request

import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_owner import owner_rpc_headers


def fetch_cv_attribution_audit(window: str) -> dict:
    if window == "today":
        payload = {"p_days":30, "p_window":"today"}
    elif window == "last_hour":
        payload = {"p_days":30, "p_window":"last_hour"}
    elif window.endswith("d") and window[:-1].isdigit() and int(window[:-1]) in {7,30,90,365}:
        payload = {"p_days":int(window[:-1]), "p_window":"days"}
    else:
        raise ValueError("Unsupported attribution audit window.")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_cv_attribution_audit_v1",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=owner_rpc_headers(),
    )
    try:
        with request.urlopen(req,timeout=20) as response:
            data=json.load(response)
    except (error.HTTPError,error.URLError,TimeoutError) as exc:
        raise RuntimeError("CV attribution audit is temporarily unavailable.") from exc
    if not isinstance(data,dict) or not isinstance(data.get("overview"),dict):
        raise RuntimeError("Unexpected attribution audit response.")
    return data


def render_cv_attribution_audit(window: str) -> None:
    st.subheader("CV & role attribution audit")
    st.caption(
        "One page-view event belongs to one source. Role and UTM labels are dimensions "
        "of the same event, not additional views. Recorded views are not necessarily people."
    )
    try:
        audit=fetch_cv_attribution_audit(window)
    except (RuntimeError,PermissionError,ValueError):
        st.warning("Attribution reconciliation is temporarily unavailable; other reports remain accessible.")
        return

    overview=audit["overview"]
    raw=int(overview.get("cv_page_views") or 0)
    suspect=int(overview.get("suspect_scan_views") or 0)
    residual=max(0,raw-suspect)
    cv_sessions=int(overview.get("cv_sessions") or 0)
    overlap=int(overview.get("cv_utm_source_same_view") or 0)
    role_overlap=int(overview.get("cv_with_role") or 0)

    a,b,c,d=st.columns(4)
    a.metric("CV-tagged page views",raw,help="Recorded events with canonical source=cv. Not CV file downloads.")
    b.metric("Distinct CV session IDs",cv_sessions,help="A browser may create many session IDs. This is not a count of people.")
    c.metric("Suspected preview / scan views",suspect,help="Three different pages and session IDs from the same coarse browser signature within 30 seconds.")
    d.metric("Other CV-tagged views",residual,help="Not matched by the three-page burst screen; these are not verified human visits.")
    if raw:
        st.caption(
            f"{suspect} of {raw} CV-tagged views ({suspect/raw:.0%}) match a repeated "
            "Home–Certifications–Presence-like independent-session burst. "
            "Raw page-view totals remain unchanged; the flagged events should not be counted as verified recruiter attention."
        )
    if overlap:
        st.info(
            f"{overlap} of the CV page views also carry utm_source=cv. "
            "They are the SAME events—not another source of visits. "
            "CV source and role tables must never be added together."
        )
    if role_overlap:
        st.caption(f"{role_overlap} CV-tagged page views also have a role label. They remain one view each.")
    else:
        st.caption("No CV-tagged page-view event in this reporting window has a separate role label.")

    left,right=st.columns(2)
    with left:
        pages=audit.get("cv_pages") or []
        if pages:
            st.markdown("**CV-tagged pages · raw versus suspected preview activity**")
            st.dataframe([
                {"Page":p.get("page"),"Raw views":int(p.get("raw_views") or 0),
                 "Suspected preview":int(p.get("suspect_scan_views") or 0),
                 "Other recorded views":int(p.get("other_views") or 0)}
                for p in pages
            ],hide_index=True,width="stretch")
    with right:
        roles=audit.get("roles") or []
        st.markdown("**Role-attributed views · across all sources**")
        if roles:
            st.dataframe([
                {"Role / campaign":p.get("role"),"Page views":int(p.get("page_views") or 0),
                 "Distinct session IDs":int(p.get("sessions") or 0)}
                for p in roles
            ],hide_index=True,width="stretch")
        else:
            st.caption("No separately tagged roles in the selected window.")
    st.caption(
        "The role table is a different breakdown of page views, not an incremental "
        "audience. Explicit source=application + role=Test traffic is excluded. "
        "Suspected preview classification is based on correlated timestamps, pages and "
        "browser properties; it is a conservative diagnostic, not proof of automation."
    )
