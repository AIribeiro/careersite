from __future__ import annotations

import json
from urllib import error, parse, request

import streamlit as st
import streamlit.components.v1 as components

from site_analytics import (
    ANALYTICS_PUBLISHABLE_KEY,
    ANALYTICS_URL,
    RECOMMENDED_ATTRIBUTION_SOURCES,
)

DASHBOARD_RPC = "careersite_analytics_dashboard"
PUBLIC_BASE_URL = "https://jairribeiro-ai.streamlit.app/"


def _noindex() -> None:
    components.html(
        """
<script>
(() => {
  const doc = window.parent.document;
  let robots = doc.head.querySelector('meta[name="robots"]');
  if (!robots) {
    robots = doc.createElement('meta');
    robots.setAttribute('name', 'robots');
    doc.head.appendChild(robots);
  }
  robots.setAttribute('content', 'noindex,nofollow,noarchive');
})();
</script>
""",
        height=0,
        width=0,
    )


def _fetch_dashboard(access_code: str, days: int) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{DASHBOARD_RPC}"
    payload = json.dumps({"p_token": access_code, "p_days": int(days)}).encode("utf-8")
    req = request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "apikey": ANALYTICS_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in {400, 401, 403}:
            raise ValueError("Invalid analytics access code.") from exc
        raise RuntimeError(f"Analytics service returned HTTP {exc.code}: {body[:180]}") from exc
    except error.URLError as exc:
        raise RuntimeError("Analytics service is temporarily unreachable.") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected analytics response format.")
    return data


def _pct(numerator: int, denominator: int) -> str:
    if not denominator:
        return "—"
    return f"{100 * numerator / denominator:.1f}%"


def _build_attribution_link(source: str, role: str, destination: str) -> str:
    params: list[tuple[str, str]] = []
    if destination and destination != "home":
        params.append(("page", destination))
    params.append(("source", source))
    if role.strip():
        params.append(("role", role.strip()))
    return PUBLIC_BASE_URL + "?" + parse.urlencode(params)


def render_analytics_dashboard() -> None:
    """Render the hidden, access-controlled hiring-funnel dashboard."""
    _noindex()

    st.title("Hiring-funnel analytics")
    st.caption(
        "Privacy-conscious behavioral measurement for the career site. "
        "No heatmaps, recordings, persistent visitor IDs or personal visitor profiles."
    )

    if "careersite_analytics_access_code" not in st.session_state:
        st.session_state.careersite_analytics_access_code = ""

    if not st.session_state.careersite_analytics_access_code:
        access_code = st.text_input("Access code", type="password", autocomplete="off")
        if st.button("Open analytics", type="primary"):
            try:
                _fetch_dashboard(access_code, 30)
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
            else:
                st.session_state.careersite_analytics_access_code = access_code
                st.rerun()
        st.info("This page is intentionally absent from the public site navigation and is marked noindex.")
        return

    top_left, top_right = st.columns([3, 1])
    with top_left:
        days = st.selectbox("Reporting window", [7, 30, 90, 365], index=1, format_func=lambda x: f"Last {x} days")
    with top_right:
        if st.button("Lock dashboard"):
            st.session_state.careersite_analytics_access_code = ""
            st.rerun()

    try:
        data = _fetch_dashboard(st.session_state.careersite_analytics_access_code, int(days))
    except ValueError:
        st.session_state.careersite_analytics_access_code = ""
        st.error("The access code is no longer valid. Reload the page and enter it again.")
        return
    except RuntimeError as exc:
        st.error(str(exc))
        return

    totals = data.get("totals", {}) or {}
    sessions = int(totals.get("sessions", 0) or 0)
    home_sessions = int(totals.get("home_sessions", 0) or 0)
    impact_sessions = int(totals.get("impact_sessions", 0) or 0)
    lens_sessions = int(totals.get("lens_sessions", 0) or 0)
    cv_sessions = int(totals.get("cv_sessions", 0) or 0)

    st.subheader("Hiring funnel")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sessions", sessions)
    c2.metric("Home sessions", home_sessions)
    c3.metric("Reached Impact", impact_sessions, _pct(impact_sessions, home_sessions))
    c4.metric("Opened a lens", lens_sessions, _pct(lens_sessions, home_sessions))
    c5.metric("Downloaded CV", cv_sessions, _pct(cv_sessions, sessions))

    st.caption(
        "Percentages use Home sessions for Impact/lens progression and all measured sessions for CV conversion. "
        "Treat very small samples as directional only."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Role-lens usage")
        lenses = data.get("lenses", []) or []
        if lenses:
            st.dataframe(lenses, hide_index=True, use_container_width=True)
        else:
            st.caption("No lens views in this reporting window yet.")

    with right:
        st.subheader("Event activity")
        events = data.get("events", []) or []
        if events:
            st.dataframe(events, hide_index=True, use_container_width=True)
        else:
            st.caption("No events in this reporting window yet.")

    st.subheader("Attribution by job-search activity")
    attribution = data.get("attribution", []) or []
    if attribution:
        st.dataframe(attribution, hide_index=True, use_container_width=True)
    else:
        st.caption("No attributed sessions yet.")

    st.subheader("Daily trend")
    daily = data.get("daily", []) or []
    if daily:
        st.dataframe(daily, hide_index=True, use_container_width=True)
    else:
        st.caption("No daily activity yet.")

    st.divider()
    st.subheader("Attribution link builder")
    st.caption(
        "Use the source label to identify the job-search activity, not the person. "
        "Email is tracked separately from recruiter outreach. The optional role label lets selected applications be grouped by mandate."
    )

    a, b, c = st.columns(3)
    with a:
        source = st.selectbox("Source", list(RECOMMENDED_ATTRIBUTION_SOURCES), index=0)
    with b:
        role = st.text_input("Role / campaign (optional)", placeholder="ai-transformation")
    with c:
        destination = st.selectbox(
            "Landing page",
            ["home", "impact", "enterprise", "transformation", "governance", "consulting"],
            index=0,
        )

    link = _build_attribution_link(source, role, destination)
    st.code(link, language=None)
    st.caption(
        "Attribution persists only for the current browser tab/session. It does not create a durable visitor profile."
    )
