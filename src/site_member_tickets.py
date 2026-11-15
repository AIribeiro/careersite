"""Short-lived, one-time server escrow for member HTTP-only cookie attachment.

The Streamlit process issues a random ticket only after a verified Reader /
Advisory login. The same-origin Starlette endpoint redeems it to install
Secure, HttpOnly cookies. Neither access nor refresh token is sent through
JavaScript, URL query strings, or persistent client-side storage at attach time.
"""
from __future__ import annotations

import secrets
import threading
import time

TTL_SECONDS = 45
MAX_PENDING = 192
_lock = threading.Lock()
_pending: dict[str, tuple[float, dict]] = {}


def issue_member_cookie_ticket(session: dict, user: dict) -> str:
    """Escrow only an already verified, refreshable session."""
    if (
        not isinstance(session, dict)
        or not str(session.get("access_token") or "")
        or not str(session.get("refresh_token") or "")
        or not isinstance(user, dict)
        or not str(user.get("id") or "")
        or not user.get("email_confirmed_at")
    ):
        raise ValueError("A verified member session is required.")
    ticket = secrets.token_urlsafe(32)
    now = time.monotonic()
    with _lock:
        for key, (deadline, _) in tuple(_pending.items()):
            if deadline <= now:
                _pending.pop(key, None)
        if len(_pending) >= MAX_PENDING:
            oldest = min(_pending, key=lambda key: _pending[key][0])
            _pending.pop(oldest, None)
        _pending[ticket] = (now + TTL_SECONDS, dict(session))
    return ticket


def redeem_member_cookie_ticket(ticket: str) -> dict | None:
    """A ticket can be redeemed only once and never after its deadline."""
    if not isinstance(ticket, str) or not 32 <= len(ticket) <= 128:
        return None
    with _lock:
        payload = _pending.pop(ticket, None)
    if payload is None:
        return None
    deadline, session = payload
    return session if deadline > time.monotonic() else None



# Access-only restoration uses a separate escrow: the verified browser's
# HttpOnly cookie remains the sole holder of the rotating refresh token.
_restores: dict[str, tuple[float, dict]] = {}


def issue_member_restore_ticket(access: str, expires_at: int, user: dict) -> str:
    """Return a one-use ticket after an HTTP cookie was independently checked."""
    if (
        not isinstance(access, str) or len(access) < 12
        or not isinstance(expires_at, int) or expires_at <= time.time()
        or not isinstance(user, dict) or not user.get("id")
        or not user.get("email_confirmed_at")
    ):
        raise ValueError("A verified, unexpired member access token is required.")
    ticket = secrets.token_urlsafe(32)
    now = time.monotonic()
    with _lock:
        for key, (deadline, _) in tuple(_restores.items()):
            if deadline <= now:
                _restores.pop(key, None)
        if len(_restores) >= MAX_PENDING:
            oldest = min(_restores, key=lambda key: _restores[key][0])
            _restores.pop(oldest, None)
        _restores[ticket] = (now + TTL_SECONDS, {
            "access_token": access, "expires_at": expires_at,
        })
    return ticket


def redeem_member_restore_ticket(ticket: str) -> dict | None:
    if not isinstance(ticket, str) or not 32 <= len(ticket) <= 128:
        return None
    with _lock:
        payload = _restores.pop(ticket, None)
    if not payload:
        return None
    deadline, session = payload
    return session if deadline > time.monotonic() else None
