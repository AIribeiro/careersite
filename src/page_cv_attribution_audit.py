"""Owner-only, non-additive CV source / role attribution reconciliation."""
from __future__ import annotations

import json
from urllib import error, request

import streamlit as st

from site_analytics import ANALYTICS_URL
from site_analytics_public import public_analytics_rpc_headers


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
        headers=public_analytics_rpc_headers(),
    )
    try:
        with request.urlopen(req,timeout=20) as response:
            data=json.load(response)
    except (error.HTTPError,error.URLError,TimeoutError) as exc:
        raise RuntimeError("CV attribution audit is temporarily unavailable.") from exc
    if not isinstance(data,dict) or not isinstance(data.get("overview"),dict):
        raise RuntimeError("Unexpected attribution audit response.")
    return data


def _count(item: dict, key: str) -> int:
    """Read a non-negative aggregate count without implying visitor identity."""
    try:
        return max(0, int(item.get(key) or 0))
    except (TypeError, ValueError):
        return 0


def _cv_page_quality_chart(pages: list[dict]) -> None:
    """Show suspected previews alongside other recorded views, by page."""
    import altair as alt

    rows = []
    for item in pages:
        name = str(item.get("page") or "Unknown page").replace("_", " ").title()
        raw = _count(item, "raw_views")
        suspected = min(raw, _count(item, "suspect_scan_views"))
        other = max(0, raw - suspected)
        if not raw:
            continue
        rows.extend([
            {"Page": name, "Classification": "Suspected preview", "Views": suspected,
             "Share": 100 * suspected / raw},
            {"Page": name, "Classification": "Other recorded", "Views": other,
             "Share": 100 * other / raw},
        ])
    if not rows:
        st.info("No CV-tagged page views in this period.")
        return
    order = sorted({row["Page"] for row in rows},
                   key=lambda name: -sum(row["Views"] for row in rows if row["Page"] == name))
    chart = alt.Chart(alt.Data(values=rows)).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("Page:N", sort=order, title=None),
        x=alt.X("sum(Views):Q", title="CV-tagged page views",
                axis=alt.Axis(tickMinStep=1)),
        color=alt.Color(
            "Classification:N",
            scale=alt.Scale(
                domain=["Suspected preview", "Other recorded"],
                range=["#c56f3d", "#517a62"],
            ),
            legend=alt.Legend(title=None, orient="bottom"),
        ),
        tooltip=[
            alt.Tooltip("Page:N"),
            alt.Tooltip("Classification:N"),
            alt.Tooltip("Views:Q", format=","),
            alt.Tooltip("Share:Q", title="Share within page (%)", format=".1f"),
        ],
    ).properties(height=max(170, len(order) * 44))
    st.altair_chart(chart, use_container_width=True)


def _role_attribution_chart(roles: list[dict]) -> None:
    """Role traffic is a different breakdown; never add it to CV source views."""
    import altair as alt

    rows = [
        {"Role / campaign": str(item.get("role") or "Untagged"),
         "Views": _count(item, "page_views")}
        for item in roles if _count(item, "page_views")
    ]
    if not rows:
        st.info("No role-attributed page views in this period.")
        return
    rows = sorted(rows, key=lambda item: -item["Views"])[:10]
    order = [item["Role / campaign"] for item in rows]
    chart = alt.Chart(alt.Data(values=rows)).mark_bar(
        color="#60758a", cornerRadiusEnd=5
    ).encode(
        y=alt.Y("Role / campaign:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=220)),
        x=alt.X("Views:Q", title="Page views (all sources)",
                axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip("Role / campaign:N"),
                 alt.Tooltip("Views:Q", format=",")],
    ).properties(height=max(180, len(rows) * 38))
    st.altair_chart(chart, use_container_width=True)


def render_cv_attribution_audit(window: str) -> None:
    st.subheader("CV-linked traffic · evidence, not just volume")
    st.caption(
        "Source=cv marks tracked page-view events, not CV file downloads or identified recruiters. "
        "Role and UTM tags describe those same events, not additional visitors."
    )
    try:
        audit = fetch_cv_attribution_audit(window)
    except (RuntimeError, PermissionError, ValueError):
        st.warning("CV attribution is temporarily unavailable; other reports remain accessible.")
        return

    overview = audit["overview"]
    raw = _count(overview, "cv_page_views")
    suspect = _count(overview, "suspect_scan_views")
    residual = max(0, raw - suspect)
    cv_sessions = _count(overview, "cv_sessions")
    overlap = _count(overview, "cv_utm_source_same_view")
    role_overlap = _count(overview, "cv_with_role")
    pages = audit.get("cv_pages") or []
    roles = audit.get("roles") or []

    if raw:
        share = 100 * suspect / raw
        if share >= 80:
            headline = "Most CV-linked page activity matches a suspected preview pattern."
        elif share >= 50:
            headline = "A substantial share of CV-linked activity matches suspected previews."
        elif suspect:
            headline = "Some CV-linked activity matches a suspected preview pattern."
        else:
            headline = "No CV-linked views matched the specific preview-burst rule."

        st.markdown(
            f"**{headline}** {suspect:,} of {raw:,} recorded CV-tagged page views "
            f"({share:.0f}%) are flagged. The remaining {residual:,} "
            "views are *unclassified*, not confirmed people or recruiter interest."
        )
        if suspect:
            st.caption(
                "The rule identifies correlated Home–Certifications–Presence-style visits "
                "across separate session IDs. It suggests link-preview or automated "
                "scanning activity but does not prove any session is a bot."
            )
        if raw < 100:
            st.caption("Small sample: one burst can materially change the proportions.")
    else:
        st.info("No CV-tagged page views in this reporting period.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Where CV-linked views occurred**")
        st.caption("Suspected previews vs other recorded views; not confirmed people.")
        _cv_page_quality_chart(pages)
    with right:
        st.markdown("**Which role or campaign tags appear?**")
        st.caption("Page views across all sources. This is a separate breakdown, not extra traffic.")
        _role_attribution_chart(roles)

    if overlap:
        st.caption(
            f"**Attribution check:** {overlap:,} CV-tagged page views also use "
            "utm_source=cv. These are the same events, counted once."
        )

    with st.expander("Inspect exact counts, source overlaps and reconciliation", expanded=False):
        a, b, c, d = st.columns(4)
        a.metric("CV-tagged page views", raw, help="Events tagged source=cv; not CV downloads.")
        b.metric("Distinct session IDs", cv_sessions, help="IDs are not unique people.")
        c.metric("Suspected preview views", suspect, help="Conservative burst classifier, not proven bots.")
        d.metric("Other recorded views", residual, help="Not verified human visits.")
        if pages:
            st.markdown("**CV-tagged page breakdown**")
            st.dataframe([
                {"Page": p.get("page"), "Raw views": _count(p, "raw_views"),
                 "Suspected preview": _count(p, "suspect_scan_views"),
                 "Other recorded views": _count(p, "other_views")}
                for p in pages
            ], hide_index=True, width="stretch")
        if roles:
            st.markdown("**Role-attributed views across all sources**")
            st.dataframe([
                {"Role / campaign": p.get("role"), "Page views": _count(p, "page_views"),
                 "Distinct session IDs": _count(p, "sessions")}
                for p in roles
            ], hide_index=True, width="stretch")
        st.caption(
            f"Role-labelled CV views: {role_overlap:,}. CV/UTM source overlap: {overlap:,}. "
            "Role and source totals are non-additive. Explicit source=application + role=Test "
            "traffic is excluded. View counts are preserved; classifications apply only to analysis."
        )
