"""Guardrails for mobile presentation inside a legacy masked redirect."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from site_embedded_mobile import (
    EMBEDDED_MOBILE_SCRIPT,
    MASKED_FRAME_FALLBACK_CSS,
    READER_DIALOG_MOBILE_CSS,
    READER_DIALOG_MOBILE_SCRIPT,
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

    def test_masked_frame_has_css_fallback_even_if_javascript_does_not_run(self):
        # A 980px inner layout + physical phone width is the specific failure.
        css = MASKED_FRAME_FALLBACK_CSS
        self.assertIn("(min-width:760px) and (max-device-width:700px)", css)
        self.assertIn(".site:not(.native-shell):not(.reader-shell) {zoom:2.5}", css)
        self.assertIn(
            '[data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell)',
            css,
        )
        self.assertIn("(max-device-width:359px)", css)
        self.assertIn("(min-device-width:401px) and (max-device-width:430px)", css)
        self.assertIn("(min-device-width:601px) and (max-device-width:700px)", css)

    def test_css_fallback_mounts_in_public_and_native_experiences(self):
        from site_embedded_mobile import mount_masked_mobile_fix, mount_native_masked_mobile_fix
        from unittest.mock import patch
        with patch("site_embedded_mobile.st.html") as rendered:
            mount_masked_mobile_fix()
            self.assertEqual(rendered.call_count, 4)
            self.assertEqual(rendered.call_args_list[0].args[0], MASKED_FRAME_FALLBACK_CSS)
            self.assertEqual(rendered.call_args_list[1].args[0], READER_DIALOG_MOBILE_CSS)
            self.assertEqual(rendered.call_args_list[2].args[0], READER_DIALOG_MOBILE_SCRIPT)
            self.assertEqual(rendered.call_args_list[3].args[0], EMBEDDED_MOBILE_SCRIPT)
            self.assertTrue(rendered.call_args_list[3].kwargs["unsafe_allow_javascript"])
            rendered.reset_mock()
            mount_native_masked_mobile_fix()
            self.assertEqual(rendered.call_count, 4)
            self.assertEqual(rendered.call_args_list[0].args[0], MASKED_FRAME_FALLBACK_CSS)
            self.assertEqual(rendered.call_args_list[1].args[0], READER_DIALOG_MOBILE_CSS)
            self.assertEqual(rendered.call_args_list[2].args[0], READER_DIALOG_MOBILE_SCRIPT)
            self.assertIn(".native-shell-header", rendered.call_args_list[3].args[0])
            self.assertTrue(rendered.call_args_list[3].kwargs["unsafe_allow_javascript"])

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

    def test_reader_email_verification_has_phone_rules_inside_masked_frame(self):
        # The email callback opens ?page=readers, which renders reader_header
        # before native Streamlit forms. Its original CSS had only viewport
        # breakpoints, leaving the library desktop-sized in a 980px iframe.
        from unittest.mock import patch
        from site_reader_shell import reader_header

        with patch("streamlit.session_state", {"reader_native_session": None}):
            rendered = reader_header()
        self.assertIn(
            "@media(max-width:900px), (max-device-width:900px){", rendered,
        )
        self.assertIn(
            "@media(max-width:650px), (max-device-width:650px){", rendered,
        )
        self.assertIn(
            "@media(max-width:700px), (max-device-width:700px){", rendered,
        )
        self.assertIn(
            ".reader-shell .reader-hero-grid {grid-template-columns:minmax(0,1fr);gap:29px}",
            rendered,
        )
        self.assertIn(
            ".st-key-reader_flow [data-testid=\"stForm\"]{padding:7px 0 0!important}",
            rendered,
        )
        self.assertIn('class="mobile-menu-label">Menu</span></summary>', rendered)

    def test_reader_verification_removes_one_time_secret_before_rendering(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "page_reader_native.py").read_text(
            encoding="utf-8"
        )
        start = source.index("def render_reader_native() -> None:")
        body = source[start:]
        self.assertLess(
            body.index("_consume_query_verification()"),
            body.index("st.html(reader_header(staging=staging))"),
        )
        callback = source[source.index("def _consume_query_verification() -> None:"):]
        self.assertLess(
            callback.index('st.query_params.pop("token_hash", None)'),
            callback.index('user = _verify({"token_hash": token, "type": auth_type})'),
        )

    def test_all_streamlit_modals_share_the_same_mobile_scale(self):
        # Streamlit portals are not descendants of .site and should not rely
        # on a hidden marker that is present only in Reader dialogs.
        css = READER_DIALOG_MOBILE_CSS
        script = READER_DIALOG_MOBILE_SCRIPT
        self.assertIn('[data-testid="stDialog"] > div', css)
        self.assertIn('(max-width:700px), (max-device-width:700px)', css)
        self.assertIn('(min-width:760px) and (max-device-width:700px)', css)
        self.assertIn('zoom:var(--jr-modal-zoom)!important', css)
        self.assertIn('font-size:16px!important', css)
        self.assertIn('overflow-y:auto!important', css)
        self.assertIn('flex-wrap:wrap!important', css)
        self.assertIn('document.querySelectorAll(\'[data-testid="stDialog"]\')', script)
        self.assertIn("window.self !== window.top", script)
        self.assertIn("layout > physical * 1.45", script)
        self.assertIn("panel.style.setProperty('zoom', String(ratio), 'important')", script)
        self.assertIn("panel.style.setProperty('width', available + 'px', 'important')", script)
        self.assertIn("new MutationObserver(adaptDialog)", script)
        self.assertNotIn('jr-reader-dialog-marker', css)
        self.assertNotIn('jr-reader-dialog-marker', script)
        self.assertNotIn('token_hash', script)
        self.assertNotIn('access_token', script)

    def test_shared_modal_fix_loads_early_on_public_and_native_pages(self):
        from site_embedded_mobile import mount_reader_dialog_mobile_fix
        from unittest.mock import patch
        with patch('site_embedded_mobile.st.html') as rendered:
            mount_reader_dialog_mobile_fix()
        self.assertEqual(rendered.call_count, 2)
        self.assertEqual(rendered.call_args_list[0].args[0], READER_DIALOG_MOBILE_CSS)
        self.assertEqual(rendered.call_args_list[1].args[0], READER_DIALOG_MOBILE_SCRIPT)
        self.assertTrue(rendered.call_args_list[1].kwargs["unsafe_allow_javascript"])
        # The callback is mounted from the common page shell, before dialogs.
        from pathlib import Path
        src = (Path(__file__).resolve().parents[1] /
               'src' / 'site_embedded_mobile.py').read_text(encoding='utf-8')
        self.assertGreaterEqual(src.count('    mount_reader_dialog_mobile_fix()'), 2)
        native = (Path(__file__).resolve().parents[1] /
                  'src' / 'page_reader_native.py').read_text(encoding='utf-8')
        for name in ('_briefing_access_dialog', '_article_access_dialog',
                     '_weekly_ai_access_dialog', '_renewal_decision_dialog'):
            if 'def ' + name not in native:
                continue
            head = native.index('def ' + name + '(')
            body = native[head:native.find('\ndef ', head + 4)
                          if native.find('\ndef ', head + 4) > 0 else len(native)]
            self.assertIn('mount_reader_dialog_mobile_fix()', body)

    def test_phone_menu_replaces_wrapping_desktop_navigation(self):
        from site_components import MOBILE_NAV_CSS, nav
        self.assertIn("@media(max-width:700px), (max-device-width:700px)", MOBILE_NAV_CSS)
        self.assertIn("navin>.links{display:none!important}", MOBILE_NAV_CSS)
        markup = nav("advisory")
        self.assertIn('<details class="mobile-menu">', markup)
        self.assertIn('class="mobile-menu-links"', markup)
        self.assertIn('class="mobile-menu-label">Menu</span></summary>', markup)
        self.assertIn('flex-direction:row!important', MOBILE_NAV_CSS)
        self.assertIn('justify-content:space-between!important', MOBILE_NAV_CSS)
        self.assertIn('.site .nav .mobile-menu{display:block;position:relative;flex:0 0 44px', MOBILE_NAV_CSS)
        self.assertIn('margin-left:auto', MOBILE_NAV_CSS)
        self.assertIn('width:44px;min-width:44px;min-height:44px', MOBILE_NAV_CSS)
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
