"""Same-origin HTTP auth routes for long-lived CMS + Analytics sessions.

Credentials only cross HTTPS in POST bodies and HttpOnly, Secure, SameSite=Lax
cookies. Refresh-token rotation occurs in an HTTP response so the persistent
browser cookie always follows Supabase's current refresh token.
"""
from __future__ import annotations

from html import escape
import time
from urllib.parse import parse_qs, urlsplit

from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from site_cms import OWNER_EMAIL, _request_json, owner_refresh, owner_signin
from site_owner_persistence import (
    ACCESS_COOKIE, EXPIRY_COOKIE, REFRESH_COOKIE, ALLOWED_DESTINATIONS,
)
from site_analytics import ANALYTICS_URL

# Expires after 365 days without renewing; signing in again remains possible.
# Supabase revocation/refresh-token expiration takes precedence.
COOKIE_AGE_SECONDS = 365 * 24 * 60 * 60
COOKIE_OPTIONS = {
    "max_age":COOKIE_AGE_SECONDS,
    "httponly":True,
    "secure":True,
    "samesite":"lax",
    "path":"/",
}


def _destination(request) -> str:
    requested = str(request.query_params.get("next") or "analytics").lower()
    return requested if requested in ALLOWED_DESTINATIONS else "analytics"


def _after(destination: str) -> str:
    return f"/?page={destination}"


def _no_store(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Robots-Tag"] = "noindex,nofollow,noarchive"
    return response


def _clear(response: Response) -> Response:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, EXPIRY_COOKIE):
        response.delete_cookie(name,path="/",secure=True,httponly=True,samesite="lax")
    return _no_store(response)


def _set_session(response: Response, session: dict) -> Response:
    access = str(session.get("access_token") or "")
    refresh = str(session.get("refresh_token") or "")
    expires = int(session.get("expires_at") or
                  (time.time() + int(session.get("expires_in") or 0)))
    if not access or not refresh or expires <= time.time():
        raise ValueError("Supabase authentication response was incomplete.")
    for name,value in ((ACCESS_COOKIE,access),(REFRESH_COOKIE,refresh),(EXPIRY_COOKIE,str(expires))):
        response.set_cookie(name,value,**COOKIE_OPTIONS)
    return _no_store(response)


def _same_origin_post(request) -> bool:
    # Non-GET mutations require the same-origin browser request. A browser
    # without Origin can use Referer; Sec-Fetch-Site must not be cross-site.
    if request.headers.get("sec-fetch-site","") == "cross-site":
        return False
    origin = request.headers.get("origin") or request.headers.get("referer") or ""
    if not origin:
        return False
    p = urlsplit(origin)
    hostname = (p.hostname or "").lower()
    return hostname == str(request.url.hostname or "").lower() and p.scheme == "https"


def _signin_html(destination: str, *, failed: bool = False) -> HTMLResponse:
    notice = ('<p role="alert" class="error">Sign-in failed. Check your password and try again.</p>'
              if failed else "")
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Private sign-in | Portfolio</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;background:#f4f0e8;color:#10131a;
min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0}}
main{{background:#fffdfa;border:1px solid #ddd4c7;padding:30px;
max-width:380px;width:calc(100% - 50px)}}
h1{{font:500 2rem Georgia,serif;margin:0 0 8px}}
p{{color:#6f6a62}}label{{display:block;margin:18px 0 8px}}
input{{box-sizing:border-box;width:100%;padding:12px;font:inherit;border:1px solid #bbb}}
button{{margin-top:22px;padding:12px 20px;width:100%;background:#10131a;
color:white;border:0;font:inherit;cursor:pointer}}
.error{{color:#a33223}}
</style></head><body><main>
<h1>Portfolio owner sign-in</h1>
<p>One secure sign-in for Analytics and the CMS.</p>{notice}
<form method="post" action="/owner-auth/login?next={destination}" autocomplete="on">
<input type="hidden" name="next" value="{destination}">
<label for="owner_password">Password</label>
<input autofocus required autocomplete="current-password" type="password"
id="owner_password" name="password" minlength="1" maxlength="512">
<button type="submit">Sign in</button>
</form></main></body></html>"""
    response = HTMLResponse(html,status_code=401 if failed else 200)
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; style-src 'unsafe-inline'; "
        "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )
    return _no_store(response)


async def owner_auth_route(request) -> Response:
    action = str(request.path_params.get("action") or "")
    dest = _destination(request)

    if action == "login":
        if request.method == "GET":
            return _signin_html(dest)
        if request.method != "POST" or not _same_origin_post(request):
            return _no_store(Response("Forbidden",status_code=403))
        if int(request.headers.get("content-length") or "0") > 8192:
            return _no_store(Response("Request too large",status_code=413))
        body = await request.body()
        if len(body) > 8192:
            return _no_store(Response("Request too large",status_code=413))
        data = parse_qs(body.decode("utf-8",errors="replace"),keep_blank_values=True)
        password = str((data.get("password") or [""])[0])
        try:
            session = await run_in_threadpool(owner_signin,password)
            response = RedirectResponse(_after(dest),status_code=303)
            return _set_session(response,session)
        except (RuntimeError,ValueError,TimeoutError):
            return _signin_html(dest,failed=True)

    if action == "refresh":
        if request.method != "GET":
            return _no_store(Response("Method not allowed",status_code=405))
        old_refresh = str(request.cookies.get(REFRESH_COOKIE) or "")
        if not old_refresh:
            return _clear(RedirectResponse(f"/owner-auth/login?next={dest}",status_code=303))
        try:
            session = await run_in_threadpool(owner_refresh,old_refresh)
            user = session.get("user") if isinstance(session,dict) else None
            if not isinstance(user,dict) or str(user.get("email") or "").lower() != OWNER_EMAIL:
                # The refresh endpoint does not rely on an unchecked cookie identity.
                access = str(session.get("access_token") or "")
                actual = await run_in_threadpool(
                    _request_json,"GET",
                    f"{ANALYTICS_URL.rstrip('/')}/auth/v1/user", token=access
                )
                if not isinstance(actual,dict) or str(actual.get("email") or "").lower() != OWNER_EMAIL:
                    raise RuntimeError("Owner identity mismatch")
            return _set_session(RedirectResponse(_after(dest),status_code=303),session)
        except (RuntimeError,ValueError,TimeoutError):
            return _clear(RedirectResponse(f"/owner-auth/login?next={dest}",status_code=303))

    if action == "logout":
        if request.method != "POST" or not _same_origin_post(request):
            return _no_store(Response("Forbidden",status_code=403))
        access = str(request.cookies.get(ACCESS_COOKIE) or "")
        refresh = str(request.cookies.get(REFRESH_COOKIE) or "")
        if access or refresh:
            try:
                await run_in_threadpool(
                    _request_json,"POST",
                    f"{ANALYTICS_URL.rstrip('/')}/auth/v1/logout",
                    token=access,
                    payload={},
                )
            except (RuntimeError,TimeoutError):
                # An expired access token cannot revoke the refresh session.
                # Try a one-time refresh and log out the resulting access token.
                if refresh:
                    try:
                        newer = await run_in_threadpool(owner_refresh,refresh)
                        await run_in_threadpool(
                            _request_json,"POST",
                            f"{ANALYTICS_URL.rstrip('/')}/auth/v1/logout",
                            token=str(newer["access_token"]),
                            payload={},
                        )
                    except (RuntimeError,ValueError,KeyError,TimeoutError):
                        pass
        return _clear(Response(status_code=204))

    return _no_store(Response("Not found",status_code=404))
