from __future__ import annotations

import streamlit as st

from page_analytics import render_analytics_dashboard as render_site_analytics_dashboard
from page_article_analytics import render_article_analytics


def render_analytics_dashboard() -> None:
    """Render the established hiring-funnel dashboard plus article intelligence."""
    render_site_analytics_dashboard()

    render_article_analytics()
