"""Native Advisory and password-reset responsiveness contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


class AdvisoryMobileTests(unittest.TestCase):
    def test_native_mobile_script_scales_entire_form_not_only_public_html(self):
        from site_embedded_mobile import NATIVE_EMBEDDED_MOBILE_SCRIPT
        script=NATIVE_EMBEDDED_MOBILE_SCRIPT
        self.assertIn('[data-testid="stAppViewContainer"]',script)
        self.assertIn(".native-shell-header",script)
        self.assertIn("window.screen && window.screen.width",script)
        self.assertIn("framed && physical >= 280",script)
        self.assertIn("viewport > physical * 1.45",script)
        self.assertIn("app.style.zoom = String(ratio)",script)
        self.assertIn("'width', physical + 'px'",script)
        self.assertIn("orientationchange",script)
        self.assertIn("app.style.removeProperty('zoom')",script)

    def test_native_css_supports_phone_viewport_or_masked_device_width(self):
        from site_native_shell import native_header
        result=native_header("advisory-access")
        self.assertIn("@media(max-width:620px), (max-device-width:620px)",result)
        self.assertIn(".st-key-native_advisory_content [data-testid=\"stForm\"]",result)
        self.assertIn("flex-direction:column!important",result)
        self.assertIn("min-height:47px",result)
        self.assertIn("overflow-x:auto",result)

    def test_mobile_fix_is_mounted_in_advisory_password_and_analytics_views(self):
        for file in ("src/page_advisory_portal.py","main.py"):
            body=(ROOT/file).read_text(encoding="utf-8")
            ast.parse(body,filename=file)
            self.assertIn("mount_native_masked_mobile_fix()",body)
        portal=(ROOT/"src/page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertLess(portal.index('st.html(native_footer("advisory-access"))'),
                        portal.index("mount_native_masked_mobile_fix()"))

    def test_advisory_grid_phone_rules_are_last_and_frame_aware(self):
        from page_public_services import SERVICES_CSS
        from site_embedded_mobile import support_masked_mobile_media
        self.assertGreater(
            SERVICES_CSS.rfind('@media(max-width:850px)'),
            SERVICES_CSS.index('.site .advisory-hero-grid{grid-template-columns:minmax(0,1.26fr)')
        )
        responsive = support_masked_mobile_media(SERVICES_CSS)
        self.assertIn('@media(max-width:850px), (max-device-width:850px)', responsive)
        self.assertIn('@media(max-width:620px), (max-device-width:620px)', responsive)
        self.assertIn('grid-template-columns:minmax(0,1fr)', responsive)
        self.assertIn('.site .advisory-hero-grid{grid-template-columns:minmax(0,1fr);gap:29px}', responsive)
        # Retain the original premium Advisory buttons: wrapped, not full-width cards.
        self.assertIn('.site .advisory-actions{display:flex;align-items:center;gap:22px;flex-wrap:wrap;', responsive)
        self.assertNotIn('.site .advisory-actions .advisory-button{display:flex;width:100%', responsive)

    def test_password_recovery_form_has_no_hard_coded_desktop_columns(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(
            str(ROOT/"tests"/"advisory_password_setup_smoke_app.py"),
            default_timeout=30,
        ).run()
        self.assertFalse(app.exception,[str(x.message) for x in app.exception])
        labels=[x.label for x in app.text_input]
        self.assertIn("New or existing password",labels)
        self.assertIn("Confirm password",labels)
        self.assertFalse(app.columns if hasattr(app,"columns") else False)


if __name__=="__main__":
    unittest.main()
