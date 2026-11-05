from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class HomeEmployerStripTests(unittest.TestCase):
    def test_all_five_actual_employers_are_present(self) -> None:
        from home_employer_strip import EMPLOYERS, home_employer_strip
        self.assertEqual(len(EMPLOYERS), 5)
        html = home_employer_strip()
        for name in (
            "MSX International", "Volvo Group", "Kimberly-Clark",
            "IBM", "Hewlett Packard Enterprise",
        ):
            with self.subTest(name=name):
                self.assertIn(name, html)
        self.assertEqual(html.count('class="career-employer career-employer--'), 5)

    def test_home_position_is_between_hero_and_whats_new(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        hero = home.index('<section class="hero">')
        strip = home.index('{home_employer_strip()}')
        whats_new = home.index('{home_whats_new()}')
        self.assertLess(hero, strip)
        self.assertLess(strip, whats_new)

    def test_lightweight_responsive_and_accessible(self) -> None:
        from home_employer_strip import home_employer_strip
        html = home_employer_strip()
        self.assertIn('aria-labelledby="career-employers-title"', html)
        self.assertIn('@media(max-width:760px)', html)
        self.assertIn('@media(max-width:440px)', html)
        self.assertNotIn("base64,", html)
        self.assertNotIn("javascript:", html)
        self.assertEqual(html.count('loading="lazy"'), 5)


if __name__ == "__main__":
    unittest.main()
