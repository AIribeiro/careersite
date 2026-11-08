"""Public portfolio-only analytics landing; no recruiting/market/forecast reads."""
from __future__ import annotations

import altair as alt
import streamlit as st

from analytics_reporting_period import initialize_reporting_period, remember_reporting_period
from page_analytics import (
    REPORTING_WINDOWS, REPORTING_WINDOW_LABELS, _fetch_dashboard,
    _dashboard_payload,
)
from page_article_analytics import _article_title
from page_content_intelligence import (
    _article_metadata, _fetch_rpc, content_label, fetch_intelligence,
)
from portfolio_signal_brief import ranked_portfolio_signals
from portfolio_metric_cards import portfolio_metric_grid
from page_executive_briefings_analytics import published_briefings
from page_home_journey import render_home_journey

# Routes retired in the October 2026 six-page navigation redesign.
RETIRED_ROUTES = {"presence", "certifications", "enterprise", "transformation", "governance", "consulting"}
from site_cms import fetch_published_articles
from thinking_weekly_brief import edition_label, is_weekly_brief


@st.cache_data(ttl=300, show_spinner=False)
def _lifetime_content_report() -> dict:
    return fetch_intelligence("all")


def lifetime_caption(total: int | None, measure: str) -> str:
    if total is None:
        return "Lifetime total temporarily unavailable"
    return f"Lifetime total: {total:,} {measure}"


def portfolio_visit_rows(report: dict, kind: str) -> list[dict]:
    """Classified page/article views; repeat views are not unique visitors."""
    if kind not in ("page", "article"):
        raise ValueError("Unsupported portfolio content kind")
    values = []
    for row in report.get("performance", []):
        if not isinstance(row, dict) or row.get("kind") != kind:
            continue
        views = max(0, int(row.get("views") or 0))
        if views < 1:
            continue
        content = str(row.get("content") or "")
        label = _article_title(content) if kind == "article" else content_label(content)
        if kind == "page" and content in RETIRED_ROUTES:
            label += " · retired route"
        values.append({
            "Content": label,
            "Slug": content,
            "Views": views,
            "Sessions": max(0, int(row.get("sessions") or 0)),
        })
    return sorted(values, key=lambda row: (-row["Views"], row["Content"]))


def split_editorial_rows(
    articles: list[dict], published_catalogue: list[object],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Mutually exclusive CMS-backed article, Weekly AI and briefing subsets.

    The briefing *library* is a page, never an article. Only published CMS
    kind='Executive Briefing' rows qualify; item-session reads may overlap.
    """
    from page_executive_briefings_analytics import published_briefings

    weekly = {
        article.slug: article for article in published_catalogue
        if getattr(article, "status", "") == "published" and is_weekly_brief(article)
    }
    briefings = {article.slug: article for article in published_briefings(published_catalogue)}
    essays: list[dict] = []
    editions: list[dict] = []
    briefing_rows: list[dict] = []
    for row in articles:
        slug = str(row.get("Slug") or "")
        if slug in weekly:
            item = dict(row)
            item["Title"] = item["Content"]
            item["Content"] = edition_label(weekly[slug])
            editions.append(item)
        elif slug in briefings:
            briefing_rows.append(row)
        else:
            essays.append(row)
    sort = lambda r: (-r["Views"], r["Content"])
    return sorted(essays, key=sort), sorted(editions, key=sort), sorted(briefing_rows, key=sort)


def split_reader_rows(
    articles: list[dict], published_editions: list[object],
) -> tuple[list[dict], list[dict]]:
    """Backward-compatible split for callers expecting only a weekly subset."""
    essays, weekly, briefings = split_editorial_rows(articles, published_editions)
    return sorted(essays + briefings, key=lambda r: (-r["Views"], r["Content"])), weekly


def _ranking_chart(rows: list[dict], *, compact: bool = False) -> None:
    """Equal chart heights keep all three content cards aligned on desktop."""
    if not rows:
        st.caption("No recorded views for this content in the selected period.")
        return
    top = rows[:5] if compact else rows[:7]
    tooltips = ["Content:N", alt.Tooltip("Views:Q", format=","),
                alt.Tooltip("Sessions:Q", format=",")]
    if any(r.get("Title") for r in top):
        tooltips.insert(1, "Title:N")
    chart = (
        alt.Chart(alt.Data(values=top))
        .mark_bar(cornerRadiusEnd=5, size=20 if compact else 22)
        .encode(
            x=alt.X("Views:Q", title="Recorded views",
                    axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Content:N", sort=[r["Content"] for r in top],
                    title=None, axis=alt.Axis(labelLimit=145 if compact else 250)),
            tooltip=tooltips,
        ).properties(height=220 if compact else max(180, 38 * len(top)))
    )
    st.altair_chart(chart, width="stretch")


@st.cache_data(ttl=300, show_spinner=False)
def _recent_content_report() -> dict:
    """Lightweight recent comparison, rechecked within five minutes.

    Only existing anonymous content aggregates are read. Hiring data is never
    queried in the public page. Behaviour RPC isn't needed for the brief.
    """
    payload = _dashboard_payload("7d")
    payload["p_article_metadata"] = _article_metadata()
    return _fetch_rpc("careersite_content_intelligence_v2", payload)


def render_public_portfolio_overview() -> None:
    """Visits and article reading are the first public evidence, never hiring."""
    st.title("Portfolio visits & reads")
    st.caption(
        "What visitors explore across the portfolio and which articles receive "
        "attention. Site sessions are deduplicated browser sessions, not unique "
        "people; repeat content views count."
    )
    initialize_reporting_period(st.session_state, _fetch_dashboard)
    window = st.selectbox(
        "Reporting period",
        [name for name, _ in REPORTING_WINDOWS],
        format_func=lambda key: REPORTING_WINDOW_LABELS[key],
        key="careersite_analytics_reporting_window",
        on_change=remember_reporting_period,
        args=(st.session_state,),
        help="Defaults to the first period with visits, from Last hour through All. "
             "Calendar periods use Stockholm time; weeks start Monday. "
             "Last Week and Last Month are completed periods. You can select any period manually.",
    )
    # Keep the manual refresh immediately beside the reporting controls,
    # before any potentially expensive report or visual is rendered.
    if st.button("Refresh insights", key="portfolio_refresh_insights"):
        _lifetime_content_report.clear()
        _recent_content_report.clear()
        st.rerun()

    try:
        report = fetch_intelligence(str(window))
    except (RuntimeError, ValueError, TimeoutError) as exc:
        st.warning("Portfolio reporting is temporarily unavailable.")
        st.caption(str(exc))
        return

    pages = portfolio_visit_rows(report, "page")
    historical_routes = [row for row in pages if row["Slug"] in RETIRED_ROUTES]
    current_routes = [row for row in pages if row["Slug"] not in RETIRED_ROUTES]
    articles = portfolio_visit_rows(report, "article")
    quality = report.get("quality") or {}
    page_views = max(0, int(quality.get("page_views") or 0))
    article_views = max(0, int(quality.get("article_views") or 0))
    legacy_views = max(0, int(quality.get("legacy_thinking_views") or 0))
    # One anonymous session is counted once across ordinary pages and editorial
    # readers, including direct entry to an article/briefing.
    site_sessions = (max(0, int(quality["site_sessions"]))
                     if quality.get("site_sessions") is not None else None)
    site_views = (max(0, int(quality["site_views"]))
                  if quality.get("site_views") is not None else None)
    # The content RPC reports WEEKLY AI as ordinary article-view rows.
    # Use published format metadata to make mutually exclusive visual groups.
    catalogue_available = True
    try:
        published_editions = list(fetch_published_articles())
    except RuntimeError:
        published_editions = []
        catalogue_available = False
    regular_articles, weekly_editions, briefing_rows = split_editorial_rows(
        articles, published_editions)
    regular_views = sum(row["Views"] for row in regular_articles)
    regular_item_sessions = sum(row["Sessions"] for row in regular_articles)
    weekly_views = sum(row["Views"] for row in weekly_editions)
    weekly_item_sessions = sum(row["Sessions"] for row in weekly_editions)
    briefing_views = sum(row["Views"] for row in briefing_rows)
    briefing_item_sessions = sum(row["Sessions"] for row in briefing_rows)
    published_briefing_count = (
        len(published_briefings(published_editions)) if catalogue_available else None
    )
    rows_reconcile = regular_views + weekly_views + briefing_views == article_views
    lifetime_views = lifetime_articles = lifetime_weekly = lifetime_briefings = None
    try:
        lifetime_report = report if str(window) == "all" else _lifetime_content_report()
        lifetime_quality = lifetime_report.get("quality") or {}
        if lifetime_quality.get("site_views") is not None:
            lifetime_views = max(0, int(lifetime_quality["site_views"]))
        if catalogue_available and "performance" in lifetime_report:
            lifetime_essays, lifetime_editions, lifetime_briefing_rows = split_editorial_rows(
                portfolio_visit_rows(lifetime_report, "article"), published_editions)
            lifetime_articles = sum(row["Views"] for row in lifetime_essays)
            lifetime_weekly = sum(row["Views"] for row in lifetime_editions)
            lifetime_briefings = sum(row["Views"] for row in lifetime_briefing_rows)
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        pass  # Keep selected-period reports usable when lifetime loading fails.

    with st.expander("Reporting context · October navigation change", expanded=False):
        st.caption(
            "The portfolio changed to six public destinations on 23 October 2026. "
            "Windows spanning that date contain two navigation structures. "
            "Compare complete days within each structure, not raw historical page rankings."
        )
        if historical_routes:
            st.markdown("**Earlier portfolio destinations**")
            st.caption(
                "Retired destination observations are preserved as their own historical "
                "cohorts. Views are not reassigned to About or Experience."
            )
            _ranking_chart(historical_routes, compact=True)
    # All four headlines use canonical views, so selected-period values
    # can be compared with the corresponding lifetime view totals.
    # Site-wide sessions remain a separate supporting reach metric.
    cards = [
        {
            "title": "Portfolio visits",
            "category": "Reach",
            "measure": "Site-wide views",
            "views": site_views,
            "lifetime": lifetime_views,
            "lifetime_unit": "views",
            "sessions": site_sessions,
            "sessions_label": "site-wide browser sessions",
            "items": len(current_routes),
            "item_unit": "active destinations",
            "rank_title": "Top portfolio pages",
            "rows": current_routes,
        },
        {
            "title": "Articles",
            "category": "Thinking",
            "measure": "Article views",
            "views": regular_views,
            "lifetime": lifetime_articles,
            "sessions": regular_item_sessions,
            "sessions_label": "article-item sessions",
            "items": len(regular_articles),
            "item_unit": "articles viewed",
            "rank_title": "Most-viewed articles",
            "rows": regular_articles,
            "available": catalogue_available,
        },
        {
            "title": "Weekly AI",
            "category": "Editorial",
            "measure": "Edition views",
            "views": weekly_views,
            "lifetime": lifetime_weekly,
            "sessions": weekly_item_sessions,
            "sessions_label": "edition-item sessions",
            "items": len(weekly_editions),
            "item_unit": "editions viewed",
            "rank_title": "Most-viewed editions",
            "rows": weekly_editions,
            "available": catalogue_available,
        },
        {
            "title": "Executive Briefings",
            "category": "Executive",
            "measure": "Briefing views",
            "views": briefing_views,
            "lifetime": lifetime_briefings,
            "sessions": briefing_item_sessions,
            "sessions_label": "briefing-item sessions",
            "items": len(briefing_rows),
            "total_items": published_briefing_count,
            "item_unit": "published briefings viewed",
            "rank_title": "Most-viewed briefings",
            "rows": briefing_rows,
            "available": catalogue_available,
        },
    ]
    for card in cards:
        card["period_label"] = REPORTING_WINDOW_LABELS.get(str(window), "Selected period")
    st.html(portfolio_metric_grid(cards))

    # Advanced Insights tabs are visible by default. Individual tabs render
    # only their active report and reuse cached anonymous aggregate reads.
    from page_public_legacy_insights import render_public_legacy_insights
    render_public_legacy_insights(str(window))
    st.divider()

    if site_views is not None:
        # The canonical view stream counts editorial entry once using article_view,
        # never again as the parallel article-page page_view event.
        segments = (f"{page_views:,} ordinary page views + "
                    f"{article_views:,} editorial views")
        if legacy_views:
            segments += f" + {legacy_views:,} historical Thinking views"
        if site_views != page_views + article_views + legacy_views:
            st.warning("Site content views do not reconcile with their page/article "
                       "subtotals; please inspect tracking coverage.")
        st.caption(
            f"Site-wide reach: {site_sessions:,} browser sessions generated "
            f"{site_views:,} content views ({segments}). "
            "A session can open multiple pages or publications."
            if site_sessions is not None else
            f"Content views: {site_views:,} ({segments}). "
            "Site-session reporting is temporarily unavailable."
        )
    if catalogue_available and not rows_reconcile:
        st.caption(
            "The per-content view breakdown does not reconcile with the overall "
            "article-view total for this window; investigate reporting coverage "
            "before comparing the three reading categories."
        )
    st.caption(
        "All four card headlines are view counts compared with lifetime views "
        "of the same content category. The first card counts canonical site-wide "
        "views without duplicate article-page events; its supporting metric "
        "counts distinct browser sessions. Its ranking covers ordinary portfolio "
        "pages only. Articles, Weekly AI and Executive Briefings partition "
        "editorial views already included in site-wide views. The Briefings "
        "library is an ordinary page. Item-session observations can overlap "
        "across publications and do not identify individual people."
    )

    recent_report = None
    if str(window) in ("14d", "30d", "60d", "90d", "365d", "this_month", "this_year", "all"):
        try:
            recent_report = _recent_content_report()
        except (RuntimeError, ValueError, TimeoutError, PermissionError):
            # A failed background comparator does not make the selected-period
            # visits/read charts unavailable, nor imply missing activity.
            recent_report = None

    latest_articles = (portfolio_visit_rows(recent_report, "article")
                       if recent_report else None)
    latest_pages = (portfolio_visit_rows(recent_report, "page")
                    if recent_report else None)
    top_insights, deeper_insights, limitations = ranked_portfolio_signals(
        report, pages, articles, window=str(window),
        recent_report=recent_report, recent_articles=latest_articles,
        recent_pages=latest_pages,
    )
    st.subheader("What changed and why it matters")
    st.caption(
        "Highest-signal evidence first. Recent seven-day movements inform the "
        "interpretation of broad historical reporting windows."
        if recent_report else
        "Selected-period findings, ranked by evidence and relevance."
    )
    summaries = st.columns(len(top_insights), gap="large")
    for column, insight in zip(summaries, top_insights):
        with column:
            st.markdown(f"**{insight.title}**")
            st.write(insight.message)
            st.markdown(f"*Next to examine:* {insight.next_check}")
            st.caption(insight.evidence)

    st.divider()
    render_home_journey(str(window))

    st.divider()
    st.subheader("Other relevant portfolio signals")
    st.caption(
        "Further evidence appears only when its sample and relevance justify "
        "a finding. Lower-confidence notes are kept in the evidence drilldown."
    )
    if deeper_insights:
        details = st.columns(min(2, len(deeper_insights)), gap="large")
        for index, insight in enumerate(deeper_insights):
            with details[index % len(details)]:
                st.markdown(f"**{insight.title}**")
                st.write(insight.message)
                st.markdown(f"*Next to examine:* {insight.next_check}")
                st.caption(insight.evidence)
    else:
        st.caption("No further high-confidence changes in this period.")

    with st.expander("Evidence, measurement limits and comparison rules", expanded=False):
        st.caption(
            "Signals use classified views, article-session observations and "
            "source/campaign cohorts. These are not unique people or evidence "
            "of particular readers' intentions."
        )
        for limitation in limitations:
            st.write(limitation)
        if not limitations:
            st.write("No additional evidence limitations were flagged for these signals.")
        if recent_report:
            st.caption(
                "Recent comparison refreshes within five minutes. Use Refresh insights "
                "to request a fresh report."
            )

    st.caption(
        "Page and article sessions are measured independently and must not be "
        "summed as unique visitors. These are content observations, not evidence "
        "that any particular employer or recruiter visited."
    )
    st.caption(
        "For individual Executive Briefings, reading depth, source attribution, "
        "WEEKLY AI audio and measurement diagnostics, open Explore content."
    )
