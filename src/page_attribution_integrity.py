"""Cross-channel attribution reconciliation using owner-only, aggregate SQL."""
from __future__ import annotations
import json
from urllib import error,request

import altair as alt
import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_public import public_analytics_rpc_headers


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
        method="POST",headers=public_analytics_rpc_headers())
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


def _pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "—"
    return f"{100 * numerator / denominator:.0f}%"


def _source_quality_rows(channels: list[dict]) -> list[dict]:
    """Keep first-touch channel cohorts disjoint and normalize chart labels."""
    rows = []
    for source in channels:
        total = _n(source, "content_sessions")
        if not total:
            continue
        quality = _n(source, "quality_eligible")
        rows.append({
            "Channel": str(source.get("channel") or "Unattributed / unknown"),
            "Content sessions": total,
            "Quality-eligible": quality,
            "Quality share": 100 * quality / total,
            "Suspected": (_n(source, "preview_burst_sessions")
                          + _n(source, "other_suspected_automation")),
        })
    return sorted(rows, key=lambda row: (-row["Content sessions"], row["Channel"]))


def _source_classifications(channels: list[dict]) -> list[dict]:
    """Disjoint V5 quality categories; preserve unexplained residuals explicitly."""
    parts = (
        ("Quality-eligible", "quality_eligible"),
        ("Suspected preview", "preview_burst_sessions"),
        ("Other suspected", "other_suspected_automation"),
        ("Legacy / ungraded", "legacy_ungraded"),
    )
    rows = []
    for source in channels:
        total = _n(source, "content_sessions")
        if not total:
            continue
        name = str(source.get("channel") or "Unattributed / unknown")
        classified = 0
        for label, field in parts:
            count = _n(source, field)
            classified += count
            if count:
                rows.append({"Channel": name, "Classification": label, "Sessions": count,
                             "Content sessions": total})
        residual = max(0, total - classified)
        if residual:
            rows.append({"Channel": name, "Classification": "Unclassified",
                         "Sessions": residual, "Content sessions": total})
    return rows


def _campaign_quality_rows(campaigns: list[dict]) -> list[dict]:
    rows = []
    for item in campaigns:
        total = _n(item, "content_sessions")
        if total <= 0:
            continue
        qualified = _n(item, "quality_eligible")
        rows.append({
            "Source / campaign": (
                f"{item.get('channel') or 'Unattributed'} · "
                f"{item.get('campaign') or 'untagged'}"
            ),
            "Content sessions": total,
            "Quality-eligible": qualified,
            "Quality share": 100 * qualified / total,
        })
    return sorted(rows, key=lambda r: (-r["Quality-eligible"], -r["Content sessions"]))


def _attribution_readout(overview: dict, channels: list[dict], campaigns: list[dict]) -> None:
    """Observations calculated from the selected window, never generic AI claims."""
    total = _n(overview, "content_sessions")
    eligible = _n(overview, "quality_eligible")
    preview = _n(overview, "suspected_preview_bursts")
    other = _n(overview, "suspected_automation_other")
    st.markdown("#### What the traffic quality tells us")
    if not total:
        st.info("No content sessions recorded for this period. Widen the reporting window.")
        return

    st.markdown(
        f"**Qualified attention:** {_pct(eligible, total)} of content sessions meet "
        f"the V5 quality rules. **{preview + other}** sessions are suspected automation "
        "under diagnostic heuristics; these are not verified bot identities."
    )
    source_rows = _source_quality_rows(channels)
    unknown = next((r for r in source_rows
                    if r["Channel"].casefold() in (
                        "unattributed / unknown", "direct/unknown", "direct / unknown")), None)
    if unknown and unknown["Content sessions"]:
        st.markdown(
            f"**Attribution gap:** {unknown['Content sessions']} sessions have no "
            f"known first-touch channel, and {_pct(unknown['Suspected'], unknown['Content sessions'])} "
            "of those are flagged as suspected automation. Do not interpret unattributed "
            "traffic as confirmed direct readership."
        )

    tagged = [r for r in source_rows
              if r is not unknown and r["Quality-eligible"] > 0]
    if tagged:
        strongest = max(tagged, key=lambda r: (r["Quality-eligible"], r["Quality share"]))
        st.markdown(
            f"**Strongest tagged source by eligible volume:** {strongest['Channel']} "
            f"({strongest['Quality-eligible']} of {strongest['Content sessions']} "
            "content sessions). This is a small observational cohort, not evidence "
            "that the channel will perform equally well next week."
        )

    campaign_rows = _campaign_quality_rows(campaigns)
    tagged_campaigns = [r for r in campaign_rows
                        if r["Quality-eligible"] > 0
                        and "untagged" not in r["Source / campaign"].lower()]
    if tagged_campaigns:
        lead = tagged_campaigns[0]
        st.caption(
            f"Leading tagged campaign cohort: {lead['Source / campaign']} "
            f"({lead['Quality-eligible']} quality-eligible of {lead['Content sessions']} "
            "sessions). Campaign and channel views are two cuts of the same sessions."
        )


def _render_source_charts(channels: list[dict]) -> None:
    quality_rows = _source_quality_rows(channels)
    if not quality_rows:
        st.info("No content sessions are available for source comparison.")
        return

    order = [r["Channel"] for r in quality_rows]
    parts = _source_classifications(channels)
    st.markdown("#### Where the qualified sessions come from")
    left, right = st.columns([1.4, 1])
    with left:
        st.caption("Source volume, split into mutually exclusive quality categories")
        chart = alt.Chart(alt.Data(values=parts)).mark_bar().encode(
            y=alt.Y("Channel:N", sort=order, title=None),
            x=alt.X("sum(Sessions):Q", title="Content sessions",
                    axis=alt.Axis(tickMinStep=1)),
            color=alt.Color(
                "Classification:N",
                scale=alt.Scale(
                    domain=["Quality-eligible", "Suspected preview",
                            "Other suspected", "Legacy / ungraded", "Unclassified"],
                    range=["#39785f", "#d49b58", "#c46f63", "#9a9b9e", "#6f87a5"],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=["Channel:N", "Classification:N",
                     alt.Tooltip("sum(Sessions):Q", title="Sessions", format=",")],
        ).properties(height=max(210, len(order) * 43))
        st.altair_chart(chart, use_container_width=True)
    with right:
        st.caption("Share of sessions meeting V5 quality rules")
        rates = alt.Chart(alt.Data(values=quality_rows)).mark_bar(
            cornerRadiusEnd=5, color="#39785f"
        ).encode(
            y=alt.Y("Channel:N", sort=order, title=None),
            x=alt.X("Quality share:Q", title="Quality-eligible (%)",
                    scale=alt.Scale(domain=[0, 100])),
            tooltip=["Channel:N",
                     alt.Tooltip("Quality-eligible:Q", format=","),
                     alt.Tooltip("Content sessions:Q", format=","),
                     alt.Tooltip("Quality share:Q", format=".1f", title="Share (%)")],
        ).properties(height=max(210, len(order) * 43))
        st.altair_chart(rates, use_container_width=True)
    st.caption(
        "Rates have different sample sizes; use the counts in tooltips before "
        "comparing channels. 'Quality-eligible' is a reporting classification, "
        "not a verified human, employer or recruiter identity."
    )


def _render_campaign_chart(campaigns: list[dict]) -> None:
    rows = _campaign_quality_rows(campaigns)
    if not rows:
        return
    displayed = rows[:12]
    order = [r["Source / campaign"] for r in displayed]
    st.markdown("#### Which campaigns attract eligible attention")
    st.caption("The chart shows qualified volume by first-touch source and campaign, not additional sessions.")
    chart = alt.Chart(alt.Data(values=displayed)).mark_bar(
        cornerRadiusEnd=5, color="#60758a"
    ).encode(
        y=alt.Y("Source / campaign:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=260)),
        x=alt.X("Quality-eligible:Q", title="Quality-eligible content sessions",
                axis=alt.Axis(tickMinStep=1)),
        tooltip=["Source / campaign:N", alt.Tooltip("Quality-eligible:Q", format=","),
                 alt.Tooltip("Content sessions:Q", format=","),
                 alt.Tooltip("Quality share:Q", format=".1f", title="Share (%)")],
    ).properties(height=max(190, len(displayed) * 37))
    st.altair_chart(chart, use_container_width=True)


def render_attribution_integrity(window: str) -> None:
    st.subheader("Acquisition quality · all channels")
    st.caption(
        "First-touch browser sessions are reconciled once across sources. "
        "Campaign and role are attributes of these same sessions, not extra visits."
    )
    try:
        data = fetch_attribution_integrity(window)
    except (RuntimeError, PermissionError, ValueError):
        st.warning("Cross-channel reconciliation is temporarily unavailable; other analytics remain available.")
        return

    overview = data["overview"]
    channels = [x for x in (data.get("channels") or []) if _n(x, "recorded_sessions")]
    campaigns = data.get("campaigns") or []
    _attribution_readout(overview, channels, campaigns)
    _render_source_charts(channels)
    _render_campaign_chart(campaigns)

    # Keep auditability, but make the decision-making content the default view.
    with st.expander("Inspect exact source and campaign counts", expanded=False):
        st.markdown("**Reconciled first-touch sources**")
        source_rows = [{
            "First-touch channel": p.get("channel"),
            "Content sessions": _n(p, "content_sessions"),
            "Quality-eligible": _n(p, "quality_eligible"),
            "Legacy / ungraded": _n(p, "legacy_ungraded"),
            "Suspected bursts": _n(p, "preview_burst_sessions"),
            "Other suspected": _n(p, "other_suspected_automation"),
            "Navigation views": _n(p, "navigation_page_views"),
            "Article views": _n(p, "article_views"),
            "Telemetry only": _n(p, "telemetry_only"),
        } for p in channels]
        if source_rows:
            st.dataframe(source_rows, hide_index=True, width="stretch")
        else:
            st.info("No recorded traffic in this reporting window.")
        st.markdown("**Campaign and role detail**")
        if campaigns:
            st.dataframe([{
                "Parent channel": x.get("channel"),
                "Campaign / role label": x.get("campaign"),
                "Content sessions": _n(x, "content_sessions"),
                "Quality-eligible": _n(x, "quality_eligible"),
                "Legacy / ungraded": _n(x, "legacy_ungraded"),
                "Suspected automation": _n(x, "flagged_sessions"),
            } for x in campaigns], hide_index=True, width="stretch")
        st.caption(
            "Article reading events and navigation page views are different event "
            "types. UTM campaign takes precedence over the legacy role label. "
            "Source and campaign tables contain the same first-touch sessions "
            "and must never be summed together."
        )
        st.caption(
            f"Other reporting exclusions: {_n(overview, 'telemetry_only')} telemetry-only "
            f"sessions; {_n(overview, 'legacy_ungraded')} legacy/ungraded content "
            "sessions are not classified as human or automation."
        )

    with st.expander("Measurement integrity and reconciliation checks", expanded=False):
        checks = [
            ("Unattributed sessions with an external referrer", _n(overview, "untagged_with_referrer"),
             "Unknown tag does not prove direct navigation."),
            ("Explicit source / UTM source conflicts", _n(overview, "source_conflicts"),
             "Explicitly tagged source wins; not a second visit."),
            ("Role / UTM campaign conflicts", _n(overview, "campaign_conflicts"),
             "Conflicting labels still describe one session."),
            ("Article page-wrapper events", _n(overview, "article_page_wrappers"),
             "Excluded from navigation views, because article_view counts the read."),
            ("Excluded explicit test sessions", _n(overview, "test_sessions"),
             "Source=application and role=Test are excluded."),
        ]
        st.dataframe([{"Check": label, "Observed": n, "Meaning": explanation}
                      for label, n, explanation in checks],
                     hide_index=True, width="stretch")
        unexpected = data.get("unexpected_tags") or []
        if unexpected:
            st.markdown("**Unrecognized source strings**")
            st.dataframe([{"Recorded tag": str(x.get("raw_first_source"))[:100],
                           "Sessions": _n(x, "sessions")} for x in unexpected],
                         hide_index=True, width="stretch")
        st.caption(
            "V5 quality classification applies only after V5 tracking exists. "
            "Automation indicators use cohort-level heuristics and do not "
            "verify a bot or a person's identity. No IPs, signatures or "
            "visitor IDs are returned from the aggregation query."
        )
