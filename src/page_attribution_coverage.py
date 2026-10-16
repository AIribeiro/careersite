"""Owner-only, post-activation source-evidence and UTM-medium reporting."""
from __future__ import annotations

import json
from urllib import error, request

import altair as alt
import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_owner import owner_rpc_headers


def fetch_attribution_coverage(days: int) -> dict:
    if days not in (7, 30, 90, 365):
        raise ValueError("Unsupported reporting period.")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_attribution_coverage_v1",
        data=json.dumps({"p_days": days}).encode("utf-8"),
        headers=owner_rpc_headers(),
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=25) as response:
            data = json.load(response)
    except (error.URLError, error.HTTPError, TimeoutError) as exc:
        raise RuntimeError("Source coverage could not be refreshed.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("overview"), dict):
        raise RuntimeError("Unexpected coverage report response.")
    return data


def _pct(value: object) -> str:
    return f"{float(value):.1f}%" if value is not None else "—"


def render_attribution_coverage() -> None:
    st.title("Attribution quality")
    st.caption(
        "Evidence of where new portfolio visits originate, measured only from "
        "the start of the improved tracking. Source tags, external referrers "
        "and unresolved origins remain separate."
    )
    days = st.segmented_control(
        "Coverage period",
        [7, 30, 90, 365],
        format_func=lambda v: f"{v} days",
        default=30,
        key="admin_attribution_coverage_days",
        width="stretch",
    ) or 30

    try:
        report = fetch_attribution_coverage(int(days))
    except (ValueError, RuntimeError, PermissionError):
        st.warning("Attribution coverage is temporarily unavailable. Other reports are unaffected.")
        return

    o = report["overview"]
    total = int(o.get("sessions") or 0)
    tagged = int(o.get("tagged") or 0)
    referred = int(o.get("referrer_only") or 0)
    unknown = int(o.get("unknown") or 0)
    started_at = str(report.get("monitoring_started_at") or "")[:16].replace("T", " ")
    st.caption(f"Forward monitoring started: {started_at} UTC. Earlier sessions are excluded.")

    a, b, c = st.columns(3, gap="medium")
    a.metric("Identifiable source", _pct(o.get("identifiable_pct")),
             help="Explicit channel tag or external referrer, once per first content session.")
    b.metric("Explicit source tags", f"{tagged:,}",
             help="Sessions with a declared source at their first recorded content event.")
    c.metric("Still unknown", f"{unknown:,}",
             help="No source tag or usable external referrer on the first content event.")

    if total == 0:
        st.info(
            "No eligible new content sessions yet. The monitoring window begins "
            "with the database release; historical unknown sessions were not recoded."
        )
        return

    st.markdown(
        f"**Coverage:** {tagged:,} explicitly tagged, {referred:,} referred without "
        f"a campaign tag, and {unknown:,} unresolved out of {total:,} new content "
        "sessions. These groups are mutually exclusive."
    )

    st.subheader("How attribution coverage is developing")
    raw = report.get("daily") or []
    daily = [
        {
            "Day": str(row.get("day") or ""),
            "Tagged": int(row.get("tagged") or 0),
            "Referrer-only": int(row.get("referrer_only") or 0),
            "Unknown": int(row.get("unknown") or 0),
            "Sessions": int(row.get("sessions") or 0),
            "Coverage (%)": row.get("identifiable_pct"),
        } for row in raw if isinstance(row, dict)
    ]
    data = [r for r in daily if r["Sessions"] > 0]
    if data:
        st.altair_chart(
            alt.Chart(alt.Data(values=data))
            .transform_fold(["Tagged", "Referrer-only", "Unknown"],
                            as_=["Evidence", "Sessions by evidence"])
            .mark_bar()
            .encode(
                x=alt.X("Day:N", title=None),
                y=alt.Y("Sessions by evidence:Q", title="New content sessions", stack="zero"),
                color=alt.Color("Evidence:N", title="Source evidence"),
                tooltip=["Day:N", "Evidence:N",
                         alt.Tooltip("Sessions by evidence:Q", format=",")],
            ).properties(height=260),
            width="stretch",
        )
        if len(data) >= 2:
            st.altair_chart(
                alt.Chart(alt.Data(values=[
                    {"Day":r["Day"],"Coverage (%)":r["Coverage (%)"]}
                    for r in data if r["Coverage (%)"] is not None
                ])).mark_line(point=True)
                .encode(
                    x=alt.X("Day:N",title=None),
                    y=alt.Y("Coverage (%):Q",title="Identifiable source (%)",
                            scale=alt.Scale(domain=[0,100])),
                    tooltip=["Day:N",alt.Tooltip("Coverage (%):Q",format=".1f")],
                ).properties(height=170),
                width="stretch",
            )
        if total < 20 or len(data) < 3:
            st.caption(
                "Early sample: the apparent trend is unstable. Wait for more "
                "new sessions and multiple reporting days before assessing change."
            )

    st.subheader("Tracking completeness of tagged visits")
    medium_pct = o.get("tagged_with_medium_pct")
    campaign_pct = o.get("tagged_with_campaign_pct")
    left, right = st.columns(2)
    left.metric("Medium recorded", _pct(medium_pct),
                help="utm_medium present among explicitly tagged content sessions.")
    right.metric("Campaign recorded", _pct(campaign_pct),
                 help="utm_campaign present among explicitly tagged content sessions.")
    if tagged:
        st.caption(
            f"{int(o.get('medium_count') or 0):,} of {tagged:,} tagged sessions have "
            f"utm_medium; {int(o.get('campaign_count') or 0):,} have utm_campaign. "
            "A direct visit does not require campaign tags."
        )
    if int(o.get("source_conflicts") or 0):
        st.warning(
            f"{int(o['source_conflicts'])} sessions contain conflicting explicit "
            "source and utm_source labels. Check the distributed URLs."
        )
    sources = report.get("sources") or []
    with st.expander("Verified source labels and measurement rules", expanded=False):
        st.caption(
            "The source is classified from the first recorded content event in "
            "each post-activation session. No user identities are inferred. "
            "Explicit test traffic is excluded. Referrer-only evidence identifies "
            "the referring host, not an exact social campaign. "
            "Telemetry-only sessions and historical sessions are excluded."
        )
        if sources:
            st.dataframe(
                [{"Declared source": r.get("source"), "Content sessions":r.get("sessions")}
                 for r in sources],
                hide_index=True, width="stretch",
            )
        st.caption(
            "Percentage changes require comparable observation windows with "
            "sufficient new sessions. This view does not redistribute unknown "
            "traffic across known channels."
        )
