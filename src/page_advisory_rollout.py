"""Executive AI Rollout Readiness Advisor: one-session, evidence-led assessment.

A separately approved Advisory entitlement gives access to a short assessment,
a deterministic decision brief, and an optional downloadable PDF. The result is
guidance based on self-reported inputs, not a compliance sign-off.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape
from io import BytesIO
from urllib.parse import quote

import streamlit as st

from page_public_services import SERVICES_CSS
from page_advisory_scorecard import SCORECARD_CSS
from site_components import nav, footer
from site_cms import _request_json, _rest_url
from page_advisory_client_journey import (
    _client_requests, _request_messages, _create_request, _reply, CLOSED,
)
from page_advisory_service_feedback import ROLLOUT_SERVICE, render_optional_feedback
from advisory_service_visibility import service_enabled, advisory_role

SERVICE_TITLE = "Enterprise AI Rollout Readiness Advisor"
REQUEST_TITLE = "Enterprise AI Rollout Readiness Advisor — access request"
REQUEST_MARKER = "ENTERPRISE AI ROLLOUT ADVISOR ACCESS REQUEST"
SERVICE_KEY = ROLLOUT_SERVICE

# key, assessment area, question, recommended response, critical scale gate
QUESTIONS = (
    ("baseline","Business value","Have you documented the current performance baseline?",
     "Measure the current process before projecting value.",False),
    ("outcome","Business value","Has the pilot demonstrated an attributable business outcome?",
     "Validate business outcomes with users and compare them with the baseline.",False),
    ("sponsor","Business value","Is there an accountable executive sponsor and business owner?",
     "Assign an accountable sponsor with authority to resolve business constraints.",False),
    ("economics","Business value","Have full lifecycle costs and the economic case been tested?",
     "Confirm total cost, benefits and the assumptions behind the investment case.",False),
    ("reliability","Operational readiness","Has reliability been validated under realistic operating conditions?",
     "Test reliability, exceptions and escalation before broad exposure.",True),
    ("data","Operational readiness","Are critical data inputs reliable and explicitly owned?",
     "Resolve data ownership, quality and access limitations.",False),
    ("workflow","Operational readiness","Have affected workflows, responsibilities and procedures been redesigned?",
     "Test the redesigned workflow end to end with business users.",False),
    ("fallback","Operational readiness","Are service support, failures and fallback procedures defined?",
     "Assign production support and prove manual fallback and recovery procedures.",False),
    ("security","Governance and risk","Are security, privacy and vendor controls reviewed for the intended scale?",
     "Complete the proportionate security, privacy and third-party review.",True),
    ("oversight","Governance and risk","Are human oversight and escalation responsibilities explicit?",
     "Define who can override AI outputs, investigate failures and halt use.",True),
    ("regulation","Governance and risk","Have relevant legal, sector and AI regulatory duties been assessed?",
     "Verify regulatory applicability and document outstanding obligations.",True),
    ("owner","People and adoption","Is a business leader accountable for adoption after launch?",
     "Make one business owner accountable for changed work and realized benefit.",True),
    ("employees","People and adoption","Have representative employees tested the solution in their actual work?",
     "Run real-work trials with affected roles, not only technical demonstrations.",False),
    ("learning","People and adoption","Are role-specific training and support ready?",
     "Prepare practical role-specific guidance and a local support route.",False),
    ("usage","People and adoption","Are meaningful adoption and workflow-change measures defined?",
     "Measure sustained, appropriate usage and its impact on work.",False),
    ("capacity","Scaling capability","Is the architecture and operating capacity sized for phased expansion?",
     "Validate capacity, cost and performance at the next deployment size.",False),
    ("accountability","Scaling capability","Are rollout stages, owners and decision rights agreed?",
     "Set decision owners and explicit conditions at each release gate.",False),
    ("exit","Scaling capability","Are stop, rollback and reinvestment criteria defined?",
     "Agree evidence thresholds for proceeding, pausing or withdrawing.",False),
)
AREAS = ("Business value","Operational readiness","Governance and risk",
         "People and adoption","Scaling capability")
OPTIONS = (
    "Not assessed / no evidence",
    "Planned, not yet demonstrated",
    "Partly tested or evidenced",
    "Demonstrated with credible evidence",
)
STAGES = ("Pilot completed","Pilot in progress","Limited production","Preparing wider rollout")
CRITICALITIES = ("Low","Moderate","High")
SCOPES = ("One team or function","Several functions","Enterprise-wide")

def validate_answers(raw: dict) -> dict:
    """Normalize only the expected 18 questions and non-confidential context."""
    if not isinstance(raw, dict):
        raise ValueError("Invalid assessment")
    responses = raw.get("responses")
    if not isinstance(responses, dict) or set(responses) != {q[0] for q in QUESTIONS}:
        raise ValueError("Answer all 18 assessment questions.")
    if any(type(v) is not int or v not in (0,1,2,3) for v in responses.values()):
        raise ValueError("Unsupported readiness rating")
    context = raw.get("context")
    if not isinstance(context, dict):
        raise ValueError("Missing assessment context")
    use_case = str(context.get("use_case") or "").strip()
    if not 5 <= len(use_case) <= 120:
        raise ValueError("Give a short, non-confidential description of the AI use case.")
    if (context.get("stage") not in STAGES or
        context.get("criticality") not in CRITICALITIES or
        context.get("scope") not in SCOPES):
        raise ValueError("Invalid assessment context")
    return {"responses": responses, "context": {
        "use_case": use_case, "stage": context["stage"],
        "criticality": context["criticality"], "scope": context["scope"],
    }}

def assess(raw: dict) -> dict:
    """Explicit rules; critical gates override averages and self-report confidence."""
    answers = validate_answers(raw)
    response = answers["responses"]
    dimensions = {}
    for area in AREAS:
        vals = [response[q[0]] for q in QUESTIONS if q[1] == area]
        dimensions[area] = round(100 * sum(vals) / (3 * len(vals)))
    overall = round(sum(dimensions.values()) / len(dimensions))
    missing = [q for q in QUESTIONS if response[q[0]] == 0]
    high_impact = answers["context"]["criticality"] == "High"
    # High-consequence uses require demonstrated safeguards, not partial testing.
    gates = [q for q in QUESTIONS if q[4] and response[q[0]] <
             (3 if high_impact and q[0] in ("reliability","security","oversight","regulation") else 2)]
    weak = sorted(QUESTIONS, key=lambda q: (response[q[0]], not q[4]))
    actions = []
    for q in list(gates) + weak:
        if response[q[0]] < 3 and q[3] not in actions:
            actions.append(q[3])
        if len(actions) == 3:
            break
    # A pilot still underway is not sufficient evidence for enterprise deployment.
    pilot_unfinished = answers["context"]["stage"] == "Pilot in progress"
    if gates:
        label = "PAUSE SCALING"
        verdict = "Do not authorize wider deployment until critical conditions are resolved."
        reason = ("At least one critical security, oversight, reliability, regulatory or "
                  "adoption-ownership condition is not sufficiently demonstrated.")
    elif len(missing) >= 5:
        label = "EVIDENCE INCOMPLETE"
        verdict = "Defer the scaling decision until essential evidence has been collected."
        reason = "Too many readiness conditions remain unassessed to support a credible decision."
    elif pilot_unfinished and answers["context"]["scope"] == "Enterprise-wide":
        label = "CONTROLLED EXPANSION"
        verdict = "Complete the pilot validation before authorizing enterprise-wide deployment."
        reason = "An unfinished pilot cannot establish the evidence needed for broad operational exposure."
    elif min(dimensions.values()) <= 50:
        label = "CONTROLLED EXPANSION"
        verdict = "Limit expansion to a controlled operational test with explicit exit criteria."
        reason = "A material business, operating, governance, adoption or scaling weakness remains."
    elif min(dimensions.values()) >= 75 and overall >= 78 and len(missing) == 0:
        label = "PHASED GO"
        verdict = "Consider a phased rollout, subject to independent risk and business approval."
        reason = "Self-reported evidence indicates readiness across the five assessed dimensions."
    else:
        label = "CONDITIONAL GO"
        verdict = "Proceed only with a limited next stage and named validation conditions."
        reason = "The foundation is credible, but some conditions still need stronger evidence."
    for fallback in (
        "Confirm executive authorization, accountable business ownership and release conditions.",
        "Expand in controlled waves, with explicit stop and fallback criteria.",
        "Review actual adoption, business outcomes and operational incidents against the baseline.",
    ):
        if len(actions) >= 3:
            break
        if fallback not in actions:
            actions.append(fallback)
    weakest = min(dimensions, key=dimensions.get)
    if weakest == "People and adoption":
        insight = "The limiting factor is adoption: changing work and ownership requires more proof than launching the technology."
    elif weakest == "Business value":
        insight = "The value case is the constraint. More users or broader deployment will not establish business benefit on their own."
    elif weakest == "Operational readiness":
        insight = "The solution may work in a pilot, but repeatable operations and exception handling need more proof."
    elif weakest == "Governance and risk":
        insight = "Unresolved accountability and control conditions can make scale unjustifiable regardless of technical promise."
    else:
        insight = "The economics and organizational capability to expand require more evidence than the pilot alone provides."
    confidence = "Limited" if len(missing)>=5 else ("Moderate" if len(missing) or sum(v<3 for v in response.values())>=8 else "Higher")
    return {
        "label":label,"verdict":verdict,"reason":reason,"insight":insight,
        "overall":overall,"dimensions":dimensions,"priorities":actions,
        "confidence":confidence,"unassessed":len(missing),
        "critical_gates":[q[2] for q in gates],
    }

def _entitlements(token: str, uid: str) -> list[dict]:
    rows = _request_json(
        "GET", _rest_url("portfolio_advisory_rollout_access?select=id,request_id,"
                         "status,approved_at&user_id=eq." + quote(uid,safe="") +
                         "&order=approved_at.desc&limit=20"),
        token=token, timeout=12)
    if not isinstance(rows,list):
        raise RuntimeError("Rollout entitlements could not be verified")
    return rows

def _assessments(token: str, uid: str, request_id: str | None = None) -> list[dict]:
    """Member RLS enforces record ownership. Read all approved historic sessions."""
    endpoint = ("portfolio_advisory_rollout_assessments?"
                "select=id,request_id,answers,created_at,model_version"
                "&user_id=eq." + quote(uid,safe=""))
    if request_id:
        endpoint += "&request_id=eq." + quote(request_id,safe="")
    endpoint += "&order=created_at.desc&limit=100"
    rows=_request_json("GET",_rest_url(endpoint),token=token,timeout=12)
    if not isinstance(rows,list):
        raise RuntimeError("Assessment history unavailable")
    return rows

def _submit_assessment(token: str, request_id: str, raw: dict) -> str:
    data = validate_answers(raw)
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_rollout_assess_v1"),
        token=token, payload={"p_request_id":request_id,"p_answers":data},timeout=18)
    if not isinstance(result,dict) or not result.get("id"):
        raise RuntimeError("Assessment was not confirmed by the server")
    return str(result["id"])

def _find_request(token: str, uid: str) -> tuple[dict | None,bool]:
    active = next((r for r in _client_requests(token,uid)
                   if str(r.get("status")) not in CLOSED),None)
    if not active:
        return None,False
    already = str(active.get("title") or "").casefold() == REQUEST_TITLE.casefold()
    if not already:
        already = any(
            m.get("sender")=="client" and REQUEST_MARKER in str(m.get("body") or "")
            for m in _request_messages(token,uid,str(active["id"]))
        )
    return active,already

def request_access(token: str, uid: str, challenge: str, outcome: str) -> str:
    if not service_enabled("rollout") and advisory_role(token) != "admin":
        raise ValueError("The Rollout Advisor is temporarily unavailable for new access requests.")
    challenge = str(challenge or "").strip()
    outcome = str(outcome or "").strip()
    if not (25<=len(challenge)<=1200 and 20<=len(outcome)<=800):
        raise ValueError("Describe the rollout decision and desired outcome in sufficient detail.")
    active,already = _find_request(token,uid)
    if already:
        return "already_requested"
    if active:
        _reply(token,uid,str(active["id"]),REQUEST_MARKER+
               "\n\nRollout context: "+challenge+
               "\nDecision needed: "+outcome+
               "\nPlease review individual access to the on-demand rollout advisor.")
        return "added_to_engagement"
    _create_request(token,uid,{
        "title":REQUEST_TITLE,
        "service_key":"rollout",
        "desired_outcome":outcome,
        "business_context":"Enterprise AI rollout decision: "+challenge,
        "decision_timing":"1–3 months",
        "contact_preference":"Email",
    })
    return "new_request"

def _access_request_ui(token: str, uid: str) -> None:
    st.markdown("### Request individual access")
    st.write("This complimentary decision service is reserved for selected Advisory clients. "
             "Registration does not grant automatic access.")
    try:
        _,requested = _find_request(token,uid)
    except (ValueError,RuntimeError,TimeoutError,KeyError):
        st.error("The Advisory request state is temporarily unavailable.")
        return
    if requested:
        st.info("Your access request is under individual review.")
        if st.button("Follow this request in conversations",
                     key="rollout_pending_conversation"):
            from page_advisory_member_experience import navigate
            navigate("messages")
        return
    with st.form("rollout_access_request"):
        challenge = st.text_area("What rollout decision are you facing?",max_chars=1200,
                                 placeholder="Describe the rollout stage and business decision without confidential details.")
        outcome = st.text_area("What decision would a useful assessment help you make?",max_chars=800)
        submitted = st.form_submit_button("Request access",type="primary")
    if submitted:
        try:
            state = request_access(token,uid,challenge,outcome)
            st.success("Your request has been added to your Advisory conversation."
                       if state=="added_to_engagement" else
                       "Your access request has been submitted for individual review.")
            st.rerun()
        except ValueError as ex:
            st.warning(str(ex))
        except (RuntimeError,TimeoutError,KeyError):
            st.error("Unable to confirm the access request.")

def _input_form(token: str, request_id: str, uid: str = "") -> None:
    st.markdown("### Begin a readiness assessment")
    st.caption("A focused, one-session assessment across five decision dimensions. "
               "Select 'Demonstrated' only when credible supporting evidence exists.")
    st.info("**What you will receive:** an executive verdict, three ranked actions, "
            "named release conditions, and a downloadable decision brief. "
            "This is not a compliance approval.")
    with st.form("rollout_decision_assessment",clear_on_submit=False):
        a,b = st.columns([2,1])
        with a:
            use_case=st.text_input("AI use case or initiative (high level)",max_chars=120,
                                   placeholder="e.g. Customer service knowledge assistant")
        with b:
            stage=st.selectbox("Current stage",STAGES)
        a,b=st.columns(2)
        with a:
            criticality=st.selectbox("Operational consequence if AI is wrong",CRITICALITIES,index=1)
        with b:
            scope=st.selectbox("Intended next rollout scope",SCOPES)
        # One decision dimension on screen at a time. The form remains a
        # single verified submission, but never presents 18 open controls.
        st.caption("Complete the five assessment tabs before generating your brief.")
        dimension_tabs = st.tabs([
            "Business value", "Operations", "Governance", "People & adoption", "Scale"
        ])
        responses={}
        for area, tab in zip(AREAS, dimension_tabs):
            with tab:
                st.caption(str(sum(q[1] == area for q in QUESTIONS)) +
                           " evidence-based questions · " + area)
                for key,question_area,question,action,is_gate in QUESTIONS:
                    if question_area != area:
                        continue
                    responses[key]=st.selectbox(question,range(4),index=0,
                        format_func=lambda v:OPTIONS[v],key="rollout_q_"+key)
        consent=st.checkbox("I understand this is an indicative advisory assessment, "
                            "not an independent audit or authorization to deploy.")
        submitted=st.form_submit_button("Generate executive decision brief",type="primary")
    if submitted:
        if not consent:
            st.warning("Acknowledge the scope of this advisory assessment.")
            return
        try:
            raw={"responses":responses,"context":{
                "use_case":use_case,"stage":stage,"criticality":criticality,"scope":scope}}
            new_id=_submit_assessment(token,request_id,raw)
            if uid:
                from site_onboarding_measurement import record_first_value
                record_first_value(token, uid, "advisory", "first_assessment")
            st.session_state["rollout_latest_report_id"]=new_id
            st.query_params["rollout_record"]=new_id
            st.query_params["rollout_section"]="decision"
            st.query_params["rollout_detail"]="verdict"
            st.rerun()
        except ValueError as ex:
            st.warning(str(ex))
        except (RuntimeError,TimeoutError,KeyError):
            st.error("Your assessment could not be saved. Check your access and try again.")

def _pdf_report(result: dict, data: dict) -> bytes:
    """Live premium v2 PDF: management verdict, readiness, action owners, release conditions."""
    from page_rollout_premium_pdf import render_premium_rollout_pdf
    return render_premium_rollout_pdf(result, data)

ROLLOUT_SECTIONS = ("overview", "assess", "decision", "history")
ROLLOUT_LABELS = {
    "overview": "About this service",
    "assess": "New assessment",
    "decision": "Decision brief",
    "history": "My history",
}
REPORT_SECTIONS = ("verdict", "actions", "evidence")
REPORT_LABELS = {
    "verdict": "Verdict & readiness",
    "actions": "Executive actions",
    "evidence": "Evidence & report",
}


def _navigate_rollout(section: str, detail: str | None = None,
                      record_id: str | None = None) -> None:
    """Private nested route. Preserve auth and selected member section."""
    if section not in ROLLOUT_SECTIONS:
        return
    st.query_params["rollout_section"] = section
    if detail in REPORT_SECTIONS:
        st.query_params["rollout_detail"] = detail
    if record_id:
        st.query_params["rollout_record"] = record_id
    st.rerun()


def _rollout_nav_changed() -> None:
    selected = st.session_state.get("rollout_workspace_nav")
    if selected in ROLLOUT_SECTIONS:
        st.query_params["rollout_section"] = selected


def _report_nav_changed() -> None:
    selected = st.session_state.get("rollout_report_nav")
    if selected in REPORT_SECTIONS:
        st.query_params["rollout_detail"] = selected


def _navigation() -> str:
    requested = str(st.query_params.get("rollout_section") or "overview")
    if requested not in ROLLOUT_SECTIONS:
        requested = "overview"
    if st.session_state.get("rollout_workspace_nav") != requested:
        st.session_state["rollout_workspace_nav"] = requested
    st.pills(
        "Rollout service sections", ROLLOUT_SECTIONS,
        format_func=lambda v: ROLLOUT_LABELS[v],
        key="rollout_workspace_nav", selection_mode="single",
        required=True, on_change=_rollout_nav_changed,
        label_visibility="collapsed", wrap=False, width="stretch",
    )
    return requested


def _report_navigation() -> str:
    requested = str(st.query_params.get("rollout_detail") or "verdict")
    if requested not in REPORT_SECTIONS:
        requested = "verdict"
    if st.session_state.get("rollout_report_nav") != requested:
        st.session_state["rollout_report_nav"] = requested
    st.pills(
        "Decision brief sections", REPORT_SECTIONS,
        format_func=lambda v: REPORT_LABELS[v], key="rollout_report_nav",
        selection_mode="single", required=True,
        on_change=_report_nav_changed, label_visibility="collapsed",
        wrap=False, width="stretch",
    )
    return requested


def _feedback_for_result(session: dict, user: dict,
                         request_id: str, stage: str, is_demo: bool) -> None:
    # Owner QA scenario responses never distort customer satisfaction statistics.
    if is_demo:
        st.caption("Synthetic owner test · Customer satisfaction surveys are disabled for this example.")
        return
    render_optional_feedback(
        str(session["access_token"]), str(user["id"]), SERVICE_KEY,
        stage, request_id=request_id,
    )


def _report_download(session: dict, user: dict, request_id: str,
                     rid: str, result: dict, data: dict, is_demo: bool,
                     slot: str) -> None:
    try:
        pdf=_pdf_report(result,data)
    except (RuntimeError,ValueError,UnicodeError,TypeError):
        st.error("The PDF could not be generated. Your private decision is still available.")
        return
    clicked=st.download_button(
        "Download executive decision brief (PDF · premium v2)",
        data=pdf, file_name="enterprise-ai-rollout-executive-decision-brief-v2.pdf",
        mime="application/pdf", key="rollout_pdf_"+slot+"_"+rid,
        use_container_width=True, type="primary",
    )
    if clicked:
        st.session_state["rollout_downloaded_"+rid]=True
    if st.session_state.get("rollout_downloaded_"+rid):
        _feedback_for_result(session,user,request_id,"report_download",is_demo)


def _evidence_screen(record:dict,result:dict)->None:
    data=record["answers"]
    evidence=data.get("evidence") if isinstance(data.get("evidence"),dict) else {}
    demo=data.get("demo") if isinstance(data.get("demo"),dict) else {}
    st.markdown("### Readiness evidence and decision basis")
    st.caption("Inspect all 18 ratings and supporting evidence. Notes, where supplied, "
               "are self-reported; this service does not independently verify them.")
    area=st.selectbox(
        "Filter decision dimension", ("All dimensions",)+AREAS,
        key="rollout_evidence_dimension",
    )
    evidence_rows=[]
    for key,dimension,question,_,critical in QUESTIONS:
        if area!="All dimensions" and area!=dimension:
            continue
        item=evidence.get(key) if isinstance(evidence.get(key),dict) else {}
        score=data["responses"].get(key,0)
        evidence_rows.append({
            "Dimension":dimension,
            "Readiness question":question,
            "Rating":OPTIONS[score] if type(score) is int and 0<=score<len(OPTIONS) else "Not available",
            "Critical scale condition":"Yes" if critical else "No",
            "Evidence reference":str(item.get("ref") or "Not provided"),
            "Evidence basis":str(item.get("detail") or "No evidence note submitted"),
        })
    st.dataframe(evidence_rows,use_container_width=True,hide_index=True,height=360)
    if demo.get("is_demo"):
        st.warning("Owner QA scenario: all supporting evidence references and pilot figures "
                   "are synthetic and are not documents from a real organization.")
    if result["critical_gates"]:
        st.markdown("#### Release conditions still requiring evidence")
        from page_rollout_premium_pdf import _gate_keys, CATALOG
        for key in _gate_keys(data):
            action=CATALOG.get(key)
            if action:
                st.markdown("**"+action[0]+"** — "+action[5])
    st.caption("Evidence reviews and regulatory, legal, operational or deployment "
               "authorizations must be completed by the responsible organization.")


def _report_ui(session: dict, user: dict, request_id: str, record: dict) -> None:
    """Render exactly one decision subview; never a continuous report/dashboard."""
    from page_rollout_workspace_ui import render_case_heading, render_verdict
    from page_rollout_action_ui import render_action_plan
    data=record.get("answers")
    try:
        result=assess(data)
    except (ValueError,TypeError,KeyError):
        st.error("This saved assessment cannot be interpreted using the current rules.")
        return
    rid=str(record["id"])
    demo=isinstance(data.get("demo"),dict) and data["demo"].get("is_demo") is True
    render_case_heading(record)
    st.caption("Decision rules · rollout-v1  |  Executive report · premium-v2")
    detail=_report_navigation()
    if detail=="verdict":
        render_verdict(result,data)
        a,b=st.columns(2)
        with a:
            if st.button("Review my three executive actions",type="primary",
                         key="rollout_to_actions_"+rid,use_container_width=True):
                _navigate_rollout("decision","actions",rid)
        with b:
            if st.button("Review evidence and download report",
                         key="rollout_to_evidence_"+rid,use_container_width=True):
                _navigate_rollout("decision","evidence",rid)
        _feedback_for_result(session,user,request_id,"assessment_completion",demo)
    elif detail=="actions":
        render_action_plan(data, result)
        if st.button("Read the verdict and readiness rationale",
                     key="rollout_to_verdict_"+rid):
            _navigate_rollout("decision","verdict",rid)
        _feedback_for_result(session,user,request_id,"executive_recommendation",demo)
    else:
        _evidence_screen(record,result)
        st.markdown("### Your executive decision brief")
        st.write("Download the signed-off-format report for a leadership discussion. "
                 "The document gives a recommendation based on your submitted evidence; "
                 "it does not confer deployment approval.")
        _report_download(session,user,request_id,rid,result,data,demo,"evidence")


def _history_ui(history:list[dict]) -> None:
    st.markdown("### Your rollout decisions")
    st.caption("A read-only archive of completed assessments. Every new analysis "
               "creates a separate record; earlier decisions are not overwritten.")
    if not history:
        st.info("No completed rollout assessments yet.")
        if st.button("Start your first readiness assessment",type="primary",
                     key="rollout_history_start"):
            _navigate_rollout("assess")
        return
    search=st.text_input("Find an assessment",placeholder="Use case or rollout context",
                         key="rollout_history_search")
    filter_status=st.selectbox(
        "Decision",("All decisions","PAUSE SCALING","EVIDENCE INCOMPLETE",
                    "CONTROLLED EXPANSION","CONDITIONAL GO","PHASED GO"),
        key="rollout_history_filter",
    )
    rows=[]
    for record in history:
        try:
            result=assess(record["answers"])
            ctx=record["answers"]["context"]
        except (KeyError,ValueError,TypeError):
            continue
        if search.strip().casefold() not in str(ctx.get("use_case") or "").casefold():
            continue
        if filter_status!="All decisions" and result["label"]!=filter_status:
            continue
        demo=record["answers"].get("demo")
        rows.append((record,ctx,result,bool(isinstance(demo,dict) and demo.get("is_demo"))))
    st.caption(f"{len(rows)} of {len(history)} saved assessments match.")
    if not rows:
        st.info("No assessments match the current filters.")
        return
    st.dataframe([
        {
            "Date":str(r.get("created_at") or "")[:10],
            "Initiative":str(ctx.get("use_case") or "Unnamed"),
            "Executive verdict":result["label"].replace("_"," ").title(),
            "Readiness":str(result["overall"])+"/100",
            "Release gates":len(result["critical_gates"]),
            "Type":"Owner test" if demo else "Client assessment",
        } for r,ctx,result,demo in rows
    ],hide_index=True,use_container_width=True,height=min(360,85+len(rows)*35))
    refs={str(r["id"]):(r,ctx,result,demo) for r,ctx,result,demo in rows}
    ids=list(refs)
    selected=st.selectbox(
        "Select a decision to review",ids,
        format_func=lambda rid:
            str(refs[rid][0].get("created_at") or "")[:10]+" · "+
            str(refs[rid][1].get("use_case") or "AI rollout")+
            " · "+refs[rid][2]["label"].replace("_"," ").title(),
        key="rollout_history_selected",
    )
    record,ctx,result,demo=refs[selected]
    with st.container(border=True):
        st.caption("SELECTED DECISION"+(" · SYNTHETIC TEST" if demo else ""))
        st.markdown("#### "+str(ctx.get("use_case") or "AI rollout"))
        a,b,c=st.columns(3)
        a.metric("Readiness",str(result["overall"])+"/100")
        b.metric("Critical gates",len(result["critical_gates"]))
        c.metric("Evidence confidence",result["confidence"])
        st.write("**"+result["label"].replace("_"," ").title()+"** — "+result["verdict"])
        if st.button("Open selected decision",type="primary",
                     key="rollout_history_open",use_container_width=True):
            _navigate_rollout("decision","verdict",selected)
    if st.button("Start another assessment",key="rollout_history_new"):
        _navigate_rollout("assess")


def render_private_rollout(session:dict,user:dict)->None:
    """Premium focused subpages within the authorized Advisory member space."""
    from page_rollout_workspace_ui import WORKSPACE_CSS,render_service_overview
    token=str(session.get("access_token") or "")
    uid=str(user.get("id") or "")
    if not token or not uid or not user.get("email_confirmed_at"):
        return
    st.html(WORKSPACE_CSS)
    st.markdown("### Enterprise AI Rollout Readiness Advisor")
    st.caption("Private executive decision service · A focused assessment, not a tracking tool")
    section=_navigation()
    try:
        access=_entitlements(token,uid)
    except (ValueError,RuntimeError,TimeoutError,KeyError):
        st.error("The service authorization could not be verified. Try again.")
        return
    # Read the entire private assessment archive for this member, including
    # earlier approvals. Supabase RLS still controls every returned record.
    if access:
        try:
            history=_assessments(token,uid)
        except (RuntimeError,ValueError,TimeoutError,KeyError):
            st.error("Saved assessment history is temporarily unavailable.")
            return
    else:
        history=[]
    if section=="overview":
        render_service_overview(bool(access),history)
        if st.button("View public service methodology",
                     key="rollout_open_methodology"):
            st.query_params.from_dict({"page": "advisory-rollout"})
            st.rerun()
        if history:
            latest=history[0]
            try:
                result=assess(latest["answers"])
            except (ValueError,TypeError,KeyError):
                result=None
            if result:
                st.markdown("### Your latest decision")
                with st.container(border=True):
                    st.caption(str(latest.get("created_at") or "")[:10] +
                               " · "+str(latest["answers"]["context"].get("use_case") or "AI initiative"))
                    st.markdown("#### "+result["label"].replace("_"," ").title())
                    st.write(result["verdict"])
                    col1,col2=st.columns(2)
                    with col1:
                        if st.button("Open executive decision brief",
                                     type="primary",key="rollout_home_latest",
                                     use_container_width=True):
                            _navigate_rollout("decision","verdict",str(latest["id"]))
                    with col2:
                        if st.button("Browse decision history",
                                     key="rollout_home_history",use_container_width=True):
                            _navigate_rollout("history")
        if access:
            if st.button("Start a new readiness assessment",key="rollout_home_new"):
                _navigate_rollout("assess")
        else:
            from advisory_service_visibility import advisory_role
            if advisory_role(token) == "admin":
                st.info("Admin access · You can activate your own Rollout assessment workspace.")
                if st.button("Activate my admin Rollout workspace",
                             key="admin_rollout_activate_overview", type="primary"):
                    try:
                        result = _request_json(
                            "POST", _rest_url("rpc/portfolio_advisory_admin_ensure_workspace_v1"),
                            token=token, payload={"p_service_key": "rollout"}, timeout=15,
                        )
                        if not isinstance(result, dict) or result.get("service_key") != "rollout":
                            raise RuntimeError("Admin access not confirmed")
                        st.rerun()
                    except (RuntimeError, ValueError, TimeoutError, KeyError):
                        st.error("Admin workspace could not be activated.")
            else:
                _access_request_ui(token,uid)
        return
    if not access:
        from advisory_service_visibility import advisory_role
        if advisory_role(token) == "admin":
            st.info(
                "Admin access · Activate a private Rollout Advisor workspace. "
                "This does not change what regular users can see."
            )
            if st.button("Activate my admin Rollout workspace",
                         type="primary", key="admin_rollout_activate"):
                try:
                    result = _request_json(
                        "POST",
                        _rest_url("rpc/portfolio_advisory_admin_ensure_workspace_v1"),
                        token=token, payload={"p_service_key": "rollout"}, timeout=15,
                    )
                    if not isinstance(result, dict) or result.get("service_key") != "rollout":
                        raise RuntimeError("Admin Rollout access was not confirmed")
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError, KeyError):
                    st.error("Admin workspace could not be activated. Please review your service access.")
            return
        st.warning("Access to this decision service requires individual approval. "
                   "Your Advisory account alone does not grant permission.")
        if st.button("Return to service and access request",
                     key="rollout_noaccess_overview"):
            _navigate_rollout("overview")
        return
    if section=="assess":
        st.markdown("### New executive readiness assessment")
        st.caption("A new assessment creates a new decision record. Past reports remain preserved.")
        _input_form(token,str(access[0]["request_id"]),uid)
        return
    if section=="history":
        _history_ui(history)
        return
    if not history:
        st.info("No decision brief exists yet. Complete a readiness assessment first.")
        if st.button("Start assessment",type="primary",key="rollout_empty_decision"):
            _navigate_rollout("assess")
        return
    selected_id=str(st.query_params.get("rollout_record") or "")
    if selected_id not in {str(r["id"]) for r in history}:
        selected_id=str(history[0]["id"])
    selected=next(r for r in history if str(r["id"])==selected_id)
    _report_ui(session,user,str(selected.get("request_id") or access[0]["request_id"]),selected)

def advisory_rollout() -> str:
    """Public explanatory page; it never includes client records."""
    return f'''{SERVICES_CSS}{SCORECARD_CSS}{nav("advisory")}
<main class="scorecard-page">
<section class="sc-hero"><div class="container">
 <div class="sc-kicker">Executive AI Advisory / Selective complimentary access</div>
 <h1>Enterprise AI Rollout Readiness Advisor.</h1>
 <p class="sc-lead">Your pilot works. Is your organization actually ready to scale it?</p>
 <p>Complete a focused readiness assessment and receive a clear executive position: proceed in phases, expand conditionally, test further or pause. The recommendation identifies critical constraints and your three highest-priority next actions.</p>
 <div class="sc-actions"><a class="sc-btn" href="?page=advisory-access&amp;view=rollout" target="_self">Request individual access →</a>
 <a class="sc-btn alt" href="#rollout-method">See the assessment method</a></div>
 <p style="font-size:13px;margin-top:19px">No payment required. Access is individually approved for selected Advisory clients; registration alone does not grant this service.</p>
</div></section>
<section class="sc-wrap" id="rollout-method">
 <span class="sc-kicker">The management decision</span>
 <h2>From technical proof to organizational readiness.</h2>
 <p>This is not a tracking dashboard or an ongoing project-management system. It is one practical assessment that challenges whether the business can turn an AI pilot into sustained operational value.</p>
 <div class="sc-grid">
  <article class="sc-card"><span class="sc-num">01 / Value</span><h3>Business case</h3><p>Real outcomes, baselines, ownership and the economics beyond the pilot.</p></article>
  <article class="sc-card"><span class="sc-num">02 / Operations</span><h3>Operating readiness</h3><p>Reliability, data, redesigned workflows, support and recovery.</p></article>
  <article class="sc-card"><span class="sc-num">03 / Trust</span><h3>Governance and risk</h3><p>Security, privacy, human oversight and applicable obligations.</p></article>
  <article class="sc-card"><span class="sc-num">04 / People</span><h3>Adoption and ownership</h3><p>Changed work, role readiness, frontline validation and accountable leadership.</p></article>
  <article class="sc-card"><span class="sc-num">05 / Scale</span><h3>Scaling capability</h3><p>Capacity, rollout gates, investment conditions and exit criteria.</p></article>
 </div>
 <div class="sc-boundary"><p><strong>The decision is not an average score.</strong> Critical deficiencies in oversight, reliability, adoption ownership or controls can override an otherwise strong readiness profile. Unknown answers reduce confidence; the service does not invent evidence.</p></div>
</section>
<section class="sc-wrap sc-dark" style="max-width:none">
 <div style="max-width:1100px;margin:auto">
  <span class="sc-kicker">The outcome</span><h2>An executive decision brief, not another checklist.</h2>
  <div class="sc-grid-2">
   <article class="sc-card"><span class="sc-num">Verdict</span><h3>What should happen now?</h3><p>Proceed, proceed conditionally, run a controlled expansion, or pause.</p></article>
   <article class="sc-card"><span class="sc-num">Reasoning</span><h3>What is the real constraint?</h3><p>The weakest dimension, critical gates and how strong the supporting evidence is.</p></article>
   <article class="sc-card"><span class="sc-num">Next actions</span><h3>Three practical priorities</h3><p>Concrete actions that make the next executive decision more defensible.</p></article>
   <article class="sc-card"><span class="sc-num">Your report</span><h3>Private PDF summary</h3><p>Download a concise decision brief. You can optionally rate its usefulness to improve the service.</p></article>
  </div>
 </div>
</section>
<section class="sc-wrap">
 <span class="sc-kicker">A focused advisory experience</span>
 <h2>One assessment. One clear perspective.</h2>
 <p>Answer 18 structured questions in approximately 8–12 minutes, then receive your decision brief. Assessment responses and reports are private to the individually approved client and the Advisory owner. The experience requires no recurring updates.</p>
 <p class="sc-note">This service is a decision aid based on self-reported information, not an independent audit, deployment authorization or regulatory certification. No confidential operational documents are required.</p>
 <div class="sc-actions"><a class="sc-btn" href="?page=advisory-access&amp;view=rollout" target="_self">Open Advisory account →</a>
 <a class="sc-btn light" href="?page=advisory" target="_self">Return to Executive Advisory →</a></div>
</section>
</main>{footer()}'''
