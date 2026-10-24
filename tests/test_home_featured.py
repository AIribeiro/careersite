"""Home featured article follows the existing Thinking highlight, not a new ranking."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import unescape
from unittest.mock import patch
import unittest

from site_cms import CmsArticle


class HomeFeaturedArticleTests(unittest.TestCase):
    def article(self, slug: str, hours_old: int, *, subtitle: str = "", **kwargs) -> CmsArticle:
        return CmsArticle(
            id=slug,
            slug=slug,
            title=slug.replace("-", " ").title(),
            status="published",
            published_at=(datetime.now(timezone.utc) - timedelta(hours=hours_old)).isoformat(),
            subtitle=subtitle,
            excerpt="Excerpt shown only when the article has no subtitle.",
            **kwargs,
        )

    def test_home_uses_current_thinking_highlight_not_a_hardcoded_slug(self) -> None:
        from page_home_featured import current_home_article
        popular = self.article("popular-essay", 150)
        fresh = self.article("new-perspective", 3, subtitle="The original article deck.")
        with patch("site_cms.fetch_published_articles", return_value=(popular, fresh)), \
             patch("site_cms._public_reads_or_none",
                   return_value={"popular-essay": 500, "new-perspective": 0}):
            selected = current_home_article()
        self.assertEqual(selected.slug, "new-perspective")
        self.assertEqual(selected.deck, "The original article deck.")
        self.assertEqual(selected.href, "?page=thinking&article=new-perspective")
        self.assertEqual(selected.read_minutes, 1)

    def test_home_uses_most_read_when_no_new_publication(self) -> None:
        from page_home_featured import current_home_article
        older = self.article("older-most-read", 150)
        newer = self.article("newer-fewer-reads", 30)
        with patch("site_cms.fetch_published_articles", return_value=(older, newer)), \
             patch("site_cms._public_reads_or_none",
                   return_value={"older-most-read": 30, "newer-fewer-reads": 3}):
            selected = current_home_article()
        self.assertEqual(selected.slug, "older-most-read")
        self.assertEqual(selected.deck, older.excerpt)

    def test_weekly_ai_is_never_home_highlight(self) -> None:
        from page_home_featured import current_home_article
        weekly = self.article("weekly-ai-2026-10-19", 2, kind="Weekly Brief", category="Weekly AI")
        ordinary = self.article("ordinary-essay", 40)
        with patch("site_cms.fetch_published_articles", return_value=(weekly, ordinary)), \
             patch("site_cms._public_reads_or_none",
                   return_value={"weekly-ai-2026-10-19": 500, "ordinary-essay": 4}):
            selected = current_home_article()
        self.assertEqual(selected.slug, "ordinary-essay")

    def test_cms_outage_gracefully_uses_thinking_fallback(self) -> None:
        from page_home_featured import current_home_article
        from thinking_landing import CURRENT_PRIMARY
        from thinking_articles import article_by_key
        with patch("site_cms.fetch_published_articles", side_effect=RuntimeError("offline")):
            selected = current_home_article()
        self.assertEqual(selected.slug, article_by_key(CURRENT_PRIMARY).slug)
        self.assertIn("page=thinking&article=", selected.href)

    def test_premium_panel_contains_live_title_deck_art_and_article_link(self) -> None:
        from page_home_featured import HomeArticlePreview, home_featured_article
        selected = HomeArticlePreview(
            slug="a-slug",
            title='Decision <Leadership> & Adoption',
            deck='An article subtitle — not an invented summary. <unsafe>',
            kind_topic='Perspective · AI & Data',
            published_label='24 Oct 2026',
            read_minutes=5,
            href="?page=thinking&article=a-slug",
            image_url="https://example.org/article.webp",
            image_alt='Art for the article',
        )
        with patch("page_home_featured.current_home_article", return_value=selected):
            html = home_featured_article()
        self.assertIn('data-analytics-section="home-featured-article"', html)
        self.assertIn('Decision &lt;Leadership&gt; &amp; Adoption', html)
        self.assertIn('An article subtitle — not an invented summary. &lt;unsafe&gt;', html)
        self.assertNotIn('<unsafe>', html)
        self.assertIn('src="https://example.org/article.webp"', html)
        self.assertEqual(html.count('href="?page=thinking&amp;article=a-slug"'), 3)
        self.assertIn('data-hq-event="home_featured_article_open"', html)

    def test_featured_panel_is_immediately_before_contact(self) -> None:
        from page_home import home
        with patch("page_home.home_featured_article", return_value="<section id='highlight-test'></section>"):
            html = home()
        feature_pos = html.index("highlight-test")
        contact_pos = html.index('<section class="cta"><div class="container ctain">')
        self.assertLess(feature_pos, contact_pos)
        self.assertNotIn('<section class="', html[feature_pos:contact_pos])


if __name__ == "__main__":
    unittest.main()
