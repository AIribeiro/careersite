"""Evidence-led Home-to-portfolio journey reporting (public aggregate data only)."""
from __future__ import annotations

import altair as alt
import streamlit as st

from page_analytics import _dashboard_payload
from page_content_intelligence import _fetch_rpc


@st.cache_data(ttl=300, show_spinner=False)
def fetch_home_journey(window: str) -> dict:
    """A valid existing public analytics window, with no session-level output."""
    return _fetch_rpc("careersite_home_journey_v1", _dashboard_payload(window))


def _n(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (ValueError, TypeError):
        return 0


def home_journey_findings(report: dict) -> dict:
    """Keep clicks (intent) separate from confirmed destination page views."""
    home = _n(report.get("home_landings"))
    onward = min(home, _n(report.get("onward_sessions")))
    last7 = _n(report.get("last_7d_home_landings"))
    last7onward = min(last7, _n(report.get("last_7d_onward_sessions")))
    clicks = _n(report.get("navigation_clicks"))
    confirmed = min(clicks, _n(report.get("confirmed_clicks")))
    return {
        "home": home,
        "onward": onward,
        "no_destination": home - onward,
        "onward_rate": onward / home if home else None,
        "last7": last7,
        "last7onward": last7onward,
        "clicks": clicks,
        "confirmed": confirmed,
        "unconfirmed": clicks - confirmed,
        "click_confirm_rate": confirmed / clicks if clicks else None,
    }


def _destination_chart(report: dict) -> None:
    labels = {
        "impact": "Experience & impact",
        "thinking": "Thinking & articles",
        "ai-data-governance": "AI & Data Governance",
        "about": "About",
        "presence": "Speaking & publications (retired)",
        "certifications": "Credentials (retired)",
        "contact": "Contact",
        "enterprise": "Enterprise AI leadership (retired)",
        "transformation": "AI adoption (retired)",
        "governance": "Governance role lens (retired)",
        "consulting": "Consulting role lens (retired)",
    }
    rows = [
        {"Destination": labels.get(str(r.get("page")),str(r.get("page") or "Other")),
         "Sessions": _n(r.get("sessions"))}
        for r in report.get("destinations", [])
        if isinstance(r, dict) and _n(r.get("sessions"))
    ]
    if not rows:
        st.caption("No onward page views recorded in this period.")
        return
    rows.sort(key=lambda r: (-r["Sessions"],r["Destination"]))
    chart = (alt.Chart(alt.Data(values=rows))
             .mark_bar(cornerRadiusEnd=4)
             .encode(x=alt.X("Sessions:Q", title="Recorded sessions", axis=alt.Axis(tickMinStep=1)),
                     y=alt.Y("Destination:N", sort=[r["Destination"] for r in rows],
                             title=None),
                     tooltip=["Destination:N","Sessions:Q"])
             .properties(height=max(155,36*len(rows))))
    st.altair_chart(chart, width="stretch")


def _journey_comparison(rows: list[dict], label_key: str, total_key: str,
                        confirmed_key: str, success_label: str, pending_label: str) -> None:
    """Show volume and measured continuation together, with exact values on hover."""
    values = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        total = _n(row.get(total_key))
        if not total:
            continue
        confirmed = min(total, _n(row.get(confirmed_key)))
        label = str(row.get(label_key) or "Unknown").replace("-", " ").title()
        for status, count, order in ((success_label, confirmed, 0),
                                      (pending_label, total - confirmed, 1)):
            values.append({"Group": label, "Status": status, "Count": count,
                           "Total": total, "Rate": confirmed / total, "Order": order})
    if not values:
        st.info("No observations available for this comparison in the selected period.")
        return
    order = list(dict.fromkeys(r["Group"] for r in sorted(values, key=lambda r: -r["Total"])))
    base = alt.Chart(alt.Data(values=values))
    bars = base.mark_bar(cornerRadiusEnd=5, size=24).encode(
        x=alt.X("Count:Q", stack="zero", title="Recorded observations",
                axis=alt.Axis(tickMinStep=1)),
        y=alt.Y("Group:N", sort=order, title=None, axis=alt.Axis(labelLimit=210)),
        color=alt.Color("Status:N", title=None,
                        scale=alt.Scale(domain=[success_label, pending_label],
                                        range=["#c47642", "#d6d4ce"]),
                        legend=alt.Legend(orient="bottom", labelLimit=280)),
        order=alt.Order("Order:Q", sort="ascending"),
        tooltip=[alt.Tooltip("Group:N", title="Scope"), "Status:N",
                 alt.Tooltip("Count:Q", title="Observations", format=","),
                 alt.Tooltip("Total:Q", title="Total", format=","),
                 alt.Tooltip("Rate:Q", title="Confirmed continuation", format=".1%")],
    )
    st.altair_chart(bars.properties(height=max(130, len(order) * 48)), width="stretch")
    # A shared percentage scale makes small mobile cohorts comparable with desktop.
    rates = base.transform_filter(alt.datum.Order == 0).mark_bar(
        cornerRadiusEnd=5, size=18, color="#c47642"
    ).encode(
        x=alt.X("Rate:Q", title="Confirmed continuation rate",
                scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")),
        y=alt.Y("Group:N", sort=order, title=None),
        tooltip=["Group:N", alt.Tooltip("Rate:Q", format=".1%"),
                 alt.Tooltip("Count:Q", title="Confirmed", format=","), "Total:Q"],
    )
    labels = rates.mark_text(align="left", dx=5, color="#666666").encode(
        text=alt.Text("Rate:Q", format=".1%"))
    st.altair_chart((rates + labels).properties(height=max(100, len(order) * 38)), width="stretch")


def render_home_journey(window: str) -> None:
    st.subheader("From Home to the rest of the portfolio")
    st.caption("The six-page design began on 23 October 2026. Retired route labels below represent historical navigation only; they must not be counted as distinct current destinations. For a clean redesign comparison, use complete post-release days and the same pre-release duration.")
    st.caption(
        "Where Home-entry sessions go next, which navigation routes they select, "
        "and whether a destination page view was subsequently recorded."
    )
    try:
        report = fetch_home_journey(window)
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        st.caption("Home journey diagnostics are temporarily unavailable; existing visit reports remain available.")
        return

    data = home_journey_findings(report)
    if not data["home"]:
        st.caption("No Home-entry sessions were recorded for this period.")
        return

    left, right = st.columns([1.05,1.25],gap="large")
    with left:
        st.markdown("**Recorded onward journeys**")
        st.progress(data["onward_rate"],
                    text=f"{data['onward']:,} of {data['home']:,} Home entries · {data['onward_rate']:.1%}")
        st.caption(f"{data['no_destination']:,} entries have no second page view recorded. "
                   "This is not proof that visitors immediately left.")
        if data["last7"] >= 20 and data["last7onward"] == 0:
            st.warning(
                f"No onward page views were recorded among {data['last7']:,} Home-entry "
                "sessions in the last seven days. Validate navigation tracking before "
                "attributing this entirely to visitor choice."
            )
        elif data["onward_rate"] < 0.10 and data["home"] >= 20:
            st.write("Home visitors rarely continue to another measured page. "
                     "Review hero routing, mobile visibility and route telemetry.")
        st.markdown("**Explicit route selections**")
        if data["clicks"]:
            st.write(f"{data['clicks']:,} recorded navigation clicks; "
                     f"{data['confirmed']:,} followed by a matching destination view "
                     f"({data['click_confirm_rate']:.0%}).")
            if data["unconfirmed"]:
                st.caption("An unconfirmed click may indicate missing destination tracking, "
                           "failed navigation, or a click immediately before a session ended.")
        else:
            st.caption("No explicit navigation-click events in this period. "
                       "Separate route-intent tracking begins with this release; "
                       "earlier page views remain in the historical baseline.")
    with right:
        st.markdown("**First recorded destination after Home**")
        _destination_chart(report)

    devices_col, routes_col = st.columns(2, gap="large")
    with devices_col:
        with st.container(border=True):
            st.markdown("#### How journeys differ by device")
            st.caption("Compare audience size and the share that reached another page.")
            _journey_comparison(report.get("device_breakdown") or [], "device", "landings", "onward",
                                "Reached another page", "No onward view recorded")
            st.caption("A missing onward view does not establish that someone left. "
                       "Rates based on small groups can move sharply with one visit.")
    with routes_col:
        with st.container(border=True):
            st.markdown("#### Which routes lead to arrivals?")
            st.caption("Compare selected routes with subsequently recorded destination views.")
            _journey_comparison(report.get("route_selections") or [], "page", "clicks", "confirmed",
                                "Confirmed arrival", "Arrival not confirmed")
            st.caption("Each route uses its own recorded clicks as the denominator. "
                       "Missing click records leave this comparison unavailable.")

    with st.expander("How these journeys are measured"):
        st.caption(
            "Session = short-lived browser-tab session. Home entry = first recorded page "
            "within the selected period is Home. Onward = a subsequent different page_view "
            "in that session. A route click is never counted as an arrival unless a matching "
            "destination page_view occurs afterward within 30 minutes. "
            "Internal navigation and section exposure are sensitive to deployment and browser behavior."
        )
