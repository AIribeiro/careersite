"""Regression tests for hourly Thinking collection ranking.

These tests avoid live analytics dependencies: the public aggregate RPC is
verified separately in Supabase. They protect routing, timing, selectors,
fallbacks and preservation of the existing content.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import thinking_dynamic_order
from thinking_landing import landing
from about_next_navigation import portfolio_next_navigation


def test_thinking_sections_have_stable_anchor_ids_and_status():
    page = landing()
    assert page.count('id="thinking-briefings"') == 1
    assert page.count('id="thinking-articles"') == 1
    assert page.count('id="thinking-order-status"') == 1
    assert 'href="?page=thinking#weekly-ai"' in page
    assert 'href="?page=thinking#thinking-briefings"' in page
    assert 'href="?page=thinking#thinking-articles"' in page
    assert "Weekly AI · Executive Briefings · Articles" in page


def test_weekly_ai_injection_has_the_expected_third_section_anchor():
    weekly_source = (ROOT / "src" / "thinking_weekly_brief.py").read_text(encoding="utf-8")
    assert 'id="weekly-ai"' in weekly_source
    assert 'data-analytics-section="weekly-ai-feature"' in weekly_source


def test_thinking_hourly_controller_uses_public_aggregate_only(monkeypatch):
    captured = []

    def collect(html, *, height, width):
        captured.append(html)
        assert height == 0
        assert width == 0

    monkeypatch.setattr(thinking_dynamic_order.components, "html", collect)
    thinking_dynamic_order.mount_thinking_hourly_order()
    assert len(captured) == 1
    script = captured[0]

    assert "/rest/v1/rpc/careersite_thinking_recent_views_v1" in script
    assert "['weekly_ai', 'briefings', 'articles']" in script
    assert "'#weekly-ai'" in script
    assert "'#thinking-briefings'" in script
    assert "'#thinking-articles'" in script
    assert "counts.get(b) - counts.get(a)" in script
    assert "kinds.indexOf(a) - kinds.indexOf(b)" in script
    assert "3600000 - (Date.now() % 3600000)" in script
    assert "visibilitychange" in script
    assert "credential" in script.lower()
    assert "data-analytics-section" not in script  # no tracking-event inflation
    assert "article_slug" not in script
    assert "session_id" not in script


def test_controller_preserves_dom_and_falls_back_on_unavailable_analytics(monkeypatch):
    output = []
    monkeypatch.setattr(
        thinking_dynamic_order.components, "html",
        lambda script, **kwargs: output.append(script),
    )
    thinking_dynamic_order.mount_thinking_hourly_order()
    script = output[0]
    assert "parent.insertBefore(node, marker)" in script
    assert "doc.createComment('thinking-collection-order')" in script
    assert "observed.getBoundingClientRect()" in script
    assert "if (!response.ok)" in script
    assert "waitForDOM(kinds, 24)" in script
    assert "No recorded views in the past hour" in script
    assert "Recent readership unavailable" in script
    assert "request.signal.aborted" in script
    assert "stopped" in script


def test_controller_is_only_mounted_for_thinking_catalogue():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'PAGE == "thinking"' in main
    assert "not ARTICLE_QUERY" in main
    assert 'str(st.query_params.get("weekly_ai", "")).lower() != "archive"' in main
    assert "mount_thinking_hourly_order()" in main
    assert 'id="thinking-continue"' in portfolio_next_navigation("thinking")


def test_rpc_schema_is_committed_and_uses_raw_view_events_not_sessions():
    sql = (ROOT / "docs" / "sql" / "careersite_thinking_recent_views_v1.sql").read_text(
        encoding="utf-8"
    )
    assert "careersite_thinking_recent_views_v1()" in sql
    assert "e.event_name = 'article_view'" in sql
    assert "count(*)::bigint AS views" in sql
    assert "count(DISTINCT" not in sql
    assert "interval '60 minutes'" in sql
    assert "a.status = 'published'" in sql
    assert "SET search_path = ''" in sql
    assert "REVOKE ALL" in sql
    assert "GRANT EXECUTE" in sql
