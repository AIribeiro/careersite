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
        filename = "Jair_Ribeiro_Senior_AI_Data_Leader_CV_2026.pdf"
        path = ROOT / "static" / filename

        # Validate the exact repository-backed bytes BEFORE importing the PDF
        # generator. This prevents a runtime regeneration from masking a broken
        # or stale committed artifact.
        committed = path.read_bytes()
        self.assertTrue(committed.startswith(b"%PDF-"))
        self.assertTrue(committed.rstrip().endswith(b"%%EOF"))
        self.assertGreater(len(committed), 4000)
        reader = PdfReader(BytesIO(committed), strict=True)
        self.assertGreaterEqual(len(reader.pages), 1)
        self.assertIsNotNone(reader.trailer.get("/Root"))

        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", f"static/{filename}"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        self.assertEqual(tracked.returncode, 0, "Canonical PDF must be committed to main")

        # The source generator must reproduce the committed artifact byte for
        # byte, and the production runtime binding must expose that static file.
        import site_cv
        self.assertEqual(committed, site_cv.CV_BYTES)
        self.assertEqual(site_cv.CV_SITE_DISPLAY, "AI & Data Portfolio")
        self.assertEqual(
            site_cv.CV_SITE_URL,
            "https://jairribeiro-ai.streamlit.app/?source=cv",
        )
        self.assertIn(b"/Subtype /Link", committed)
        self.assertIn(site_cv.CV_SITE_URL.encode("latin-1"), committed)
        source = (ROOT / "src/site_cv.py").read_text(encoding="utf-8")
        self.assertIn("CV_SITE_DISPLAY, link=CV_SITE_URL", source)

        import site_cv_runtime  # noqa: F401
        from site_assets import CV_BYTES, CV_URI

        self.assertEqual(CV_BYTES, committed)
        self.assertEqual(CV_URI, f"/app/static/{filename}")

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
        self.assertEqual(site_cv.CV_SITE_DISPLAY, CV_PORTFOLIO_LABEL)
        self.assertNotEqual(site_cv.CV_SITE_DISPLAY, CANONICAL_SITE_DISPLAY)
        self.assertEqual(site_cv.CV_SITE_URL, PERMANENT_SURFACES["cv"])
        self.assertEqual(page_analytics.PUBLIC_BASE_URL, CANONICAL_SITE_URL)
        self.assertEqual(tuple(RECOMMENDED_ATTRIBUTION_SOURCES), ATTRIBUTION_SOURCES)
        self.assertEqual(
            ATTRIBUTION_SOURCES,
            ("linkedin", "email", "cv", "outreach", "application"),
        )
        self.assertEqual(
            PERMANENT_SURFACES["linkedin"],
            "https://jairribeiro-ai.streamlit.app/?source=linkedin",
        )
        self.assertEqual(
            PERMANENT_SURFACES["application"],
            "https://jairribeiro-ai.streamlit.app/?source=application",
        )
        self.assertEqual(
            APPLICATION_LENSES["head_data_ai"],
            "https://jairribeiro-ai.streamlit.app/?page=enterprise&source=application&role=head-data-ai",
        )
        self.assertEqual(
            APPLICATION_LENSES["ai_transformation"],
            "https://jairribeiro-ai.streamlit.app/?page=transformation&source=application&role=ai-transformation",
        )
        self.assertEqual(
            APPLICATION_LENSES["ai_governance"],
            "https://jairribeiro-ai.streamlit.app/?page=governance&source=application&role=ai-governance",
        )
        self.assertEqual(
            APPLICATION_LENSES["business_driven_ai"],
            "https://jairribeiro-ai.streamlit.app/?page=consulting&source=application&role=business-driven-ai",
        )
        self.assertEqual(
            APPLICATION_LENSES["ai_data_leadership"],
            "https://jairribeiro-ai.streamlit.app/?page=impact&source=application&role=ai-data-leadership",
        )
        self.assertEqual(
            POST_INTERVIEW_LINKS["operating_model"],
            "https://jairribeiro-ai.streamlit.app/?page=impact&source=email&role=ai-transformation#leadership-frameworks",
        )
        self.assertEqual(LINKEDIN_FEATURED["title"], "Enterprise AI & Data Leadership")
        self.assertNotIn("lovable.app", "\n".join(PERMANENT_SURFACES.values()))
        self.assertNotIn("lovable.app", "\n".join(APPLICATION_LENSES.values()))
        self.assertNotIn("lovable.app", "\n".join(POST_INTERVIEW_LINKS.values()))

    def test_curated_media_bundle_loads(self) -> None:
        import site_media  # noqa: F401
        from site_assets import (
            ABOUT_BW_URI,
            HERO_URI,
            PANEL_DIALOGUE_URI,
            THINKING_PANEL_URI,
            WORKSHOP_URI,
        )

        assets = [HERO_URI, WORKSHOP_URI, PANEL_DIALOGUE_URI, THINKING_PANEL_URI, ABOUT_BW_URI]
        for uri in assets:
            self.assertTrue(uri.startswith("data:image/"))
            self.assertGreater(len(uri), 10000)

    def test_all_public_pages_are_in_navigation(self) -> None:
        from site_components import ROLE_LENSES, nav

        html = nav("home")
        for label in ("Home", "Leadership Impact", "Thinking", "About", "Contact", "Role lenses"):
            self.assertIn(label, html)
        self.assertEqual(
            set(ROLE_LENSES),
            {"enterprise", "transformation", "governance", "consulting"},
        )
        self.assertNotIn("Analytics", html)

    def test_experience_metrics_are_precise(self) -> None:
        for relative in (
            "src/page_home.py",
            "src/page_about.py",
            "src/site_cv.py",
            "src/site_assets.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("20+", text, relative)
            self.assertIn("8+", text, relative)
            self.assertNotIn("15+ years", text, relative)
            self.assertNotIn("More than 15 years", text, relative)

    def test_home_keeps_distinctive_positioning(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        meta = (ROOT / "src/site_meta.py").read_text(encoding="utf-8")
        components = (ROOT / "src/site_components.py").read_text(encoding="utf-8")

        self.assertIn("AI scales as a system, not as a model.", home)
        self.assertIn("decision system around AI", home)
        self.assertIn("Based in Gothenburg · Sweden &amp; international mandates", home)
        self.assertIn("decision system around AI", meta)
        self.assertIn("Based in Gothenburg · Sweden &amp; international mandates", components)
        self.assertIn("Download my CV ↓", home)
        self.assertIn('data-hq-event="cv_download_home"', home)
        self.assertNotIn("Gothenburg, Sweden · Sweden / International", home)

    def test_analytics_taxonomy_privacy_and_attribution(self) -> None:
        from site_analytics import (
            ALLOWED_EVENTS,
            LENS_PAGES,
            RECOMMENDED_ATTRIBUTION_SOURCES,
        )

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
            },
        )
        self.assertEqual(
            set(LENS_PAGES),
            {"enterprise", "transformation", "governance", "consulting"},
        )
        self.assertEqual(
            tuple(RECOMMENDED_ATTRIBUTION_SOURCES),
            ("linkedin", "email", "cv", "outreach", "application"),
        )

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
        self.assertIn("inject_analytics(PAGE, source=\"streamlit\")", app)
        self.assertIn("import site_cv_runtime", app)
        self.assertNotIn("import site_cv  #", app)
        self.assertNotIn("site_cv_delivery", app)

        self.assertIn("noindex,nofollow,noarchive", dashboard)
        self.assertIn("Attribution link builder", dashboard)
        self.assertIn("RECOMMENDED_ATTRIBUTION_SOURCES", dashboard)
        self.assertIn("Email is tracked separately from recruiter outreach", dashboard)
        self.assertIn("source", dashboard)
        self.assertIn("role", dashboard)


if __name__ == "__main__":
    unittest.main()
