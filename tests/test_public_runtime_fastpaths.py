"""Focused regression checks for public-page latency fixes."""
from __future__ import annotations

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import home_whats_new as news


class PublicRuntimeFastPathTests(unittest.TestCase):
    def test_credential_source_is_parsed_once_until_file_changes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            catalog = root / "src" / "page_certifications.py"
            catalog.write_text(
                "FLAGSHIP = [{'title': 'First', 'issuer': 'School', 'date': 'Nov 2026'}]",
                encoding="utf-8",
            )
            actual_parse = ast.parse
            with patch.object(news, "ROOT", root), patch.object(
                news.ast, "parse", wraps=actual_parse
            ) as parse:
                self.assertEqual(len(news._credential_items()), 1)
                self.assertEqual(len(news._credential_items()), 1)
                self.assertEqual(parse.call_count, 1)
                catalog.write_text(
                    "FLAGSHIP = [{'title': 'Second credential', 'issuer': 'School', "
                    "'date': 'Dec 2026'}]",
                    encoding="utf-8",
                )
                self.assertEqual(news._credential_items()[0].title, "Second credential")
                self.assertEqual(parse.call_count, 2)

    def test_reader_collectors_are_not_mounted_on_public_catalogue_pages(self):
        source = (Path(__file__).resolve().parents[1] / "main.py").read_text()
        self.assertIn(
            "if CMS_ARTICLE_META is not None or ARTICLE_META is not None:", source
        )
        self.assertLess(
            source.index("if CMS_ARTICLE_META is not None or ARTICLE_META is not None:"),
            source.index("inject_article_analytics(PAGE"),
        )
        self.assertIn('inject_analytics(PAGE, source="streamlit")', source)

    def test_base_analytics_keeps_catalogue_article_clicks(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" / "site_analytics.py"
        ).read_text()
        self.assertIn("linkedArticle", source)
        self.assertIn("'article_click'", source)
        self.assertIn("article_slug: safeText(linkedArticle, 160)", source)
        self.assertIn("win.__jairArticleContext = null;", source)
        self.assertIn("if (!win.__jairArticleContext && win.__jairAnalyticsSend)", source)

    def test_dom_observation_starts_only_when_browser_is_idle(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" /
            "site_behavior_telemetry_v2.py"
        ).read_text()
        self.assertIn("requestIdleCallback(boot", source.replace(
            "requestIdleCallback(() => { if (state.active) boot(); }", "requestIdleCallback(boot"
        ))
        self.assertIn("win.setTimeout(() => { if (state.active) boot(); }, 750)", source)


if __name__ == "__main__":
    unittest.main()
