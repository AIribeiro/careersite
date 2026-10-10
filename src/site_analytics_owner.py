"""Shared server-side authorization for owner-only analytics RPCs.

Supabase reporting functions grant EXECUTE only to authenticated and
independently verify the owner JWT. A publishable key is not authentication.
Never send these report requests with just an apikey.
"""
from __future__ import annotations

import streamlit as st

from site_analytics import ANALYTICS_PUBLISHABLE_KEY
from site_owner_persistence import persistent_owner_session


def owner_rpc_headers() -> dict[str, str]:
    """Supply the same validated/refreshable owner session used by the CMS."""
    session = persistent_owner_session()
    if not session or not session.get("access_token"):
        st.session_state.pop("cms_auth", None)
        raise PermissionError("Owner sign-in is required to read portfolio analytics.")
    st.session_state["cms_auth"] = session
    return {
        "apikey": ANALYTICS_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {session['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
