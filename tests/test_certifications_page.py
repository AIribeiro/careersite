from __future__ import annotations

from pathlib import Path
from PIL import Image
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class CertificationsPageTests(unittest.TestCase):
    def test_certifications_route_and_about_navigation(self) -> None:
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        about = (ROOT / "src/page_about.py").read_text(encoding="utf-8")

        self.assertIn('"certifications"', main)
        self.assertIn("from page_certifications import certifications", main)
        self.assertIn("?page=certifications", about)

        from site_components import ABOUT_PAGES, nav

        self.assertEqual(ABOUT_PAGES["certifications"], "Credentials & Certifications")
        menu = nav("certifications")
        self.assertIn("Credentials &amp; Certifications", menu)
        self.assertIn('summary class="link on"', menu)

    def test_flagship_credentials_are_curated_unique_and_verifiable(self) -> None:
        from page_certifications import FLAGSHIP, EITCA_COMPONENTS

        titles = [str(item["title"]) for item in FLAGSHIP]
        self.assertEqual(len(FLAGSHIP), 6)
        self.assertEqual(len(titles), len(set(titles)))
        self.assertIn("Generative AI for Executives and Business Leaders Specialization", titles)
        self.assertIn("Responsible Generative AI", titles)
        self.assertIn("AI for Organizational Leaders", titles)
        self.assertIn("Agentic AI and AI Agents: A Primer for Leaders", titles)
        self.assertIn("Fundamentals of Building AI Agents", titles)
        self.assertNotIn("EITCA/AI Artificial Intelligence Academy", titles)
        self.assertIn("Azure Databricks Platform Architect · Academy Accreditation", titles)
        self.assertNotIn("Executive Data Science Specialization", titles)
        self.assertNotIn("Explainable AI (XAI)", titles)
        self.assertTrue(all(str(item.get("verify_url", "")).startswith("https://") for item in FLAGSHIP))
        self.assertEqual(len(EITCA_COMPONENTS), 12)

    def test_page_preserves_senior_leadership_positioning_and_evidence(self) -> None:
        from page_certifications import certifications

        page = certifications()
        self.assertIn("Where the credential record adds depth.", page)
        self.assertIn("Strategy &amp; value", page)
        self.assertIn("Adoption &amp; operating model", page)
        self.assertIn("24 ECTS", page)
        self.assertIn("12 component certifications", page)
        self.assertNotIn("Valid through Apr 2027", page)
        self.assertIn("Architecture-level judgment without engineering positioning", page)
        self.assertGreaterEqual(page.count("Verify credential ↗"), 7)
        self.assertIn("EITCA/AI/SLJ25004525", page)
        self.assertIn("European Union flags outside a modern institutional building", page)
        self.assertIn("eu-round-emblem", page)
        self.assertIn("European credential context", page)
        banner = ROOT / "images/eitca_eu_banner.webp"
        self.assertTrue(banner.exists())
        with Image.open(banner) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (1280, 720))
            image.verify()
        from site_media import eitca_eu_banner
        self.assertTrue(eitca_eu_banner.startswith("data:image/webp;base64,"))
        self.assertIn("What this adds to my leadership", page)
        self.assertIn("For me, the value of EITCA/AI", page)
        self.assertIn("That depth strengthens the bridge I need to lead effectively", page)
        self.assertIn("eitca-value-grid", page)
        self.assertIn("View full LinkedIn credential record", page)
        self.assertIn("https://www.linkedin.com/in/jairribeiro/details/certifications/", page)
        self.assertNotIn("Top 10 Thought Leader", page)


if __name__ == "__main__":
    unittest.main()
