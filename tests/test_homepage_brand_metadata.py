"""Branded home metadata and native Streamlit favicon regression checks."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import site_meta


class BrandedHomepageMetadataTests(unittest.TestCase):
    def test_homepage_contract_matches_main_domain_settings(self):
        self.assertEqual(site_meta.HOME_TITLE,
                         "Jair Ribeiro | Enterprise AI & Data Leadership")
        self.assertEqual(
            site_meta.DESCRIPTIONS["home"],
            "Jair Ribeiro explores how leaders turn enterprise AI and data strategy "
            "into business results. Executive briefings, governance perspectives "
            "and practical insights on AI adoption.",
        )
        self.assertIn("AI Strategy", site_meta.HOME_KEYWORDS)
        self.assertIn("AI Advisory", site_meta.HOME_KEYWORDS)

    def test_home_metadata_is_injected_into_streamlit_document_head(self):
        with patch.object(site_meta.components, "html") as render:
            site_meta.inject_metadata("home", site_meta.HOME_TITLE)
        script = render.call_args.args[0]
        self.assertIn("const title = " + json.dumps(site_meta.HOME_TITLE), script)
        self.assertIn("const description = " + json.dumps(site_meta.HOME_DESCRIPTION), script)
        self.assertIn("const keywords = " + json.dumps(site_meta.HOME_KEYWORDS), script)
        self.assertIn("const doc = window.parent.document", script)
        self.assertIn("meta('meta[name=\"keywords\"]'", script)
        self.assertIn("meta('meta[name=\"author\"]'", script)
        self.assertIn("meta('meta[property=\"og:title\"]'", script)
        self.assertIn("meta('meta[name=\"twitter:description\"]'", script)
        self.assertIn("const base = \"https://jairribeiro.com/\"", script)
        self.assertIn("height=0", str(render.call_args))

    def test_other_pages_keep_their_specific_descriptions(self):
        with patch.object(site_meta.components, "html") as render:
            site_meta.inject_metadata("briefings", "Executive AI Briefings | Jair Ribeiro")
        script = render.call_args.args[0]
        self.assertIn(json.dumps(site_meta.DESCRIPTIONS["briefings"]), script)
        self.assertIn('const keywords = "";', script)
        self.assertIn("doc.head.querySelector('meta[name=\"keywords\"]')?.remove()", script)

    def test_page_title_and_existing_portrait_favicon_are_configured(self):
        main_source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("from site_meta import HOME_TITLE,", main_source)
        self.assertIn('"home": HOME_TITLE', main_source)
        self.assertIn("page_title=PAGE_TITLE", main_source)
        self.assertIn("page_icon=str(PAGE_ICON)", main_source)
        self.assertTrue((ROOT / "images" / "profile_red_bg.jpg.jpg").is_file())


if __name__ == "__main__":
    unittest.main()
