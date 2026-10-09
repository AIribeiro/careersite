from __future__ import annotations

import json
from urllib import error, request

import altair as alt
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
from site_analytics import ANALYTICS_URL
from site_analytics_owner import owner_rpc_headers
from thinking_articles import resolve_article

ARTICLE_DASHBOARD_RPC = "careersite_analytics_articles_v2"


def _fetch_article_dashboard(window: str) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{ARTICLE_DASHBOARD_RPC}"
    payload = json.dumps(_dashboard_payload(window)).encode("utf-8")
    req = request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers=owner_rpc_headers(),
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
    if article is not None:
        return article.title
    from site_cms import fetch_published_articles
    try:
        return next((item.title for item in fetch_published_articles() if item.slug == value), value or "Unknown article")
    except RuntimeError:
        return value or "Unknown article"


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



def _reader_source_rows(rows: list[dict], slug: str = "") -> list[dict]:
    """Sum article-session visits, never claim cross-article unique readers."""
    labels = {"kpmg": "KPMG", "linkedin": "LinkedIn", "x": "X", "twitter": "Twitter",
              "facebook": "Facebook", "whatsapp": "WhatsApp", "email": "Email",
              "direct/unknown": "Direct / untagged"}
    counts: dict[str, int] = {}
    originals: dict[str, str] = {}
    for row in rows:
        if slug and row.get("article_slug") != slug:
            continue
        raw = str(row.get("attribution_source") or "direct/unknown").strip() or "direct/unknown"
        key = raw.casefold()
        count = max(0, int(row.get("sessions") or 0))
        counts[key] = counts.get(key, 0) + count
        originals.setdefault(key, raw)
    total = sum(counts.values())
    return [{"Source": labels.get(key, originals[key]), "Reading visits": count,
             "Share": count / total if total else 0,
             "Label": f"{count:,}  ·  {count / total:.0%}" if total else "0",
             "Tagged": key != "direct/unknown"}
            for key, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])) if count]


def render_reader_sources(window: str, kind: str = "article") -> None:
    """Immediate attribution overview above the detailed article reports."""
    is_page = kind == "page"
    noun = "Page" if is_page else "Reading"
    st.subheader("Where page visitors come from" if is_page else "Where readers come from")
    st.caption("Visits by source tag — including links shared with a company or contact.")
    try:
        if is_page:
            from page_content_intelligence import _fetch_rpc
            data = _fetch_rpc("careersite_page_sources", _dashboard_payload(window))
            data["sources"] = [dict(row, article_slug=row["page"]) for row in data.get("sources", [])]
        else:
            data = _fetch_article_dashboard(window)
    except (ValueError, RuntimeError, TimeoutError):
        st.info("Reader sources are temporarily unavailable. Other reports remain below.")
        return
    source_rows = data.get("sources", []) or []
    slugs = sorted({str(row["article_slug"]) for row in source_rows if row.get("article_slug")})
    def content_name(slug: str) -> str:
        if not slug:
            return "All pages" if is_page else "All articles"
        return slug.replace("-", " ").replace("_", " ").title() if is_page else _article_title(slug)
    selected = st.selectbox("Source breakdown for", [""] + slugs,
                            format_func=content_name, key=f"reader_sources_{kind}")
    rows = _reader_source_rows(source_rows, selected)
    if not rows:
        st.info("No visits in this window. Choose a longer reporting window to see earlier activity.")
        return
    total = sum(row["Reading visits"] for row in rows)
    tagged = sum(row["Reading visits"] for row in rows if row["Tagged"])
    top = next((row for row in rows if row["Tagged"]), None)
    a, b, c = st.columns(3)
    a.metric("Top tagged source", top["Source"] if top else "No source tags yet")
    b.metric(f"{noun} visits", f"{total:,}")
    c.metric("With source attribution", f"{tagged / total:.0%}")
    hover = alt.selection_point(fields=["Source"], on="pointerover", clear="pointerout", empty=False)
    base = alt.Chart(alt.Data(values=rows)).encode(
        y=alt.Y("Source:N", sort=[row["Source"] for row in rows], title=None,
                axis=alt.Axis(labelLimit=240, labelFontSize=14, ticks=False, domain=False)),
        x=alt.X("Reading visits:Q", title=None,
                scale=alt.Scale(domain=[0, max(row["Reading visits"] for row in rows) * 1.4]),
                axis=alt.Axis(tickMinStep=1, gridOpacity=0.12, domain=False)),
        tooltip=[alt.Tooltip("Source:N"), alt.Tooltip("Reading visits:Q", title=f"{noun} visits", format=","),
                 alt.Tooltip("Share:Q", title="Share of visits", format=".1%")],
    )
    bars = base.mark_bar(cornerRadiusEnd=8, height=26).encode(
        color=alt.condition(hover, alt.value("#22b8b0"),
                            alt.Color("Tagged:N", scale=alt.Scale(domain=[True, False],
                                      range=["#527bd9", "#9ca3af"]), legend=None)),
    ).add_params(hover)
    values = base.mark_text(align="left", dx=8, fontSize=13, fontWeight="bold").encode(text="Label:N")
    st.altair_chart((bars + values).properties(height=max(180, len(rows) * 46)), use_container_width=True)
    if is_page:
        st.caption("One page visit = one browser session opening one page. Across pages, a session can count more than once. "
                   "Attribution uses the first recorded source tag for that page/session in the selected window. "
                   "Article views and historical unclassified Thinking visits are excluded.")
    else:
        st.caption("One reading visit = one browser session opening one article. Across articles, the same session can count more than once. "
                   "Source tags are retained in the browser tab.")
    st.caption("Tags identify the shared link, not the visitor's identity or employer. Direct / untagged means no recorded source tag.")
    with st.expander("Exact source counts", expanded=False):
        st.dataframe([{"Source": row["Source"], f"{noun} visits": row["Reading visits"],
                       "Share": f"{row['Share']:.1%}"} for row in rows], hide_index=True, use_container_width=True)
    st.divider()


def render_article_analytics() -> None:
    """Render article-specific reading and social-sharing intelligence."""
    window = str(st.session_state.get("careersite_analytics_reporting_window") or "30d")
    try:
        data = _fetch_article_dashboard(window)
    except ValueError:
        st.warning("Article intelligence is temporarily unavailable.")
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

    reader_visits = sum(int(row.get("sessions") or 0) for row in article_rows)
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
    a1.metric("Article views", views, f"{reader_visits} article-session visits")
    a2.metric("Measured sessions", sessions, f"{confirmed_duration_sessions} ≥5s confirmed")
    a3.metric("Engaged reads", _pct(engaged_sessions, reader_visits), f"{engaged_sessions} ≥10s active")
    a4.metric(
        "Avg active read",
        _seconds(totals.get("avg_active_seconds")),
        f"median {_seconds(totals.get('median_active_seconds'))}",
    )
    a5.metric("Share actions", shares, f"{share_sessions} sharing sessions")
    a6.metric(
        "Duration unconfirmed",
        unconfirmed_duration_sessions,
        _pct(unconfirmed_duration_sessions, reader_visits),
    )
    st.caption(f"Portfolio article-open clicks in this window: {open_clicks}. Reading-rate denominators use article-session visits; a session reading two articles contributes two visits.")

    left, right = st.columns([1.45, 1])
    with left:
        with st.container(border=True):
            _section(
                "Reading",
                "Most-read articles",
                "Measured sessions count distinct browser sessions with an article view; they are not assumed to equal people.",
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
        _section("Trend", "Article measured sessions", "Daily article-view sessions in Stockholm reporting time.")
        _article_daily_chart(data.get("daily", []))

    with st.container(border=True):
        _section(
            "Acquisition",
            "Tagged acquisition source",
            "Select an article to see the source tag retained for that browser tab/session; this is campaign attribution, not a verified referrer.",
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
        "Article analytics remains first-party and session-scoped: measured sessions are distinct browser session IDs with an actual article view and should not be interpreted as unique people. "
        "active reading time is reported only after a heartbeat confirms duration. Article slug, share channel and active reading time are recorded, "
        "but no persistent visitor ID, raw IP address, full user agent, heatmap or cross-session profile is created."
    )
