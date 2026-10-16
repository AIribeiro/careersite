"""Reactive, evidence-weighted signals for the PUBLIC portfolio dashboard.

Selected-period charts remain authoritative. A recent seven-day aggregate can
supply comparative context for broad historical views; all calls remain to
public content reports. Signals are ranked, not always displayed in a fixed
order, and weak measurement is treated as uncertainty, never failed reading.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    key: str
    title: str
    message: str
    next_check: str
    evidence: str
    score: int


def _n(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _pct(numerator: int, denominator: int) -> int:
    return round(100 * numerator / denominator) if denominator > 0 else 0


def _movement(current: int, before: int) -> str:
    direction = "up" if current >= before else "down"
    return f"{direction} {_pct(abs(current - before), before)}%"


def _period_totals(report: dict, kind: str) -> tuple[int, int]:
    now = before = 0
    for row in report.get("period_comparison", []):
        if not isinstance(row, dict) or row.get("kind") != kind:
            continue
        now += _n(row.get("current_views"))
        before += _n(row.get("previous_views"))
    return now, before


def _item_rows(report: dict, kind: str) -> list[dict]:
    return [r for r in report.get("performance", [])
            if isinstance(r, dict) and r.get("kind") == kind
            and _n(r.get("views")) > 0]


def _article_coverage(report: dict) -> tuple[int, int]:
    sessions = measured = 0
    for row in _item_rows(report, "article"):
        count = _n(row.get("sessions"))
        sessions += count
        measured += min(count, _n(row.get("depth_measured_sessions")))
    return measured, sessions


def _article_followons(report: dict) -> int:
    return sum(min(_n(r.get("later_portfolio_sessions")), _n(r.get("sessions")))
               for r in _item_rows(report, "article"))


def _descriptive_titles(rows: list[dict]) -> dict[str, str]:
    """Caller supplies original slugs AND display titles (no raw HTML)."""
    return {str(r.get("Slug", "")): str(r.get("Content", ""))
            for r in rows if str(r.get("Slug", ""))}


def ranked_portfolio_signals(
    report: dict,
    pages: list[dict],
    articles: list[dict],
    *,
    window: str,
    recent_report: dict | None = None,
    recent_articles: list[dict] | None = None,
    recent_pages: list[dict] | None = None,
) -> tuple[list[Signal], list[Signal], list[str]]:
    """Priority-first and contextual, not a fixed paragraph per KPI.

    Returns main signals (<=2), complementary signals (<=3) and concise
    diagnostics. No ranking based on tiny denominator changes.
    """
    recent = recent_report if isinstance(recent_report, dict) else None
    focus = recent or report
    cadence = "past 7 days" if recent else "selected reporting period"
    candidates: list[Signal] = []
    diagnostics: list[str] = []
    add = candidates.append

    p_now, p_before = _period_totals(focus, "page")
    a_now, a_before = _period_totals(focus, "article")
    comparable_pages = min(p_now, p_before) >= 20
    comparable_articles = min(a_now, a_before) >= 20

    if comparable_pages and comparable_articles:
        p_delta = (p_now - p_before) / p_before
        a_delta = (a_now - a_before) / a_before
        if p_delta * a_delta < 0 and min(abs(p_delta), abs(a_delta)) >= 0.15:
            leader = "rose" if p_delta > 0 else "fell"
            other = "fell" if a_delta < 0 else "rose"
            add(Signal(
                "split_movement", "Portfolio visits and reading are moving apart",
                f"Over the {cadence}, page views {leader} "
                f"{_pct(abs(p_now-p_before), p_before)}%, while article views "
                f"{other} {_pct(abs(a_now-a_before), a_before)}%. "
                "Reach and reading are not developing at the same pace.",
                "Inspect article discovery links and incoming channels before "
                "attributing the difference to reader preference.",
                f"Pages: {p_now:,} vs {p_before:,}; articles: "
                f"{a_now:,} vs {a_before:,}; equal-length periods.",
                100,
            ))
    for kind, now, before, comparable in (
        ("Portfolio page", p_now, p_before, comparable_pages),
        ("Article", a_now, a_before, comparable_articles),
    ):
        if comparable and abs(now-before) / before >= 0.2:
            # A divergence already captures the same fact more usefully.
            if any(s.key == "split_movement" for s in candidates):
                continue
            add(Signal(
                f"{kind.lower().replace(' ','_')}_movement",
                f"{kind} views {_movement(now, before)}",
                f"Recorded {kind.lower()} views moved {_movement(now, before)} "
                f"in the {cadence} against its immediately preceding "
                "equal-duration window.",
                "Review what changed in content publication and distribution; "
                "the view-count shift alone does not explain its cause.",
                f"{now:,} recent views vs {before:,} previous views.",
                88 if kind == "Article" else 84,
            ))

    focus_articles = recent_articles if recent else articles
    if focus_articles is None:
        focus_articles = []
    meaningful_reads = sum(_n(r.get("Views")) for r in focus_articles)
    if meaningful_reads >= 20 and focus_articles:
        leader = max(focus_articles, key=lambda r: _n(r.get("Views")))
        leading_count = _n(leader.get("Views"))
        leading_share = leading_count / meaningful_reads
        slug = str(leader.get("Slug", ""))
        prior = next((
            _n(row.get("previous_views"))
            for row in focus.get("period_comparison", [])
            if isinstance(row, dict) and row.get("kind") == "article"
            and str(row.get("content", "")) == slug
        ), None)
        if leading_count >= 12 and leading_share >= 0.35:
            name = str(leader.get("Content") or "Leading article")
            wording = ("It had no recorded views in the preceding equal "
                       "period; treat this as newly observed interest, not "
                       "a validated growth rate."
                       if prior == 0 else
                       "It is attracting a large fraction of current reading "
                       "attention, regardless of lifetime popularity.")
            add(Signal(
                "current_reading_leader", f"Recent reading is concentrated in {name}",
                f"{name} received {_pct(leading_count, meaningful_reads)}% "
                f"of classified article views in the {cadence}. {wording}",
                "Compare the article's format and distribution with other "
                "current publications before repeating the approach.",
                f"{leading_count:,} of {meaningful_reads:,} article views"
                + (f"; preceding window {prior:,}." if prior is not None else "."),
                91 if prior == 0 else 77,
            ))

    # Track specific destination changes rather than restating the homepage's
    # historical dominance. A one-count historical baseline is directional
    # only, never described as an extreme percentage gain.
    focus_pages = recent_pages if recent else pages
    previous_by_slug = {
        str(row.get("content", "")): _n(row.get("previous_views"))
        for row in focus.get("period_comparison", [])
        if isinstance(row, dict) and row.get("kind") == "page"
    }
    for row in sorted(focus_pages or [], key=lambda r: -_n(r.get("Views"))):
        slug = str(row.get("Slug", "")).strip().lower()
        if slug in ("home", "", "root"):
            continue
        now = _n(row.get("Views"))
        prior = previous_by_slug.get(slug)
        if now >= 12 and prior is not None and now >= 2 * max(1, prior):
            add(Signal(
                "emerging_page", f"{row['Content']} gained visibility",
                f"The {row['Content']} page recorded {now:,} views in the "
                f"{cadence}, compared with {prior:,} in the prior window. "
                "This suggests a shift toward that page, not necessarily "
                "new individual readers.",
                "Inspect the inbound links or campaigns associated with "
                "this page to explain the change.",
                f"{now:,} vs {prior:,} classified page views; small "
                "baselines are treated as directional only.",
                69 if prior >= 5 else 59,
            ))
            break

    # Prefer verified sustained active time over a popular headline when
    # evidence counts are sufficient. Session observations are per article.
    observed = _item_rows(report, "article")
    all_sessions = sum(_n(r.get("sessions")) for r in observed)
    all_engaged = sum(min(_n(r.get("engaged_sessions")), _n(r.get("sessions")))
                      for r in observed)
    if all_sessions >= 30:
        benchmark = all_engaged / all_sessions
        eligible = [
            r for r in observed
            if _n(r.get("sessions")) >= 12
            and _n(r.get("engaged_sessions")) >= 8
            and _n(r.get("engaged_sessions")) / _n(r.get("sessions")) >= max(.60, benchmark + .17)
        ]
        if eligible:
            strongest = max(eligible,
                            key=lambda r: _n(r.get("engaged_sessions")) /
                            _n(r.get("sessions")))
            slug = str(strongest.get("content") or "")
            title = _descriptive_titles(articles).get(slug, slug.replace("-", " ").title())
            engaged, sessions = _n(strongest["engaged_sessions"]), _n(strongest["sessions"])
            add(Signal(
                "engagement_outlier", f"{title} holds attention beyond its reach",
                f"{_pct(engaged, sessions)}% of its article-session "
                "observations met the measured engagement threshold, "
                f"compared with {_pct(all_engaged, all_sessions)}% across "
                "the classified article set.",
                "Compare this article's topic and structure with higher-reach "
                "titles; engagement does not by itself establish comprehension.",
                f"{engaged:,} of {sessions:,} article sessions reached the "
                "engagement threshold (≥10 seconds).",
                81 if sessions >= 20 else 72,
            ))

    # Attribution is needed to judge what drives discovery. Keep untagged
    # sessions visible, rather than claiming any particular channel's effect.
    campaign_rows = [r for r in focus.get("campaigns", []) if isinstance(r, dict)]
    total_attributed = sum(_n(r.get("sessions")) for r in campaign_rows)
    unknown = sum(_n(r.get("sessions")) for r in campaign_rows
                  if str(r.get("channel") or "").casefold().strip()
                  in ("direct/unknown", "direct / unknown", "unknown", "unattributed"))
    if total_attributed >= 30 and unknown / total_attributed >= 0.50:
        add(Signal(
            "attribution_gap", "Most entry sources remain unclassified",
            f"{_pct(unknown, total_attributed)}% of recorded "
            f"source/campaign session observations in the {cadence} "
            "are marked direct or unknown. Named channels alone therefore "
            "give an incomplete picture of how readers arrive.",
            "Standardize source and campaign tags on shared links, then "
            "reassess channel quality over the next reporting window.",
            f"{unknown:,} unknown of {total_attributed:,} classified "
            "source/campaign session observations.",
            76 if unknown / total_attributed >= .7 else 66,
        ))

    measured, sessions = _article_coverage(report)
    recent_measured, recent_sessions = _article_coverage(focus)
    if sessions >= 30 and measured / sessions < .60:
        if recent and recent_sessions >= 20 and recent_measured / recent_sessions >= .80:
            add(Signal(
                "coverage_improving", "Recent reading is better measured than the historical total",
                f"Reading-depth measurement covers {_pct(recent_measured, recent_sessions)}% "
                f"of article-item sessions in the {cadence}, versus "
                f"{_pct(measured, sessions)}% in the selected reporting period. "
                "Recent reading assessments have better instrument coverage.",
                "Use recent measured cohorts for depth comparisons and avoid "
                "judging historical unmeasured visits as shallow reads.",
                f"Recent: {recent_measured:,}/{recent_sessions:,}; "
                f"selected period: {measured:,}/{sessions:,}.",
                73,
            ))
        else:
            diagnostics.append(
                f"Reading-depth tracking covers {_pct(measured, sessions)}% of "
                f"the selected period ({measured:,}/{sessions:,} article-item "
                "sessions). Missing depth is unmeasured, not low engagement."
            )

    if articles:
        followon = _article_followons(report)
        article_item_sessions = sum(_n(r.get("sessions")) for r in _item_rows(report, "article"))
        if followon >= 10 and article_item_sessions and followon / article_item_sessions >= .05:
            add(Signal(
                "article_continuation", "Articles are leading to more portfolio exploration",
                f"{followon:,} article-level follow-on observations were "
                "recorded during the selected period. The pattern is "
                "consistent with continued browsing, not identified people.",
                "Examine which article links precede deeper page exploration.",
                "Follow-on counts can overlap across multiple articles; "
                "they are not unique conversions.",
                58,
            ))

    if p_before < 20 or a_before < 20:
        diagnostics.append(
            f"The {cadence} has an insufficient baseline for at least one "
            "traffic category. Percentage changes require at least 20 views "
            "in both comparable periods."
        )
    if recent and window != "7d":
        diagnostics.append(
            f"Charts and totals reflect the selected {window} reporting window; "
            "recent-movement signals use a separate seven-day vs preceding "
            "seven-day comparison."
        )

    # De-duplicate overlapping signals; high-value recent developments first,
    # breadth and measurement context next. The prioritization is deliberately
    # stable for identical input data and does not generate invented insights.
    scored = sorted(candidates, key=lambda s: (-s.score, s.key))
    top = scored[:2]
    details = scored[2:5]
    if not top:
        top = [Signal(
            "limited_activity", "Not enough evidence for a directional assessment",
            "Recent observations do not yet support a stable comparison of "
            "portfolio reach, article reading or engagement.",
            "Use a longer reporting window or return once sufficient "
            "content has been measured.",
            "Signal thresholds are minimum observations, not estimates "
            "of individual visitor interest.",
            0,
        )]
    if not details and any(s.key == "split_movement" for s in top):
        details = [Signal(
            "interpretation_boundary", "What this does not establish",
            "The divergence describes measured page and article activity. "
            "It cannot identify readers or explain changes in intent.",
            "Compare article entrances and channel attribution in Explore content.",
            "Session and article-item observations are not unique people.",
            0,
        )]
    return top, details, diagnostics
