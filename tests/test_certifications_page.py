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
        self.assertEqual(len(FLAGSHIP), 10)
        self.assertEqual(len(titles), len(set(titles)))
        self.assertIn("Generative AI for Executives and Business Leaders Specialization", titles)
        self.assertIn("Responsible Generative AI", titles)
        self.assertIn("AI for Organizational Leaders", titles)
        self.assertIn("Agentic AI and AI Agents: A Primer for Leaders", titles)
        self.assertIn("Fundamentals of Building AI Agents", titles)
        self.assertNotIn("EITCA/AI Artificial Intelligence Academy", titles)
        self.assertIn("Azure Databricks Platform Architect · Academy Accreditation", titles)
        self.assertIn("Executive Data Science Specialization", titles)
        self.assertIn("Explainable AI (XAI)", titles)
        self.assertIn("Generative AI for Leaders", titles)
        self.assertIn("Generative AI for Product Managers", titles)
        self.assertTrue(all(str(item.get("verify_url", "")).startswith("https://") for item in FLAGSHIP))
        self.assertEqual(len(EITCA_COMPONENTS), 12)

    def test_credly_badges_are_curated_verifiable_and_use_original_artwork(self) -> None:
        from page_certifications import CREDLY_BADGES, CREDLY_PROFILE, certifications

        self.assertEqual(len(CREDLY_BADGES), 8)
        titles = [str(item["title"]) for item in CREDLY_BADGES]
        self.assertEqual(len(titles), len(set(titles)))
        self.assertIn("Fundamentals of Building AI Agents", titles)
        self.assertIn("AI Agents Using RAG and LangChain", titles)
        self.assertIn("Generative AI for Product Managers Specialization", titles)
        self.assertIn("Generative AI: Foundation Models and Platforms", titles)
        self.assertIn("Data Privacy Fundamentals", titles)
        self.assertIn("Enterprise Design Thinking Co-Creator", titles)
        self.assertIn("Microsoft Certified: Azure AI Fundamentals", titles)
        self.assertIn("Microsoft Certified: Azure Data Fundamentals", titles)
        self.assertTrue(all("/badges/" in str(item["url"]) for item in CREDLY_BADGES))
        self.assertEqual(CREDLY_PROFILE, "https://www.credly.com/users/jair-pinto-ribeiro/")

        badge_dir = ROOT / "images/credly"
        expected = {
            "fundamentals_ai_agents.png",
            "ai_agents_rag_langchain.png",
            "genai_product_managers.png",
            "genai_foundation_models.png",
            "data_privacy_fundamentals.png",
            "enterprise_design_thinking_cocreator.png",
            "azure_ai_fundamentals.png",
            "azure_data_fundamentals.png",
        }
        self.assertEqual({p.name for p in badge_dir.glob("*.png")}, expected)
        for path in badge_dir.glob("*.png"):
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.width, image.height)
                self.assertGreaterEqual(image.width, 352)
                image.verify()

        page = certifications()
        self.assertIn("Verified digital badges", page)
        self.assertIn("Specific capability evidence, independently verifiable.", page)
        self.assertIn("View full Credly profile", page)
        self.assertEqual(page.count("Verify on Credly ↗"), 8)
        self.assertGreaterEqual(page.count("digital badge"), 8)

    def test_page_preserves_senior_leadership_positioning_and_evidence(self) -> None:
        from page_certifications import certifications

        page = certifications()
        self.assertIn("What the credential record covers.", page)
        self.assertIn("Strategy &amp; value", page)
        self.assertIn("Adoption &amp; operating model", page)
        self.assertIn("24 ECTS", page)
        self.assertIn("12 component certifications", page)
        self.assertNotIn("Valid through Apr 2027", page)
        self.assertIn("Architecture-level judgment without engineering positioning", page)
        self.assertGreaterEqual(page.count("Verify credential ↗"), 11)
        self.assertIn("Ten credentials complement the featured EITCA/AI programme", page)
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
        self.assertIn("Scope and relevance", page)
        self.assertIn("EITCA/AI adds structured technical breadth", page)
        self.assertIn("The credential supports business-facing work", page)
        self.assertIn("eitca-value-grid", page)
        self.assertIn("View full LinkedIn credential record", page)
        self.assertIn("https://www.linkedin.com/in/jairribeiro/details/certifications/", page)
        self.assertNotIn("Top 10 Thought Leader", page)


if __name__ == "__main__":
    unittest.main()
