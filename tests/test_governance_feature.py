"""Regression tests for the featured executive governance operating-model graphic."""
from __future__ import annotations

import unittest
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree
import re

from governance_feature import GOVERNANCE_FEATURE


class GovernanceFeatureTests(unittest.TestCase):
    def test_print_download_is_canonical_static_asset(self):
        from pypdf import PdfReader
        from PIL import Image
        root = Path(__file__).resolve().parents[1]
        pdf = root / "static" / "ai-data-governance-framework-a4.pdf"
        portrait = root / "static" / "governance-avatar.webp"
        self.assertTrue(pdf.is_file())
        self.assertTrue(portrait.is_file())
        reader = PdfReader(str(pdf), strict=True)
        self.assertEqual(len(reader.pages), 1)
        page = reader.pages[0]
        self.assertAlmostEqual(float(page.mediabox.width), 595.276, delta=1.0)
        self.assertAlmostEqual(float(page.mediabox.height), 841.890, delta=1.0)
        with Image.open(portrait) as picture:
            self.assertEqual(picture.size, (320, 320))
            self.assertEqual(picture.format, "WEBP")
        html = GOVERNANCE_FEATURE
        self.assertIn('class="gf-download-cta"', html)
        self.assertIn('href="app/static/ai-data-governance-framework-a4.pdf"', html)
        self.assertIn('download="Jair_Ribeiro_AI_Data_Governance_Framework_A4.pdf"', html)


    def test_source_faithful_decision_structure(self):
        html = GOVERNANCE_FEATURE
        self.assertIn('id="governance-operating-model"', html)
        self.assertEqual(html.count('class="node"'), 6)
        for step in ('Frame', 'Classify', 'Assign', 'Evidence', 'Decide', 'Monitor'):
            self.assertIn(f'<b>{step}</b>', html)
        self.assertEqual(html.count('<i aria-hidden="true">'), 7)
        for signal in ('KNOW', 'OWN', 'EXPLAIN', 'RESPOND'):
            self.assertIn(f'<strong>{signal}</strong>', html)

    def test_exact_framework_vocabulary_and_accountability(self):
        html = GOVERNANCE_FEATURE
        # The framework belongs to the source page: no generic substitutions.
        principles = ("Boundaries", "Accountability", "Evidence", "Traceability")
        mechanisms = (
            "Trusted inputs",
            "Decision ownership",
            "Control by consequence",
            "Traceable outcomes",
            "Monitoring after launch",
            "Material-change review",
        )
        accountabilities = (
            "Business owner",
            "Data owner / steward",
            "Product / technology owner",
            "Appropriate risk authority",
            "Portfolio / governance authority",
            "Named operating owner",
        )
        questions = ("Purpose", "Data", "Accountability", "Boundaries",
                     "Evidence", "Traceability", "Monitoring")
        for label in principles + mechanisms + accountabilities + questions:
            self.assertIn(f"<strong>{label}</strong>", html)
        self.assertIn("Four decision tests", html)
        self.assertIn("Six decision accountabilities", html)
        self.assertIn("ACCOUNTABILITY BY DESIGN", html)
        self.assertIn("Continue · constrain · stop", html)
        self.assertIn("where is human judgment required?", html)
        self.assertNotIn("Executive Sponsor", html)
        self.assertNotIn("Policies & Standards", html)

    def test_semantic_icons_preserve_factual_text_and_mobile_layout(self):
        html = GOVERNANCE_FEATURE
        self.assertEqual(html.count('class="gf-icon gf-icon-principle"'), 4)
        self.assertEqual(html.count('class="gf-icon gf-icon-mechanism"'), 6)
        self.assertEqual(html.count('class="gf-icon gf-icon-signal"'), 4)
        self.assertEqual(html.count('class="gf-icon gf-icon-core"'), 1)
        self.assertEqual(html.count('class="gf-mechanism"'), 6)
        self.assertEqual(html.count('class="gf-signal"'), 4)
        self.assertNotIn("<svg ", html)
        self.assertNotIn("</svg>", html)
        body = html.split('</style>', 1)[1]
        self.assertEqual(body.count('data-glyph="'), 15)
        self.assertEqual(html.count('background-image:url("data:image/svg+xml,'), 18)
        self.assertIn('padding-top:139px', html)
        self.assertIn('height:132px', html)
        self.assertNotIn('class="step"', html)
        self.assertEqual(html.count('<img '), 1)
        self.assertIn('src="app/static/governance-avatar.webp"', html)
        self.assertEqual(html.count('<img '), 1)
        self.assertIn('src="app/static/governance-avatar.webp"', html)
        self.assertIn('data:image/svg+xml,', html)

    def test_css_icon_assets_are_real_parseable_svg_images(self):
        # Native SVG tags disappear inside st.html; only CSS image URLs
        # are allowed in this feature. Validate every embedded glyph.
        images = re.findall(
            r'background-image:url\("data:image/svg\+xml,([^"]+)"\)',
            GOVERNANCE_FEATURE,
        )
        self.assertEqual(len(images), 18)
        svg_ns = "{http://www.w3.org/2000/svg}"
        for encoded in images:
            document = unquote(encoded)
            root = ElementTree.fromstring(document)
            self.assertEqual(root.tag, svg_ns + "svg")
            self.assertTrue(
                any(node.tag in (svg_ns + "path", svg_ns + "circle", svg_ns + "ellipse")
                    for node in root.iter()),
                "An icon must contain visible vector geometry",
            )
            self.assertNotIn('stroke="currentColor"', document)

    def test_premium_hierarchy_and_semantic_structure(self):
        html = GOVERNANCE_FEATURE
        self.assertIn('class="foundation-head"', html)
        self.assertEqual(html.count('class="foundation-symbol"'), 2)
        self.assertIn('class="core"', html)
        self.assertIn('class="principle-note"', html)
        self.assertIn('class="signals"', html)
        self.assertIn('class="takeaway"', html)
        self.assertIn('max-width:630px', html)
        self.assertIn('grid-template-columns:1fr 1fr', html)
        self.assertIn('max-width:480px', html)
        self.assertIn('data:image/svg+xml,', html)
        self.assertNotIn('http://', html)

    def test_fast_responsive_and_no_conflicting_arrow_classes(self):
        html = GOVERNANCE_FEATURE
        self.assertIn('@media(max-width:480px)', html)
        self.assertIn('@media(max-width:740px)', html)
        self.assertIn('content-visibility:auto', html)
        self.assertNotIn('class="step"', html)  # Global site .step:after draws a foreign arrow.
        self.assertIn('data:image/svg+xml,', html)
        self.assertNotIn('<script', html)
        self.assertEqual(html.count('<img '), 1)
        self.assertIn('src="app/static/governance-avatar.webp"', html)

    def test_complete_infographic_is_the_first_section_beneath_navigation(self):
        source = (Path(__file__).resolve().parents[1] / 'src' / 'page_ai_data_governance.py').read_text()
        self.assertIn('from governance_feature import GOVERNANCE_FEATURE', source)
        self.assertEqual(source.count('{GOVERNANCE_FEATURE}'), 1)
        self.assertIn("<main>\n{GOVERNANCE_FEATURE}", source)
        self.assertLess(source.index('{GOVERNANCE_FEATURE}'), source.index('<section class="pagehero">'))
        self.assertLess(source.index('<section class="pagehero">'), source.index('id="governance-evidence"'))
        self.assertIn('href="#governance-operating-model"', source)
        self.assertIn('Back to the operating model ↑', source)


if __name__ == '__main__':
    unittest.main()
