"""Regression checks for the compact, decision-first briefing experience."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class ExecutiveBriefingReaderTests(unittest.TestCase):
    def test_modified_modules_are_syntactically_valid(self):
        for path in (
            "src/briefings_visual.py",
            "src/page_executive_briefings.py",
            "src/thinking_landing.py",
            "src/site_cms.py",
        ):
            with self.subTest(path=path):
                ast.parse(source(path), filename=path)

    def test_landing_uses_original_artwork_and_direct_cta(self):
        page = source("src/thinking_landing.py")
        self.assertIn("PROMO_CSS", page)
        self.assertIn("{briefing_visual()}", page)
        self.assertIn('data-analytics-section="thinking-executive-briefings"', page)
        self.assertIn('data-hq-event="thinking_briefings_contact"', page)

    def test_index_is_short_and_only_lists_published_work(self):
        page = source("src/page_executive_briefings.py")
        self.assertIn('BRIEFING_KIND = "Executive Briefing"', page)
        self.assertIn("published_briefings()", page)
        self.assertIn('data-analytics-section="briefings-capability-map"', page)
        self.assertIn("not a ladder", page)
        self.assertNotIn("Editorial direction", page)
        self.assertIn('data-hq-event="briefings_contact_open"', page)

    def test_reader_preserves_original_cms_content_but_keeps_it_optional(self):
        page = source("src/page_executive_briefings.py")
        cms = source("src/site_cms.py")
        self.assertIn('class="briefing-reader-detail"', page)
        self.assertIn("article.content_html", page)
        self.assertIn("{tags}{source}", page)
        self.assertIn('data-hq-event="briefing_reader_contact"', page)
        self.assertIn('if article.kind == "Executive Briefing":', cms)
        self.assertIn("executive_briefing_article(", cms)

    def test_graphic_has_accessible_label_and_no_external_dependencies(self):
        visual = source("src/briefings_visual.py")
        self.assertIn('role="img"', visual)
        self.assertIn("aria-label=", visual)
        self.assertIn("viewBox=", visual)
        self.assertIn("prefers-reduced-motion", visual)
        self.assertNotIn("<script", visual)


if __name__ == "__main__":
    unittest.main()
