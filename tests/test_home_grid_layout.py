from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeGridLayoutTests(unittest.TestCase):
    def test_home_uses_distinct_grids_for_cases_focus_and_references(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")

        cases = home.split('<p class="eyebrow">Selected leadership cases</p>', 1)[1]
        cases = cases.split('<p class="eyebrow">Leadership focus</p>', 1)[0]
        self.assertIn(
            'grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:18px',
            cases,
        )
        self.assertEqual(cases.count('<article class="card">'), 3)

        focus = home.split('<p class="eyebrow">Leadership focus</p>', 1)[1]
        focus = focus.split('{framework_teaser()}', 1)[0]
        self.assertIn('<div class="grid3">', focus)
        self.assertEqual(focus.count('<a class="card"'), 3)
        self.assertNotIn("AI Portfolio &amp; Business Value", focus)

        references = home.split('<p class="eyebrow">External perspective</p>', 1)[1]
        references = references.split('<section class="cta">', 1)[0]
        self.assertIn('<div class="principles">', references)
        self.assertEqual(references.count('<article class="principle">'), 4)


if __name__ == "__main__":
    unittest.main()
