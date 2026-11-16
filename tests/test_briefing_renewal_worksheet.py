from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from briefing_renewal_worksheet import (  # noqa: E402
    SLUG, build_decision_record_pdf, decision_record_cta_html,
)


class RenewalDecisionRecordTests(unittest.TestCase):
    def test_pdf_is_fillable_and_a4(self):
        binary = build_decision_record_pdf()
        self.assertTrue(binary.startswith(b"%PDF-"))
        pdf = PdfReader(BytesIO(binary), strict=True)
        self.assertEqual(len(pdf.pages), 1)
        self.assertAlmostEqual(float(pdf.pages[0].mediabox.width), 595.28, delta=1)
        self.assertAlmostEqual(float(pdf.pages[0].mediabox.height), 841.89, delta=1)
        self.assertEqual(set(pdf.get_fields() or {}), {
            "outcome", "incumbent", "alternative", "clean_sheet",
            "real_world", "decision", "owner", "next_gate",
        })

    def test_cta_targets_native_reader_dialog_not_public_pdf(self):
        html = decision_record_cta_html()
        self.assertIn("worksheet=1", html)
        self.assertIn("article=" + SLUG, html)
        self.assertIn("Download the fillable A4 decision record", html)
        self.assertNotIn(".pdf", html)
        self.assertNotIn("raw.githubusercontent.com", html)


if __name__ == "__main__":
    unittest.main()
