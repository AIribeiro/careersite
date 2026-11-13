"""Private executive Advisory CRM, separate from publication readership.

Advisory registration is not a paid engagement, nor an editorial opt-in.
Owner-only writes use a server-authorized, audited Supabase RPC.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlencode
import json

import streamlit as st

from page_owner_reader_management import _verify_owner, _csv_bytes
from site_cms import _request_json, _rest_url

PAGE_SIZE = 500
MAX_ROWS = 10000
TABLES = {
    "portfolio_advisory_profiles": ("*", "created_at.desc"),
    "portfolio_advisory_intents": ("*", "created_at.desc"),
    "portfolio_advisory_admin_records": ("*", "updated_at.desc"),
    "portfolio_advisory_admin_audit": ("*", "created_at.desc"),
}
STAGES = ("inquiry", "discovery", "proposal", "engaged", "closed")


def _read_advisory(token: str, table: str) -> list[dict]:
    if table not in TABLES:
        raise ValueError("Unsupported Advisory management source.")
    fields, order = TABLES[table]
    collected: list[dict] = []
    for offset in range(0, MAX_ROWS, PAGE_SIZE):
        query = urlencode({
            "select": fields, "order": order,
            "offset": offset, "limit": PAGE_SIZE,
        })
        result = _request_json("GET", _rest_url(table + "?" + query),
                               token=token, timeout=16)
        if not isinstance(result, list):
            raise RuntimeError("Invalid private Advisory response.")
        collected.extend(row for row in result if isinstance(row, dict))
        if len(result) < PAGE_SIZE:
            return collected
    st.warning("Advisory directory reached the 10,000-row safety limit.")
    return collected


def _people(profiles: list[dict], intents: list[dict],
            records: list[dict]) -> list[dict]:
    """One row per identity; completed profile supersedes pending intent."""
    by_id: dict[str, dict] = {}
    for intent in intents:
        uid = str(intent.get("user_id") or "")
        if uid:
            by_id[uid] = {
                "user_id": uid,
                "email": intent.get("email", ""),
                "first_name": "", "last_name": "", "organization": "",
                "role_title": "", "decision_context": "",
                "account_status": "pending",
                "onboarding": "Pending onboarding",
                "created_at": intent.get("created_at", ""),
                "source": intent.get("source", ""),
            }
    for profile in profiles:
        uid = str(profile.get("user_id") or "")
        if uid:
            by_id[uid] = {
                **profile,
                "user_id": uid,
                "onboarding": "Profile completed",
                "source": by_id.get(uid, {}).get("source", "completed_signup"),
            }
    controls = {
        str(row.get("user_id")): row
        for row in records if row.get("user_id")
    }
    output = []
    for uid, data in by_id.items():
        ctl = controls.get(uid, {})
        output.append({
            **data,
            "relationship_stage": ctl.get("relationship_stage", "inquiry"),
            "internal_notes": ctl.get("internal_notes", ""),
            "next_action": ctl.get("next_action", ""),
            "follow_up_on": ctl.get("follow_up_on"),
            "updated_at": ctl.get("updated_at", data.get("updated_at", "")),
        })
    return sorted(output, key=lambda p: str(p.get("created_at") or ""), reverse=True)


def _owner_action(token: str, uid: str, action: str,
                  *, value: str | None = None, follow_up: str | None = None) -> dict:
    if action not in ("stage", "note", "next_action", "follow_up", "suspend", "reinstate"):
        raise ValueError("Unsupported Advisory operation.")
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_owner_action_v1"),
        token=token, payload={
            "p_user_id": uid, "p_action": action,
            "p_value": value, "p_date": follow_up,
        }, timeout=16,
    )
    if not isinstance(result, dict) or str(result.get("user_id")) != uid:
        raise RuntimeError("Advisory change was not confirmed by the server.")
    return result


def _date(value: object) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _details(token: str, person: dict) -> None:
    uid = str(person["user_id"])
    label = str(person.get("email") or "")
    completed = person.get("onboarding") == "Profile completed"
    st.markdown("#### Relationship record")
    st.write("**Email:** " + label)
    st.write("**Onboarding:** " + str(person.get("onboarding")))
    st.write("**Access:** " + (
        str(person.get("account_status") or "active").title()
        if completed else "Pending professional profile"
    ))
    if not completed:
        st.info(
            "An email-verified account exists, but the Advisory professional "
            "profile was not completed. This is not an active client, "
            "contract, or paid engagement. The user can finish registration "
            "through the Advisory account page with their existing password."
        )
    else:
        a, b = st.columns(2)
        with a:
            st.write("**Name:** " + " ".join(filter(None, [
                str(person.get("first_name") or ""),
                str(person.get("last_name") or ""),
            ])))
            st.write("**Role:** " + str(person.get("role_title") or "Not provided"))
            st.write("**Organization:** " + str(person.get("organization") or "Not provided"))
        with b:
            st.write("**Advisory focus:** " + str(person.get("advisory_focus") or "Not provided"))
            st.write("**Decision timeframe:** " + str(person.get("decision_horizon") or "Not provided"))
            st.write("**Registered:** " + str(person.get("created_at") or "")[:19])
        st.write("**Decision context (member-provided):**")
        st.text(str(person.get("decision_context") or "Not provided"))
    st.caption("Client status and commercial terms must be agreed separately. No marketing consent is inferred.")

    with st.expander("Relationship stage and next step", expanded=True):
        stage = str(person.get("relationship_stage") or "inquiry")
        selected = st.selectbox(
            "Relationship stage", STAGES,
            index=STAGES.index(stage) if stage in STAGES else 0,
            format_func=lambda v: v.title(),
            key="advisory_stage_" + uid,
        )
        if st.button("Save relationship stage", key="advisory_stage_save_" + uid,
                     disabled=selected == stage):
            try:
                _owner_action(token, uid, "stage", value=selected)
                st.success("Relationship stage saved and audited.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Stage could not be updated.")
        with st.form("advisory_next_action_" + uid):
            action = st.text_area(
                "Next agreed action / follow-up", value=str(person.get("next_action") or ""),
                max_chars=2000, height=75,
                help="Keep private client context relevant, proportionate and secure.",
            )
            save_action = st.form_submit_button("Save next action")
        if save_action:
            try:
                _owner_action(token, uid, "next_action", value=action)
                st.success("Next action saved and audited.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Next action could not be saved.")
        existing = _date(person.get("follow_up_on"))
        follow_up = st.date_input(
            "Follow-up date", value=existing, format="YYYY-MM-DD",
            key="advisory_follow_up_" + uid,
        )
        if st.button("Save follow-up date", key="advisory_followup_save_" + uid):
            try:
                _owner_action(token, uid, "follow_up",
                              follow_up=follow_up.isoformat() if follow_up else None)
                st.success("Follow-up date saved and audited.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Follow-up date could not be saved.")

    with st.expander("Private owner notes"):
        with st.form("advisory_notes_" + uid):
            notes = st.text_area(
                "Internal notes (not visible to the Advisory member)",
                value=str(person.get("internal_notes") or ""),
                max_chars=10000, height=130,
                help="Do not store credentials, secrets or unnecessarily sensitive details.",
            )
            save_notes = st.form_submit_button("Save private notes")
        if save_notes:
            try:
                _owner_action(token, uid, "note", value=notes)
                st.success("Private note saved and audited.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Private note could not be saved.")

    if completed:
        with st.expander("Advisory account access"):
            st.caption(
                "Suspension affects Advisory access only. "
                "Reader access and editorial consent are managed separately."
            )
            confirmation = st.text_input(
                "Type the account email to confirm",
                key="advisory_confirm_" + uid,
            )
            suspended = person.get("account_status") == "suspended"
            action = "reinstate" if suspended else "suspend"
            if st.button(
                "Reinstate Advisory access" if suspended else "Suspend Advisory access",
                disabled=confirmation.strip().casefold() != label.strip().casefold(),
                key="advisory_account_action_" + uid,
            ):
                try:
                    _owner_action(token, uid, action)
                    st.success("Advisory access updated and audited.")
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("Advisory account access could not be changed.")

    snapshot = {
        "identity": {k: v for k, v in person.items()
                     if k not in ("internal_notes",)},
        "internal_notes": str(person.get("internal_notes") or ""),
    }
    st.download_button(
        "Export this relationship (private JSON)",
        data=json.dumps(snapshot, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name="advisory-" + uid + "-private.json",
        mime="application/json", key="advisory_export_" + uid,
    )


def render_owner_advisory_management(owner_session: dict) -> None:
    try:
        token = _verify_owner(owner_session)
    except (PermissionError, RuntimeError, ValueError, TimeoutError):
        st.error("Advisory Management is restricted to the authenticated portfolio owner.")
        return
    st.title("Advisory Management")
    st.caption(
        "Private executive relationships · Prospective advisory clients, onboarding, "
        "decision context, follow-ups and separately agreed engagements."
    )
    shortcuts = st.columns([1, 1, 3])
    with shortcuts[0]:
        st.link_button(
            "Advisory service ↗",
            "https://jairribeiro.com/?page=advisory",
            use_container_width=True,
        )
    with shortcuts[1]:
        st.link_button(
            "Advisory account ↗",
            "https://jairribeiro.com/?page=advisory-access",
            use_container_width=True,
        )
    if st.button("Refresh advisory data", key="advisory_owner_refresh"):
        st.rerun()

    try:
        profiles = _read_advisory(token, "portfolio_advisory_profiles")
        intents = _read_advisory(token, "portfolio_advisory_intents")
        controls = _read_advisory(token, "portfolio_advisory_admin_records")
        audit = _read_advisory(token, "portfolio_advisory_admin_audit")
    except (RuntimeError, ValueError, TimeoutError):
        st.error("The Advisory directory is temporarily unavailable.")
        return
    people = _people(profiles, intents, controls)

    kpi = st.columns(4)
    kpi[0].metric("Advisory registrations", len(people))
    kpi[1].metric("Pending onboarding", sum(p.get("onboarding") != "Profile completed" for p in people))
    kpi[2].metric("Completed accounts", sum(p.get("onboarding") == "Profile completed" for p in people))
    kpi[3].metric("Engaged relationships", sum(p.get("relationship_stage") == "engaged" for p in people))
    st.caption(
        "Registration only confirms the Advisory account. A specific request, "
        "owner response and agreed scope are separate steps. "
        "Open **Action inbox** to respond to client input and move the work forward."
    )
    inbox_tab, directory, pipeline, audit_tab = st.tabs(
        ["Action inbox", "Advisory directory", "Relationship pipeline", "Administration audit"]
    )
    with inbox_tab:
        from page_owner_advisory_requests import render_advisory_action_inbox
        render_advisory_action_inbox(token, people)
    with directory:
        search = st.text_input(
            "Find an advisory registrant",
            placeholder="Search name, organization, email or decision context",
            key="advisory_owner_search",
        ).strip().casefold()
        stage = st.selectbox(
            "Directory filter",
            ["All relationships", "Pending onboarding", "Completed profiles",
             "Inquiries", "Discovery", "Proposal", "Engaged", "Closed"],
            key="advisory_owner_filter",
        )
        filtered = []
        for p in people:
            content = " ".join(str(p.get(field) or "") for field in (
                "first_name", "last_name", "email", "organization",
                "role_title", "decision_context", "advisory_focus",
            )).casefold()
            if search not in content:
                continue
            if stage == "Pending onboarding" and p.get("onboarding") == "Profile completed":
                continue
            if stage == "Completed profiles" and p.get("onboarding") != "Profile completed":
                continue
            if stage in ("Inquiries", "Discovery", "Proposal", "Engaged", "Closed") and (
                str(p.get("relationship_stage", "")).casefold() !=
                ("inquiry" if stage == "Inquiries" else stage.casefold())
            ):
                continue
            filtered.append(p)
        st.caption(f"{len(filtered)} Advisory relationships")
        st.dataframe([{
            "Name": " ".join(filter(None, [
                str(p.get("first_name") or ""), str(p.get("last_name") or ""),
            ])),
            "Email": str(p.get("email") or ""),
            "Organization": str(p.get("organization") or ""),
            "Role": str(p.get("role_title") or ""),
            "Onboarding": str(p.get("onboarding") or ""),
            "Relationship": str(p.get("relationship_stage") or "").title(),
            "Account": str(p.get("account_status") or "").title(),
            "Follow-up": str(p.get("follow_up_on") or ""),
            "Registered": str(p.get("created_at") or "")[:10],
        } for p in filtered[:500]], hide_index=True, use_container_width=True)
        if filtered:
            selected_id = st.selectbox(
                "Review Advisory relationship",
                [str(p["user_id"]) for p in filtered],
                format_func=lambda uid: next(
                    (str(p.get("email") or "") for p in filtered if str(p["user_id"]) == uid),
                    uid,
                ),
                key="advisory_owner_selected_id",
            )
            person = next((p for p in filtered if str(p["user_id"]) == selected_id), None)
            if person:
                st.divider()
                _details(token, person)
        csv = _csv_bytes(
            ["Email", "Name", "Organization", "Role", "Onboarding", "Stage", "Follow-up", "Registered"],
            [[p.get("email"), " ".join(filter(None, (p.get("first_name"),p.get("last_name")))),
              p.get("organization"), p.get("role_title"), p.get("onboarding"),
              p.get("relationship_stage"), p.get("follow_up_on"), p.get("created_at")]
             for p in filtered],
        )
        st.download_button(
            "Export Advisory directory (CSV)", data=csv,
            file_name="jairribeiro-advisory-relationships.csv",
            mime="text/csv", disabled=not filtered,
            key="advisory_owner_directory_csv",
        )
    with pipeline:
        for stage_name in STAGES:
            group = [p for p in people if p.get("relationship_stage") == stage_name]
            with st.expander(stage_name.title() + f" · {len(group)}", expanded=stage_name == "inquiry"):
                if not group:
                    st.caption("No relationships at this stage.")
                else:
                    for p in group:
                        st.write(
                            "**" + str(p.get("email") or "") + "** · " +
                            str(p.get("onboarding")) + " · Next: " +
                            str(p.get("next_action") or "Not set")
                        )
        st.caption("Pipeline stage is set by the owner. No automatic conversion to a paid client.")
    with audit_tab:
        st.caption("Every owner stage, note, follow-up or account action is recorded.")
        if audit:
            by_id = {str(p["user_id"]): str(p.get("email") or "") for p in people}
            st.dataframe([{
                "When": str(row.get("created_at") or "")[:19],
                "Relationship": by_id.get(str(row.get("user_id")), "Removed account"),
                "Action": str(row.get("action") or ""),
                "Detail": str(row.get("detail") or ""),
            } for row in audit[:500]], hide_index=True, use_container_width=True)
        else:
            st.caption("No administrative changes yet.")
