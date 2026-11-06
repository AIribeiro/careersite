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
    assert "st.segmented_control(" in source
    for section in ("overview", "audience", "discovery", "engagement", "actions"):
        assert f'section == "{section}"' in source
    assert "st.tabs(" not in source


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
