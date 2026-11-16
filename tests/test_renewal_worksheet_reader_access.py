"""Regression coverage for authenticated Renewal Challenge resources."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class RenewalReaderAccessTests(unittest.TestCase):
    def test_full_reader_shows_worksheet_before_artwork(self):
        import page_executive_briefings as briefing
        article = SimpleNamespace(
            slug="would-you-fund-the-same-ai-initiatives-today",
            title="Would You Fund the Same AI Initiatives Today?",
            subtitle="Reassess the next AI investment.",
            excerpt="Compare options.",
            content_html="<h2>Application</h2><p>Test.</p>",
        )
        with patch.object(briefing, "_article_infographic", return_value='<figure id="artwork"></figure>'), \
             patch.object(briefing, "nav", return_value=""), \
             patch.object(briefing, "footer", return_value=""), \
             patch.object(briefing, "contact_block", return_value=""):
            html = briefing.executive_briefing_article(
                article, "", "", "", "", "", ""
            )
        self.assertEqual(html.count('data-analytics-section="briefing-decision-record"'), 1)
        self.assertLess(
            html.index("Download fillable A4 Executive Decision Record"),
            html.index('<figure id="artwork">'),
        )
        self.assertIn("worksheet=1", html)

    def test_member_library_download_exposes_actual_pdf_with_verified_session(self):
        import page_reader_native as reader
        from pypdf import PdfReader
        from io import BytesIO

        session = {"access_token": "unit-test-token"}
        user = {"id": "test-verified-reader"}
        with patch.object(reader, "_session", return_value=(session, user)), \
             patch.object(reader.st, "download_button") as download:
            reader._renewal_worksheet_download(session, user, key="regression")
        download.assert_called_once()
        kwargs = download.call_args.kwargs
        self.assertEqual(kwargs["mime"], "application/pdf")
        self.assertEqual(kwargs["file_name"], "AI_Portfolio_Renewal_Executive_Decision_Record.pdf")
        self.assertTrue(kwargs["data"].startswith(b"%PDF-"))
        self.assertEqual(len(PdfReader(BytesIO(kwargs["data"])).get_fields()), 8)
        self.assertEqual(kwargs["on_click"], reader._record_worksheet_download)

    def test_anonymous_member_download_cannot_expose_bytes(self):
        import page_reader_native as reader
        with patch.object(reader, "_session", return_value=(None, None)), \
             patch.object(reader.st, "download_button") as download, \
             patch.object(reader.st, "info") as info:
            reader._renewal_worksheet_download(
                {"access_token": "stale"}, {"id": "guest"}, key="anonymous"
            )
        download.assert_not_called()
        info.assert_called_once()


if __name__ == "__main__":
    unittest.main()
