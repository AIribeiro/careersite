"""Structure, substance and tablet-readability contract for the seven-question guide."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import ast
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from seven_questions_guide import LENSES, SEVEN_QUESTIONS_CSS, seven_questions_body


class GuideParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.hrefs = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if "href" in attrs:
            self.hrefs.append(attrs["href"])


class SevenQuestionsGuideTests(unittest.TestCase):
    def test_python_modules_parse(self):
        for name in ("src/seven_questions_guide.py", "src/page_executive_briefings.py"):
            with self.subTest(module=name):
                ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)

    def test_original_seven_question_categories_are_restored(self):
        self.assertEqual(
            [lens["name"] for lens in LENSES],
            ["Go / No Go", "Clarify Meaning", "Challenge Assumptions",
             "Critical Check", "Explore Causes", "Consider Effects", "Drive to Action"],
        )

    def test_each_lens_gives_a_real_decision_instrument(self):
        for lens in LENSES:
            with self.subTest(lens=lens["name"]):
                self.assertEqual(len(lens["core"]), 3)
                for key in ("power", "request", "warning", "gate"):
                    self.assertGreater(len(lens[key]), 45)
        html = seven_questions_body()
        self.assertEqual(html.count('class="aiq-lens"'), 7)
        self.assertEqual(html.count("Core questions · ask the team"), 7)
        self.assertEqual(html.count("Power prompt · challenge the room"), 7)
        self.assertIn("A 15-minute executive decision review", html)
        self.assertIn("service-case triage", html)
        self.assertIn("Vervago", html)

    def test_navigation_has_seven_working_targets(self):
        parser = GuideParser()
        parser.feed(seven_questions_body())
        for index in range(1, 8):
            self.assertIn(f"aiq-lens-{index}", parser.ids)
            self.assertIn(f"#aiq-lens-{index}", parser.hrefs)
        self.assertEqual(parser.tags.count("nav"), 1)

    def test_responsive_layout_does_not_force_a_narrow_table(self):
        self.assertIn("@media(max-width:780px)", SEVEN_QUESTIONS_CSS)
        self.assertIn(".aiq-lens-body{grid-template-columns:minmax(0,1fr)}", SEVEN_QUESTIONS_CSS)
        self.assertIn(".aiq-gates{grid-template-columns:minmax(0,1fr)}", SEVEN_QUESTIONS_CSS)
        self.assertIn("@media(max-width:520px)", SEVEN_QUESTIONS_CSS)
        self.assertNotIn("white-space:nowrap", SEVEN_QUESTIONS_CSS)
        page = (ROOT / "src/page_executive_briefings.py").read_text(encoding="utf-8")
        self.assertIn("seven_questions_body()", page)
        self.assertIn('main class="briefing-reader aiq-guide-reader"', page)
        self.assertIn("article.content_html", page)
        self.assertIn("briefing-reader-detail", page)


if __name__ == "__main__":
    unittest.main()
