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

    def test_fast_responsive_and_no_conflicting_arrow_classes(self):
        html = GOVERNANCE_FEATURE
        self.assertIn('@media(max-width:480px)', html)
        self.assertIn('@media(max-width:740px)', html)
        self.assertIn('content-visibility:auto', html)
        self.assertNotIn('class="step"', html)  # Global site .step:after draws a foreign arrow.
        self.assertNotIn('data:image/', html)
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
