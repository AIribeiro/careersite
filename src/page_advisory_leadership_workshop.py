"""Self-service Executive AI Leadership Workshop in the existing Advisory member area.

Verified Advisory accounts only; data reads and writes use a member token and
Supabase row-level security. No service-role access or marketing enrollment.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from urllib.parse import quote
import re

import streamlit as st

from site_cms import _request_json, _rest_url
from page_advisory_shared_ui import service_overview
from page_advisory_leadership_logic import (
    MODEL_VERSION, CONTEXT, DIMENSIONS, RESPONSES, EXERCISES, assess,
    clean_answers, clean_exercises, interpret_exercise, aggregate_team,
)
from page_advisory_leadership_report import render_leadership_pdf

SECTIONS = ("overview", "new", "history", "workspace", "invitations")
LABELS = {"overview": "About the service", "new": "New workshop",
          "history": "My workshops", "workspace": "Open workshop",
          "invitations": "Invitations"}
OWNER_ROLES = ("Executive sponsor", "Business process owner", "AI / data leader",
               "Operations leader", "Technology leader", "Risk / governance lead",
               "Finance leader", "People / change leader", "To be assigned")
DECISIONS = ("Proceed with defined leadership actions", "Test a change before scaling",
             "Pause the next commitment", "Request more evidence", "Stop or redesign the proposal")
REVIEW = ("Within 30 days", "Next quarter", "Next 6 months", "To be agreed")
EMAIL = re.compile(r"^[^@\s<>]{1,64}@[^@\s<>]{1,189}$")
WORKSHOP_CSS = """
<style>
.st-key-leadership_workspace [data-testid="stVerticalBlockBorderWrapper"]{
border-color:#d9d4cc!important;border-radius:9px!important}
.st-key-leadership_workspace [data-testid="stMetric"]{
border:0!important;background:#f7f5f0;padding:14px!important}
.st-key-leadership_workspace [data-testid="stSelectbox"]{min-width:0}
@media(max-width:650px){
.st-key-leadership_workspace .stHorizontalBlock{flex-wrap:wrap!important}
.st-key-leadership_workspace .stColumn{min-width:min(100%,290px)!important}
}
</style>
"""


def _url(path: str) -> str:
    return _rest_url(path)


def _api(method: str, path: str, token: str, payload: dict | None = None,
         *, returning: bool = False):
    kwargs = {"token": token, "timeout": 16}
    if payload is not None:
        kwargs["payload"] = payload
    if returning:
        kwargs["prefer"] = "return=representation"
    return _request_json(method, _url(path), **kwargs)


def _workshops(token: str) -> list[dict]:
    data = _api("GET", "portfolio_leadership_workshops?"
        "select=id,title,owner_id,mode,context,decisions,status,model_version,created_at,updated_at"
        "&order=updated_at.desc&limit=80", token)
    if not isinstance(data, list):
        raise RuntimeError("Workshop history is unavailable.")
    return data


def _participants(token: str, wid: str) -> list[dict]:
    data = _api("GET", "portfolio_leadership_participants?"
        "select=id,workshop_id,owner_id,invited_email,user_id,status,share_answers,completed,invited_at"
        "&workshop_id=eq." + quote(wid, safe="") + "&order=invited_at.asc&limit=25", token)
    if not isinstance(data, list):
        raise RuntimeError("Workshop invitations are unavailable.")
    return data


def _responses(token: str, wid: str) -> list[dict]:
    data = _api("GET", "portfolio_leadership_responses?"
        "select=id,workshop_id,participant_id,user_id,answers,exercises,completed,model_version,updated_at"
        "&workshop_id=eq." + quote(wid, safe="") + "&limit=25", token)
    if not isinstance(data, list):
        raise RuntimeError("Assessment records are unavailable.")
    return data


def _pending(token: str, email: str) -> list[dict]:
    safe = quote(email.lower(), safe="")
    data = _api("GET", "portfolio_leadership_participants?"
        "select=id,workshop_id,invited_email,status"
        "&status=eq.invited&user_id=is.null&invited_email=eq."
        + safe + "&order=invited_at.desc&limit=25", token)
    return data if isinstance(data, list) else []


def _new_workshop(token: str, uid: str, email: str, title: str,
                  mode: str, context: dict) -> str:
    name = str(title).strip()
    if not 5 <= len(name) <= 140 or mode not in ("individual", "team"):
        raise ValueError("Use a short, non-confidential title of 5–140 characters.")
    if not isinstance(context, dict) or any(context.get(k) not in options for k, options in CONTEXT.items() if k != "mode"):
        raise ValueError("Choose the relevant organizational context.")
    if context.get("mode") != mode:
        raise ValueError("Workshop format is inconsistent.")
    rows = _api("POST", "portfolio_leadership_workshops?select=id",
                token, {"owner_id": uid, "title": name, "mode": mode,
                        "context": context, "model_version": MODEL_VERSION},
                returning=True)
    if not isinstance(rows, list) or len(rows) != 1 or not rows[0].get("id"):
        raise RuntimeError("The workshop was not saved.")
    wid = str(rows[0]["id"])
    accepted = _api("POST", "portfolio_leadership_participants?select=id",
                    token, {"owner_id": uid, "workshop_id": wid, "user_id": uid,
                            "invited_email": email.lower(), "status": "accepted",
                            "share_answers": True}, returning=True)
    if not isinstance(accepted, list) or not accepted:
        raise RuntimeError("Workshop created, but organizer membership could not be verified. Open it from history and contact support.")
    return wid


def _save_response(token: str, uid: str, wid: str, member: dict,
                   old: dict | None, answers: dict, exercises: dict) -> None:
    answers = clean_answers(answers)
    exercises = clean_exercises(exercises)
    result = assess(answers)
    required = result["scenarios"]
    completed = bool(result["complete"] and len(required) == 2
                     and all(s in exercises for s in required))
    payload = {"answers": answers, "exercises": exercises,
               "completed": completed, "model_version": MODEL_VERSION,
               "updated_at": datetime.now(timezone.utc).isoformat()}
    if old:
        saved = _api("PATCH", "portfolio_leadership_responses?id=eq." +
                     quote(str(old["id"]), safe="") + "&select=id",
                     token, payload, returning=True)
    else:
        payload.update({"workshop_id": wid, "participant_id": member["id"],
                        "owner_id": member["owner_id"], "user_id": uid})
        saved = _api("POST", "portfolio_leadership_responses?select=id",
                     token, payload, returning=True)
    if not isinstance(saved, list) or len(saved) != 1:
        raise RuntimeError("The assessment save was not confirmed.")
    changed = _api("PATCH", "portfolio_leadership_participants?id=eq." +
                   quote(str(member["id"]), safe="") + "&select=id",
                   token, {"completed": completed}, returning=True)
    if not isinstance(changed, list) or len(changed) != 1:
        raise RuntimeError("Saved answers, but completion status could not be confirmed.")


def _go(section: str, wid: str = "", detail: str = "") -> None:
    if section not in SECTIONS:
        return
    st.query_params["workshop_section"] = section
    if wid:
        st.query_params["workshop_id"] = wid
    elif section != "workspace":
        st.query_params.pop("workshop_id", None)
    if detail:
        st.query_params["workshop_detail"] = detail
    elif section != "workspace":
        st.query_params.pop("workshop_detail", None)
    st.rerun()


def _nav_changed() -> None:
    v = st.session_state.get("leadership_workshop_nav")
    if v in SECTIONS:
        st.query_params["workshop_section"] = v


def _navigation() -> str:
    v = str(st.query_params.get("workshop_section") or "overview")
    if v not in SECTIONS:
        v = "overview"
    if st.session_state.get("leadership_workshop_nav") != v:
        st.session_state["leadership_workshop_nav"] = v
    st.pills("Leadership workshop sections", SECTIONS,
             format_func=lambda x: LABELS[x], selection_mode="single",
             required=True, key="leadership_workshop_nav",
             on_change=_nav_changed, label_visibility="collapsed",
             wrap=False, width="stretch")
    return v


def _overview(items: list[dict]) -> None:
    service_overview(
        hero="Are we ready to lead AI adoption, not just deploy it?",
        description=("Examine how executives set AI priorities, own decisions, govern risk "
                     "and change work. Complete an evidence-led leadership assessment "
                     "and turn its findings into an agreed decision agenda."),
        access="Free with verified Advisory registration",
        assessment_format="Individual or leadership-team workshop",
        saved_count=len(items),
        outputs=(
            ("Leadership profile", "Seven dimensions of organizational practice",
             "21 structured questions with explicit evidence limits and critical decision gates."),
            ("Discussion agenda", "Realistic executive dilemmas",
             "Preselected choices expose trade-offs in investment, adoption, authority and trust."),
            ("Decision brief", "Owned priorities and private PDF",
             "Three evidence-led actions, suggested accountable roles and review conditions."),
        ),
        steps=(
            ("Create a workspace", "Choose a non-confidential topic and individual or team format."),
            ("Assess and discuss", "Save answers, complete two leadership dilemmas and review the evidence."),
            ("Document the decision", "Record responsible roles, download the brief and revisit results."),
        ),
        boundary=("Ratings and recommendations depend on participants' self-reported answers. "
                  "Team members must opt in before organizers can see individual responses. "
                  "This service does not certify maturity or approve AI investments or deployment."),
    )
    if items:
        current = items[0]
        with st.container(border=True):
            st.caption("Your most recent workshop")
            st.markdown("#### " + str(current["title"]))
            st.caption(str(current["mode"]).title() + " · " + str(current["status"]).title())
            if st.button("Continue this workshop", type="primary",
                         key="leadership_latest"):
                _go("workspace", str(current["id"]))
    if st.button("Create a leadership workshop", type="primary",
                 key="leadership_new_home"):
        _go("new")


def _new(token: str, uid: str, email: str) -> None:
    st.markdown("### New leadership workshop")
    st.caption("One workshop stores its own answers, discussions and decision record. "
               "Avoid confidential business or employee information.")
    with st.form("leadership_create_form"):
        title = st.text_input("Workshop title", max_chars=140,
                              placeholder="e.g. Enterprise AI adoption leadership review")
        mode = st.radio("Participation format",
                        ("individual", "team"), horizontal=True,
                        format_func=lambda x: "Individual executive" if x == "individual" else "Leadership team")
        context = {"mode": mode}
        c1, c2 = st.columns(2)
        for i, (k, options) in enumerate(CONTEXT.items()):
            if k == "mode":
                continue
            with (c1 if i % 2 == 0 else c2):
                context[k] = st.selectbox(k.replace("_", " ").title(),
                                          options, index=None, placeholder="Select one")
        created = st.form_submit_button("Create free workshop", type="primary",
                                        use_container_width=True)
    if created:
        try:
            wid = _new_workshop(token, uid, email, title, mode, context)
            st.success("Your private workshop was created.")
            _go("workspace", wid)
        except ValueError as exc:
            st.warning(str(exc))
        except (RuntimeError, TimeoutError, KeyError):
            st.error("Could not confirm workshop creation. Check My workshops before retrying.")


def _history(items: list[dict]) -> None:
    st.markdown("### My leadership workshops")
    st.caption("Open a saved assessment to continue, revisit its decisions or download a report.")
    if not items:
        st.info("No saved workshops yet.")
        if st.button("Start my first workshop", type="primary"):
            _go("new")
        return
    search = st.text_input("Find a workshop", placeholder="Search title")
    visible = [w for w in items if search.casefold().strip() in w["title"].casefold()]
    for w in visible:
        with st.container(border=True):
            a, b = st.columns([3, 1], gap="small")
            with a:
                st.markdown("**" + escape(w["title"]) + "**")
                st.caption(str(w["mode"]).title() + " · " + str(w["status"]).title() +
                           " · Updated " + str(w["updated_at"])[:10])
            with b:
                if st.button("Open workshop", key="leadership_history_" + str(w["id"]),
                             use_container_width=True):
                    _go("workspace", str(w["id"]))


def _invitations(token: str, uid: str, email: str) -> None:
    st.markdown("### Leadership-team invitations")
    st.caption("Only invitations sent to your verified account email can be accepted.")
    pending = _pending(token, email)
    if not pending:
        st.info("No pending invitations for this account.")
        return
    for invite in pending:
        with st.container(border=True):
            st.write("Invitation to a private leadership-team workshop")
            share = st.checkbox("Allow the organizer to see my individual assessment and "
                                "include it in team findings (optional).",
                                key="leadership_share_" + str(invite["id"]))
            a,b = st.columns(2)
            with a:
                accept = st.button("Accept invitation", type="primary",
                                   key="leadership_accept_" + str(invite["id"]))
            with b:
                decline = st.button("Decline", key="leadership_decline_" + str(invite["id"]))
            if accept or decline:
                status = "accepted" if accept else "declined"
                updated = _api("PATCH",
                               "portfolio_leadership_participants?id=eq." +
                               quote(str(invite["id"]), safe="") + "&select=id",
                               token, {"user_id": uid, "status": status,
                                       "share_answers": bool(share) if accept else False,
                                       "responded_at": datetime.now(timezone.utc).isoformat()},
                               returning=True)
                if not isinstance(updated, list) or len(updated) != 1:
                    st.error("The invitation response could not be confirmed.")
                elif accept:
                    st.success("Invitation accepted.")
                    _go("workspace", str(invite["workshop_id"]))
                else:
                    st.success("Invitation declined.")
                    st.rerun()


def _answer_form(token: str, uid: str, wid: str, member: dict,
                 old: dict | None) -> None:
    current = clean_answers((old or {}).get("answers") or {})
    st.markdown("### Leadership readiness assessment")
    st.caption("21 questions · Seven dimensions. Choose evidence of current practice, "
               "not planned future capability. Use Save progress whenever you need to stop.")
    current_result = assess(current)
    st.progress(current_result["answered"] / 21,
                text=f"{current_result['answered']} of 21 answers saved")
    with st.form("leadership_questions_" + wid, clear_on_submit=False):
        tabs = st.tabs([f"{i+1:02d} · {title}" for i, (_, title, _, _) in enumerate(DIMENSIONS)])
        choices = {}
        for tab, (_, title, _, questions) in zip(tabs, DIMENSIONS):
            with tab:
                st.caption("Select the closest demonstrated condition in your organization.")
                for key, question, why, action, owner in questions:
                    previous = current.get(key)
                    choices[key] = st.selectbox(
                        question, options=list(range(4)), index=previous,
                        placeholder="Select one, or leave unassessed",
                        format_func=lambda v: RESPONSES[v],
                        help=why,
                        key="leadership_q_" + wid + key,
                    )
        a, b = st.columns(2)
        with a:
            save = st.form_submit_button("Save progress", use_container_width=True)
        with b:
            proceed = st.form_submit_button("Save and review exercises",
                                             type="primary", use_container_width=True)
    if save or proceed:
        try:
            # Every dropdown can remain unanswered while drafting.
            _save_response(token, uid, wid, member, old, choices,
                           (old or {}).get("exercises") or {})
            if proceed:
                _go("workspace", wid, "exercises")
            st.success("Your answers were saved to this private workshop.")
            st.rerun()
        except ValueError as exc:
            st.warning(str(exc))
        except (RuntimeError, TimeoutError, KeyError):
            st.error("The answers could not be saved. Review the entries and try again.")


def _exercise_form(token: str, uid: str, wid: str, member: dict,
                   old: dict | None) -> None:
    answers = (old or {}).get("answers") or {}
    result = assess(answers)
    selected = result["scenarios"]
    st.markdown("### Executive discussion exercises")
    st.caption("The two scenarios relate to the assessed leadership gaps. "
               "Responses reveal reasoning and trade-offs; they are not a certification test.")
    with st.form("leadership_exercises_" + wid):
        chosen = {}
        for key in selected:
            item = EXERCISES[key]
            st.markdown("#### " + item["title"])
            st.write(item["scenario"])
            previous = ((old or {}).get("exercises") or {}).get(key)
            chosen[key] = st.radio("What should leadership do first?",
                options=list(range(4)), index=previous,
                format_func=lambda i, k=key: EXERCISES[k]["choices"][i],
                key="leadership_ex_" + wid + key)
            st.caption("Trade-off to discuss: " + item["tradeoff"])
            st.divider()
        save = st.form_submit_button("Save exercises and review findings", type="primary",
                                      use_container_width=True)
    if save:
        if any(v is None for v in chosen.values()):
            st.warning("Choose a response for both dilemmas.")
            return
        try:
            merged = dict((old or {}).get("exercises") or {})
            merged.update(chosen)
            _save_response(token, uid, wid, member, old, answers, merged)
            _go("workspace", wid, "findings")
        except (ValueError, RuntimeError, TimeoutError, KeyError):
            st.error("Exercise results could not be saved. Please retry.")
    if old:
        for key in selected:
            if key in (old.get("exercises") or {}):
                interpretation = interpret_exercise(key, old["exercises"][key])
                with st.expander("Decision interpretation · " + EXERCISES[key]["title"]):
                    st.write(interpretation["message"])
                    st.caption("The selection is a discussion starting point, not a pass/fail grade.")


def _team_ui(token: str, uid: str, email: str, workshop: dict,
             participants: list[dict], responses: list[dict], owner: bool) -> None:
    wid = str(workshop["id"])
    st.markdown("### Leadership team")
    accepted = [p for p in participants if p["status"] == "accepted"]
    st.caption(f"{len(participants)} participants recorded · {len(accepted)} accepted · "
               f"{sum(bool(p.get('completed')) for p in accepted)} completed.")
    if owner:
        with st.expander("Invite an executive", expanded=False):
            st.caption("Invitation records are private. Share the workshop link yourself; "
                       "the service does not automatically send email.")
            with st.form("leadership_invite_" + wid):
                address = st.text_input("Participant's professional email", max_chars=254)
                send = st.form_submit_button("Add invitation")
            if send:
                address = address.strip().lower()
                if not EMAIL.fullmatch(address) or address == email.lower():
                    st.warning("Enter another participant's valid email.")
                elif len(participants) >= 12:
                    st.warning("This workshop is limited to 12 participants.")
                elif address in {str(p["invited_email"]).lower() for p in participants}:
                    st.warning("This email has already been invited.")
                else:
                    try:
                        rows = _api("POST", "portfolio_leadership_participants?select=id",
                                    token, {"workshop_id": wid, "owner_id": uid,
                                            "invited_email": address, "status": "invited"},
                                    returning=True)
                        if not isinstance(rows, list) or not rows:
                            raise RuntimeError("Invitation not confirmed")
                        st.success("Invitation recorded. Share the sign-in link directly.")
                        st.rerun()
                    except (RuntimeError, TimeoutError, ValueError, KeyError):
                        st.error("The invitation could not be recorded.")
            st.code("https://jairribeiro.com/?page=advisory-access&view=workshop")
            st.caption("Ask your invitee to open the Invitations tab after signing in.")
        for p in participants:
            with st.container(border=True):
                st.markdown("**" + escape(str(p["invited_email"])) + "**")
                st.caption(str(p["status"]).title() +
                    (" · Assessment completed" if p.get("completed") else " · Not complete") +
                    (" · Shared with organizer" if p.get("share_answers") else " · Responses private"))
                if str(p.get("user_id") or "") != uid:
                    with st.expander("Remove participant", expanded=False):
                        st.warning("Removing this participant revokes access and permanently "
                                   "deletes their answers from this workshop.")
                        confirm = st.checkbox("I understand the removal is permanent",
                                               key="leadership_remove_confirm_" + str(p["id"]))
                        if st.button("Remove this participant", disabled=not confirm,
                                     key="leadership_remove_" + str(p["id"])):
                            deleted = _api(
                                "DELETE", "portfolio_leadership_participants?id=eq." +
                                quote(str(p["id"]), safe="") + "&select=id",
                                token, returning=True)
                            if isinstance(deleted, list) and len(deleted) == 1:
                                st.success("Participant access and responses removed.")
                                st.rerun()
                            else:
                                st.error("Could not confirm participant removal.")
        # Organizer can access only responses whose owners explicitly consented.
        consented = [r["answers"] for r in responses
                     if any(p["id"] == r["participant_id"] and p.get("share_answers")
                            and p["status"] == "accepted" and r.get("completed")
                            for p in participants)]
        team = aggregate_team(consented)
        st.markdown("#### Shared leadership findings")
        if not team["available"]:
            st.info(team["reason"] + " Participant responses are not treated as anonymous.")
        else:
            st.caption(team["note"])
            for key, title, _, _ in DIMENSIONS:
                m = team["dimensions"][key]
                st.write(f"**{title}** — " +
                         (f"{m['average']} / 100; spread {m['spread']} points"
                          if m["average"] is not None else "Insufficient responses"))
    else:
        me = next((p for p in participants if p.get("user_id") == uid), None)
        if me:
            st.write("Only you can see your answers unless you explicitly opt in to sharing "
                     "them with the organizer. This workshop is not anonymous.")
            sharing = st.checkbox("Share my individual answers with the workshop organizer",
                                  value=bool(me.get("share_answers")),
                                  key="leadership_share_edit_" + wid)
            if st.button("Save sharing preference", key="leadership_share_save_" + wid):
                rows = _api("PATCH",
                            "portfolio_leadership_participants?id=eq." +
                            quote(str(me["id"]), safe="") + "&select=id",
                            token, {"share_answers": bool(sharing)}, returning=True)
                if isinstance(rows, list) and len(rows) == 1:
                    st.success("Your sharing preference was updated.")
                    st.rerun()
                else:
                    st.error("Could not update the sharing preference.")


def _decision_ui(token: str, workshop: dict, owner: bool,
                 current: dict | None) -> None:
    wid = str(workshop["id"])
    st.markdown("### Executive decisions and next actions")
    st.caption("Recommendations suggest accountability. A decision is not agreed until an "
               "accountable executive confirms its owner and evidence requirements.")
    if current:
        report = assess(current.get("answers") or {})
        for i, action in enumerate(report["actions"], 1):
            with st.container(border=True):
                st.caption(f"PROPOSED PRIORITY {i:02d}")
                st.markdown("**" + action["action"] + "**")
                st.write("Proposed owner: " + action["owner"])
                st.caption("Evidence: " + action["evidence"])
    decisions = workshop.get("decisions") or []
    if decisions:
        for n, d in enumerate(decisions, 1):
            if isinstance(d, dict):
                with st.container(border=True):
                    st.write(f"**Decision {n}:** " + str(d.get("decision") or ""))
                    st.caption("Owner: " + str(d.get("owner") or "Not assigned") +
                               " · Review: " + str(d.get("review") or "Not agreed"))
                    if d.get("note"):
                        st.write(str(d["note"]))
    if not owner:
        st.info("Only the workshop organizer can record collective leadership decisions.")
        return
    with st.form("leadership_decision_" + wid):
        choice = st.selectbox("Decision to record", DECISIONS)
        owner_role = st.selectbox("Accountable function", OWNER_ROLES)
        review = st.selectbox("Review horizon", REVIEW)
        note = st.text_area("Optional decision-specific condition",
                            max_chars=400, placeholder="Evidence needed before the next gate")
        save = st.form_submit_button("Record leadership decision", type="primary",
                                      use_container_width=True)
    if save:
        next_decisions = list(decisions)
        if len(next_decisions) >= 12:
            st.warning("Maximum 12 decisions per workshop. Start a new session for another review.")
            return
        next_decisions.append({"decision": choice, "owner": owner_role,
                               "review": review, "note": note.strip()})
        rows = _api("PATCH", "portfolio_leadership_workshops?id=eq." +
                    quote(wid, safe="") + "&select=id", token,
                    {"decisions": next_decisions, "status": "completed",
                     "updated_at": datetime.now(timezone.utc).isoformat()},
                    returning=True)
        if isinstance(rows, list) and len(rows) == 1:
            st.success("The decision was recorded.")
            st.rerun()
        else:
            st.error("Could not save the decision record.")


def _findings(token: str, uid: str, workshop: dict, me: dict | None,
              old: dict | None, participants: list[dict],
              responses: list[dict], owner: bool) -> None:
    wid = str(workshop["id"])
    st.markdown("### Executive leadership findings")
    if not old:
        st.info("Save your assessment answers to generate findings.")
        return
    raw = old.get("answers") or {}
    report = assess(raw)
    st.caption("Evidence confidence: " + report["confidence"])
    with st.container(border=True):
        st.caption("SELF-REPORTED LEADERSHIP POSITION")
        st.markdown("### " + report["label"].replace("_", " ").title())
        st.write(report["reason"])
        a,b,c=st.columns(3)
        a.metric("Questions answered", f"{report['answered']} / 21")
        b.metric("Coverage", f"{report['coverage']}%")
        c.metric("Weighted index", str(report["overall"]) if report["overall"] is not None else "Not issued")
        if report["critical_gates"]:
            st.warning("Critical conditions: " + "; ".join(report["critical_gates"]))
    st.markdown("#### Seven leadership dimensions")
    for key, title, weight, _ in DIMENSIONS:
        value = report["scores"][key]
        st.write(f"**{title}** · " + (str(value) + "/100" if value is not None else "Not assessed"))
        if value is not None:
            st.progress(int(value) / 100)
    st.markdown("#### Executive actions")
    for i, action in enumerate(report["actions"], 1):
        with st.container(border=True):
            st.markdown("**" + str(i) + ". " + action["action"] + "**")
            st.caption("Suggested owner: " + action["owner"] + " · Evidence: " + action["evidence"])
    if not old.get("completed"):
        st.info("The report is preliminary. Complete all 21 answers and both discussion "
                "exercises for a finished decision brief.")
    else:
        team = None
        if owner and workshop["mode"] == "team":
            visible = [r["answers"] for r in responses if r.get("completed") and
                       any(p["id"] == r["participant_id"] and p.get("share_answers")
                           for p in participants)]
            team = aggregate_team(visible)
        try:
            pdf = render_leadership_pdf(workshop, raw, old.get("exercises") or {}, team)
            st.download_button("Download executive decision brief (PDF)",
                               data=pdf, file_name="executive-ai-leadership-workshop.pdf",
                               mime="application/pdf", type="primary",
                               use_container_width=True,
                               key="leadership_pdf_" + wid)
        except (ValueError, RuntimeError, TypeError, UnicodeError):
            st.error("The PDF could not be generated. Your saved assessment remains available.")
    st.caption("This assessment is not an independent audit, organizational certification, "
               "regulatory opinion or permission to authorize spending or live AI use.")
    if st.button("Request selective pro-bono advisory", key="leadership_probono_" + wid):
        from page_advisory_member_experience import navigate
        navigate("requests")


def _workshop_settings(token: str, uid: str, workshop: dict,
                       member: dict, owner: bool) -> None:
    wid = str(workshop["id"])
    st.markdown("### Workshop settings")
    if owner:
        st.caption("As organizer, you can permanently erase this workshop, all "
                   "participant invitations, saved answers and decision records.")
        with st.expander("Delete workshop permanently", expanded=False):
            st.warning("This cannot be undone. All participant responses will be deleted.")
            verification = st.text_input("Type the workshop title to confirm",
                                         key="leadership_delete_confirm_" + wid)
            if st.button("Delete this workshop and all records",
                         disabled=verification != workshop["title"],
                         key="leadership_delete_" + wid):
                removed = _api("DELETE",
                               "portfolio_leadership_workshops?id=eq." +
                               quote(wid, safe="") + "&select=id",
                               token, returning=True)
                if isinstance(removed, list) and len(removed) == 1:
                    _go("history")
                else:
                    st.error("Deletion could not be verified; no success is claimed.")
    elif workshop.get("mode") == "team":
        st.caption("You may withdraw your participation and delete your own assessment. "
                   "This does not affect the other participants.")
        with st.expander("Leave workshop and delete my responses", expanded=False):
            agree = st.checkbox("I understand my answers will be permanently removed",
                                key="leadership_leave_agree_" + wid)
            if st.button("Leave and delete my answers", disabled=not agree,
                         key="leadership_leave_" + wid):
                removed = _api("DELETE",
                               "portfolio_leadership_participants?id=eq." +
                               quote(str(member["id"]), safe="") + "&select=id",
                               token, returning=True)
                if isinstance(removed, list) and len(removed) == 1:
                    _go("history")
                else:
                    st.error("The request could not be confirmed.")
    else:
        st.caption("This is your private individual workshop. The organizer may "
                   "delete it permanently using the owner controls.")


def _workspace(token: str, uid: str, email: str, items: list[dict]) -> None:
    wid = str(st.query_params.get("workshop_id") or "")
    item = next((w for w in items if str(w["id"]) == wid), None)
    if not item:
        st.info("Select a workshop from My workshops. You may need to accept an invitation first.")
        if st.button("View my workshops"):
            _go("history")
        return
    owner = str(item["owner_id"]) == uid
    people = _participants(token, wid)
    me = next((p for p in people if str(p.get("user_id") or "") == uid and p["status"] == "accepted"), None)
    if not me:
        st.warning("No accepted invitation is associated with this account.")
        return
    data = _responses(token, wid)
    old = next((r for r in data if str(r.get("user_id") or "") == uid), None)
    st.caption("PRIVATE EXECUTIVE LEADERSHIP WORKSHOP · " + str(item["mode"]).upper())
    st.markdown("### " + escape(str(item["title"])))
    context = item.get("context") or {}
    st.caption(" · ".join(str(context.get(k) or "") for k in ("stage", "scope", "priority")))
    details = ("assessment", "exercises", "findings", "decisions") + (
        ("team",) if item.get("mode") == "team" else ()) + ("settings",)
    labels = {"assessment": "Assessment", "exercises": "Discussion exercises",
              "findings": "Findings & report", "decisions": "Decision record",
              "team": "Team & invitations", "settings": "Settings"}
    requested = str(st.query_params.get("workshop_detail") or "assessment")
    if requested not in details:
        requested = "assessment"
    key = "leadership_detail_" + wid
    if st.session_state.get(key) != requested:
        st.session_state[key] = requested
    chosen = st.pills("Workshop workspace", details,
                      format_func=lambda s: labels[s], key=key,
                      selection_mode="single", required=True,
                      label_visibility="collapsed", wrap=False, width="stretch")
    if chosen != requested:
        st.query_params["workshop_detail"] = chosen
        requested = chosen
    if requested == "assessment":
        _answer_form(token, uid, wid, me, old)
    elif requested == "exercises":
        _exercise_form(token, uid, wid, me, old)
    elif requested == "findings":
        _findings(token, uid, item, me, old, people, data, owner)
    elif requested == "decisions":
        _decision_ui(token, item, owner, old)
    elif requested == "settings":
        _workshop_settings(token, uid, item, me, owner)
    else:
        _team_ui(token, uid, email, item, people, data, owner)


def render_private_leadership_workshop(session: dict, user: dict) -> None:
    """Entry point from the existing verified Advisory member shell."""
    token = str(session.get("access_token") or "")
    uid = str(user.get("id") or "")
    email = str(user.get("email") or "").strip().lower()
    if not token or not uid or not email or not user.get("email_confirmed_at"):
        st.error("A verified Advisory account is required.")
        return
    from page_rollout_workspace_ui import WORKSPACE_CSS
    st.html(WORKSPACE_CSS + WORKSHOP_CSS)
    with st.container(key="leadership_workspace"):
        st.markdown("### Executive AI Leadership Workshop")
        st.caption("Private self-service advisory · Free registration · No independent assessment claims")
        section = _navigation()
        try:
            items = _workshops(token)
        except (ValueError, RuntimeError, TimeoutError, KeyError):
            st.error("Your workshop records are temporarily unavailable.")
            return
        try:
            if section == "overview":
                _overview(items)
            elif section == "new":
                _new(token, uid, email)
            elif section == "history":
                _history(items)
            elif section == "invitations":
                _invitations(token, uid, email)
            else:
                _workspace(token, uid, email, items)
        except (ValueError, RuntimeError, TimeoutError, KeyError):
            st.error("This workshop could not be loaded or updated. Your prior saved data remains available.")
