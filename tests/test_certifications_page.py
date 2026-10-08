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
        self.assertIn("Microsoft Leadership and Innovation Professional Certificate", titles)
        self.assertNotIn("Executive Data Science Specialization", titles)
        self.assertIn("Explainable AI (XAI)", titles)
        self.assertIn("Generative AI for Leaders", titles)
        self.assertIn("Generative AI for Product Managers", titles)
        latest = next(item for item in FLAGSHIP if item["title"] == "Microsoft Leadership and Innovation Professional Certificate")
        self.assertEqual(latest["issuer"], "Microsoft")
        self.assertEqual(latest["date"], "Oct 2026")
        self.assertEqual(latest["credential"], "49J7ASIMWWFA")
        self.assertEqual(latest["verify_url"], "https://www.coursera.org/account/accomplishments/professional-cert/49J7ASIMWWFA")
        self.assertEqual(latest["alternate_verify_url"], "https://www.coursera.org/account/accomplishments/specialization/49J7ASIMWWFA")
        self.assertEqual(latest["program_url"], "https://www.coursera.org/professional-certificates/microsoft-leadership-and-innovation")
        self.assertTrue(latest["featured"])
        self.assertEqual(sum(bool(item.get("featured")) for item in FLAGSHIP), 1)
        self.assertTrue(all(str(item.get("verify_url", "")).startswith("https://") for item in FLAGSHIP))
        self.assertEqual(len(EITCA_COMPONENTS), 12)

    def test_credly_badges_are_curated_verifiable_and_use_original_artwork(self) -> None:
        from page_certifications import ACCREDIBLE_BADGES, ACCREDIBLE_WALLET, CREDLY_BADGES, CREDLY_PROFILE, certifications

        self.assertEqual(len(CREDLY_BADGES), 8)
        titles = [str(item["title"]) for item in CREDLY_BADGES]
        self.assertEqual(len(titles), len(set(titles)))
        self.assertIn("Cognitive Practitioner", titles)
        self.assertNotIn("Fundamentals of Building AI Agents", titles)
        self.assertIn("AI Agents Using RAG and LangChain", titles)
        self.assertIn("Generative AI for Product Managers Specialization", titles)
        self.assertIn("Generative AI: Foundation Models and Platforms", titles)
        self.assertIn("Data Privacy Fundamentals", titles)
        self.assertIn("Enterprise Design Thinking Co-Creator", titles)
        self.assertIn("Microsoft Certified: Azure AI Fundamentals", titles)
        self.assertIn("Microsoft Certified: Azure Data Fundamentals", titles)
        self.assertTrue(all("/badges/" in str(item["url"]) for item in CREDLY_BADGES))
        self.assertEqual(CREDLY_PROFILE, "https://www.credly.com/users/jair-pinto-ribeiro/")
        self.assertEqual(ACCREDIBLE_WALLET, "https://www.credential.net/profile/jairribeiro188506/wallet")
        self.assertEqual(len(ACCREDIBLE_BADGES), 1)
        self.assertEqual(ACCREDIBLE_BADGES[0]["title"], "Academy Accreditation - Generative AI Fundamentals")
        self.assertIn("debbdbb9-df3f-46d8-a218-4f5f73288dae", ACCREDIBLE_BADGES[0]["url"])

        badge_dir = ROOT / "images/credly"
        expected = {
            "cognitive_practitioner.png",
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

        accredible_artwork = ROOT / "images/credentials/databricks_genai_fundamentals.png"
        self.assertTrue(accredible_artwork.exists())
        with Image.open(accredible_artwork) as image:
            self.assertEqual(image.format, "PNG")
            self.assertGreaterEqual(image.width, 300)
            self.assertGreaterEqual(image.height, 300)
            image.verify()

        page = certifications()
        self.assertIn("Verified digital badges", page)
        self.assertIn("Specific capability evidence, independently verifiable.", page)
        self.assertIn("Credly profile ↗", page)
        self.assertIn("Accredible wallet ↗", page)
        self.assertEqual(page.count("Verify on Credly ↗"), 8)
        self.assertEqual(page.count("Verify on Accredible ↗"), 1)
        self.assertIn("Academy Accreditation - Generative AI Fundamentals", page)
        self.assertGreaterEqual(page.count("digital badge"), 9)

    def test_openai_academy_badge_is_highlighted_and_verifiable(self) -> None:
        from page_certifications import OPENAI_AI_LEADERSHIP_URL, certifications
        from site_media import openai_ai_leadership

        self.assertTrue(
            OPENAI_AI_LEADERSHIP_URL.startswith(
                "https://oaiacademy.credential.net/855a1e37-b0d2-4e7d-aed6-ae9a839c6de0?"
            )
        )
        self.assertIn("key=", OPENAI_AI_LEADERSHIP_URL)
        self.assertNotIn("/auth?token=", OPENAI_AI_LEADERSHIP_URL)

        artwork = ROOT / "images/credentials/openai_ai_leadership_premium.jpg"
        self.assertTrue(artwork.exists())
        with Image.open(artwork) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (2172, 724))
            image.verify()

        self.assertTrue(openai_ai_leadership.startswith("data:image/jpeg;base64,"))
        page = certifications()
        self.assertIn("Highlighted badge · OpenAI Academy", page)
        self.assertIn("<h3>AI Leadership</h3>", page)
        self.assertIn("how I lead enterprise AI", page)
        self.assertIn("Verify issued badge ↗", page)
        self.assertIn("course completion and passing assessment", page)
        self.assertIn(OPENAI_AI_LEADERSHIP_URL, page)
        self.assertNotIn("/auth?token=", page)
        self.assertLess(
            page.index("Highlighted badge · OpenAI Academy"),
            page.index("Additional selected badges"),
        )

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
        self.assertGreaterEqual(page.count("Verify credential ↗"), 10)
        self.assertIn("Ten selected credentials complement the featured EITCA/AI programme", page)
        diploma = ROOT / "images/credentials/microsoft_leadership_innovation_diploma.png"
        self.assertTrue(diploma.exists())
        with Image.open(diploma) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (595, 560))
            image.verify()
        from site_media import microsoft_leadership_innovation_diploma
        self.assertTrue(microsoft_leadership_innovation_diploma.startswith("data:image/png;base64,"))

        self.assertIn("Current credentials across enterprise AI and leadership priorities.", page)
        self.assertIn("Leadership highlight · Microsoft", page)
        self.assertIn("Microsoft Leadership and Innovation Professional Certificate", page)
        self.assertIn("49J7ASIMWWFA", page)
        self.assertIn("Verify Professional Certificate ↗", page)
        self.assertIn("View Specialization Diploma ↗", page)
        self.assertIn("Microsoft Leadership and Innovation Specialization diploma", page)
        self.assertIn("Specialization · 4 courses · Oct 2026", page)
        self.assertIn("Professional Certificate + Specialization diploma", page)
        self.assertIn("https://www.coursera.org/account/accomplishments/specialization/49J7ASIMWWFA", page)
        self.assertIn("Copilot as decision support, not decision replacement", page)
        self.assertNotIn("Leading with Foresight &amp; Impact", page)
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
