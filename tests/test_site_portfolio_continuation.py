"""Smoke tests for the public-page navigation injection that previously crashed.

The deployed Streamlit render path passes a page name into this helper. Keep
its call compatible with the page-aware navigation renderer and idempotent.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_portfolio_continuation import inject_portfolio_continuation
from about_next_navigation import portfolio_next_navigation


BASE_DOCUMENT = '<nav class="nav"></nav><main><section>Page content</section></main><footer></footer>'
CORE = ("impact", "ai-data-governance", "thinking", "contact")


def test_each_core_page_renders_navigation_without_type_error():
    for page in CORE:
        result = inject_portfolio_continuation(BASE_DOCUMENT, page)
        assert result.count(f'data-analytics-section="{page}-next-destinations"') == 1
        assert result.count('class="about-next portfolio-next"') == 1
        assert result.index('class="about-next portfolio-next"') < result.index("</main>")
        assert result.index("</main>") < result.index("<footer")
        assert result.count('class="about-next-card"') == 3


def test_preexisting_navigation_is_not_duplicated():
    for page in CORE:
        original = BASE_DOCUMENT.replace("</main>", portfolio_next_navigation(page) + "</main>")
        assert inject_portfolio_continuation(original, page) == original
        assert inject_portfolio_continuation(original, page).count("about-next-grid") == 1


def test_injection_is_idempotent():
    for page in CORE:
        first = inject_portfolio_continuation(BASE_DOCUMENT, page)
        second = inject_portfolio_continuation(first, page)
        assert first == second


def test_article_archive_and_unrelated_pages_are_not_modified():
    assert inject_portfolio_continuation(BASE_DOCUMENT, "thinking", article_slug="sample-article") == BASE_DOCUMENT
    assert inject_portfolio_continuation(BASE_DOCUMENT, "thinking", weekly_archive=True) == BASE_DOCUMENT
    for page in ("home", "about", "briefings", "briefing", "analytics"):
        assert inject_portfolio_continuation(BASE_DOCUMENT, page) == BASE_DOCUMENT
    assert inject_portfolio_continuation("no main", "ai-data-governance") == "no main"


def test_public_render_uses_the_injector_and_the_correct_page_aware_api():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    module = (ROOT / "src" / "site_portfolio_continuation.py").read_text(encoding="utf-8")
    assert "raw_document = inject_portfolio_continuation(" in main
    assert "from about_next_navigation import portfolio_next_navigation" in module
    assert "portfolio_next_navigation(page)" in module
    assert "about_next_navigation(page)" not in module
