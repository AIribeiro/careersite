from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SocialBridgeAttributionTests(unittest.TestCase):
    def test_facebook_is_a_first_class_social_source(self) -> None:
        bridge = (ROOT / "scripts/build_linkedin_share_site.py").read_text(encoding="utf-8")

        self.assertIn("['linkedin', 'x', 'facebook', 'social']", bridge)
        self.assertIn("if (source === 'fb') source = 'facebook';", bridge)
        self.assertIn("ref.includes('facebook.com')", bridge)
        self.assertIn("ref.includes('fb.com')", bridge)
        self.assertIn("ref.includes('messenger.com')", bridge)
        self.assertIn("source === 'facebook' ? 'facebook_groups' : 'thinking'", bridge)
        self.assertIn("target.searchParams.set('utm_source', source)", bridge)
        self.assertIn("target.searchParams.set('utm_campaign', campaign)", bridge)

    def test_social_crawlers_are_not_redirected_as_human_readers(self) -> None:
        bridge = (ROOT / "scripts/build_linkedin_share_site.py").read_text(encoding="utf-8")

        self.assertIn("facebookexternalhit", bridge)
        self.assertIn("linkedinbot", bridge)
        self.assertIn("twitterbot", bridge)


if __name__ == "__main__":
    unittest.main()
