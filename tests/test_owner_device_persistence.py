"""Browser-reopen session restoration and Supabase refresh lifecycle.

No real tokens leave tests. Cover the preferred cookie route failing, owner
validation, revoked sessions, token renewal and logout clearing.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import site_owner_persistence as owner
from site_owner_device_persistence import _DEVICE_JS


def session(token="old-refresh", seconds=3600):
    return {
        "access_token": "access-" + token,
        "refresh_token": token,
        "expires_at": int(time.time()) + seconds,
        "user": {"email": owner.OWNER_EMAIL},
    }


class OwnerDevicePersistenceTests(unittest.TestCase):
    def test_browser_reopen_uses_saved_token_when_cookies_are_absent(self):
        state = {}
        stored = SimpleNamespace(
            restored={"refresh_token":"saved-refresh-token","saved_at":1234,"read_nonce":0},
            status="available"
        )
        fresh = session("rotated-refresh-token")
        with (
            patch.object(owner.st, "session_state", state),
            patch.object(owner, "_cookies", return_value={}),
            patch.object(owner, "_restore_component", return_value=SimpleNamespace(session=None)),
            patch.object(owner, "_device_component", return_value=stored) as component,
            patch.object(owner, "owner_refresh", return_value=fresh) as refresh,
            patch.object(owner, "_verify_owner_access",
                         return_value={"email":owner.OWNER_EMAIL}) as verify,
            patch.object(owner.st,"rerun") as rerun,
        ):
            result = owner.persistent_owner_session()
        self.assertEqual(result["refresh_token"],"rotated-refresh-token")
        self.assertEqual(state["cms_auth"]["refresh_token"],"rotated-refresh-token")
        refresh.assert_called_once_with("saved-refresh-token")
        verify.assert_called_once_with("access-rotated-refresh-token")
        self.assertEqual(component.call_args.kwargs["data"]["mode"],"read")
        rerun.assert_called_once()

    def test_authenticated_session_writes_rotating_refresh_to_browser(self):
        current=session("new-token",3600)
        state={"cms_auth":current}
        with (
            patch.object(owner.st, "session_state", state),
            patch.object(owner, "_persist_browser_cookies_if_requested"),
            patch.object(owner, "_device_component",
                         return_value=SimpleNamespace(status="stored")) as browser,
        ):
            got = owner.persistent_owner_session()
        self.assertIs(got,current)
        browser.assert_called_once()
        data=browser.call_args.kwargs["data"]
        self.assertEqual(data["mode"],"write")
        self.assertEqual(data["refresh_token"],"new-token")
        self.assertNotIn("access_token",data)
        self.assertNotIn("password",data)

    def test_revoked_refresh_token_is_cleared_not_retried(self):
        state={}
        cached=SimpleNamespace(restored={"refresh_token":"revoked-long-refresh-token","read_nonce":0},status="available")
        with (
            patch.object(owner.st,"session_state",state),
            patch.object(owner,"_cookies",return_value={}),
            patch.object(owner,"_restore_component",return_value=SimpleNamespace(session=None)),
            patch.object(owner,"_device_component",return_value=cached),
            patch.object(owner,"owner_refresh",side_effect=RuntimeError("invalid refresh")),
            patch.object(owner.st,"rerun") as rerun,
        ):
            self.assertIsNone(owner.persistent_owner_session())
        self.assertTrue(state["owner_device_clear_pending"])
        rerun.assert_called_once()

        with (
            patch.object(owner.st,"session_state",state),
            patch.object(owner,"_cookies",return_value={}),
            patch.object(owner,"_restore_component",return_value=SimpleNamespace(session=None)),
            patch.object(owner,"_device_component",return_value=SimpleNamespace(status="cleared",restored=cached.restored)) as browser,
            patch.object(owner,"owner_refresh") as refresh,
        ):
            self.assertIsNone(owner.persistent_owner_session())
        self.assertNotIn("owner_device_clear_pending",state)
        self.assertEqual(browser.call_args.kwargs["data"]["mode"],"clear")
        refresh.assert_not_called()

    def test_non_owner_token_is_rejected_on_browser_restore(self):
        state={}
        cached=SimpleNamespace(restored={"refresh_token":"not-the-owner-long-token","read_nonce":0},status="available")
        with (
            patch.object(owner.st,"session_state",state),
            patch.object(owner,"_cookies",return_value={}),
            patch.object(owner,"_restore_component",return_value=SimpleNamespace(session=None)),
            patch.object(owner,"_device_component",return_value=cached),
            patch.object(owner,"owner_refresh",return_value=session("non-owner")),
            patch.object(owner,"_verify_owner_access",return_value=None),
            patch.object(owner.st,"rerun"),
        ):
            self.assertIsNone(owner.persistent_owner_session())
        self.assertNotIn("cms_auth",state)
        self.assertTrue(state["owner_device_clear_pending"])

    def test_failed_cookie_bridge_does_not_disable_device_restoration(self):
        state={}
        cached=SimpleNamespace(restored={"refresh_token":"saved-device-refresh-token","read_nonce":0},status="available")
        with (
            patch.object(owner.st,"session_state",state),
            patch.object(owner,"_cookies",return_value={}),
            patch.object(owner,"_restore_component",side_effect=RuntimeError("cloud route blocked")),
            patch.object(owner,"_device_component",return_value=cached),
            patch.object(owner,"owner_refresh",return_value=session("fresh-device")),
            patch.object(owner,"_verify_owner_access",return_value={"email":owner.OWNER_EMAIL}),
            patch.object(owner.st,"rerun"),
        ):
            got=owner.persistent_owner_session()
        self.assertEqual(got["refresh_token"],"fresh-device")

    def test_expired_in_memory_session_renews_and_is_written(self):
        state={"cms_auth":session("old-expired",seconds=-10)}
        renewed=session("rotated",seconds=3600)
        with (
            patch.object(owner.st,"session_state",state),
            patch.object(owner,"ensure_owner_session",return_value=renewed),
            patch.object(owner,"issue_owner_cookie_ticket",return_value="random-ticket"),
            patch.object(owner,"_persist_browser_cookies_if_requested"),
            patch.object(owner,"_device_component",return_value=SimpleNamespace(status="stored")) as browser,
        ):
            result=owner.persistent_owner_session()
        self.assertEqual(result["refresh_token"],"rotated")
        self.assertEqual(browser.call_args.kwargs["data"]["refresh_token"],"rotated")

    def test_device_component_is_optional_for_existing_login(self):
        current=session("current-valid")
        with (
            patch.object(owner.st,"session_state",{"cms_auth":current}),
            patch.object(owner,"_persist_browser_cookies_if_requested"),
            patch.object(owner,"_device_component",side_effect=RuntimeError("blocked storage")),
        ):
            self.assertEqual(owner.persistent_owner_session()["access_token"],current["access_token"])

    def test_stale_component_generation_does_not_rotate(self):
        state={"owner_device_read_nonce":2}
        cached=SimpleNamespace(
            restored={"refresh_token":"older-device-credential",
                      "read_nonce":1},
            status="available"
        )
        with (
            patch.object(owner.st,"session_state",state),
            patch.object(owner,"_cookies",return_value={}),
            patch.object(owner,"_restore_component",return_value=SimpleNamespace(session=None)),
            patch.object(owner,"_device_component",return_value=cached),
            patch.object(owner,"owner_refresh") as rotate,
        ):
            self.assertIsNone(owner.persistent_owner_session())
            rotate.assert_not_called()
            self.assertNotIn("owner_device_clear_pending",state)

    def test_client_storage_never_contains_access_token_or_password(self):
        self.assertIn("localStorage.setItem",_DEVICE_JS)
        self.assertIn("localStorage.removeItem",_DEVICE_JS)
        self.assertIn("refresh_token",_DEVICE_JS)
        self.assertNotIn("access_token",_DEVICE_JS)
        self.assertNotIn("password",_DEVICE_JS)
        self.assertIn("if (window.__jairOwnerStorageAction === action) return",_DEVICE_JS)
        self.assertIn("localStorage.removeItem('jair_portfolio_owner_supabase_v1')",
                      owner._LOGOUT_JS)


if __name__ == "__main__":
    unittest.main()
