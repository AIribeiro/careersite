"""Regression checks for Executive AI Briefings public/content architecture."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def content(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_public_route_and_navigation():
    main = content("main.py")
    nav = content("src/site_components.py")
    assert '"briefings": executive_briefings' in main
    assert '"briefings"' in main
    assert 'link("briefings"' not in nav
    assert 'Route("/briefings", _briefings_share' in content("app.py")


def test_series_is_visible_and_contextual():
    page = content("src/page_executive_briefings.py")
    assert "Executive AI Briefings" in page
    assert "published_briefings" in page
    assert 'BRIEFING_KIND = "Executive Briefing"' in page
    assert "not a ladder" in page
    assert 'href="?page=briefings"' in content("src/thinking_landing.py")
    assert "home_briefings_strip()" in content("src/page_home.py")


def test_content_studio_and_article_return_path():
    assert '"Executive Briefing"' in content("src/page_admin.py")
    cms = content("src/site_cms.py")
    assert 'article.kind != "Executive Briefing"' in cms
    assert 'briefing_back_href = "?page=briefings"' in cms
    assert "executive-capability-grid" in content("src/site_styles.py")


def test_seo_and_analytics_discovery():
    assert '"briefings": "Executive AI Briefings' in content("src/site_meta.py")
    assert 'data-analytics-section="briefings-capability-map"' in content("src/page_executive_briefings.py")
    assert 'data-hq-event="briefings_featured_open"' in content("src/page_executive_briefings.py")
