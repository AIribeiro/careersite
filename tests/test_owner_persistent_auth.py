"""Browser-persistent Supabase owner auth regression tests."""
from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import site_owner_persistence as persist
import site_owner_http_auth as httpauth


class FakeRequest:
    def __init__(self,method="GET",action="login",destination="analytics",
                 origin="https://testserver",data=None,cookies=None):
        self.method=method
        self.path_params={"action":action}
        self.query_params={"next":destination}
        self.headers={"origin":origin,"content-type":"application/x-www-form-urlencoded"}
        self.url=SimpleNamespace(hostname="testserver")
        self.cookies=cookies or {}
        self._data=data or {}

    async def body(self):
        return urlencode(self._data).encode("utf-8")


class PersistentAuthTests(unittest.TestCase):
    def setUp(self):
        self.good_session={
            "access_token":"test-access-token",
            "refresh_token":"test-refresh-token",
            "expires_at":int(time.time())+3600,
            "user":{"email":"jair.ribeiro@outlook.it"},
        }

    def test_http_login_sets_secure_httponly_owner_cookies(self):
        with patch.object(httpauth,"owner_signin",return_value=self.good_session) as signin:
            response=asyncio.run(httpauth.owner_auth_route(FakeRequest(
                method="POST",action="login",data={"password":"correct-owner-password"})))
        self.assertEqual(response.status_code,303)
        self.assertEqual(response.headers["location"],"/?page=analytics")
        self.assertEqual(signin.call_args.args,("correct-owner-password",))
        cookies=response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies),3)
        for value in cookies:
            self.assertIn("httponly",value.lower())
            self.assertIn("secure",value.lower())
            self.assertIn("samesite=lax",value.lower())
            self.assertIn("path=/",value.lower())
            self.assertIn("max-age=",value.lower())
        self.assertIn("no-store",response.headers["cache-control"])

    def test_invalid_login_rejected_without_cookie(self):
        with patch.object(httpauth,"owner_signin",side_effect=RuntimeError("Wrong password")):
            response=asyncio.run(httpauth.owner_auth_route(FakeRequest(
                method="POST",action="login",data={"password":"wrong"})))
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.headers.getlist("set-cookie"),[])
        self.assertNotIn("Wrong password",response.body.decode())

    def test_cross_site_post_cannot_login_or_logout(self):
        req=FakeRequest(method="POST",action="login",
                        origin="https://attacker.example",data={"password":"whatever"})
        with patch.object(httpauth,"owner_signin") as signin:
            response=asyncio.run(httpauth.owner_auth_route(req))
        self.assertEqual(response.status_code,403)
        signin.assert_not_called()
        res=asyncio.run(httpauth.owner_auth_route(
            FakeRequest(method="POST",action="logout",
                        origin="https://attacker.example",
                        cookies={persist.ACCESS_COOKIE:"token"})))
        self.assertEqual(res.status_code,403)

    def test_refresh_rotates_cookie_and_redirects(self):
        req=FakeRequest(action="refresh",cookies={
            persist.REFRESH_COOKIE:"old-refresh-token",
        })
        with patch.object(httpauth,"owner_refresh",return_value=self.good_session) as refresh:
            response=asyncio.run(httpauth.owner_auth_route(req))
        self.assertEqual(refresh.call_args.args,("old-refresh-token",))
        self.assertEqual(response.status_code,303)
        self.assertIn("/?page=analytics",response.headers["location"])
        self.assertTrue(any("test-refresh-token" in c for c in response.headers.getlist("set-cookie")))

    def test_invalid_refresh_clears_cookies_and_requires_new_login(self):
        req=FakeRequest(action="refresh",cookies={
            persist.REFRESH_COOKIE:"revoked",
        })
        with patch.object(httpauth,"owner_refresh",side_effect=RuntimeError("revoked")):
            response=asyncio.run(httpauth.owner_auth_route(req))
        self.assertEqual(response.status_code,303)
        self.assertIn("/owner-auth/login",response.headers["location"])
        self.assertEqual(len(response.headers.getlist("set-cookie")),3)
        self.assertTrue(all("Max-Age=0" in c or "max-age=0" in c for c in
                            response.headers.getlist("set-cookie")))

    def test_logout_revokes_and_clears_all_cookies(self):
        req=FakeRequest(method="POST",action="logout",cookies={
            persist.ACCESS_COOKIE:"access-for-logout",
            persist.REFRESH_COOKIE:"refresh-for-logout",
        })
        with patch.object(httpauth,"_request_json",return_value=None) as revoke:
            response=asyncio.run(httpauth.owner_auth_route(req))
        self.assertEqual(response.status_code,204)
        self.assertEqual(len(response.headers.getlist("set-cookie")),3)
        self.assertTrue(all("Max-Age=0" in c or "max-age=0" in c for c in
                            response.headers.getlist("set-cookie")))
        self.assertIn("/auth/v1/logout",revoke.call_args.args[1])

    def test_expired_access_still_revokes_refresh_session_on_logout(self):
        req=FakeRequest(method="POST",action="logout",cookies={
            persist.ACCESS_COOKIE:"expired-access",
            persist.REFRESH_COOKIE:"working-refresh",
        })
        calls=[]
        def revoke(method,url,*,token=None,payload=None):
            calls.append((method,url,token))
            if len(calls)==1:
                raise RuntimeError("expired")
            return None
        with patch.object(httpauth,"_request_json",side_effect=revoke), \\
             patch.object(httpauth,"owner_refresh",return_value=self.good_session) as refresh:
            response=asyncio.run(httpauth.owner_auth_route(req))
        self.assertEqual(response.status_code,204)
        refresh.assert_called_once_with("working-refresh")
        self.assertEqual(calls[0][2],"expired-access")
        self.assertEqual(calls[1][2],"test-access-token")
        self.assertEqual(len(response.headers.getlist("set-cookie")),3)

    def test_restoration_validates_owner_identity(self):
        cookies={
            persist.ACCESS_COOKIE:"known-access",
            persist.REFRESH_COOKIE:"known-refresh",
            persist.EXPIRY_COOKIE:str(int(time.time())+3600),
        }
        with patch.object(persist,"_cookies",return_value=cookies), \
             patch.object(persist.st,"session_state",{}), \
             patch.object(persist,"_request_json",return_value={
                 "email":"jair.ribeiro@outlook.it"
             }) as user:
            session=persist.persistent_owner_session()
        self.assertEqual(session["access_token"],"known-access")
        self.assertIn("/auth/v1/user",user.call_args.args[1])
        self.assertEqual(user.call_args.kwargs["token"],"known-access")

    def test_restoration_rejects_forged_owner_and_expired_access(self):
        cookies={
            persist.ACCESS_COOKIE:"arbitrary-access",
            persist.REFRESH_COOKIE:"known-refresh",
            persist.EXPIRY_COOKIE:str(int(time.time())+3600),
        }
        with patch.object(persist,"_cookies",return_value=cookies), \
             patch.object(persist.st,"session_state",{}), \
             patch.object(persist,"_request_json",return_value={
                 "email":"different@example.org"
             }):
            self.assertIsNone(persist.persistent_owner_session())
        cookies[persist.EXPIRY_COOKIE]=str(int(time.time())-30)
        with patch.object(persist,"_cookies",return_value=cookies), \
             patch.object(persist.st,"session_state",{}), \
             patch.object(persist,"_request_json") as user:
            self.assertIsNone(persist.persistent_owner_session())
            user.assert_not_called()

    def test_unrecognized_destination_cannot_open_redirect(self):
        req=FakeRequest(action="login",destination="https://outside.example")
        response=asyncio.run(httpauth.owner_auth_route(req))
        self.assertNotIn("outside.example",response.body.decode())
        self.assertIn("action=\"/owner-auth/login?next=analytics\"",response.body.decode())


if __name__=="__main__":
    unittest.main()
