"""Keep the three About photographs at identical visual heights on every screen."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_about import FAMILY_PHOTOS, _family_gallery
from site_styles import CSS


def _family_styles() -> str:
    return CSS.split("/* About photography: one shared visual height", 1)[1].split(
        "/* About: multilingual leadership.", 1
    )[0]


def test_three_photos_use_same_height_variable_at_all_breakpoints():
    gallery = _family_gallery()
    css = _family_styles()
    assert gallery.count('<figure class="about-family-photo ') == 3
    assert len(FAMILY_PHOTOS) == 3
    # All figures receive a single common height, with one responsive override
    # to the variable rather than independent, inconsistent item heights.
    assert ".site .about-family-photo{" in css
    assert "height:var(--about-photo-height)" in css
    assert css.count("--about-photo-height:") == 2
    assert "height:auto" not in css
    assert "max-height:" not in css


def test_desktop_uses_aspect_aware_three_column_grid():
    css = _family_styles()
    assert "grid-template-columns:minmax(0,1.333fr) minmax(0,.667fr) minmax(0,.512fr)" in css
    assert "object-fit:cover" in css
    assert "align-items:stretch" in css


def test_mobile_keeps_full_photos_at_equal_height_in_swipe_gallery():
    css = _family_styles()
    assert "@media(max-width:620px)" in css
    assert "display:flex" in css
    assert "overflow-x:auto" in css
    assert "scroll-snap-type:x mandatory" in css
    assert "object-fit:contain" in css
    assert "aspect-ratio:1448/1086" in css
    assert "aspect-ratio:1024/1536" in css
    assert "aspect-ratio:1431/2798" in css


def test_original_images_and_accessible_descriptions_unchanged():
    gallery = _family_gallery()
    assert gallery.startswith('<div class="about-family-gallery"')
    for filename, alt, width, height, kind in FAMILY_PHOTOS:
        assert filename in gallery
        assert f'alt="{alt}"' in gallery
        assert f'width="{width}" height="{height}"' in gallery
        assert f"about-family-photo--{kind}" in gallery
