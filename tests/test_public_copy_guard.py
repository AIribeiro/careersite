from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class PublicCopyGuardTests(unittest.TestCase):
    def test_public_pages_use_evidence_first_language(self) -> None:
        paths = (
            "src/page_home.py",
            "src/page_about.py",
            "src/page_impact.py",
            "src/page_ai_data_governance.py",
            "src/page_thinking.py",
            "src/thinking_landing.py",
            "src/page_presence.py",
            "src/page_certifications.py",
            "src/page_contact.py",
            "src/site_lenses.py",
            "src/site_components.py",
            "src/site_artifacts.py",
            "src/site_meta.py",
        )
        pages = {path: (ROOT / path).read_text(encoding="utf-8") for path in paths}
        public_copy = "\n".join(pages.values())

        # Avoid meta-language that repeatedly tells the reader how senior,
        # thoughtful or hireable the portfolio is. Evidence should carry that.
        forbidden = (
            "Speaking & Thought Leadership",
            "Leadership Impact",
            "Role lenses",
            "Discuss a leadership opportunity",
            "my strongest fit",
            "My strongest fit",
            "my strongest contribution",
            "My strongest contribution",
            "The articles are not the point. The decisions behind them are.",
            "How I lead AI and data when strategy meets enterprise reality.",
            "Current leadership questions",
            "AI CAN DO A LOT.",
            "PEOPLE MAKE IT MATTER.",
            "I make complexity understandable",
            "I make disagreement useful",
            "Where I create the most value.",
            "The leadership problems I tend to work around.",
            "I am not interested in publishing for volume.",
            "If it does not change the conversation, it is mostly content.",
            "The value I try to add is not technical demonstration.",
            "I treat recognition as external validation of the work, not as a professional title.",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, public_copy)

        home = pages["src/page_home.py"]
        about = pages["src/page_about.py"]
        impact = pages["src/page_impact.py"]
        thinking = pages["src/page_thinking.py"]
        thinking_landing = pages["src/thinking_landing.py"]
        presence = pages["src/page_presence.py"]
        certifications = pages["src/page_certifications.py"]
        contact = pages["src/page_contact.py"]
        lenses = pages["src/site_lenses.py"]
        components = pages["src/site_components.py"]
        governance = pages["src/page_ai_data_governance.py"]

        # New Swedish-market editorial framing: topic/evidence first.
        self.assertIn("Selected Experience", components)
        self.assertIn("Experience by mandate", components)
        self.assertIn("Speaking & Publications", components)
        self.assertIn("Selected experience →", home)
        self.assertIn("Adoption in practice", home)
        self.assertIn("Comments from people I worked with.", home)
        self.assertIn("Working across business, AI and technology.", about)
        self.assertIn("Separate facts, assumptions and open questions", about)
        self.assertIn("Decision / contribution", impact)
        self.assertIn("Notes on enterprise AI decisions, operating models, adoption and value.", thinking_landing)
        self.assertIn("Each piece starts from a concrete operating decision.", thinking)
        self.assertIn("Speaking &amp; Publications", presence)
        self.assertIn("Selected AI, data and leadership credentials.", certifications)
        self.assertIn("Discuss the mandate.", contact)
        self.assertIn("Experience spans enterprise AI, Data &amp; Analytics", lenses)
        self.assertIn("AI &amp; Data Governance · Operating perspective", governance)
        self.assertIn("Four observable signals", governance)

        # Preserve concrete evidence and scope. Canonical facts may now be
        # interpolated from career_facts.py, so validate the rendered pages.
        from page_about import about as render_about
        from page_home import home as render_home
        from page_impact import impact as render_impact

        home_html = render_home()
        about_html = render_about()
        impact_html = render_impact()

        self.assertIn("20+ years", home_html)
        self.assertIn("AI solutions and agents introduced across warranty, sales and aftermarket", home_html)
        self.assertIn("PoC → repeatable capability", home_html)
        self.assertIn("100+ AI initiatives, PoCs and projects", impact_html)
        self.assertIn("reporting directly to the Chief Data &amp; Analytics Officer", impact_html)
        self.assertIn("Enterprise CoE mandate across strategy, operations, technology and business leaders", impact_html)
        self.assertIn("2026–2027 maturity roadmap", impact_html)
        self.assertIn("2026–2027 maturity roadmap", about_html)
        self.assertIn("Global Thought Leaders &amp; Influencers on Emerging Technology, 2023.", about_html)
        self.assertIn("Where the business-translation thread started.", impact_html)
        self.assertIn("legal, compliance and sustainability", impact_html)

        # Adoption evidence should stay operational rather than vanity-metric led.
        self.assertNotIn("1,500+ practitioners", home_html)
        self.assertNotIn("130,000+ interactions", home_html)
        self.assertNotIn("100+ AI sessions", impact_html)
        self.assertNotIn("1,000+ employees", impact_html)


if __name__ == "__main__":
    unittest.main()
