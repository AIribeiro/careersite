"""Short-lived one-time server escrow to attach browser cookies to a valid CMS login.

A verified in-app Supabase login yields a refresh token on the Streamlit server.
To save it in an HttpOnly cookie WITHOUT passing it to browser JavaScript,
the server issues a random, one-use, 60-second bearer ticket. The same-origin
Starlette endpoint redeems that ticket and writes cookie headers. No tokens,
emails, passwords or user data are written to disk, analytics or URLs.

Both Streamlit and Starlette run inside the same app process under app.py.
If a deployment uses separate processes or does not mount custom routes,
redemption fails closed while the normal in-app login remains functional.
"""
from __future__ import annotations

import secrets
import threading
import time

TTL_SECONDS = 60
MAX_PENDING = 128
_lock = threading.Lock()
_pending: dict[str,tuple[float,dict]] = {}


def issue_owner_cookie_ticket(session: dict) -> str:
    """Only call after Supabase has already confirmed the owner password."""
    if (not isinstance(session,dict) or not session.get("access_token")
            or not session.get("refresh_token")):
        raise ValueError("A verified refreshable Supabase session is required.")
    identity = session.get("user")
    if not isinstance(identity,dict) or str(identity.get("email") or "").casefold() != "jair.ribeiro@outlook.it":
        raise ValueError("A verified owner identity is required.")
    now = time.monotonic()
    ticket = secrets.token_urlsafe(32)
    with _lock:
        for key,(deadline,_) in tuple(_pending.items()):
            if deadline <= now:
                _pending.pop(key,None)
        if len(_pending)>=MAX_PENDING:
            oldest = min(_pending,key=lambda key:_pending[key][0])
            _pending.pop(oldest,None)
        _pending[ticket] = (now+TTL_SECONDS,dict(session))
    return ticket


def redeem_owner_cookie_ticket(ticket: str) -> dict | None:
    if not isinstance(ticket,str) or len(ticket)<32 or len(ticket)>128:
        return None
    with _lock:
        payload = _pending.pop(ticket,None)
    if not payload:
        return None
    deadline,session=payload
    return session if deadline > time.monotonic() else None
