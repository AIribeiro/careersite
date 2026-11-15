"""Member cookie endpoints shared by Premium Reader and Executive Advisory.

Supabase Auth remains the identity provider. The member's own Supabase
RLS policies still decide whether individual Advisory services are available.
The server never trusts user metadata as an Advisory authorization grant.
"""
from __future__ import annotations

import time
from urllib.parse import parse_qs, urlsplit

from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse, Response

from reader_membership import _refresh, _verified_user
from site_analytics import ANALYTICS_URL
from site_cms import _request_json, _rest_url
from site_member_tickets import redeem_member_cookie_ticket

ACCESS_COOKIE = "__Secure-jair_member_access"
REFRESH_COOKIE = "__Secure-jair_member_refresh"
EXPIRY_COOKIE = "__Secure-jair_member_exp"
COOKIE_AGE = 60 * 24 * 60 * 60
REFRESH_HEADROOM = 90
FIRST_PARTY_HOSTS = frozenset(("jairribeiro.com", "advisory.jairribeiro.com"))


def _cookie_domain(request) -> str | None:
    """Share a cookie across branded domains only when actually first-party.

    The Streamlit Cloud origin is deliberately host-only. A registrar's
    masked iframe cannot set a cookie for an unrelated browser origin.
    """
    host = str(request.url.hostname or "").lower()
    return "jairribeiro.com" if host in FIRST_PARTY_HOSTS else None


def _cookie_options(request) -> dict:
    return {
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "path": "/",
        "max_age": COOKIE_AGE,
        **({"domain": _cookie_domain(request)} if _cookie_domain(request) else {}),
    }


def _no_store(response: Response) -> Response:
    response.headers.update({
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Robots-Tag": "noindex,nofollow,noarchive",
    })
    return response


def _set_session(response: Response, request, session: dict) -> Response:
    access = str(session.get("access_token") or "")
    refresh = str(session.get("refresh_token") or "")
    expiry = int(session.get("expires_at") or (
        time.time() + int(session.get("expires_in") or 0)
    ))
    if not access or not refresh or expiry <= time.time():
        raise ValueError("Supabase returned an incomplete session.")
    opts = _cookie_options(request)
    for name, value in (
        (ACCESS_COOKIE, access), (REFRESH_COOKIE, refresh),
        (EXPIRY_COOKIE, str(expiry)),
    ):
        response.set_cookie(name, value, **opts)
    return _no_store(response)


def _clear(response: Response, request) -> Response:
    domain = _cookie_domain(request)
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, EXPIRY_COOKIE):
        response.delete_cookie(
            name, path="/", secure=True, httponly=True, samesite="lax",
            **({"domain": domain} if domain else {}),
        )
    return _no_store(response)


def _same_origin(request) -> bool:
    if str(request.headers.get("sec-fetch-site") or "") == "cross-site":
        return False
    origin = str(request.headers.get("origin") or request.headers.get("referer") or "")
    if origin:
        parsed = urlsplit(origin)
        return (
            parsed.scheme == "https"
            and (parsed.hostname or "").lower() ==
            str(request.url.hostname or "").lower()
            and parsed.port in (None, 443)
        )
    return request.headers.get("sec-fetch-site") == "same-origin"


async def _read_form(request, limit: int = 1024) -> dict[str, str]:
    try:
        size = int(request.headers.get("content-length") or "0")
    except (ValueError, TypeError):
        size = limit + 1
    if size > limit:
        raise ValueError("Request too large.")
    body = await request.body()
    if len(body) > limit:
        raise ValueError("Request too large.")
    data = parse_qs(body.decode("utf-8", "replace"), max_num_fields=4)
    return {key: value[0] for key, value in data.items() if len(value) == 1}


def _verified_member(token: str) -> dict:
    user = _verified_user(token)
    if not isinstance(user, dict) or not user.get("email_confirmed_at"):
        raise RuntimeError("Account verification is required.")
    state = _request_json(
        "POST", _rest_url("rpc/portfolio_reader_member_status_v1"),
        token=token, payload={}, timeout=10,
    )
    if state != "active":
        raise RuntimeError("Reader account access is unavailable.")
    return user


async def member_auth_route(request) -> Response:
    """Same-origin cookie attachment, renewal and joint member sign-out."""
    action = str(request.path_params.get("action") or "")
    if request.method != "POST":
        return _no_store(Response("Method not allowed", status_code=405))
    if not _same_origin(request):
        return _no_store(Response("Forbidden", status_code=403))

    if action == "attach":
        try:
            payload = await _read_form(request)
            session = redeem_member_cookie_ticket(str(payload.get("ticket") or ""))
            if not session:
                return _no_store(JSONResponse({"saved": False}, status_code=401))
            token = str(session["access_token"])
            await run_in_threadpool(_verified_member, token)
            return _set_session(JSONResponse({"saved": True}), request, session)
        except (RuntimeError, ValueError, TimeoutError, KeyError, TypeError):
            return _no_store(JSONResponse({"saved": False}, status_code=401))

    if action == "bootstrap":
        access = str(request.cookies.get(ACCESS_COOKIE) or "")
        refresh = str(request.cookies.get(REFRESH_COOKIE) or "")
        try:
            expiry = int(request.cookies.get(EXPIRY_COOKIE) or 0)
        except (ValueError, TypeError):
            expiry = 0
        if not refresh:
            return _no_store(JSONResponse({"authenticated": False}, status_code=401))
        try:
            if not access or expiry <= time.time() + REFRESH_HEADROOM:
                # Supabase refresh tokens rotate. Only the HTTP response writes
                # the replacement; no refresh token crosses browser JavaScript.
                session = await run_in_threadpool(_refresh, refresh)
                await run_in_threadpool(_verified_member, str(session["access_token"]))
                expires = int(session.get("expires_at") or (
                    time.time() + int(session.get("expires_in") or 0)
                ))
                result = JSONResponse({
                    "authenticated": True,
                    "access_token": str(session["access_token"]),
                    "expires_at": expires,
                })
                return _set_session(result, request, session)
            await run_in_threadpool(_verified_member, access)
            return _no_store(JSONResponse({
                "authenticated": True, "access_token": access,
                "expires_at": expiry,
            }))
        except (RuntimeError, ValueError, TimeoutError, KeyError, TypeError):
            # Do not clear cookies on a failed refresh: another browser tab
            # might have rotated this shared token concurrently. Fail closed.
            return _no_store(JSONResponse({"authenticated": False}, status_code=401))

    if action == "logout":
        # The server clears persistent credentials even if Supabase logout
        # cannot be completed. The in-page client also revokes its own token.
        token = str(request.cookies.get(ACCESS_COOKIE) or "")
        if token:
            try:
                await run_in_threadpool(
                    _request_json, "POST",
                    ANALYTICS_URL.rstrip("/") + "/auth/v1/logout?scope=local",
                    token=token, payload={}, timeout=10,
                )
            except (RuntimeError, TimeoutError, ValueError, KeyError):
                pass
        return _clear(JSONResponse({"signed_out": True}), request)

    return _no_store(Response("Not found", status_code=404))
