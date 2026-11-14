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
from page_advisory_feedback import render_feedback

SERVICE_TITLE = "Enterprise AI Rollout Readiness Advisor"
REQUEST_TITLE = "Enterprise AI Rollout Readiness Advisor — access request"
REQUEST_MARKER = "ENTERPRISE AI ROLLOUT ADVISOR ACCESS REQUEST"
SERVICE_KEY = "rollout"

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
    gates = [q for q in QUESTIONS if q[4] and response[q[0]] < 2]
    weak = sorted(QUESTIONS, key=lambda q: (response[q[0]], not q[4]))
    actions = []
    for q in list(gates) + weak:
        if response[q[0]] < 3 and q[3] not in actions:
            actions.append(q[3])
        if len(actions) == 3:
            break
    if gates:
        label = "PAUSE SCALING"
        verdict = "Do not authorize wider deployment until critical conditions are resolved."
        reason = ("At least one critical security, oversight, reliability, regulatory or "
                  "adoption-ownership condition is not sufficiently demonstrated.")
    elif len(missing) >= 5:
        label = "EVIDENCE INCOMPLETE"
        verdict = "Defer the scaling decision until essential evidence has been collected."
        reason = "Too many readiness conditions remain unassessed to support a credible decision."
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

def _assessments(token: str, uid: str, request_id: str) -> list[dict]:
    rows = _request_json(
        "GET", _rest_url("portfolio_advisory_rollout_assessments?"
                         "select=id,answers,created_at,model_version"
                         "&user_id=eq." + quote(uid,safe="") +
                         "&request_id=eq." + quote(request_id,safe="") +
                         "&order=created_at.desc&limit=30"),
        token=token, timeout=12)
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
        st.info("Your request is under individual review in your existing Advisory conversation.")
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

def _input_form(token: str, request_id: str) -> None:
    st.markdown("### Begin a readiness assessment")
    st.caption("18 short questions across five decision dimensions. Use non-confidential information. "
               "Only select 'Demonstrated' when credible evidence exists.")
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
        responses={}
        for area in AREAS:
            with st.expander(area,expanded=True):
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
            st.session_state["rollout_latest_report_id"]=new_id
            st.session_state["rollout_new_assessment"]=False
            st.success("Your decision brief has been generated and saved privately.")
            st.rerun()
        except ValueError as ex:
            st.warning(str(ex))
        except (RuntimeError,TimeoutError,KeyError):
            st.error("Your assessment could not be saved. Check your access and try again.")

def _pdf_report(result: dict, data: dict) -> bytes:
    from fpdf import FPDF
    pdf=FPDF(format="A4")
    pdf.set_auto_page_break(auto=True,margin=18)
    pdf.add_page()
    pdf.set_margins(20,20,20)
    def safe(text: object) -> str:
        return str(text).replace("—","-").replace("–","-").replace("’","'").replace("•","-").encode("latin-1","replace").decode("latin-1")
    def section(title: str,body: str):
        pdf.set_font("Helvetica","B",12)
        pdf.ln(4);pdf.multi_cell(0,7,safe(title),new_x="LMARGIN",new_y="NEXT")
        pdf.set_font("Helvetica","",10)
        pdf.multi_cell(0,6,safe(body),new_x="LMARGIN",new_y="NEXT")
    pdf.set_font("Helvetica","B",17)
    pdf.multi_cell(0,9,"Enterprise AI Rollout - Executive Decision Brief",new_x="LMARGIN",new_y="NEXT")
    pdf.set_font("Helvetica","",10)
    pdf.multi_cell(0,6,safe(data["context"]["use_case"]+" | "+data["context"]["stage"]),new_x="LMARGIN",new_y="NEXT")
    section("EXECUTIVE VERDICT / "+result["label"],result["verdict"])
    section("Reasoning",result["reason"])
    section("Critical insight",result["insight"])
    section("Readiness profile","\n".join(
        k+": "+str(v)+"%" for k,v in result["dimensions"].items()))
    section("Three priorities","\n".join(str(i+1)+". "+v
        for i,v in enumerate(result["priorities"])))
    if result["critical_gates"]:
        section("Critical unresolved conditions",
                "\n".join("- "+v for v in result["critical_gates"]))
    section("Evidence confidence",result["confidence"]+
            "; "+str(result["unassessed"])+" of 18 conditions unassessed.")
    section("Decision boundary","Self-reported inputs and rule-based advisory guidance. "
            "Independent security, legal, regulatory, technical and operational approvals "
            "remain the organization's responsibility. This is not a compliance certification.")
    pdf.set_y(-17);pdf.set_font("Helvetica","I",8)
    pdf.cell(0,9,"Jair Ribeiro  |  jairribeiro.com  |  Selective Executive AI Advisory")
    return bytes(pdf.output())

def _report_ui(session: dict,user: dict,request_id: str,record: dict) -> None:
    data=record.get("answers")
    try:
        result=assess(data)
    except (ValueError,TypeError):
        st.error("This assessment could not be interpreted. Start a new assessment.")
        return
    rid=str(record["id"])
    st.markdown("### Your executive decision brief")
    st.caption("Assessment "+str(record.get("created_at") or "")[:10]+" · Rule set: rollout-v1")
    if result["label"] in ("PAUSE SCALING","EVIDENCE INCOMPLETE"):
        st.warning("**"+result["label"]+"** · "+result["verdict"])
    else:
        st.info("**"+result["label"]+"** · "+result["verdict"])
    st.write("**Why this decision:** "+result["reason"])
    st.markdown("#### Readiness by decision dimension")
    for area,value in result["dimensions"].items():
        st.progress(value/100,text=area+" · "+str(value)+"%")
    st.markdown("#### The critical insight")
    st.write(result["insight"])
    st.markdown("#### What to do next")
    for i,action in enumerate(result["priorities"],1):
        st.markdown(str(i)+". "+action)
    if result["critical_gates"]:
        st.warning("**Critical conditions:** "+"; ".join(result["critical_gates"]))
    st.caption("Evidence confidence: "+result["confidence"]+" · "+
               str(result["unassessed"])+" of 18 conditions unassessed. "
               "These are self-reported ratings, not verified evidence.")
    st.caption("The output supports executive judgment; it cannot authorize deployment "
               "or replace legal, risk, security or operational reviews.")
    render_feedback(session,user,SERVICE_KEY,"assessment",rid,request_id)
    render_feedback(session,user,SERVICE_KEY,"recommendation",rid,request_id)
    try:
        pdf=_pdf_report(result,data)
    except (RuntimeError,ValueError,UnicodeError):
        st.error("The report could not be generated; your decision brief remains visible.")
        return
    clicked=st.download_button(
        "Download executive decision brief (PDF)",data=pdf,
        file_name="enterprise-ai-rollout-decision-brief.pdf",
        mime="application/pdf",key="rollout_pdf_"+rid,use_container_width=True,
    )
    if clicked:
        st.session_state["rollout_downloaded_"+rid]=True
    if st.session_state.get("rollout_downloaded_"+rid):
        render_feedback(session,user,SERVICE_KEY,"download",rid,request_id)

def render_private_rollout(session: dict,user: dict) -> None:
    token=str(session.get("access_token") or "")
    uid=str(user.get("id") or "")
    if not token or not uid or not user.get("email_confirmed_at"):
        return
    st.markdown("## Enterprise AI Rollout Readiness Advisor")
    st.caption("Single-session executive decision service · Individually approved complimentary access")
    try:
        access=_entitlements(token,uid)
    except (ValueError,RuntimeError,TimeoutError,KeyError):
        st.error("We could not verify access to this service.")
        return
    if not access:
        st.markdown("Assess whether an AI pilot is ready for wider deployment, identify critical "
                    "adoption and governance constraints, and receive an executive recommendation.")
        st.page_link("https://jairribeiro.com/?page=advisory-rollout",
                     label="Explore the readiness methodology")
        _access_request_ui(token,uid)
        return
    selected=access[0]
    request_id=str(selected["request_id"])
    try:
        history=_assessments(token,uid,request_id)
    except (RuntimeError,ValueError,TimeoutError,KeyError):
        st.error("Your assessment records could not be loaded.")
        return
    if history:
        selected_id=st.session_state.get("rollout_latest_report_id")
        if selected_id not in [str(x["id"]) for x in history]:
            selected_id=str(history[0]["id"])
        record=next((x for x in history if str(x["id"])==selected_id),history[0])
        _report_ui(session,user,request_id,record)
        if st.button("Run a new one-session assessment",key="rollout_new_button"):
            st.session_state["rollout_new_assessment"]=True
    if not history or st.session_state.get("rollout_new_assessment"):
        st.divider()
        _input_form(token,request_id)

def advisory_rollout() -> str:
    """Public explanatory page; it never includes client records."""
    return f'''{SERVICES_CSS}{SCORECARD_CSS}{nav("advisory")}
<main class="scorecard-page">
<section class="sc-hero"><div class="container">
 <div class="sc-kicker">Executive AI Advisory / Selective complimentary access</div>
 <h1>Enterprise AI Rollout Readiness Advisor.</h1>
 <p class="sc-lead">Your pilot works. Is your organization actually ready to scale it?</p>
 <p>Complete a focused readiness assessment and receive a clear executive position: proceed in phases, expand conditionally, test further or pause. The recommendation identifies critical constraints and your three highest-priority next actions.</p>
 <div class="sc-actions"><a class="sc-btn" href="?page=advisory-access" target="_self">Request individual access →</a>
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
 <div class="sc-actions"><a class="sc-btn" href="?page=advisory-access" target="_self">Open Advisory account →</a>
 <a class="sc-btn light" href="?page=advisory" target="_self">Return to Executive Advisory →</a></div>
</section>
</main>{footer()}'''
