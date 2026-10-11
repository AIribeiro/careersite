"""Client-side device restore fallback for Streamlit Cloud owner authentication.

Streamlit Cloud may block the custom Starlette cookie endpoints or omit cookies
from the WebSocket handshake. Supabase's refresh-token flow, as used by the
Supabase browser SDK, can persist an authenticated session in origin-scoped
browser storage. This fallback is only activated by a successful owner sign-in.

Security trade-off: localStorage is readable by same-origin JavaScript, unlike
HttpOnly cookies. Prefer HttpOnly cookies when supported, validate restored
tokens with Supabase server-side and clear stored tokens at sign-out. Never put
passwords, access tokens, or refresh tokens in query params, HTML, analytics,
logs or externally accessible pages.
"""
from __future__ import annotations

import streamlit as st

STORAGE_KEY = "jair_portfolio_owner_supabase_v1"

_DEVICE_JS = """
const DEVICE_KEY = 'jair_portfolio_owner_supabase_v1';
export default function({data, setStateValue}) {
    if (!data || !data.mode) return;
    const mode = String(data.mode);
    // Component V2 remounts on reruns. Skip repeat callbacks for an
    // unchanged mode and refresh token to avoid an infinite rerun loop.
    const action = mode + ':' + String(data.refresh_token || '')
                 + ':' + String(data.expires_at || 0)
                 + ':' + String(Boolean(data.force));
    if (window.__jairOwnerStorageAction === action) return;
    window.__jairOwnerStorageAction = action;
    try {
        if (mode === 'clear') {
            window.localStorage.removeItem(DEVICE_KEY);
            setStateValue('status', 'cleared');
            return;
        }
        if (mode === 'write') {
            const refresh = String(data.refresh_token || '');
            if (!refresh || refresh.length < 16) {
                setStateValue('status', 'invalid');
                return;
            }
            const previous = window.localStorage.getItem(DEVICE_KEY);
            let oldToken = '';
            let oldExpires = 0;
            try {
                const parsed = previous ? JSON.parse(previous) : null;
                oldToken = String(parsed?.refresh_token || '');
                oldExpires = Number(parsed?.expires_at || 0);
            } catch (_) {}
            const expires = Number(data.expires_at || 0);
            // A second tab may have just refreshed this Supabase session.
            // Never overwrite that newer rotating token with an older one.
            if (oldToken !== refresh && !data.force
                && (oldExpires > expires ||
                    (oldExpires === expires && oldExpires > 0))) {
                setStateValue('status', 'newer_saved_session');
                return;
            }
            if (oldToken !== refresh || oldExpires !== expires) {
                window.localStorage.setItem(DEVICE_KEY, JSON.stringify({
                    version: 1,
                    refresh_token: refresh,
                    expires_at: expires,
                    saved_at: Date.now()
                }));
            }
            setStateValue('status', 'stored');
            return;
        }
        if (mode === 'read') {
            const raw = window.localStorage.getItem(DEVICE_KEY);
            if (!raw) {
                setStateValue('status', 'empty');
                return;
            }
            let saved = null;
            try { saved = JSON.parse(raw); } catch (_) {}
            if (!saved || saved.version !== 1
                || typeof saved.refresh_token !== 'string'
                || saved.refresh_token.length < 16) {
                window.localStorage.removeItem(DEVICE_KEY);
                setStateValue('status', 'empty');
                return;
            }
            setStateValue('restored', {
                refresh_token: saved.refresh_token,
                saved_at: Number(saved.saved_at || 0)
            });
            setStateValue('status', 'available');
        }
    } catch (_) {
        setStateValue('status', 'unavailable');
    }
}
"""


def device_session_component(**kwargs):
    """Register at mount time inside the Streamlit script, not at import."""
    component = st.components.v2.component(
        "careersite_owner_device_session_v1",
        js=_DEVICE_JS,
    )
    return component(**kwargs)
