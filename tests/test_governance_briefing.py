"""Editorial and rendering regression checks for the governance briefing."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from page_executive_briefings import (
    GOVERNANCE_LAYERS,
    GOVERNANCE_RECORD_FIELDS,
    GOVERNANCE_SLUG,
    executive_briefing_article,
    governance_20_minute_review,
    governance_decision_map,
    governance_decision_record,
    governance_case_example,
    governance_visual_map,
)
from site_cms import CmsArticle


class GovernanceBriefingTests(unittest.TestCase):
    def test_seven_distinct_layers_with_questions_and_evidence(self):
        self.assertEqual(len(GOVERNANCE_LAYERS), 7)
        self.assertEqual(len({entry[0] for entry in GOVERNANCE_LAYERS}), 7)
        markup = governance_decision_map()
        self.assertEqual(markup.count('class="gov-seven-layer gov-seven-layer--'), 7)
        self.assertEqual(markup.count("<strong>Executive question</strong>"), 7)
        self.assertEqual(markup.count("<strong>Ask to see</strong>"), 7)
        self.assertEqual(markup.count('<div class="gov-seven-mode">'), 0)
        self.assertEqual(markup.count("One service workflow."), 0)
        example = governance_case_example()
        self.assertEqual(example.count('<div class="gov-seven-mode">'), 3)
        self.assertEqual(example.count("One service workflow."), 1)

    def test_full_resolution_vector_asset_and_accessible_caption(self):
        asset = Path(__file__).resolve().parents[1] / "static" / "ai-governance-executive-seven-layer-map.svg"
        self.assertTrue(asset.is_file())
        svg = asset.read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 1536 864"', svg)
        self.assertIn("Information integrity", svg)
        self.assertIn("Accountable ownership", svg)
        self.assertIn("Bounded AI action", svg)
        markup = governance_visual_map()
        # The SVG markup is self-contained. A separate /app/static SVG
        # request is forbidden: it caused a large broken-image placeholder.
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', markup)
        self.assertIn('viewBox="0 0 1536 864"', markup)
        self.assertNotIn('<img ', markup)
        self.assertNotIn('/app/static/', markup)
        self.assertEqual(markup.count('class="row-label"'), 7)
        self.assertIn("At-a-glance governance map.", markup)

    def test_missing_svg_displays_seven_readable_layers_without_blank_space(self):
        from unittest.mock import patch
        with patch("page_executive_briefings._embedded_governance_svg", return_value=""):
            markup = governance_visual_map()
        self.assertIn("gov-visual-fallback", markup)
        self.assertNotIn("<svg ", markup)
        self.assertNotIn("<img ", markup)
        for _number, title, *_rest in GOVERNANCE_LAYERS:
            self.assertIn(title, markup)

    def test_record_has_six_fields_and_decision_gates(self):
        self.assertEqual(len(GOVERNANCE_RECORD_FIELDS), 6)
        markup = governance_decision_record()
        self.assertEqual(markup.count('class="gov-record-field"'), 6)
        for label in ("Business outcome", "Accountable owner", "AI authority",
                      "Risk and controls", "Evidence of readiness",
                      "Decision and next review"):
            self.assertIn(label, markup)
        for label in ("Proceed", "Hold", "Stop"):
            self.assertIn(f"<strong>{label}</strong>", markup)

    def test_short_review_has_four_explicit_timeboxes(self):
        markup = governance_20_minute_review()
        for window in ("0–5 min", "5–10 min", "10–15 min", "15–20 min"):
            self.assertIn(window, markup)
        self.assertEqual(markup.count("<li><b>"), 4)

    def test_published_governance_page_avoids_second_full_article(self):
        article = CmsArticle(
            title="AI Governance Explained to Executives",
            subtitle="Seven governance layers and one decision record.",
            slug=GOVERNANCE_SLUG,
            kind="Executive Briefing",
            status="published",
            content_html="<p>Supporting sources, not a repeated seven-layer list.</p>",
        )
        markup = executive_briefing_article(
            article=article, read_metadata="4 min read", image="",
            tags="", source="", share_footer="<p>Share this briefing</p>",
            cms_css="<style></style>",
        )
        self.assertIn('class="briefing-reader governance-reader"', markup)
        self.assertEqual(markup.count('class="gov-seven-layer gov-seven-layer--'), 7)
        self.assertEqual(markup.count('class="gov-record-field"'), 6)
        self.assertEqual(markup.count("One service workflow."), 1)
        self.assertEqual(markup.count('<figure class="gov-visual"'), 1)
        self.assertEqual(markup.count('<div class="gov-seven-mode">'), 3)
        self.assertIn("Explore the seven executive questions and evidence to request", markup)
        self.assertIn("A 20-minute governance review.", markup)
        self.assertIn("Application notes and source references", markup)
        self.assertIn("<p>Supporting sources, not a repeated seven-layer list.</p>", markup)
        self.assertEqual(markup.count('data-hq-event="briefing_reader_contact"'), 1)
        self.assertNotIn("Read the full reasoning, application example", markup)
        self.assertNotIn('class="briefing-full-content"', markup)

    def test_other_briefing_keeps_the_existing_reader(self):
        article = CmsArticle(
            title="Choosing AI Capabilities",
            subtitle="Executive guide",
            slug="ai-capabilities-executive-decisions",
            kind="Executive Briefing",
            status="published",
            content_html="<p>Body</p>",
        )
        markup = executive_briefing_article(
            article=article, read_metadata="4 min read", image="",
            tags="", source="", share_footer="", cms_css="",
        )
        self.assertNotIn('class="briefing-reader governance-reader"', markup)
        self.assertIn('class="briefing-full-content"', markup)


if __name__ == "__main__":
    unittest.main()
