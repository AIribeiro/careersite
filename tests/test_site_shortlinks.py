"""Permanent, channel-specific short article links expand before analytics."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_shortlinks import expand_shortlink, registered_short_links, short_article_link, weekly_ai_short_link


class ShortArticleLinkTests(unittest.TestCase):
    def test_each_social_channel_has_an_owned_short_url_with_full_tracking(self):
        slug = "ai-is-turning-data-definitions-into-a-leadership-problem"
        channels = {
            "linkedin": ("dl", "social"),
            "x": ("dx", "social"),
            "threads": ("dt", "social"),
            "facebook": ("df", "social"),
            "whatsapp": ("dw", "messaging"),
        }
        for channel, (code, medium) in channels.items():
            with self.subTest(channel=channel):
                link = short_article_link(slug, channel)
                self.assertEqual(
                    link, "https://airibeiro.github.io/careersite/go/" + code + "/"
                )
                self.assertEqual(parse_qs(urlparse(link).query), {})
                self.assertEqual(
                    urlparse(link).path, "/careersite/go/" + code + "/"
                )
                target = expand_shortlink(code)
                self.assertEqual(target, {
                    "page": "thinking",
                    "article": slug,
                    "source": channel,
                    "role": "article",
                    "utm_source": channel,
                    "utm_medium": medium,
                    "utm_campaign": "thinking",
                    "utm_content": slug,
                })
                self.assertLess(len(link), 60)

    def test_next_experts_article_has_distinct_permanent_links(self):
        slug = "if-ai-does-the-routine-work-how-will-we-develop-the-next-experts"
        expected = {
            "linkedin": ("el", "social"),
            "x": ("ex", "social"),
            "threads": ("et", "social"),
            "facebook": ("ef", "social"),
            "whatsapp": ("ew", "messaging"),
        }
        for channel, (code, medium) in expected.items():
            with self.subTest(channel=channel):
                link = short_article_link(slug, channel)
                self.assertEqual(
                    link, "https://airibeiro.github.io/careersite/go/" + code + "/"
                )
                self.assertEqual(parse_qs(urlparse(link).query), {})
                self.assertEqual(
                    urlparse(link).path, "/careersite/go/" + code + "/"
                )
                self.assertEqual(expand_shortlink(code), {
                    "page": "thinking",
                    "article": slug,
                    "source": channel,
                    "role": "article",
                    "utm_source": channel,
                    "utm_medium": medium,
                    "utm_campaign": "thinking",
                    "utm_content": slug,
                })
                self.assertNotEqual(
                    link,
                    short_article_link(
                        "ai-is-turning-data-definitions-into-a-leadership-problem",
                        channel,
                    ),
                )

    def test_registered_static_redirect_targets_preserve_campaigns(self):
        rows = registered_short_links()
        self.assertGreaterEqual(len(rows), 21)
        for code, slug, channel, target in rows:
            with self.subTest(code=code):
                if code.startswith("w"):
                    params0 = parse_qs(urlparse(target).query)
                    found = weekly_ai_short_link(
                        slug, channel,
                        campaign=params0["utm_campaign"][0],
                        content=params0["utm_content"][0],
                    )
                else:
                    found = short_article_link(slug, channel)
                self.assertEqual(
                    found,
                    f"https://airibeiro.github.io/careersite/go/{code}/",
                )
                params = parse_qs(urlparse(target).query)
                self.assertEqual(params["page"], ["thinking"])
                self.assertEqual(params["article"], [slug])
                self.assertEqual(params["source"], [channel])
                self.assertEqual(params["utm_source"], [channel])
                if code.startswith("w"):
                    self.assertEqual(params["role"], ["weeklyai"])
                    self.assertTrue(params["utm_campaign"][0].startswith("weekly_ai_"))
                    self.assertTrue(params["utm_content"][0])
                else:
                    self.assertEqual(params["utm_campaign"], ["thinking"])
                    self.assertEqual(params["utm_content"], [slug])
                    self.assertEqual(params["role"], ["article"])

    def test_weekly_ai_registry_preserves_all_story_and_channel_attribution(self):
        slug = "weekly-ai-2026-10-11"
        campaign = "weekly_ai_2026_w41"
        stories = ["work_task_changes", "physical_ai", "agent_identity", "adoption_gap", "leadership_mindsets"]
        rows = [row for row in registered_short_links() if row[1] == slug]
        self.assertEqual(len(rows), 11)
        for position, story in enumerate(stories, 1):
            for channel, suffix in (("x", "x"), ("threads", "t")):
                expected = f"https://airibeiro.github.io/careersite/go/w202641{position}{suffix}/"
                self.assertEqual(
                    weekly_ai_short_link(slug, channel, campaign=campaign, content=story), expected
                )
                record = next(row for row in rows if row[0] == f"w202641{position}{suffix}")
                q = parse_qs(urlparse(record[3]).query)
                self.assertEqual(q["source"], [channel])
                self.assertEqual(q["utm_source"], [channel])
                self.assertEqual(q["utm_medium"], ["social"])
                self.assertEqual(q["utm_campaign"], [campaign])
                self.assertEqual(q["utm_content"], [story])
                self.assertEqual(q["role"], ["weeklyai"])
        self.assertEqual(
            weekly_ai_short_link(
                slug, "linkedin", campaign=campaign + "_wednesday",
                content="weekly_perspective",
            ),
            "https://airibeiro.github.io/careersite/go/w2026410l/",
        )
        self.assertIsNone(weekly_ai_short_link(slug, "x", campaign=campaign, content="unverified"))
        self.assertIsNone(weekly_ai_short_link(slug, "threads", campaign=campaign+"_wednesday", content="physical_ai"))

    def test_unregistered_or_attack_codes_do_not_resolve(self):
        for code in (None, "", "invalid", "../", "aa", "do", "dli", "dd",
                     "https://attacker.invalid", ["dl"]):
            with self.subTest(code=code):
                self.assertIsNone(expand_shortlink(code))
        self.assertIsNone(
            short_article_link("non-existent", "linkedin")
        )
        self.assertIsNone(
            short_article_link(
                "ai-is-turning-data-definitions-into-a-leadership-problem",
                "linkedin",
                campaign="dailyquote",
            )
        )
        self.assertIsNone(
            short_article_link(
                "ai-is-turning-data-definitions-into-a-leadership-problem",
                "linkedin",
                role="dailyquote",
            )
        )

    def test_streamlit_expands_code_before_route_selection_and_instrumentation(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertLess(
            source.index("SHORT_TARGET = expand_shortlink(SHORT_CODE)"),
            source.index('PAGE = st.query_params.get("page", "home")'),
        )
        self.assertLess(
            source.index("st.query_params.from_dict(SHORT_TARGET)"),
            source.index('PAGE = st.query_params.get("page", "home")'),
        )
        self.assertLess(
            source.index("st.query_params.from_dict(SHORT_TARGET)"),
            source.index("inject_article_analytics(PAGE"),
        )

    def test_streamlit_query_params_expansion_is_atomic(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_string(
            "import streamlit as st\n"
            "from site_shortlinks import expand_shortlink\n"
            "target = expand_shortlink(st.query_params.get('go', ''))\n"
            "if target is not None:\n"
            "    st.query_params.from_dict(target)\n"
            "st.write(st.query_params.get('article', 'missing'))\n"
        )
        at.query_params["go"] = "dl"
        at.run(timeout=15)
        self.assertFalse(at.exception)
        self.assertEqual(
            at.query_params.get("article"),
            ["ai-is-turning-data-definitions-into-a-leadership-problem"],
        )
        self.assertEqual(at.query_params.get("source"), ["linkedin"])
        self.assertEqual(at.query_params.get("utm_medium"), ["social"])
        self.assertNotIn("go", at.query_params)


if __name__ == "__main__":
    unittest.main()
