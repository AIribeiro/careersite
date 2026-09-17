from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeCaseOrderTests(unittest.TestCase):
    def test_home_leads_with_three_modern_leadership_cases(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        section = home.split('<p class="eyebrow">Selected leadership cases</p>', 1)[1]
        section = section.split('<p class="eyebrow">Leadership focus</p>', 1)[0]

        volvo = section.index('<span class="org">Volvo Group / Volvo Trucks</span>')
        msx = section.index('<span class="org">MSX International</span>')
        kimberly_clark = section.index('<span class="org">Kimberly-Clark</span>')

        self.assertLess(volvo, msx)
        self.assertLess(msx, kimberly_clark)
        self.assertNotIn('<span class="org">IBM</span>', section)
        self.assertIn(
            "Across these roles, the context changed but the underlying questions became increasingly connected",
            section,
        )


if __name__ == "__main__":
    unittest.main()
