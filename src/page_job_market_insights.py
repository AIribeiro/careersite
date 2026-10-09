"""Owner-only Swedish hiring-market intelligence, using live Supabase evidence."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from job_market_correlations import OUTCOMES, analyze_market
from portfolio_job_correlations import analyze_portfolio_job_correlations
from page_content_intelligence import _fetch_rpc
from site_cms import _request_json, _rest_url, ensure_owner_session

MARKET_FIELDS = (
    "id,series_key,indicator_key,indicator_name,record_type,observation_date,period_start,"
    "period_end,period_label,frequency,published_at,region,sector,role_family,metric_value,"
    "metric_value_text,metric_unit,comparison_value,change_value,signal_score,confidence_score,"
    "relevance_score,is_leading_indicator,expected_lag_days,insight_summary,"
    "job_search_implication,methodology_note,source_organization,source_title,source_url,"
    "is_current,valid_until,is_quantitative,first_seen_at,last_confirmed_at,updated_at"
)
HIGHLIGHTS = (
    "employment_outlook_net", "employment_outlook_net_vgr",
    "employment_outlook_it_tech", "employment_outlook_services_consulting",
    "employment_outlook_manufacturing_auto",
)


def fetch_market_records(token: str) -> list[dict]:
    """Owner access uses the existing CMS JWT and read-only market RLS policy."""
    results = []
    offset = 0
    while offset < 20000:
        batch = _request_json("GET", _rest_url(
            f"job_market_insights?select={MARKET_FIELDS}&order=id.asc&limit=500&offset={offset}"
        ), token=token)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected job-market response.")
        results.extend(batch)
        if len(batch) < 500:
            return results
        offset += 500
    raise RuntimeError("Market evidence exceeds the page limit; restrict the database query.")


def _latest_by_indicator(rows: list[dict]) -> dict:
    result = {}
    for r in rows:
        key = r.get("indicator_key")
        if key and (key not in result or
                    str(r.get("observation_date") or "") > str(result[key].get("observation_date") or "")):
            result[key] = r
    return result


def _format_value(row: dict) -> str:
    val = row.get("metric_value")
    if val is None:
        return str(row.get("metric_value_text") or "—")
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    unit = str(row.get("metric_unit") or "").lower()
    if unit in ("percent", "percent_change", "percent_of_labour_force"):
        return f"{v:,.1f}%"
    if unit == "net_balance":
        return f"{v:,.1f} balance"
    if unit.startswith("index"):
        return f"{v:,.1f}"
    if unit in ("jobs", "people", "occupational_groups"):
        return f"{v:,.0f}"
    return f"{v:,.1f} {unit.replace('_', ' ')}".strip()


def _market_pulse(model: dict) -> None:
    by_key = _latest_by_indicator(model["latest"])
    st.subheader("Market direction: demand is not the same as hiring")
    st.caption("External releases are observations about the Swedish market, not estimates of demand for one senior candidate.")
    first = [by_key[k] for k in HIGHLIGHTS if k in by_key]
    if first:
        cols = st.columns(min(3, len(first)))
        for index, item in enumerate(first):
            with cols[index % len(cols)]:
                st.metric(str(item.get("indicator_name") or "Employment outlook"), _format_value(item),
                          help=f"Source: {item.get('source_organization') or 'Unrecorded'}. "
                               f"Observed {item.get('period_label') or item.get('observation_date')}. "
                               "Net employment outlook is not the percentage of vacancies or the chance of an offer.")
        points = [{"Segment": r.get("indicator_name"), "Net outlook": float(r["metric_value"]),
                   "Period": r.get("period_label") or r.get("observation_date")}
                  for r in first if r.get("metric_value") is not None]
        if points:
            st.altair_chart(
                alt.Chart(alt.Data(values=points)).mark_bar(cornerRadiusEnd=5).encode(
                    x=alt.X("Net outlook:Q", title="Net employment outlook (percentage points)"),
                    y=alt.Y("Segment:N", sort="-x", title=None, axis=alt.Axis(labelLimit=350)),
                    tooltip=["Segment:N", "Net outlook:Q", "Period:N"],
                ).properties(height=max(195, len(points)*42)), width="stretch")
            st.caption("These outlook estimates share one survey family and period; they are cross-sectional comparisons, not a time trend.")
    for item in _readouts(by_key):
        st.markdown(f"**{item[0]}** — {item[1]}")


def _readouts(by_key: dict) -> list[tuple[str,str]]:
    result = []
    services = by_key.get("services_pmi")
    employment = by_key.get("services_pmi_employment_below_50_streak")
    if services and employment:
        result.append(("Services expansion vs recruitment",
            f"Services PMI is {_format_value(services)}, while its employment component has remained below 50 for "
            f"{_format_value(employment)}. More services activity has not yet meant broad employment expansion."))
    vgr = by_key.get("employment_outlook_net_vgr")
    vacancies = by_key.get("new_vacancies_arbetsformedlingen")
    if vgr and vacancies:
        direction = vacancies.get("change_value")
        delta = f" ({float(direction):+,.0f} against its comparison period)" if direction is not None else ""
        result.append(("Västra Götaland: intentions vs observed vacancies",
            f"The reported net hiring outlook is {_format_value(vgr)}, but registered new vacancies are "
            f"{_format_value(vacancies)}{delta}. The reports cover different periods and populations; "
            "this is a tension to monitor, not a statistical correlation."))
    ai = by_key.get("ai_mentions_growth_non_it")
    if ai:
        result.append(("AI adoption beyond technical departments",
            f"The historical change in AI-related vacancy mentions outside IT is {_format_value(ai)}. "
            "This widens the areas worth searching for enterprise AI leadership, but does not prove that "
            "senior leadership vacancies or interview invitations increased."))
    return result


def _market_history(model: dict) -> None:
    st.subheader("Market trends: independent releases only")
    if not model["trends"]:
        st.info("Every indicator currently has one independently observed period. "
                "The engine cannot show a genuine indicator time series until the same series is updated for new periods.")
    else:
        st.dataframe(model["trends"], hide_index=True, width="stretch")
        eligible = [r for g in model["groups"].values() if len(g) >= 2 for r in g
                    if r.get("metric_value") is not None]
        if eligible:
            options = {key: g for key,g in model["groups"].items() if
                       sum(r.get("metric_value") is not None for r in g) >= 2}
            if options:
                selected = st.selectbox("Historical series",list(options),
                    format_func=lambda k: str(options[k][-1].get("indicator_name") or k),
                    key="job_market_history_series")
                chart = [{"Date":r.get("period_end") or r.get("observation_date"),
                          "Metric":float(r["metric_value"])} for r in options[selected]
                         if r.get("metric_value") is not None]
                st.altair_chart(alt.Chart(alt.Data(values=chart)).mark_line(point=True).encode(
                    x="Date:T",y=alt.Y("Metric:Q",title=options[selected][-1].get("metric_unit")),
                    tooltip=["Date:T","Metric:Q"]).properties(height=260),width="stretch")


def _relationship_screen(model: dict, *, compact: bool) -> None:
    c = model["coverage"]
    st.subheader("Automatic market ↔ job-search ↔ portfolio correlations")
    st.caption("Re-evaluated against fresh Supabase records every 15 minutes while this page is open. "
               "New market indicator series automatically enter the tests when enough releases accumulate.")
    cols = st.columns(4)
    cols[0].metric("Full job-search months", c["job_full_months"])
    cols[1].metric("Full portfolio months", c["portfolio_full_months"])
    cols[2].metric("Repeated market series", c["repeat_series"])
    cols[3].metric("Qualified statistical tests", c["tested"])
    findings = model["findings"]
    if not findings:
        st.info(
            "No defensible market-to-job or market-to-portfolio correlation is available yet. "
            "Each market indicator currently has too few independent releases for a lag test. "
            "The system is monitoring the data rather than inventing a coefficient."
        )
    else:
        st.markdown(f"**{len(findings)} relationship(s) meet monitoring or repeated-association screens.**")
        st.dataframe([{
            "Market indicator": f["indicator"],
            "Outcome": OUTCOMES[f["outcome"]],
            "Delay": f"{f['lag_months']} calendar month(s)",
            "Pearson r": round(f["r"], 2),
            "Rank correlation": round(f["rho"],2) if f["rho"] is not None else None,
            "Adjusted q": f["q"],
            "Independent pairs": f["n"],
            "Assessment": f["status"],
        } for f in findings[:15]],hide_index=True,width="stretch")
        st.caption("Exploratory ecological associations only. A positive result is not a causal hiring effect.")
    if not compact:
        monthly = model["monthly"]
        if monthly:
            st.subheader("Your recorded job-search activity")
            labels = [k for k in ("applications","responses","interviews") if k in OUTCOMES]
            series = [{"Month":r["Month"],"Stage":OUTCOMES[k],"Events":r[k]}
                      for r in monthly for k in labels]
            st.altair_chart(alt.Chart(alt.Data(values=series)).mark_line(point=True).encode(
                x="Month:T", y=alt.Y("Events:Q",axis=alt.Axis(tickMinStep=1)),
                color="Stage:N",tooltip=["Month:T","Stage:N","Events:Q"]
            ).properties(height=285),width="stretch")
            st.caption("Counts are primary, deduplicated events in complete months. "
                       "The first partially imported and current incomplete months are excluded. "
                       "Missing evidence is not verified inactivity.")
        else:
            st.caption("No complete job-search calendar months are available for trend comparison.")
    with st.expander("Methodology and evidence limits", expanded=False):
        st.markdown(
            "Each external measure is grouped by indicator, source, reporting frequency, geography and sector. "
            "Source observations and subjective `signal_score` are kept separate. Duplicated revisions of "
            "the same period do not become additional observations. Market releases need a documented "
            "publication date to participate in lagged tests; unseen historical releases cannot be backfilled "
            "as imaginary observations. The same market metric is compared with recorded application, contact, "
            "completed interview, progression, rejection and portfolio outcomes at 0/1/2/3-month lags. "
            "Only full calendar months are paired; no forward filling or synthetic zero-history. "
            "The baseline needs at least 12 independent pairs, variation in source and outcome data, "
            "Pearson/Spearman agreement, leave-one-out and change checks. Repeated associations require at "
            "least 24 pairs, direction stability in both halves and an adjusted multiple-testing screen. "
            "These exploratory tests still cannot establish causation or individual visitor identity. "
            "The engine expands its candidate pool and recomputes its assessments on every refresh; "
            "it is not an automatically retrained predictive model. Offer or interview probability and "
            "time-to-offer forecasts are withheld without a sufficiently large, prospectively validated cohort."
        )


def _evidence(model: dict) -> None:
    st.subheader("Source ledger")
    st.caption("Raw values, interpreted direction and provenance stay separate. "
               "Source links allow you to inspect the underlying publications.")
    region_options = sorted({str(r.get("region") or "Sweden-wide") for r in model["latest"]})
    selection = st.selectbox("Geography",["All geographies"] + region_options,
                             key="job_market_region_filter")
    filtered = [r for r in model["latest"] if
                selection == "All geographies" or str(r.get("region") or "Sweden-wide") == selection]
    st.dataframe([{
        "Indicator": r.get("indicator_name"),
        "Region": r.get("region") or "Sweden-wide",
        "Sector": r.get("sector"),
        "Metric": _format_value(r),
        "Change (source units)": r.get("change_value"),
        "Interpretation score": r.get("signal_score"),
        "Relevance / 100": r.get("relevance_score"),
        "Confidence / 100": r.get("confidence_score"),
        "Observation": r.get("observation_date"),
        "Source": r.get("source_organization"),
        "Reference": r.get("source_url") if str(r.get("source_url") or "").startswith("https://") else None,
    } for r in filtered], hide_index=True, width="stretch",
        column_config={"Reference":st.column_config.LinkColumn("Source document")})
    choices = {f"{r.get('indicator_name')} · {r.get('source_organization')}":r for r in filtered}
    if choices:
        selected = st.selectbox("Inspect source interpretation", list(choices),
                                key="job_market_inspect")
        item = choices[selected]
        st.write(item.get("insight_summary") or "No summary recorded.")
        st.caption(item.get("job_search_implication") or "No search-specific interpretation recorded.")
        if item.get("methodology_note"):
            st.caption("Method: " + str(item["methodology_note"]))
    st.caption("Source publication timing, reporting periods, revisions and the freshness of underlying "
               "data differ. A market signal does not automatically represent a current live vacancy.")


def _portfolio_context(site: dict | None, jobs: list[dict]) -> None:
    st.subheader("Portfolio behavior and recruitment")
    if not site:
        st.caption("Owner-qualified portfolio session aggregates are temporarily unavailable.")
        return
    report = analyze_portfolio_job_correlations(site, jobs)
    if report["notice"]:
        st.info(report["notice"])
        return
    st.caption(f"{report['coverage']['coverage']} complete tracked days available. "
               "Portfolio and recruitment are tested separately at daily frequency, "
               "without assuming visitors can be attributed to employers.")
    if report["top_status"] is None:
        st.info("No validated portfolio-to-recruitment association so far. "
                "The Job Search Analytics > Portfolio correlations panel automatically rechecks "
                "new sources, pages and behavior as observations accumulate.")
    else:
        hits = [r for r in report["ranked"] if r["status"] in ("Repeated association","Worth monitoring")]
        st.dataframe([{
            "Portfolio behavior": report["features"].get(r["feature"],r["feature"]),
            "Search event":report["outcomes"].get(r["outcome"],r["outcome"]),
            "Timing":r["lag"],"Correlation":round(r["r"],2),
            "Evidence":r["status"]} for r in hits[:5]],hide_index=True,width="stretch")


def _load(session, provided_jobs):
    valid = ensure_owner_session(session)
    if not valid or not valid.get("access_token"):
        raise PermissionError("Owner sign-in is required.")
    st.session_state["cms_auth"] = valid
    token = str(valid["access_token"])
    market = fetch_market_records(token)
    if provided_jobs is None:
        from page_job_search_analytics import fetch_job_records
        jobs = fetch_job_records(token)
    else:
        jobs = provided_jobs
    try:
        site = _fetch_rpc("careersite_portfolio_signals_daily_v1", {"p_days":365})
    except (RuntimeError, PermissionError, TimeoutError, ValueError):
        site = None
    return market, jobs, site


@st.fragment(run_every="15m")
def render_swedish_job_market(session: dict | None) -> None:
    st.title("Swedish Job Market")
    st.caption("External hiring conditions, your recorded search outcomes and portfolio audience behavior — "
               "with explicit evidence thresholds.")
    try:
        market, jobs, site = _load(session, None)
        now = datetime.now(ZoneInfo("Europe/Stockholm"))
        model = analyze_market(market,jobs,site,now.date())
    except (RuntimeError,PermissionError,TimeoutError,ValueError,TypeError):
        st.error("Market intelligence could not be refreshed. Please check the owner session and source permissions.")
        return
    if not market:
        st.info("No Swedish market observations have been recorded.")
        return
    c = model["coverage"]
    newest = max(str(r.get("observation_date") or "") for r in market)
    st.caption(f"Checked {now:%d %b %Y, %H:%M} Stockholm · {c['observations']} distinct observations · "
               f"{c['indicators']} indicator series · latest observed {newest}. "
               "Automatic recomputation uses the existing Analytics sign-in.")
    _market_pulse(model)
    st.divider()
    _market_history(model)
    st.divider()
    _relationship_screen(model,compact=False)
    st.divider()
    _portfolio_context(site,jobs)
    st.divider()
    _evidence(model)
    if st.button("Recalculate market analysis",key="market_refresh"):
        st.rerun(scope="fragment")


@st.fragment(run_every="15m")
def render_market_relationships(jobs: list[dict]) -> None:
    """Permanent live section inside the Job Search Analytics statistics page."""
    try:
        session = st.session_state.get("cms_auth")
        market, _, site = _load(session,jobs)
        model = analyze_market(market,jobs,site,
                               datetime.now(ZoneInfo("Europe/Stockholm")).date())
    except (RuntimeError,PermissionError,TimeoutError,ValueError,TypeError):
        st.warning("The market comparison is temporarily unavailable; existing job statistics remain visible.")
        return
    _relationship_screen(model,compact=True)
    if st.button("Recalculate market comparisons",key="market_stats_refresh"):
        st.rerun(scope="fragment")
