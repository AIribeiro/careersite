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
        "presence": "Speaking & publications",
        "certifications": "Credentials",
        "contact": "Contact",
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


def render_home_journey(window: str) -> None:
    st.subheader("From Home to the rest of the portfolio")
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

    with st.expander("Route selections, devices and measurement definitions"):
        choices = [
            {
                "Route": r.get("page"),
                "Clicks": _n(r.get("clicks")),
                "Confirmed arrivals": _n(r.get("confirmed")),
            }
            for r in report.get("route_selections", [])
            if isinstance(r, dict)
        ]
        if choices:
            st.dataframe(choices, hide_index=True, width="stretch")
        else:
            st.caption("Route-click records are not yet available.")
        devices = [
            {"Device": row.get("device") or "Unknown",
             "Home entries": _n(row.get("landings")),
             "Onward sessions": _n(row.get("onward"))}
            for row in report.get("device_breakdown", [])
            if isinstance(row, dict)
        ]
        if devices:
            st.dataframe(devices, hide_index=True, width="stretch")
        st.caption(
            "Session = short-lived browser-tab session. Home entry = first recorded page "
            "within the selected period is Home. Onward = a subsequent different page_view "
            "in that session. A route click is never counted as an arrival unless a matching "
            "destination page_view occurs afterward within 30 minutes. "
            "Internal navigation and section exposure are sensitive to deployment and browser behavior."
        )
