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
        "Enabled means visible and available to regular members. Disabled hides the "
        "service, its calls-to-action and new starts from regular visitors and members. "
        "Admins still see and can use the service normally. Existing records, approvals "
        "and private conversations are preserved."
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
    b.metric("Hidden from regular users", len(states) - active)
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
                     else "Disabled · Hidden from regular users · Admins retain access")
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

    _render_renewal_metrics(token)

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

def _render_renewal_metrics(token: str) -> None:
    """Owner-only totals; source rows contain no customer inputs or monetary values."""
    st.divider()
    st.subheader("AI Portfolio Renewal Advisor · service activity")
    st.caption(
        "Registered-member counts and event totals exclude the five synthetic cases. "
        "Recommendations describe model outputs, not actual realized business results."
    )
    try:
        profiles = _request_json(
            "GET", _rest_url("portfolio_advisory_profiles?select=user_id&limit=3000"),
            token=token, timeout=12,
        )
        events = _request_json(
            "GET", _rest_url(
                "portfolio_advisory_renewal_events?select=user_id,event,recommendation,recorded_at"
                "&synthetic=eq.false&order=recorded_at.desc&limit=3000"
            ), token=token, timeout=15,
        )
        if not isinstance(profiles, list) or not isinstance(events, list):
            raise RuntimeError("Private activity could not be verified.")
    except (RuntimeError, ValueError, TimeoutError, OSError, KeyError):
        st.info("Renewal activity statistics are temporarily unavailable.")
        return

    from collections import Counter
    from datetime import datetime, timedelta, timezone

    today = datetime.now(timezone.utc)
    recent = today - timedelta(days=30)
    users = {str(r.get("user_id")) for r in events if r.get("user_id")}
    active_30 = {
        str(r.get("user_id"))
        for r in events
        if r.get("user_id") and str(r.get("recorded_at") or "")[:10] >= recent.date().isoformat()
    }
    counts = Counter(str(r.get("event") or "") for r in events)
    a, b, c = st.columns(3)
    a.metric("Registered Advisory users", len(profiles), help="Existing account records; limit 3,000.")
    b.metric("Renewal service users", len(users))
    c.metric("Active in 30 days", len(active_30))
    a, b, c = st.columns(3)
    a.metric("Starts", counts["service_start"])
    b.metric("Analyses completed", counts["analyzed"])
    c.metric("Completion per start", f"{counts['analyzed']/counts['service_start']:.0%}" if counts["service_start"] else "—")
    a, b, c = st.columns(3)
    a.metric("Scenario saves", counts["scenario_saved"])
    b.metric("PDF + Excel downloads", counts["pdf_download"] + counts["excel_download"])
    c.metric("Recorded executive decisions", counts["decision_recorded"])
    distribution = Counter(
        str(r.get("recommendation") or "")
        for r in events if r.get("event") == "analyzed" and r.get("recommendation")
    )
    with st.expander("Recommendation distribution and service diagnostics"):
        st.dataframe([
            {"Recommendation": key, "Analyses": distribution.get(key, 0)}
            for key in ("RENEW", "REPLACE", "TEST", "STOP", "HOLD")
        ], hide_index=True, use_container_width=True)
        st.caption(
            f"Observed operation errors: {counts['error']}. "
            "Only anonymous error counts are stored, not business descriptions. "
            "Repeated analyses may be counted more than once."
        )
    if len(events) >= 3000 or len(profiles) >= 3000:
        st.warning("Metrics are limited to the most recent 3,000 events or member records.")
