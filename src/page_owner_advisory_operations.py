"""Owner-only advisory operations: access, reader invitations and truthful pipeline.

Every entitlement change goes through an independently authorized database RPC.
Owner service approval is independent of the relationship/engagement stage.
Each new approval creates a transactional-email notification record.
Reader onboarding invitations do not grant service access or send email.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from site_cms import _request_json, _rest_url
from advisory_approval_email import deliver_approval_notice, approval_notice_message
from page_owner_advisory_requests import _client_waiting, _overdue
from page_advisory_client_journey import STATUS

STAGES = ("inquiry", "discovery", "proposal", "engaged", "closed")
SERVICES = (
    ("scorecard", "AI Portfolio Prioritization Scorecard",
     "portfolio_advisory_scorecard_owner_action_v1",
     "portfolio_advisory_scorecards"),
    ("rollout", "Enterprise AI Rollout Readiness",
     "portfolio_advisory_rollout_owner_action_v1",
     "portfolio_advisory_rollout_access"),
)
PIPELINE = (
    ("Intake & review", ("submitted", "reviewing", "awaiting_client")),
    ("Qualification", ("discovery", "proposal")),
    ("Delivery & handover", ("active", "completed")),
    ("Closed", ("closed", "declined")),
)


def _today() -> date:
    return datetime.now(ZoneInfo("Europe/Stockholm")).date()


def _read_access(token: str, table: str) -> list[dict]:
    if table not in {"portfolio_advisory_scorecards", "portfolio_advisory_rollout_access"}:
        raise ValueError("Unsupported service entitlement")
    data = _request_json(
        "GET", _rest_url(table + "?select=id,request_id,user_id,status,approved_at,revoked_at"
                         "&order=approved_at.desc&limit=1000"),
        token=token, timeout=15,
    )
    if not isinstance(data, list):
        raise RuntimeError("Service entitlements unavailable")
    return data


def read_service_access(token: str) -> dict[str, list[dict]]:
    return {key: _read_access(token, table) for key, _, _, table in SERVICES}


def _service_action(token: str, request_id: str, service_key: str, action: str) -> dict:
    found = next((s for s in SERVICES if s[0] == service_key), None)
    if not found or action not in {"approve", "revoke"}:
        raise ValueError("Unsupported service access action")
    result = _request_json(
        "POST", _rest_url("rpc/" + found[2]), token=token,
        payload={"p_request_id": request_id, "p_action": action}, timeout=16,
    )
    if not isinstance(result, dict) or result.get("status") != (
        "active" if action == "approve" else "revoked"
    ):
        raise RuntimeError("Service permission change was not confirmed")
    return result


def _latest_notification(token: str, request_id: str, service: str) -> dict | None:
    if service not in ("scorecard", "rollout"):
        raise ValueError("Unsupported notification type")
    rows = _request_json(
        "GET", _rest_url(
            "portfolio_advisory_approval_notifications?"
            "select=id,state,error_category,created_at,sent_at,attempts"
            "&request_id=eq." + request_id + "&service_key=eq." + service
            + "&order=created_at.desc&limit=1"
        ), token=token, timeout=12,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Email status unavailable")
    return rows[0] if rows else None


def _approval_decision(token: str, rid: str, service: str) -> str:
    """One owner action: approve access, then immediately dispatch its email."""
    result = _service_action(token, rid, service, "approve")
    if result.get("unchanged"):
        return "Service access was already approved. No duplicate email was created."
    notification_id = str(result.get("notification_id") or "")
    if not notification_id:
        return ("Access granted, but no email event was returned. "
                "Check the notification log before retrying.")
    try:
        delivery = deliver_approval_notice(token, notification_id)
        return approval_notice_message(delivery)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        return ("Access granted and an email event was created, but delivery could not "
                "be confirmed. Check the email status below and retry if needed.")


def _notice_panel(token: str, rid: str, service: str, prefix: str) -> None:
    """Report provider acceptance separately from the actual access decision."""
    try:
        notice = _latest_notification(token, rid, service)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.warning("Email delivery status is temporarily unavailable.")
        return
    if notice is None:
        st.caption("No approval notification recorded for this service.")
        return
    state = str(notice.get("state") or "pending")
    labels = {
        "sent": "Supabase Auth accepted access email request",
        "pending": "Awaiting email delivery",
        "sending": "Sending notification",
        "failed": "Supabase access email failed — retry available",
    }
    st.caption("Client notification: " + labels.get(state, state)
               + (" · " + str(notice.get("sent_at") or "")[:16].replace("T", " ")
                  if state == "sent" else ""))
    if state in ("pending", "failed"):
        if st.button("Retry Supabase access email", key=prefix + "_email_retry_" + rid + "_" + service):
            try:
                outcome = deliver_approval_notice(token, str(notice["id"]))
                st.session_state["advisory_ops_notification_flash"] = approval_notice_message(outcome)
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError):
                st.error("The email attempt could not be completed. The grant is unchanged.")


def _invite_reader(token: str, user_id: str) -> str:
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_owner_invite_reader_v1"),
        token=token, payload={"p_user_id": user_id}, timeout=16,
    )
    if not isinstance(result, dict) or str(result.get("user_id")) != user_id:
        raise RuntimeError("Reader invitation was not confirmed")
    status = str(result.get("status") or "")
    if status not in {"invited", "already_invited", "already_member"}:
        raise RuntimeError("Unexpected invitation result")
    return status


def _name(p: dict) -> str:
    return " ".join(filter(None, (
        str(p.get("first_name") or "").strip(),
        str(p.get("last_name") or "").strip(),
    ))) or str(p.get("email") or "Reader")


def _priority_label(request: dict) -> str:
    if _client_waiting(request):
        return "Response required"
    if _overdue(request):
        return "Follow-up due"
    if request.get("status") == "awaiting_client":
        return "Waiting for client"
    if request.get("status") in ("closed", "declined"):
        return "Closed"
    return "In progress"


def _service_status(access: dict[str, list[dict]], request_id: str, service: str) -> str:
    row = next((x for x in access.get(service, [])
                if str(x.get("request_id") or "") == request_id), None)
    return str(row.get("status") or "Not granted") if row else "Not granted"


def render_operations_overview(people: list[dict], requests: list[dict],
                               readers: list[dict], access: dict[str, list[dict]]) -> None:
    st.subheader("What needs a decision")
    pmap = {str(p["user_id"]): p for p in people}
    awaiting = [r for r in requests if _client_waiting(r)]
    due = [r for r in requests if _overdue(r)]
    open_requests = [r for r in requests if r.get("status") not in ("closed", "declined")]
    active = [r for r in requests if r.get("status") == "active"]
    reader_only = [p for p in readers if pmap.get(str(p.get("user_id") or ""), {}).get("onboarding") == "Reader only"]

    k = st.columns(5)
    k[0].metric("Needs reply", len(awaiting))
    k[1].metric("Follow-ups due", len(due))
    k[2].metric("Open requests", len(open_requests))
    k[3].metric("Agreed engagements", len(active))
    k[4].metric("Reader-only members", len(reader_only))
    st.caption("Engagements count client requests at the active stage, not account registrations.")

    relevant = sorted(
        (r for r in requests if _client_waiting(r) or _overdue(r)
         or r.get("status") in ("submitted", "reviewing")),
        key=lambda r: (
            0 if _client_waiting(r) else 1 if _overdue(r) else 2,
            str(r.get("updated_at") or ""),
        ),
    )
    if relevant:
        st.markdown("#### Priority queue")
        st.dataframe([
            {
                "Action": _priority_label(r),
                "Client": str(pmap.get(str(r.get("user_id")), {}).get("email") or "Unknown"),
                "Business decision": str(r.get("title") or ""),
                "Request stage": STATUS.get(str(r.get("status")), (str(r.get("status")), ""))[0],
                "Follow-up": str(r.get("follow_up_on") or "—"),
            } for r in relevant[:30]
        ], hide_index=True, use_container_width=True)
        st.caption("Use **Requests & replies** to open a request, respond and confirm its next stage.")
    else:
        st.success("No outstanding replies or due follow-ups in the current records.")

    st.markdown("#### Service entitlement snapshot")
    cols = st.columns(2)
    for col, (key, label, _, _) in zip(cols, SERVICES):
        with col:
            granted = [x for x in access.get(key, []) if x.get("status") == "active"]
            eligible = {str(r["id"]): r for r in requests
                        if r.get("status") not in ("closed", "declined")}
            operational = sum(str(x.get("request_id")) in eligible for x in granted)
            st.metric(label, operational)
            st.caption("Approved individual service access (not a paid engagement)")


def _render_request_service_controls(
    token: str, req: dict, access: dict[str, list[dict]], *, prefix: str
) -> None:
    rid = str(req.get("id") or "")
    if not rid:
        return
    stage = str(req.get("status") or "submitted")
    eligible = stage not in ("closed", "declined")
    st.caption(
        "Owner approval grants this service directly. No discovery, proposal or "
        "engagement-stage update is required. The request journey remains unchanged."
    )
    st.caption(
        "Emails use the same Supabase Auth email system as Library and Advisory "
        "registration. The email contains an account-access link, while the "
        "approved service is identified in the member portal."
    )
    if not eligible:
        st.warning("This request is closed. Reopen it before granting a new service.")
    for service, label, _, _ in SERVICES:
        current = _service_status(access, rid, service)
        with st.container(border=True):
            st.markdown("**" + label + "**")
            st.write("Access: **" + ("Approved" if current == "active" else current.title()) + "**")
            if current == "active":
                _notice_panel(token, rid, service, prefix)
                if st.button("Revoke access", key=prefix + "_revoke_" + rid + "_" + service):
                    try:
                        _service_action(token, rid, service, "revoke")
                        st.session_state["advisory_ops_notification_flash"] = (
                            label + ": access revoked. Previous assessments were retained."
                        )
                        st.rerun()
                    except (RuntimeError, ValueError, TimeoutError, KeyError):
                        st.error("Access revocation could not be confirmed.")
            else:
                if st.button(
                    "Approve access & send Supabase email",
                    key=prefix + "_approve_" + rid + "_" + service,
                    type="primary", disabled=not eligible,
                    help="Grants this individual service and sends an access email. "
                         "No relationship stage change is required.",
                ):
                    try:
                        message = _approval_decision(token, rid, service)
                        st.session_state["advisory_ops_notification_flash"] = label + ": " + message
                        st.rerun()
                    except (RuntimeError, ValueError, TimeoutError, KeyError) as exc:
                        st.error("Service approval was not confirmed: " + str(exc))


def render_service_access_for_request(token: str, req: dict) -> None:
    """Inline single-step approval from the selected request's Action inbox."""
    st.markdown("#### Individual service access")
    st.caption("Approve directly here. Each new grant generates a client email notification.")
    try:
        access = read_service_access(token)
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("Service access status could not be verified.")
        return
    _render_request_service_controls(token, req, access, prefix="inbox")


def render_service_access(token: str, people: list[dict], requests: list[dict],
                          access: dict[str, list[dict]]) -> None:
    st.subheader("Service access & approval")
    st.caption(
        "Select the user and service, then approve. A confirmation email is sent "
        "to their verified address and its outcome recorded. Approval does not "
        "change the Advisory relationship pipeline or create a paid engagement."
    )
    if not requests:
        st.info("No Advisory requests yet. Ask the client to submit a request before choosing a service.")
        return
    people_by_id = {str(p["user_id"]): p for p in people}
    ordered = sorted(requests, key=lambda r: (
        r.get("status") in ("closed", "declined"),
        not _client_waiting(r),
        str(r.get("updated_at") or ""),
    ))
    st.dataframe([
        {
            "Client": str(people_by_id.get(str(r.get("user_id")), {}).get("email") or "Unknown"),
            "Request": str(r.get("title") or ""),
            "Status": STATUS.get(str(r.get("status")), (str(r.get("status")), ""))[0],
            "Scorecard": _service_status(access, str(r["id"]), "scorecard"),
            "Rollout": _service_status(access, str(r["id"]), "rollout"),
        } for r in ordered
    ], hide_index=True, use_container_width=True)
    choices = {str(r["id"]): r for r in ordered}
    rid = st.selectbox(
        "Choose a client request", list(choices),
        format_func=lambda value: (
            str(people_by_id.get(str(choices[value].get("user_id")), {}).get("email") or "Client")
            + " · " + str(choices[value].get("title") or "Advisory request")
        ),
        key="advisory_ops_service_request",
    )
    req = choices[rid]
    st.write("**Business outcome:** " + str(req.get("desired_outcome") or "Not provided"))
    _render_request_service_controls(token, req, access, prefix="services")


def render_reader_invitations(token: str, readers: list[dict],
                              people: list[dict]) -> None:
    st.subheader("Promote a library reader to Advisory")
    notice = st.session_state.pop("advisory_ops_invite_notice", None)
    if notice:
        st.success(notice)
    st.caption(
        "Invite an existing verified reader without creating a duplicate identity or "
        "changing their editorial consent. The member must sign in and complete their "
        "Advisory professional details before using the service. No invitation email is "
        "automatically sent."
    )
    eligible = [p for p in readers if p.get("user_id")
                and next((person.get("onboarding") for person in people
                          if str(person.get("user_id")) == str(p["user_id"])), None) == "Reader only"]
    st.metric("Library members without Advisory onboarding", len(eligible))
    if not eligible:
        st.info("No reader-only memberships currently available for invitation.")
        return
    search = st.text_input(
        "Find a reader", placeholder="Search reader name, organization or email",
        key="advisory_ops_reader_search",
    ).strip().casefold()
    matching = [p for p in eligible if search in " ".join(str(p.get(k) or "") for k in (
        "email", "first_name", "last_name", "organization", "job_title"
    )).casefold()]
    if not matching:
        st.info("No matching library members.")
        return
    st.dataframe([
        {
            "Name": _name(p),
            "Email": str(p.get("email") or ""),
            "Role": str(p.get("job_title") or ""),
            "Organization": str(p.get("organization") or ""),
        } for p in matching[:100]
    ], hide_index=True, use_container_width=True)
    by_id = {str(p["user_id"]): p for p in matching}
    uid = st.selectbox("Select member", list(by_id), key="advisory_ops_promote_user",
                       format_func=lambda value: (
                           _name(by_id[value]) + " · " + str(by_id[value].get("email") or "")
                       ))
    target = by_id[uid]
    with st.form("advisory_ops_invite_" + uid):
        email = str(target.get("email") or "")
        typed = st.text_input("Type the reader's email to confirm the invitation")
        submitted = st.form_submit_button("Invite to Advisory", type="primary")
    if submitted:
        if typed.strip().casefold() != email.strip().casefold():
            st.error("The email confirmation does not match.")
        else:
            try:
                outcome = _invite_reader(token, uid)
                st.session_state["advisory_ops_invite_notice"] = ({
                    "invited": "Advisory invitation recorded.",
                    "already_invited": "A pending invitation already exists.",
                    "already_member": "This reader already has an Advisory account.",
                }[outcome] + " Share https://jairribeiro.com/?page=advisory-access "
                  "with the member; no message was automatically sent and no "
                  "individual service entitlement was granted.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError) as exc:
                st.error("Could not record this invitation: " + str(exc))


def render_request_pipeline(people: list[dict], requests: list[dict]) -> None:
    st.subheader("Request journey")
    st.caption(
        "One card per client request, including historical requests. Counts are not "
        "inferred from account registrations or overwritten by the latest request."
    )
    by_uid = {str(p["user_id"]): p for p in people}
    for heading, statuses in PIPELINE:
        group = [r for r in requests if r.get("status") in statuses]
        with st.expander(f"{heading} · {len(group)}", expanded=heading != "Closed"):
            if not group:
                st.caption("No requests in this part of the journey.")
                continue
            st.dataframe([
                {
                    "Client": str(by_uid.get(str(r.get("user_id")), {}).get("email") or "Unknown"),
                    "Business decision": str(r.get("title") or ""),
                    "Stage": STATUS.get(str(r.get("status")), (str(r.get("status")), ""))[0],
                    "Attention": _priority_label(r),
                    "Follow-up": str(r.get("follow_up_on") or "—"),
                    "Last updated": str(r.get("updated_at") or "")[:10],
                } for r in sorted(group, key=lambda r: str(r.get("updated_at") or ""), reverse=True)
            ], hide_index=True, use_container_width=True)
    st.markdown("#### Relationship planning")
    st.caption(
        "This is the private relationship view. Owner-managed stages, notes and "
        "follow-up dates are separate from the status of an individual client request. "
        "Edit a relationship from **Relationships**."
    )
    planned = [p for p in people if p.get("onboarding") != "Reader only"]
    st.dataframe([
        {
            "Person": str(p.get("email") or ""),
            "Owner relationship stage": str(p.get("relationship_stage") or "inquiry").title(),
            "Latest request": str(p.get("latest_request_status") or "No request").replace("_", " ").title(),
            "Next owner action": str(p.get("next_action") or ""),
            "Follow-up": str(p.get("follow_up_on") or "—"),
            "Due": bool(p.get("follow_up_on") and str(p["follow_up_on"])[:10] <= _today().isoformat()),
        } for p in sorted(planned, key=lambda p: (
            not bool(p.get("follow_up_on")),
            str(p.get("follow_up_on") or "9999"),
        ))
    ], hide_index=True, use_container_width=True)
