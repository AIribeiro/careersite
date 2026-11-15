"""Portfolio-owner-only management of Advisory Regular and Admin roles."""
from __future__ import annotations

import streamlit as st

from site_cms import _request_json, _rest_url
from advisory_service_visibility import SERVICE_LABELS

OWNER_EMAIL = "jair.ribeiro@outlook.it"


def _read_roles(token: str) -> dict[str, str]:
    rows = _request_json(
        "GET",
        _rest_url("portfolio_advisory_user_roles?select=user_id,role&limit=5000"),
        token=token, timeout=12,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Unable to verify assigned roles.")
    return {str(row["user_id"]): str(row["role"]) for row in rows
            if row.get("user_id") and row.get("role") in ("admin", "regular")}


def _set_role(token: str, uid: str, role: str) -> bool:
    if role not in ("admin", "regular"):
        raise ValueError("Unsupported user role.")
    data = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_set_user_role_v1"),
        token=token, payload={"p_user_id": uid, "p_role": role}, timeout=15,
    )
    if not isinstance(data, dict) or str(data.get("user_id")) != uid or data.get("role") != role:
        raise RuntimeError("The server did not confirm the role assignment.")
    return data.get("changed") is True


def render_user_roles(token: str, people: list[dict]) -> None:
    st.subheader("User roles")
    st.caption(
        "Regular members see only services enabled for the public. Admins see and can "
        "use all services, including those hidden from regular users. This role does "
        "not give access to other people's private records or to the owner CMS. "
        "Only the portfolio owner can change assignments."
    )
    try:
        roles = _read_roles(token)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("User roles could not be loaded. No changes were made.")
        return

    users = {str(person.get("user_id") or ""): person for person in people
             if person.get("user_id") and str(person.get("email") or "").strip()}
    admin_count = sum(
        roles.get(uid, "regular") == "admin"
        for uid in users
    )
    a, b, c = st.columns(3)
    a.metric("Admin accounts", admin_count)
    b.metric("Regular accounts", len(users) - admin_count)
    c.metric("Known accounts", len(users))

    if not users:
        st.info("No verified accounts are available for role assignment.")
        return
    query = st.text_input(
        "Find a user by name or email",
        key="advisory_user_roles_search",
        placeholder="Search portfolio members",
    ).strip().casefold()
    filtered = [
        uid for uid, p in users.items() if not query
        or query in str(p.get("email") or "").casefold()
        or query in (str(p.get("first_name") or "") + " " + str(p.get("last_name") or "")).casefold()
    ]
    filtered.sort(key=lambda uid: str(users[uid].get("email") or "").casefold())
    if not filtered:
        st.info("No user matches this search.")
        return
    with st.container(border=True):
        st.dataframe([
            {
                "Account": str(users[uid].get("email") or ""),
                "Membership": str(users[uid].get("onboarding") or "Advisory member"),
                "Role": "Admin" if roles.get(uid, "regular") == "admin" else "Regular",
            }
            for uid in filtered
        ], hide_index=True, use_container_width=True)
    selected = st.selectbox(
        "Select account", filtered,
        format_func=lambda uid: str(users[uid].get("email") or ""),
        key="advisory_user_role_selected",
    )
    current = roles.get(selected, "regular")
    owner = str(users[selected].get("email") or "").strip().casefold() == OWNER_EMAIL
    st.caption("Current role: **" + current.title() + "**")
    desired = st.segmented_control(
        "Assigned role", ["regular", "admin"],
        format_func=lambda v: v.title(),
        default=current,
        key="advisory_role_new_" + selected,
        disabled=owner,
    )
    if owner:
        st.info("The verified portfolio owner is a permanent Admin and cannot be demoted.")
    if st.button(
        "Save role assignment", type="primary",
        disabled=owner or desired == current,
        key="advisory_role_save_" + selected,
    ):
        try:
            changed = _set_role(token, selected, str(desired))
            if changed:
                st.session_state["advisory_role_notice"] = "User role updated and audited."
            else:
                st.session_state["advisory_role_notice"] = "The role was already assigned."
            st.rerun()
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            st.error("Role assignment failed. The previous role is unchanged.")

    flash = st.session_state.pop("advisory_role_notice", None)
    if flash:
        st.success(str(flash))
    with st.expander("Role change history"):
        try:
            rows = _request_json(
                "GET", _rest_url(
                    "portfolio_advisory_user_role_audit?"
                    "select=user_id,previous_role,new_role,changed_at"
                    "&order=changed_at.desc&limit=60"
                ), token=token, timeout=12,
            )
            if isinstance(rows, list) and rows:
                st.dataframe([
                    {
                        "When": str(row.get("changed_at") or "")[:16].replace("T", " "),
                        "Account": str(users.get(str(row.get("user_id")), {}).get("email") or "Unknown"),
                        "From": str(row.get("previous_role") or "").title(),
                        "To": str(row.get("new_role") or "").title(),
                    }
                    for row in rows
                ], hide_index=True, use_container_width=True)
            else:
                st.caption("No role changes have been recorded.")
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            st.caption("Role history is temporarily unavailable.")
