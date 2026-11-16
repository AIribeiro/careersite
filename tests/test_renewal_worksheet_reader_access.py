"""Regression coverage for authenticated Renewal Excel Decision Advisor."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class RenewalReaderAccessTests(unittest.TestCase):
    def test_full_reader_shows_excel_cta_before_artwork(self):
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
            html.index("Download Excel Decision Advisor (.xlsx)"),
            html.index('<figure id="artwork">'),
        )
        self.assertIn("worksheet=1", html)
        self.assertNotIn("fillable A4 record",html)

    def test_member_library_exposes_xlsx_only_with_verified_session(self):
        import page_reader_native as reader
        from briefing_renewal_excel import FILE_NAME,MIME
        session={"access_token":"unit-test-token"}
        user={"id":"test-verified-reader"}
        with patch.object(reader, "_session", return_value=(session,user)), \
             patch.object(reader.st,"download_button") as download:
            reader._renewal_worksheet_download(session,user,key="regression")
        download.assert_called_once()
        params=download.call_args.kwargs
        self.assertEqual(params["mime"],MIME)
        self.assertEqual(params["file_name"],FILE_NAME)
        self.assertTrue(params["data"].startswith(b"PK"))
        with ZipFile(BytesIO(params["data"])) as archive:
            self.assertIn("xl/workbook.xml",archive.namelist())
            self.assertIn("xl/worksheets/sheet3.xml",archive.namelist())
        self.assertEqual(params["on_click"],reader._record_worksheet_download)

    def test_anonymous_user_gets_no_workbook_bytes(self):
        import page_reader_native as reader
        with patch.object(reader,"_session",return_value=(None,None)), \
             patch.object(reader.st,"download_button") as download, \
             patch.object(reader.st,"info") as info:
            reader._renewal_worksheet_download(
                {"access_token":"stale"},{"id":"guest"},key="anonymous"
            )
        download.assert_not_called()
        info.assert_called_once()


if __name__=="__main__":
    unittest.main()
