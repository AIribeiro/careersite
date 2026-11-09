"""Regression checks for the About page's publicly delivered photography."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_about import FAMILY_PHOTOS, _family_gallery
from site_media import PUBLIC_IMAGE_BASE


def test_family_gallery_files_are_committed():
    for name, _alt, _width, _height, _kind in FAMILY_PHOTOS:
        asset = ROOT / "images" / name
        assert asset.is_file(), f"Missing About photograph: {name}"
        assert asset.stat().st_size > 10_000, f"Empty About photograph: {name}"


def test_family_gallery_uses_canonical_public_media_not_app_route():
    gallery = _family_gallery()
    assert gallery.count("<figure ") == 3
    assert gallery.count("<img ") == 3
    assert gallery.count(PUBLIC_IMAGE_BASE) == 3
    assert "/portfolio-image/" not in gallery
    assert "srcset=" not in gallery
    for name, alt, _width, _height, _kind in FAMILY_PHOTOS:
        assert name in gallery
        assert f'alt="{alt}"' in gallery
