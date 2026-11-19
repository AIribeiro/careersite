"""Site-wide contextual footer contracts across public and native portfolio routes."""
from __future__ import annotations

from html.parser import HTMLParser
from unittest.mock import patch
import unittest

from about_next_navigation import _PAGE_COPY, portfolio_next_navigation
from site_portfolio_continuation import inject_portfolio_continuation
from site_native_shell import native_footer
from site_reader_shell import reader_footer
from site_styles import CSS


class _CardLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.navigator_count = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "nav" and attributes.get("aria-label") == "Continue exploring the portfolio":
            self.navigator_count += 1
        if tag == "a" and "about-next-card" in attributes.get("class", ""):
            self.links.append(attributes)


class SitewideFooterTests(unittest.TestCase):
    PUBLIC_ROUTES = {
        "home", "impact", "ai-data-governance", "thinking", "about", "contact",
        "briefings", "briefing", "advisory", "advisory-decision",
        "advisory-rollout", "advisory-scorecard", "advisory-leadership",
        "advisory-renewal", "advisory-market-signals", "advisory-market-demo",
        "privacy",
    }

    def test_every_page_has_a_dynamic_three_destination_footer(self):
        self.assertTrue(self.PUBLIC_ROUTES.issubset(_PAGE_COPY))
        for page in self.PUBLIC_ROUTES | {"readers", "advisory-access", "analytics"}:
            with self.subTest(page=page):
                if page == "advisory":
                    with (
                        patch("advisory_service_visibility.viewer_is_admin", return_value=False),
                        patch("advisory_service_visibility.service_enabled", return_value=False),
                    ):
                        navigation = portfolio_next_navigation(page)
                else:
                    navigation = portfolio_next_navigation(page)
                parser = _CardLinks()
                parser.feed(navigation)
                self.assertEqual(parser.navigator_count, 1)
                self.assertEqual(len(parser.links), 3)
                destinations = [a["href"].removeprefix("?page=") for a in parser.links]
                self.assertEqual(len(set(destinations)), 3)
                self.assertNotIn(page, destinations)
                self.assertTrue(all(a.get("target") == "_self" for a in parser.links))

    def test_compact_footer_is_full_width_and_responsive_in_every_shell(self):
        # The public, native and reader shells share one canonical stylesheet.
        self.assertIn("/* Portfolio-wide continuation footer", CSS)
        footer_css = CSS.split("/* Portfolio-wide continuation footer", 1)[1].split(
            "/* End shared portfolio continuation footer. */", 1
        )[0]
        self.assertIn(".site .portfolio-next>.container{", footer_css)
        self.assertIn("max-width:none;", footer_css)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr));", footer_css)
        self.assertIn("@media(min-width:721px)", footer_css)
        self.assertIn("@media(min-width:541px) and (max-width:720px)", footer_css)
        self.assertIn("@media(max-width:540px)", footer_css)
        self.assertIn("@media(min-device-width:541px) and (max-device-width:720px)", footer_css)
        self.assertNotIn("min-height:224px", footer_css)
        native = native_footer("analytics")
        self.assertIn("/* Portfolio-wide continuation footer", native)
        self.assertIn("(max-device-width:540px)", native)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr));", native)

    def test_service_availability_never_leaks_hidden_links(self):
        with (
            patch("advisory_service_visibility.viewer_is_admin", return_value=False),
            patch("advisory_service_visibility.service_enabled", return_value=False),
        ):
            public = portfolio_next_navigation("advisory")
        self.assertNotIn('href="?page=advisory-decision"', public)
        with (
            patch("advisory_service_visibility.viewer_is_admin", return_value=True),
            patch("advisory_service_visibility.service_enabled", return_value=True),
        ):
            admin = portfolio_next_navigation("advisory")
        self.assertIn('href="?page=advisory-decision"', admin)

    def test_articles_and_services_get_one_final_navigator(self):
        for page in self.PUBLIC_ROUTES:
            with self.subTest(page=page):
                base = '<nav>Header</nav><main><section>Content</section></main><footer>Site footer</footer>'
                if page == "advisory":
                    with patch("advisory_service_visibility.service_enabled", return_value=False), patch(
                        "advisory_service_visibility.viewer_is_admin", return_value=False
                    ):
                        decorated = inject_portfolio_continuation(base, page, article_slug="sample")
                else:
                    decorated = inject_portfolio_continuation(base, page, article_slug="sample")
                self.assertEqual(decorated.count('class="about-next portfolio-next"'), 1)
                self.assertLess(decorated.index('class="about-next portfolio-next"'), decorated.index('</main>'))
                self.assertLess(decorated.index('</main>'), decorated.index('<footer>'))
                self.assertEqual(inject_portfolio_continuation(decorated, page), decorated)

    def test_editorial_strip_stays_above_the_shared_footer(self):
        base = ('<main><section data-analytics-section="site-writing-footer">'
                'Editorial recommendation</section></main><footer>Footer</footer>')
        page = inject_portfolio_continuation(base, "briefing", article_slug="article-a")
        self.assertLess(page.index("site-writing-footer"), page.index("briefing-next-destinations"))

    def test_native_and_reader_accounts_use_the_same_markup(self):
        for page in ("analytics", "advisory-access"):
            html = native_footer(page)
            self.assertIn('class="about-next portfolio-next"', html)
            self.assertIn('aria-label="Continue exploring the portfolio"', html)
            self.assertIn('grid-template-columns:repeat(3,minmax(0,1fr))', html)
            self.assertLess(html.index('class="about-next portfolio-next"'), html.index('class="footer"'))
        self.assertIn('class="about-next portfolio-next"', reader_footer())
        locked = native_footer("analytics", navigation_locked=True)
        self.assertNotIn('href="?page=briefings"', locked)
        self.assertIn('aria-disabled="true"', locked)


if __name__ == "__main__":
    unittest.main()
