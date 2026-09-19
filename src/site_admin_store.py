from __future__ import annotations

import streamlit as st

ADMIN_STORAGE_KEY = "jair_analytics_admin_session_v1"

_admin_session_store = st.components.v2.component(
    "analytics_admin_session_store",
    js=r"""
export default function(component) {
  const { data, setStateValue } = component;
  const key = data?.storage_key || "jair_analytics_admin_session_v1";

  let token = "";
  try {
    if (data?.clear === true) {
      window.localStorage.removeItem(key);
    } else if (data?.write_token) {
      window.localStorage.setItem(key, String(data.write_token));
    }
    token = window.localStorage.getItem(key) || "";
  } catch (_) {
    token = "";
  }

  setStateValue("token", token);
  setStateValue("ready", true);
}
""",
)


def admin_session_store(
    *,
    write_token: str = "",
    clear: bool = False,
    key: str = "careersite_analytics_admin_store",
):
    """Read/write the opaque analytics admin token in browser localStorage."""
    return _admin_session_store(
        data={
            "storage_key": ADMIN_STORAGE_KEY,
            "write_token": write_token,
            "clear": bool(clear),
        },
        default={"token": "", "ready": False},
        key=key,
        on_token_change=lambda: None,
        on_ready_change=lambda: None,
    )
