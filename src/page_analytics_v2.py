from __future__ import annotations

import streamlit as st

from page_analytics import (
    render_analytics_dashboard as render_site_analytics_dashboard,
    _noindex, _dashboard_css, REPORTING_WINDOWS, REPORTING_WINDOW_LABELS,
)
from page_article_analytics import render_article_analytics
from page_content_intelligence import render_content_intelligence


def render_analytics_dashboard() -> None:
    """Two bookmarkable analytics pages, with existing reports preserved."""
    _noindex()
    _dashboard_css()
    section = str(st.query_params.get("view", "pages"))
    if section not in {"pages", "articles"}:
        section = "pages"
    st.markdown(
        '<nav aria-label="Analytics navigation" style="display:flex;gap:24px;padding:18px 0;border-bottom:1px solid #ddd4c7;margin-bottom:24px">'
        + ''.join(f'<a href="?page=analytics&view={value}" target="_self" aria-current="{"page" if section == value else "false"}" style="font-weight:{"800" if section == value else "400"}">{label}</a>' for value, label in (("pages", "Page Views"), ("articles", "Article Views")))
        + '<a href="?page=home" target="_self">Back to portfolio</a></nav>',
        unsafe_allow_html=True,
    )
    st.title("Page Views" if section == "pages" else "Article Views")
    window = st.selectbox("Reporting window", [key for key, _ in REPORTING_WINDOWS], index=0,
                          format_func=lambda key: REPORTING_WINDOW_LABELS[key],
                          key="careersite_analytics_reporting_window")
    render_content_intelligence("page" if section == "pages" else "article", str(window))
    st.divider()
    if section == "pages":
        render_site_analytics_dashboard()
    else:
        render_article_analytics()
