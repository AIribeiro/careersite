"""Member-native AI Portfolio Renewal Advisor: lifecycle, decisions, scenarios and reports.

Uses the verified Advisory session and member JWT from page_advisory_portal.
Every database read/write is owner-scoped AND enforced independently by Supabase RLS.
"""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
from urllib.parse import quote
from copy import deepcopy
import re

import streamlit as st

from advisory_service_visibility import advisory_role, service_enabled
from site_cms import _request_json, _rest_url
from page_advisory_renewal_logic import (
    MODEL_VERSION, DEFAULT_MATERIALITY, STAGES, ROUTES, EVIDENCE, READINESS,
    CONTROLS, assess, scenario, validate,
)
from page_advisory_renewal_reports import report_pdf, report_xlsx
from page_advisory_shared_ui import service_overview, case_header
from page_rollout_workspace_ui import WORKSPACE_CSS
from page_public_services import SERVICES_CSS
from page_advisory_scorecard import SCORECARD_CSS
from site_components import nav, footer

MAX_CASES = 100
MAX_SCENARIOS = 20
SECTIONS=("overview","assessments","assessment","analysis","recommendation","history","help")
TABS={"overview":"Overview","assessments":"My assessments","assessment":"Assessment",
      "analysis":"Decision analysis","recommendation":"Executive recommendation",
      "history":"Decision history","help":"Account / help"}
STEPS=("Decision context","Existing initiative","Strongest alternative","Challenge & analyze")
CSS="""
<style>
.st-key-renewal_workspace{--rn:#132d42;--rg:#a87553}
.st-key-renewal_workspace [data-testid="stVerticalBlockBorderWrapper"]{border:1px solid #ded9cf;border-radius:9px}
.st-key-renewal_workspace [data-testid="stMetric"]{background:#f7f5f0;padding:15px;border-radius:6px}
.st-key-renewal_workspace [data-testid="stPills"]{overflow-x:auto;max-width:100%}
.st-key-renewal_workspace [data-testid="stPills"] button{white-space:nowrap;min-height:42px}
.st-key-renewal_workspace .stHorizontalBlock{gap:.75rem}
.renewal-recommendation{background:#132d42;padding:22px 25px;margin:8px 0 18px;color:#fff}
.renewal-recommendation span{display:block;color:#d6aa85;font-size:11px;font-weight:800;letter-spacing:.12em}
.renewal-recommendation strong{font:500 36px Georgia,serif;display:block;padding:9px 0;color:#fff}
.renewal-recommendation p{color:#dce7ec;font-size:14px;line-height:1.65;max-width:850px}
.renewal-table{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0}
.renewal-table article{background:#f7f7f5;border:1px solid #dfdbd5;padding:16px}
.renewal-table article b{font:500 22px Georgia,serif;color:#16384b;display:block;margin:8px 0}
.renewal-table article small{color:#6a7479}
@media(max-width:700px),(max-device-width:700px){
 .st-key-renewal_workspace .stHorizontalBlock{flex-wrap:wrap!important}
 .st-key-renewal_workspace .stColumn{min-width:min(100%,280px)!important}
 .renewal-table{grid-template-columns:1fr}
 .renewal-recommendation{padding:17px}
}
</style>
"""


def advisory_renewal() -> str:
    """A credible public decision explanation before the membership gate."""
    return f'''{SERVICES_CSS}{SCORECARD_CSS}
<style>
.site .renewal-public .sc-hero{{background:linear-gradient(120deg,#10263a,#25475a)}}
.site .renewal-public .rn-steps{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}}
.site .renewal-public .rn-steps article{{padding:22px;border:1px solid #dcd8d0;background:#fff}}
.site .renewal-public .rn-steps h3{{font:500 23px Georgia,serif;color:#183246}}
.site .renewal-public .rn-outcome{{padding:24px;background:#f4f5f2;border-left:4px solid #b27d59}}
@media(max-width:700px){{.site .renewal-public .rn-steps{{grid-template-columns:1fr}}}}
</style>{nav("advisory")}
<main class="site sc-page renewal-public">
<section class="sc-hero"><span class="sc-kicker">COMPLIMENTARY EXECUTIVE DECISION SUPPORT</span>
<h1>AI Portfolio Renewal Advisor</h1>
<p>Would you still fund this AI initiative today, knowing what you know now?</p>
<p>An existing AI initiative can meet its milestones and still be the wrong next commitment.
Compare what the business can gain from continuing against its strongest credible alternative.
Past expenditure cannot justify the next allocation.</p>
<div class="sc-actions"><a class="sc-btn" href="?page=advisory-access&amp;view=renewal" target="_self">Register free · Open advisor</a>
<a class="sc-btn light" href="?page=advisory-access&amp;view=renewal&amp;signin=1" target="_self">Already registered? Sign in</a></div>
</section>
<section class="sc-section"><span class="sc-kicker">THE QUESTION TRADITIONAL PROJECT REVIEWS MISS</span>
<h2>Delivery progress is not renewed investment merit.</h2>
<p>A standard review asks whether work is on time and within budget. This advisor asks which use
of the next funding, specialist capacity and executive attention offers the strongest prospective business case.
It evaluates one incumbent against another route to the same business outcome: a smaller AI solution,
process redesign, system improvement, experiment or release of resources.</p></section>
<section class="sc-section"><h2>How the Renewal Challenge works</h2>
<div class="rn-steps">
<article><span class="sc-kicker">01 / FRAME</span><h3>Define the next commitment</h3><p>Specify the operating outcome, baseline, future benefit and cost, horizon, owner, scarce capacity and evidence for both options.</p></article>
<article><span class="sc-kicker">02 / CHALLENGE</span><h3>Judge twice</h3><p>First compare the future case without giving earlier approval an advantage. Then restore actual switching costs, continuity, obligations, risk and readiness.</p></article>
<article><span class="sc-kicker">03 / DECIDE</span><h3>Record a defensible choice</h3><p>Review RENEW, REPLACE, TEST, STOP or HOLD, explore sensitivity, then record the executive's own decision, owner and next evidence gate.</p></article>
</div></section>
<section class="sc-section"><h2>What to prepare</h2><p>Bring one initiative approaching a decision point; an outcome KPI and current baseline;
total future benefits and delivery/run costs for the same horizon; specialist days;
the strongest alternative; and honest evidence, adoption, data, operating-owner and risk assessments.
Estimated values must be identified as estimates, not measured results.</p></section>
<section class="sc-section"><span class="sc-kicker">ILLUSTRATIVE OUTCOME · SYNTHETIC ONLY</span>
<div class="rn-outcome"><h2>REPLACE · repair the process before expanding the AI assistant</h2>
<p>In a hypothetical 12-month service case, the process alternative produces higher prospective net value
after transition expense, uses fewer scarce specialist days and has clearer operating ownership.
The decision is conditional on protecting service continuity and checking the measured case-resolution KPI.</p>
<p><strong>Next management action:</strong> Redirect the next gated commitment to knowledge ownership and case routing;
retain useful assistant assets and review the results after 60 days.</p></div></section>
<section class="sc-section"><h2>Your executive output</h2>
<p>A private assessment history; a clear explanation of the financial comparison and mandatory human-review gates;
saved scenario challenges; a dated authorized decision; a printable executive PDF and an editable
Excel export populated from your actual case. You can return to drafts without seeking individual approval.</p>
<h2>What the method can and cannot say</h2><p>Developed by Jair Ribeiro from the published
<a href="?page=briefing&amp;article=would-you-fund-the-same-ai-initiatives-today" target="_self">AI Portfolio Renewal Challenge</a>,
informed by prospective appraisal, portfolio governance and AI risk-management principles.
It does not audit your inputs, certify compliance or predict actual returns. The 10% default financial
materiality band is adjustable management judgment, not an independently validated industry rule.
Mandatory obligations and material unpriced value are handled as human decision gates, not numerical multipliers.</p></section>
<section class="sc-section"><h2>Access is complimentary for registered Advisory members.</h2>
<p>Registration lets you save private work and resume your decisions. No service purchase or individual
admin approval is required. Sensitive assessment contents are not sent to an AI model.</p>
<div class="sc-actions"><a class="sc-btn" href="?page=advisory-access&amp;view=renewal" target="_self">Open my private workspace</a>
<a class="sc-btn light" href="?page=advisory-access&amp;view=renewal&amp;signin=1" target="_self">Sign in</a></div></section>
</main>{footer()}'''


def _api(method: str, path: str, token: str, payload: dict | None = None,
         *, returning: bool = False):
    opts={"token":token,"timeout":17}
    if payload is not None:opts["payload"]=payload
    if returning:opts["prefer"]="return=representation"
    return _request_json(method,_rest_url(path),**opts)


def _cases(token: str, uid: str) -> list[dict]:
    rows=_api("GET","portfolio_advisory_renewal_assessments?select=id,initiative,status,"
              "inputs,analysis,model_version,revision,synthetic,next_review,created_at,updated_at"
              "&owner_id=eq."+quote(uid,safe="")+"&order=updated_at.desc&limit=120",token)
    if not isinstance(rows,list):raise RuntimeError("Private case history unavailable.")
    return rows


def _children(token: str,table: str,aid: str, limit: int=50) -> list[dict]:
    if table not in ("portfolio_advisory_renewal_scenarios","portfolio_advisory_renewal_decisions",
                    "portfolio_advisory_renewal_versions"):
        raise ValueError("Invalid assessment history table.")
    rows=_api("GET",table+"?select=*&assessment_id=eq."+quote(aid,safe="")+
              "&order="+("revision.desc" if table.endswith("versions") else
                         "recorded_at.desc" if table.endswith("decisions") else "created_at.desc")+
              "&limit="+str(limit),token)
    if not isinstance(rows,list):raise RuntimeError("Decision history could not be verified.")
    return rows


def _event(token: str,uid: str,aid: str | None,event: str,synthetic: bool,
           recommendation: str | None = None) -> None:
    # Only coarse action categories enter owner reporting; never business values.
    payload={"user_id":uid,"assessment_id":aid,"event":event,"synthetic":synthetic}
    if recommendation in ("RENEW","REPLACE","TEST","STOP","HOLD"):
        payload["recommendation"]=recommendation
    try:_api("POST","portfolio_advisory_renewal_events",token,payload)
    except (RuntimeError,ValueError,TimeoutError,OSError):pass


def _create(token: str,uid: str,count: int) -> str:
    if count>=MAX_CASES:raise ValueError("Maximum active cases reached. Archive or delete a case before starting another.")
    rows=_api("POST","portfolio_advisory_renewal_assessments?select=id",token,
              {"owner_id":uid,"initiative":"Untitled renewal decision","status":"draft",
               "inputs":{},"analysis":{},"model_version":MODEL_VERSION},returning=True)
    if not isinstance(rows,list) or len(rows)!=1 or not rows[0].get("id"):
        raise RuntimeError("The server did not confirm the new draft.")
    return str(rows[0]["id"])


def _save(token: str,uid: str,case: dict,inputs: dict,*, analyze: bool=False) -> dict:
    if not isinstance(inputs,dict):raise ValueError("Invalid assessment input.")
    result=assess(inputs) if analyze else {}
    if analyze and result["recommendation"]=="COMPLETE INPUTS":
        raise ValueError("Complete inputs: "+"; ".join(result["missing"][:4]))
    status="analyzed" if analyze else ("ready" if assess(inputs)["recommendation"]!="COMPLETE INPUTS" else "draft")
    name=str((inputs.get("context") or {}).get("name") or "Untitled renewal decision").strip()[:200]
    aid=quote(str(case["id"]),safe="")
    rows=_api("PATCH","portfolio_advisory_renewal_assessments?id=eq."+aid+
              "&owner_id=eq."+quote(uid,safe="")+"&select=id",token,
              {"initiative":name,"inputs":inputs,"analysis":result,
               "status":status,"model_version":MODEL_VERSION,
               "next_review":(inputs.get("context") or {}).get("review_date") or None},
              returning=True)
    if not isinstance(rows,list) or len(rows)!=1 or str(rows[0]["id"])!=str(case["id"]):
        raise RuntimeError("The assessment save could not be independently confirmed.")
    return result


def _start(token: str,uid: str,count: int) -> None:
    aid=_create(token,uid,count)
    _event(token,uid,aid,"service_start",False)
    st.session_state["renewal_selected"]=aid
    st.session_state["renewal_stage"]=STEPS[0]
    st.session_state["renewal_section"]="assessment"
    st.query_params["renewal_section"]="assessment"
    st.rerun()


def _go(section: str,aid: str="") -> None:
    st.session_state["renewal_section"]=section
    st.query_params["renewal_section"]=section
    if aid:st.session_state["renewal_selected"]=aid
    st.rerun()


def _nav_changed() -> None:
    requested=st.session_state.get("rn_nav_pills")
    if requested in SECTIONS:
        st.query_params["renewal_section"]=requested
        st.session_state["renewal_section"]=requested


def _stage_changed() -> None:
    requested=st.session_state.get("renewal_stage_select")
    if requested in STEPS:
        st.session_state["renewal_stage"]=requested


def _default_case() -> dict:
    return {
        "context":{"name":"","function":"Customer service","outcome":"","baseline":"",
                   "stage":"pilot","owner":"","authority":"","currency":"SEK",
                   "horizon_months":12,"next_commitment":0.0,"opportunity_cost_day":0.0,
                   "materiality":DEFAULT_MATERIALITY,"mandatory_obligation":False,
                   "material_nonfinancial":False,"nonfinancial_reviewed":False,
                   "review_date":str(date.today()+timedelta(days=90))},
        "incumbent":{"name":"","benefit":0.0,"remaining_cost":0.0,"specialist_days":0.0,
                     "transition_cost":0.0,"evidence":"hypothesis","adoption":"partial",
                     "operations":"partial","data":"partial","controls":"mitigate",
                     "operating_owner":False,"mandatory_meets":True},
        "alternative":{"name":"","route":"process_redesign","benefit":0.0,
                     "remaining_cost":0.0,"specialist_days":0.0,"transition_cost":0.0,
                     "evidence":"hypothesis","adoption":"partial","operations":"partial",
                     "data":"partial","controls":"mitigate","operating_owner":False,
                     "mandatory_meets":True}
    }


def _inputs(case: dict) -> dict:
    base=_default_case()
    existing=case.get("inputs") or {}
    for key in ("context","incumbent","alternative"):
        if isinstance(existing.get(key),dict):base[key].update(existing[key])
    return base


def _selector(label: str, values: tuple | list, default, *, key: str, format_func=None):
    idx=values.index(default) if default in values else 0
    return st.selectbox(label,values,index=idx,key=key,format_func=format_func)


def _yes(label: str, value: bool, key: str, help: str="") -> bool:
    return _selector(label,("No","Yes"),"Yes" if value else "No",
                     key=key)== "Yes"


def _num(label: str, value, key: str, help: str="") -> float:
    try:v=max(0.0,float(value))
    except (ValueError,TypeError):v=0.0
    return st.number_input(label,min_value=0.0,max_value=1e15,value=v,
                           step=100.0,key=key,help=help or None,format="%.2f")


def _stage_ui(case: dict,token: str,uid: str) -> None:
    data=_inputs(case)
    desired=st.session_state.get("renewal_stage",STEPS[0])
    if st.session_state.get("renewal_stage_select") != desired:
        st.session_state["renewal_stage_select"]=desired
    stage=st.pills("Assessment stage",STEPS,selection_mode="single",
                   default=desired, on_change=_stage_changed,
                   key="renewal_stage_select",required=True,width="stretch")
    st.session_state["renewal_stage"]=stage
    prefix="rn_"+str(case["id"])[:8]+"_"+str(STEPS.index(stage))
    st.caption("Working on: "+str(data["context"]["name"] or case["initiative"])+
               "  |  "+str(stage)+"  |  Auto-analysis is not investment approval")
    if stage==STEPS[3]:
        missing=assess(data).get("missing",[])
        if missing:
            st.warning(str(len(missing))+" input issues remain before analysis.")
            for item in missing[:8]:st.caption(item)
        else:
            st.success("Both options have enough structured inputs for a rules-based comparison.")
        c1,c2=st.columns(2)
        if c1.button("Save as draft",key=prefix+"_draft"):
            try:_save(token,uid,case,data)
            except (ValueError,RuntimeError,TimeoutError) as e:st.error(str(e))
            else:_event(token,uid,str(case["id"]),"draft_saved",case.get("synthetic",False));st.success("Draft saved.")
        if c2.button("Analyze both options",type="primary",key=prefix+"_analyze"):
            try:final=_save(token,uid,case,data,analyze=True)
            except (ValueError,RuntimeError,TimeoutError) as e:st.error(str(e))
            else:
                _event(token,uid,str(case["id"]),"analyzed",case.get("synthetic",False),final["recommendation"])
                _go("recommendation",str(case["id"]))
        return
    with st.form(prefix+"_form",clear_on_submit=False,border=True):
        if stage==STEPS[0]:
            d=data["context"]
            st.markdown("#### 01 / Establish the next decision")
            d["name"]=st.text_input("Initiative name",value=d["name"],max_chars=200)
            d["function"]=_selector("Business function",("Customer service","Operations","Finance","HR","Commercial","Supply chain","IT / technology","Other"),d["function"],key=prefix+"_function")
            d["outcome"]=st.text_input("Target business outcome and KPI",value=d["outcome"],help="Describe a measurable change in business performance, not model functionality.")
            d["baseline"]=st.text_area("Current operational baseline",value=d["baseline"],height=80,help="Observed baseline, evidence period and source. Clearly separate estimates.")
            d["stage"]=_selector("Incumbent lifecycle stage",STAGES,d["stage"],key=prefix+"_stage",format_func=lambda v:v.title())
            a,b=st.columns(2)
            with a:
                d["owner"]=st.text_input("Accountable business owner",value=d["owner"])
                d["currency"]=_selector("Currency",("SEK","EUR","USD","GBP","BRL"),d["currency"],key=prefix+"_cur")
                d["horizon_months"]=st.number_input("Shared horizon in months",min_value=1,max_value=60,value=int(d["horizon_months"]),step=1)
            with b:
                d["authority"]=st.text_input("Funding decision authority",value=d["authority"])
                d["next_commitment"]=_num("Next commitment requested (total, shared currency)",d["next_commitment"],prefix+"_next")
                d["opportunity_cost_day"]=_num("Opportunity cost per specialist day",d["opportunity_cost_day"],prefix+"_day",help="Use a supported forgone alternative value or document why zero is appropriate.")
            materiality_pct=st.slider("Material financial advantage required (%)",min_value=1,max_value=50,value=int(round(float(d["materiality"])*100)),step=1,
                                      help="Default 10%; management judgment, not a statistically validated threshold.")
            d["materiality"]=materiality_pct/100
            d["mandatory_obligation"]=_yes("Mandatory legal, contractual or service-continuity duty?",d["mandatory_obligation"],prefix+"_mandatory")
            d["material_nonfinancial"]=_yes("Material nonfinancial benefit or avoided risk?",d["material_nonfinancial"],prefix+"_nonfinance")
            if d["material_nonfinancial"]:
                d["nonfinancial_reviewed"]=_yes("Has an accountable specialist reviewed this unpriced consideration?",d["nonfinancial_reviewed"],prefix+"_reviewed")
            else:d["nonfinancial_reviewed"]=False
            d["review_date"]=str(st.date_input("Next review or evidence gate",value=date.fromisoformat(d["review_date"]) if d.get("review_date") else date.today()+timedelta(days=90)))
        else:
            key="incumbent" if stage==STEPS[1] else "alternative"
            d=data[key]
            st.markdown("#### "+("02 / Evaluate the existing initiative" if key=="incumbent" else "03 / Establish the strongest alternative"))
            d["name"]=st.text_input("Route name",value=d["name"],max_chars=200)
            if key=="alternative":
                d["route"]=_selector("Alternative route",ROUTES,d.get("route","process_redesign"),key=prefix+"_route",
                    format_func=lambda v:v.replace("_"," ").capitalize())
            st.caption("Enter the TOTAL anticipated benefit, cost and specialist capacity over the common "+
                       str(data["context"]["horizon_months"])+"-month horizon in "+str(data["context"]["currency"])+".")
            a,b=st.columns(2)
            with a:
                d["benefit"]=_num("Prospective incremental benefit",d["benefit"],prefix+"_benefit",help="Future measurable business benefit over the whole stated horizon; do not add sunk cost.")
                d["specialist_days"]=_num("Scarce specialist days required",d["specialist_days"],prefix+"_days",help="Constrained specialist capacity; do not count the same capacity twice.")
            with b:
                d["remaining_cost"]=_num("Remaining delivery and operating costs",d["remaining_cost"],prefix+"_cost",help="Unspent delivery and run costs over the same horizon.")
                d["transition_cost"]=_num("Transition/switching/exit costs",d["transition_cost"],prefix+"_switch",help="Future migration, exit and retained-service cost. For incumbent often zero.")
            d["evidence"]=_selector("Evidence maturity",EVIDENCE,d["evidence"],key=prefix+"_evidence")
            x,y,z=st.columns(3)
            with x:d["adoption"]=_selector("Adoption readiness",READINESS,d["adoption"],key=prefix+"_adoption")
            with y:d["operations"]=_selector("Operating readiness",READINESS,d["operations"],key=prefix+"_operations")
            with z:d["data"]=_selector("Data readiness",READINESS,d["data"],key=prefix+"_data")
            d["controls"]=_selector("Risk and control status",CONTROLS,d["controls"],key=prefix+"_controls")
            d["operating_owner"]=_yes("Is ongoing operating ownership confirmed?",d["operating_owner"],prefix+"_owner")
            d["mandatory_meets"]=_yes("Would this option satisfy mandatory duties?",d["mandatory_meets"],prefix+"_meets")
            d["benefit_basis"]=st.text_area("Benefit basis and measurement period",value=str(d.get("benefit_basis","")),height=72,
                                           help="What is measured, estimated or assumed? State the source and time window.")
            d["cost_basis"]=st.text_area("Future cost basis and exclusions",value=str(d.get("cost_basis","")),height=72,
                                        help="Include only the remaining horizon; avoid double-counting specialist capacity already in costs.")
            d["evidence_note"]=st.text_area("Observed evidence, dependencies and data limits",value=str(d.get("evidence_note","")),height=72)
            d["reusable_assets"]=st.text_input("Useful existing assets or migration impacts",value=str(d.get("reusable_assets","")))
            st.caption("Observations are not automatically treated as proven outcomes; missing financial evidence can change the executive judgment.")
        a,b=st.columns(2)
        save=a.form_submit_button("Save draft",use_container_width=True)
        advance=b.form_submit_button("Save & continue",type="primary",use_container_width=True)
    if save or advance:
        try:_save(token,uid,case,data)
        except (ValueError,RuntimeError,TimeoutError) as e:st.error(str(e))
        else:
            _event(token,uid,str(case["id"]),"draft_saved",case.get("synthetic",False))
            if advance:
                st.session_state["renewal_stage"]=STEPS[min(3,STEPS.index(stage)+1)]
                st.rerun()
            st.success("Saved to your private assessment history.")


def _analysis_ui(token: str,uid: str,case: dict) -> None:
    data=_inputs(case)
    outcome=assess(data)
    if outcome["recommendation"]=="COMPLETE INPUTS":
        st.warning("This assessment cannot be analyzed until its inputs are complete.")
        for m in outcome["missing"][:8]:st.caption(m)
        if st.button("Return to inputs",type="primary"): _go("assessment")
        return
    c=data["context"];first=outcome["pass_one"];second=outcome["pass_two"]
    st.markdown("### Two-pass decision analysis")
    st.caption(str(c["currency"])+" · "+str(c["horizon_months"])+" months · "+
               MODEL_VERSION+" · no sunk expenditure counted")
    a,b=st.columns(2)
    with a:
        st.markdown("#### Pass one · Clean sheet")
        st.metric("Preferred direction",first["direction"].replace("_"," ").title())
        st.metric("Alternative less incumbent",f"{first['delta']:,.0f} {c['currency']}")
    with b:
        st.markdown("#### Pass two · Real-world")
        st.metric("Financial direction",second["direction"].replace("_"," ").title())
        st.metric("Alternative less incumbent",f"{second['delta']:,.0f} {c['currency']}")
    p=outcome["pass_two"]
    st.html('<div class="renewal-table"><article><small>INCUMBENT / NET FUTURE VALUE</small><b>'+
        escape(f"{p['incumbent_net']:,.0f} {c['currency']}")+'</b><small>'+
        escape(f"{p['incumbent_specialist_days']:,.0f}")+' specialist days</small></article>'+
        '<article><small>ALTERNATIVE / NET FUTURE VALUE</small><b>'+
        escape(f"{p['alternative_net']:,.0f} {c['currency']}")+'</b><small>'+
        escape(f"{p['alternative_specialist_days']:,.0f}")+' specialist days</small></article></div>')
    with st.expander("Exact financial calculations and assumptions"):
        st.write("Future net = prospective business benefit − remaining delivery/run expense − scarce days × opportunity cost per day − actual transition costs.")
        st.json({"incumbent":data["incumbent"],"alternative":data["alternative"],
                 "opportunity_cost_day":c["opportunity_cost_day"],
                 "materiality":outcome["materiality"]},expanded=False)
    st.markdown("#### Challenge the assumptions")
    st.caption("Change a defensible assumption. The comparison updates immediately; saving creates a separate scenario, not a rewrite of the base case.")
    scenario_type=st.selectbox("Stress test",("Alternative benefit downside","Incumbent meets its target",
          "Replacement delayed by months","Replacement transition shock","Capacity cannot be released",
          "Higher specialist opportunity cost","Alternative evidence matures",
          "Mandatory duty blocks replacement"),key="rn_scenario_type")
    change={}
    if scenario_type=="Alternative benefit downside":
        pct=st.slider("Alternative benefit reduction",0,60,20,5,key="rn_down")
        change={"alternative.benefit":round(float(data["alternative"]["benefit"])*(1-pct/100),2)}
    elif scenario_type=="Incumbent meets its target":
        pct=st.slider("Incumbent benefit increase",0,100,25,5,key="rn_up")
        change={"incumbent.benefit":round(float(data["incumbent"]["benefit"])*(1+pct/100),2)}
    elif scenario_type=="Replacement delayed by months":
        months=st.slider("Additional months before benefits materialize",0,int(c["horizon_months"]),min(6,int(c["horizon_months"])),1,key="rn_delay")
        st.caption("Assumption: benefits accrue uniformly over the shared horizon; only the alternative's future benefit is reduced. Costs are held constant.")
        change={"alternative.benefit":round(float(data["alternative"]["benefit"])*max(0,int(c["horizon_months"])-months)/int(c["horizon_months"]),2)}
    elif scenario_type=="Replacement transition shock":
        pct=st.slider("Alternative transition cost increase",0,200,50,10,key="rn_switch")
        change={"alternative.transition_cost":round(float(data["alternative"]["transition_cost"])*(1+pct/100),2)}
    elif scenario_type=="Capacity cannot be released":
        st.caption("Conservative comparison: assume the alternative cannot release incumbent specialist capacity. The alternative bears at least the incumbent's specialist days.")
        change={"alternative.specialist_days":max(float(data["alternative"]["specialist_days"]),float(data["incumbent"]["specialist_days"]))}
    elif scenario_type=="Higher specialist opportunity cost":
        pct=st.slider("Scarce specialist day cost increase",0,200,50,10,key="rn_day")
        change={"context.opportunity_cost_day":round(float(c["opportunity_cost_day"])*(1+pct/100),2)}
    elif scenario_type=="Alternative evidence matures":
        change={"alternative.evidence":"operational","alternative.adoption":"ready","alternative.operations":"ready"}
    else:change={"context.mandatory_obligation":True,"alternative.mandatory_meets":False}
    scenario_inputs,what_if=scenario(data,change)
    x,y=st.columns(2)
    with x:st.metric("Base recommendation",outcome["recommendation"])
    with y:st.metric("Scenario recommendation",what_if["recommendation"],
                     delta=("Changed" if outcome["recommendation"]!=what_if["recommendation"] else "Unchanged"),
                     delta_color="off")
    st.write(what_if["reasons"][0])
    try:scenarios=_children(token,"portfolio_advisory_renewal_scenarios",str(case["id"]))
    except (RuntimeError,ValueError,TimeoutError):scenarios=[]
    if st.button("Save this scenario",key="rn_save_scenario",type="primary"):
        if len(scenarios)>=MAX_SCENARIOS:st.error("Limit of 20 saved scenarios per assessment reached.")
        else:
            try:
                _api("POST","portfolio_advisory_renewal_scenarios",token,
                     {"owner_id":uid,"assessment_id":case["id"],"label":scenario_type,
                      "changes":change,"inputs":scenario_inputs,"analysis":what_if,
                      "base_revision":case["revision"],"model_version":MODEL_VERSION,
                      "synthetic":case["synthetic"]})
            except (RuntimeError,ValueError,TimeoutError) as e:st.error("Scenario could not be saved: "+str(e))
            else:_event(token,uid,str(case["id"]),"scenario_saved",case["synthetic"]);st.rerun()
    if scenarios:
        with st.expander(f"Saved scenario history ({len(scenarios)})"):
            for s in scenarios:
                st.markdown("**"+str(s["label"])+"** · "+
                    str((s.get("analysis") or {}).get("recommendation",""))+
                    " · "+str(s.get("created_at",""))[:10])
    if st.button("Open executive recommendation",type="primary",key="rn_to_recommend"):
        _go("recommendation")


def _recommendation_ui(token: str,uid: str,case: dict) -> None:
    result=assess(_inputs(case))
    if result["recommendation"]=="COMPLETE INPUTS":
        st.warning("No executive recommendation until all required inputs are supplied.")
        if st.button("Complete assessment",type="primary"): _go("assessment")
        return
    if not case.get("analysis") or case.get("model_version")!=MODEL_VERSION:
        st.info("The analysis has changed since the last saved snapshot. Review and save it before using the executive report.")
        if st.button("Save current analysis",type="primary",key="rn_save_analysis"):
            try:_save(token,uid,case,_inputs(case),analyze=True)
            except (RuntimeError,ValueError,TimeoutError) as e:st.error(str(e))
            else:st.rerun()
        return
    st.html('<section class="renewal-recommendation"><span>DETERMINISTIC EXECUTIVE RECOMMENDATION</span>'+
         '<strong>'+escape(result["recommendation"])+'</strong><p>'+escape(result["reasons"][0])+
         '</p></section>')
    for heading,value in (("Why this choice",result["reasons"]),("What could change the decision",result["uncertainty"])):
        st.markdown("#### "+heading)
        for item in value or ["No additional limitation supplied."]:
            st.markdown("- "+str(item))
    st.markdown("#### Management action")
    st.info(result["next_action"])
    d=_inputs(case)["context"]
    st.caption("ACCOUNTABILITY · "+str(d["owner"])+" · Funding authority: "+str(d["authority"])+
               " · Next proposed review: "+str(d.get("review_date","To be agreed")))
    try:decisions=_children(token,"portfolio_advisory_renewal_decisions",str(case["id"]))
    except (RuntimeError,ValueError,TimeoutError):decisions=[]
    current=decisions[0] if decisions else None
    if current:
        st.success("Executive choice recorded: "+str(current["authorized_action"])+
                   " · Review "+str(current["next_review"]))
        if current["authorized_action"]!=result["recommendation"]:
            st.warning("The authorized choice differs from the deterministic recommendation. The executive rationale is preserved.")
        st.caption(str(current["rationale"]))
    with st.expander("Record the executive's authorized decision (separate from model)",expanded=not bool(current)):
        with st.form("rn_signoff_"+str(case["id"])[:8],border=False):
            action=st.selectbox("Authorized action",("RENEW","REPLACE","TEST","STOP","HOLD"),
                                index=("RENEW","REPLACE","TEST","STOP","HOLD").index(result["recommendation"])
                                if result["recommendation"] in ("RENEW","REPLACE","TEST","STOP","HOLD") else 0)
            authority=st.text_input("Named decision authority",value=str(d["authority"]))
            rationale=st.text_area("Reasoning, trade-offs and displaced work",height=120,
                help="State why this is the right next commitment, particularly if departing from the model.")
            review=st.date_input("Next executive review",value=date.fromisoformat(d["review_date"]) if d.get("review_date") else date.today()+timedelta(days=60))
            submitted=st.form_submit_button("Record executive authorization",type="primary")
        if submitted:
            if len(rationale.strip())<12 or len(authority.strip())<2:
                st.error("A named authority and at least 12 characters of decision rationale are required.")
            else:
                try:
                    _api("POST","portfolio_advisory_renewal_decisions",token,
                         {"owner_id":uid,"assessment_id":case["id"],"authorized_action":action,
                          "recommendation_at_signoff":result["recommendation"],
                          "authorized_by":authority.strip(),"rationale":rationale.strip(),
                          "next_review":str(review),"supporting_revision":case["revision"],
                          "synthetic":case["synthetic"]})
                    _api("PATCH","portfolio_advisory_renewal_assessments?id=eq."+quote(case["id"],safe=""),token,
                         {"status":"decision_recorded","next_review":str(review)})
                except (RuntimeError,ValueError,TimeoutError) as e:
                    st.error("Decision persistence could not be confirmed: "+str(e))
                else:
                    _event(token,uid,str(case["id"]),"decision_recorded",case["synthetic"])
                    st.rerun()
    st.markdown("#### Private executive exports")
    st.caption("Generated in the authenticated session; files are never uploaded to public static storage.")
    if case.get("analysis"):
        try:
            pdf=report_pdf(_inputs(case),result,current,synthetic=case["synthetic"],created=case["created_at"])
            excel=report_xlsx(_inputs(case),result,current,synthetic=case["synthetic"])
        except (ValueError,RuntimeError,UnicodeError) as e:
            st.error("Report generation failed: "+str(e))
            return
        a,b=st.columns(2)
        if a.download_button("Download executive PDF",pdf,
                             file_name="AI_Portfolio_Renewal_"+case["id"][:8]+".pdf",
                             mime="application/pdf",use_container_width=True):
            _event(token,uid,case["id"],"pdf_download",case["synthetic"])
        if b.download_button("Download editable Excel",excel,
                             file_name="AI_Portfolio_Renewal_"+case["id"][:8]+".xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             use_container_width=True):
            _event(token,uid,case["id"],"excel_download",case["synthetic"])


def render_private_renewal(session: dict,user: dict) -> None:
    token=str(session.get("access_token") or "")
    uid=str(user.get("id") or "")
    if not token or not uid or not user.get("email_confirmed_at"):
        st.error("A verified Advisory member is required.");return
    try:admin=advisory_role(token)=="admin"
    except (ValueError,RuntimeError,TimeoutError):admin=False
    if not service_enabled("renewal",admin=admin):
        st.error("This service is currently unavailable.");return
    st.html(WORKSPACE_CSS+CSS)
    with st.container(key="renewal_workspace"):
        st.markdown("### AI Portfolio Renewal Advisor")
        st.caption("Reassess the next commitment · Member-private decision workspace · "+MODEL_VERSION)
        requested=str(st.query_params.get("renewal_section") or st.session_state.get("renewal_section","overview"))
        if requested not in SECTIONS:requested="overview"
        if st.session_state.get("rn_nav_pills") != requested:
            st.session_state["rn_nav_pills"]=requested
        section=st.pills("Renewal workspace",SECTIONS,selection_mode="single",
                         default=requested,on_change=_nav_changed,
                         required=True,format_func=lambda v:TABS[v],key="rn_nav_pills",
                         width="stretch")
        st.session_state["renewal_section"]=section
        try:records=_cases(token,uid)
        except (RuntimeError,ValueError,TimeoutError,OSError):
            st.error("Your private assessments cannot be loaded. No assumptions were changed.");return
        selected_id=st.session_state.get("renewal_selected") or ""
        cases={str(row["id"]):row for row in records}
        case=cases.get(selected_id)
        if section=="overview":
            service_overview(
                hero="Challenge the next investment, not the original approval.",
                description="Compare one AI initiative already consuming resources against its strongest credible route to the same business outcome. Preserve learning while refusing to treat sunk cost as a business case.",
                access="Complimentary for registered members",assessment_format="Two-pass / two-route challenge",
                saved_count=len(records),
                outputs=(("Recommendation","Renew, replace, test, stop or hold",
                          "Deterministic reasoning tied to prospective outcomes and mandatory conditions."),
                         ("Scenario","What could reverse the result",
                          "Sensitivity to benefit, switching cost, constrained capacity and readiness."),
                         ("Decision record","An accountable executive outcome",
                          "Authorized choice, evidence requirement, review date, private PDF and Excel.")),
                steps=(("Frame","Enter a common business outcome, horizon and prospective costs."),
                       ("Challenge","Compare future merits, then restore obligations and transition consequences."),
                       ("Authorize","Run scenario checks, record the real leadership choice and next gate.")),
                boundary="This is a management decision aid based on your inputs. It does not authorize spending, validate a forecast or determine legal compliance.")
            if st.button("Start new assessment",type="primary",key="rn_overview_new"):
                try:_start(token,uid,len(records))
                except (RuntimeError,ValueError,TimeoutError) as e:st.error(str(e))
            if records:
                st.markdown("#### Recent cases")
                for row in records[:5]:
                    a,b=st.columns([4,1])
                    a.markdown("**"+str(row["initiative"])+"**  \\n"+
                               str(row["status"]).replace("_"," ").title()+
                               (" · Synthetic" if row["synthetic"] else "")+
                               " · updated "+str(row["updated_at"])[:10])
                    if b.button("Open",key="rn_recent_"+str(row["id"])):
                        _go("recommendation" if row["status"]!="draft" else "assessment",str(row["id"]))
            return
        if section=="assessments":
            st.markdown("#### Your private assessment history")
            search=st.text_input("Find an initiative",placeholder="Search by name or recommendation",key="rn_find")
            filtered=[r for r in records if search.casefold() in
                      (str(r["initiative"])+str((r.get("analysis") or {}).get("recommendation",""))).casefold()]
            if st.button("Start a new assessment",type="primary",key="rn_history_new"):
                try:_start(token,uid,len(records))
                except (RuntimeError,ValueError,TimeoutError) as e:st.error(str(e))
            if not filtered:st.info("No matching assessments. Start a new renewal challenge.")
            for row in filtered:
                a,b=st.columns([4,1],vertical_alignment="center")
                a.markdown("**"+escape(str(row["initiative"]))+"**")
                a.caption(("SYNTHETIC · " if row["synthetic"] else "")+
                    str(row["status"]).replace("_"," ").title()+" · "+
                    str((row.get("analysis") or {}).get("recommendation","Not analyzed"))+
                    " · Review "+str(row.get("next_review") or "not set"))
                if b.button("Open case",key="rn_case_"+str(row["id"])):
                    _go("recommendation" if (row.get("analysis") or {}).get("recommendation") else "assessment",str(row["id"]))
            return
        if not case:
            st.info("Select an assessment in My assessments or start a new one.")
            if st.button("Browse assessments",type="primary",key="rn_browse"): _go("assessments")
            return
        case_header(title=case["initiative"],date=str(case["updated_at"])[:10],
                    context="Renewal challenge / "+case["status"].replace("_"," ")+
                    " / revision "+str(case["revision"]),synthetic=case["synthetic"])
        if section=="assessment":
            _stage_ui(case,token,uid)
        elif section=="analysis":
            _analysis_ui(token,uid,case)
        elif section=="recommendation":
            _recommendation_ui(token,uid,case)
        elif section=="history":
            st.markdown("#### Permanent decision and scenario history")
            try:
                versions=_children(token,"portfolio_advisory_renewal_versions",case["id"],100)
                scenarios=_children(token,"portfolio_advisory_renewal_scenarios",case["id"],50)
                decisions=_children(token,"portfolio_advisory_renewal_decisions",case["id"],50)
            except (ValueError,RuntimeError,TimeoutError):
                st.error("History could not be verified. The case was not changed.");return
            a,b,c=st.columns(3)
            a.metric("Saved versions",len(versions));b.metric("Scenarios",len(scenarios));c.metric("Executive decisions",len(decisions))
            for item in decisions[:12]:
                st.markdown("**"+item["authorized_action"]+"** · "+str(item["recorded_at"])[:16]+
                            " · authority "+str(item["authorized_by"]))
                st.caption(str(item["rationale"]))
            with st.expander("Assumption revisions",expanded=False):
                for v in versions:st.caption("Revision "+str(v["revision"])+" · "+str(v["recorded_at"])[:16]+
                                             " · "+str(v["model_version"]))
            with st.expander("Stored scenario snapshots",expanded=False):
                for s in scenarios:st.caption(str(s["label"])+" · "+str((s.get("analysis") or {}).get("recommendation"))+
                                            " · "+str(s["created_at"])[:16])
        elif section=="help":
            st.markdown("#### About the Renewal Challenge")
            st.write("Sunk costs are excluded. Real switching expense and usable existing assets belong in the forward case. The site records an evidence-based recommendation, while an executive separately authorizes any commitment.")
            st.markdown("[Published methodology](?page=briefing&article=would-you-fund-the-same-ai-initiatives-today) · [Privacy and data notice](?page=privacy) · [Support](mailto:info@jairribeiro.com)")
            st.caption("To request deletion of your full account or records contact support. You can correct your draft in the Assessment tab; revisions remain traceable.")
