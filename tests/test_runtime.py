from __future__ import annotations

from io import BytesIO
from pathlib import Path
import subprocess
import sys
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class RuntimeSmokeTests(unittest.TestCase):
    def test_canonical_cv_delivery(self) -> None:
        filename = "Jair_Ribeiro_Enterprise_AI_Data_Leader_CV_2026.pdf"
        path = ROOT / "static" / filename

        committed = path.read_bytes()
        self.assertTrue(committed.startswith(b"%PDF-"))
        self.assertTrue(committed.rstrip().endswith(b"%%EOF"))
        self.assertGreater(len(committed), 4000)
        reader = PdfReader(BytesIO(committed), strict=True)
        self.assertGreaterEqual(len(reader.pages), 1)
        self.assertIsNotNone(reader.trailer.get("/Root"))
        self.assertIn(b"/Subtype /Link", committed)
        self.assertIn(b"https://jairribeiro-ai.streamlit.app/?source=cv", committed)

        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", f"static/{filename}"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        self.assertEqual(tracked.returncode, 0, "Canonical PDF must be committed to main")

        import site_cv_runtime  # noqa: F401
        from site_assets import CV_BYTES, CV_URI

        self.assertEqual(CV_BYTES, committed)
        self.assertEqual(CV_URI, f"app/static/{filename}")
        self.assertFalse(CV_URI.startswith("/"))

        import site_cv

        generated = site_cv.CV_BYTES
        self.assertTrue(generated.startswith(b"%PDF-"))
        self.assertTrue(generated.rstrip().endswith(b"%%EOF"))
        generated_reader = PdfReader(BytesIO(generated), strict=True)
        self.assertGreaterEqual(len(generated_reader.pages), 1)
        self.assertIsNotNone(generated_reader.trailer.get("/Root"))
        self.assertEqual(site_cv.CV_FILENAME, filename)
        self.assertEqual(site_cv.CV_SITE_DISPLAY, "AI & Data Portfolio")
        self.assertEqual(site_cv.CV_SITE_URL, "https://jairribeiro-ai.streamlit.app/?source=cv")
        self.assertIn(b"/Subtype /Link", generated)
        self.assertIn(site_cv.CV_SITE_URL.encode("latin-1"), generated)
        source = (ROOT / "src/site_cv.py").read_text(encoding="utf-8")
        self.assertIn("Enterprise AI & Data Leader", source)
        self.assertNotIn("Senior AI & Data Leader", source)
        self.assertIn("CV_SITE_DISPLAY, link=CV_SITE_URL", source)
        self.assertIn('site_assets.CV_URI = f"app/static/{CV_FILENAME}"', source)

    def test_distribution_policy_is_canonical_and_contextual(self) -> None:
        import page_analytics
        import site_cv
        from site_analytics import RECOMMENDED_ATTRIBUTION_SOURCES
        from site_distribution import (
            APPLICATION_LENSES,
            ATTRIBUTION_SOURCES,
            CANONICAL_SITE_DISPLAY,
            CANONICAL_SITE_URL,
            CV_PORTFOLIO_LABEL,
            LINKEDIN_FEATURED,
            PERMANENT_SURFACES,
            POST_INTERVIEW_LINKS,
        )

        self.assertEqual(CANONICAL_SITE_URL, "https://jairribeiro-ai.streamlit.app/")
        self.assertEqual(CANONICAL_SITE_DISPLAY, "jairribeiro-ai.streamlit.app")
        self.assertEqual(CV_PORTFOLIO_LABEL, "AI & Data Portfolio")
        self.assertNotEqual(site_cv.CV_SITE_DISPLAY, CANONICAL_SITE_DISPLAY)
        self.assertEqual(site_cv.CV_SITE_URL, PERMANENT_SURFACES["cv"])
        self.assertEqual(page_analytics.PUBLIC_BASE_URL, CANONICAL_SITE_URL)
        self.assertEqual(tuple(RECOMMENDED_ATTRIBUTION_SOURCES), ATTRIBUTION_SOURCES)
        self.assertEqual(ATTRIBUTION_SOURCES, ("linkedin", "email", "cv", "outreach", "application"))
        self.assertEqual(PERMANENT_SURFACES["linkedin"], "https://jairribeiro-ai.streamlit.app/?source=linkedin")
        self.assertEqual(PERMANENT_SURFACES["application"], "https://jairribeiro-ai.streamlit.app/?source=application")
        self.assertEqual(APPLICATION_LENSES["head_data_ai"], "https://jairribeiro-ai.streamlit.app/?page=enterprise&source=application&role=head-data-ai")
        self.assertEqual(APPLICATION_LENSES["ai_transformation"], "https://jairribeiro-ai.streamlit.app/?page=transformation&source=application&role=ai-transformation")
        self.assertEqual(APPLICATION_LENSES["ai_governance"], "https://jairribeiro-ai.streamlit.app/?page=governance&source=application&role=ai-governance")
        self.assertEqual(APPLICATION_LENSES["business_driven_ai"], "https://jairribeiro-ai.streamlit.app/?page=consulting&source=application&role=business-driven-ai")
        self.assertEqual(APPLICATION_LENSES["ai_data_leadership"], "https://jairribeiro-ai.streamlit.app/?page=impact&source=application&role=ai-data-leadership")
        self.assertEqual(POST_INTERVIEW_LINKS["operating_model"], "https://jairribeiro-ai.streamlit.app/?page=impact&source=email&role=ai-transformation#leadership-frameworks")
        self.assertEqual(LINKEDIN_FEATURED["title"], "Enterprise AI & Data Leadership")
        self.assertNotIn("lovable.app", "\n".join(PERMANENT_SURFACES.values()))

    def test_curated_media_bundle_loads(self) -> None:
        import site_media  # noqa: F401
        from site_assets import ABOUT_BW_URI, HERO_URI, PANEL_DIALOGUE_URI, THINKING_PANEL_URI, WORKSHOP_URI

        for uri in [HERO_URI, WORKSHOP_URI, PANEL_DIALOGUE_URI, THINKING_PANEL_URI, ABOUT_BW_URI]:
            self.assertTrue(uri.startswith("data:image/"))
            self.assertGreater(len(uri), 10000)

    def test_all_public_pages_are_in_navigation(self) -> None:
        from site_components import ROLE_LENSES, nav

        html = nav("home")
        for label in ("Home", "Leadership Impact", "Thinking", "About", "Contact", "Role lenses"):
            self.assertIn(label, html)
        self.assertEqual(set(ROLE_LENSES), {"enterprise", "transformation", "governance", "consulting"})
        self.assertEqual(ROLE_LENSES["transformation"], "AI Transformation & Adoption")
        self.assertNotIn("Analytics", html)

        active = nav("transformation")
        self.assertIn('summary class="link on"', active)
        self.assertIn("AI Transformation &amp; Adoption", active)

    def test_experience_metrics_are_precise(self) -> None:
        for relative in ("src/page_home.py", "src/page_about.py", "src/site_cv.py", "src/site_assets.py"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("20+", text, relative)
            self.assertIn("8+", text, relative)
            self.assertNotIn("15+ years", text, relative)
            self.assertNotIn("More than 15 years", text, relative)

        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
        self.assertIn("across my volvo ai roles", home.lower())
        self.assertIn("across my volvo ai roles", impact.lower())
        self.assertNotIn("managed a portfolio of 100+", home.lower())
        self.assertNotIn("managed a portfolio of 100+", impact.lower())

    def test_revised_portfolio_positioning(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        about = (ROOT / "src/page_about.py").read_text(encoding="utf-8")
        impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
        lenses = (ROOT / "src/site_lenses.py").read_text(encoding="utf-8")
        artifacts = (ROOT / "src/site_artifacts.py").read_text(encoding="utf-8")
        meta = (ROOT / "src/site_meta.py").read_text(encoding="utf-8")

        self.assertIn("I work at the point where enterprise AI strategy meets operating reality", home)
        self.assertIn("AI scales as a system, not as a model.", home)
        self.assertIn("Based in Gothenburg · Sweden &amp; international mandates", home)
        self.assertIn("The leadership problems I tend to work around.", home)
        self.assertIn("Governance, Operating Model &amp; Responsible Scale", home)
        self.assertIn("AI Portfolio &amp; Business Value", home)
        self.assertIn("Choose which ideas deserve more investment.", home)
        self.assertNotIn("Business-Driven AI &amp; Consulting", home)
        self.assertIn("Business-Driven AI & Consulting", lenses)
        self.assertNotIn("Translating AI capability into a business problem worth solving.", home)
        self.assertIn("Translating AI capability into a business problem worth solving.", impact)
        self.assertIn("Claes Sandros", home)
        self.assertIn("Anna Börjesson Sandberg", home)
        self.assertIn("Kumara Datta", home)
        self.assertIn("Jim Edwards", home)
        self.assertEqual(home.count('data-hq-event="role_lens_'), 3)
        self.assertEqual(home.count('data-hq-event="impact_portfolio_home"'), 1)
        self.assertEqual(home.count('<article class="card"><span class="org">'), 3)
        self.assertEqual(home.count('data-hq-event="reference_'), 4)
        self.assertIn("Download my CV ↓", home)

        for editorial_instruction in (
            "These figures are included for context, not as a scorecard",
            "These are broad contexts, not job-title boxes",
            "Each example focuses on the situation",
            "not a list of responsibilities copied from a CV",
            "More specific role lenses remain available in the navigation",
        ):
            self.assertNotIn(editorial_instruction, home)

        for aggressive in ("coding theatre", "compliance theatre", "Challenge without theatre"):
            self.assertNotIn(aggressive, about)
            self.assertNotIn(aggressive, lenses)
        self.assertIn("Make disagreement useful", about)
        self.assertIn("Specialist depth should remain with the specialists", about)
        self.assertIn("examples", artifacts.lower())
        self.assertNotIn("proprietary methods", artifacts.lower().replace("not proprietary methods", ""))
        self.assertIn("curated portfolio", meta.lower())

    def test_analytics_taxonomy_privacy_and_attribution(self) -> None:
        from site_analytics import ALLOWED_EVENTS, LENS_PAGES, RECOMMENDED_ATTRIBUTION_SOURCES

        self.assertEqual(
            set(ALLOWED_EVENTS),
            {
                "page_view",
                "impact_view",
                "lens_view",
                "cv_download",
                "email_click",
                "linkedin_click",
                "article_click",
                "engagement_ping",
            },
        )
        self.assertEqual(set(LENS_PAGES), {"enterprise", "transformation", "governance", "consulting"})
        self.assertEqual(tuple(RECOMMENDED_ATTRIBUTION_SOURCES), ("linkedin", "email", "cv", "outreach", "application"))

        analytics = (ROOT / "src/site_analytics.py").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        dashboard = (ROOT / "src/page_analytics.py").read_text(encoding="utf-8")

        self.assertIn("sessionStorage", analytics)
        self.assertNotIn("localStorage", analytics)
        self.assertNotIn("document.cookie", analytics)
        self.assertNotIn("user_agent", analytics)
        self.assertIn("params.get('source')", analytics)
        self.assertIn("params.get('role')", analytics)
        self.assertIn("attribution_source", analytics)
        self.assertIn("attribution_role", analytics)
        self.assertIn("jair_hq_attribution_v1", analytics)

        self.assertIn('PUBLIC_VALID | {"analytics"}', app)
        self.assertIn('if PAGE == "analytics":', app)
        self.assertIn("render_analytics_dashboard()", app)
        self.assertIn('inject_analytics(PAGE, source="streamlit")', app)
        self.assertIn("import site_cv_runtime", app)
        self.assertNotIn("site_cv_delivery", app)

        self.assertIn("noindex,nofollow,noarchive", dashboard)
        self.assertIn("Attribution link builder", dashboard)
        self.assertIn("RECOMMENDED_ATTRIBUTION_SOURCES", dashboard)
        self.assertIn("Job-search sources", dashboard)
        self.assertIn("st.vega_lite_chart", dashboard)
        self.assertNotIn("st.dataframe", dashboard)


if __name__ == "__main__":
    unittest.main()
