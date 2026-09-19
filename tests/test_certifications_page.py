from __future__ import annotations

from pathlib import Path
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

    def test_flagship_credentials_are_curated_and_unique(self) -> None:
        from page_certifications import FLAGSHIP, EITCA_COMPONENTS

        titles = [str(item["title"]) for item in FLAGSHIP]
        self.assertEqual(len(FLAGSHIP), 8)
        self.assertEqual(len(titles), len(set(titles)))
        self.assertIn("Fundamentals of Building AI Agents", titles)
        self.assertIn("Generative AI for Executives and Business Leaders Specialization", titles)
        self.assertIn("Responsible Generative AI", titles)
        self.assertIn("Explainable AI (XAI)", titles)
        self.assertIn("EITCA/AI Artificial Intelligence Academy", titles)
        self.assertIn("Azure Databricks Platform Architect · Academy Accreditation", titles)
        self.assertEqual(len(EITCA_COMPONENTS), 12)

    def test_page_preserves_senior_leadership_positioning(self) -> None:
        from page_certifications import certifications

        page = certifications()
        self.assertIn("Four dimensions that matter in senior AI &amp; Data roles.", page)
        self.assertIn("24 ECTS across 12 component certifications", page)
        self.assertIn("not to replace specialist engineering ownership", page)
        self.assertIn("View full LinkedIn credential record", page)
        self.assertIn("https://www.linkedin.com/in/jairribeiro/details/certifications/", page)
        self.assertNotIn("Top 10 Thought Leader", page)


if __name__ == "__main__":
    unittest.main()
