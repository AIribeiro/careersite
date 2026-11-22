"""Evidence-first public-copy contracts without tying copy to a frozen layout."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class PublicCopyGuardTests(unittest.TestCase):
    def test_public_pages_do_not_use_self_promotional_claims(self):
        paths = (
            "src/page_home.py", "src/page_about.py", "src/page_impact.py",
            "src/page_ai_data_governance.py", "src/page_thinking.py",
            "src/thinking_landing.py", "src/page_presence.py",
            "src/page_certifications.py", "src/page_contact.py",
            "src/site_lenses.py", "src/site_components.py",
            "src/site_artifacts.py", "src/site_meta.py",
            "src/portfolio_operating_evidence.py",
        )
        combined = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in paths)
        for forbidden in (
            "Speaking & Thought Leadership",
            "Leadership Impact", "Role lenses",
            "Discuss a leadership opportunity",
            "my strongest fit", "My strongest fit",
            "my strongest contribution", "My strongest contribution",
            "The articles are not the point. The decisions behind them are.",
            "How I lead AI and data when strategy meets enterprise reality.",
            "Current leadership questions",
            "AI CAN DO A LOT.", "PEOPLE MAKE IT MATTER.",
            "I make complexity understandable", "I make disagreement useful",
            "Where I create the most value.",
            "The leadership problems I tend to work around.",
            "I am not interested in publishing for volume.",
            "If it does not change the conversation, it is mostly content.",
            "The value I try to add is not technical demonstration.",
            "I treat recognition as external validation of the work, not as a professional title.",
        ):
            self.assertNotIn(forbidden, combined)

    def test_featured_work_explicitly_bounded(self):
        from page_home import home
        from page_impact import impact
        from page_about import about
        from portfolio_operating_evidence import home_evidence, impact_evidence
        h, i, a = home(), impact(), about()
        evidence = impact_evidence()
        self.assertIn("20+ years", h)
        self.assertIn("Customer Interview Analyzer", h)
        self.assertIn("80+ AI opportunities", h)
        self.assertIn("working multilingual GenAI prototype", h)
        self.assertIn("did not proceed to a production rollout", i)
        self.assertIn("working GenAI prototype", evidence)
        self.assertIn("100+ AI learning sessions", evidence)
        self.assertIn("80+ AI opportunities", evidence)
        self.assertIn("2026–2027", i)
        self.assertIn("2025–2026", a)
        self.assertIn("LinkedIn profile", i)
        self.assertNotIn("1,500+ practitioners", h)
        self.assertNotIn("130,000+ interactions", h)
        self.assertNotIn("verified ROI", h)
        self.assertNotIn("100+ production deployments", i)
        self.assertLess(h.index("leadership-in-practice"), h.index("home-whats-new") if "home-whats-new" in h else len(h))
        self.assertEqual(home_evidence().count('class="card"'), 4)

    def test_governance_separates_operating_evidence_from_research(self):
        from page_ai_data_governance import ai_data_governance
        page = ai_data_governance()
        self.assertIn("Four observable signals", page)
        self.assertIn("See the evidence →", page)
        self.assertIn("Governance deliverables, not just principles.", page)
        self.assertIn("Research &amp; published perspective", page)
        self.assertLess(page.index('id="governance-evidence"'),
                        page.index("Research &amp; published perspective"))
        self.assertIn('href="?page=impact#operating-evidence"', page)


if __name__ == "__main__":
    unittest.main()
