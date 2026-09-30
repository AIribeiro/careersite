from __future__ import annotations

import html
import json
from urllib import error, parse, request

import streamlit as st
import streamlit.components.v1 as components

from site_analytics import (
    ANALYTICS_PUBLISHABLE_KEY,
    ANALYTICS_URL,
    RECOMMENDED_ATTRIBUTION_SOURCES,
)

DASHBOARD_RPC = "careersite_analytics_dashboard_v2"
HIRING_INTELLIGENCE_RPC = "careersite_hiring_intelligence_v1"
PUBLIC_DASHBOARD_TOKEN = "public-readonly-v1"
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

ACCENT = "#c56f3d"
ACCENT_SOFT = "#ead7c9"
INK = "#10131a"
MUTED = "#6f6a62"
PANEL = "#fffdfa"
BORDER = "#ddd4c7"
GREEN = "#517a62"
BLUE = "#60758a"


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


def _dashboard_payload(window: str) -> dict[str, object]:
    if window == "last_hour":
        return {"p_token": PUBLIC_DASHBOARD_TOKEN, "p_days": 30, "p_window": "last_hour"}
    if window == "today":
        return {"p_token": PUBLIC_DASHBOARD_TOKEN, "p_days": 30, "p_window": "today"}
    if window.endswith("d") and window[:-1].isdigit():
        days = int(window[:-1])
        if days in {7, 30, 90, 365}:
            return {"p_token": PUBLIC_DASHBOARD_TOKEN, "p_days": days, "p_window": "days"}
    raise ValueError("Unsupported analytics reporting window.")


def _fetch_dashboard(window: str) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{DASHBOARD_RPC}"
    payload = json.dumps(_dashboard_payload(window)).encode("utf-8")
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


def _fetch_hiring_intelligence(window: str) -> dict:
    """Fetch the quality-filtered hiring evidence layer.

    This is additive to the established dashboard RPC so a temporary failure
    here never makes the core analytics dashboard unavailable.
    """
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{HIRING_INTELLIGENCE_RPC}"
    payload = json.dumps(_dashboard_payload(window)).encode("utf-8")
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
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def _pct(numerator: int, denominator: int) -> str:
    if not denominator:
        return "—"
    return f"{100 * numerator / denominator:.1f}%"


def _seconds(value: object) -> str:
    try:
        seconds = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    if seconds <= 0:
        return "—"
    if seconds < 1:
        return "<1s"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes / 60:.1f}h"


def _build_attribution_link(source: str, role: str, destination: str) -> str:
    params: list[tuple[str, str]] = []
    if destination and destination != "home":
        params.append(("page", destination))
    params.append(("source", source))
    if role.strip():
        params.append(("role", role.strip()))
    return PUBLIC_BASE_URL + "?" + parse.urlencode(params)


def _dashboard_css() -> None:
    st.markdown(
        f"""
<style>
.block-container {{
    max-width: 1500px;
    padding-top: 1.3rem;
    padding-bottom: 3rem;
}}
[data-testid="stMetric"] {{
    background: linear-gradient(150deg, {PANEL} 0%, #f8f2e9 100%);
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 16px 18px 14px 18px;
    box-shadow: 0 5px 18px rgba(16,19,26,.045);
}}
[data-testid="stMetricLabel"] {{
    color: {MUTED};
    font-size: .78rem;
    letter-spacing: .02em;
}}
[data-testid="stMetricValue"] {{
    color: {INK};
    font-weight: 750;
}}
[data-testid="stMetricDelta"] {{
    font-size: .75rem;
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {BORDER};
    border-radius: 18px;
    background: rgba(255,253,250,.75);
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: .4rem;
    border-bottom: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 12px 12px 0 0;
    padding-left: 1rem;
    padding-right: 1rem;
}}
.stTabs [aria-selected="true"] {{
    background: rgba(197,111,61,.11);
}}
.analytics-hero {{
    padding: 18px 22px 16px 22px;
    border: 1px solid {BORDER};
    border-radius: 22px;
    background:
      radial-gradient(circle at 88% 18%, rgba(197,111,61,.16), transparent 28%),
      linear-gradient(135deg, #fffdfa 0%, #f4eee5 100%);
    margin-bottom: 1rem;
}}
.analytics-eyebrow {{
    color: {ACCENT};
    text-transform: uppercase;
    letter-spacing: .14em;
    font-weight: 750;
    font-size: .72rem;
    margin-bottom: .25rem;
}}
.analytics-title {{
    color: {INK};
    font-size: clamp(1.55rem, 2.3vw, 2.35rem);
    line-height: 1.08;
    font-weight: 780;
    margin: 0 0 .35rem 0;
}}
.analytics-subtitle {{
    color: {MUTED};
    font-size: .96rem;
    max-width: 880px;
    margin: 0;
}}
.section-kicker {{
    color: {ACCENT};
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .11em;
    font-weight: 700;
    margin: 0 0 .15rem 0;
}}
.section-title {{
    color: {INK};
    font-size: 1.15rem;
    font-weight: 740;
    margin: 0 0 .35rem 0;
}}
.mini-note {{
    color: {MUTED};
    font-size: .79rem;
    line-height: 1.35;
}}
.funnel-wrap {{
    display: grid;
    gap: 10px;
    margin-top: .35rem;
}}
.funnel-row {{
    display: grid;
    grid-template-columns: minmax(105px, .8fr) 2.4fr 72px;
    align-items: center;
    gap: 10px;
}}
.funnel-label {{
    color: {INK};
    font-size: .82rem;
    font-weight: 650;
}}
.funnel-track {{
    height: 12px;
    background: #eee5da;
    border-radius: 999px;
    overflow: hidden;
}}
.funnel-fill {{
    height: 100%;
    background: linear-gradient(90deg, {ACCENT}, #d89a73);
    border-radius: 999px;
}}
.funnel-value {{
    text-align: right;
    color: {MUTED};
    font-variant-numeric: tabular-nums;
    font-size: .82rem;
}}
.callout {{
    border-left: 3px solid {ACCENT};
    background: rgba(197,111,61,.07);
    padding: 11px 13px;
    border-radius: 0 12px 12px 0;
    color: {MUTED};
    font-size: .82rem;
    margin-top: .7rem;
}}
@media (max-width: 760px) {{
    .block-container {{ padding-left: .85rem; padding-right: .85rem; }}
    .analytics-hero {{ padding: 16px; }}
    .funnel-row {{ grid-template-columns: 90px 1fr 58px; gap: 7px; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def _section(kicker: str, title: str, note: str | None = None) -> None:
    note_html = f'<div class="mini-note">{html.escape(note)}</div>' if note else ""
    st.markdown(
        f"""
<div>
  <div class="section-kicker">{html.escape(kicker)}</div>
  <div class="section-title">{html.escape(title)}</div>
  {note_html}
</div>
""",
        unsafe_allow_html=True,
    )


def _empty(message: str) -> None:
    st.caption(message)


def _count(value: object) -> int:
    """Normalize aggregate count fields returned by PostgREST for charting."""
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def _top_rows(rows: object, limit: int = 8) -> list[dict]:
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows[:limit] if isinstance(row, dict)]


def _bar_chart(
    rows: object,
    category: str,
    value: str = "sessions",
    *,
    limit: int = 8,
    height: int = 280,
    horizontal: bool = True,
    color: str = ACCENT,
    sort: object = "-x",
) -> None:
    ranked = sorted(rows, key=lambda row: float(row.get(value) or 0), reverse=True) if isinstance(rows, list) and sort == "-x" else rows
    data = _top_rows(ranked, limit)
    if value in {"sessions", "events", "engaged_sessions", "page_views"}:
        for row in data:
            row[value] = _count(row.get(value))
    if not data:
        _empty("No data in this reporting window yet.")
        return

    numeric_values: list[float] = []
    for row in data:
        try:
            numeric_values.append(float(row.get(value, 0) or 0))
        except (TypeError, ValueError):
            continue
    if numeric_values and max(numeric_values) <= 0:
        _empty("No data in this reporting window yet.")
        return

    count_format = "d" if value in {"sessions", "events", "engaged_sessions", "page_views", "shares"} else None

    if horizontal:
        encoding = {
            "y": {
                "field": category,
                "type": "nominal",
                "sort": sort,
                "axis": {"title": None, "labelLimit": 170, "labelColor": MUTED},
            },
            "x": {
                "field": value,
                "type": "quantitative",
                "axis": {
                    "title": None,
                    "grid": False,
                    "labelColor": MUTED,
                    **({"format": count_format} if count_format else {}),
                },
            },
            "tooltip": [
                {"field": category, "type": "nominal", "title": "Category"},
                {
                    "field": value,
                    "type": "quantitative",
                    "title": value.replace("_", " ").title(),
                    **({"format": count_format} if count_format else {}),
                },
            ],
        }
    else:
        encoding = {
            "x": {
                "field": category,
                "type": "nominal",
                "sort": sort,
                "axis": {"title": None, "labelAngle": 0, "labelColor": MUTED},
            },
            "y": {
                "field": value,
                "type": "quantitative",
                "axis": {
                    "title": None,
                    "gridColor": "#eee5da",
                    "labelColor": MUTED,
                    **({"format": count_format} if count_format else {}),
                },
            },
            "tooltip": [
                {"field": category, "type": "nominal", "title": "Category"},
                {
                    "field": value,
                    "type": "quantitative",
                    "title": value.replace("_", " ").title(),
                    **({"format": count_format} if count_format else {}),
                },
            ],
        }

    st.vega_lite_chart(
        data=data,
        spec={
            "mark": {"type": "bar", "cornerRadiusEnd": 6, "color": color},
            "encoding": encoding,
            "height": height,
            "config": {
                "view": {"stroke": None},
                "axis": {"domain": False, "ticks": False, "labelFontSize": 11},
            },
        },
        use_container_width=True,
        theme=None,
    )


def _donut_chart(
    rows: object,
    category: str,
    value: str = "sessions",
    *,
    limit: int = 6,
    height: int = 300,
) -> None:
    data = _top_rows(rows, limit)
    if not data:
        _empty("No data in this reporting window yet.")
        return
    st.vega_lite_chart(
        data=data,
        spec={
            "mark": {"type": "arc", "innerRadius": 68, "outerRadius": 115, "cornerRadius": 4},
            "encoding": {
                "theta": {"field": value, "type": "quantitative"},
                "color": {
                    "field": category,
                    "type": "nominal",
                    "legend": {
                        "title": None,
                        "orient": "bottom",
                        "columns": 2,
                        "labelLimit": 120,
                        "labelColor": MUTED,
                    },
                    "scale": {
                        "range": [ACCENT, "#d79870", "#947764", "#60758a", GREEN, "#b89f7f"]
                    },
                },
                "tooltip": [
                    {"field": category, "type": "nominal", "title": "Category"},
                    {"field": value, "type": "quantitative", "title": value.replace("_", " ").title()},
                ],
            },
            "height": height,
            "config": {"view": {"stroke": None}},
        },
        use_container_width=True,
        theme=None,
    )


def _daily_chart(rows: object) -> None:
    data = _top_rows(rows, 366)
    if not data:
        _empty("No daily activity yet.")
        return
    st.vega_lite_chart(
        data=data,
        spec={
            "layer": [
                {
                    "mark": {"type": "area", "color": ACCENT, "opacity": 0.14},
                    "encoding": {
                        "x": {
                            "field": "day",
                            "type": "temporal",
                            "axis": {"title": None, "labelColor": MUTED, "grid": False},
                        },
                        "y": {
                            "field": "sessions",
                            "type": "quantitative",
                            "axis": {"title": None, "labelColor": MUTED, "gridColor": "#eee5da"},
                        },
                        "tooltip": [
                            {"field": "day", "type": "temporal", "title": "Date"},
                            {"field": "sessions", "type": "quantitative", "title": "Sessions"},
                            {"field": "events", "type": "quantitative", "title": "Events"},
                            {"field": "impact_sessions", "type": "quantitative", "title": "Impact"},
                            {"field": "cv_sessions", "type": "quantitative", "title": "CV download sessions"},
                        ],
                    },
                },
                {
                    "mark": {"type": "line", "strokeWidth": 2.5, "color": ACCENT},
                    "encoding": {
                        "x": {"field": "day", "type": "temporal"},
                        "y": {"field": "sessions", "type": "quantitative"},
                    },
                },
                {
                    "mark": {"type": "point", "filled": True, "size": 54, "color": ACCENT},
                    "encoding": {
                        "x": {"field": "day", "type": "temporal"},
                        "y": {"field": "sessions", "type": "quantitative"},
                    },
                },
            ],
            "height": 310,
            "config": {
                "view": {"stroke": None},
                "axis": {"domain": False, "ticks": False, "labelFontSize": 11},
            },
        },
        use_container_width=True,
        theme=None,
    )


def _duration_chart(rows: object) -> None:
    data = _top_rows(rows, 10)
    if not data:
        _empty("No duration data yet.")
        return
    st.vega_lite_chart(
        data=data,
        spec={
            "mark": {"type": "bar", "cornerRadiusTopLeft": 6, "cornerRadiusTopRight": 6, "color": ACCENT},
            "encoding": {
                "x": {
                    "field": "duration_bucket",
                    "type": "ordinal",
                    "sort": ["Unconfirmed", "<10s", "10–29s", "30–59s", "1–2m", "2–5m", "5m+"],
                    "axis": {"title": None, "labelAngle": 0, "labelColor": MUTED},
                },
                "y": {
                    "field": "sessions",
                    "type": "quantitative",
                    "axis": {"title": None, "gridColor": "#eee5da", "labelColor": MUTED},
                },
                "tooltip": [
                    {"field": "duration_bucket", "type": "ordinal", "title": "Active time"},
                    {"field": "sessions", "type": "quantitative", "title": "Sessions"},
                ],
            },
            "height": 280,
            "config": {"view": {"stroke": None}, "axis": {"domain": False, "ticks": False}},
        },
        use_container_width=True,
        theme=None,
    )


def _hour_chart(rows: object) -> None:
    data = _top_rows(rows, 24)
    if not data:
        _empty("No hourly activity yet.")
        return
    prepared = []
    for row in data:
        prepared.append({"hour_label": f"{int(row.get('hour', 0)):02d}:00", "sessions": row.get("sessions", 0)})
    _bar_chart(prepared, "hour_label", horizontal=False, limit=24, height=255, sort=None, color=BLUE)


def _funnel(home: int, impact: int, lens: int, cv: int) -> None:
    stages = [
        ("All sessions", home),
        ("Impact", impact),
        ("Role lens", lens),
        ("CV download", cv),
    ]
    ceiling = max(home, 1)
    rows = []
    for label, value in stages:
        width = max(2.0 if value else 0.0, min(100.0, 100 * value / ceiling))
        pct = _pct(value, home) if label != "All sessions" else "100%" if home else "—"
        rows.append(
            f"""
<div class="funnel-row">
  <div class="funnel-label">{html.escape(label)}</div>
  <div class="funnel-track"><div class="funnel-fill" style="width:{width:.1f}%"></div></div>
  <div class="funnel-value">{value} · {pct}</div>
</div>
"""
        )
    st.markdown('<div class="funnel-wrap">' + "".join(rows) + "</div>", unsafe_allow_html=True)


def _hiring_funnel(rows: object) -> None:
    """Render the ordered evidence funnel from analysis-eligible sessions."""
    if not isinstance(rows, list):
        _empty("No quality-layer data in this reporting window yet.")
        return

    stages = [
        dict(row)
        for row in rows
        if isinstance(row, dict) and str(row.get("stage") or "") != "Engaged"
    ]
    if not stages:
        _empty("No quality-layer data in this reporting window yet.")
        return

    base = _count(stages[0].get("sessions"))
    ceiling = max(base, 1)
    rendered: list[str] = []
    for row in stages:
        label = str(row.get("stage") or "Stage")
        value = _count(row.get("sessions"))
        width = max(2.0 if value else 0.0, min(100.0, 100 * value / ceiling))
        pct = "100%" if label == "Analysis eligible" and base else _pct(value, base)
        rendered.append(
            f"""
<div class="funnel-row">
  <div class="funnel-label">{html.escape(label)}</div>
  <div class="funnel-track"><div class="funnel-fill" style="width:{width:.1f}%"></div></div>
  <div class="funnel-value">{value} · {pct}</div>
</div>
"""
        )
    st.markdown('<div class="funnel-wrap">' + "".join(rendered) + "</div>", unsafe_allow_html=True)


def _page_rows(rows: object, family: str | None = None) -> list[dict]:
    if not isinstance(rows, list):
        return []
    prepared: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        if family is not None and str(item.get("page_family") or "") != family:
            continue

        # The RPC returns the full page catalogue so unvisited pages appear as
        # zero rows. Those rows flatten Vega's quantitative scale and make the
        # navigation panel look broken. Keep only pages with actual activity
        # and normalize aggregate counts to integers for display.
        item["sessions"] = _count(item.get("sessions"))
        item["page_views"] = _count(item.get("page_views"))
        if item["sessions"] <= 0 and item["page_views"] <= 0:
            continue
        prepared.append(item)
    return prepared


def _top_label(rows: object, field: str) -> str:
    data = _top_rows(rows, 1)
    if not data:
        return "—"
    return str(data[0].get(field) or "—")


def render_analytics_dashboard() -> None:
    """Render the hidden, noindex hiring-funnel dashboard."""
    _noindex()
    _dashboard_css()

    st.markdown(
        """
<div class="analytics-hero">
  <div class="analytics-eyebrow">Career site intelligence</div>
  <div class="analytics-title">Visitor & hiring-funnel analytics</div>
  <p class="analytics-subtitle">
    A visual view of who arrives, how deeply they explore, which paths convert, and where recruiter attention concentrates.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    window = str(st.session_state.get("careersite_analytics_reporting_window") or "last_hour")
    try:
        data = _fetch_dashboard(str(window))
    except ValueError:
        st.error("Analytics is temporarily unavailable.")
        return
    except RuntimeError as exc:
        st.error(str(exc))
        return

    hiring = _fetch_hiring_intelligence(str(window))

    period_label = str(data.get("period_label") or REPORTING_WINDOW_LABELS.get(str(window), str(window)))
    period_since = data.get("period_since")
    reset_at = data.get("reset_at")

    totals = data.get("totals", {}) or {}
    sessions = int(totals.get("sessions", 0) or 0)
    home_sessions = int(totals.get("home_sessions", 0) or 0)
    impact_sessions = int(totals.get("impact_sessions", 0) or 0)
    lens_sessions = int(totals.get("lens_sessions", 0) or 0)
    cv_sessions = int(totals.get("cv_sessions", 0) or 0)
    email_sessions = int(totals.get("email_sessions", 0) or 0)
    linkedin_sessions = int(totals.get("linkedin_sessions", 0) or 0)
    engaged_sessions = int(totals.get("engaged_sessions", 0) or 0)
    single_page_sessions = int(totals.get("single_page_sessions", 0) or 0)
    confirmed_duration_sessions = int(totals.get("confirmed_duration_sessions", 0) or 0)
    unconfirmed_duration_sessions = int(totals.get("unconfirmed_duration_sessions", 0) or 0)
    quality = hiring.get("quality_summary", {}) or {}
    quality_sessions = _count(quality.get("analysis_eligible_sessions"))
    quality_engaged = _count(quality.get("engaged_sessions"))
    quality_evidence_reached = _count(quality.get("evidence_reached_sessions"))
    quality_evidence_engaged = _count(quality.get("evidence_engaged_sessions"))
    quality_verified = _count(quality.get("evidence_verified_sessions"))
    quality_hiring_intent = _count(quality.get("hiring_intent_sessions"))
    quality_recorded = _count(quality.get("recorded_sessions"))
    quality_automation = _count(quality.get("suspected_automation_sessions"))
    quality_telemetry_only = _count(quality.get("telemetry_only_sessions"))
    quality_explicit_test = _count(quality.get("explicit_test_sessions"))
    quality_since = hiring.get("quality_since")

    cv_download_events = next(
        (
            int(row.get("events", 0) or 0)
            for row in data.get("events", [])
            if isinstance(row, dict) and row.get("event_name") == "cv_download"
        ),
        0,
    )

    st.caption(
        f"{period_label}"
        + (f" · since {period_since}" if period_since else "")
        + (f" · reset baseline {reset_at}" if reset_at else "")
    )

    if hiring:
        q1, q2, q3, q4, q5 = st.columns(5)
        q1.metric("Analysis-eligible", quality_sessions, f"{quality_recorded} recorded v5")
        q2.metric("Engaged", _pct(quality_engaged, quality_sessions), f"{quality_engaged} sessions")
        q3.metric("Median active time", _seconds(quality.get("median_engaged_seconds")))
        q4.metric("Evidence verified", quality_verified, _pct(quality_verified, quality_sessions))
        q5.metric("Hiring intent", quality_hiring_intent, _pct(quality_hiring_intent, quality_sessions))
        st.caption(
            "Quality metrics use tracking v5 only"
            + (f" · since {quality_since}" if quality_since else "")
            + ". Analysis-eligible means a valid content view, excluding explicit tests and a conservative suspected-automation cohort. "
            "Sessions are browser-tab sessions, not unique people."
        )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Measured sessions", sessions)
    k2.metric("Engagement", _pct(engaged_sessions, sessions), f"{engaged_sessions} engaged")
    k3.metric(
        "Avg active time",
        _seconds(totals.get("avg_active_seconds")),
        f"{confirmed_duration_sessions} confirmed sessions",
    )
    k4.metric("Pages / session", f"{float(totals.get('avg_pages_per_session', 0) or 0):.2f}")
    k5.metric("CV downloads", cv_download_events, f"{cv_sessions} downloading sessions")
    st.caption(
        "Recorded-traffic metrics below remain available for continuity. They can include automation and telemetry-only sessions; "
        "use the quality layer above for behavioral interpretation. Sessions are distinct browser-tab session IDs, not unique people."
    )

    o1, o2, o3, o4, o5 = st.columns(5)
    o1.metric("Reached Impact", _pct(impact_sessions, sessions), f"{impact_sessions} sessions")
    o2.metric("Opened a lens", _pct(lens_sessions, sessions), f"{lens_sessions} sessions")
    o3.metric("CV conversion", _pct(cv_sessions, sessions), f"{cv_sessions} downloading sessions")
    o4.metric("Contact channel sessions", email_sessions + linkedin_sessions, "email + LinkedIn; overlap possible")
    o5.metric("Single-page", _pct(single_page_sessions, sessions), f"{single_page_sessions} sessions")

    overview_tab, quality_tab, audience_tab, acquisition_tab, engagement_tab, tools_tab = st.tabs(
        ["Overview", "Quality & intent", "Audience", "Acquisition", "Engagement", "Tools"]
    )

    with overview_tab:
        left, right = st.columns([1.65, 1])
        with left:
            with st.container(border=True):
                _section("Traffic", "Session trend", "Hover for daily sessions, events and downstream conversions.")
                _daily_chart(data.get("daily", []))
        with right:
            with st.container(border=True):
                if hiring:
                    _section(
                        "Hiring evidence",
                        "Evidence funnel",
                        "Ordered stages use analysis-eligible v5 sessions. General engagement is shown separately because it is not a prerequisite for reaching a specialist evidence page.",
                    )
                    _hiring_funnel(hiring.get("quality_funnel", []))
                    st.markdown(
                        f'<div class="callout">Engaged: <b>{quality_engaged}</b> · '
                        f'Evidence reached: <b>{quality_evidence_reached}</b> · '
                        f'Evidence engaged: <b>{quality_evidence_engaged}</b></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    _section("Funnel", "Depth of exploration", "Independent stage reach, relative to all sessions.")
                    _funnel(sessions, impact_sessions, lens_sessions, cv_sessions)

        if hiring:
            with st.container(border=True):
                _section(
                    "Legacy continuity",
                    "Recorded-traffic depth",
                    "The original raw session funnel is retained for historical continuity; use it as a recorded-traffic diagnostic rather than a people count.",
                )
                _funnel(sessions, impact_sessions, lens_sessions, cv_sessions)

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                _section("Role fit", "Most explored role lenses")
                _bar_chart(data.get("lenses", []), "lens", value="sessions", limit=6, height=245)
        with right:
            with st.container(border=True):
                _section("Actions", "Conversion activity")
                _bar_chart(data.get("events", []), "event_name", value="sessions", limit=8, height=245, color=GREEN)

        left, right = st.columns([1.45, 1])
        with left:
            with st.container(border=True):
                _section(
                    "Navigation",
                    "Page exploration",
                    "Distinct sessions that opened each page in the selected reporting window.",
                )
                _bar_chart(
                    _page_rows(data.get("pages", [])),
                    "page_label",
                    value="sessions",
                    limit=12,
                    height=340,
                    color=BLUE,
                )
        with right:
            with st.container(border=True):
                _section(
                    "About",
                    "About & profile pages",
                    "About, Credentials & Certifications, and Speaking & Publications are tracked separately.",
                )
                about_rows = _page_rows(data.get("pages", []), "About")
                _bar_chart(
                    about_rows,
                    "page_label",
                    value="sessions",
                    limit=3,
                    height=340,
                    color=GREEN,
                )
                if about_rows:
                    about_sessions = sum(int(row.get("sessions", 0) or 0) for row in about_rows)
                    about_views = sum(int(row.get("page_views", 0) or 0) for row in about_rows)
                    st.caption(
                        f"About-family activity: {about_sessions} page-session visits · {about_views} page views."
                    )

        s1, s2, s3 = st.columns(3)
        s1.info(f"Top device: **{_top_label(hiring.get('devices', []) if hiring else data.get('devices', []), 'device_type')}**")
        s2.info(f"Top source: **{_top_label(hiring.get('normalized_channels', []) if hiring else data.get('attribution', []), 'channel' if hiring else 'attribution_source')}**")
        s3.info(f"Top country: **{_top_label(hiring.get('countries', []) if hiring else data.get('countries', []), 'country_code')}**")

    with quality_tab:
        if not hiring:
            st.info("The audience-quality layer is not available for this reporting window.")
        else:
            a1, a2, a3, a4, a5 = st.columns(5)
            a1.metric("Recorded v5", quality_recorded)
            a2.metric("Analysis eligible", quality_sessions)
            a3.metric("Suspected automation", quality_automation)
            a4.metric("Telemetry only", quality_telemetry_only)
            a5.metric("Explicit test", quality_explicit_test)

            st.caption(
                "No raw events are deleted. Classification happens only in reporting. "
                "Suspected automation is a conservative cohort heuristic, not proof that an individual session was a bot."
            )

            left, right = st.columns([1.35, 1])
            with left:
                with st.container(border=True):
                    _section(
                        "Hiring evidence",
                        "Evidence progression",
                        "Analysis-eligible → evidence reached → evidence engaged → evidence verified → hiring intent.",
                    )
                    _hiring_funnel(hiring.get("quality_funnel", []))
            with right:
                with st.container(border=True):
                    _section(
                        "Actions",
                        "Action intent tiers",
                        "Exploration, evidence verification and direct hiring-intent behavior are kept separate.",
                    )
                    _bar_chart(hiring.get("action_tiers", []), "tier", value="sessions", limit=6, height=285, color=GREEN)

            left, right = st.columns(2)
            with left:
                with st.container(border=True):
                    _section(
                        "Acquisition",
                        "Qualified channel mix",
                        "LinkedIn variants roll up to one parent channel while campaign/source detail remains preserved.",
                    )
                    _bar_chart(hiring.get("normalized_channels", []), "channel", value="sessions", limit=10, height=300, color=BLUE)
            with right:
                with st.container(border=True):
                    _section(
                        "Traffic quality",
                        "Excluded from behavioral analysis",
                        "Telemetry-only sessions are measurement-invalid; suspected automation is excluded conservatively; explicit tests are deliberately tagged.",
                    )
                    _bar_chart(hiring.get("excluded_traffic", []), "category", value="sessions", limit=6, height=300)

            left, right = st.columns(2)
            with left:
                with st.container(border=True):
                    _section("Qualified audience", "Country", "Geography after the quality filter.")
                    _bar_chart(hiring.get("countries", []), "country_code", value="sessions", limit=10, height=280, color=GREEN)
            with right:
                with st.container(border=True):
                    _section("Qualified audience", "Device mix", "Device mix after the quality filter.")
                    _donut_chart(hiring.get("devices", []), "device_type", value="sessions", limit=6, height=280)

            rule = hiring.get("automation_rule", {}) or {}
            st.caption(
                "Automation heuristic: repeated exact technical signature ≥ "
                f"{_count(rule.get('minimum_repeated_signature_sessions'))} sessions, "
                "zero recorded interactions, zero recorded actions, and cohort average active time below "
                f"{_seconds(float(rule.get('maximum_signature_average_engaged_ms') or 0) / 1000)}. "
                "The rule is intentionally narrow to avoid misclassifying legitimate visitors."
            )

    with audience_tab:
        left, right = st.columns([1, 1.25])
        with left:
            with st.container(border=True):
                _section("Audience", "Device mix")
                _donut_chart(hiring.get("devices", []) if hiring else data.get("devices", []), "device_type")
        with right:
            with st.container(border=True):
                _section("Technology", "Browsers")
                _bar_chart(data.get("browsers", []), "browser_family", limit=8, height=300)

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                _section("Technology", "Operating systems")
                _bar_chart(data.get("operating_systems", []), "os_family", limit=8, height=280, color=BLUE)
        with right:
            with st.container(border=True):
                _section("Geography", "Country")
                _bar_chart(hiring.get("countries", []) if hiring else data.get("countries", []), "country_code", limit=10, height=280, color=GREEN)

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                _section("Locale", "Browser language")
                _bar_chart(data.get("languages", []), "language", limit=10, height=260)
        with right:
            with st.container(border=True):
                _section("Locale", "Timezone")
                _bar_chart(data.get("timezones", []), "timezone", limit=10, height=260, color=BLUE)

        st.caption(
            "Country and device use analysis-eligible sessions when the v5 quality layer is available. "
            "Browser, operating-system, language and timezone panels remain recorded-traffic diagnostics for historical continuity. "
            "Country is a coarse two-letter code; no raw IP addresses or third-party geolocation lookups are stored."
        )

    with acquisition_tab:
        left, right = st.columns([1.35, 1])
        with left:
            with st.container(border=True):
                if hiring:
                    _section(
                        "Attribution",
                        "Qualified parent channels",
                        "LinkedIn source variants are normalized into one parent channel for decision-making.",
                    )
                    _bar_chart(hiring.get("normalized_channels", []), "channel", limit=10, height=320)
                else:
                    _section("Attribution", "Job-search sources", "Which distribution activity brings visitors into the site.")
                    _bar_chart(data.get("attribution", []), "attribution_source", limit=10, height=320)
        with right:
            with st.container(border=True):
                _section("Referrals", "External referrers")
                _bar_chart(data.get("referrers", []), "referrer_host", limit=10, height=320, color=BLUE)

        if hiring:
            with st.container(border=True):
                _section(
                    "Attribution detail",
                    "Recorded source taxonomy",
                    "Raw source labels are retained below so campaign diagnostics remain visible even though the primary channel view is normalized.",
                )
                _bar_chart(data.get("attribution", []), "attribution_source", limit=12, height=260, color=ACCENT)

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                _section("Journey", "Landing pages")
                _bar_chart(data.get("landing_pages", []), "landing_page", limit=10, height=280, color=GREEN)
        with right:
            with st.container(border=True):
                _section("Journey", "Exit pages")
                _bar_chart(data.get("exit_pages", []), "exit_page", limit=10, height=280)

    with engagement_tab:
        left, right = st.columns([1.15, 1])
        with left:
            with st.container(border=True):
                _section(
                    "Quality",
                    "Active time distribution",
                    "Visible active time only. Initial-hit-only sessions are shown as Unconfirmed instead of being assigned a false 0–1 second duration.",
                )
                _duration_chart(data.get("duration_buckets", []))
        with right:
            with st.container(border=True):
                _section("Timing", "Sessions by hour", "Stockholm local time.")
                _hour_chart(data.get("hours", []))

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                _section("Timing", "Sessions by weekday", "Stockholm local time.")
                _bar_chart(
                    data.get("weekdays", []),
                    "weekday",
                    horizontal=False,
                    limit=7,
                    height=260,
                    sort=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    color=GREEN,
                )
        with right:
            with st.container(border=True):
                _section("Engagement", "Device quality", "Engaged sessions by device class.")
                _bar_chart(hiring.get("devices", []) if hiring else data.get("devices", []), "device_type", value="engaged_sessions", limit=6, height=260, color=BLUE)

        with st.container(border=True):
            _section(
                "Interpretation",
                "How timing is counted",
                "Active time counts only while the page is visible. A session's duration is considered confirmed after an engagement heartbeat arrives; sessions with only the initial hit remain Duration unconfirmed. A new session starts after 30 minutes without visible activity.",
            )
            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Engaged sessions", engaged_sessions, _pct(engaged_sessions, sessions))
            q2.metric("Median active time", _seconds(totals.get("median_active_seconds")))
            q3.metric("Average active time", _seconds(totals.get("avg_active_seconds")))
            q4.metric(
                "Duration unconfirmed",
                unconfirmed_duration_sessions,
                _pct(unconfirmed_duration_sessions, sessions),
            )

    with tools_tab:
        with st.container(border=True):
            _section(
                "Distribution",
                "Attribution link builder",
                "Create trackable links for CVs, LinkedIn, recruiter outreach, email and selected applications.",
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
                "Attribution persists only for the current browser tab/session. "
                "It does not create a durable visitor profile."
            )

        with st.container(border=True):
            _section("Privacy", "Measurement boundaries")
            st.markdown(
                "The dashboard uses first-party session analytics only: no heatmaps, recordings, raw IP storage, "
                "full user-agent storage, persistent visitor IDs, advertising pixels or cross-session profiles."
            )
