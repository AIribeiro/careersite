"""Free Executive AI Briefing public-preview quality and access contracts."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from briefing_reader_preview import opening_paragraphs, render_public_briefing_preview


class BriefingPublicPreviewTests(unittest.TestCase):
    @staticmethod
    def fixture():
        # The preview must come from the author's real article structure and
        # never invent a case study or expose the final editorial detail.
        html = (
            "<h2>The Leadership Decision</h2>"
            "<p><strong>Capacity is part of the approval decision.</strong> "
            "Before starting another enterprise AI initiative, record the "
            "business result, the actual allocated people and time, and what "
            "existing work can be stopped or delayed to deliver it. "
            "An attractive demonstration is not enough to approve delivery.</p>"
            "<p><strong>Next move:</strong> Put the active initiatives and "
            "their shared specialists in the same executive review. Ask the "
            "owners which commitments can realistically be delivered and which "
            "should pause rather than treating everyone's spare time as free.</p>"
            "<p>The supply of ideas is not the constraint. Teams, security "
            "reviews and domain experts are simultaneously involved in other "
            "work, and an overloaded portfolio may create little sustained "
            "business change even while its reports show a healthy pipeline.</p>"
            "<h2>Detailed operating framework</h2>"
            + "<p>UNLOCKED_ONLY_DETAIL_4382 operational framework with proof, "
              "baseline and domain ownership. " + ("Only available to a verified "
              "reader with full article access. " * 16) + "</p>"
            + '<figure><img src="https://example.com/premium-infographic.webp"/></figure>'
        )
        return SimpleNamespace(
            slug="capacity-is-the-real-constraint",
            title="Capacity Is the Real Constraint",
            subtitle="Deciding which AI work the business can genuinely deliver.",
            excerpt="A leadership decision about the commitments behind AI.",
            content_html=html,
        )

    def test_anonymous_cms_reader_never_receives_full_html(self):
        from unittest.mock import patch
        from site_cms import CmsArticle, render_cms_article

        article = self.fixture()
        stored = CmsArticle(
            id="test-article",
            slug=article.slug,
            title=article.title,
            subtitle=article.subtitle,
            content_html=article.content_html,
            kind="Executive Briefing",
            status="published",
        )
        with (
            patch("site_cms._public_reads_or_none", return_value=None),
            patch("site_cms.article_read_metadata", return_value="November 2026"),
            patch("site_cms.reader_header_image_src", return_value=""),
            patch("site_cms.fetch_published_articles", return_value=()),
            patch("page_reader_native._session", return_value=(None, None)),
        ):
            page = render_cms_article(stored)
        self.assertIn("The Leadership Decision", page)
        self.assertIn("A decision to put to work", page)
        self.assertIn("Continue with the full briefing", page)
        self.assertNotIn("UNLOCKED_ONLY_DETAIL_4382", page)
        self.assertNotIn("premium-infographic.webp", page)

    def test_substantive_editorial_preview_excludes_full_edition(self):
        article = self.fixture()
        opening = opening_paragraphs(article.content_html)
        self.assertGreaterEqual(len(opening), 2)
        self.assertIn("Capacity is part of the approval decision", opening[0])
        self.assertTrue(any("shared specialists" in p for p in opening))
        self.assertNotIn("UNLOCKED_ONLY_DETAIL_4382", " ".join(opening))
        html = render_public_briefing_preview(article, "November 2026")
        self.assertIn("The Leadership Decision", html)
        self.assertIn("A decision to put to work", html)
        self.assertIn("Capacity is part of the approval decision", html)
        self.assertIn("shared specialists", html)
        self.assertIn("Continue with the full briefing", html)
        self.assertIn("A4 PDF", html)
        self.assertNotIn("UNLOCKED_ONLY_DETAIL_4382", html)
        self.assertNotIn("premium-infographic.webp", html)
        self.assertNotIn("<figure", html)

    def test_free_signup_and_returning_reader_preserve_the_specific_edition(self):
        html = render_public_briefing_preview(self.fixture())
        self.assertIn(
            "?page=briefing&amp;article=capacity-is-the-real-constraint&amp;access=1",
            html,
        )
        self.assertIn("access=1&amp;signin=1", html)
        self.assertIn("No payment details", html)
        self.assertIn("Editorial email updates are optional", html)

    def test_cms_does_not_render_full_article_to_anonymous_visitor(self):
        # The real CMS renderer must branch BEFORE rendering the full article;
        # a CSS-covered article is not a valid access gate.
        from site_cms import CmsArticle, render_cms_article
        article = CmsArticle(
            title="Capacity Is the Real Constraint",
            slug="capacity-is-the-real-constraint",
            status="published",
            kind="Executive Briefing",
            header_image_url="https://example.com/safe-cover.webp",
            subtitle="Senior leadership choices about finite capacity.",
            content_html=self.fixture().content_html,
        )
        with (
            patch("page_reader_native._session", return_value=(None, None)),
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("site_cms.fetch_published_articles", return_value=()),
        ):
            public_html = render_cms_article(article)
        self.assertIn("Capacity is part of the approval decision", public_html)
        self.assertIn("Continue with the full briefing", public_html)
        self.assertNotIn("UNLOCKED_ONLY_DETAIL_4382", public_html)
        self.assertNotIn("premium-infographic.webp", public_html)

    def test_verified_reader_gets_full_cms_article_path(self):
        # For verified sessions only, use the complete existing editorial
        # renderer including the original briefing's unique infographic.
        from site_cms import CmsArticle, render_cms_article
        article = CmsArticle(
            title="Capacity Is the Real Constraint",
            slug="capacity-is-the-real-constraint",
            status="published",
            kind="Executive Briefing",
            header_image_url="https://example.com/safe-cover.webp",
            subtitle="Senior leadership choices about finite capacity.",
            content_html=self.fixture().content_html,
        )
        with (
            patch("page_reader_native._session", return_value=({"access_token":"test"}, {"id":"reader"})),
            patch("site_cms._public_reads_or_none", return_value={}),
            patch("site_cms.fetch_published_articles", return_value=()),
            patch("page_executive_briefings.executive_briefing_article", return_value="VERIFIED_COMPLETE_EDITORIAL_CONTENT") as full,
        ):
            html = render_cms_article(article)
        self.assertTrue(full.called)
        self.assertIn("VERIFIED_COMPLETE_EDITORIAL_CONTENT", html)

    def test_edition_benefits_come_from_real_section_titles(self):
        html = render_public_briefing_preview(self.fixture())
        self.assertIn("Inside the complete edition", html)
        self.assertIn("Detailed operating framework", html)
        self.assertNotIn("Made-up case study", html)

    def test_unlabelled_opening_is_not_misrepresented_as_decision(self):
        article = self.fixture()
        article.content_html = (
            "<h2>Why the project stalls</h2>"
            "<p>Unallocated specialists can slow an otherwise useful delivery. "
            "A compelling demonstration does not establish the receiving "
            "process, the work to stop, or the resources that must be reserved "
            "before a dependable service can be built and maintained.</p>"
            "<p>Ask the process owner which commitments are funded, which "
            "staff have time reserved, and which operating work will change "
            "when the service becomes part of normal business activity.</p>"
            + "<p>" + ("A complete edition must supply supporting evidence. " * 30) + "</p>"
        )
        html = render_public_briefing_preview(article)
        self.assertIn("<h2>The executive perspective</h2>", html)
        self.assertNotIn("<h2>The Leadership Decision</h2>", html)
        self.assertNotIn("A decision to put to work", html)

    def test_missing_body_uses_published_summary_not_invented_claim(self):
        article = self.fixture()
        article.content_html = ""
        article.excerpt = "The author's published description of this executive decision."
        html = render_public_briefing_preview(article)
        self.assertIn("The author&#x27;s published description", html)
        self.assertNotIn("The executive question starts with", html)

    def test_markup_escaped_and_preview_short_for_short_editions(self):
        article = self.fixture()
        article.title = '<script>alert("leak")</script>'
        article.content_html = (
            "<p>" + ("Material about a current business decision and owner. " * 30) + "</p>"
            "<p>" + ("Private operational guidance and evidence only. " * 30) + "</p>"
        )
        rendered = render_public_briefing_preview(article)
        self.assertNotIn('<script>alert("leak")', rendered)
        self.assertIn("&lt;script&gt;", rendered)
        opening = opening_paragraphs(article.content_html)
        self.assertLess(
            sum(len(p.split()) for p in opening),
            len(" ".join(opening).split()) + 1,
        )
        self.assertLess(
            sum(len(p.split()) for p in opening),
            len(" ".join(["Material about a current business decision and owner. " * 30,
                          "Private operational guidance and evidence only. " * 30]).split()),
        )


if __name__ == "__main__":
    unittest.main()
