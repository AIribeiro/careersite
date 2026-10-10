"""Owner authentication across Streamlit WebSocket sessions.

Persistent credentials are issued as Secure, HttpOnly, same-site cookies only
by the Starlette auth endpoints, never exposed to browser-side JavaScript,
query parameters, Streamlit URLs, localStorage, or analytics telemetry.
Supabase validates each newly restored access token.
"""
from __future__ import annotations

import time

import streamlit as st
import streamlit.components.v1 as components

from site_cms import OWNER_EMAIL, _request_json
from site_analytics import ANALYTICS_URL

ACCESS_COOKIE = "__Host-jair_owner_access"
REFRESH_COOKIE = "__Host-jair_owner_refresh"
EXPIRY_COOKIE = "__Host-jair_owner_exp"
ALLOWED_DESTINATIONS = frozenset(("analytics", "admin"))
REFRESH_HEADROOM_SECONDS = 75


def _cookies() -> dict:
    try:
        return st.context.cookies
    except (AttributeError, RuntimeError):
        return {}


def has_persistent_session() -> bool:
    return bool(_cookies().get(REFRESH_COOKIE))


def persistent_owner_session() -> dict | None:
    """Restore and verify an owner access token; never rotate a refresh token in Streamlit.

    Only the HTTP auth endpoint may refresh the token because it must also
    atomically rotate the HttpOnly refresh cookie in the browser response.
    """
    current = st.session_state.get("cms_auth")
    if isinstance(current, dict) and current.get("access_token"):
        if int(current.get("expires_at") or 0) > time.time() + REFRESH_HEADROOM_SECONDS:
            return current
    st.session_state.pop("cms_auth", None)

    cookies = _cookies()
    access = str(cookies.get(ACCESS_COOKIE) or "")
    refresh = str(cookies.get(REFRESH_COOKIE) or "")
    try:
        expires_at = int(cookies.get(EXPIRY_COOKIE) or 0)
    except (ValueError, TypeError):
        expires_at = 0
    if not access or not refresh or expires_at <= time.time() + REFRESH_HEADROOM_SECONDS:
        return None

    try:
        result = _request_json(
            "GET", f"{ANALYTICS_URL.rstrip('/')}/auth/v1/user",
            token=access,
        )
    except (RuntimeError, TimeoutError):
        return None
    if not isinstance(result, dict) or str(result.get("email") or "").lower() != OWNER_EMAIL:
        return None

    session = {"access_token":access,"refresh_token":refresh,
               "expires_at":expires_at,"user":result}
    st.session_state["cms_auth"] = session
    return session


def show_owner_login_or_refresh(destination: str) -> None:
    """On expired access, silently rotate via same-site server endpoint."""
    target = destination if destination in ALLOWED_DESTINATIONS else "analytics"
    if has_persistent_session():
        # No credentials are interpolated into HTML or sent to scripts.
        components.html(
            f'<script>window.parent.location.replace("/owner-auth/refresh?next={target}");</script>',
            height=0,
        )
        st.caption("Restoring your authenticated session…")
        st.markdown(
            f'<a href="/owner-auth/refresh?next={target}" target="_self">'
            'Continue securely if the page does not reload</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<a href="/owner-auth/login?next={target}" target="_self">'
            'Sign in securely</a>',
            unsafe_allow_html=True,
        )


def browser_owner_signout() -> None:
    """Clear Streamlit state immediately, then revoke and clear HttpOnly cookies."""
    st.session_state.pop("cms_auth", None)
    st.session_state.pop("cms_edit_id", None)
    components.html(
        """
<script>
(async () => {
  try {
    await window.parent.fetch('/owner-auth/logout', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'logout=1'
    });
  } finally {
    window.parent.location.replace('/?page=analytics');
  }
})();
</script>""",
        height=0,
    )
    st.caption("Signing out…")
    st.caption("If this page does not redirect, close and reopen the Analytics page.")
