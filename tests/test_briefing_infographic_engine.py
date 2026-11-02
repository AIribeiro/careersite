from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import patch

from briefing_infographic_engine import (
    PATTERNS, REVIEW_KEYS, generate_infographic_spec, infographic_html,
    render_svg, source_fingerprint, validate_spec,
)
from briefing_infographic_store import approved_infographic_for


def mock_article(slug="example", title="Executive AI Operating Model"):
    return SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        slug=slug, title=title,
        subtitle="A clear executive decision with evidence and accountable owners.",
        content_html="<h2>The business outcome</h2><p>Context and evidence.</p>"
                     "<h2>Decision rights</h2><p>Owner and next gate.</p>",
        kind="Executive Briefing",
    )


def spec(pattern="flow", count=4):
    return {
        "pattern":pattern,
        "title":"The evidence behind this business decision",
        "deck":"Every approved use needs ownership and a next review.",
        "items":[{
            "label":str(i+1).zfill(2),
            "title":f"Control boundary {i+1}",
            "detail": "Evidence of the operating consequence and accountable decision."
        } for i in range(count)],
        "conclusion":"Proceed only when credible evidence and authority support the change.",
    }


class InfographicEngineTests(unittest.TestCase):
    def test_six_visual_patterns_render_accessible_svg_and_mobile(self):
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern):
                sample=spec(pattern,count=7 if pattern in ("questions","layers") else 4)
                for mobile in (False,True):
                    svg=render_svg(sample,mobile=mobile)
                    root=ET.fromstring(svg)
                    self.assertTrue(root.tag.endswith("svg"))
                    labels=" ".join(root.itertext()).lower()
                    self.assertIn("evidence",labels)
                    self.assertIn("control boundary",labels)
                    self.assertIn("proceed only",labels)
                    self.assertNotIn("<script",svg)

    def test_mobile_embeds_both_variants_and_analytics_section(self):
        html=infographic_html(
            spec(), "This original executive diagram shows four controls and "
            "one business approval decision.", "Original executive graphic", "example"
        )
        self.assertIn('data-analytics-section="briefing-infographic"',html)
        self.assertIn('<picture',html)
        self.assertIn('media="(max-width: 700px)"',html)
        self.assertEqual(html.count("data:image/svg+xml;base64,"),2)
        self.assertIn("<figcaption>",html)

    def test_automatic_generation_uses_current_article_headings(self):
        s=generate_infographic_spec(mock_article())
        self.assertIn("business outcome",s["items"][0]["title"].lower())
        self.assertIn("Decision rights",s["items"][1]["title"])
        validate_spec(s)

    def test_invalid_specs_and_employer_mentions_are_rejected(self):
        bad=spec()
        bad["items"][0]["detail"]="At Volvo, the result improved."
        with self.assertRaises(ValueError):
            validate_spec(bad)
        with self.assertRaises(ValueError):
            validate_spec(spec("timeline",count=6))

    def test_stale_article_fingerprint_never_renders(self):
        article=mock_article()
        record={
            "status":"approved","spec":spec(),
            "alt_text":"Original executive graphic about the relevant ownership controls.",
            "caption":"Original visual",
            "source_fingerprint":source_fingerprint(article),
        }
        self.assertIn("<picture",approved_infographic_for(article,row=record))
        article.content_html+="<p>Changed after approval</p>"
        self.assertEqual(approved_infographic_for(article,row=record),"")

    def test_fingerprint_is_deterministic(self):
        article=mock_article()
        self.assertEqual(source_fingerprint(article),source_fingerprint(article))
        article.subtitle+=" edited"
        self.assertNotEqual(source_fingerprint(article),source_fingerprint(mock_article()))


if __name__ == "__main__":
    unittest.main()
