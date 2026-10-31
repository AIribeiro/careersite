"""Regression checks for Executive AI Briefings public/content architecture."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def content(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class ExecutiveAiBriefingTests(unittest.TestCase):
    def test_public_route_and_navigation(self):
        main = content("main.py")
        nav = content("src/site_components.py")
        self.assertIn('"briefings": executive_briefings', main)
        self.assertIn('"briefings"', main)
        self.assertNotIn('link("briefings"', nav)
        self.assertIn('Route("/briefings", _briefings_share', content("app.py"))

    def test_series_is_visible_and_contextual(self):
        page = content("src/page_executive_briefings.py")
        self.assertIn("Executive AI Briefings", page)
        self.assertIn("published_briefings", page)
        self.assertIn('BRIEFING_KIND = "Executive Briefing"', page)
        self.assertIn("not a ladder", page)
        self.assertIn('href="?page=briefings"', content("src/thinking_landing.py"))
        self.assertIn("home_briefings_strip()", content("src/page_home.py"))

    def test_content_studio_and_article_return_path(self):
        self.assertIn('"Executive Briefing"', content("src/page_admin.py"))
        cms = content("src/site_cms.py")
        self.assertIn('article.kind != "Executive Briefing"', cms)
        self.assertIn('briefing_back_href = "?page=briefings"', cms)
        self.assertIn("executive-capability-grid", content("src/site_styles.py"))
        self.assertIn("def _render_executive_social_image", cms)

    def test_seven_question_visuals_and_article_route(self):
        visuals = content("src/executive_questions_visuals.py")
        cms = content("src/site_cms.py")
        self.assertIn('SLUG = "seven-questions-for-better-ai-decisions"', visuals)
        self.assertIn("aiq-flow-items", visuals)
        self.assertIn("aiq-cards", visuals)
        self.assertIn("aiq-cover-orbit", visuals)
        for icon in ("focus", "clarify", "test", "evidence", "cause", "effect", "act"):
            self.assertIn("aiq-icon-" + icon, visuals)
        self.assertIn("from executive_questions_visuals import cover", cms)
        self.assertIn("from executive_questions_visuals import QUESTIONS_STYLES", cms)
        self.assertIn("from executive_questions_visuals import social_image", cms)

    def test_seo_and_analytics_discovery(self):
        self.assertIn('"briefings": "Executive AI Briefings', content("src/site_meta.py"))
        page = content("src/page_executive_briefings.py")
        self.assertIn('data-analytics-section="briefings-capability-map"', page)
        self.assertIn('briefings_featured_open', page)
        self.assertIn('class="briefings-library-grid"', page)
        self.assertIn('def executive_briefing_page()', page)


if __name__ == "__main__":
    unittest.main()
