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
        st.altair_chart(chart, width="stretch")
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
    st.altair_chart(chart, width="stretch")


def _attribution_quality_chart(channels: list[dict]) -> None:
    """Compare source quality without treating suspected automation as verified bots."""
    import altair as alt

    plot = []
    rank = []
    palette = {
        "Quality-eligible": "#517a62",
        "Suspected previews": "#c56f3d",
        "Other suspected": "#bd9b7e",
        "Legacy / ungraded": "#60758a",
        "Other / unclassified": "#cbc5be",
    }
    for item in channels:
        total = _n(item, "content_sessions")
        if not total:
            continue
        name = str(item.get("channel") or "Unattributed / unknown")
        buckets = [
            ("Quality-eligible", _n(item, "quality_eligible")),
            ("Suspected previews", _n(item, "preview_burst_sessions")),
            ("Other suspected", _n(item, "other_suspected_automation")),
            ("Legacy / ungraded", _n(item, "legacy_ungraded")),
        ]
        other = max(0, total - sum(count for _, count in buckets))
        buckets.append(("Other / unclassified", other))
        rank.append((name, _n(item, "quality_eligible"), total))
        for label, count in buckets:
            if count:
                plot.append({
                    "Channel": name, "Classification": label, "Sessions": count,
                    "Share": 100 * count / total,
                })

    if not plot:
        st.info("No content-session channel data for this period.")
        return
    # Quality-first ordering keeps large suspected-automation cohorts from hiding useful sources.
    order = [item[0] for item in sorted(rank, key=lambda row: (-row[1], -row[2], row[0]))]
    chart = alt.Chart(alt.Data(values=plot)).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("Channel:N", sort=order, title=None),
        x=alt.X("sum(Sessions):Q", title="Content sessions",
                axis=alt.Axis(tickMinStep=1)),
        color=alt.Color(
            "Classification:N",
            scale=alt.Scale(domain=list(palette), range=list(palette.values())),
            legend=alt.Legend(title=None, orient="bottom", columns=2),
        ),
        tooltip=[
            alt.Tooltip("Channel:N"),
            alt.Tooltip("Classification:N"),
            alt.Tooltip("Sessions:Q", format=","),
            alt.Tooltip("Share:Q", title="Within-channel share (%)", format=".1f"),
        ],
    ).properties(height=max(235, len(order) * 46))
    st.altair_chart(chart, width="stretch")


def _attribution_campaign_chart(campaigns: list[dict]) -> None:
    """Show qualified campaign cohorts without double-counting parent channels."""
    import altair as alt

    rows = []
    for item in campaigns:
        qualified = _n(item, "quality_eligible")
        if not qualified:
            continue
        rows.append({
            "Campaign / source": (
                f"{str(item.get('campaign') or 'untagged')} · "
                f"{str(item.get('channel') or 'unknown')}"
            ),
            "Qualified": qualified,
            "Content sessions": _n(item, "content_sessions"),
        })
    if not rows:
        st.info("No quality-eligible campaign cohorts in this period.")
        return
    rows = sorted(rows, key=lambda row: (-row["Qualified"], row["Campaign / source"]))[:10]
    order = [row["Campaign / source"] for row in rows]
    chart = alt.Chart(alt.Data(values=rows)).mark_bar(
        color="#60758a", cornerRadiusEnd=5
    ).encode(
        y=alt.Y("Campaign / source:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=230)),
        x=alt.X("Qualified:Q", title="Quality-eligible sessions",
                axis=alt.Axis(tickMinStep=1)),
        tooltip=[
            alt.Tooltip("Campaign / source:N"),
            alt.Tooltip("Qualified:Q", format=","),
            alt.Tooltip("Content sessions:Q", format=","),
        ],
    ).properties(height=max(210, len(rows) * 34))
    st.altair_chart(chart, width="stretch")


def render_attribution_integrity(window: str) -> None:
    st.subheader("Where meaningful portfolio attention comes from")
    st.caption(
        "First-touch browser sessions are assigned to one parent channel. "
        "Quality-eligible is a tracking classification, not a verified person. "
        "Campaign tags describe the same sessions and are never added to channel totals."
    )
    try:
        data = fetch_attribution_integrity(window)
    except (RuntimeError, PermissionError, ValueError):
        st.warning("Cross-channel reconciliation is temporarily unavailable; other analytics remain available.")
        return

    o = data["overview"]
    channels = [item for item in (data.get("channels") or []) if _n(item, "recorded_sessions")]
    campaigns = data.get("campaigns") or []
    content = _n(o, "content_sessions")
    eligible = _n(o, "quality_eligible")
    bursts = _n(o, "suspected_preview_bursts")
    other_suspected = _n(o, "suspected_automation_other")
    suspicious = bursts + other_suspected

    if content:
        qualified_share = 100 * eligible / content
        suspected_share = 100 * suspicious / content
        if suspicious > eligible:
            finding = "Suspected automation currently exceeds quality-eligible attention."
        elif eligible > suspicious:
            finding = "Quality-eligible attention exceeds suspected automation."
        else:
            finding = "Quality-eligible and suspected-automation volumes are similar."
        st.markdown(
            f"**Qualified attention:** {eligible:,} of {content:,} content sessions "
            f"({qualified_share:.0f}%) qualify for behavioral analysis. "
            f"**Interpretation:** {finding} "
            f"{suspicious:,} ({suspected_share:.0f}%) are classified as suspected "
            "preview or other automation activity. These labels are diagnostic, not verified identities."
        )
        named = [
            item for item in channels
            if _n(item, "quality_eligible") > 0 and
            str(item.get("channel") or "").strip().casefold()
            not in {"unattributed / unknown", "direct/unknown", "direct / unknown"}
        ]
        if named:
            top = max(named, key=lambda item: _n(item, "quality_eligible"))
            name = str(top.get("channel"))
            n = _n(top, "quality_eligible")
            st.caption(
                f"**Strongest tagged channel by qualified volume:** {name} "
                f"({n:,} eligible sessions, {100 * n / eligible:.0f}% of the eligible total). "
                "This is a directional signal; small channel cohorts should not be treated as reliable rankings."
            )
        if content < 100:
            st.caption("Small sample: compare longer reporting windows before changing distribution strategy.")
    else:
        st.info("No content sessions in this reporting period.")

    st.markdown("**Channel quality · volume and classification**")
    _attribution_quality_chart(channels)
    st.caption(
        "Every bar represents mutually exclusive first-touch sessions within its channel. "
        "The suspected categories exclude those sessions from the quality-eligible count."
    )

    st.markdown("**Campaigns contributing quality-eligible sessions**")
    _attribution_campaign_chart(campaigns)
    st.caption(
        "Campaign and channel breakdowns describe overlapping dimensions of the same sessions; "
        "do not sum the two charts."
    )

    with st.expander("Inspect exact counts, attribution labels and counting checks", expanded=False):
        st.markdown("**Reconciliation snapshot**")
        st.dataframe([{
            "Content sessions": content,
            "Quality-eligible V5": eligible,
            "Suspected previews V5": bursts,
            "Legacy / ungraded": _n(o, "legacy_ungraded"),
        }], hide_index=True, width="stretch")

        st.caption(
            f"Also excluded: {_n(o, 'telemetry_only'):,} telemetry-only sessions and "
            f"{other_suspected:,} other suspected-automation sessions. "
            "No recorded events are removed; classification affects reporting."
        )
        st.markdown("**Reconciled first-touch sources**")
        if channels:
            st.dataframe([{
                "First-touch channel": p.get("channel"),
                "Content sessions": _n(p, "content_sessions"),
                "Quality-eligible": _n(p, "quality_eligible"),
                "Legacy / ungraded": _n(p, "legacy_ungraded"),
                "Suspected bursts": _n(p, "preview_burst_sessions"),
                "Other suspected": _n(p, "other_suspected_automation"),
                "Navigation views": _n(p, "navigation_page_views"),
                "Article views": _n(p, "article_views"),
                "Telemetry only": _n(p, "telemetry_only"),
            } for p in channels], hide_index=True, width="stretch")
        st.caption(
            "Navigation views exclude article-page wrapper events. "
            "Article reads are counted using their own event type."
        )
        if campaigns:
            st.markdown("**Campaign and role detail**")
            st.dataframe([{
                "Parent channel": x.get("channel"),
                "Campaign / role": x.get("campaign"),
                "Content sessions": _n(x, "content_sessions"),
                "Quality-eligible": _n(x, "quality_eligible"),
                "Legacy / ungraded": _n(x, "legacy_ungraded"),
                "Suspected automation": _n(x, "flagged_sessions"),
            } for x in campaigns], hide_index=True, width="stretch")
        st.caption(
            "UTM campaign takes precedence over the older 'role' parameter for campaign labels. "
            "Campaign and channel totals are non-additive."
        )
        checks = [
            ("Unattributed sessions with an external referrer", _n(o, "untagged_with_referrer"),
             "An untagged referral is not proof of direct navigation."),
            ("Explicit source vs UTM source conflicts", _n(o, "source_conflicts"),
             "The explicitly tagged source wins; one session is counted."),
            ("Role vs UTM campaign conflicts", _n(o, "campaign_conflicts"),
             "Conflicting labels describe the same session."),
            ("Article page-wrapper events", _n(o, "article_page_wrappers"),
             "Excluded from navigation view counts to prevent overlap."),
            ("Excluded explicit test sessions", _n(o, "test_sessions"),
             "Source=application + role=Test is excluded."),
        ]
        st.markdown("**Counting and tag checks**")
        st.dataframe([{"Check": label, "Observed": count, "Interpretation": note}
                      for label, count, note in checks],
                     hide_index=True, width="stretch")
        unexpected = data.get("unexpected_tags") or []
        if unexpected:
            st.markdown("**Unrecognized source strings**")
            st.dataframe([
                {"Recorded tag": str(x.get("raw_first_source"))[:100],
                 "Session IDs": _n(x, "sessions")}
                for x in unexpected
            ], hide_index=True, width="stretch")
        st.caption(
            "V5-quality tracking cannot be imputed to historic sessions. "
            "Suspicious bursts use coarse temporary technical signatures; no raw IPs, "
            "persistent visitor identifiers or browser signatures are exposed."
        )

    with st.expander("How to interpret quality classifications", expanded=False):
        st.markdown(
            "**Eligible is not a confirmed human visitor.** The quality filter removes "
            "explicit tests, telemetry-only activity and conservative suspected automation "
            "patterns. A qualifying session may still be a preview, a candidate, an "
            "unrelated reader or a recruiter; first-party event data does not identify them."
        )
        st.caption(
            "Browser-tab sessions are not unique people. Campaign/role tags and first-touch "
            "source classifications are different dimensions of the same events. "
            "Compare patterns using longer windows rather than inferring employer interest from "
            "small counts or short-lived spikes."
        )
