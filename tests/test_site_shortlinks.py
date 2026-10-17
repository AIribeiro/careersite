"""Permanent, channel-specific short article links expand before analytics."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from site_shortlinks import expand_shortlink, short_article_link


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
                    link, "https://jairribeiro-ai.streamlit.app/?go=" + code
                )
                self.assertEqual(parse_qs(urlparse(link).query), {"go": [code]})
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
