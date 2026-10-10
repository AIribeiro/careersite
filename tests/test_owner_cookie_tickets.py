"""In-page sign-in becomes persistent without a redirect or exposing refresh tokens."""
from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from urllib.parse import urlencode
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

import site_owner_tickets as tickets
import site_owner_http_auth as http
import site_owner_persistence as persistent


class Request:
    method="POST"
    path_params={"action":"attach"}
    query_params={}
    headers={"origin":"https://jairribeiro-ai.streamlit.app",
             "content-type":"application/x-www-form-urlencoded"}
    url=SimpleNamespace(hostname="localhost")
    cookies={}

    def __init__(self,secret=""):
        self.secret=secret

    async def body(self):
        return urlencode({"ticket":self.secret}).encode()


class OneTimeTickets(unittest.TestCase):
    def setUp(self):
        self.session={
            "access_token":"valid-access",
            "refresh_token":"server-only-secret",
            "expires_at":int(time.time())+3600,
            "user":{"email":"jair.ribeiro@outlook.it"},
        }

    def test_one_time_no_replay(self):
        ticket=tickets.issue_owner_cookie_ticket(self.session)
        self.assertGreaterEqual(len(ticket),32)
        self.assertNotIn("server-only-secret",ticket)
        self.assertEqual(tickets.redeem_owner_cookie_ticket(ticket)["refresh_token"],"server-only-secret")
        self.assertIsNone(tickets.redeem_owner_cookie_ticket(ticket))

    def test_bad_owner_refused_and_token_expiry(self):
        other=dict(self.session,user={"email":"not-owner@example.com"})
        with self.assertRaises(ValueError):
            tickets.issue_owner_cookie_ticket(other)
        with patch.object(tickets.time,"monotonic",return_value=200):
            token=tickets.issue_owner_cookie_ticket(self.session)
        with patch.object(tickets.time,"monotonic",return_value=200+tickets.TTL_SECONDS+1):
            self.assertIsNone(tickets.redeem_owner_cookie_ticket(token))

    def test_attach_produces_httponly_cookies_without_exposing_refresh_token(self):
        ticket=tickets.issue_owner_cookie_ticket(self.session)
        with patch.object(http,"_request_json",return_value={"email":"jair.ribeiro@outlook.it"}):
            response=asyncio.run(http.owner_auth_route(Request(ticket)))
        self.assertEqual(response.status_code,200)
        self.assertIn('"saved":true',response.body.decode().lower())
        self.assertNotIn("server-only-secret",response.body.decode())
        self.assertEqual(len(response.headers.getlist("set-cookie")),3)
        self.assertTrue(all("httponly" in c.lower() and "secure" in c.lower()
                            for c in response.headers.getlist("set-cookie")))
        with patch.object(http,"_request_json"):
            again=asyncio.run(http.owner_auth_route(Request(ticket)))
        self.assertEqual(again.status_code,401)

    def test_attach_rejects_cross_origin(self):
        ticket=tickets.issue_owner_cookie_ticket(self.session)
        req=Request(ticket)
        req.headers={"origin":"https://evil.example"}
        res=asyncio.run(http.owner_auth_route(req))
        self.assertEqual(res.status_code,403)
        self.assertIsNotNone(tickets.redeem_owner_cookie_ticket(ticket))

    def test_legacy_password_form_no_longer_depends_on_blocked_link(self):
        from streamlit.testing.v1 import AppTest
        program="from site_owner_persistence import show_owner_login_or_refresh\nshow_owner_login_or_refresh('analytics')"
        app=AppTest.from_string(program).run(timeout=15)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.text_input),1)
        self.assertEqual(app.button[0].label,"Sign in")
        self.assertFalse(any("owner-auth/login" in m.value for m in app.markdown))

    def test_legacy_session_renews_without_cookies(self):
        old=dict(self.session,expires_at=int(time.time())-50)
        newer=dict(self.session,access_token="refreshed-access",
                   expires_at=int(time.time())+3600)
        with (
            patch.object(persistent.st,"session_state",{"cms_auth":old}),
            patch.object(persistent,"ensure_owner_session",return_value=newer),
            patch.object(persistent,"issue_owner_cookie_ticket",return_value="opaque-ticket"),
            patch.object(persistent,"_persist_browser_cookies_if_requested"),
        ):
            result=persistent.persistent_owner_session()
        self.assertEqual(result["access_token"],"refreshed-access")

    def test_signout_also_revokes_original_fallback_session(self):
        state={"cms_auth":dict(self.session)}
        with (
            patch.object(persistent.st,"session_state",state),
            patch.object(persistent,"ensure_owner_session",return_value=dict(self.session)),
            patch.object(persistent,"_request_json",return_value=None) as revoke,
            patch.object(persistent,"_logout_component",
                         return_value=SimpleNamespace(failed=False)),
            patch.object(persistent.st,"markdown"),
            patch.object(persistent.st,"caption"),
        ):
            persistent.browser_owner_signout()
        self.assertNotIn("cms_auth",state)
        self.assertIn("/auth/v1/logout",revoke.call_args.args[1])


if __name__=="__main__":
    unittest.main()
