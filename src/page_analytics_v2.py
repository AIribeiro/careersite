from __future__ import annotations

import streamlit as st

from page_analytics import render_analytics_dashboard as render_site_analytics_dashboard
from page_article_analytics import render_article_analytics


def render_analytics_dashboard() -> None:
    """Render the established hiring-funnel dashboard plus article intelligence."""
    render_site_analytics_dashboard()

    if not st.session_state.get("careersite_analytics_access_code"):
        return
    if st.session_state.get("careersite_analytics_reset_pending", False):
        return

    render_article_analytics()
