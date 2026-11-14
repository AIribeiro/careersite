"""Guardrails for mobile presentation inside a legacy masked redirect."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from site_embedded_mobile import (
    EMBEDDED_MOBILE_SCRIPT,
    support_masked_mobile_media,
)


class MaskedForwardingMobileTests(unittest.TestCase):
    def test_existing_css_mobile_rules_still_apply_in_normal_viewports(self):
        css = ".layout{display:grid}@media(max-width:700px){.layout{display:block}}"
        result = support_masked_mobile_media(css)
        self.assertIn("@media(max-width:700px), (max-device-width:700px){", result)
        self.assertIn(".layout{display:block}", result)

    def test_only_simple_width_media_queries_are_extended(self):
        css = (
            "@media(min-width:701px) and (max-width:980px){.x{color:red}}"
            "@media(max-width:520px){.x{color:blue}}"
            "@media(prefers-reduced-motion:reduce){.x{transition:none}}"
        )
        result = support_masked_mobile_media(css)
        self.assertIn(
            "@media(min-width:701px) and (max-width:980px){",
            result,
        )
        self.assertIn(
            "@media(max-width:520px), (max-device-width:520px){",
            result,
        )
        self.assertIn(
            "@media(prefers-reduced-motion:reduce){",
            result,
        )

    def test_fix_is_restricted_to_oversized_embedded_phone_viewports(self):
        self.assertIn("window.self !== window.top", EMBEDDED_MOBILE_SCRIPT)
        self.assertIn("deviceWidth <= 720", EMBEDDED_MOBILE_SCRIPT)
        self.assertIn("layoutWidth > deviceWidth * 1.45", EMBEDDED_MOBILE_SCRIPT)
        self.assertIn('site.style.removeProperty("zoom")', EMBEDDED_MOBILE_SCRIPT)
        self.assertNotIn("window.top.document", EMBEDDED_MOBILE_SCRIPT)

    def test_phone_canvas_is_explicit_before_public_zoom(self):
        # A 980px frame plus zoom on an auto-sized element collapses the
        # Advisory grid into an unreadable narrow column.
        self.assertIn('site.style.setProperty("width", deviceWidth + "px", "important")',
                      EMBEDDED_MOBILE_SCRIPT)
        self.assertIn('site.style.setProperty("min-width", "0", "important")',
                      EMBEDDED_MOBILE_SCRIPT)
        self.assertIn('site.style.removeProperty("width")', EMBEDDED_MOBILE_SCRIPT)
        self.assertLess(
            EMBEDDED_MOBILE_SCRIPT.index('site.style.setProperty("width", deviceWidth'),
            EMBEDDED_MOBILE_SCRIPT.index('site.style.zoom = String(scale)')
        )

    def test_page_specific_styles_are_adapted_for_masked_frames(self):
        main = (Path(__file__).resolve().parents[1] / "main.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("responsive_document = support_masked_mobile_media(page_document)", main)
        self.assertIn("responsive_document + '</div>'", main)

    def test_phone_menu_replaces_wrapping_desktop_navigation(self):
        from site_components import MOBILE_NAV_CSS, nav
        self.assertIn("@media(max-width:700px), (max-device-width:700px)", MOBILE_NAV_CSS)
        self.assertIn("navin>.links{display:none!important}", MOBILE_NAV_CSS)
        markup = nav("advisory")
        self.assertIn('<details class="mobile-menu">', markup)
        self.assertIn('class="mobile-menu-links"', markup)
        self.assertIn('Menu</summary>', markup)
        self.assertEqual(markup.count('href="?page=thinking"'), 2)

    def test_main_mounts_after_public_site_html_only(self):
        main = (Path(__file__).resolve().parents[1] / "main.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("support_masked_mobile_media(CSS + IMAGE_CSS + pathway_css)", main)
        self.assertIn("mount_masked_mobile_fix()", main)
        self.assertLess(
            main.index("st.html(support_masked_mobile_media("),
            main.index("    mount_masked_mobile_fix()"),
        )


if __name__ == "__main__":
    unittest.main()
