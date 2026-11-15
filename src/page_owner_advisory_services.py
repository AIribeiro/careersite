"""Owner-only Advisory service catalogue control panel."""
from __future__ import annotations

import streamlit as st

from advisory_service_visibility import SERVICE_LABELS, service_visibility
from site_cms import _request_json, _rest_url


def _read_owner_catalogue(token: str) -> list[dict]:
    rows = _request_json(
        "GET",
        _rest_url(
            "portfolio_advisory_service_visibility?"
            "select=service_key,display_name,is_enabled&order=service_key.asc"
        ),
        token=token,
        timeout=12,
    )
    if not isinstance(rows, list) or {str(r.get("service_key")) for r in rows} != set(SERVICE_LABELS):
        raise RuntimeError("The service catalogue could not be confirmed.")
    if any(type(r.get("is_enabled")) is not bool for r in rows):
        raise RuntimeError("The service catalogue returned invalid availability.")
    return rows


def _set_service_visibility(token: str, service_key: str, enabled: bool) -> bool:
    if service_key not in SERVICE_LABELS or type(enabled) is not bool:
        raise ValueError("Unknown service availability action.")
    result = _request_json(
        "POST",
        _rest_url("rpc/portfolio_advisory_set_service_visibility_v1"),
        token=token,
        payload={"p_service_key": service_key, "p_enabled": enabled},
        timeout=15,
    )
    if not isinstance(result, dict) or (
        result.get("service_key") != service_key
        or result.get("is_enabled") is not enabled
    ):
        raise RuntimeError("Supabase did not confirm the requested service state.")
    service_visibility.clear()
    return bool(result.get("changed"))


def render_service_management(token: str) -> None:
    st.subheader("Service availability")
    st.caption(
        "Choose which Advisory services can receive new clients. "
        "Disabling a service removes its active call-to-action on the public Advisory page "
        "and pauses new starts; it does not erase client records or revoke existing approvals. "
        "Your Advisory account, member history and current conversations remain available."
    )
    try:
        rows = _read_owner_catalogue(token)
    except (RuntimeError, ValueError, TimeoutError, OSError, KeyError):
        st.error("Service availability could not be loaded. No changes were made.")
        return

    states = {str(r["service_key"]): bool(r["is_enabled"]) for r in rows}
    active = sum(states.values())
    a, b, c = st.columns(3)
    a.metric("Enabled services", active)
    b.metric("Paused services", len(states) - active)
    c.metric("Total services", len(states))
    st.divider()

    for key, label in SERVICE_LABELS.items():
        enabled = states[key]
        with st.container(border=True, key="owner_service_catalogue_" + key):
            heading, control = st.columns([3.5, 1.4], gap="small", vertical_alignment="center")
            with heading:
                st.markdown("**" + label + "**")
                st.caption(
                    ("Enabled · Public entry is available" if enabled
                     else "Disabled · New requests and start CTAs are paused")
                )
            with control:
                if st.button(
                    "Disable service" if enabled else "Enable service",
                    key="owner_service_toggle_" + key,
                    use_container_width=True,
                    type="secondary" if enabled else "primary",
                ):
                    try:
                        _set_service_visibility(token, key, not enabled)
                    except (RuntimeError, ValueError, TimeoutError, KeyError, OSError):
                        st.error("This change was not confirmed. The prior setting is preserved.")
                    else:
                        st.session_state["advisory_service_flash"] = (
                            label + (" enabled." if not enabled else " disabled.")
                        )
                        st.rerun()

    notice = st.session_state.pop("advisory_service_flash", "")
    if notice:
        st.success(notice)

    with st.expander("Recent availability changes"):
        try:
            audit = _request_json(
                "GET",
                _rest_url(
                    "portfolio_advisory_service_visibility_audit?"
                    "select=service_key,previous_enabled,current_enabled,changed_at"
                    "&order=changed_at.desc&limit=30"
                ),
                token=token,
                timeout=12,
            )
            if isinstance(audit, list) and audit:
                st.dataframe([
                    {
                        "Changed": str(r.get("changed_at") or "")[:16].replace("T", " "),
                        "Service": SERVICE_LABELS.get(str(r.get("service_key") or ""), ""),
                        "Change": "Enabled" if r.get("current_enabled") is True else "Disabled",
                    } for r in audit
                ], hide_index=True, use_container_width=True)
            else:
                st.caption("No availability changes recorded yet.")
        except (RuntimeError, ValueError, TimeoutError, KeyError, OSError):
            st.caption("Availability audit is temporarily unavailable.")
