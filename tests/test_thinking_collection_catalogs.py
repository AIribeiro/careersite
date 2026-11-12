"""Regression tests for the two matching Thinking editorial catalogues."""

from datetime import date, timedelta
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_cms import CmsArticle
from thinking_landing import landing
import thinking_collection_catalogs as catalogs


def _briefings(count=11):
    return tuple(
        CmsArticle(
            title=f"Executive briefing {number}",
            slug=f"test-executive-briefing-{number:02d}",
            subtitle=f"Decision, ownership and business implications {number}.",
            excerpt=f"A short introduction to executive decision {number}.",
            kind="Executive Briefing",
            category="AI Governance",
            status="published",
            published_at=f"2025-06-{number:02d}T12:00:00+00:00",
            read_minutes=8,
        )
        for number in range(1, count + 1)
    )


def _weekly(count=6):
    return tuple(
        CmsArticle(
            title=f"Weekly perspective {number}",
            slug=f"weekly-ai-{(date(2026, 9, 4) + timedelta(weeks=number)).isoformat()}",
            subtitle=f"What changed this week: {number}.",
            excerpt=f"The implications and trade-offs behind week {number}.",
            kind="Weekly Brief",
            category="Weekly AI",
            status="published",
            published_at=f"{(date(2026, 9, 4) + timedelta(weeks=number)).isoformat()}T19:00:00+00:00",
            read_minutes=1,
        )
        for number in range(count)
    )


def test_three_sections_keep_required_anchors_and_existing_articles(monkeypatch):
    monkeypatch.setattr(catalogs, "_image_url", lambda article, kind: "")
    doc = landing()
    updated = catalogs.inject_thinking_collections(doc, _briefings() + _weekly())
    for section_id in ("weekly-ai", "thinking-briefings", "thinking-articles"):
        assert updated.count(f'id="{section_id}"') == 1
    assert updated.index('id="weekly-ai"') < updated.index('id="thinking-briefings"')
    assert updated.index('id="thinking-briefings"') < updated.index('id="thinking-articles"')
    assert 'class="thinking-briefing-card"' not in updated
    assert "Clarity before the next AI decision." in updated
    assert "The AI week, through a leadership lens." in updated
    assert 'id="thinking-order-status"' not in updated
    assert 'id="speaking-publications"' not in updated or updated.index('id="speaking-publications"') > updated.index('id="thinking-articles"')


def test_premium_reader_stays_directly_after_hero_with_all_three_collections(monkeypatch):
    """The reader invitation is fixed; only editorial formats can be reordered."""
    monkeypatch.setattr(catalogs, "_image_url", lambda article, kind: "")
    for published in (_briefings() + _weekly(), ()):
        html = catalogs.inject_thinking_collections(landing(), published)
        hero = html.index('<section class="pagehero">')
        hero_end = html.index('</section>', hero) + len('</section>')
        invitation = html.index('<section class="thinking-reader-invite"')
        weekly = html.index('<section class="section white cms-latest thinking-collection thinking-collection--weekly_ai"')
        briefings = html.index('<section class="section white cms-latest thinking-collection thinking-collection--briefings"')
        articles = html.index('id="thinking-articles"')
        assert hero < hero_end < invitation < weekly < briefings < articles
        # There is no editorial section inserted between hero and reader CTA.
        assert 'id="weekly-ai"' not in html[hero_end:invitation]
        assert html.count('id="premium-reader-library"') == 1


def test_hourly_controller_cannot_move_collections_above_premium_reader():
    client = (ROOT / "src" / "thinking_dynamic_order.py").read_text("utf-8")
    assert "root.querySelector('#premium-reader-library')" in client
    assert "fixedReader.parentNode !== parent" in client
    assert "fixedReader.nextElementSibling === nodes[0]" in client
    assert "parent.insertBefore(marker, fixedReader.nextSibling)" in client
    assert "nodes.forEach(node => parent.insertBefore(node, marker))" in client
    assert "counts.get(b)[metric] - counts.get(a)[metric]" in client


def test_briefings_feature_automatic_readership_and_four_cards(monkeypatch):
    monkeypatch.setattr(catalogs, "_image_url", lambda article, kind: "")
    articles = _briefings()
    # No recent publications, so the existing Articles selection rule chooses
    # the most-read briefing; this selection remains separate from pagination.
    counts = {a.slug: index for index, a in enumerate(articles)}
    html = catalogs._collection("briefings", articles, counts)
    featured = articles[-1]
    assert featured.title in html
    assert f'data-hq-content-slug="{featured.slug}"' in html
    assert html.count('class="recent-card cms-article-card"') == 4
    assert html.count('class="cms-thinking-highlight thinking-collection-highlight"') == 1
    assert 'class="cms-pagination"' in html
    assert "Showing 1–4 of 10 Executive AI Briefings editions" in html
    assert f'data-hq-event="thinking_briefings_highlight_open"' in html
    assert 'class="cms-article-excerpt"' in html
    assert 'briefings_page=2' in html
    assert 'briefings_page=3' in html
    assert 'thinking_briefings_library_open' in html
    # Highlight must not recur as one of the 4 regular entries.
    assert html.count(f'data-hq-event="thinking_briefings_edition_open" data-hq-content-slug="{featured.slug}"') == 0


def test_weekly_feature_is_newest_and_four_older_issues_are_listed(monkeypatch):
    monkeypatch.setattr(catalogs, "_image_url", lambda article, kind: "")
    articles = _weekly(6)
    html = catalogs._collection("weekly_ai", articles, None)
    assert html.count('class="recent-card cms-article-card"') == 4
    assert html.count('class="cms-thinking-highlight thinking-collection-highlight"') == 1
    assert f'data-hq-event="thinking_weekly_ai_highlight_open"' in html
    assert 'weekly_page=2' in html
    assert "Showing 1–4 of 5 Weekly AI editions" in html
    assert 'thinking_weekly_full_archive' in html
    assert articles[-1].title in html
    assert '?page=thinking&amp;weekly_ai=archive' in html


def test_independent_pagination_preserves_other_page_and_attribution(monkeypatch):
    import streamlit as st

    monkeypatch.setattr(st, "query_params", {
        "weekly_page": "2", "briefings_page": "2", "articles_page": "3",
        "source": "linkedin", "role": "Executive",
        "utm_campaign": "portfolio_refresh",
    })
    briefs = catalogs._page_href("briefings", 3)
    weekly = catalogs._page_href("weekly_ai", 1)
    assert "briefings_page=3" in briefs
    assert "weekly_page=2" in briefs
    assert "articles_page=3" in briefs
    assert "weekly_page=1" in weekly
    assert "briefings_page=2" in weekly
    assert "utm_campaign=portfolio_refresh" in briefs
    assert "source=linkedin" in weekly
    assert "role=Executive" in briefs
    assert briefs.endswith("#thinking-briefings")
    assert weekly.endswith("#weekly-ai")


def test_paging_clamps_to_valid_range_and_excludes_highlight(monkeypatch):
    import streamlit as st

    monkeypatch.setattr(catalogs, "_image_url", lambda article, kind: "")
    monkeypatch.setattr(st, "query_params", {
        "weekly_page": "2", "briefings_page": "3",
    })
    briefing_html = catalogs._collection("briefings", _briefings(10), None)
    weekly_html = catalogs._collection("weekly_ai", _weekly(6), None)
    assert briefing_html.count('class="recent-card cms-article-card"') == 1
    assert "Showing 9–9 of 9" in briefing_html
    assert weekly_html.count('class="recent-card cms-article-card"') == 1
    assert "Showing 5–5 of 5" in weekly_html
    assert catalogs._page_number("100", 3) == 3
    assert catalogs._page_number("-1", 3) == 1
    assert catalogs._page_number("oops", 3) == 1


def test_empty_cms_still_renders_matching_sections():
    html = catalogs.inject_thinking_collections(landing(), ())
    assert "The Weekly AI archive begins with" in html
    assert "Executive AI Briefings will appear here" in html
    assert html.count('id="weekly-ai"') == 1
    assert html.count('id="thinking-briefings"') == 1


def test_existing_readership_ordering_controller_requires_unchanged_section_ids():
    client = (ROOT / "src" / "thinking_dynamic_order.py").read_text("utf-8")
    assert "'#weekly-ai'" in client
    assert "'#thinking-briefings'" in client
    assert "'#thinking-articles'" in client
    assert "kinds = ['weekly_ai', 'briefings', 'articles']" in client
    assert "counts.get(b)[metric] - counts.get(a)[metric]" in client


def test_catalogues_do_not_override_the_independent_briefings_library():
    from page_executive_briefings import executive_briefings

    assert callable(executive_briefings)
    source = (ROOT / "src" / "page_executive_briefings.py").read_text("utf-8")
    assert "def executive_briefings()" in source
    assert "briefings-library-card" in source


def test_previous_promo_visual_and_styles_are_not_reintroduced():
    template = (ROOT / "src" / "thinking_landing.py").read_text("utf-8")
    assert 'from briefings_visual import PROMO_CSS, briefing_visual' not in template
    assert '{briefing_visual()}' not in template
    assert 'class="thinking-briefing-card"' not in template
    updated = catalogs.inject_thinking_collections(landing(), ())
    assert 'class="thinking-briefing-card"' not in updated
    assert updated.count('id="thinking-briefings"') == 1
