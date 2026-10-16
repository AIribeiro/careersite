"""Evidence-calibrated, deterministic interpretations of public portfolio activity.

Every finding comes from the same aggregate report and reporting period as the
charts. No visitor identity, employer, hiring outcome or causality is inferred.
This pure module intentionally makes no network requests or Streamlit calls.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioInsight:
    heading: str
    interpretation: str
    basis: str


def _count(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _percent(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.0f}%" if denominator > 0 else "—"


def _classified_views(rows: list[dict]) -> int:
    return sum(_count(row.get("Views")) for row in rows)


def _article_measurement(report: dict) -> tuple[int, int, int]:
    """Article-item session observations, not distinct site-wide visitors."""
    sessions = measured = deep_reads = 0
    for row in report.get("performance", []):
        if not isinstance(row, dict) or row.get("kind") != "article":
            continue
        observed = _count(row.get("sessions"))
        covered = min(_count(row.get("depth_measured_sessions")), observed)
        sessions += observed
        measured += covered
        deep_reads += min(_count(row.get("deep_read_sessions")), covered)
    return sessions, measured, deep_reads


def _period_views(report: dict, kind: str) -> tuple[int, int]:
    current = previous = 0
    for row in report.get("period_comparison", []):
        if not isinstance(row, dict) or row.get("kind") != kind:
            continue
        current += _count(row.get("current_views"))
        previous += _count(row.get("previous_views"))
    return current, previous


def derive_portfolio_insights(
    report: dict,
    pages: list[dict],
    articles: list[dict],
) -> tuple[list[PortfolioInsight], list[PortfolioInsight]]:
    """Return top/bottom insight groups with explicit denominators and caveats.

    Page/article view totals may differ from the full quality totals when older
    events cannot be attributed to individual content items. The narrative uses
    classified item views for shares and says so.
    """
    top: list[PortfolioInsight] = []
    bottom: list[PortfolioInsight] = []
    page_views = _classified_views(pages)
    article_views = _classified_views(articles)

    if page_views >= 10 and pages:
        leader = pages[0]
        top.append(PortfolioInsight(
            "Where portfolio attention concentrates",
            f"{leader['Content']} leads page exploration, accounting for "
            f"{_percent(_count(leader['Views']), page_views)} of classified "
            f"page views. This is where recorded visits concentrate, not proof "
            f"that readers stopped on that page.",
            f"{_count(leader['Views']):,} of {page_views:,} classified page views "
            f"across {len(pages)} visited pages.",
        ))
    elif page_views:
        top.append(PortfolioInsight(
            "Early portfolio activity",
            "Page visits are recorded, but this period is too small for a "
            "stable comparison between destinations.",
            f"{page_views:,} classified page views.",
        ))
    else:
        top.append(PortfolioInsight(
            "Page interest not yet measurable",
            "No classified page visits are available for this reporting period. "
            "A lack of events is not evidence of a lack of interest.",
            "The selected report contains no page-attributed views.",
        ))

    if article_views >= 20 and len(articles) >= 3:
        leading_three = sum(_count(row["Views"]) for row in articles[:3])
        top.append(PortfolioInsight(
            "How reading interest is distributed",
            f"The three most-read articles represent "
            f"{_percent(leading_three, article_views)} of classified article "
            f"views. Interest spans {len(articles)} articles, but a smaller "
            f"group currently draws most of the reading activity."
            if leading_three * 2 >= article_views else
            f"The three most-read articles represent "
            f"{_percent(leading_three, article_views)} of classified article "
            f"views. Reading is spread beyond the leading titles, across "
            f"{len(articles)} articles.",
            f"{leading_three:,} of {article_views:,} classified article views "
            f"across {len(articles)} read articles.",
        ))
    elif article_views:
        top.append(PortfolioInsight(
            "Article readership is emerging",
            f"Articles have received {article_views:,} classified views, "
            "but the sample is not yet broad enough for a reliable reading "
            "concentration assessment.",
            f"{len(articles)} articles with recorded views in this period.",
        ))
    else:
        top.append(PortfolioInsight(
            "No classified article reads",
            "No article-attributed views are recorded in this period. "
            "This does not establish that articles were unseen.",
            "Article-specific tracking and publication dates affect coverage.",
        ))

    home_views = sum(_count(row["Views"]) for row in pages
                     if str(row.get("Content", "")).strip().casefold() == "home")
    if page_views >= 10 and home_views:
        beyond_home = max(0, page_views - home_views)
        bottom.append(PortfolioInsight(
            "Exploration beyond the landing page",
            f"{_percent(beyond_home, page_views)} of classified page views "
            f"occurred on pages other than Home. This indicates activity "
            "on deeper portfolio pages, but does not establish that people "
            "navigated from Home to those pages in the same session.",
            f"{beyond_home:,} non-Home page views of {page_views:,} "
            "classified page views.",
        ))
    elif page_views:
        bottom.append(PortfolioInsight(
            "Portfolio exploration breadth",
            f"{len(pages)} portfolio pages received recorded visits in "
            "this period. The next useful question is whether attention "
            "persists across multiple content sections.",
            "Page-view breadth is not a unique-visitor or journey count.",
        ))

    item_sessions, measured, deep = _article_measurement(report)
    if item_sessions and measured >= 10:
        covered = _percent(measured, item_sessions)
        if measured * 2 >= item_sessions:
            interpretation = (
                f"Reading-depth instrumentation covered {covered} of "
                f"article-item session observations. {deep} of the {measured} "
                "measured observations met the strict deep-read proxy "
                "(at least 30 seconds of activity and 90% page depth). "
                "The proxy is not proof of comprehension."
            )
        else:
            interpretation = (
                f"Reading-depth instrumentation covered only {covered} of "
                f"article-item session observations. There were {deep} "
                "observed deep-read cases among the measured subset. "
                "The remaining observations cannot be classified as "
                "uninterested readers or unfinished reads."
            )
        bottom.append(PortfolioInsight(
            "Reading depth and measurement confidence",
            interpretation,
            f"{measured:,} depth-measured of {item_sessions:,} article-item "
            "session observations; a strict reading proxy, not a visitor count.",
        ))
    elif item_sessions:
        bottom.append(PortfolioInsight(
            "Reading depth remains uncertain",
            "Article views are recorded, but reading-depth coverage is "
            "too limited to draw a defensible conclusion about sustained "
            "attention. Unmeasured reads are not failed reads.",
            f"{measured:,} depth-measured of {item_sessions:,} article-item "
            "session observations.",
        ))

    follow_ups = []
    for row in report.get("performance", []):
        if not isinstance(row, dict) or row.get("kind") != "article":
            continue
        count = min(_count(row.get("later_portfolio_sessions")),
                    _count(row.get("sessions")))
        if count:
            follow_ups.append((count, str(row.get("content") or "")))
    if follow_ups:
        total = sum(count for count, _ in follow_ups)
        bottom.append(PortfolioInsight(
            "Continued exploration after reading",
            f"At least one article was followed by further portfolio "
            f"exploration in the same measured journey. {total:,} "
            "article-level follow-on observations were recorded. This is "
            "an on-site behavior signal, not a recruiter identification "
            "or evidence that the article caused the subsequent action.",
            f"Follow-on activity appeared on {len(follow_ups)} distinct "
            "articles; observations can overlap across articles.",
        ))
    elif article_views:
        bottom.append(PortfolioInsight(
            "No verified reading-to-portfolio journey",
            "No article-to-portfolio continuation was recorded in the "
            "available session-level measurements. This should be "
            "treated as unobserved, not as proof that articles do not "
            "encourage further exploration.",
            "Attribution depends on the installed tracking and consent-free "
            "session measurement.",
        ))

    current_pages, previous_pages = _period_views(report, "page")
    current_articles, previous_articles = _period_views(report, "article")
    shifts = []
    for name, now, before in (
        ("page views", current_pages, previous_pages),
        ("article views", current_articles, previous_articles),
    ):
        # At least 20 observations in both windows prevents exaggerated
        # movement from low denominators or entirely unrecorded baselines.
        if now >= 20 and before >= 20:
            change = (now - before) / before
            if abs(change) < 0.05:
                shifts.append(f"{name} remained broadly stable ({now:,} vs "
                              f"{before:,})")
            else:
                direction = "rose" if change > 0 else "fell"
                shifts.append(f"{name} {direction} by "
                              f"{_percent(abs(now - before), before)} "
                              f"({now:,} vs {before:,})")
    if shifts:
        bottom.append(PortfolioInsight(
            "Movement against the preceding period",
            "; ".join(shifts).capitalize() +
            ". This is an observed change in recorded views, not a "
            "causal explanation or a forecast.",
            "Comparison uses equal-duration adjacent reporting windows "
            "and is shown only for categories with at least 20 "
            "observations in both windows.",
        ))
    else:
        bottom.append(PortfolioInsight(
            "Movement cannot yet be assessed",
            "There is not enough recorded activity in both the selected "
            "period and the preceding equal-length period to characterize "
            "a rise or decline reliably. A missing baseline is not "
            "interpreted as zero demand.",
            f"Previous-period classified views: {previous_pages:,} pages "
            f"and {previous_articles:,} articles; a minimum of 20 in "
            "each compared period is required.",
        ))

    topics = [row for row in report.get("topic_performance", [])
              if isinstance(row, dict) and _count(row.get("views")) > 0]
    total_topics = sum(_count(row.get("views")) for row in topics)
    if total_topics >= 20 and len(topics) >= 2:
        first = max(topics, key=lambda row: _count(row.get("views")))
        heading = str(first.get("topic") or "Uncategorized")
        bottom.append(PortfolioInsight(
            "Editorial topics attracting readership",
            f"{heading} currently has the largest share of article views "
            f"within classified editorial topics "
            f"({_percent(_count(first.get('views')), total_topics)}). "
            "This indicates observed topic reach, not that the subject "
            "is preferred by individual readers.",
            f"{_count(first.get('views')):,} of {total_topics:,} "
            f"topic-classified article views across {len(topics)} topics.",
        ))

    return top, bottom
