from __future__ import annotations

import json
from urllib import error, request

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL

ANALYTICS_SESSION_COOKIE = "jair_analytics_admin_session"
ANALYTICS_SESSION_COOKIE_MAX_AGE = 10 * 365 * 24 * 60 * 60
ISSUE_SESSION_RPC = "careersite_analytics_issue_session"
REVOKE_SESSION_RPC = "careersite_analytics_revoke_session"


def _rpc(name: str, payload: dict[str, object]) -> dict:
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{name}"
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "apikey": ANALYTICS_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in {400, 401, 403}:
            raise ValueError("Invalid analytics access code.") from exc
        raise RuntimeError(f"Analytics authentication returned HTTP {exc.code}: {body[:180]}") from exc
    except error.URLError as exc:
        raise RuntimeError("Analytics authentication is temporarily unreachable.") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected analytics authentication response.")
    return data


def issue_admin_session(access_code: str) -> str:
    data = _rpc(ISSUE_SESSION_RPC, {"p_token": access_code})
    token = str(data.get("session_token") or "").strip()
    if len(token) < 40:
        raise RuntimeError("Analytics authentication did not return a valid session.")
    return token


def revoke_admin_session(session_token: str) -> bool:
    if not session_token:
        return False
    try:
        data = _rpc(REVOKE_SESSION_RPC, {"p_session_token": session_token})
    except (ValueError, RuntimeError):
        return False
    return bool(data.get("revoked"))
