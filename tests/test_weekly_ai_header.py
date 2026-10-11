"""The image is a reusable visual, while the week and edition remain dynamic."""
from pathlib import Path
import unittest

from site_cms import CmsArticle
from thinking_weekly_brief import (
    WEEKLY_IMAGE_FILE,
    _weekly_header_image_uri,
    inject_weekly_brief_landing,
)


class WeeklyAiEvergreenHeroTests(unittest.TestCase):
    def test_visual_asset_is_repository_backed_webp(self):
        image = Path(WEEKLY_IMAGE_FILE)
        data = image.read_bytes()
        self.assertGreater(len(data), 1000)
        self.assertEqual(data[:4], b"RIFF")
        self.assertEqual(data[8:12], b"WEBP")
        self.assertTrue(_weekly_header_image_uri().startswith("data:image/webp;base64,"))

    def test_banner_is_evergreen_and_current_week_remains_live(self):
        def edition(slug, published_at):
            return CmsArticle(
                id=slug, slug=slug,
                title="WEEKLY AI — Enterprise decisions",
                category="Weekly AI", kind="Weekly Brief", status="published",
                excerpt="Selected enterprise AI news", published_at=published_at,
            )
        site = "<nav>Portfolio navigation</nav><main><section>Original Thinking</section></main>"
        first = inject_weekly_brief_landing(
            site, [edition("weekly-ai-2026-10-11", "2026-10-11T09:00:00Z")]
        )
        next_week = inject_weekly_brief_landing(
            site, [edition("weekly-ai-2026-10-19", "2026-10-19T08:00:00Z")]
        )
        for html in (first, next_week):
            self.assertIn("weekly-ai-brand", html)
            self.assertIn("A one-minute briefing", html)
            self.assertIn('class="weekly-ai-brand-art"', html)
            self.assertIn("data:image/webp;base64,", html)
            self.assertIn("Browse all weeks (1)", html)
            self.assertLess(html.index("weekly-ai-brand"), html.index("weekly-ai-feature"))
        self.assertIn("Vecka · 2026", first)
        self.assertIn('class="weekly-ai-number">41', first)
        self.assertIn('class="weekly-ai-number">42', next_week)


if __name__ == "__main__":
    unittest.main()
