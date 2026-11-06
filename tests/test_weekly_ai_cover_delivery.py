"""Regression coverage for the Friday Weekly AI cover delivery contract.

The Friday CMS row may be published before the generated PNG is committed.
The public reader and crawler must both derive the correct versioned route
without relying on /app/static or on a CMS header_image_url update.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_cms import CmsArticle, effective_header_image_url, cms_feature_image_meta
from thinking_weekly_brief import _edition_cover_html, weekly_edition_cover_url, _weekly_header_image_uri


def weekly_article(**changes):
    values = dict(
        id="weekly-cover-test",
        slug="weekly-ai-2026-11-06",
        title="WEEKLY AI — AI's Next Test Is Operational Trust",
        category="Weekly AI",
        kind="Weekly Brief",
        status="published",
        header_image_url="",
    )
    values.update(changes)
    return CmsArticle(**values)


class WeeklyAiCoverDeliveryTests(unittest.TestCase):
    def test_null_cms_image_uses_real_dedicated_route_with_cache_busting(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            image = b"\x89PNG\r\n\x1a\n" + b"A" * 5000
            (folder / "weekly-ai-2026-11-06.png").write_bytes(image)
            expected_hash = hashlib.sha256(image).hexdigest()[:12]
            with patch("thinking_weekly_brief.WEEKLY_COVER_DIR", folder):
                article = weekly_article()
                url = weekly_edition_cover_url(article.slug)
                self.assertEqual(
                    url,
                    "https://jairribeiro-ai.streamlit.app/weekly-ai-cover/"
                    f"weekly-ai-2026-11-06.png?v={expected_hash}",
                )
                self.assertEqual(effective_header_image_url(article), url)
                self.assertEqual(
                    cms_feature_image_meta(article),
                    (url, "image/png", 1200, 627),
                )
                markup = _edition_cover_html(article)
                inline = "data:image/png;base64," + base64.b64encode(image).decode("ascii")
                self.assertIn('src="' + inline + '"', markup)
                self.assertIn('<figure class="weekly-ai-edition-cover"', markup)
                self.assertNotIn("/weekly-ai-cover/weekly-ai-2026-11-06.png", markup)
                self.assertNotIn("/app/static/weekly-ai/", markup)
                self.assertIn("AI&#x27;s Next Test", markup)

    def test_missing_cover_is_not_cached_and_appears_after_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            article = weekly_article()
            with patch("thinking_weekly_brief.WEEKLY_COVER_DIR", folder):
                self.assertEqual(weekly_edition_cover_url(article.slug), "")
                self.assertEqual(_edition_cover_html(article), "")
                (folder / f"{article.slug}.png").write_bytes(
                    b"\x89PNG\r\n\x1a\n" + b"B" * 5000
                )
                self.assertIn("/weekly-ai-cover/", weekly_edition_cover_url(article.slug))
                self.assertIn('src="data:image/png;base64,', _edition_cover_html(article))
                # A newly revised cover must bypass the old browser cache.
                old_url = weekly_edition_cover_url(article.slug)
                (folder / f"{article.slug}.png").write_bytes(
                    b"\x89PNG\r\n\x1a\n" + b"C" * 5000
                )
                self.assertNotEqual(old_url, weekly_edition_cover_url(article.slug))

    def test_explicit_cms_header_is_authoritative(self):
        article = weekly_article(
            header_image_url="https://example.com/editorial-cover.webp",
            header_image_alt="Editorial art",
        )
        self.assertEqual(
            effective_header_image_url(article),
            "https://example.com/editorial-cover.webp",
        )
        self.assertIn('alt="Editorial art"', _edition_cover_html(article))
        self.assertIn("https://example.com/editorial-cover.webp", _edition_cover_html(article))

    def test_unrelated_articles_and_bad_slugs_do_not_get_friday_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            image = b"\x89PNG\r\n\x1a\n" + b"D" * 5000
            (folder / "weekly-ai-2026-11-06.png").write_bytes(image)
            with patch("thinking_weekly_brief.WEEKLY_COVER_DIR", folder):
                self.assertFalse(weekly_edition_cover_url("../weekly-ai-2026-11-06"))
                other = weekly_article(category="AI Governance", kind="Article")
                self.assertNotIn("/weekly-ai-cover/", effective_header_image_url(other))

    def test_evergreen_uses_first_party_route_not_raw_github(self):
        self.assertEqual(_weekly_header_image_uri(), "/weekly-ai-cover/evergreen.webp")

    def test_real_week45_asset_and_media_route_are_committed(self):
        image = ROOT / "static" / "weekly-ai" / "weekly-ai-2026-11-06.png"
        self.assertGreater(image.stat().st_size, 2048)
        with image.open("rb") as asset:
            self.assertEqual(asset.read(8), b"\x89PNG\r\n\x1a\n")
        self.assertIn(
            'Route("/weekly-ai-cover/{slug}.png", _weekly_ai_cover',
            (ROOT / "app.py").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "/weekly-ai-cover/weekly-ai-2026-11-06.png?v=",
            weekly_edition_cover_url("weekly-ai-2026-11-06"),
        )
        html = _edition_cover_html(weekly_article())
        self.assertIn('src="data:image/png;base64,', html)
        encoded = html.split('src="data:image/png;base64,', 1)[1].split('"', 1)[0]
        self.assertEqual(base64.b64decode(encoded), image.read_bytes())


if __name__ == "__main__":
    unittest.main()
