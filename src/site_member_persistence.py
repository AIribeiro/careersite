"""Best-effort persistent Reader/Advisory session on the existing ASGI host.

Both member experiences already use the same Supabase Auth identity in Streamlit.
A one-use restore ticket can be redeemed server-side from a same-origin POST;
neither the access JWT nor rotating refresh token is sent to browser JS. This
does not use localStorage, sessionStorage, passwords in cookies, or auth URLs.

When registrar masking, mobile browser cookie policies, or a proxy block this
endpoint, the normal native login still works. Only a working first-party
HTTP-cookie boundary can guarantee restoration across browser reloads.
"""
from __future__ import annotations

import logging
import time

import streamlit as st

from reader_membership import _register_profile
from site_member_http_auth import _verified_member
from site_member_tickets import (
    issue_member_cookie_ticket, redeem_member_restore_ticket,
)

LOG = logging.getLogger("careersite.member.persistence")
REFRESH_HEADROOM = 90

_ATTACH_JS = """
export default function({data, setStateValue}) {
  const ticket = String(data?.ticket || '');
  if (!ticket || ticket === window.__jairMemberAttach) return;
  window.__jairMemberAttach = ticket;
  fetch('/member-auth/attach', {
    method:'POST', credentials:'same-origin', cache:'no-store',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({ticket}).toString()
  }).then(async response => {
    if (!response.ok) throw new Error('attach_unavailable');
    const result = await response.json();
    setStateValue('status', result.saved ? 'saved' : 'unavailable');
  }).catch(() => setStateValue('status', 'unavailable'));
}
"""

_RESTORE_JS = """
export default function({data, setStateValue}) {
  if (!data?.enabled) return;
  const nonce = Number(data.nonce || 0);
  if (window.__jairMemberRestoreNonce === nonce) return;
  window.__jairMemberRestoreNonce = nonce;
  fetch('/member-auth/bootstrap', {
    method:'POST', credentials:'same-origin', cache:'no-store',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'restore=1'
  }).then(async response => {
    if (!response.ok) throw new Error('no_saved_session');
    const result = await response.json();
    if (!result.authenticated || !result.restore_ticket)
      throw new Error('no_saved_session');
    // The ticket is single use and expires after 45 seconds. Access and
    // refresh credentials remain strictly on the server and in HttpOnly cookies.
    setStateValue('session', {
      restore_ticket: result.restore_ticket, nonce
    });
  }).catch(() => setStateValue('status', 'unavailable'));
}
"""

_LOGOUT_JS = """
export default function({data, setStateValue}) {
  if (!data?.requested) return;
  const nonce = Number(data.nonce || 0);
  if (window.__jairMemberLogoutNonce === nonce) return;
  window.__jairMemberLogoutNonce = nonce;
  fetch('/member-auth/logout', {
    method:'POST', credentials:'same-origin', cache:'no-store',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'logout=1'
  }).then(async response => {
    if (!response.ok) throw new Error('logout_unavailable');
    const result = await response.json();
    setStateValue('status', result.signed_out ? 'cleared' : 'unavailable');
  }).catch(() => setStateValue('status', 'unavailable'));
}
"""


def _component(name: str, js: str, **kwargs):
    """Register V2 components at runtime rather than in an ASGI module import."""
    widget = st.components.v2.component(name, js=js)
    return widget(**kwargs)


def queue_member_session_cookie(session: dict, user: dict) -> None:
    """Call only after Supabase confirms email and active Reader membership."""
    try:
        st.session_state["member_cookie_attach_ticket"] = (
            issue_member_cookie_ticket(session, user)
        )
        st.session_state.pop("member_cookie_attach_status", None)
    except ValueError:
        LOG.warning("Could not issue a verified member cookie attachment ticket.")


def _attach_if_pending() -> None:
    ticket = str(st.session_state.get("member_cookie_attach_ticket") or "")
    if not ticket:
        return
    try:
        result = _component(
            "jair_member_session_attach_v1", _ATTACH_JS,
            key="member_session_attach", data={"ticket": ticket},
            default={"status": None}, on_status_change=lambda: None,
        )
    except (RuntimeError, AttributeError, ValueError):
        st.session_state.pop("member_cookie_attach_ticket", None)
        st.session_state["member_cookie_attach_status"] = "unavailable"
        return
    status = getattr(result, "status", None)
    if status in ("saved", "unavailable"):
        st.session_state.pop("member_cookie_attach_ticket", None)
        st.session_state["member_cookie_attach_status"] = status


def _restore_from_cookie() -> None:
    if st.session_state.get("member_restore_checked"):
        return
    nonce = int(st.session_state.get("member_restore_nonce", 0))
    try:
        result = _component(
            "jair_member_session_restore_v1", _RESTORE_JS,
            key="member_session_restore",
            data={"enabled": True, "nonce": nonce},
            default={"session": None, "status": None},
            on_session_change=lambda: None, on_status_change=lambda: None,
        )
    except (RuntimeError, AttributeError, ValueError):
        st.session_state["member_restore_checked"] = True
        return
    candidate = getattr(result, "session", None)
    if not isinstance(candidate, dict):
        if getattr(result, "status", None) == "unavailable":
            st.session_state["member_restore_checked"] = True
        return
    if candidate.get("nonce") != nonce:
        return
    try:
        restored = redeem_member_restore_ticket(
            str(candidate.get("restore_ticket") or "")
        )
        if not isinstance(restored, dict):
            raise ValueError("Restoration ticket was used or expired.")
        expiry = int(restored.get("expires_at") or 0)
        token = str(restored.get("access_token") or "")
        if not token or expiry <= time.time() + REFRESH_HEADROOM:
            raise ValueError("Access token is not current.")
        # The HTTP endpoint has already checked Reader status, but always
        # reverify in Python before enabling any private Streamlit content.
        user = _verified_member(token)
        session = {
            "access_token": token, "expires_at": expiry,
            "_cookie_backed": True,
        }
        _register_profile(session, user)
        st.session_state["reader_native_session"] = session
        st.session_state["reader_native_user"] = user
        st.session_state["member_restore_checked"] = True
        st.rerun()
    except (RuntimeError, ValueError, TimeoutError, TypeError, KeyError):
        st.session_state["member_restore_checked"] = True


def _finish_browser_signout() -> bool:
    """Block private rendering until cookies are cleared or failure is shown."""
    nonce = int(st.session_state.get("member_signout_nonce", 0))
    try:
        result = _component(
            "jair_member_session_logout_v1", _LOGOUT_JS,
            key="member_session_logout",
            data={"requested": True, "nonce": nonce},
            default={"status": None}, on_status_change=lambda: None,
        )
        status = getattr(result, "status", None)
    except (RuntimeError, AttributeError, ValueError):
        status = "unavailable"
    if status in ("cleared", "unavailable"):
        st.session_state.pop("member_signout_pending", None)
        st.session_state["member_restore_checked"] = True
        if status == "unavailable":
            st.session_state["reader_native_flash"] = (
                "warning",
                "Signed out of this page, but the browser session cookie could "
                "not be cleared. Close the browser and contact support if "
                "your account still appears signed in after refreshing.",
            )
        st.rerun()
        return False
    st.caption("Signing out of your Reader and Advisory session…")
    return True


def mount_member_persistence() -> bool:
    """Mount before the portfolio navigation on every session-safe rerun.

    Returns True only when a sign-out is pending, so callers can avoid
    rendering private workspaces during the cookie-clearing operation.
    """
    if st.session_state.get("member_signout_pending"):
        return _finish_browser_signout()

    current = st.session_state.get("reader_native_session")
    if isinstance(current, dict) and current.get("access_token"):
        if (
            current.get("_cookie_backed")
            and int(current.get("expires_at") or 0) <=
                time.time() + REFRESH_HEADROOM
        ):
            st.session_state.pop("reader_native_session", None)
            st.session_state.pop("reader_native_user", None)
            st.session_state.pop("member_restore_checked", None)
            st.session_state["member_restore_nonce"] = (
                int(st.session_state.get("member_restore_nonce", 0)) + 1
            )
            st.rerun()
        _attach_if_pending()
        return False

    _restore_from_cookie()
    return False


def begin_member_browser_signout() -> None:
    st.session_state["member_signout_pending"] = True
    st.session_state["member_signout_nonce"] = (
        int(st.session_state.get("member_signout_nonce", 0)) + 1
    )
    st.session_state.pop("member_restore_checked", None)
    st.session_state.pop("member_cookie_attach_ticket", None)
