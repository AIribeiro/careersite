"""Durable owner sign-in with a Streamlit Cloud-safe HTTP cookie bridge.

Community Cloud may omit custom cookies on WebSocket upgrades. A small trusted
v2 component makes a same-origin HTTPS request; the refresh token stays in
Secure/HttpOnly cookies. Only the short-lived access JWT crosses into Streamlit
widget state, and Python validates it independently before privileged reads.
The original password form remains available if browser restoration fails.
"""
from __future__ import annotations

import time

import streamlit as st

from site_cms import OWNER_EMAIL, _request_json, owner_signin
from site_analytics import ANALYTICS_URL

ACCESS_COOKIE = "__Host-jair_owner_access"
REFRESH_COOKIE = "__Host-jair_owner_refresh"
EXPIRY_COOKIE = "__Host-jair_owner_exp"
ALLOWED_DESTINATIONS = frozenset(("analytics", "admin"))
REFRESH_HEADROOM_SECONDS = 75

# Component V2 executes on the app origin (not a cross-origin iframe).
# No refresh tokens, passwords or durable credentials are sent to the client
# component; those remain HttpOnly in the browser's cookie jar.
_RESTORE_JS = """
export default function({ data, setStateValue }) {
  if (!data || !data.enabled) return;
  const key = String(data.nonce);
  if (window.__jairOwnerRestoreAttempt === key) return;
  window.__jairOwnerRestoreAttempt = key;
  fetch('/owner-auth/bootstrap', {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'restore=1'
  }).then(async response => {
    if (!response.ok) throw new Error('not_authenticated');
    const result = await response.json();
    if (!result.authenticated || !result.access_token) throw new Error('not_authenticated');
    setStateValue('session', {
      access_token: result.access_token,
      expires_at: result.expires_at
    });
  }).catch(() => { setStateValue('status', 'signed_out'); });
}
"""

_LOGOUT_JS = """
export default function({ data, setTriggerValue }) {
  if (!data || !data.requested || window.__jairLogoutStarted) return;
  window.__jairLogoutStarted = true;
  fetch('/owner-auth/logout', {
    method: 'POST', credentials: 'same-origin', cache: 'no-store',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'logout=1'
  }).then(response => {
    if (!response.ok) throw new Error('logout_failed');
    window.location.replace('/?page=analytics');
  }).catch(() => {
    setTriggerValue('failed', true);
    window.__jairLogoutStarted = false;
  });
}
"""

_restore_component = st.components.v2.component(
    "careersite_owner_session_restore", js=_RESTORE_JS
)
_logout_component = st.components.v2.component(
    "careersite_owner_session_logout", js=_LOGOUT_JS
)


def _verify_owner_access(access: str) -> dict | None:
    if not access:
        return None
    try:
        identity = _request_json(
            "GET", f"{ANALYTICS_URL.rstrip('/')}/auth/v1/user", token=access,
        )
    except (RuntimeError, TimeoutError):
        return None
    if not isinstance(identity, dict):
        return None
    if str(identity.get("email") or "").lower() != OWNER_EMAIL:
        return None
    return identity


def _cookies() -> dict:
    try:
        return st.context.cookies
    except (AttributeError, RuntimeError):
        return {}


def has_persistent_session() -> bool:
    return bool(_cookies().get(REFRESH_COOKIE))


def persistent_owner_session() -> dict | None:
    """Verify Supabase ownership before granting CMS/Analytics access.

    Browser bridge handles the missing-custom-cookie problem on Streamlit Cloud.
    The user's password can always be used in-app if that bridge is unavailable.
    """
    current = st.session_state.get("cms_auth")
    if isinstance(current, dict) and current.get("access_token"):
        try:
            expires = int(current.get("expires_at") or 0)
        except (ValueError,TypeError):
            expires = 0
        if expires > time.time() + REFRESH_HEADROOM_SECONDS:
            return current
        st.session_state.pop("cms_auth",None)
        st.session_state["owner_restore_nonce"] = (
            int(st.session_state.get("owner_restore_nonce",0)) + 1
        )

    cookies = _cookies()
    access = str(cookies.get(ACCESS_COOKIE) or "")
    try:
        expires_at = int(cookies.get(EXPIRY_COOKIE) or 0)
    except (ValueError, TypeError):
        expires_at = 0
    if access and expires_at > time.time() + REFRESH_HEADROOM_SECONDS:
        identity = _verify_owner_access(access)
        if identity:
            session = {"access_token": access, "expires_at": expires_at, "user": identity}
            st.session_state["cms_auth"] = session
            return session

    restored = _restore_component(
        key="owner_http_cookie_bridge",
        data={"enabled": True, "nonce": int(st.session_state.get("owner_restore_nonce",0))},
        default={"session": None, "status": None},
        on_session_change=lambda: None,
        on_status_change=lambda: None,
    )
    candidate = restored.session if isinstance(restored.session, dict) else None
    if not candidate:
        return None
    try:
        expires_at = int(candidate.get("expires_at") or 0)
    except (ValueError,TypeError):
        return None
    if expires_at <= time.time() + REFRESH_HEADROOM_SECONDS:
        return None
    access = str(candidate.get("access_token") or "")
    identity = _verify_owner_access(access)
    if not identity:
        return None
    session = {"access_token":access,"expires_at":expires_at,"user":identity}
    st.session_state["cms_auth"] = session
    return session


def show_owner_login_or_refresh(destination: str) -> None:
    """Accessible login button plus proven in-app form fallback."""
    target = destination if destination in ALLOWED_DESTINATIONS else "analytics"
    if has_persistent_session():
        st.caption("Checking your existing browser session. If it does not restore, sign in below.")
    st.markdown(
        f'<a href="/owner-auth/login?next={target}" target="_self">'
        'Sign in and stay signed in</a>',
        unsafe_allow_html=True,
    )
    with st.form(f"owner_fallback_login_{target}",clear_on_submit=True):
        password = st.text_input("Owner password",type="password")
        submitted = st.form_submit_button("Sign in here instead")
    if submitted:
        try:
            session = owner_signin(password)
            st.session_state["cms_auth"] = session
            st.rerun()
        except (RuntimeError,ValueError,TimeoutError):
            st.error("Sign-in failed. Check your owner password and try again.")
    st.caption(
        "The first option remembers this browser; the password form is a "
        "fallback if your browser blocks persistent authentication."
    )


def browser_owner_signout() -> None:
    """Browser POST clears cookies and revokes tokens; never store JWT in URLs."""
    st.session_state.pop("cms_auth",None)
    st.session_state.pop("cms_edit_id",None)
    result = _logout_component(
        key="owner_http_logout",
        data={"requested":True},
        on_failed_change=lambda:None,
    )
    st.caption("Signing out and clearing saved credentials…")
    if result.failed:
        st.error("Automatic sign-out failed. Use the secure sign-out page.")
    st.markdown('<a href="/owner-auth/logout" target="_self">Secure sign-out page</a>',
                unsafe_allow_html=True)
