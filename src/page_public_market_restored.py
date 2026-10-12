"""Full Swedish Market dashboard restored for public read-only Analytics.

Reuses the original direction, trend, correlation and evidence UIs. Loads
complete external historical observations through vetted non-personal RPC and
monthly outcomes through deduplicated anonymous aggregate reporting.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from job_market_correlations import analyze_market
from page_job_market_insights import (
    _market_pulse, _market_history, _relationship_screen, _evidence,
)
from page_public_analytics import _portfolio_job_relationships
from page_content_intelligence import _fetch_rpc
from site_analytics_public import fetch_public_analytics_rpc


def _load_public_market() -> tuple[dict,dict,dict | None]:
    market=fetch_public_analytics_rpc("careersite_public_market_history_v1")
    jobs=fetch_public_analytics_rpc("careersite_public_job_summary_v1",{"p_days":730})
    try:
        portfolio=_fetch_rpc("careersite_portfolio_signals_daily_v1",{"p_days":365})
    except (RuntimeError,ValueError,PermissionError,TimeoutError):
        portfolio=None
    return market,jobs,portfolio


def render_public_market_restored() -> None:
    st.title("Swedish Job Market")
    st.caption(
        "Market direction, official-source historical trends, job-search "
        "relationships, portfolio context and a verifiable source ledger."
    )
    try:
        raw,jobs,portfolio=_load_public_market()
        now=datetime.now(ZoneInfo("Europe/Stockholm"))
        model=analyze_market(
            raw.get("history") or [], [], portfolio, now.date(),
            public_job_summary=jobs,
        )
    except (RuntimeError,ValueError,TypeError,PermissionError,KeyError):
        st.error(
            "The Swedish market analysis could not be refreshed. "
            "External source data may be temporarily unavailable."
        )
        return
    if not raw.get("history"):
        st.info("No source-backed historical observations are currently available.")
        return
    coverage=model["coverage"]
    newest=max(str(r.get("observation_date") or "") for r in raw["history"])
    st.caption(
        f"Checked {now:%d %b %Y, %H:%M} Stockholm · "
        f"{coverage['observations']} deduplicated releases · "
        f"{coverage['indicators']} indicator series · latest {newest}. "
        "Historical revisions are not counted as independent releases."
    )
    focus=st.segmented_control(
        "Market question",
        options=["direction","relationships","evidence"],
        default="direction",
        format_func=lambda x:{
            "direction":"What is changing?",
            "relationships":"What connects to my search?",
            "evidence":"Sources & measurement",
        }[x],
        key="market_analysis_focus",width="stretch",
    ) or "direction"
    st.divider()
    if focus=="direction":
        _market_pulse(model)
        st.divider()
        _market_history(model)
    elif focus=="relationships":
        _relationship_screen(model,compact=False)
        st.divider()
        _portfolio_job_relationships(jobs)
        st.caption(
            "Only anonymized dated recruitment counts are used here. "
            "Employer names and underlying recruiter events remain private."
        )
    else:
        _evidence(model)
    if st.button("Recalculate market analysis",key="market_refresh"):
        st.rerun()
