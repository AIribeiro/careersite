"""Google Search Console ownership verification remains scoped to public Pages."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.google_search_console_verification import prepare


class GoogleSearchConsoleVerificationTests(unittest.TestCase):
    def test_unconfigured_is_noop(self):
        with TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "index.html").write_text("<html><head></head><body>Homepage</body></html>")
            self.assertFalse(prepare(folder)["configured"])
            self.assertEqual(len(list(folder.iterdir())), 1)

    def test_google_file_and_meta_proofs_without_mutating_other_pages(self):
        with TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "index.html").write_text("<html><head></head><body>Homepage</body></html>")
            discovery = folder / "discover/index.html"
            discovery.parent.mkdir()
            discovery.write_text("<html><head></head><body>Discovery</body></html>")
            name = "google0123456789abcdef.html"
            token = "abcdefghijklmnopqrstuvwxyz123456"
            result = prepare(folder, file_name=name, meta_token=token)
            self.assertTrue(result["configured"])
            self.assertEqual(
                (folder / name).read_text(),
                "google-site-verification: google0123456789abcdef.html\n"
            )
            self.assertIn('name="google-site-verification"', (folder / "index.html").read_text())
            self.assertIn(token, discovery.read_text())
            first = (folder / "index.html").read_text()
            prepare(folder, file_name=name, meta_token=token)
            self.assertEqual(first, (folder / "index.html").read_text())
            self.assertIn("Homepage", first)

    def test_invalid_proof_fails_closed(self):
        with TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "index.html").write_text("<html><head></head></html>")
            for filename in ("../google0123456789abcdef.html", "googleabc.html", "other0123456789abcdef.html"):
                with self.assertRaises(ValueError):
                    prepare(folder, file_name=filename)
            with self.assertRaises(ValueError):
                prepare(folder, meta_token='x" onload="evil')
            self.assertEqual(len(list(folder.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
