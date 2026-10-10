"""Cross-channel attribution reconciliation using owner-only, aggregate SQL."""
from __future__ import annotations
import json
from urllib import error,request

import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_owner import owner_rpc_headers


def fetch_attribution_integrity(window: str) -> dict:
    if window in ("today","last_hour"):
        args={"p_days":30,"p_window":window}
    elif window.endswith("d") and window[:-1].isdigit() and int(window[:-1]) in (7,30,90,365):
        args={"p_days":int(window[:-1]),"p_window":"days"}
    else:
        raise ValueError("Unsupported attribution window.")
    req=request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_attribution_integrity_v1",
        data=json.dumps(args).encode("utf-8"),
        method="POST",headers=owner_rpc_headers())
    try:
        with request.urlopen(req,timeout=25) as response:
            data=json.load(response)
    except (error.HTTPError,error.URLError,TimeoutError) as exc:
        raise RuntimeError("Attribution reconciliation could not be refreshed.") from exc
    if not isinstance(data,dict) or not isinstance(data.get("overview"),dict):
        raise RuntimeError("Unexpected cross-channel attribution response.")
    return data


def _n(d: dict, key: str) -> int:
    return int(d.get(key) or 0)


def render_attribution_integrity(window: str) -> None:
    st.subheader("Attribution integrity · all channels")
    st.caption(
        "CV, LinkedIn, Facebook, WhatsApp, X, other social and unattributed visits "
        "are reconciled as mutually exclusive first-touch browser sessions. "
        "Role and campaign tags describe those same sessions; they are not additional visits."
    )
    try:
        data=fetch_attribution_integrity(window)
    except (RuntimeError,PermissionError,ValueError):
        st.warning("Cross-channel reconciliation is temporarily unavailable; other analytics remain available.")
        return
    o=data["overview"]
    columns=st.columns(4)
    columns[0].metric("Recorded content sessions",_n(o,"content_sessions"),
                      help="Disjoint browser-tab sessions with a page or article event. Not unique people.")
    columns[1].metric("Quality-eligible (V5)",_n(o,"quality_eligible"),
                      help="V5 sessions excluding explicit tests, telemetry-only and suspected automation.")
    columns[2].metric("Suspected preview batches (V5)",_n(o,"suspected_preview_bursts"),
                      help="Independent-session bursts across three different pages within 30 seconds; distinct from other automation.")
    columns[3].metric("Legacy / ungraded",_n(o,"legacy_ungraded"),
                      help="Content sessions predating V5-quality tracking; NOT assessed as human or bot.")
    st.caption(
        f"{_n(o,'telemetry_only')} telemetry-only sessions and "
        f"{_n(o,'suspected_automation_other')} other V5 signature-based suspected-automation "
        "sessions are also excluded from qualified counts. "
        "Suspicious classifications are diagnostic, not verified robot identities."
    )

    st.markdown("**Reconciled sources**")
    channels=data.get("channels") or []
    rows=[{
        "First-touch channel":p.get("channel"),
        "Content sessions":_n(p,"content_sessions"),
        "Quality-eligible":_n(p,"quality_eligible"),
        "Legacy / ungraded":_n(p,"legacy_ungraded"),
        "Suspected bursts":_n(p,"preview_burst_sessions"),
        "Other suspected":_n(p,"other_suspected_automation"),
        "Navigation views":_n(p,"navigation_page_views"),
        "Article views":_n(p,"article_views"),
        "Telemetry only":_n(p,"telemetry_only"),
    } for p in channels if _n(p,"recorded_sessions")]
    if rows:
        st.dataframe(rows,hide_index=True,width="stretch")
    else:
        st.info("No recorded traffic in this window.")
    st.caption(
        "Navigation views exclude article-page wrapper events. Article reads are counted "
        "by their own event type. Content-session totals and quality categories reconcile "
        "across mutually exclusive first-touch sources."
    )

    st.markdown("**Campaign and role detail**")
    campaign_data=data.get("campaigns") or []
    if campaign_data:
        st.dataframe([{
            "Parent channel":x.get("channel"),
            "Campaign / role label":x.get("campaign"),
            "Content sessions":_n(x,"content_sessions"),
            "Quality-eligible":_n(x,"quality_eligible"),
            "Legacy / ungraded":_n(x,"legacy_ungraded"),
            "Suspected automation":_n(x,"flagged_sessions"),
        } for x in campaign_data],hide_index=True,width="stretch")
    st.caption(
        "UTM campaign takes precedence over the older 'role' parameter for the "
        "campaign label. Multiple source variants with the same campaign are kept "
        "in their own parent-channel cohorts; summing channel and campaign tables "
        "would count the same sessions twice."
    )

    with st.expander("Counting checks · source conflicts, unknown tags and article overlap"):
        checks=[
            ("Unattributed sessions with an external referrer",_n(o,"untagged_with_referrer"),
             "An untagged referral is not proof of direct navigation; it remains unattributed."),
            ("Explicit source ↔ UTM source conflicts",_n(o,"source_conflicts"),
             "The explicitly tagged source wins. The contradictory UTM value is not another visit."),
            ("Role ↔ UTM campaign conflicts",_n(o,"campaign_conflicts"),
             "Conflicting labels represent a single session; do not sum them."),
            ("Article page-wrapper events",_n(o,"article_page_wrappers"),
             "Tracked page_view events for an article also tracked via article_view; excluded from navigation views."),
            ("Excluded explicit test sessions",_n(o,"test_sessions"),
             "Source=application + role=Test is excluded from traffic reports."),
        ]
        st.dataframe([{"Check":label,"Observed":n,"Interpretation":why}
            for label,n,why in checks],hide_index=True,width="stretch")
        bad=data.get("unexpected_tags") or []
        if bad:
            st.markdown("**Unrecognized source strings (kept separate from unattributed)**")
            st.dataframe([{"Recorded tag":str(x.get("raw_first_source"))[:100],
                           "Session IDs":_n(x,"sessions")} for x in bad],
                         hide_index=True,width="stretch")
        st.caption(
            "V5 quality assessment begins when tracking V5 becomes available. "
            "Exact browser signatures are used only temporarily inside the owner-only "
            "query to detect suspicious bursts; no signatures, visitor IDs, or IPs "
            "are returned. Legacy recordings cannot be reliably reclassified."
        )
