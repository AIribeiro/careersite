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
    "portfolio_reader_profiles": ("*", "created_at.desc"),
    "portfolio_advisory_scorecard_audit": ("*", "created_at.desc"),
    "portfolio_advisory_rollout_audit": ("*", "created_at.desc"),
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
            records: list[dict], readers: list[dict] | None = None) -> list[dict]:
    """One row per verified reader or advisory identity; preserve membership boundaries."""
    by_id: dict[str, dict] = {}
    for reader in readers or []:
        uid = str(reader.get("user_id") or "")
        if uid:
            by_id[uid] = {
                "user_id": uid, "email": reader.get("email", ""),
                "first_name": reader.get("first_name", ""),
                "last_name": reader.get("last_name", ""),
                "organization": reader.get("organization", ""),
                "role_title": reader.get("job_title", ""),
                "decision_context": "",
                "account_status": "reader_only",
                "onboarding": "Reader only",
                "created_at": reader.get("created_at", ""),
                "source": reader.get("acquisition_source", "reader_library"),
            }
    for intent in intents:
        uid = str(intent.get("user_id") or "")
        if uid:
            reader = by_id.get(uid, {})
            by_id[uid] = {
                "user_id": uid,
                "email": intent.get("email", ""),
                "first_name": reader.get("first_name", ""),
                "last_name": reader.get("last_name", ""),
                "organization": reader.get("organization", ""),
                "role_title": reader.get("role_title", ""),
                "decision_context": "",
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


def _reflect_request_journey(people: list[dict], requests: list[dict]) -> list[dict]:
    """Keep owner relationship stages separate from the real request pipeline."""
    latest: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for req in sorted(requests, key=lambda x: str(x.get("created_at") or ""), reverse=True):
        uid = str(req.get("user_id") or "")
        if not uid:
            continue
        latest.setdefault(uid, req)
        counts[uid] = counts.get(uid, 0) + 1
    result = []
    for person in people:
        uid = str(person["user_id"])
        req = latest.get(uid)
        result.append({
            **person,
            "request_count": counts.get(uid, 0),
            "has_request": bool(req),
            "latest_request_status": str(req.get("status") or "") if req else "",
        })
    return result


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
    if person.get("onboarding") == "Reader only":
        st.info("This is a verified library reader, not yet an Advisory member. "
                "Use **Access & invitations** to invite this person to Advisory. "
                "No Advisory services are granted by an invitation.")
        return
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
        st.write("**Owner-managed relationship stage:** " + stage.title())
        st.write("**Latest request stage:** " +
                 (str(person.get("latest_request_status")).replace("_", " ").title()
                  if person.get("latest_request_status") else "No request submitted"))
        st.caption("Relationship planning is private. Client-facing request stages "
                   "must be changed from Requests & replies.")
        stage_choices = st.selectbox(
            "Private relationship stage", STAGES,
            index=STAGES.index(stage) if stage in STAGES else 0,
            key="advisory_owner_relationship_stage_" + uid,
        )
        if st.button("Save relationship stage",
                     disabled=stage_choices == stage,
                     key="advisory_owner_relationship_save_" + uid):
            try:
                _owner_action(token, uid, "stage", value=stage_choices)
                st.success("Relationship stage updated and audited.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Relationship stage could not be saved.")
        with st.form("advisory_next_action_" + uid):
            action = st.text_area(
                "Private relationship planning note (not visible to client)", value=str(person.get("next_action") or ""),
                max_chars=2000, height=75,
                help="Keep private client context relevant, proportionate and secure.",
            )
            save_action = st.form_submit_button("Save internal planning note")
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
    """One owner workspace for requests, entitlements and member relationships."""
    try:
        token = _verify_owner(owner_session)
    except (PermissionError, RuntimeError, ValueError, TimeoutError):
        st.error("Advisory Operations is restricted to the authenticated portfolio owner.")
        return

    st.title("Advisory Operations")
    notice = st.session_state.pop("advisory_ops_notification_flash", None)
    if notice:
        st.info(str(notice))
    st.caption(
        "A private control center for client requests, selective service access, "
        "reader invitations, relationships, feedback and audit history."
    )
    a, b, c = st.columns([1, 1, 1])
    with a:
        st.link_button("Public Advisory services",
                       "https://jairribeiro.com/?page=advisory", use_container_width=True)
    with b:
        st.link_button("Member sign-in",
                       "https://jairribeiro.com/?page=advisory-access", use_container_width=True)
    with c:
        if st.button("Refresh all records", key="advisory_owner_refresh", use_container_width=True):
            st.rerun()

    from page_owner_advisory_requests import (
        _read_owner_requests, _client_waiting, _overdue,
        render_advisory_action_inbox, read_request_history,
    )
    from page_owner_advisory_operations import (
        read_service_access, render_operations_overview, render_reader_invitations,
        render_service_access, render_request_pipeline,
    )
    try:
        profiles = _read_advisory(token, "portfolio_advisory_profiles")
        intents = _read_advisory(token, "portfolio_advisory_intents")
        controls = _read_advisory(token, "portfolio_advisory_admin_records")
        audit = _read_advisory(token, "portfolio_advisory_admin_audit")
        readers = _read_advisory(token, "portfolio_reader_profiles")
        requests = _read_owner_requests(token)
        access = read_service_access(token)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("Advisory management data could not be read. No changes have been made.")
        return

    people = _reflect_request_journey(_people(profiles, intents, controls, readers), requests)
    responded = sum(_client_waiting(r) for r in requests)
    overdue = sum(_overdue(r) for r in requests)
    if responded:
        st.warning(f"{responded} Advisory request(s) need a response.")
    if overdue:
        st.info(f"{overdue} client follow-up(s) are due.")
    st.caption(
        f"{len(profiles)} completed Advisory profiles · {len(intents)} invitations / signup intents · "
        f"{len(readers)} library members · {len(requests)} client requests"
    )
    overview, inbox, permission_tab, directory, pipeline, feedback_tab, audit_tab = st.tabs([
        "Overview", "Requests & replies", "Access & invitations",
        "Relationships", "Pipeline", "Service feedback", "Audit",
    ])

    with overview:
        render_operations_overview(people, requests, readers, access)

    with inbox:
        render_advisory_action_inbox(token, people, requests)

    with permission_tab:
        render_service_access(token, people, requests, access)
        st.divider()
        render_reader_invitations(token, readers, people)

    with directory:
        st.subheader("People & advisory relationships")
        st.caption("The directory includes library-only members so potential Advisory clients are not invisible.")
        search = st.text_input(
            "Search people", placeholder="Name, email, organization or business decision",
            key="advisory_owner_search",
        ).strip().casefold()
        membership = st.selectbox(
            "Membership", [
                "All people", "Reader only", "Advisory invitation pending",
                "Advisory profile completed", "Suspended Advisory",
            ], key="advisory_owner_filter",
        )
        matching = []
        for person in people:
            content = " ".join(str(person.get(k) or "") for k in (
                "first_name", "last_name", "email", "organization", "role_title",
                "decision_context", "advisory_focus",
            )).casefold()
            if search not in content:
                continue
            state = str(person.get("onboarding") or "")
            if membership == "Reader only" and state != "Reader only":
                continue
            if membership == "Advisory invitation pending" and state != "Pending onboarding":
                continue
            if membership == "Advisory profile completed" and state != "Profile completed":
                continue
            if membership == "Suspended Advisory" and person.get("account_status") != "suspended":
                continue
            matching.append(person)

        st.caption(f"{len(matching)} people match the selected filters.")
        st.dataframe([
            {
                "Name": " ".join(filter(None, (str(p.get("first_name") or ""),
                                               str(p.get("last_name") or "")))),
                "Email": str(p.get("email") or ""),
                "Organization": str(p.get("organization") or ""),
                "Membership": str(p.get("onboarding") or ""),
                "Access": str(p.get("account_status") or "").title(),
                "Relationship stage": str(p.get("relationship_stage") or "—").title(),
                "Requests": int(p.get("request_count") or 0),
                "Latest request": str(p.get("latest_request_status") or "—").replace("_", " ").title(),
                "Follow-up": str(p.get("follow_up_on") or "—"),
            } for p in matching[:500]
        ], hide_index=True, use_container_width=True)
        if len(matching) > 500:
            st.caption("Showing the first 500 results. Narrow your search to select a particular member.")
        if matching:
            by_id = {str(p["user_id"]): p for p in matching}
            selected_id = st.selectbox(
                "Open relationship record", list(by_id),
                format_func=lambda uid: str(by_id[uid].get("email") or uid),
                key="advisory_owner_selected_id",
            )
            st.divider()
            _details(token, by_id[selected_id])

        csv = _csv_bytes(
            ["Email", "Name", "Organization", "Membership", "Stage", "Requests",
             "Follow-up", "Registered"],
            [[p.get("email"), " ".join(filter(None, (p.get("first_name"), p.get("last_name")))),
              p.get("organization"), p.get("onboarding"), p.get("relationship_stage"),
              p.get("request_count"), p.get("follow_up_on"), p.get("created_at")]
             for p in matching],
        )
        st.download_button(
            "Export filtered directory (CSV)", data=csv,
            file_name="jairribeiro-advisory-relationships.csv",
            mime="text/csv", disabled=not matching, key="advisory_owner_directory_csv",
        )

    with pipeline:
        render_request_pipeline(people, requests)

    with feedback_tab:
        from page_owner_advisory_feedback import render_owner_feedback
        render_owner_feedback(token, people)

    with audit_tab:
        st.subheader("Change history")
        st.caption("Request transitions, service entitlements and account changes are logged separately.")
        try:
            request_history = read_request_history(token)
            scorecard_history = _read_advisory(token, "portfolio_advisory_scorecard_audit")
            rollout_history = _read_advisory(token, "portfolio_advisory_rollout_audit")
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            st.error("Some audit records are temporarily unavailable.")
            request_history, scorecard_history, rollout_history = [], [], []
        st.markdown("#### Client request decisions")
        if request_history:
            labels = {str(r.get("id")): str(r.get("title") or "Request") for r in requests}
            st.dataframe([{
                "When": str(r.get("created_at") or "")[:19],
                "Request": labels.get(str(r.get("request_id")), "Historical request"),
                "Action": str(r.get("action") or ""),
                "From": str(r.get("old_status") or ""),
                "To": str(r.get("new_status") or ""),
            } for r in request_history], hide_index=True, use_container_width=True)
        else:
            st.caption("No recorded request changes.")
        st.markdown("#### Service access changes")
        score_ids = {str(x.get("id")): str(x.get("request_id")) for x in access.get("scorecard", [])}
        roll_ids = {str(x.get("id")): str(x.get("request_id")) for x in access.get("rollout", [])}
        service_events = (
            [{"Service": "Scorecard", "Request ID": score_ids.get(str(x.get("scorecard_id")), ""),
              **x} for x in scorecard_history]
            + [{"Service": "Rollout", "Request ID": roll_ids.get(str(x.get("access_id")), ""),
                **x} for x in rollout_history]
        )
        if service_events:
            st.dataframe([{
                "When": str(r.get("created_at") or "")[:19],
                "Service": str(r.get("Service") or ""),
                "Action": str(r.get("action") or ""),
                "Request": str(r.get("Request ID") or ""),
            } for r in sorted(service_events, key=lambda x: str(x.get("created_at") or ""), reverse=True)],
                hide_index=True, use_container_width=True)
        else:
            st.caption("No recorded service entitlement changes.")
        st.markdown("#### Membership and relationship administration")
        if audit:
            by_id = {str(p["user_id"]): str(p.get("email") or "") for p in people}
            st.dataframe([{
                "When": str(r.get("created_at") or "")[:19],
                "Person": by_id.get(str(r.get("user_id")), "Former account"),
                "Action": str(r.get("action") or ""),
                "Detail": str(r.get("detail") or ""),
            } for r in audit[:500]], hide_index=True, use_container_width=True)
        else:
            st.caption("No recorded membership administration.")
