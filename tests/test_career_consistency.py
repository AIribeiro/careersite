from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import sys
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from career_facts import (  # noqa: E402
    IBM_TITLE,
    KIMBERLY_TITLE,
    MSX_PUBLIC_DATES,
    MSX_PUBLIC_TIMELINE,
    MSX_TITLE,
    SELECTED_CREDENTIALS,
    VOLVO_AI_INITIATIVES,
    VOLVO_AI_LEARNING_SESSIONS,
    VOLVO_CURRENT_TITLE,
    VOLVO_WORKFLOW_SCOPE,
)


class CareerFactConsistencyTests(unittest.TestCase):
    @staticmethod
    def _pdf_text() -> str:
        import site_cv

        reader = PdfReader(BytesIO(site_cv.CV_BYTES), strict=True)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _public_source_text() -> str:
        paths = list(SRC.glob("page_*.py")) + [
            SRC / "site_cv.py",
            SRC / "site_assets.py",
            SRC / "site_components.py",
        ]
        return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())

    def test_public_msx_period_is_consistent(self) -> None:
        from page_about import about
        from page_impact import impact

        pdf_text = self._pdf_text()
        self.assertIn(MSX_PUBLIC_DATES, pdf_text)
        self.assertNotIn("Dec 2025 - Jun 2026", pdf_text)
        self.assertNotIn("Dec 2025 - Present", pdf_text)

        impact_html = impact()
        self.assertIn(MSX_PUBLIC_DATES.replace(" - ", " – "), impact_html)
        self.assertIn(MSX_PUBLIC_TIMELINE, about())

        public_source = self._public_source_text()
        self.assertIsNone(
            re.search(r"MSX.{0,160}Dec 2025\s*[-–]\s*Jun 2026", public_source, re.I | re.S),
            "Public MSX positioning must not drift back to a June 2026 end date.",
        )
        self.assertIsNone(
            re.search(r"MSX.{0,160}Present", public_source, re.I | re.S),
            "Public MSX positioning must not imply the role is current.",
        )

    def test_role_titles_and_scale_claims_match(self) -> None:
        from page_impact import impact

        pdf_text = self._pdf_text()
        for title in (MSX_TITLE, VOLVO_CURRENT_TITLE, KIMBERLY_TITLE, IBM_TITLE):
            self.assertIn(title, pdf_text)

        self.assertIn(f"{VOLVO_AI_INITIATIVES} AI initiatives", pdf_text)
        self.assertIn(f"{VOLVO_AI_INITIATIVES} AI initiatives", impact())

    def test_training_is_enablement_not_adoption_proof(self) -> None:
        from page_home import home
        from page_presence import presence

        pdf_text = self._pdf_text()
        self.assertIn(
            f"Delivered {VOLVO_AI_LEARNING_SESSIONS} AI learning sessions and training opportunities",
            pdf_text,
        )
        self.assertIn("strengthening AI literacy and the quality of business demand", pdf_text)
        self.assertIn(
            f"operational adoption of AI solutions and agents in {VOLVO_WORKFLOW_SCOPE} workflows",
            pdf_text.lower(),
        )

        presence_html = presence()
        self.assertIn("supporting enablement evidence", presence_html.lower())
        self.assertIn("operational adoption is evidenced separately", presence_html.lower())

        home_html = home()
        self.assertNotIn("reducing cycle time and cost while increasing practical use", home_html)
        self.assertIn("targeting cycle time, cost and practical adoption", home_html)

    def test_selected_credentials_exist_on_both_surfaces(self) -> None:
        from page_certifications import certifications

        pdf_text = self._pdf_text()
        cert_html = certifications()

        self.assertIn(SELECTED_CREDENTIALS[0], pdf_text)
        self.assertIn(SELECTED_CREDENTIALS[1], pdf_text)
        self.assertIn(SELECTED_CREDENTIALS[2], pdf_text)

        self.assertIn("EITCA/AI Artificial Intelligence Academy", cert_html)
        self.assertIn(SELECTED_CREDENTIALS[1], cert_html)
        self.assertIn(SELECTED_CREDENTIALS[2], cert_html)

    def test_high_risk_public_claims_have_single_source(self) -> None:
        cv_source = (SRC / "site_cv.py").read_text(encoding="utf-8")
        home_source = (SRC / "page_home.py").read_text(encoding="utf-8")
        about_source = (SRC / "page_about.py").read_text(encoding="utf-8")
        impact_source = (SRC / "page_impact.py").read_text(encoding="utf-8")

        self.assertIn("from career_facts import", cv_source)
        self.assertIn("from career_facts import", home_source)
        self.assertIn("from career_facts import", about_source)
        self.assertIn("from career_facts import", impact_source)


if __name__ == "__main__":
    unittest.main()
