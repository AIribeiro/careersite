"""Home featured article follows the existing Thinking highlight, not a new ranking."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
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

    def test_article_artwork_is_confined_to_a_responsive_frame(self) -> None:
        """The image cannot expand the Home featured card to its native size."""
        from site_styles import CSS

        feature_css = CSS.split("/* Home editorial feature:", 1)[1].split("</style>", 1)[0]
        self.assertIn(".site .home-featured>.container{width:min(980px,calc(100% - 44px));max-width:100%}", feature_css)
        self.assertIn("grid-template-columns:minmax(0,.43fr) minmax(0,.57fr)", feature_css)
        self.assertIn(".site .home-featured-story{", feature_css)
        self.assertIn("max-width:100%;min-width:0;overflow:hidden", feature_css)
        self.assertIn(".site .home-featured-media img{position:absolute;inset:0;margin:auto", feature_css)
        self.assertIn("max-height:320px", feature_css)
        self.assertIn("min-width:0;min-height:0;object-fit:contain", feature_css)
        self.assertIn("height:clamp(155px,33vw,220px)", feature_css)
        self.assertIn("height:clamp(145px,43vw,185px)", feature_css)
        self.assertNotIn("min-height:360px", feature_css)

    def test_ipad_breakpoint_keeps_side_by_side_editorial_layout(self) -> None:
        """Do not stack the article at iPad portrait widths (~768-834 CSS px)."""
        from site_styles import CSS

        feature_css = CSS.split("/* Home editorial feature:", 1)[1].split("</style>", 1)[0]
        self.assertIn("@media(min-width:701px) and (max-width:980px)", feature_css)
        stacked_css = feature_css.split("@media(max-width:700px)", 1)[1]
        self.assertIn("grid-template-columns:minmax(0,1fr)", stacked_css)
        self.assertNotIn("@media(max-width:850px)", feature_css)
        tablet_css = feature_css.split("@media(min-width:701px) and (max-width:980px)", 1)[1]
        tablet_css = tablet_css.split("@media(max-width:700px)", 1)[0]
        self.assertIn("max-height:270px", tablet_css)
        self.assertIn("font-size:clamp(27px,3.6vw,33px)", tablet_css)

    def test_featured_article_and_contact_remain_inside_site_wrapper(self) -> None:
        """Catch surplus HTML closing tags which silently disable scoped CSS.

        An extra closing div in References previously closed .site before
        the article, causing Safari to display its full-resolution image and
        unstyled default text despite correct responsive CSS.
        """
        from page_home import home

        class DocumentNesting(HTMLParser):
            VOID = {"area", "base", "br", "col", "embed", "hr", "img",
                    "input", "link", "meta", "param", "source", "track", "wbr"}

            def __init__(self) -> None:
                super().__init__()
                self.stack: list[tuple[str, dict[str, str | None]]] = []
                self.unbalanced: list[str] = []
                self.feature_inside_site = False
                self.contact_inside_site = False

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                attributes = dict(attrs)
                inside_site = any(
                    node == "div" and "site" in (values.get("class") or "").split()
                    for node, values in self.stack
                )
                if attributes.get("data-analytics-section") == "home-featured-article":
                    self.feature_inside_site = inside_site
                if tag == "section" and "cta" in (attributes.get("class") or "").split():
                    self.contact_inside_site = inside_site
                if tag not in self.VOID:
                    self.stack.append((tag, attributes))

            def handle_endtag(self, tag: str) -> None:
                if tag in self.VOID:
                    return
                if not self.stack or self.stack[-1][0] != tag:
                    self.unbalanced.append(
                        f"Unexpected </{tag}> after {self.stack[-1][0] if self.stack else 'root'}"
                    )
                    return
                self.stack.pop()

        article = '<section data-analytics-section="home-featured-article"></section>'
        with patch("page_home.home_featured_article", return_value=article):
            markup = '<div class="site">' + home() + '</div>'
        checker = DocumentNesting()
        checker.feed(markup)
        self.assertFalse(checker.unbalanced, checker.unbalanced)
        self.assertFalse(checker.stack, checker.stack)
        self.assertTrue(checker.feature_inside_site)
        self.assertTrue(checker.contact_inside_site)

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
