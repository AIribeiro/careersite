from __future__ import annotations

import json
from urllib import error, request

import streamlit as st

from page_analytics import (
    ACCENT,
    BLUE,
    GREEN,
    MUTED,
    _bar_chart,
    _dashboard_payload,
    _empty,
    _pct,
    _section,
    _seconds,
)
from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL
from thinking_articles import resolve_article

ARTICLE_DASHBOARD_RPC = "careersite_analytics_articles_v2"


def _fetch_article_dashboard(access_code: str, window: str) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{ARTICLE_DASHBOARD_RPC}"
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
        raise RuntimeError(f"Article analytics returned HTTP {exc.code}: {body[:180]}") from exc
    except error.URLError as exc:
        raise RuntimeError("Article analytics is temporarily unreachable.") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected article analytics response format.")
    return data


def _article_title(slug: object) -> str:
    value = str(slug or "").strip()
    article = resolve_article(value)
    return article.title if article is not None else value or "Unknown article"


def _article_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    prepared: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item["article"] = _article_title(item.get("article_slug"))
        prepared.append(item)
    return prepared


def _share_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    labels = {
        "linkedin": "LinkedIn",
        "x": "X",
        "email": "Email",
        "copy": "Copy link",
    }
    prepared: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        action = str(item.get("article_action") or "unknown")
        item["channel"] = labels.get(action, action.replace("_", " ").title())
        prepared.append(item)
    return prepared


def _source_rows(rows: object, slug: str) -> list[dict]:
    if not isinstance(rows, list):
        return []
    prepared: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or str(row.get("article_slug") or "") != slug:
            continue
        item = dict(row)
        item["source"] = str(item.get("attribution_source") or "direct/unknown")
        prepared.append(item)
    return prepared


def _article_daily_chart(rows: object) -> None:
    if not isinstance(rows, list) or not rows:
        _empty("No article activity in this reporting window yet.")
        return
    data = [dict(row) for row in rows if isinstance(row, dict)]
    st.vega_lite_chart(
        data=data,
        spec={
            "layer": [
                {
                    "mark": {"type": "area", "color": ACCENT, "opacity": 0.13},
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
                            {"field": "sessions", "type": "quantitative", "title": "Reader sessions"},
                            {"field": "views", "type": "quantitative", "title": "Article views"},
                            {"field": "shares", "type": "quantitative", "title": "Shares"},
                        ],
                    },
                },
                {
                    "mark": {"type": "line", "strokeWidth": 2.4, "color": ACCENT},
                    "encoding": {
                        "x": {"field": "day", "type": "temporal"},
                        "y": {"field": "sessions", "type": "quantitative"},
                    },
                },
                {
                    "mark": {"type": "point", "filled": True, "size": 52, "color": ACCENT},
                    "encoding": {
                        "x": {"field": "day", "type": "temporal"},
                        "y": {"field": "sessions", "type": "quantitative"},
                    },
                },
            ],
            "height": 285,
            "config": {
                "view": {"stroke": None},
                "axis": {"domain": False, "ticks": False, "labelFontSize": 11},
            },
        },
        use_container_width=True,
        theme=None,
    )


def render_article_analytics() -> None:
    """Render article-specific reading and social-sharing intelligence."""
    access_code = str(st.session_state.get("careersite_analytics_access_code") or "")
    if not access_code:
        return

    window = str(st.session_state.get("careersite_analytics_reporting_window") or "30d")
    try:
        data = _fetch_article_dashboard(access_code, window)
    except ValueError:
        st.warning("Article intelligence could not authenticate with the current dashboard session.")
        return
    except RuntimeError as exc:
        st.warning(str(exc))
        return

    totals = data.get("totals", {}) or {}
    article_rows = _article_rows(data.get("articles", []))
    share_rows = _share_rows(data.get("share_actions", []))

    views = int(totals.get("views", 0) or 0)
    sessions = int(totals.get("sessions", 0) or 0)
    shares = int(totals.get("shares", 0) or 0)
    share_sessions = int(totals.get("share_sessions", 0) or 0)
    engaged_sessions = int(totals.get("engaged_sessions", 0) or 0)
    confirmed_duration_sessions = int(totals.get("confirmed_duration_sessions", 0) or 0)
    unconfirmed_duration_sessions = int(totals.get("unconfirmed_duration_sessions", 0) or 0)
    open_clicks = int(totals.get("open_clicks", 0) or 0)

    st.divider()
    st.markdown(
        """
<div class="analytics-hero">
  <div class="analytics-eyebrow">Content intelligence</div>
  <div class="analytics-title">Article visits & interactions</div>
  <p class="analytics-subtitle">
    Which ideas attract recruiter attention, how long readers actively engage, what gets shared, and which distribution sources bring people into each article.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    a1, a2, a3, a4, a5, a6 = st.columns(6)
    a1.metric("Article views", views, f"{sessions} reader sessions")
    a2.metric("Reader sessions", sessions, f"{confirmed_duration_sessions} duration-confirmed")
    a3.metric("Engaged readers", _pct(engaged_sessions, sessions), f"{engaged_sessions} ≥10s active")
    a4.metric(
        "Avg active read",
        _seconds(totals.get("avg_active_seconds")),
        f"median {_seconds(totals.get('median_active_seconds'))}",
    )
    a5.metric("Share actions", shares, f"{share_sessions} sharing sessions")
    a6.metric(
        "Duration unconfirmed",
        unconfirmed_duration_sessions,
        _pct(unconfirmed_duration_sessions, sessions),
    )
    st.caption(f"Portfolio article-open clicks in this window: {open_clicks}.")

    left, right = st.columns([1.45, 1])
    with left:
        with st.container(border=True):
            _section(
                "Reading",
                "Most-read articles",
                "Reader sessions count distinct browsing sessions with an actual article view.",
            )
            _bar_chart(article_rows, "article", value="sessions", limit=8, height=320)
    with right:
        with st.container(border=True):
            _section("Sharing", "Share channels", "Direct share actions from article footers.")
            _bar_chart(share_rows, "channel", value="shares", limit=6, height=320, color=GREEN)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            _section(
                "Depth",
                "Active reading time",
                "Average visible active time for duration-confirmed article sessions only; initial-hit-only sessions are excluded from the average.",
            )
            _bar_chart(article_rows, "article", value="avg_active_seconds", limit=8, height=300, color=BLUE)
    with right:
        with st.container(border=True):
            _section("Amplification", "Most-shared articles", "Articles that triggered a LinkedIn, X, email or copy-link action.")
            _bar_chart(article_rows, "article", value="shares", limit=8, height=300, color=GREEN)

    with st.container(border=True):
        _section("Trend", "Article reader sessions", "Daily article readership in Stockholm reporting time.")
        _article_daily_chart(data.get("daily", []))

    with st.container(border=True):
        _section(
            "Acquisition",
            "Where article readers came from",
            "Select an article to see the job-search attribution source retained for that browser tab/session.",
        )
        slugs = [str(row.get("article_slug") or "") for row in article_rows if row.get("article_slug")]
        if not slugs:
            _empty("No article reader source data in this reporting window yet.")
        else:
            selected = st.selectbox(
                "Article",
                slugs,
                format_func=_article_title,
                key="careersite_article_analytics_selected_slug",
            )
            sources = _source_rows(data.get("sources", []), selected)
            _bar_chart(sources, "source", value="sessions", limit=10, height=260, color=ACCENT)

    st.caption(
        "Article analytics remains first-party and session-scoped: reader sessions are distinct session IDs with an actual article view; "
        "active reading time is reported only after a heartbeat confirms duration. Article slug, share channel and active reading time are recorded, "
        "but no persistent visitor ID, raw IP address, full user agent, heatmap or cross-session profile is created."
    )
