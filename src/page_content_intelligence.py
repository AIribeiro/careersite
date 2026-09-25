"""Aggregate-only attention, content and action reporting."""
from __future__ import annotations

import csv
import io
import json
from urllib import error, request

import streamlit as st

from page_analytics import _bar_chart, _dashboard_payload, _seconds
from page_article_analytics import _article_title
from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL
from site_cms import fetch_published_articles
from thinking_articles import ARTICLES


def _article_metadata() -> list[dict[str, object]]:
    articles: dict[str, dict[str, object]] = {}
    for article in ARTICLES:
        articles[article.slug] = {
            "slug": article.slug,
            "title": article.title,
            "topic": article.topic,
            "kind": article.kind,
            "published_date": article.published_iso[:10],
        }
    try:
        for article in fetch_published_articles():
            articles[article.slug] = {
                "slug": article.slug,
                "title": article.title,
                "topic": article.category or "Uncategorized",
                "kind": article.kind or "Article",
                "published_date": article.published_iso[:10],
            }
    except RuntimeError:
        pass
    return list(articles.values())


def fetch_intelligence(window: str) -> dict:
    payload = _dashboard_payload(window)
    payload["p_article_metadata"] = _article_metadata()
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_content_intelligence_v2",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"apikey": ANALYTICS_PUBLISHABLE_KEY, "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            data = json.load(response)
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError("Content intelligence is temporarily unavailable; established reports remain below.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Content intelligence returned an unexpected response.")
    return data


def content_label(value: str) -> str:
    if value.startswith("article:"):
        return _article_title(value[8:])
    return value.replace("_", " ").title()


def _count(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rate(numerator: object, denominator: object) -> str:
    n, d = _count(numerator), _count(denominator)
    if not d:
        return "—"
    return f"{100 * n / d:.1f}% ({n} of {d})"


def _change(current: object, previous: object) -> str:
    now, before = _count(current), _count(previous)
    if not before:
        return f"new ({now} vs 0)" if now else "0.0% (0 vs 0)"
    return f"{100 * (now - before) / before:+.1f}% ({now} vs {before})"


def _milliseconds(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{number:.0f} ms"


def performance_rows(data: dict, kind: str) -> list[dict]:
    rows = []
    for row in data.get("performance", []):
        if row.get("kind") != kind:
            continue
        sessions = _count(row.get("sessions"))
        depth_n = _count(row.get("depth_measured_sessions"))
        rows.append({
            "Content": _article_title(row["content"]) if kind == "article" else content_label(row["content"]),
            "Views": _count(row.get("views")),
            "Sessions": sessions,
            "Engaged ≥10s": _rate(row.get("engaged_sessions"), sessions),
            "Avg visible time": _seconds(row.get("avg_active_seconds")),
            "Timing confirmed": _rate(row.get("confirmed_sessions"), sessions),
            "Depth measured": depth_n,
            "Reached 25%": _rate(row.get("quarter_sessions"), depth_n),
            "Reached 50%": _rate(row.get("halfway_sessions"), depth_n),
            "Reached 75%": _rate(row.get("three_quarter_sessions"), depth_n),
            "Reached 90%": _rate(row.get("bottom_sessions"), depth_n),
            "Deep read ≥30s + 90%": _rate(row.get("deep_read_sessions"), depth_n),
            "Share rate": _rate(row.get("sharing_sessions"), sessions),
            "Later portfolio": _rate(row.get("later_portfolio_sessions"), sessions),
            "Later CV": _rate(row.get("later_cv_sessions"), sessions),
            "Later contact": _rate(row.get("later_contact_sessions"), sessions),
        })
    return rows


def export_csv(rows: list[dict]) -> str:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value
                for key, value in row.items()
            })
    return output.getvalue()


def _render_exposure(data: dict, kind: str) -> None:
    if kind == "article":
        st.subheader("Article-card click-through")
        st.caption("The denominator is sessions where the specific card was at least 50% visible. A click is counted only for an exposed card in the same session.")
        cards = [{
            "Article / card": row.get("label") or row.get("element_key"),
            "Placement": row.get("placement"),
            "Exposed sessions": _count(row.get("exposed_sessions")),
            "Click sessions": _count(row.get("click_sessions")),
            "CTR": _rate(row.get("click_sessions"), row.get("exposed_sessions")),
        } for row in data.get("article_cards", [])]
        if cards:
            st.dataframe(cards, hide_index=True, use_container_width=True)
        else:
            st.info("Awaiting article-card exposure events from the new instrumentation.")

    st.subheader("CTA performance by placement")
    st.caption("Header, content-section, article-footer and footer CTAs are measured against sessions that actually saw each CTA.")
    ctas = [{
        "CTA": str(row.get("element_key") or "cta").replace("_", " ").title(),
        "Label": row.get("label") or "—",
        "Placement": row.get("placement") or "—",
        "Exposed sessions": _count(row.get("exposed_sessions")),
        "Click sessions": _count(row.get("click_sessions")),
        "CTR": _rate(row.get("click_sessions"), row.get("exposed_sessions")),
    } for row in data.get("cta_placements", [])]
    if ctas:
        st.dataframe(ctas, hide_index=True, use_container_width=True)
    else:
        st.info("Awaiting CTA exposure events from the new instrumentation.")

    if kind == "page":
        st.subheader("Section reach")
        st.caption("A section counts as reached when at least 15% of it enters the viewport. The denominator is sessions that viewed that page.")
        sections = [{
            "Page": content_label(str(row.get("page") or "")),
            "Section": row.get("section_label") or str(row.get("section_key") or "").replace("-", " ").title(),
            "Reached sessions": _count(row.get("reached_sessions")),
            "Page sessions": _count(row.get("page_sessions")),
            "Reach": _rate(row.get("reached_sessions"), row.get("page_sessions")),
        } for row in data.get("section_reach", [])]
        if sections:
            st.dataframe(sections, hide_index=True, use_container_width=True)
        else:
            st.info("Awaiting section-exposure events from the new instrumentation.")


def _render_paths(data: dict, kind: str) -> None:
    st.subheader("Where visitors go next")
    paths_rows = [
        dict(row, path=f"{content_label(row['from_content'])} → {content_label(row['to_content'])}")
        for row in data.get("journeys", [])
        if (str(row.get("from_content", "")).startswith("article:") if kind == "article"
            else not str(row.get("from_content", "")).startswith("article:"))
    ]
    _bar_chart(paths_rows, "path", value="sessions", limit=15, height=400)
    st.caption("Consecutive different content views in the same tab/session. Sequence is observed behavior, not causal attribution.")

    funnel = data.get("ordered_funnel", {})
    article_sessions = _count(funnel.get("article_sessions"))
    article_impact = _count(funnel.get("article_to_impact_sessions"))
    article_impact_cv = _count(funnel.get("article_to_impact_to_cv_sessions"))
    st.subheader("Ordered Article → Impact → CV journey")
    f1, f2, f3 = st.columns(3)
    f1.metric("Article sessions", article_sessions)
    f2.metric("Reached Impact after article", _rate(article_impact, article_sessions))
    f3.metric("Reached CV after Article → Impact", _rate(article_impact_cv, article_sessions))
    if article_impact:
        st.caption(f"CV after reaching Impact: {_rate(article_impact_cv, article_impact)}.")

    multi = data.get("multi_article", {})
    readers = _count(multi.get("reader_sessions"))
    multi_readers = _count(multi.get("multi_article_sessions"))
    st.subheader("Multi-article reading")
    st.metric("Read 2+ different articles in one session", _rate(multi_readers, readers))

    st.subheader("Time to first meaningful action")
    action_labels = {"case_study": "Open Leadership Impact", "cv": "Download CV", "contact": "Click contact"}
    actions = [{
        "Action": action_labels.get(str(row.get("action")), str(row.get("action")).replace("_", " ").title()),
        "Sessions": _count(row.get("sessions")),
        "Median time": _seconds(row.get("median_seconds")),
        "Average time": _seconds(row.get("avg_seconds")),
    } for row in data.get("time_to_action", [])]
    if actions:
        st.dataframe(actions, hide_index=True, use_container_width=True)
    else:
        st.info("No meaningful-action timing is available in this window.")

    left, right = st.columns(2)
    with left:
        st.subheader("First observed content")
        _bar_chart([
            dict(row, label=content_label(row["content"]))
            for row in data.get("entrances", [])
            if str(row.get("content", "")).startswith("article:") == (kind == "article")
        ], "label", limit=10)
    with right:
        st.subheader("Last observed content")
        _bar_chart([
            dict(row, label=content_label(row["content"]))
            for row in data.get("exits", [])
            if str(row.get("content", "")).startswith("article:") == (kind == "article")
        ], "label", limit=10)
    st.caption("Last observed content is not a confirmed exit; a session may still be active.")


def _render_trends(data: dict, kind: str) -> None:
    st.subheader("Period-over-period movement")
    st.caption("The selected window is compared with the immediately preceding window of equal duration. Counts are shown beside every percentage change.")
    comparisons = []
    for row in data.get("period_comparison", []):
        if row.get("kind") != kind:
            continue
        comparisons.append({
            "Content": _article_title(row["content"]) if kind == "article" else content_label(row["content"]),
            "Sessions": f"{_count(row.get('current_sessions'))} now / {_count(row.get('previous_sessions'))} previous",
            "Session change": _change(row.get("current_sessions"), row.get("previous_sessions")),
            "Views": f"{_count(row.get('current_views'))} now / {_count(row.get('previous_views'))} previous",
            "View change": _change(row.get("current_views"), row.get("previous_views")),
            "Engaged-session change": _change(row.get("current_engaged_sessions"), row.get("previous_engaged_sessions")),
        })
    if comparisons:
        st.dataframe(comparisons, hide_index=True, use_container_width=True)
    else:
        st.info("No comparable content activity in these two periods.")

    if kind == "article":
        st.subheader("Topic performance")
        topics = [{
            "Topic": row.get("topic") or "Uncategorized",
            "Article sessions": _count(row.get("article_sessions")),
            "Views": _count(row.get("views")),
            "Engaged ≥10s": _rate(row.get("engaged_sessions"), row.get("article_sessions")),
            "Reached 75%": _rate(row.get("reached_75_sessions"), row.get("depth_measured_sessions")),
            "Reached 90%": _rate(row.get("reached_90_sessions"), row.get("depth_measured_sessions")),
            "Later portfolio": _rate(row.get("later_portfolio_sessions"), row.get("article_sessions")),
            "Later CV": _rate(row.get("later_cv_sessions"), row.get("article_sessions")),
            "Later contact": _rate(row.get("later_contact_sessions"), row.get("article_sessions")),
        } for row in data.get("topic_performance", [])]
        if topics:
            st.dataframe(topics, hide_index=True, use_container_width=True)

        st.subheader("First seven days after publication")
        st.caption("This normalizes articles by publication age instead of comparing unequal lifetimes. It uses each article's first seven calendar days, independent of the reporting-window filter above.")
        first7 = [{
            "Article": row.get("title") or _article_title(row.get("slug")),
            "Published": row.get("published_date"),
            "Topic": row.get("topic") or "Uncategorized",
            "Views": _count(row.get("views")),
            "Sessions": _count(row.get("sessions")),
            "Engaged ≥10s": _rate(row.get("engaged_sessions"), row.get("sessions")),
            "Reached 75%": _rate(row.get("reached_75_sessions"), row.get("depth_measured_sessions")),
        } for row in data.get("publication_age", [])]
        if first7:
            st.dataframe(first7, hide_index=True, use_container_width=True)
        else:
            st.info("No first-seven-day article history is available yet.")


def _render_experience(data: dict) -> None:
    st.subheader("Technical experience by device")
    st.caption("Browser-side document measurements: TTFB, largest-contentful-paint, cumulative layout shift and the maximum observed interaction-event duration. Small samples can move sharply; these show association with engagement, not causation.")
    rows = []
    for row in data.get("experience", []):
        measured = _count(row.get("measured_sessions"))
        slow_lcp = _count(row.get("slow_lcp_sessions"))
        slow_lcp_engaged = _count(row.get("slow_lcp_engaged_sessions"))
        rows.append({
            "Device": str(row.get("device_type") or "unknown").title(),
            "Measured sessions": measured,
            "P75 TTFB": _milliseconds(row.get("p75_ttfb_ms")),
            "P75 LCP": _milliseconds(row.get("p75_lcp_ms")),
            "P75 CLS": row.get("p75_cls") if row.get("p75_cls") is not None else "—",
            "P75 interaction": _milliseconds(row.get("p75_interaction_ms")),
            "LCP >2.5s": _rate(slow_lcp, measured),
            "Engaged among slow-LCP": _rate(slow_lcp_engaged, slow_lcp),
            "CLS >0.1": _rate(row.get("unstable_cls_sessions"), measured),
            "Interaction >200ms": _rate(row.get("slow_interaction_sessions"), measured),
        })
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.info("Awaiting browser performance events from the new instrumentation.")


def render_content_intelligence(kind: str, window: str) -> None:
    try:
        data = fetch_intelligence(window)
    except RuntimeError as exc:
        st.warning(str(exc))
        return

    quality = data.get("quality", {})
    prefix = "article" if kind == "article" else "page"
    a, b, c = st.columns(3)
    a.metric("Article views" if kind == "article" else "Portfolio page views", _count(quality.get(prefix + "_views")))
    b.metric("Reader sessions" if kind == "article" else "Portfolio sessions", _count(quality.get(prefix + "_sessions")))
    c.metric("Contact-intent sessions · whole site", _count(quality.get("contact_sessions")))
    st.caption("Sessions are anonymous browser-tab sessions, not people. Contact intent deduplicates email and LinkedIn within a session and does not confirm a message or hiring enquiry.")

    if kind == "page" and quality.get("legacy_thinking_views"):
        st.info(f"{quality['legacy_thinking_views']} historical Thinking views cannot be reliably separated into index and article visits. They remain in the established reports below.")

    performance, exposure, paths, trends, acquisition, experience, health = st.tabs([
        "Content performance", "Exposure & action", "Visitor paths", "Trends & topics",
        "Source quality", "Technical experience", "Measurement health",
    ])

    with performance:
        rows = performance_rows(data, kind)
        st.subheader("Reading progression & downstream action" if kind == "article" else "Page attention & downstream action")
        st.caption("Visible time and scroll exposure are behavioral proxies, not proof of attention or comprehension. Every rate includes its numerator and denominator.")
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)
            st.download_button("Download content report (CSV)", export_csv(rows), file_name=f"{prefix}-analytics-{window}.csv", mime="text/csv")
        else:
            st.info("No measured content views in this reporting window.")

    with exposure:
        _render_exposure(data, kind)

    with paths:
        _render_paths(data, kind)

    with trends:
        _render_trends(data, kind)

    with acquisition:
        st.subheader("Which sources bring attention and action?")
        st.caption("Whole-site session cohorts, using the first observed source/campaign in this window. Rates include counts because small samples can move sharply.")
        campaigns = []
        for row in data.get("campaigns", []):
            sessions = _count(row.get("sessions"))
            campaigns.append({
                "Source": row.get("channel"),
                "Campaign / role": row.get("campaign"),
                "Sessions": sessions,
                "Reader rate": _rate(row.get("reader_sessions"), sessions),
                "Engaged rate": _rate(row.get("engaged_sessions"), sessions),
                "CV rate": _rate(row.get("cv_sessions"), sessions),
                "Contact rate": _rate(row.get("contact_sessions"), sessions),
            })
        if campaigns:
            st.dataframe(campaigns, hide_index=True, use_container_width=True)
        else:
            st.info("No source activity in this window.")

    with experience:
        _render_experience(data)

    with health:
        content_sessions = _count(quality.get("content_sessions"))
        measured_v4 = _count(quality.get("attention_measured_content_sessions"))
        st.write(f"Last received event: {quality.get('last_event_at') or 'No events in window'}")
        st.write(f"Depth/timing measurement first seen: {quality.get('new_measurement_since') or 'Awaiting measured visitor events'}")
        st.write(f"Exposure/action measurement first seen: {quality.get('attention_measurement_since') or 'Awaiting v4 visitor events'}")
        st.write(f"Content sessions with v4 instrumentation: {_rate(measured_v4, content_sessions)}")
        st.caption("New exposure and browser-performance measurements are not backfilled. Missing historical measurements mean unavailable, not zero. Browser blocks, disabled JavaScript and failed requests can prevent collection. No persistent visitor profile is created.")

    st.caption(
        f"{data.get('period_label', window)} · since {data.get('period_since', '—')} · "
        f"previous comparison starts {data.get('previous_period_since', '—')} · generated {data.get('generated_at', '—')}"
    )
