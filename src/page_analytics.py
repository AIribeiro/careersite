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
RESET_RPC = "careersite_analytics_reset"
PUBLIC_BASE_URL = "https://jairribeiro-ai.streamlit.app/"
REPORTING_WINDOWS = (
    ("last_hour", "Last hour"),
    ("today", "Today"),
    ("7d", "Last 7 days"),
    ("30d", "Last 30 days"),
    ("90d", "Last 90 days"),
    ("365d", "Last 365 days"),
)
REPORTING_WINDOW_LABELS = dict(REPORTING_WINDOWS)


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


def _dashboard_payload(access_code: str, window: str) -> dict[str, object]:
    if window == "last_hour":
        return {"p_token": access_code, "p_days": 30, "p_window": "last_hour"}
    if window == "today":
        return {"p_token": access_code, "p_days": 30, "p_window": "today"}
    if window.endswith("d") and window[:-1].isdigit():
        days = int(window[:-1])
        if days in {7, 30, 90, 365}:
            return {"p_token": access_code, "p_days": days, "p_window": "days"}
    raise ValueError("Unsupported analytics reporting window.")


def _fetch_dashboard(access_code: str, window: str) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{DASHBOARD_RPC}"
    payload = json.dumps(_dashboard_payload(access_code, window)).encode("utf-8")
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


def _reset_analytics(access_code: str) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{RESET_RPC}"
    payload = json.dumps({"p_token": access_code}).encode("utf-8")
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
        raise RuntimeError(f"Analytics reset returned HTTP {exc.code}: {body[:180]}") from exc
    except error.URLError as exc:
        raise RuntimeError("Analytics service is temporarily unreachable.") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected analytics reset response format.")
    if not data.get("reset_at"):
        raise RuntimeError("Analytics reset did not return a persistent reset baseline.")
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
    if "careersite_analytics_reset_pending" not in st.session_state:
        st.session_state.careersite_analytics_reset_pending = False

    if not st.session_state.careersite_analytics_access_code:
        access_code = st.text_input("Access code", type="password", autocomplete="off")
        if st.button("Open analytics", type="primary"):
            try:
                _fetch_dashboard(access_code, "30d")
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
            else:
                st.session_state.careersite_analytics_access_code = access_code
                st.rerun()
        st.info("This page is intentionally absent from the public site navigation and is marked noindex.")
        return

    flash = st.session_state.get("careersite_analytics_flash")
    if flash:
        st.success(str(flash))
        del st.session_state["careersite_analytics_flash"]

    filter_col, reset_col, lock_col = st.columns([3, 1, 1])
    with filter_col:
        window = st.selectbox(
            "Reporting window",
            [key for key, _ in REPORTING_WINDOWS],
            index=3,
            format_func=lambda key: REPORTING_WINDOW_LABELS[key],
            key="careersite_analytics_reporting_window",
        )
    with reset_col:
        st.write("")
        if st.button("Reset analytics", use_container_width=True):
            st.session_state.careersite_analytics_reset_pending = True
    with lock_col:
        st.write("")
        if st.button("Lock dashboard", use_container_width=True):
            st.session_state.careersite_analytics_access_code = ""
            st.session_state.careersite_analytics_reset_pending = False
            st.rerun()

    if st.session_state.careersite_analytics_reset_pending:
        st.warning(
            "Reset permanently establishes a new zero baseline for all dashboard metrics and deletes stored events from before that moment. "
            "New visits after the reset will start increasing the counters again."
        )
        confirm_col, cancel_col, _ = st.columns([1.4, 1, 3])
        with confirm_col:
            if st.button("Confirm reset to zero", type="primary", use_container_width=True):
                try:
                    result = _reset_analytics(st.session_state.careersite_analytics_access_code)
                except ValueError:
                    st.session_state.careersite_analytics_access_code = ""
                    st.session_state.careersite_analytics_reset_pending = False
                    st.error("The access code is no longer valid. Reload the page and enter it again.")
                    return
                except RuntimeError as exc:
                    st.error(str(exc))
                    return
                deleted = int(result.get("deleted_events", 0) or 0)
                remaining = int(result.get("remaining_events", 0) or 0)
                reset_at = str(result.get("reset_at") or "")
                st.session_state.careersite_analytics_reset_pending = False
                st.session_state.careersite_analytics_flash = (
                    f"Analytics reset persisted at {reset_at}. {deleted} pre-reset event{'s' if deleted != 1 else ''} deleted. "
                    f"{remaining} event{'s' if remaining != 1 else ''} arrived at or after the new baseline."
                )
                st.rerun()
        with cancel_col:
            if st.button("Cancel reset", use_container_width=True):
                st.session_state.careersite_analytics_reset_pending = False
                st.rerun()

    try:
        data = _fetch_dashboard(st.session_state.careersite_analytics_access_code, str(window))
    except ValueError:
        st.session_state.careersite_analytics_access_code = ""
        st.session_state.careersite_analytics_reset_pending = False
        st.error("The access code is no longer valid. Reload the page and enter it again.")
        return
    except RuntimeError as exc:
        st.error(str(exc))
        return

    period_label = str(data.get("period_label") or REPORTING_WINDOW_LABELS.get(str(window), str(window)))
    period_since = data.get("period_since")
    reset_at = data.get("reset_at")
    st.caption(f"Showing: {period_label}" + (f" · since {period_since}" if period_since else ""))
    if reset_at:
        st.caption(f"Persistent analytics reset baseline: {reset_at}. Events before this timestamp are excluded from every reporting window.")

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

    st.subheader("Activity by day")
    daily = data.get("daily", []) or []
    if daily:
        st.dataframe(daily, hide_index=True, use_container_width=True)
    else:
        st.caption("No activity in this reporting window yet.")

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
