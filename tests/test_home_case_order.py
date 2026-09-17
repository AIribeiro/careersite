from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeCaseOrderTests(unittest.TestCase):
    def test_volvo_leads_selected_home_cases(self) -> None:
        home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
        section = home.split('<p class="eyebrow">Selected leadership cases</p>', 1)[1]
        section = section.split('{framework_teaser()}', 1)[0]

        volvo = section.index('<span class="org">Volvo Group / Volvo Trucks</span>')
        msx = section.index('<span class="org">MSX International</span>')
        kimberly_clark = section.index('<span class="org">Kimberly-Clark</span>')
        ibm = section.index('<span class="org">IBM</span>')

        self.assertLess(volvo, msx)
        self.assertLess(msx, kimberly_clark)
        self.assertLess(kimberly_clark, ibm)
        self.assertIn("Across Volvo, MSX, Kimberly-Clark and IBM", section)


if __name__ == "__main__":
    unittest.main()
