"""Regression checks for Advisory account copy and authentic portrait delivery."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / "images" / "advisory-portrait.webp.b64"
PUBLIC_PAGE = ROOT / "src" / "page_public_services.py"
PORTAL = ROOT / "src" / "page_advisory_portal.py"


def test_advisory_portrait_asset_is_present_and_valid_webp():
    assert PHOTO.is_file(), "Advisory photo is missing from the repository"
    data = base64.b64decode(PHOTO.read_text(encoding="ascii").strip(), validate=True)
    assert len(data) > 6000
    assert data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def test_advisory_page_loads_the_committed_portrait_from_canonical_image_directory():
    source = PUBLIC_PAGE.read_text(encoding="utf-8")
    assert "from site_media import IMAGE_DIR" in source
    assert '"advisory-portrait.webp.b64"' in source
    assert '"data:image/webp;base64," + encoded_photo' in source
    assert '<img src="{photo}"' in source


def test_direct_advisory_account_language_is_consistent():
    page = PUBLIC_PAGE.read_text(encoding="utf-8")
    portal = PORTAL.read_text(encoding="utf-8")
    assert "Create a separate Advisory account" not in page
    assert "Create your advisory account to keep" in page
    assert ">Create your advisory account →</a>" in page
    assert "Create your advisory account to share" in portal
    assert '["Create your advisory account", "Sign in to advisory"]' in portal
