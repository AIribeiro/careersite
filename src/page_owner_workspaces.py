"""Owner-only, domain-separated portfolio, hiring and social workspaces.

No new tracking tables: use the existing first-party aggregates and private
owner reads. Cross-domain findings are labelled as associations, not attribution.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from analytics_reporting_period import initialize_reporting_period, remember_reporting_period
from page_analytics import (
    REPORTING_WINDOWS, REPORTING_WINDOW_LABELS, _fetch_dashboard,
    _fetch_hiring_intelligence,
)
from page_content_intelligence import (
    _campaign_visual_rows, _render_source_quality, fetch_intelligence,
)
from page_public_portfolio_overview import render_public_portfolio_overview
from page_linkedin_career_scorecard import render_linkedin_career_scorecard


_PORTFOLIO_VIEWS = {
    "overview": "Overview",
    "content": "Content & readers",
    "audience": "Audience & journeys",
    "quality": "Measurement quality",
    "contribution": "Hiring contribution",
}
_SOCIAL_VIEWS = {
    "overview": "Overview",
    "relationships": "LinkedIn relationships",
    "channels": "Channel performance",
    "distribution": "Distribution links",
}
_SOCIAL_WORDS = (
    "linkedin", "facebook", "instagram", "twitter", "threads", "whatsapp",
    "youtube", "reddit", "tiktok", "bluesky", "mastodon", "pinterest", "x.com",
)


def _hero(kicker: str, title: str, description: str) -> None:
    from html import escape
    st.markdown(
        """<style>
        .owner-hub-hero{padding:22px 27px 20px;margin:8px 0 18px;
          border-radius:17px;background:linear-gradient(118deg,#1a2630,#33424b);
          box-shadow:0 10px 25px rgba(24,37,49,.10);color:#fff}
        .owner-hub-hero .eyebrow{font-size:.71rem;font-weight:750;
          color:#d8b59a;text-transform:uppercase;letter-spacing:.14em}
        .owner-hub-hero h1{font-size:clamp(1.55rem,2.5vw,2.2rem);
          color:#fff!important;letter-spacing:-.035em;line-height:1.16;
          margin:5px 0 7px;font-weight:650}
        .owner-hub-hero p{font-size:.89rem;color:#e0e4e6;
          line-height:1.5;margin:0;max-width:900px}
        div[data-testid="stMetric"]{padding:9px 3px}
        </style>"""
        + '<div class="owner-hub-hero"><span class="eyebrow">'
        + escape(kicker) + '</span><h1>' + escape(title) + '</h1><p>'
        + escape(description) + '</p></div>',
        unsafe_allow_html=True,
    )


def _portfolio_url_changed() -> None:
    value = st.session_state.get("owner_portfolio_section", "overview")
    st.session_state["_owner_portfolio_route"] = value
    st.query_params["workspace"] = "public"
    st.query_params["view"] = value


def _social_url_changed() -> None:
    value = st.session_state.get("owner_social_section", "overview")
    st.session_state["_owner_social_route"] = value
    st.query_params["workspace"] = "linkedin"
    st.query_params["view"] = value


def _reporting_window() -> str:
    initialize_reporting_period(st.session_state, _fetch_dashboard)
    return str(st.selectbox(
        "Reporting period",
        [key for key, _ in REPORTING_WINDOWS],
        format_func=lambda key: REPORTING_WINDOW_LABELS[key],
        key="careersite_analytics_reporting_window",
        on_change=remember_reporting_period,
        args=(st.session_state,),
        help="Defaults to the shortest period with recorded visits. Counts are browser-session observations, not identified people.",
    ))


def _quality_cards() -> None:
    try:
        report = _fetch_hiring_intelligence("30d")
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        st.caption("Qualified portfolio behaviour could not be checked in this session.")
        return
    quality = report.get("quality_summary") or {}
    if not quality:
        st.caption("Qualified behavioural evidence is not available for this period.")
        return
    eligible = int(quality.get("analysis_eligible_sessions") or 0)
    verified = int(quality.get("evidence_verified_sessions") or 0)
    intent = int(quality.get("hiring_intent_sessions") or 0)
    engaged = int(quality.get("engaged_sessions") or 0)
    columns = st.columns(4, gap="small")
    for col, label, count, note in zip(
        columns,
        ("Qualified sessions", "Engaged", "Evidence verified", "On-site hiring intent"),
        (eligible, engaged, verified, intent),
        (
            "V5 eligible sessions",
            f"{engaged / eligible:.0%} of qualified" if eligible else "No eligible denominator",
            f"{verified / eligible:.0%} of qualified" if eligible else "No eligible denominator",
            "Actions, not recruiter identities",
        ),
    ):
        with col:
            with st.container(border=True):
                st.metric(label, f"{count:,}")
                st.caption(note)
    st.caption(
        "Last 30 days · quality-filtered browser sessions. On-site intent cannot "
        "prove who visited or whether an employer considered an application."
    )


def render_owner_portfolio(session: dict) -> None:
    """All portfolio-specific reporting, including previously private evidence."""
    _hero(
        "Portfolio intelligence", "Portfolio Analytics",
        "Content reach, qualified attention, reader journeys, measurement health and the evidence connecting the portfolio with hiring activity.",
    )
    requested = str(st.query_params.get("view", "overview")).lower().strip()
    mapped = {
        "pages": "content", "articles": "content", "portfolio": "content",
        "attribution": "quality", "overview": "overview",
    }.get(requested, requested)
    selected = mapped if mapped in _PORTFOLIO_VIEWS else "overview"
    if requested in ("pages", "articles"):
        st.session_state["analytics_portfolio_kind"] = (
            "article" if requested == "articles" else "page"
        )
    if (st.session_state.get("_owner_portfolio_route") != selected or
            "owner_portfolio_section" not in st.session_state):
        st.session_state["owner_portfolio_section"] = selected
        st.session_state["_owner_portfolio_route"] = selected
    section = st.segmented_control(
        "Portfolio report", options=list(_PORTFOLIO_VIEWS),
        format_func=lambda k: _PORTFOLIO_VIEWS[k],
        key="owner_portfolio_section", on_change=_portfolio_url_changed,
        width="stretch", label_visibility="collapsed",
    ) or selected

    if section == "overview":
        _quality_cards()
        render_public_portfolio_overview()
        return

    if section == "content":
        st.subheader("Reading and content performance")
        kind = st.segmented_control(
            "Content type", options=["page", "article", "weekly_ai"],
            format_func=lambda k: {
                "page": "Portfolio pages", "article": "Articles", "weekly_ai": "Weekly AI",
            }[k],
            key="analytics_portfolio_kind", default="page", width="stretch",
        ) or "page"
        window = _reporting_window()
        if kind == "weekly_ai":
            from page_weekly_ai_analytics import render_weekly_ai_analytics
            render_weekly_ai_analytics(window)
        else:
            from page_content_intelligence import render_content_intelligence
            render_content_intelligence(kind, window)
        return

    if section == "audience":
        st.caption("Detailed audience, devices, session depth, entry paths and visitor behaviour.")
        from page_analytics import render_analytics_dashboard as render_visitor_diagnostics
        render_visitor_diagnostics()
        return

    if section == "quality":
        st.subheader("Measurement confidence and evidence integrity")
        _quality_cards()
        from page_cv_attribution_audit import render_cv_attribution_audit
        from page_attribution_coverage import render_attribution_coverage
        window = _reporting_window()
        render_cv_attribution_audit(window)
        with st.expander("Source-tag completeness and unresolved origins", expanded=False):
            render_attribution_coverage()
        return

    st.subheader("Portfolio contribution to recruitment")
    _quality_cards()
    from page_portfolio_job_correlations import render_portfolio_job_correlations
    render_portfolio_job_correlations()
    st.caption(
        "Historical portfolio activity and job-search milestones may be compared, "
        "but this does not identify individual visitors or establish causation."
    )


def _social_rows(window: str) -> list[dict]:
    report = fetch_intelligence(window)
    rows = _campaign_visual_rows(report)
    return sorted(
        [r for r in rows if any(term in str(r["Source"]).lower() for term in _SOCIAL_WORDS)],
        key=lambda r: (-r["Sessions"], r["Source / campaign"]),
    )


def _social_insight(rows: list[dict]) -> None:
    substantial = [r for r in rows if r["Sessions"] >= 5]
    if substantial:
        leader = max(
            substantial,
            key=lambda r: (
                r.get("Engaged") if r.get("Engaged") is not None else -1,
                r["Engaged sessions"],
            ),
        )
        st.markdown(
            "**Channel to examine:** " + str(leader["Source / campaign"])
            + " recorded " + str(leader["Engaged sessions"]) + " engaged sessions "
            + "out of " + str(leader["Sessions"]) + " attributed sessions. "
            + "Check the associated campaign and subsequent contact actions before increasing distribution."
        )
    elif rows:
        st.info(
            "The tracked social cohorts are too small for reliable ranking "
            "(fewer than five sessions each). Use tracked links consistently and "
            "review engagement after more traffic is observed."
        )
    else:
        st.info(
            "No identifiable social-source sessions in this reporting period. "
            "Publish with tagged distribution links; do not label unknown visits as social traffic."
        )


def _social_overview(window: str) -> None:
    try:
        rows = _social_rows(window)
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        st.warning("Social attribution could not be refreshed from the portfolio ledger.")
        return
    totals = {
        field: sum(int(row[field] or 0) for row in rows)
        for field in ("Sessions", "Reader sessions", "Engaged sessions", "CV sessions", "Contact sessions")
    }
    cols = st.columns(4, gap="small")
    for col, label, key, detail in zip(
        cols,
        ("Social visits", "Article readers", "Engaged visits", "Contact actions"),
        ("Sessions", "Reader sessions", "Engaged sessions", "Contact sessions"),
        (
            "First-source cohorts",
            "Portfolio reading",
            "Measured engagement",
            "On-site actions only",
        ),
    ):
        with col:
            with st.container(border=True):
                st.metric(label, f"{totals[key]:,}")
                st.caption(detail)
    _social_insight(rows)
    if not rows:
        return
    by_source: dict[str, dict] = {}
    for item in rows:
        source = str(item["Source"])
        target = by_source.setdefault(
            source, {"Channel": source, "Sessions": 0, "Readers": 0, "Contacts": 0},
        )
        target["Sessions"] += int(item["Sessions"])
        target["Readers"] += int(item["Reader sessions"])
        target["Contacts"] += int(item["Contact sessions"])
    chart_rows = sorted(by_source.values(), key=lambda x: -x["Sessions"])
    st.subheader("Where attention originates")
    st.altair_chart(
        alt.Chart(alt.Data(values=chart_rows))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X("Sessions:Q", title="Attributed sessions", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Channel:N", sort="-x", title=None),
            tooltip=["Channel:N", "Sessions:Q", "Readers:Q", "Contacts:Q"],
        ).properties(height=max(180, 35 * len(chart_rows))),
        width="stretch",
    )
    st.caption(
        "Sources are first observed attribution tags/referrers. These are not "
        "LinkedIn profile impressions, identified recruiters, unique people or "
        "verified hiring conversions. Different cohorts are not deduplicated "
        "against off-site platform analytics."
    )


def render_owner_social(session: dict) -> None:
    """Consolidated first-party social attribution + LinkedIn relationship work."""
    _hero(
        "Distribution and professional network", "Social Media Presence",
        "See which channels produce readers and contact actions, prioritize real professional relationships, and generate traceable publishing links.",
    )
    selected = str(st.query_params.get("view", "overview")).lower().strip()
    if selected not in _SOCIAL_VIEWS:
        selected = "overview"
    if (st.session_state.get("_owner_social_route") != selected or
            "owner_social_section" not in st.session_state):
        st.session_state["owner_social_section"] = selected
        st.session_state["_owner_social_route"] = selected
    section = st.segmented_control(
        "Social reporting", options=list(_SOCIAL_VIEWS),
        format_func=lambda k: _SOCIAL_VIEWS[k], key="owner_social_section",
        on_change=_social_url_changed, label_visibility="collapsed", width="stretch",
    ) or selected

    if section == "relationships":
        render_linkedin_career_scorecard(embedded=True)
        return
    if section == "distribution":
        st.subheader("Tracked links for social and professional outreach")
        st.caption(
            "First-party links retain channel and campaign labels. "
            "Creating a link does not retroactively attribute prior traffic."
        )
        from site_cms import admin_list_articles
        from page_admin import _distribution_links
        try:
            articles = admin_list_articles(str(session["access_token"]))
        except (RuntimeError, ValueError, TimeoutError, PermissionError) as exc:
            st.warning("Published content list could not be loaded.")
            st.caption(str(exc))
            return
        _distribution_links(articles)
        return

    window = _reporting_window()
    _social_overview(window)
    if section == "channels":
        try:
            data = fetch_intelligence(window)
        except (RuntimeError, ValueError, TimeoutError, PermissionError):
            st.warning("Source-quality report is temporarily unavailable.")
            return
        st.divider()
        _render_source_quality(data)
        with st.expander("Channel attribution completeness", expanded=False):
            from page_attribution_coverage import render_attribution_coverage
            render_attribution_coverage()
    else:
        st.divider()
        st.markdown("**Next decision:** Compare tracked source quality with the professional relationship ledger, "
                    "then prioritize the relationships that have a verified next action.")
        if st.button("Review LinkedIn relationship actions", key="social_open_relationships"):
            st.session_state["owner_social_section"] = "relationships"
            _social_url_changed()
            st.rerun()


def _current_stage_groups(prediction: dict, plans: dict | None) -> tuple[list[dict], list[dict]]:
    """Show open/unresolved processes, excluding outcomes confirmed after a snapshot."""
    closed_outcomes = {"rejected", "withdrawn", "closed", "offer_accepted", "hired"}
    stale_states = {"employer_rejection", "stale_unknown", "closed_unreconciled"}
    progressed, applied = [], []
    for process in prediction.get("top_processes", []):
        if not isinstance(process, dict) or process.get("status") in stale_states:
            continue
        key = str(process.get("process_key") or "").strip().casefold()
        latest = (plans or {}).get(key) or {}
        if str(latest.get("outcome") or "").strip().casefold() in closed_outcomes:
            continue
        if process.get("stage") == "application_only":
            applied.append(process)
        else:
            progressed.append(process)
    return progressed, applied


def render_owner_stage_dashboard(session: dict) -> None:
    """Owner-only stage/MTO board: scheduled snapshot plus current meeting evidence."""
    from page_hiring_daily import read_daily_history
    from page_hiring_prediction_v2 import (
        STAGE_NAMES, validate_prediction_v2, _verified_meetings_by_process,
    )
    from hiring_opportunity_comparison import opportunity_comparison_html

    token = str(session.get("access_token") or "")
    st.subheader("Hiring stages & meetings to offer")
    st.caption(
        "Every open or unresolved process in the latest stage-model shortlist. "
        "Meeting totals are conditional estimates, not probabilities of receiving an offer."
    )
    if not token:
        st.warning("Sign in as the portfolio owner to see hiring stages and MTO.")
        return
    try:
        snapshots = read_daily_history(token, limit=1)
        if not snapshots:
            st.warning("No dated hiring-stage assessment is available. Earlier forecasts are not substituted.")
            return
        latest = snapshots[0]
        prediction = validate_prediction_v2(latest.get("scenario"))
    except (RuntimeError, ValueError, TimeoutError, PermissionError, KeyError) as exc:
        st.warning("The hiring-stage snapshot is unavailable; the board cannot verify process stages.")
        return

    counts = details = plans = None
    try:
        counts, details, plans = _verified_meetings_by_process(token, with_details=True)
    except (RuntimeError, TimeoutError, ValueError, PermissionError):
        st.warning(
            "Live meeting/outcome records are unavailable. The stage snapshot may include "
            "a process subsequently closed, and attended meeting counts cannot be verified."
        )

    progressed, applied = _current_stage_groups(prediction, plans)
    assessment_day = str(latest.get("forecast_day") or prediction.get("as_of") or "Unknown")
    today = datetime.now(ZoneInfo("Europe/Stockholm")).date().isoformat()
    st.caption(
        f"Stage assessment: {assessment_day} · Meeting attendance and employer outcomes: "
        + ("latest owner records" if plans is not None else "unavailable")
        + ". A scheduled interview is not a held meeting."
    )
    if assessment_day < today:
        st.warning(
            "The stage assessment predates today. Current outcomes are checked separately "
            "when the recruiting ledger is available."
        )

    if progressed:
        st.markdown(
            opportunity_comparison_html(progressed, STAGE_NAMES, counts, details, plans),
            unsafe_allow_html=True,
        )
    else:
        st.info("No open or unresolved recruiter-engaged process is documented in the latest shortlist.")
    if applied:
        with st.expander(f"Earlier-stage applications · {len(applied)}", expanded=False):
            st.caption(
                "Applications without a verified employer conversation. "
                "MTO is a role-based planning range until actual interviews are recorded."
            )
            st.markdown(
                opportunity_comparison_html(applied, STAGE_NAMES, counts, details, plans),
                unsafe_allow_html=True,
            )
    st.caption(
        "MTO = estimated total candidate meetings to a possible offer. "
        "Held = distinct attended meetings; Remaining = estimated further meetings. "
        "Interviewer decision authority and any employer-confirmed sequence take precedence "
        "over the role baseline. Hover over the MTO figures for the rationale and confidence."
    )


def render_owner_hiring_home(session: dict) -> None:
    """Private hiring-first landing. No portfolio analytics or audience charts."""
    from page_analytics_overview import _action_queue, _search_brief
    from page_job_search_analytics import fetch_job_records
    from job_search_trends import SERIES

    _hero(
        "Recruitment decision desk", "Hiring overview",
        "Active conversations, pending follow-ups, observed response rates and recorded recruitment stages. Forecasts and market evidence remain separate.",
    )
    try:
        jobs = fetch_job_records(str(session["access_token"]))
        search, trend = _search_brief(jobs, datetime.now(ZoneInfo("Europe/Stockholm")).date())
    except (RuntimeError, ValueError, TimeoutError, PermissionError, KeyError):
        st.warning("Private job-search events could not be loaded.")
        return
    # Keep the interview-stage / MTO decision board visible on the default
    # Job Hiring Analytics page, rather than burying it inside legacy forecasts.
    render_owner_stage_dashboard(session)
    st.divider()

    processes = search.get("processes") or []
    active = [p for p in processes if p.get("State") == "Active documented"]
    due = [p for p in processes if p.get("Overdue") or p.get("Follow-up due")]
    recent = trend.get("recent") or {}
    cols = st.columns(4, gap="small")
    for col, label, value, note in zip(
        cols,
        ("Active hiring processes", "Follow-ups to review", "Applications · 28d", "Two-way contacts · 28d"),
        (len(active), len(due), int(recent.get(SERIES[0], 0)), int(recent.get(SERIES[1], 0))),
        ("Recorded active state", "Evidence-based task queue", "Dated application events", "Documented exchanges"),
    ):
        with col:
            with st.container(border=True):
                st.metric(label, f"{value:,}")
                st.caption(note)
    queue = _action_queue(search)
    if queue:
        st.markdown("**Next actions — recorded hiring evidence**")
        st.dataframe(
            [{k: v for k, v in item.items() if not k.startswith("_")} for item in queue],
            hide_index=True, width="stretch",
        )
    else:
        st.caption("No overdue follow-up identified from the currently recorded hiring events.")
    st.divider()
    from page_public_analytics import render_public_job_search
    render_public_job_search(include_portfolio=False)
