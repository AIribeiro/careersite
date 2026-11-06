"""Regression contract: historical visitor insights remain public but non-sensitive."""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "src" / "page_public_portfolio_overview.py"
LEGACY = ROOT / "src" / "page_public_legacy_insights.py"
ROUTER = ROOT / "src" / "page_analytics_v2.py"


def test_public_overview_shows_advanced_tabs_by_default_below_cards():
    source = OVERVIEW.read_text(encoding="utf-8")
    assert "st.toggle(" not in source
    assert "portfolio_show_legacy_analytics" not in source
    assert source.index("st.html(portfolio_metric_grid(cards))") < source.index(
        "render_public_legacy_insights(str(window))"
    )
    assert (
        "from page_public_legacy_insights import render_public_legacy_insights"
        in source
    )
    assert "render_public_legacy_insights(str(window))" in source


def test_anonymous_navigation_reaches_the_public_overview():
    router = ROUTER.read_text(encoding="utf-8")
    assert "if owner is None:" in router
    assert "_render_public_analytics()" in router
    assert "if section == \"overview\":" in router
    assert "render_public_portfolio_overview()" in router


def test_legacy_renderer_never_invokes_owner_or_raw_campaign_reports():
    source = LEGACY.read_text(encoding="utf-8")
    assert "_fetch_dashboard(window)" in source
    for forbidden in (
        "_fetch_hiring_intelligence(", "owner_hiring_headers(",
        "render_attribution_integrity(", "render_cv_attribution_audit(",
        "render_site_analytics_dashboard(", "render_reader_sources(",
        "service_role", "raw_user_meta_data",
    ):
        assert forbidden not in source


def test_legacy_sections_load_one_at_a_time():
    source = LEGACY.read_text(encoding="utf-8")
    assert "tabs = st.tabs(" in source
    assert 'on_change="rerun"' in source
    assert 'key="portfolio_advanced_insights_tabs"' in source
    assert "if tab.open" in source
    assert "with active_tab:" in source
    assert '"Explore historical analytics"' not in source
    for section in ("signals", "overview", "audience", "discovery", "engagement",
                    "actions", "channels", "content", "ctas", "experience",
                    "behavior", "coverage"):
        assert f'"{section}"' in source
    assert "st.tabs(" in source
    assert "render_public_deep_insights(section, window, data)" in source


def test_channel_grouping_hides_exact_source_and_campaign_labels():
    tree = ast.parse(LEGACY.read_text(encoding="utf-8"))
    selected = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in ("_source_channel", "_channel_rows")
    ]
    assert len(selected) == 2
    namespace = {
        "_count": lambda value: max(0, int(value or 0)),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(LEGACY), "exec"), namespace)
    rows = namespace["_channel_rows"]([
        {"attribution_source": "linkedin?role=secret-employer", "sessions": 5},
        {"attribution_source": "linkedin?role=other-employer", "sessions": 3},
        {"attribution_source": "career-client-private-label", "sessions": 2},
        {"attribution_source": "direct/unknown", "sessions": 4},
    ])
    assert {"channel": "LinkedIn", "sessions": 8} in rows
    assert {"channel": "Direct / unattributed", "sessions": 4} in rows
    assert {"channel": "Other sources", "sessions": 2} in rows
    assert "secret-employer" not in str(rows)
    assert "career-client-private-label" not in str(rows)


def test_public_deep_insights_use_anonymous_aggregate_rpcs_only():
    deep = (ROOT / "src" / "page_public_legacy_intelligence.py").read_text(encoding="utf-8")
    model = (ROOT / "src" / "portfolio_legacy_signal_model.py").read_text(encoding="utf-8")
    assert "public_analytics_rpc_headers()" in deep
    assert "careersite_content_intelligence_v2" in deep
    assert "careersite_behavior_intelligence" in deep
    assert "@st.cache_data(ttl=300" in deep
    assert "render_public_deep_insights" in deep
    assert "traffic_findings(" in deep
    assert "channel_rollup(" in deep
    assert "_source_channel(" not in deep
    for source in (deep, model):
        for forbidden in ("owner_hiring_headers(", "service_role", "owner_session(",
                          "careersite_hiring_intelligence_v1",
                          "careersite_attribution_integrity_v1",
                          "careersite_public_job_summary_v1"):
            assert forbidden not in source


def test_behavior_and_content_reports_remain_lazy():
    source = (ROOT / "src" / "page_public_legacy_intelligence.py").read_text(encoding="utf-8")
    fn = source[source.index("def render_public_deep_insights("):]
    assert fn.index('if section == "signals"') < fn.index("fetch_public_content_aggregate(window)")
    assert fn.index('if section == "channels"') < fn.index("fetch_public_content_aggregate(window)")
    assert fn.index('if section == "behavior"') < fn.index("fetch_public_content_aggregate(window)")
    assert 'fetch_public_behavior_aggregate(window)' in fn


def test_public_ux_labels_reject_urls_and_markup():
    path = ROOT / "src" / "page_public_legacy_intelligence.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    selected = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in ("_cta_name", "_content_name")
    ]
    assert len(selected) == 2
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    label = namespace["_cta_name"]
    assert label("View my impact →") == "View my impact →"
    assert label("https://example.org/?role=employer") == "Unlabeled action"
    assert label("Contact *[click me](https://x.com)*") == "Unlabeled action"
    assert "*" not in label("Contact **today**")
    content = namespace["_content_name"]("article:why-governance-matters")
    assert content == "Why Governance Matters"


def test_advanced_insights_are_visual_dashboards_not_raw_tables():
    overview = OVERVIEW.read_text(encoding="utf-8")
    tabs = LEGACY.read_text(encoding="utf-8")
    deep = (ROOT / "src" / "page_public_legacy_intelligence.py").read_text(encoding="utf-8")
    for source in (overview, tabs, deep):
        assert "st.dataframe(" not in source
        assert "st.table(" not in source
    assert "st.subheader(\"Advanced Insights\")" in tabs
    assert "st.toggle(" not in overview
    assert "Refresh advanced insights" in tabs
    assert '"Legacy visitor analytics"' not in tabs
    assert '"Refresh legacy reports"' not in tabs
    for section in ("_channels", "_content", "_ctas", "_experience", "_behavior"):
        assert f"def {section}(" in deep
    assert "def _kpi_strip(" in deep
    assert "def _ranked_chart(" in deep
    assert "def _decision_note(" in deep
    assert 'st.vega_lite_chart(' in deep
    assert "Measured sessions" in deep


def test_every_public_portfolio_analytics_renderer_is_visual_first():
    """No unbounded tables, including Explore Content, Weekly AI, Briefings."""
    paths = (
        "page_public_portfolio_overview.py",
        "page_public_legacy_insights.py",
        "page_public_legacy_intelligence.py",
        "page_content_intelligence.py",
        "page_weekly_ai_analytics.py",
        "page_executive_briefings_analytics.py",
        "page_article_analytics.py",
    )
    for filename in paths:
        source = (ROOT / "src" / filename).read_text(encoding="utf-8")
        assert "st.dataframe(" not in source, f"Raw table returned to {filename}"
        assert "st.table(" not in source, f"Raw table returned to {filename}"


def test_advanced_dashboard_has_executive_visual_contract():
    text = (ROOT / "src" / "page_public_legacy_intelligence.py").read_text(encoding="utf-8")
    for signature in ("def _channels(", "def _content(", "def _ctas(",
                      "def _experience(", "def _behavior(", "def _coverage("):
        assert signature in text
    assert text.count("_ranked_chart(") >= 14
    assert text.count("_kpi_strip(") >= 6
    assert text.count("_decision_note(") >= 5
    assert "st.vega_lite_chart(" in text
    assert "page / error category" not in text.lower() or "error" in text.lower()
