"""Owner-only decision brief: concise, interpreted evidence across portfolio, search and market."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json

import streamlit as st

from job_search_metrics import analyze, canonical_events, day
from job_search_trends import analyze_trends, SERIES
from job_market_correlations import analyze_market
from portfolio_job_correlations import analyze_portfolio_job_correlations
from page_analytics import _fetch_hiring_intelligence
from page_content_intelligence import _fetch_rpc
from page_job_market_insights import fetch_market_records, _latest_by_indicator, _format_value, _readouts
from page_job_search_analytics import fetch_job_records
from page_hiring_predictor import render_hiring_predictor
from site_cms import ensure_owner_session


_REFRESH_INTERVAL = "5m"
_SOURCE_NAMES = {
    "jobs": "job search",
    "market": "Swedish market",
    "site": "portfolio activity",
    "hiring": "qualified portfolio behavior",
}


def _evidence_signature(value: object) -> str:
    """Stable fingerprint of source data, not a cross-session data cache."""
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _changes_since_last_check(
    previous: dict[str, str] | None, current: dict[str, str],
) -> list[str]:
    """Only report actual changed, successfully loaded sources."""
    if not previous:
        return []
    return [label for key, label in _SOURCE_NAMES.items()
            if key in previous and key in current
            and previous[key] != current[key]]


def _go(view: str) -> None:
    st.session_state["careersite_analytics_view"] = view
    st.query_params["view"] = view
    st.rerun()


def _plain_delta(a: int, b: int | None) -> str:
    if b is None:
        return "No comparable previous 28 days"
    change = a - b
    return f"{change:+d} vs prior 28d" if change else "Unchanged vs prior 28d"


def _search_brief(jobs: list[dict], today) -> tuple[dict, dict]:
    dated = [day(r.get("event_date")) for r in canonical_events(jobs)]
    dated = [d for d in dated if d and d <= today]
    start = min(dated) if dated else today
    return (analyze(jobs,start,today,False),
            analyze_trends(jobs,start,today))


def _action_queue(search: dict) -> list[dict]:
    cases = search.get("processes",[])
    queue = []
    for p in cases:
        if p.get("Overdue") or p.get("Follow-up due"):
            priority = "Follow-up needs review"
        elif p.get("Waiting"):
            priority = "Awaiting a recorded reply"
        else:
            continue
        queue.append({
            "Priority": priority,
            "Employer": p.get("Employer"),
            "Role": p.get("Role"),
            "Last event": p.get("Last event") or "Undated",
            "Days since event": p.get("Days since event"),
            "Next step": p.get("Next step") if p.get("Next step") != "Not recorded" else "Review recorded history",
            "_sort": 0 if p.get("Overdue") or p.get("Follow-up due") else 1,
        })
    return sorted(queue,key=lambda r:(r["_sort"],-(r["Days since event"] or 0)))[:5]


@st.fragment(run_every=_REFRESH_INTERVAL)
def render_analytics_overview(session: dict | None) -> None:
    st.title("Decision overview")
    st.caption("Your portfolio, job-search progress and Swedish hiring conditions in one view. "
               "Priorities first; drill-down evidence stays in its dedicated section.")
    valid = ensure_owner_session(session)
    if not valid or not valid.get("access_token"):
        st.warning("An owner session is required.")
        return
    st.session_state["cms_auth"] = valid
    now = datetime.now(ZoneInfo("Europe/Stockholm"))
    jobs = []
    market = []
    site = None
    hiring = {}
    errors = []
    with st.spinner("Comparing current evidence…"):
        try:
            jobs = fetch_job_records(str(valid["access_token"]))
        except (RuntimeError, TimeoutError, ValueError):
            errors.append("job search")
        try:
            market = fetch_market_records(str(valid["access_token"]))
        except (RuntimeError, TimeoutError, ValueError):
            errors.append("market")
        try:
            site = _fetch_rpc("careersite_portfolio_signals_daily_v1",{"p_days":365})
        except (RuntimeError, TimeoutError, PermissionError, ValueError):
            errors.append("portfolio correlation")
        hiring = _fetch_hiring_intelligence("30d")
    current_signatures = {}
    for key, payload in (("jobs", jobs), ("market", market),
                         ("site", site), ("hiring", hiring)):
        # Unavailable sources must not be mistaken for newly deleted data.
        if payload is not None and (key not in ("jobs", "market") or key not in errors):
            if key == "hiring" and not payload:
                continue
            current_signatures[key] = _evidence_signature(payload)
    previous_signatures = st.session_state.get("analytics_overview_source_signatures")
    changed = _changes_since_last_check(previous_signatures, current_signatures)
    st.session_state["analytics_overview_source_signatures"] = {
        **(previous_signatures or {}), **current_signatures,
    }
    st.caption(f"Last checked {now:%d %b %Y at %H:%M} Stockholm · "
               "automatically checks source changes every 5 minutes while Overview is open; "
               "recalculates immediately when the page is reopened. "
               "Data must first be recorded in Supabase.")
    if changed:
        st.caption("New data detected and forecast recalculated: " + ", ".join(changed) + ".")
    if errors:
        st.warning("Some sources were temporarily unavailable: " + ", ".join(errors)
                   + ". Other available sections remain usable.")

    search = trends = None
    if jobs:
        search, trends = _search_brief(jobs,now.date())

    # A single pass supplies the beta model and later drill-down summaries.
    # Cross-domain relationships are contextual unless independently validated.
    market_model = analyze_market(market,jobs,site,now.date()) if market else None
    site_corr = analyze_portfolio_job_correlations(site,jobs) if site and jobs else None
    if jobs:
        render_hiring_predictor(jobs,market_model,site_corr,hiring,now.date())
    else:
        st.subheader("Hiring predictor")
        st.info("Forecast unavailable until primary job-search evidence can be loaded.")
    st.divider()

    st.subheader("Where your search stands")
    if search:
        processes = search["processes"]
        due = [p for p in processes if p["Overdue"] or p["Follow-up due"]]
        waiting = [p for p in processes if p["Waiting"]]
        active = [p for p in processes if p["State"] == "Active documented"]
        previous = trends["previous"] if trends["baseline_available"] else None
        recent = trends["recent"]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Applications · last 28d",recent[SERIES[0]],_plain_delta(recent[SERIES[0]], previous[SERIES[0]] if previous else None),delta_color="off")
        c2.metric("Two-way contacts · last 28d",recent[SERIES[1]],_plain_delta(recent[SERIES[1]], previous[SERIES[1]] if previous else None),delta_color="off")
        c3.metric("Documented active processes",len(active),help="Based on the latest imported process states, not an employer's live ATS.")
        c4.metric("Follow-ups to review",len(due),help=f"{len(waiting)} processes additionally await an explicitly recorded response.")

        if not previous or trends["coverage"]["previous_dated"] < 5:
            st.caption("Period-on-period movement has limited coverage; treat changes as recorded activity, not proof of market improvement.")
        elif recent[SERIES[0]] > previous[SERIES[0]] and recent[SERIES[1]] <= previous[SERIES[1]]:
            st.info("Applications rose without a corresponding rise in recorded conversations. "
                    "Review mandate fit, employer access and response latency before increasing submission volume.")
        elif recent[SERIES[1]] > previous[SERIES[1]]:
            st.info("Recorded recruiter/hiring conversations increased. Prioritize active conversations and timely follow-up over volume alone.")
        else:
            st.caption("The observed application and response counts describe different process stages. "
                       "Use the mature application cohort for an actual conversion rate.")

        queue = _action_queue(search)
        if queue:
            st.markdown("**Decisions needing review**")
            st.dataframe([{k:v for k,v in row.items() if k != "_sort"} for row in queue],
                         hide_index=True,width="stretch")
        else:
            st.caption("No explicit overdue or pending-response process is documented in the imported evidence.")
        if st.button("Explore job-search funnel and next actions",key="overview_to_jobs"):
            _go("jobs")
    else:
        st.info("Job-search evidence is unavailable. The overview never substitutes market sentiment for personal outcomes.")

    st.divider()
    st.subheader("Portfolio contribution to the search")
    quality = hiring.get("quality_summary",{}) if isinstance(hiring,dict) else {}
    def count(key): return int(quality.get(key,0) or 0)
    eligible, engaged = count("analysis_eligible_sessions"), count("engaged_sessions")
    verified, intent = count("evidence_verified_sessions"), count("hiring_intent_sessions")
    if hiring:
        p1,p2,p3 = st.columns(3)
        p1.metric("Qualified portfolio sessions · 30d", eligible)
        p2.metric("Reached verified evidence",verified,
                  f"{verified/eligible:.0%} of qualified" if eligible else None,
                  delta_color="off")
        p3.metric("Recorded hiring intent",intent,
                  f"{intent/eligible:.0%} of qualified" if eligible else None,
                  delta_color="off")
        if eligible and not intent:
            st.caption("The portfolio has recorded qualified attention, but not a confirmed hiring-intent action in this window. "
                       "Treat reach and conversion separately.")
        elif eligible:
            st.caption("Portfolio intent is based on recorded on-site behavior, not a confirmed recruiter inquiry or identity.")
        else:
            st.caption("No qualified portfolio sessions are available in the 30-day quality-filtered layer.")
    else:
        st.caption("The quality-filtered visitor summary is currently unavailable.")

    if site and jobs:
        if site_corr and site_corr.get("top_status") is None:
            st.info("Portfolio visits and job-search outcomes do not yet show a defensible repeated association. "
                    "The correlation engine continues checking timing, signal quality and new sources.")
        elif site_corr:
            st.info("A portfolio ↔ job-search association passed initial screening. "
                    "Review the evidence, lag and alternate explanations before interpreting it.")
    elif site:
        st.caption("Recruitment records are required to test a portfolio-to-job relationship.")
    if st.button("Explore audience and content performance",key="overview_to_portfolio"):
        _go("portfolio")

    st.divider()
    st.subheader("What the Swedish market is telling you")
    if market:
        model = market_model
        by_key = _latest_by_indicator(model["latest"])
        highlights = [by_key[k] for k in (
            "employment_outlook_net_vgr",
            "employment_outlook_it_tech",
            "employment_outlook_services_consulting",
        ) if k in by_key]
        cols = st.columns(max(1,len(highlights)))
        for col,signal in zip(cols,highlights):
            col.metric(signal.get("indicator_name") or "Market signal",_format_value(signal),
                       help=f"Published observation: {signal.get('observation_date')}. "
                            "Survey outlook is not a probability of interview or employment.")
        interpretations = _readouts(by_key)
        for label, detail in interpretations[:2]:
            st.markdown(f"**{label}.** {detail}")
        if not model["findings"]:
            st.caption("Market-to-outcome correlations remain unconfirmed: the external indicators have too few repeated releases. "
                       "No forecast of interview or offer probability is presented.")
        if st.button("Explore Swedish market evidence",key="overview_to_market"):
            _go("market")
    else:
        st.caption("The market signal ledger is not available.")
    st.caption("Definitions: recorded primary job events are deduplicated, "
               "site sessions are anonymous sessions rather than people, and market interpretations are not empirical causal effects.")
