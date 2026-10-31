"""Regression checks for independent, sanitizer-safe executive briefings."""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from page_executive_briefings import (  # noqa: E402
    FIRST_SLUG, executive_briefings, executive_briefing_article,
)
from briefings_visual import briefing_icon  # noqa: E402


def fake_article(slug: str, title: str):
    return SimpleNamespace(
        slug=slug, title=title, subtitle="A clear decision perspective",
        excerpt="A clear decision perspective", published_label="31 Oct 2026",
        read_minutes=7, kind="Executive Briefing",
        content_html="<h2>Published evidence</h2><p>Published full text, not a preview.</p>",
    )


class BriefingsNavigationContract(unittest.TestCase):
    def test_modules_compile(self):
        for name in ("page_executive_briefings.py", "briefings_visual.py", "site_cms.py"):
            path = SRC / name
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_icon_is_a_real_html_node_after_svg_sanitization(self):
        icon = briefing_icon("target")
        self.assertTrue(icon.startswith("<span"))
        self.assertIn('class="briefing-icon ', icon)
        self.assertNotIn("<svg", icon)
        self.assertNotIn("<img", icon)

    def test_library_contains_two_separate_clickable_cards_and_no_inline_article(self):
        articles = (
            fake_article(FIRST_SLUG, "AI capabilities"),
            fake_article("seven-questions-for-better-ai-decisions", "Seven questions"),
        )
        with (
            patch("page_executive_briefings.published_briefings", return_value=articles),
            patch("page_executive_briefings.nav", return_value=""),
            patch("page_executive_briefings.footer", return_value=""),
            patch("page_executive_briefings.article_relative_url",
                  side_effect=lambda a: f"?page=briefing&article={a.slug}"),
        ):
            page = executive_briefings()
        html = page.rsplit("</style>", 1)[-1]
        self.assertEqual(html.count('class="briefings-library-card"'), 2)
        self.assertIn("page=briefing&amp;article=", html)
        self.assertIn("AI capabilities", html)
        self.assertIn("Seven questions", html)
        self.assertNotIn('class="briefing-full-content"', html)
        self.assertNotIn('class="briefings-method"', html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<svg", html)

    def test_reader_shows_complete_cms_body_and_does_not_embed_broken_cover(self):
        article = fake_article(FIRST_SLUG, "AI capabilities")
        with (
            patch("page_executive_briefings.nav", return_value=""),
            patch("page_executive_briefings.footer", return_value=""),
            patch("page_executive_briefings.contact_block", return_value=""),
        ):
            page = executive_briefing_article(
                article, "7 min", '<img src="broken-external-cover.jpg">',
                "", "", "", "",
            )
        html = page.rsplit("</style>", 1)[-1]
        self.assertIn("Published full text, not a preview.", html)
        self.assertIn('data-analytics-section="briefings-capability-map"', html)
        self.assertIn("Discuss your decision", html)
        self.assertNotIn("broken-external-cover.jpg", html)
        self.assertNotIn("<details", html)

    def test_main_has_dedicated_route_and_cms_preserves_other_article_routes(self):
        main = (SRC.parent / "main.py").read_text(encoding="utf-8")
        cms = (SRC / "site_cms.py").read_text(encoding="utf-8")
        self.assertIn('"briefing": executive_briefing_page', main)
        self.assertIn('if PAGE in {"thinking", "briefing"}', main)
        self.assertIn('page = "briefing" if article.kind.strip().casefold()', cms)
        self.assertIn('else "thinking"', cms)


if __name__ == "__main__":
    unittest.main()
