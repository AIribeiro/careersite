"""Regression contract: historical visitor insights remain public but non-sensitive."""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "src" / "page_public_portfolio_overview.py"
LEGACY = ROOT / "src" / "page_public_legacy_insights.py"
ROUTER = ROOT / "src" / "page_analytics_v2.py"


def test_public_overview_restores_lazy_legacy_toggle_below_cards():
    source = OVERVIEW.read_text(encoding="utf-8")
    assert source.index("st.html(portfolio_metric_grid(cards))") < source.index(
        '"Show legacy visitor analytics"'
    )
    assert "key=\"portfolio_show_legacy_analytics\"" in source
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
    assert 'key="portfolio_legacy_insights_tabs"' in source
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
