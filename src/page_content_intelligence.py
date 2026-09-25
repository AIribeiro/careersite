"""Aggregate-only attention, content and action reporting."""
from __future__ import annotations

import csv
import io
import json
from urllib import error, request

import altair as alt
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


def _fetch_rpc(name: str, payload: dict[str, object]) -> dict:
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{name}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"apikey": ANALYTICS_PUBLISHABLE_KEY, "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            data = json.load(response)
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"{name} is temporarily unavailable.") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{name} returned an unexpected response.")
    return data


def fetch_intelligence(window: str) -> dict:
    payload = _dashboard_payload(window)
    payload["p_article_metadata"] = _article_metadata()
    try:
        data = _fetch_rpc("careersite_content_intelligence_v2", payload)
    except RuntimeError as exc:
        raise RuntimeError("Content intelligence is temporarily unavailable; established reports remain below.") from exc

    try:
        data["behavior"] = _fetch_rpc("careersite_behavior_intelligence", _dashboard_payload(window))
    except RuntimeError as exc:
        data["behavior"] = {}
        data["behavior_error"] = str(exc)
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
            "Deep reads ≥30s + 90%": _rate(row.get("deep_read_sessions"), depth_n),
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



def _number(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _chart_height(count: int, *, per_row: int = 34, minimum: int = 260, maximum: int = 720) -> int:
    return max(minimum, min(maximum, per_row * max(1, count)))


def _exact_metrics(title: str, rows: list[dict]) -> None:
    if not rows:
        return
    with st.expander(title, expanded=False):
        st.dataframe(rows, hide_index=True, use_container_width=True)


def _rate_heatmap(rows: list[dict], label_field: str, metrics: tuple[str, ...], title: str) -> None:
    values: list[dict] = []
    for row in rows:
        for metric in metrics:
            value = row.get(metric)
            if value is None:
                continue
            values.append({
                "Label": row.get(label_field) or "Unknown",
                "Metric": metric,
                "Rate": float(value),
                "Rate label": f"{float(value):.1f}%",
            })
    if not values:
        return

    order = [str(row.get(label_field) or "Unknown") for row in rows]
    base = (
        alt.Chart(alt.Data(values=values))
        .encode(
            x=alt.X("Metric:N", title=None, sort=list(metrics), axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("Label:N", title=None, sort=order, axis=alt.Axis(labelLimit=320)),
            tooltip=[
                alt.Tooltip("Label:N"),
                alt.Tooltip("Metric:N"),
                alt.Tooltip("Rate:Q", title="Rate", format=".1f"),
            ],
        )
    )
    heat = base.mark_rect(cornerRadius=3).encode(
        color=alt.Color("Rate:Q", title="Rate %", scale=alt.Scale(scheme="blues"))
    )
    labels = base.mark_text(fontSize=11).encode(
        text="Rate label:N",
        color=alt.condition("datum.Rate >= 55", alt.value("white"), alt.value("#0f172a")),
    )
    st.altair_chart(
        (heat + labels).properties(height=_chart_height(len(rows), per_row=38), title=title),
        use_container_width=True,
    )


def _content_visual_rows(data: dict, kind: str) -> list[dict]:
    rows: list[dict] = []
    for row in data.get("performance", []):
        if row.get("kind") != kind:
            continue
        sessions = _count(row.get("sessions"))
        depth = _count(row.get("depth_measured_sessions"))
        rows.append({
            "Content": _article_title(row["content"]) if kind == "article" else content_label(row["content"]),
            "Views": _count(row.get("views")),
            "Sessions": sessions,
            "Avg visible seconds": _number(row.get("avg_active_seconds")),
            "Engaged": _percentage(row.get("engaged_sessions"), sessions),
            "Reached 25": _percentage(row.get("quarter_sessions"), depth),
            "Reached 50": _percentage(row.get("halfway_sessions"), depth),
            "Reached 75": _percentage(row.get("three_quarter_sessions"), depth),
            "Reached 90": _percentage(row.get("bottom_sessions"), depth),
            "Deep read": _percentage(row.get("deep_read_sessions"), depth),
            "Share": _percentage(row.get("sharing_sessions"), sessions),
            "Later portfolio": _percentage(row.get("later_portfolio_sessions"), sessions),
            "Later CV": _percentage(row.get("later_cv_sessions"), sessions),
            "Later contact": _percentage(row.get("later_contact_sessions"), sessions),
        })
    return rows


def _render_content_performance(data: dict, kind: str, window: str, prefix: str) -> None:
    exact_rows = performance_rows(data, kind)
    visual_rows = _content_visual_rows(data, kind)
    st.subheader("Reading progression & downstream action" if kind == "article" else "Page attention & downstream action")
    st.caption(
        "Visual time and scroll exposure are behavioral proxies, not proof of attention or comprehension. "
        "Rates remain exposure-based; hover any mark for the underlying values."
    )
    if not visual_rows:
        st.info("No measured content views in this reporting window.")
        return

    total_views = sum(_count(row.get("Views")) for row in visual_rows)
    total_content_sessions = sum(_count(row.get("Sessions")) for row in visual_rows)
    timed = [row["Avg visible seconds"] for row in visual_rows if row.get("Avg visible seconds") is not None]
    k1, k2, k3 = st.columns(3)
    k1.metric("Content views", total_views)
    k2.metric("Content-view sessions", total_content_sessions)
    k3.metric("Median content visible time", _seconds(sorted(timed)[len(timed) // 2]) if timed else "—")

    bubble_rows = [row for row in visual_rows if row.get("Avg visible seconds") is not None and row.get("Engaged") is not None]
    if bubble_rows:
        bubble = (
            alt.Chart(alt.Data(values=bubble_rows))
            .mark_circle(opacity=0.84, stroke="white", strokeWidth=1.5)
            .encode(
                x=alt.X("Sessions:Q", title="Content-view sessions", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Avg visible seconds:Q", title="Average visible time (seconds)", scale=alt.Scale(zero=True)),
                size=alt.Size("Views:Q", title="Views", scale=alt.Scale(range=[180, 1800])),
                color=alt.Color("Engaged:Q", title="Engaged ≥10s %", scale=alt.Scale(scheme="blues")),
                tooltip=[
                    alt.Tooltip("Content:N"),
                    alt.Tooltip("Views:Q", format=","),
                    alt.Tooltip("Sessions:Q", format=","),
                    alt.Tooltip("Avg visible seconds:Q", title="Avg visible seconds", format=".1f"),
                    alt.Tooltip("Engaged:Q", title="Engaged ≥10s", format=".1f"),
                    alt.Tooltip("Reached 75:Q", title="Reached 75%", format=".1f"),
                    alt.Tooltip("Later CV:Q", title="Later CV", format=".1f"),
                    alt.Tooltip("Later contact:Q", title="Later contact", format=".1f"),
                ],
            )
            .properties(height=410, title="Attention landscape")
            .interactive()
        )
        st.altair_chart(bubble, use_container_width=True)

    _rate_heatmap(
        visual_rows,
        "Content",
        ("Engaged", "Reached 25", "Reached 50", "Reached 75", "Reached 90", "Deep read"),
        "Reading progression by content (%)",
    )
    _rate_heatmap(
        visual_rows,
        "Content",
        ("Share", "Later portfolio", "Later CV", "Later contact"),
        "Downstream action by content (%)",
    )

    _exact_metrics("Exact content-performance metrics", exact_rows)
    st.download_button(
        "Download content report (CSV)",
        export_csv(exact_rows),
        file_name=f"{prefix}-analytics-{window}.csv",
        mime="text/csv",
    )


def _campaign_visual_rows(data: dict) -> list[dict]:
    rows: list[dict] = []
    for row in data.get("campaigns", []):
        sessions = _count(row.get("sessions"))
        source = row.get("channel") or "direct/unknown"
        campaign = row.get("campaign") or "untagged"
        rows.append({
            "Source / campaign": f"{source} · {campaign}",
            "Source": source,
            "Campaign": campaign,
            "Sessions": sessions,
            "Reader sessions": _count(row.get("reader_sessions")),
            "Engaged sessions": _count(row.get("engaged_sessions")),
            "CV sessions": _count(row.get("cv_sessions")),
            "Contact sessions": _count(row.get("contact_sessions")),
            "Reader": _percentage(row.get("reader_sessions"), sessions),
            "Engaged": _percentage(row.get("engaged_sessions"), sessions),
            "CV": _percentage(row.get("cv_sessions"), sessions),
            "Contact": _percentage(row.get("contact_sessions"), sessions),
        })
    return rows


def _render_source_quality(data: dict) -> None:
    st.subheader("Which sources bring attention and action?")
    st.caption(
        "Whole-site session cohorts using the first observed source/campaign in the window. "
        "Charts show quality and action rates alongside volume; low-volume cohorts can move sharply."
    )
    visual_rows = _campaign_visual_rows(data)
    if not visual_rows:
        st.info("No source activity in this window.")
        return

    bubble_rows = [row for row in visual_rows if row.get("Engaged") is not None]
    if bubble_rows:
        bubble = (
            alt.Chart(alt.Data(values=bubble_rows))
            .mark_circle(opacity=0.84, stroke="white", strokeWidth=1.5)
            .encode(
                x=alt.X("Sessions:Q", title="Sessions", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Engaged:Q", title="Engaged session rate (%)", scale=alt.Scale(zero=True)),
                size=alt.Size("Reader sessions:Q", title="Reader sessions", scale=alt.Scale(range=[180, 1700])),
                color=alt.Color("Contact:Q", title="Contact rate %", scale=alt.Scale(scheme="blues")),
                tooltip=[
                    alt.Tooltip("Source:N"),
                    alt.Tooltip("Campaign:N"),
                    alt.Tooltip("Sessions:Q", format=","),
                    alt.Tooltip("Reader:Q", title="Reader rate", format=".1f"),
                    alt.Tooltip("Engaged:Q", title="Engaged rate", format=".1f"),
                    alt.Tooltip("CV:Q", title="CV rate", format=".1f"),
                    alt.Tooltip("Contact:Q", title="Contact rate", format=".1f"),
                ],
            )
            .properties(height=410, title="Source quality: volume vs engagement")
            .interactive()
        )
        st.altair_chart(bubble, use_container_width=True)

    _rate_heatmap(
        visual_rows,
        "Source / campaign",
        ("Reader", "Engaged", "CV", "Contact"),
        "Source-to-action heatmap (%)",
    )

    exact = [{
        "Source": row["Source"],
        "Campaign / role": row["Campaign"],
        "Sessions": row["Sessions"],
        "Reader rate": _rate(row["Reader sessions"], row["Sessions"]),
        "Engaged rate": _rate(row["Engaged sessions"], row["Sessions"]),
        "CV rate": _rate(row["CV sessions"], row["Sessions"]),
        "Contact rate": _rate(row["Contact sessions"], row["Sessions"]),
    } for row in visual_rows]
    _exact_metrics("Exact source-quality metrics", exact)



def _render_exposure(data: dict, kind: str) -> None:
    if kind == "article":
        st.subheader("Article-card click-through")
        st.caption(
            "The denominator is sessions where the specific card was at least 50% visible. "
            "A click is counted only for an exposed card in the same session."
        )
        raw_cards = data.get("article_cards", [])
        card_visual = [{
            "Article / card": row.get("label") or row.get("element_key") or "Article",
            "Placement": row.get("placement") or "unknown",
            "Exposed sessions": _count(row.get("exposed_sessions")),
            "Click sessions": _count(row.get("click_sessions")),
            "CTR": _percentage(row.get("click_sessions"), row.get("exposed_sessions")),
        } for row in raw_cards]
        if card_visual:
            chart_rows = [row for row in card_visual if row.get("CTR") is not None]
            if chart_rows:
                chart = (
                    alt.Chart(alt.Data(values=chart_rows))
                    .mark_bar(cornerRadiusEnd=6)
                    .encode(
                        x=alt.X("CTR:Q", title="Click-through rate (%)", scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("Article / card:N", title=None, sort="-x", axis=alt.Axis(labelLimit=320)),
                        color=alt.Color("Placement:N", title="Placement"),
                        tooltip=[
                            alt.Tooltip("Article / card:N"),
                            alt.Tooltip("Placement:N"),
                            alt.Tooltip("Exposed sessions:Q", format=","),
                            alt.Tooltip("Click sessions:Q", format=","),
                            alt.Tooltip("CTR:Q", format=".1f"),
                        ],
                    )
                    .properties(height=_chart_height(len(chart_rows)), title="Article-card CTR")
                )
                st.altair_chart(chart, use_container_width=True)
            exact = [{
                "Article / card": row["Article / card"],
                "Placement": row["Placement"],
                "Exposed sessions": row["Exposed sessions"],
                "Click sessions": row["Click sessions"],
                "CTR": _rate(row["Click sessions"], row["Exposed sessions"]),
            } for row in card_visual]
            _exact_metrics("Exact article-card CTR metrics", exact)
        else:
            st.info("Awaiting article-card exposure events from the new instrumentation.")

    st.subheader("CTA performance by placement")
    st.caption("Header, content-section, article-footer and footer CTAs are measured against sessions that actually saw each CTA.")
    cta_visual = [{
        "CTA": str(row.get("element_key") or "cta").replace("_", " ").title(),
        "Label": row.get("label") or "—",
        "Placement": row.get("placement") or "—",
        "Exposed sessions": _count(row.get("exposed_sessions")),
        "Click sessions": _count(row.get("click_sessions")),
        "CTR": _percentage(row.get("click_sessions"), row.get("exposed_sessions")),
    } for row in data.get("cta_placements", [])]
    if cta_visual:
        chart_rows = [row for row in cta_visual if row.get("CTR") is not None]
        if chart_rows:
            chart = (
                alt.Chart(alt.Data(values=chart_rows))
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("CTR:Q", title="Click-through rate (%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Label:N", title=None, sort="-x", axis=alt.Axis(labelLimit=280)),
                    color=alt.Color("Placement:N", title="Placement"),
                    tooltip=[
                        alt.Tooltip("CTA:N"),
                        alt.Tooltip("Label:N"),
                        alt.Tooltip("Placement:N"),
                        alt.Tooltip("Exposed sessions:Q", format=","),
                        alt.Tooltip("Click sessions:Q", format=","),
                        alt.Tooltip("CTR:Q", format=".1f"),
                    ],
                )
                .properties(height=_chart_height(len(chart_rows)), title="CTA conversion after exposure")
            )
            st.altair_chart(chart, use_container_width=True)
        exact = [{
            "CTA": row["CTA"],
            "Label": row["Label"],
            "Placement": row["Placement"],
            "Exposed sessions": row["Exposed sessions"],
            "Click sessions": row["Click sessions"],
            "CTR": _rate(row["Click sessions"], row["Exposed sessions"]),
        } for row in cta_visual]
        _exact_metrics("Exact CTA metrics", exact)
    else:
        st.info("Awaiting CTA exposure events from the new instrumentation.")

    if kind == "page":
        st.subheader("Section reach")
        st.caption("A section counts as reached when at least 15% of it enters the viewport. The denominator is sessions that viewed that page.")
        section_visual = [{
            "Page": content_label(str(row.get("page") or "")),
            "Section": row.get("section_label") or str(row.get("section_key") or "").replace("-", " ").title(),
            "Reached sessions": _count(row.get("reached_sessions")),
            "Page sessions": _count(row.get("page_sessions")),
            "Reach": _percentage(row.get("reached_sessions"), row.get("page_sessions")),
        } for row in data.get("section_reach", [])]
        if section_visual:
            chart_rows = [dict(row, **{"Page · Section": f"{row['Page']} · {row['Section']}"}) for row in section_visual if row.get("Reach") is not None]
            if chart_rows:
                chart = (
                    alt.Chart(alt.Data(values=chart_rows))
                    .mark_bar(cornerRadiusEnd=6)
                    .encode(
                        x=alt.X("Reach:Q", title="Reached page sessions (%)", scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("Page · Section:N", title=None, sort="-x", axis=alt.Axis(labelLimit=340)),
                        color=alt.Color("Page:N", title="Page"),
                        tooltip=[
                            alt.Tooltip("Page:N"),
                            alt.Tooltip("Section:N"),
                            alt.Tooltip("Reached sessions:Q", format=","),
                            alt.Tooltip("Page sessions:Q", format=","),
                            alt.Tooltip("Reach:Q", format=".1f"),
                        ],
                    )
                    .properties(height=_chart_height(len(chart_rows)), title="Section reach")
                )
                st.altair_chart(chart, use_container_width=True)
            exact = [{
                "Page": row["Page"],
                "Section": row["Section"],
                "Reached sessions": row["Reached sessions"],
                "Page sessions": row["Page sessions"],
                "Reach": _rate(row["Reached sessions"], row["Page sessions"]),
            } for row in section_visual]
            _exact_metrics("Exact section-reach metrics", exact)
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
    funnel_rows = [
        {"Stage": "Article", "Sessions": article_sessions},
        {"Stage": "Impact after article", "Sessions": article_impact},
        {"Stage": "CV after Impact", "Sessions": article_impact_cv},
    ]
    funnel_chart = (
        alt.Chart(alt.Data(values=funnel_rows))
        .mark_bar(cornerRadiusEnd=8)
        .encode(
            x=alt.X("Sessions:Q", title="Sessions", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Stage:N", title=None, sort=list(reversed([row["Stage"] for row in funnel_rows]))),
            color=alt.Color(
                "Stage:N",
                title=None,
                scale=alt.Scale(domain=[row["Stage"] for row in funnel_rows], range=["#2563eb", "#0ea5e9", "#16a34a"]),
                legend=None,
            ),
            tooltip=[alt.Tooltip("Stage:N"), alt.Tooltip("Sessions:Q", format=",")],
        )
        .properties(height=220)
    )
    st.altair_chart(funnel_chart, use_container_width=True)
    f1, f2, f3 = st.columns(3)
    f1.metric("Article sessions", article_sessions)
    f2.metric("Article → Impact", _rate(article_impact, article_sessions))
    f3.metric("Article → Impact → CV", _rate(article_impact_cv, article_sessions))
    if article_impact:
        st.caption(f"CV after reaching Impact: {_rate(article_impact_cv, article_impact)}.")

    multi = data.get("multi_article", {})
    readers = _count(multi.get("reader_sessions"))
    multi_readers = _count(multi.get("multi_article_sessions"))
    st.subheader("Multi-article reading")
    st.progress(min(1.0, multi_readers / readers) if readers else 0.0, text=f"{_rate(multi_readers, readers)} read 2+ different articles in one session")

    st.subheader("Time to first meaningful action")
    action_labels = {"case_study": "Open Leadership Impact", "cv": "Download CV", "contact": "Click contact"}
    raw_actions = data.get("time_to_action", [])
    action_visual = [{
        "Action": action_labels.get(str(row.get("action")), str(row.get("action")).replace("_", " ").title()),
        "Sessions": _count(row.get("sessions")),
        "Median seconds": _number(row.get("median_seconds")),
        "Average seconds": _number(row.get("avg_seconds")),
    } for row in raw_actions]
    if action_visual:
        chart_rows: list[dict] = []
        for row in action_visual:
            if row["Median seconds"] is not None:
                chart_rows.append({"Action": row["Action"], "Measure": "Median", "Seconds": row["Median seconds"], "Sessions": row["Sessions"]})
            if row["Average seconds"] is not None:
                chart_rows.append({"Action": row["Action"], "Measure": "Average", "Seconds": row["Average seconds"], "Sessions": row["Sessions"]})
        if chart_rows:
            chart = (
                alt.Chart(alt.Data(values=chart_rows))
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Seconds:Q", title="Seconds from session entry"),
                    y=alt.Y("Action:N", title=None),
                    color=alt.Color("Measure:N", title=None, scale=alt.Scale(domain=["Median", "Average"], range=["#2563eb", "#94a3b8"])),
                    yOffset="Measure:N",
                    tooltip=[
                        alt.Tooltip("Action:N"),
                        alt.Tooltip("Measure:N"),
                        alt.Tooltip("Seconds:Q", format=".1f"),
                        alt.Tooltip("Sessions:Q", format=","),
                    ],
                )
                .properties(height=250, title="Speed to meaningful action")
            )
            st.altair_chart(chart, use_container_width=True)
        exact = [{
            "Action": row["Action"],
            "Sessions": row["Sessions"],
            "Median time": _seconds(row["Median seconds"]),
            "Average time": _seconds(row["Average seconds"]),
        } for row in action_visual]
        _exact_metrics("Exact action-timing metrics", exact)
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

def _percentage(numerator: object, denominator: object) -> float | None:
    n, d = _count(numerator), _count(denominator)
    if not d:
        return None
    return round(100 * n / d, 1)


def _trend_visual_rows(data: dict, kind: str) -> list[dict]:
    rows: list[dict] = []
    for row in data.get("period_comparison", []):
        if row.get("kind") != kind:
            continue
        current = _count(row.get("current_sessions"))
        previous = _count(row.get("previous_sessions"))
        rows.append({
            "Content": _article_title(row["content"]) if kind == "article" else content_label(row["content"]),
            "Current sessions": current,
            "Previous sessions": previous,
            "Session change %": _percentage(current - previous, previous) if previous else None,
            "Current engaged": _count(row.get("current_engaged_sessions")),
            "Previous engaged": _count(row.get("previous_engaged_sessions")),
        })
    return rows


def _topic_visual_rows(data: dict) -> list[dict]:
    rows: list[dict] = []
    for row in data.get("topic_performance", []):
        sessions = _count(row.get("article_sessions"))
        depth = _count(row.get("depth_measured_sessions"))
        rows.append({
            "Topic": row.get("topic") or "Uncategorized",
            "Article sessions": sessions,
            "Views": _count(row.get("views")),
            "Engaged %": _percentage(row.get("engaged_sessions"), sessions),
            "Reached 75%": _percentage(row.get("reached_75_sessions"), depth),
            "Reached 90%": _percentage(row.get("reached_90_sessions"), depth),
            "Later portfolio %": _percentage(row.get("later_portfolio_sessions"), sessions),
            "Later CV %": _percentage(row.get("later_cv_sessions"), sessions),
            "Later contact %": _percentage(row.get("later_contact_sessions"), sessions),
        })
    return rows


def _topic_heatmap_rows(rows: list[dict]) -> list[dict]:
    metrics = (
        "Engaged %",
        "Reached 75%",
        "Reached 90%",
        "Later portfolio %",
        "Later CV %",
        "Later contact %",
    )
    heatmap: list[dict] = []
    for row in rows:
        for metric in metrics:
            value = row.get(metric)
            if value is None:
                continue
            heatmap.append({
                "Topic": row["Topic"],
                "Metric": metric.replace(" %", ""),
                "Rate": float(value),
                "Label": f"{float(value):.1f}%",
            })
    return heatmap


def _first7_visual_rows(data: dict) -> list[dict]:
    rows: list[dict] = []
    for row in data.get("publication_age", []):
        sessions = _count(row.get("sessions"))
        depth = _count(row.get("depth_measured_sessions"))
        rows.append({
            "Article": row.get("title") or _article_title(row.get("slug")),
            "Published": row.get("published_date") or "—",
            "Topic": row.get("topic") or "Uncategorized",
            "Views": _count(row.get("views")),
            "Sessions": sessions,
            "Engaged %": _percentage(row.get("engaged_sessions"), sessions),
            "Reached 75%": _percentage(row.get("reached_75_sessions"), depth),
        })
    return rows


def _render_period_visuals(rows: list[dict]) -> None:
    if not rows:
        return

    current_total = sum(_count(row.get("Current sessions")) for row in rows)
    previous_total = sum(_count(row.get("Previous sessions")) for row in rows)
    delta = _percentage(current_total - previous_total, previous_total) if previous_total else None

    a, b, c = st.columns(3)
    a.metric("Current sessions", current_total)
    b.metric("Previous-period sessions", previous_total)
    c.metric(
        "Session movement",
        f"{delta:+.1f}%" if delta is not None else ("New activity" if current_total else "—"),
    )

    long_rows: list[dict] = []
    for row in rows:
        long_rows.extend([
            {
                "Content": row["Content"],
                "Period": "Previous",
                "Sessions": row["Previous sessions"],
            },
            {
                "Content": row["Content"],
                "Period": "Current",
                "Sessions": row["Current sessions"],
            },
        ])

    comparison = (
        alt.Chart(alt.Data(values=long_rows))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X("Sessions:Q", title="Anonymous sessions", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y(
                "Content:N",
                title=None,
                sort=alt.SortField(field="Sessions", order="descending"),
                axis=alt.Axis(labelLimit=300),
            ),
            color=alt.Color(
                "Period:N",
                title=None,
                scale=alt.Scale(domain=["Previous", "Current"], range=["#94a3b8", "#2563eb"]),
                legend=alt.Legend(orient="top"),
            ),
            yOffset="Period:N",
            tooltip=[
                alt.Tooltip("Content:N"),
                alt.Tooltip("Period:N"),
                alt.Tooltip("Sessions:Q", format=","),
            ],
        )
        .properties(height=max(280, min(650, 34 * max(1, len(rows)))), title="Current vs previous period")
    )
    st.altair_chart(comparison, use_container_width=True)

    change_rows = [row for row in rows if row.get("Session change %") is not None]
    if change_rows:
        movement = (
            alt.Chart(alt.Data(values=change_rows))
            .mark_bar(cornerRadiusEnd=5)
            .encode(
                x=alt.X(
                    "Session change %:Q",
                    title="Change in sessions (%)",
                    axis=alt.Axis(format="+.0f"),
                ),
                y=alt.Y(
                    "Content:N",
                    title=None,
                    sort=alt.SortField(field="Session change %", order="descending"),
                    axis=alt.Axis(labelLimit=300),
                ),
                color=alt.condition(
                    "datum['Session change %'] >= 0",
                    alt.value("#16a34a"),
                    alt.value("#dc2626"),
                ),
                tooltip=[
                    alt.Tooltip("Content:N"),
                    alt.Tooltip("Current sessions:Q", format=","),
                    alt.Tooltip("Previous sessions:Q", format=","),
                    alt.Tooltip("Session change %:Q", title="Change", format="+.1f"),
                ],
            )
            .properties(height=max(260, min(600, 32 * len(change_rows))), title="Momentum by content")
        )
        st.altair_chart(movement, use_container_width=True)


def _render_topic_visuals(rows: list[dict]) -> None:
    if not rows:
        return

    st.subheader("Topic landscape")
    st.caption(
        "Bubble position separates reach from engagement. Bubble size represents views; "
        "colour represents later contact rate. Hover for the exact rates and counts."
    )

    bubble_rows = [
        row for row in rows
        if row.get("Engaged %") is not None
    ]
    if bubble_rows:
        bubble = (
            alt.Chart(alt.Data(values=bubble_rows))
            .mark_circle(opacity=0.85, stroke="white", strokeWidth=1.5)
            .encode(
                x=alt.X("Article sessions:Q", title="Article sessions", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Engaged %:Q", title="Engaged ≥10s (%)", scale=alt.Scale(zero=True)),
                size=alt.Size("Views:Q", title="Views", scale=alt.Scale(range=[180, 1800])),
                color=alt.Color(
                    "Later contact %:Q",
                    title="Later contact %",
                    scale=alt.Scale(scheme="blues"),
                ),
                tooltip=[
                    alt.Tooltip("Topic:N"),
                    alt.Tooltip("Article sessions:Q", format=","),
                    alt.Tooltip("Views:Q", format=","),
                    alt.Tooltip("Engaged %:Q", format=".1f"),
                    alt.Tooltip("Reached 75%:Q", format=".1f"),
                    alt.Tooltip("Later portfolio %:Q", format=".1f"),
                    alt.Tooltip("Later CV %:Q", format=".1f"),
                    alt.Tooltip("Later contact %:Q", format=".1f"),
                ],
            )
            .properties(height=420)
            .interactive()
        )
        labels = (
            alt.Chart(alt.Data(values=bubble_rows))
            .mark_text(dy=-15, fontSize=12)
            .encode(
                x="Article sessions:Q",
                y="Engaged %:Q",
                text="Topic:N",
            )
        )
        st.altair_chart(bubble + labels, use_container_width=True)

    heat_rows = _topic_heatmap_rows(rows)
    if heat_rows:
        st.subheader("Topic performance heatmap")
        st.caption("Each cell is an exposure-aware session rate. Blank cells mean the denominator was unavailable, not zero.")
        heat = (
            alt.Chart(alt.Data(values=heat_rows))
            .mark_rect(cornerRadius=3)
            .encode(
                x=alt.X("Metric:N", title=None, axis=alt.Axis(labelAngle=-25)),
                y=alt.Y("Topic:N", title=None, sort="-x", axis=alt.Axis(labelLimit=220)),
                color=alt.Color("Rate:Q", title="Rate %", scale=alt.Scale(scheme="blues")),
                tooltip=[
                    alt.Tooltip("Topic:N"),
                    alt.Tooltip("Metric:N"),
                    alt.Tooltip("Rate:Q", format=".1f"),
                ],
            )
            .properties(height=max(220, 42 * len(rows)))
        )
        labels = (
            alt.Chart(alt.Data(values=heat_rows))
            .mark_text(fontSize=11)
            .encode(
                x="Metric:N",
                y=alt.Y("Topic:N", sort="-x"),
                text="Label:N",
                color=alt.condition("datum.Rate >= 55", alt.value("white"), alt.value("#0f172a")),
            )
        )
        st.altair_chart(heat + labels, use_container_width=True)


def _render_first7_visuals(rows: list[dict]) -> None:
    if not rows:
        return

    chart_rows = sorted(rows, key=lambda row: _count(row.get("Views")), reverse=True)
    chart = (
        alt.Chart(alt.Data(values=chart_rows))
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X("Views:Q", title="Views in first seven days", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y(
                "Article:N",
                title=None,
                sort="-x",
                axis=alt.Axis(labelLimit=330),
            ),
            color=alt.Color("Topic:N", title="Topic", legend=alt.Legend(orient="bottom")),
            tooltip=[
                alt.Tooltip("Article:N"),
                alt.Tooltip("Topic:N"),
                alt.Tooltip("Published:N"),
                alt.Tooltip("Views:Q", format=","),
                alt.Tooltip("Sessions:Q", format=","),
                alt.Tooltip("Engaged %:Q", format=".1f"),
                alt.Tooltip("Reached 75%:Q", format=".1f"),
            ],
        )
        .properties(height=max(300, min(700, 34 * len(chart_rows))), title="First-seven-day launch performance")
    )
    st.altair_chart(chart, use_container_width=True)


def _render_trends(data: dict, kind: str) -> None:
    st.subheader("Period-over-period movement")
    st.caption(
        "The selected window is compared with the immediately preceding window of equal duration. "
        "Charts are descriptive; low-volume content can move sharply."
    )

    visual_rows = _trend_visual_rows(data, kind)
    if visual_rows:
        _render_period_visuals(visual_rows)
    else:
        st.info("No comparable content activity in these two periods.")

    with st.expander("Exact period comparison", expanded=False):
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

    if kind == "article":
        topic_rows = _topic_visual_rows(data)
        st.subheader("Topic performance")
        if topic_rows:
            _render_topic_visuals(topic_rows)
            with st.expander("Exact topic metrics", expanded=False):
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
                st.dataframe(topics, hide_index=True, use_container_width=True)
        else:
            st.info("No topic-performance activity in this reporting window.")

        st.subheader("First seven days after publication")
        st.caption(
            "This normalizes articles by publication age instead of comparing unequal lifetimes. "
            "It uses each article's first seven calendar days, independent of the reporting-window filter above."
        )
        first7_rows = _first7_visual_rows(data)
        if first7_rows:
            _render_first7_visuals(first7_rows)
            with st.expander("Exact first-seven-day metrics", expanded=False):
                first7 = [{
                    "Article": row.get("title") or _article_title(row.get("slug")),
                    "Published": row.get("published_date"),
                    "Topic": row.get("topic") or "Uncategorized",
                    "Views": _count(row.get("views")),
                    "Sessions": _count(row.get("sessions")),
                    "Engaged ≥10s": _rate(row.get("engaged_sessions"), row.get("sessions")),
                    "Reached 75%": _rate(row.get("reached_75_sessions"), row.get("depth_measured_sessions")),
                } for row in data.get("publication_age", [])]
                st.dataframe(first7, hide_index=True, use_container_width=True)
        else:
            st.info("No first-seven-day article history is available yet.")


def _render_attention_ux(data: dict, kind: str) -> None:
    behavior = data.get("behavior", {})

    st.subheader("Section attention")
    st.caption(
        "Reach tells you whether a section entered the viewport; attention adds visible dwell time. "
        "Assisted-action rates mean the action occurred later in the same anonymous tab session, not that the section caused it."
    )
    section_visual = []
    section_exact = []
    for row in behavior.get("section_attention", []):
        is_article = bool(row.get("article_slug"))
        if is_article != (kind == "article"):
            continue
        reached = _count(row.get("reached_sessions"))
        measured = _count(row.get("measured_attention_sessions"))
        content = _article_title(row.get("article_slug")) if is_article else content_label(str(row.get("page") or ""))
        section = row.get("section_label") or str(row.get("section_key") or "").replace("-", " ").title()
        section_visual.append({
            "Content · Section": f"{content} · {section}",
            "Reached sessions": reached,
            "Avg attention seconds": _number(row.get("avg_attention_seconds")),
            "Median attention seconds": _number(row.get("median_attention_seconds")),
            "Attentive 5s": _percentage(row.get("attentive_5s_sessions"), reached),
            "Later Impact": _percentage(row.get("later_impact_sessions"), reached),
            "Later CV": _percentage(row.get("later_cv_sessions"), reached),
            "Later contact": _percentage(row.get("later_contact_sessions"), reached),
        })
        section_exact.append({
            "Content": content,
            "Section": section,
            "Reached sessions": reached,
            "Attention measured": _rate(measured, reached),
            "Avg attention": _seconds(row.get("avg_attention_seconds")),
            "Median attention": _seconds(row.get("median_attention_seconds")),
            "P75 attention": _seconds(row.get("p75_attention_seconds")),
            "≥5s attention": _rate(row.get("attentive_5s_sessions"), reached),
            "Later Impact": _rate(row.get("later_impact_sessions"), reached),
            "Later CV": _rate(row.get("later_cv_sessions"), reached),
            "Later contact": _rate(row.get("later_contact_sessions"), reached),
        })
    if section_visual:
        chart_rows = [row for row in section_visual if row.get("Avg attention seconds") is not None]
        if chart_rows:
            chart = (
                alt.Chart(alt.Data(values=chart_rows))
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Avg attention seconds:Q", title="Average visible attention (seconds)"),
                    y=alt.Y("Content · Section:N", title=None, sort="-x", axis=alt.Axis(labelLimit=360)),
                    color=alt.Color("Later contact:Q", title="Later contact %", scale=alt.Scale(scheme="blues")),
                    tooltip=[
                        alt.Tooltip("Content · Section:N"),
                        alt.Tooltip("Reached sessions:Q", format=","),
                        alt.Tooltip("Avg attention seconds:Q", format=".1f"),
                        alt.Tooltip("Attentive 5s:Q", title="≥5s attention %", format=".1f"),
                        alt.Tooltip("Later CV:Q", format=".1f"),
                        alt.Tooltip("Later contact:Q", format=".1f"),
                    ],
                )
                .properties(height=_chart_height(len(chart_rows)), title="Where visitors actually spend visible time")
            )
            st.altair_chart(chart, use_container_width=True)
        _rate_heatmap(
            section_visual,
            "Content · Section",
            ("Attentive 5s", "Later Impact", "Later CV", "Later contact"),
            "Section attention → later action (%)",
        )
        _exact_metrics("Exact section-attention metrics", section_exact)
    else:
        st.info("Awaiting Components-v2 section-attention events.")

    st.subheader("Element attention")
    st.caption(
        "Cards and CTAs are measured while at least 50% visible. Hover is a consideration signal, not intent. "
        "For Article Views, article-card rows describe the cards that earned the article open."
    )
    element_visual = []
    element_exact = []
    for row in behavior.get("element_attention", []):
        is_article_context = bool(row.get("article_slug"))
        element_kind = str(row.get("element_kind") or "")
        if kind == "article":
            include = is_article_context or element_kind == "article_card"
        else:
            include = not is_article_context
        if not include:
            continue
        exposed = _count(row.get("exposed_sessions"))
        label = row.get("element_label") or row.get("element_key") or "—"
        element_visual.append({
            "Element": label,
            "Type": element_kind.replace("_", " ").title(),
            "Placement": row.get("element_placement") or "—",
            "Exposed sessions": exposed,
            "Avg attention seconds": _number(row.get("avg_attention_seconds")),
            "Avg hover seconds": _number(row.get("avg_hover_seconds")),
            "Attentive 2s": _percentage(row.get("attentive_2s_sessions"), exposed),
            "Hover": _percentage(row.get("hover_sessions"), exposed),
            "Click": _percentage(row.get("click_sessions"), exposed),
        })
        element_exact.append({
            "Type": element_kind.replace("_", " ").title(),
            "Element": label,
            "Placement": row.get("element_placement") or "—",
            "Exposed sessions": exposed,
            "Attention measured": _rate(row.get("measured_attention_sessions"), exposed),
            "Avg attention": _seconds(row.get("avg_attention_seconds")),
            "Median attention": _seconds(row.get("median_attention_seconds")),
            "≥2s attention": _rate(row.get("attentive_2s_sessions"), exposed),
            "Hover rate": _rate(row.get("hover_sessions"), exposed),
            "Avg hover": _seconds(row.get("avg_hover_seconds")),
            "Click rate": _rate(row.get("click_sessions"), exposed),
        })
    if element_visual:
        bubble_rows = [row for row in element_visual if row.get("Avg attention seconds") is not None and row.get("Click") is not None]
        if bubble_rows:
            bubble = (
                alt.Chart(alt.Data(values=bubble_rows))
                .mark_circle(opacity=0.84, stroke="white", strokeWidth=1.5)
                .encode(
                    x=alt.X("Avg attention seconds:Q", title="Average visible attention (seconds)"),
                    y=alt.Y("Click:Q", title="Click rate (%)", scale=alt.Scale(zero=True)),
                    size=alt.Size("Exposed sessions:Q", title="Exposed sessions", scale=alt.Scale(range=[180, 1700])),
                    color=alt.Color("Hover:Q", title="Hover rate %", scale=alt.Scale(scheme="blues")),
                    shape=alt.Shape("Type:N", title="Element type"),
                    tooltip=[
                        alt.Tooltip("Element:N"),
                        alt.Tooltip("Type:N"),
                        alt.Tooltip("Placement:N"),
                        alt.Tooltip("Exposed sessions:Q", format=","),
                        alt.Tooltip("Avg attention seconds:Q", format=".1f"),
                        alt.Tooltip("Hover:Q", format=".1f"),
                        alt.Tooltip("Click:Q", format=".1f"),
                    ],
                )
                .properties(height=410, title="Attention vs action")
                .interactive()
            )
            st.altair_chart(bubble, use_container_width=True)
        _exact_metrics("Exact element-attention metrics", element_exact)
    else:
        st.info("Awaiting Components-v2 element-attention events.")

    st.subheader("CTA hesitation")
    st.caption("Time from first 50%-visible exposure to a click. Interpret long intervals alongside CTR and attention.")
    hesitation_visual = [{
        "CTA": row.get("element_label") or str(row.get("element_key") or "CTA").replace("_", " ").title(),
        "Placement": row.get("element_placement") or "—",
        "Click sessions": _count(row.get("sessions")),
        "Median seconds": _number(row.get("median_hesitation_seconds")),
        "P75 seconds": _number(row.get("p75_hesitation_seconds")),
        "Average seconds": _number(row.get("avg_hesitation_seconds")),
    } for row in behavior.get("cta_hesitation", [])]
    if hesitation_visual:
        long_rows = []
        for row in hesitation_visual:
            for metric, field in (("Median", "Median seconds"), ("P75", "P75 seconds")):
                if row[field] is not None:
                    long_rows.append({"CTA": row["CTA"], "Placement": row["Placement"], "Measure": metric, "Seconds": row[field], "Click sessions": row["Click sessions"]})
        if long_rows:
            chart = (
                alt.Chart(alt.Data(values=long_rows))
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Seconds:Q", title="Seconds from exposure to click"),
                    y=alt.Y("CTA:N", title=None, axis=alt.Axis(labelLimit=280)),
                    color=alt.Color("Measure:N", title=None, scale=alt.Scale(domain=["Median", "P75"], range=["#2563eb", "#94a3b8"])),
                    yOffset="Measure:N",
                    tooltip=["CTA:N", "Placement:N", "Measure:N", alt.Tooltip("Seconds:Q", format=".1f"), alt.Tooltip("Click sessions:Q", format=",")],
                )
                .properties(height=_chart_height(len(hesitation_visual)), title="CTA hesitation")
            )
            st.altair_chart(chart, use_container_width=True)
        exact = [{
            "CTA": row["CTA"],
            "Placement": row["Placement"],
            "Click sessions": row["Click sessions"],
            "Median hesitation": _seconds(row["Median seconds"]),
            "P75 hesitation": _seconds(row["P75 seconds"]),
            "Average hesitation": _seconds(row["Average seconds"]),
        } for row in hesitation_visual]
        _exact_metrics("Exact CTA-hesitation metrics", exact)
    else:
        st.info("Awaiting CTA-hesitation events.")

    st.subheader("Last observed reading region")
    st.caption("The final region observed before unload/context change is an abandonment clue, not proof of intent.")
    regions = []
    for row in behavior.get("last_regions", []):
        if row.get("kind") != kind:
            continue
        content = _article_title(row.get("article_slug")) if kind == "article" else content_label(str(row.get("page") or ""))
        regions.append({
            "Content · Region": f"{content} · {row.get('section_label') or str(row.get('section_key') or '').replace('-', ' ').title()}",
            "Sessions": _count(row.get("sessions")),
            "Avg scroll depth": _number(row.get("avg_scroll_depth")),
            "Avg visible seconds": _number(row.get("avg_visible_seconds")),
            "Avg max scroll speed": _number(row.get("avg_max_scroll_velocity")),
            "Avg reverse speed": _number(row.get("avg_max_reverse_scroll_velocity")),
        })
    if regions:
        chart = (
            alt.Chart(alt.Data(values=regions))
            .mark_bar(cornerRadiusEnd=6)
            .encode(
                x=alt.X("Sessions:Q", title="Sessions ending at region", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Content · Region:N", title=None, sort="-x", axis=alt.Axis(labelLimit=360)),
                color=alt.Color("Avg scroll depth:Q", title="Avg depth %", scale=alt.Scale(scheme="blues")),
                tooltip=[
                    alt.Tooltip("Content · Region:N"),
                    alt.Tooltip("Sessions:Q", format=","),
                    alt.Tooltip("Avg scroll depth:Q", format=".1f"),
                    alt.Tooltip("Avg visible seconds:Q", format=".1f"),
                    alt.Tooltip("Avg max scroll speed:Q", format=".0f"),
                    alt.Tooltip("Avg reverse speed:Q", format=".0f"),
                ],
            )
            .properties(height=_chart_height(len(regions)), title="Last observed content region")
        )
        st.altair_chart(chart, use_container_width=True)
        exact = [{
            "Content / region": row["Content · Region"],
            "Sessions": row["Sessions"],
            "Avg scroll depth": f"{row['Avg scroll depth']:.0f}%" if row["Avg scroll depth"] is not None else "—",
            "Avg visible time": _seconds(row["Avg visible seconds"]),
            "Avg max scroll speed": f"{row['Avg max scroll speed']:.0f} px/s" if row["Avg max scroll speed"] is not None else "—",
            "Avg reverse speed": f"{row['Avg reverse speed']:.0f} px/s" if row["Avg reverse speed"] is not None else "—",
        } for row in regions]
        _exact_metrics("Exact last-region metrics", exact)
    else:
        st.info("Awaiting end-of-context reading-region events.")

    st.subheader("Potential UX friction")
    st.caption("Dead and rage clicks are diagnostic signals, not definitive evidence of frustration.")
    signals = []
    for row in behavior.get("ux_signals", []):
        section_key = str(row.get("section_key") or "")
        if kind == "article" and not section_key.startswith("article-"):
            continue
        if kind == "page" and section_key.startswith("article-"):
            continue
        signals.append({
            "Signal": str(row.get("interaction_type") or "").replace("_", " ").title(),
            "Page": content_label(str(row.get("page") or "")),
            "Region": row.get("section_label") or section_key.replace("-", " ").title(),
            "Sessions": _count(row.get("sessions")),
            "Events": _count(row.get("events")),
            "Error type": row.get("error_type") or "—",
        })
    if signals:
        chart_rows = [dict(row, **{"Signal · Region": f"{row['Signal']} · {row['Page']} · {row['Region']}"}) for row in signals]
        chart = (
            alt.Chart(alt.Data(values=chart_rows))
            .mark_bar(cornerRadiusEnd=6)
            .encode(
                x=alt.X("Events:Q", title="Observed events", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Signal · Region:N", title=None, sort="-x", axis=alt.Axis(labelLimit=360)),
                color=alt.Color("Signal:N", title="Signal"),
                tooltip=["Signal:N", "Page:N", "Region:N", alt.Tooltip("Sessions:Q", format=","), alt.Tooltip("Events:Q", format=","), "Error type:N"],
            )
            .properties(height=_chart_height(len(chart_rows)), title="UX-friction signals")
        )
        st.altair_chart(chart, use_container_width=True)
        _exact_metrics("Exact UX-friction metrics", signals)
    else:
        st.info("No v2 UX-friction signals in this reporting window.")

    st.subheader("Time to first interaction")
    first = [{
        "First action": str(row.get("interaction_type") or "").title(),
        "Device": str(row.get("device_type") or "unknown").title(),
        "Sessions": _count(row.get("sessions")),
        "Median latency ms": _number(row.get("median_latency_ms")),
        "P75 latency ms": _number(row.get("p75_latency_ms")),
    } for row in behavior.get("first_interaction", [])]
    if first:
        long_rows = []
        for row in first:
            for metric, field in (("Median", "Median latency ms"), ("P75", "P75 latency ms")):
                if row[field] is not None:
                    long_rows.append({"First action": row["First action"], "Device": row["Device"], "Measure": metric, "Latency ms": row[field], "Sessions": row["Sessions"]})
        if long_rows:
            chart = (
                alt.Chart(alt.Data(values=long_rows))
                .mark_bar(cornerRadiusEnd=6)
                .encode(
                    x=alt.X("Latency ms:Q", title="Latency from page context start (ms)"),
                    y=alt.Y("First action:N", title=None),
                    color=alt.Color("Device:N", title="Device"),
                    column=alt.Column("Measure:N", title=None),
                    tooltip=["First action:N", "Device:N", "Measure:N", alt.Tooltip("Latency ms:Q", format=".0f"), alt.Tooltip("Sessions:Q", format=",")],
                )
                .properties(height=220)
            )
            st.altair_chart(chart, use_container_width=True)
        exact = [{
            "First action": row["First action"],
            "Device": row["Device"],
            "Sessions": row["Sessions"],
            "Median latency": _milliseconds(row["Median latency ms"]),
            "P75 latency": _milliseconds(row["P75 latency ms"]),
        } for row in first]
        _exact_metrics("Exact first-interaction metrics", exact)
    else:
        st.info("Awaiting first-interaction telemetry.")


def _render_experience(data: dict) -> None:
    behavior = data.get("behavior", {})
    vitals = {str(row.get("device_type") or "unknown"): row for row in behavior.get("web_vitals", [])}

    st.subheader("Technical experience by device")
    st.caption(
        "Browser-side document measurements include TTFB, FCP, LCP, CLS and interaction timing. "
        "INP is estimated from supported PerformanceEventTiming interaction IDs; browser support varies."
    )
    visual_rows = []
    exact_rows = []
    devices = {str(row.get("device_type") or "unknown") for row in data.get("experience", [])} | set(vitals)
    existing = {str(row.get("device_type") or "unknown"): row for row in data.get("experience", [])}
    for device in sorted(devices):
        row = existing.get(device, {})
        v2 = vitals.get(device, {})
        measured = _count(row.get("measured_sessions"))
        slow_lcp = _count(row.get("slow_lcp_sessions"))
        slow_lcp_engaged = _count(row.get("slow_lcp_engaged_sessions"))
        display_device = device.title()
        visual_rows.append({
            "Device": display_device,
            "Measured sessions": max(measured, _count(v2.get("fcp_sessions")), _count(v2.get("inp_sessions"))),
            "TTFB": _number(row.get("p75_ttfb_ms")),
            "FCP": _number(v2.get("p75_fcp_ms")),
            "LCP": _number(row.get("p75_lcp_ms")),
            "INP estimate": _number(v2.get("p75_inp_ms")),
            "Max interaction": _number(row.get("p75_interaction_ms")),
            "CLS": _number(row.get("p75_cls")),
            "LCP >2.5s": _percentage(slow_lcp, measured),
            "Engaged among slow-LCP": _percentage(slow_lcp_engaged, slow_lcp),
            "CLS >0.1": _percentage(row.get("unstable_cls_sessions"), measured),
        })
        exact_rows.append({
            "Device": display_device,
            "Measured sessions": max(measured, _count(v2.get("fcp_sessions")), _count(v2.get("inp_sessions"))),
            "P75 TTFB": _milliseconds(row.get("p75_ttfb_ms")),
            "P75 FCP": _milliseconds(v2.get("p75_fcp_ms")),
            "P75 LCP": _milliseconds(row.get("p75_lcp_ms")),
            "P75 CLS": row.get("p75_cls") if row.get("p75_cls") is not None else "—",
            "P75 INP estimate": _milliseconds(v2.get("p75_inp_ms")),
            "P75 max interaction": _milliseconds(row.get("p75_interaction_ms")),
            "LCP >2.5s": _rate(slow_lcp, measured),
            "Engaged among slow-LCP": _rate(slow_lcp_engaged, slow_lcp),
            "CLS >0.1": _rate(row.get("unstable_cls_sessions"), measured),
        })
    if visual_rows:
        latency_rows = []
        for row in visual_rows:
            for metric in ("TTFB", "FCP", "LCP", "INP estimate", "Max interaction"):
                if row.get(metric) is not None:
                    latency_rows.append({
                        "Device": row["Device"],
                        "Metric": metric,
                        "Milliseconds": row[metric],
                        "Measured sessions": row["Measured sessions"],
                    })
        if latency_rows:
            chart = (
                alt.Chart(alt.Data(values=latency_rows))
                .mark_bar(cornerRadiusEnd=5)
                .encode(
                    x=alt.X("Milliseconds:Q", title="P75 milliseconds"),
                    y=alt.Y("Metric:N", title=None, sort=["TTFB", "FCP", "LCP", "INP estimate", "Max interaction"]),
                    color=alt.Color("Device:N", title="Device"),
                    yOffset="Device:N",
                    tooltip=["Device:N", "Metric:N", alt.Tooltip("Milliseconds:Q", format=".0f"), alt.Tooltip("Measured sessions:Q", format=",")],
                )
                .properties(height=300, title="P75 browser experience")
            )
            st.altair_chart(chart, use_container_width=True)
        _rate_heatmap(
            visual_rows,
            "Device",
            ("LCP >2.5s", "Engaged among slow-LCP", "CLS >0.1"),
            "Experience-rate diagnostics (%)",
        )
        _exact_metrics("Exact technical-experience metrics", exact_rows)
    else:
        st.info("Awaiting browser performance events from the instrumentation.")

    st.subheader("Browser context & attention interruptions")
    summary_visual = [{
        "Device": str(row.get("device_type") or "unknown").title(),
        "Sessions": _count(row.get("sessions")),
        "Avg focus losses": _number(row.get("avg_focus_losses")),
        "Avg resizes": _number(row.get("avg_resizes")),
        "Avg orientation changes": _number(row.get("avg_orientation_changes")),
        "Avg logical cores": _number(row.get("avg_logical_cores")),
        "Avg device memory": _number(row.get("avg_device_memory_gb")),
        "Data saver": _percentage(row.get("save_data_sessions"), row.get("sessions")),
    } for row in behavior.get("behavior_summary", [])]
    if summary_visual:
        interruptions = []
        for row in summary_visual:
            for metric in ("Avg focus losses", "Avg resizes", "Avg orientation changes"):
                if row.get(metric) is not None:
                    interruptions.append({"Device": row["Device"], "Metric": metric.replace("Avg ", ""), "Average count": row[metric], "Sessions": row["Sessions"]})
        if interruptions:
            chart = (
                alt.Chart(alt.Data(values=interruptions))
                .mark_bar(cornerRadiusEnd=5)
                .encode(
                    x=alt.X("Average count:Q", title="Average events per measured session"),
                    y=alt.Y("Metric:N", title=None),
                    color=alt.Color("Device:N", title="Device"),
                    yOffset="Device:N",
                    tooltip=["Device:N", "Metric:N", alt.Tooltip("Average count:Q", format=".1f"), alt.Tooltip("Sessions:Q", format=",")],
                )
                .properties(height=230, title="Attention interruptions & viewport changes")
            )
            st.altair_chart(chart, use_container_width=True)

        exact = [{
            "Device": row["Device"],
            "Sessions": row["Sessions"],
            "Avg focus losses": row["Avg focus losses"] if row["Avg focus losses"] is not None else "—",
            "Avg resizes": row["Avg resizes"] if row["Avg resizes"] is not None else "—",
            "Avg orientation changes": row["Avg orientation changes"] if row["Avg orientation changes"] is not None else "—",
            "Avg logical cores": row["Avg logical cores"] if row["Avg logical cores"] is not None else "—",
            "Avg device memory": f"{row['Avg device memory']} GB" if row["Avg device memory"] is not None else "—",
            "Data saver": f"{row['Data saver']:.1f}%" if row["Data saver"] is not None else "—",
        } for row in summary_visual]
        _exact_metrics("Exact browser-context metrics", exact)
    else:
        st.info("Awaiting Components-v2 browser-context summaries.")


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

    performance, exposure, attention_ux, paths, trends, acquisition, experience, health = st.tabs([
        "Content performance", "Exposure & action", "Attention & UX", "Visitor paths", "Trends & topics",
        "Source quality", "Technical experience", "Measurement health",
    ])

    with performance:
        _render_content_performance(data, kind, window, prefix)

    with exposure:
        _render_exposure(data, kind)

    with attention_ux:
        _render_attention_ux(data, kind)

    with paths:
        _render_paths(data, kind)

    with trends:
        _render_trends(data, kind)

    with acquisition:
        _render_source_quality(data)

    with experience:
        _render_experience(data)

    with health:
        content_sessions = _count(quality.get("content_sessions"))
        measured_v4 = _count(quality.get("attention_measured_content_sessions"))
        behavior = data.get("behavior", {})
        behavior_quality = behavior.get("quality", {})

        coverage = _percentage(measured_v4, content_sessions)
        behavior_events = _count(behavior_quality.get("behavior_events"))
        behavior_sessions = _count(behavior_quality.get("behavior_sessions"))
        h1, h2, h3 = st.columns(3)
        h1.metric("v4+ measured content sessions", f"{coverage:.1f}%" if coverage is not None else "—")
        h2.metric("Components-v2 behavior events", behavior_events)
        h3.metric("Behavior-measured sessions", behavior_sessions)

        health_rows = [
            {"Milestone": "Last received event", "Value": quality.get("last_event_at") or "No events in window"},
            {"Milestone": "Depth/timing measurement first seen", "Value": quality.get("new_measurement_since") or "Awaiting measured visitor events"},
            {"Milestone": "Exposure/action measurement first seen", "Value": quality.get("attention_measurement_since") or "Awaiting v4 visitor events"},
            {"Milestone": "Components-v2 behavior first seen", "Value": behavior_quality.get("behavior_first_seen") or "Awaiting v5 visitor events"},
        ]
        with st.expander("Measurement timestamps & exact health details", expanded=False):
            st.dataframe(health_rows, hide_index=True, use_container_width=True)
            st.write(f"Content sessions with v4+ instrumentation: {_rate(measured_v4, content_sessions)}")
            st.write(f"Components-v2 behavior events: {behavior_events} across {behavior_sessions} anonymous sessions")

        if data.get("behavior_error"):
            st.warning(f"Advanced behavior endpoint unavailable: {data['behavior_error']}")
        st.caption(
            "Attention, hesitation and browser-performance measurements are not backfilled. "
            "Missing historical measurements mean unavailable, not zero. Browser blocks, disabled JavaScript "
            "and failed requests can prevent collection. Coordinates are used only in-memory to detect repeated "
            "nearby clicks and are never transmitted. No persistent visitor profile is created."
        )

    st.caption(
        f"{data.get('period_label', window)} · since {data.get('period_since', '—')} · "
        f"previous comparison starts {data.get('previous_period_since', '—')} · generated {data.get('generated_at', '—')}"
    )

