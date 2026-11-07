"""Regression: one recognizable decision heading across historical and future briefings."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from briefing_editorial_labels import (  # noqa: E402
    LEADERSHIP_DECISION_LABEL,
    normalize_leadership_decision_label,
)
from briefing_infographic_engine import source_fingerprint  # noqa: E402


class LeadershipDecisionHeadingTests(unittest.TestCase):
    def test_legacy_labels_are_replaced_in_visible_heading_only(self):
        older = (
            '<span class="briefings-index">The executive judgment</span>'
            '<h2>The executive judgment: control the workflow, not just the model</h2>'
            '<span class="aiq-kicker">The executive premise</span>'
            '<p>The executive judgment can be challenged after new evidence.</p>'
        )
        updated = normalize_leadership_decision_label(older)
        self.assertEqual(updated.count(LEADERSHIP_DECISION_LABEL), 3)
        self.assertIn("The Leadership Decision: control the workflow", updated)
        self.assertIn("<p>The executive judgment can be challenged", updated)
        self.assertEqual(normalize_leadership_decision_label(updated), updated)

    def test_all_independent_reader_templates_use_the_standard(self):
        for filename in (
            "src/page_executive_briefings.py",
            "src/data_governance_funding_briefing.py",
            "src/data_vs_ai_governance_briefing.py",
            "src/seven_questions_guide.py",
        ):
            with self.subTest(filename=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(LEADERSHIP_DECISION_LABEL, source)
                self.assertNotIn('>The executive judgment</span>', source)
                self.assertNotIn('>The executive premise</span>', source)

    def test_legacy_cms_body_is_normalized_without_changing_fingerprint(self):
        article = SimpleNamespace(
            title="A previously published security briefing",
            subtitle="Immutable approved artwork edition",
            content_html=(
                "<h2>The executive judgment: control the workflow, not just the model</h2>"
                "<p>The article's evidence remains unmodified.</p>"
            ),
        )
        baseline = source_fingerprint(article)
        presented = normalize_leadership_decision_label(article.content_html)
        self.assertIn("The Leadership Decision: control the workflow", presented)
        self.assertEqual(source_fingerprint(article), baseline)
        self.assertIn("The executive judgment:", article.content_html)

    def test_every_executive_briefing_passes_through_the_cms_normalizer(self):
        cms = (ROOT / "src/site_cms.py").read_text(encoding="utf-8")
        start = cms.index('if article.kind == "Executive Briefing":', cms.index("def render_cms_article"))
        end = cms.index("return insert_related_navigation(reader, article, available)", start)
        passage = cms[start:end]
        self.assertIn("reader = executive_briefing_article(", passage)
        self.assertIn("reader = normalize_leadership_decision_label(reader)", passage)
        self.assertIn("insert_related_navigation", cms[end:end+150])

    def test_editorial_standard_is_permanent_and_retroactive(self):
        text = (ROOT / "docs/executive_briefings_editorial_standard.md").read_text(encoding="utf-8")
        self.assertIn("The Leadership Decision", text)
        self.assertIn("previously published editions", text)
        self.assertIn("fingerprints", text)


if __name__ == "__main__":
    unittest.main()
