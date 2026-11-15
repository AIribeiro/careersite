"""Security and behavior tests for persistent Reader / Advisory sessions.

These tests use fake user identities and Supabase results only; no live account
tokens are required. They exercise HTTP cookie constraints, rotating refresh
tokens, sign-out behavior, one-use escrow, and the native Streamlit bridge.
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import site_member_http_auth as auth
import site_member_tickets as tickets


class FakeRequest:
    def __init__(self, *, action="bootstrap", method="POST", host="jairribeiro.com",
                 origin=None, form=None, cookies=None, fetch_site="same-origin"):
        self.method = method
        self.path_params = {"action": action}
        self.query_params = {}
        self.url = SimpleNamespace(hostname=host)
        self.headers = {
            "origin": origin if origin is not None else "https://" + host,
            "sec-fetch-site": fetch_site,
            "content-type": "application/x-www-form-urlencoded",
        }
        self.cookies = cookies or {}
        self._form = form or {}

    async def body(self):
        return urlencode(self._form).encode("utf-8")


def run(request: FakeRequest):
    return asyncio.run(auth.member_auth_route(request))


class MemberContinuityTests(unittest.TestCase):
    def setUp(self):
        self.session = {
            "access_token": "verified-access-not-real",
            "refresh_token": "verified-refresh-not-real",
            "expires_at": int(time.time()) + 3600,
        }
        self.user = {
            "id": "00000000-0000-4000-8000-000000000001",
            "email": "member@example.org",
            "email_confirmed_at": "2026-11-15T11:00:00Z",
        }

    def test_source_modules_parse_and_server_route_is_registered(self):
        for path in (
            "src/site_member_http_auth.py",
            "src/site_member_persistence.py",
            "src/site_member_tickets.py",
            "src/page_reader_native.py",
            "main.py", "app.py",
        ):
            ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('Route("/member-auth/{action}", member_auth_route, methods=["POST"])', app)

    def test_one_time_ticket_expires_and_is_not_redeemable_twice(self):
        token = tickets.issue_member_cookie_ticket(self.session, self.user)
        self.assertIsNone(tickets.redeem_member_cookie_ticket("bad"))
        self.assertEqual(tickets.redeem_member_cookie_ticket(token), self.session)
        self.assertIsNone(tickets.redeem_member_cookie_ticket(token))
        with self.assertRaises(ValueError):
            tickets.issue_member_cookie_ticket(self.session, {"id": self.user["id"]})

    def test_attached_cookies_are_httponly_secure_and_share_branded_origin(self):
        ticket = tickets.issue_member_cookie_ticket(self.session, self.user)
        with patch.object(auth, "_verified_member", return_value=self.user) as check:
            response = run(FakeRequest(action="attach", form={"ticket": ticket}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, b'{"saved":true}')
        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 3)
        for cookie in cookies:
            self.assertIn("httponly", cookie.lower())
            self.assertIn("secure", cookie.lower())
            self.assertIn("samesite=lax", cookie.lower())
            self.assertIn("domain=jairribeiro.com", cookie.lower())
            self.assertIn("path=/", cookie.lower())
        self.assertIn("no-store", response.headers["cache-control"])
        check.assert_called_once_with(self.session["access_token"])

    def test_streamlit_origin_cookies_remain_host_only(self):
        ticket = tickets.issue_member_cookie_ticket(self.session, self.user)
        with patch.object(auth, "_verified_member", return_value=self.user):
            response = run(FakeRequest(
                action="attach", host="jairribeiro-ai.streamlit.app",
                form={"ticket": ticket},
            ))
        self.assertTrue(all("domain=" not in c.lower()
                            for c in response.headers.getlist("set-cookie")))

    def test_cross_site_mutations_and_get_are_forbidden(self):
        response = run(FakeRequest(
            action="attach", origin="https://attacker.example",
            form={"ticket": "untrusted"},
        ))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(run(FakeRequest(action="bootstrap", method="GET")).status_code, 405)
        self.assertEqual(run(FakeRequest(
            action="logout", fetch_site="cross-site",
        )).status_code, 403)

    def test_bootstrap_returns_only_one_use_server_ticket(self):
        cookie = {
            auth.ACCESS_COOKIE: self.session["access_token"],
            auth.REFRESH_COOKIE: self.session["refresh_token"],
            auth.EXPIRY_COOKIE: str(self.session["expires_at"]),
        }
        with patch.object(auth, "_verified_member", return_value=self.user):
            response = run(FakeRequest(cookies=cookie))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"authenticated":true', response.body)
        self.assertNotIn(self.session["access_token"].encode(), response.body)
        self.assertNotIn(self.session["refresh_token"].encode(), response.body)
        self.assertEqual(response.headers.getlist("set-cookie"), [])
        import json
        ticket = json.loads(response.body)["restore_ticket"]
        restored = tickets.redeem_member_restore_ticket(ticket)
        self.assertEqual(restored["access_token"], self.session["access_token"])
        self.assertEqual(restored["expires_at"], self.session["expires_at"])
        self.assertIsNone(tickets.redeem_member_restore_ticket(ticket))

    def test_bootstrap_rotates_refresh_in_http_only_cookie(self):
        cookie = {
            auth.ACCESS_COOKIE: "old-access",
            auth.REFRESH_COOKIE: "old-refresh",
            auth.EXPIRY_COOKIE: str(int(time.time()) - 10),
        }
        with (
            patch.object(auth, "_refresh", return_value=self.session) as rotate,
            patch.object(auth, "_verified_member", return_value=self.user),
        ):
            response = run(FakeRequest(cookies=cookie))
        rotate.assert_called_once_with("old-refresh")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.session["refresh_token"].encode(), response.body)
        self.assertNotIn(self.session["access_token"].encode(), response.body)
        self.assertTrue(any(self.session["refresh_token"] in cookie
                            for cookie in response.headers.getlist("set-cookie")))

    def test_invalid_session_never_restores_and_signout_clears_cookies(self):
        with patch.object(auth, "_verified_member", side_effect=RuntimeError("suspended")):
            denied = run(FakeRequest(cookies={
                auth.ACCESS_COOKIE: self.session["access_token"],
                auth.REFRESH_COOKIE: self.session["refresh_token"],
                auth.EXPIRY_COOKIE: str(self.session["expires_at"]),
            }))
        self.assertEqual(denied.status_code, 401)
        self.assertNotIn(b"access_token", denied.body)
        with patch.object(auth, "_request_json", return_value=None) as revoke:
            signed_out = run(FakeRequest(
                action="logout", cookies={auth.ACCESS_COOKIE: "member-access"},
            ))
        self.assertEqual(signed_out.status_code, 200)
        self.assertEqual(len(signed_out.headers.getlist("set-cookie")), 3)
        self.assertTrue(all("max-age=0" in cookie.lower()
                            for cookie in signed_out.headers.getlist("set-cookie")))
        self.assertIn("/auth/v1/logout", revoke.call_args.args[1])

    def test_bridge_never_persists_refresh_token_in_browser_storage(self):
        source = (ROOT / "src/site_member_persistence.py").read_text(encoding="utf-8")
        self.assertIn("'/member-auth/bootstrap'", source)
        self.assertIn("'/member-auth/attach'", source)
        self.assertIn("'/member-auth/logout'", source)
        self.assertIn("st.session_state[\"reader_native_session\"] = session", source)
        self.assertIn('"_cookie_backed": True', source)
        self.assertNotIn("localStorage.setItem", source)
        self.assertNotIn("sessionStorage.setItem", source)
        self.assertNotIn("refresh_token: result.", source)
        self.assertNotIn("access_token: result.", source)
        self.assertIn("redeem_member_restore_ticket", source)
        native = (ROOT / "src/page_reader_native.py").read_text(encoding="utf-8")
        self.assertIn("queue_member_session_cookie(session, user)", native)
        self.assertIn("begin_member_browser_signout()", native)
        self.assertIn('if session.get("_cookie_backed")', native)


if __name__ == "__main__":
    unittest.main()
