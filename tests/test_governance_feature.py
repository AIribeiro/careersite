"""Regression tests for the featured executive governance operating-model graphic."""
from __future__ import annotations

import unittest
from pathlib import Path

from governance_feature import GOVERNANCE_FEATURE


class GovernanceFeatureTests(unittest.TestCase):
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
        self.assertNotIn('<img ', html)
        self.assertNotIn('<img ', html)
        self.assertIn('data:image/svg+xml,', html)

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
        self.assertNotIn('<img ', html)

    def test_feature_is_in_the_center_of_governance_page(self):
        source = (Path(__file__).resolve().parents[1] / 'src' / 'page_ai_data_governance.py').read_text()
        self.assertIn('from governance_feature import GOVERNANCE_FEATURE', source)
        self.assertLess(source.index('Two disciplines, one operating conversation.'), source.index('{GOVERNANCE_FEATURE}'))
        self.assertLess(source.index('{GOVERNANCE_FEATURE}'), source.index('A lifecycle-based governance model.'))
        self.assertIn('href="#governance-operating-model"', source)


if __name__ == '__main__':
    unittest.main()
