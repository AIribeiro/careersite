"""Free Executive AI Briefing public-preview quality and access contracts."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
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
