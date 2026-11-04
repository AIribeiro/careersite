"""What’s new strip: publication precedence, escaping, and lightweight operation."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import home_whats_new as news


class HomeWhatsNewTests(unittest.TestCase):
    def test_page_update_is_latest_current_local_release(self) -> None:
        current = news.latest_local_release(datetime(2026, 11, 4, 12, tzinfo=timezone.utc))
        self.assertEqual(current.type, "Page update")
        self.assertEqual(current.href, "?page=ai-data-governance")
        self.assertIn("Executive Framework", current.title)

    def test_public_credentials_are_discovered_without_importing_credential_page(self) -> None:
        with TemporaryDirectory() as directory:
            source = Path(directory) / "src"
            source.mkdir()
            (source / "page_certifications.py").write_text(
                "FLAGSHIP = [{'title': 'New verified AI certificate', "
                "'issuer': 'Test Academy', 'date': 'Dec 2026'}]\n"
                "CREDLY_BADGES = [{'title': 'Another badge', 'issuer': 'Provider', "
                "'date': 'Sep 2026', 'image': badge_image}]\n",
                encoding="utf-8",
            )
            with patch.object(news, "ROOT", Path(directory)):
                items = news._credential_items()
                latest = news.latest_local_release(datetime(2026, 12, 8, tzinfo=timezone.utc))
        self.assertEqual(len(items), 2)
        self.assertEqual(latest.title, "New verified AI certificate")
        self.assertEqual(latest.href, "?page=about#credentials-evidence")

    def test_dated_future_publications_do_not_appear_early(self) -> None:
        with patch.object(news, "_credential_items", return_value=()):
            current = news.latest_local_release(datetime(2026, 10, 20, tzinfo=timezone.utc))
        self.assertEqual(current.title, "AI & Data Governance")

    def test_untrusted_text_is_escaped_and_links_stay_relative(self) -> None:
        injected = news.NewsItem(
            type="Article",
            title="<img src=x>",
            description="<script>alert(1)</script>",
            published_at=datetime(2026, 11, 4, tzinfo=timezone.utc),
            href="?page=thinking&article=sample",
            cta="Open",
        )
        with patch.object(news, "latest_local_release", return_value=injected):
            output = news.home_whats_new()
        self.assertNotIn("<img src=x>", output)
        self.assertNotIn("<script>alert", output)
        self.assertIn("&lt;img src=x&gt;", output)
        self.assertIn('data-analytics-section="home-whats-new"', output)
        self.assertIn("What's new?", output.replace("What’s", "What's"))

    def test_render_does_not_wait_for_cms_query(self) -> None:
        with patch.object(news, "inject_live_home_update", side_effect=AssertionError("Home blocked")):
            content = news.home_whats_new()
        self.assertIn("Explore the framework", content)

    def test_live_refresh_is_a_small_client_side_request(self) -> None:
        with patch("streamlit.components.v1.html") as html:
            news.inject_live_home_update()
        script = html.call_args.args[0]
        self.assertIn("status=eq.published", script)
        self.assertIn("published_at.desc.nullslast", script)
        self.assertIn("kind === \"executive briefing\"", script)
        self.assertIn("kind === \"weekly brief\"", script)
        self.assertIn("cache: \"no-store\"", script)
        self.assertIn("AbortController", script)
        self.assertNotIn("content_html", script)
        self.assertEqual(html.call_args.kwargs["height"], 0)


if __name__ == "__main__":
    unittest.main()
