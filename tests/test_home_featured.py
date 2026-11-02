"""Home writing feature rotates independently across Thinking and Executive Briefings."""
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

    def test_home_can_select_either_a_thinking_article_or_an_executive_briefing(self) -> None:
        from page_home_featured import current_home_article
        essay = self.article("thinking-perspective", 80, kind="Article")
        briefing = self.article(
            "boardroom-decision", 2, kind="Executive Briefing",
            subtitle="Three decisions leadership must own.",
        )
        with patch("site_cms.fetch_published_articles", return_value=(essay, briefing)), \
             patch("page_home_featured.choice", side_effect=lambda pool: pool[1]) as picker:
            selected = current_home_article()
        self.assertEqual(selected.slug, "boardroom-decision")
        self.assertEqual(selected.href, "?page=briefing&article=boardroom-decision")
        self.assertEqual(selected.deck, "Three decisions leadership must own.")
        self.assertEqual(selected.content_type, "briefing")
        self.assertEqual({item.slug for item in picker.call_args.args[0]},
                         {"thinking-perspective", "boardroom-decision"})

    def test_home_selection_ignores_latest_and_readership_rankings(self) -> None:
        from page_home_featured import current_home_article
        older = self.article("older-essay", 150)
        latest = self.article("latest-essay", 2)
        with patch("site_cms.fetch_published_articles", return_value=(latest, older)), \
             patch("page_home_featured.choice", return_value=older), \
             patch("site_cms._public_reads_or_none",
                   side_effect=AssertionError("Home must not query readership")):
            selected = current_home_article()
        self.assertEqual(selected.slug, "older-essay")
        self.assertEqual(selected.deck, older.excerpt)
        self.assertEqual(selected.href, "?page=thinking&article=older-essay")

    def test_home_randomizes_on_each_render_instead_of_caching_selection(self) -> None:
        from page_home_featured import current_home_article
        first = self.article("first-essay", 48)
        second = self.article("second-essay", 72)
        with patch("site_cms.fetch_published_articles", return_value=(first, second)), \
             patch("page_home_featured.choice", side_effect=(first, second)) as picker:
            selected_first = current_home_article()
            selected_second = current_home_article()
        self.assertEqual([selected_first.slug, selected_second.slug],
                         ["first-essay", "second-essay"])
        self.assertEqual(picker.call_count, 2)

    def test_weekly_ai_and_drafts_are_never_eligible(self) -> None:
        from page_home_featured import current_home_article
        weekly = self.article("weekly-ai-2026-10-19", 2, kind="Weekly Brief", category="Weekly AI")
        draft = self.article("draft-essay", 3)
        draft.status = "draft"
        ordinary = self.article("ordinary-essay", 40)
        briefing = self.article("another-briefing", 25, kind="Executive Briefing")
        with patch("site_cms.fetch_published_articles",
                   return_value=(weekly, draft, ordinary, briefing)), \
             patch("page_home_featured.choice", side_effect=lambda pool: pool[0]) as picker:
            selected = current_home_article()
        self.assertEqual(selected.slug, "ordinary-essay")
        self.assertEqual({item.slug for item in picker.call_args.args[0]},
                         {"ordinary-essay", "another-briefing"})

    def test_cms_outage_rotates_through_legacy_thinking_fallback(self) -> None:
        from page_home_featured import current_home_article
        from thinking_articles import published_articles
        legacy = tuple(published_articles())[1]
        with patch("site_cms.fetch_published_articles", side_effect=RuntimeError("offline")), \
             patch("page_home_featured.choice", return_value=legacy) as picker:
            selected = current_home_article()
        self.assertEqual(selected.slug, legacy.slug)
        self.assertIn("page=thinking&article=", selected.href)
        self.assertGreater(len(picker.call_args.args[0]), 1)

    def test_briefing_card_links_and_cta_match_its_content_type(self) -> None:
        from page_home_featured import HomeArticlePreview, home_featured_article
        briefing = HomeArticlePreview(
            slug="executive-choice",
            title="The Executive Decision",
            deck="An executive-level assessment",
            kind_topic="Executive Briefing · AI Governance",
            published_label="2 Nov 2026",
            read_minutes=6,
            href="?page=briefing&article=executive-choice",
            image_url="https://example.org/briefing.webp",
            image_alt="Briefing cover",
            content_type="briefing",
        )
        with patch("page_home_featured.current_home_article", return_value=briefing):
            html = home_featured_article()
        self.assertEqual(html.count('href="?page=briefing&amp;article=executive-choice"'), 3)
        self.assertIn("Read the briefing", html)
        self.assertIn('data-hq-content-type="briefing"', html)
        self.assertIn('href="?page=briefings"', html)
        self.assertIn('href="?page=thinking"', html)
        self.assertNotIn("Read the article", html)

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

    def test_footer_excludes_current_reader_from_random_choice(self) -> None:
        from page_home_featured import current_home_article
        current = self.article("the-current-briefing", 2, kind="Executive Briefing")
        other = self.article("another-article", 30)
        with patch("site_cms.fetch_published_articles", return_value=(current, other)), \
             patch("page_home_featured.choice", side_effect=lambda pool: pool[0]) as picker:
            selected = current_home_article(exclude_slug=current.slug)
        self.assertEqual(selected.slug, other.slug)
        self.assertEqual([item.slug for item in picker.call_args.args[0]], [other.slug])

    def test_compact_footer_uses_native_micro_cover_and_contextual_briefing_action(self) -> None:
        from page_home_featured import HomeArticlePreview, compact_writing_footer
        sample = HomeArticlePreview(
            slug="a-briefing", title="An executive AI decision", deck="A compact explanation",
            kind_topic="Executive Briefing · Enterprise AI",
            published_label="2 Nov 2026", read_minutes=6,
            href="?page=briefing&article=a-briefing",
            image_url="https://example.org/executive.webp", image_alt="Executive artwork",
            content_type="briefing",
        )
        with patch("page_home_featured.current_home_article", return_value=sample):
            html = compact_writing_footer()
        self.assertIn('data-analytics-section="site-writing-footer"', html)
        self.assertIn('class="writing-footer-art"', html)
        self.assertIn('class="writing-footer-art-mark"', html)
        self.assertIn('class="writing-footer-art-label"', html)
        self.assertIn('>BRIEFING</span>', html)
        self.assertNotIn("<img", html)
        self.assertNotIn('src="', html)
        self.assertNotIn("https://example.org/executive.webp", html)
        self.assertIn('class="writing-footer-copy"', html)
        self.assertIn('class="writing-footer-action"', html)
        self.assertIn("From my writing", html)
        self.assertIn("Read briefing", html)
        self.assertIn('data-hq-content-type="briefing"', html)
        self.assertEqual(html.count('href="?page=briefing&amp;article=a-briefing"'), 3)
        self.assertIn('href="?page=thinking"', html)
        self.assertIn('href="?page=briefings"', html)

    def test_compact_footer_article_uses_thinking_motif_without_remote_assets(self) -> None:
        from page_home_featured import HomeArticlePreview, compact_writing_footer
        sample = HomeArticlePreview(
            slug="operations-essay", title='AI & data decisions',
            deck="A perspective", kind_topic="AI Leadership",
            published_label="1 Nov 2026", read_minutes=4,
            href="?page=thinking&article=operations-essay",
            image_url="https://broken.example.invalid/enormous-hero.jpg",
            image_alt="Unreachable image",
            content_type="article",
        )
        with patch("page_home_featured.current_home_article", return_value=sample):
            html = compact_writing_footer()
        self.assertIn('>THINKING</span>', html)
        self.assertIn("Read article", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("broken.example.invalid", html)
        self.assertEqual(html.count('href="?page=thinking&amp;article=operations-essay"'), 3)

    def test_injection_covers_public_pages_but_not_home_or_private_analytics(self) -> None:
        from page_home_featured import inject_writing_footer
        document = '<nav></nav><main><article>Page contents</article></main><footer></footer>'
        with patch("page_home_featured.compact_writing_footer",
                   return_value='<section id="writing-test"></section>') as render:
            for page in ("impact", "thinking", "briefings", "briefing", "about",
                         "contact", "ai-data-governance"):
                with self.subTest(page=page):
                    enhanced = inject_writing_footer(document, page)
                    self.assertEqual(enhanced.count('id="writing-test"'), 1)
                    self.assertLess(enhanced.index('id="writing-test"'), enhanced.index('</main>'))
                    self.assertLess(enhanced.index('</main>'), enhanced.index('<footer>'))
            for page in ("home", "analytics", "admin"):
                self.assertEqual(inject_writing_footer(document, page), document)
        self.assertEqual(render.call_count, 7)

    def test_briefing_writing_footer_precedes_the_final_contact_call(self) -> None:
        from page_home_featured import inject_writing_footer
        document = (
            '<main><article>Briefing</article>'
            '<section class="briefings-conversation" data-analytics-section="briefings-contact">'
            'Have an AI choice that needs a clearer answer?</section>'
            '</main><footer></footer>'
        )
        with patch("page_home_featured.compact_writing_footer",
                   return_value='<section id="writing-test"></section>'):
            enhanced = inject_writing_footer(document, "briefing")
        self.assertLess(enhanced.index('id="writing-test"'),
                        enhanced.index('data-analytics-section="briefings-contact"'))
        self.assertEqual(enhanced.count("Have an AI choice that needs a clearer answer?"), 1)
        self.assertEqual(enhanced.count('id="writing-test"'), 1)

    def test_injection_is_idempotent_and_reader_slug_is_forwarded(self) -> None:
        from page_home_featured import inject_writing_footer
        document = '<main><article>Reader</article></main><footer></footer>'
        with patch("page_home_featured.compact_writing_footer",
                   return_value='<section data-analytics-section="site-writing-footer"></section>') as render:
            once = inject_writing_footer(document, "thinking", article_slug="reader-slug")
            twice = inject_writing_footer(once, "thinking", article_slug="reader-slug")
        self.assertEqual(once, twice)
        self.assertEqual(render.call_count, 1)
        self.assertEqual(render.call_args.kwargs["exclude_slug"], "reader-slug")

    def test_compact_footer_is_mounted_in_the_shared_public_renderer(self) -> None:
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        main = (root / "main.py").read_text(encoding="utf-8")
        styles = (root / "src" / "site_styles.py").read_text(encoding="utf-8")
        self.assertIn("inject_writing_footer(RENDER[PAGE](), PAGE", main)
        self.assertIn(".site .writing-footer{padding:0;background:var(--paper)", styles)
        self.assertIn(".site .writing-footer-inner{display:grid;grid-template-columns:58px", styles)
        self.assertIn(".site a.writing-footer-art{position:relative;isolation:isolate", styles)
        self.assertIn("width:58px;height:72px", styles)
        self.assertIn("max-width:58px;max-height:72px", styles)
        self.assertIn("@media(max-width:820px)", styles)
        self.assertIn("@media(max-width:560px)", styles)
        self.assertIn("width:46px;min-width:46px;max-width:46px;height:61px", styles)
        self.assertNotIn(".site .writing-footer-art img", styles)

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
