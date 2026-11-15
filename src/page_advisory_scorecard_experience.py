"""Decision-first executive UX for individually approved AI Portfolio analyses.

One focused screen at a time: service portfolio -> selected analysis ->
decision, actions, options, inputs, record, report or criteria. Server-side
entitlements and the existing Save RPC remain the authority for all data.
"""
from __future__ import annotations


import streamlit as st
from urllib.parse import quote

from site_cms import _request_json, _rest_url
from page_advisory_scorecard_decision import recommend
from page_advisory_scorecard_report import (
    REPORT_VERSION, REPORT_EDITION, build_executive_pdf,
)
from page_advisory_scorecard_new_analysis import (
    read_analysis_requests, render_new_analysis_request,
)
from page_advisory_scorecard_workspace import (
    normalize, CRITERIA, _form_initiative, _policy, _decision_record,
)

SCORECARD_EXPERIENCE_VERSION = "executive_workspace_v2_20261115"

NAV = ("My analyses", "How the service works", "Request new analysis", "Open analysis")
SECTIONS = (
    "Executive decision", "Priority actions", "Portfolio options",
    "Initiatives & evidence", "Decision record", "Executive report",
    "Activity & history", "Assessment criteria",
)

CSS = """
<style>
.st-key-sc_exec_shell [data-testid="stVerticalBlockBorderWrapper"] {
  border-color: rgba(33,59,77,.16);
}
.scx-kicker {color:#a06441;font-size:.73rem;font-weight:750;letter-spacing:.13em;text-transform:uppercase}
.scx-title {font-family:Georgia,serif;font-size:clamp(1.75rem,3.2vw,2.8rem);line-height:1.14;color:#122b40;letter-spacing:-.025em;margin:.35rem 0 .7rem}
.scx-summary {font-size:1.04rem;line-height:1.65;color:#435364;max-width:760px}
.scx-hairline {height:2px;width:48px;background:#b67a54;margin:.9rem 0}
.scx-brief {padding:1.1rem 1.25rem;border-left:4px solid #b77e57;background:#f7f3ef;border-radius:3px;color:#263f52;line-height:1.6}
.scx-brief strong {color:#1b3449}
.scx-subtitle {font-size:.72rem;font-weight:740;letter-spacing:.1em;text-transform:uppercase;color:#886a59;margin-bottom:.2rem}
.scx-dim {color:#627386;font-size:.89rem}
@media(max-width:700px) {
 .scx-title {font-size:1.7rem}
 .scx-brief {padding:.8rem}
}
</style>
"""


def _go(uid: str, view: str, analysis_id: str | None = None,
        section: str | None = None) -> None:
    st.session_state["scx_nav_"+uid]=view
    if analysis_id:
        st.session_state["scx_selected_"+uid]=analysis_id
    if section and analysis_id:
        st.session_state["scx_section_"+analysis_id]=section


def _title(kicker: str, title: str, summary: str = "") -> None:
    import html
    st.html(
        '<div class="scx-kicker">'+html.escape(kicker)+'</div>'
        +'<div class="scx-title">'+html.escape(title)+'</div>'
        +('<p class="scx-summary">'+html.escape(summary)+'</p>' if summary else '')
    )


def _fmt(value: float) -> str:
    return f"{value:,.0f} SEK"


def _analysis_info(ws: dict, requests: dict[str,dict], rank: int) -> dict:
    req=requests.get(str(ws.get("analysis_request_id") or ""),{})
    payload=normalize(ws.get("payload"))
    items=payload["initiatives"]
    reviewed=sum(
        1 for x in items if x.get("name") and x.get("owner")
        and len(x.get("scores") or [])==7
        and all(isinstance(v,int) and v>0 for v in x["scores"])
        and x.get("evidence") not in ("", "Not assessed")
    )
    report=recommend(payload,revision=int(ws.get("revision") or 0))
    if not items:
        status="Not started"
        next_step="Add the first initiative and set the planning limits."
    elif reviewed<len(items):
        status="Assessment incomplete"
        next_step=f"Complete evidence and criteria for {len(items)-reviewed} initiative(s)."
    elif report["recommended"]["count"]==0:
        status="Review required"
        next_step="Resolve missing evidence, controls or portfolio constraints."
    else:
        status="Recommendation available"
        next_step="Review the proposed actions and decision conditions."
    examples=", ".join(str(x.get("name") or "") for x in items[:3] if x.get("name"))
    title=str(req.get("title") or (
        f"AI portfolio investment review · {len(items)} initiatives"
    ))
    context=str(req.get("decision_context") or (
        (f"Assess {len(items)} registered AI opportunities"
         + (f", including {examples}" if examples else "")
         + ". Decide what merits business-case review, a test, a hold or a stop.")
        if items else
        "Build a new AI portfolio assessment and determine what merits "
        "investment review, evidence testing, a hold or a stop."
    ))
    desired=str(req.get("expected_outcome") or (
        "A resource-constrained portfolio recommendation with accountable "
        "actions and a downloadable executive decision brief."
    ))
    return {
        "ws":ws, "data":payload,"report":report,"title":title,"context":context,
        "outcome":desired,"status":status,"next_step":next_step,
        "rank":rank,"count":len(items),"reviewed":reviewed,
        "approved_at":str(ws.get("approved_at") or "")[:10],
        "updated_at":str(ws.get("updated_at") or "")[:16].replace("T"," "),
        "revision":int(ws.get("revision") or 0),
    }


def _service_guide() -> None:
    _title(
        "SERVICE GUIDE · AI PORTFOLIO PRIORITIZATION",
        "From competing AI ideas to a defensible decision",
        "For leaders choosing where to commit scarce funding, delivery capacity "
        "and management attention."
    )
    st.markdown("#### What you receive")
    c1,c2,c3=st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("**01 · Portfolio decision**")
            st.write("A ranked recommendation identifying what to advance, test, hold, redesign or defer.")
    with c2:
        with st.container(border=True):
            st.markdown("**02 · Required next actions**")
            st.write("Evidence to obtain, accountable owners and conditions to resolve before authorization.")
    with c3:
        with st.container(border=True):
            st.markdown("**03 · Executive decision brief**")
            st.write("A downloadable PDF explaining the portfolio choice, trade-offs and go/no-go conditions.")
    st.markdown("#### What the assessment examines")
    st.write(
        "Up to 30 AI initiatives are compared across strategic fit, business value, "
        "feasibility, delivery capacity, data readiness, adoption and risk controls. "
        "The selection considers the stated capacity and investment limits."
    )
    with st.expander("Inputs and outputs — exactly what is required"):
        st.markdown(
            "**You provide:** initiative name, accountable owner and sponsor, "
            "seven criterion ratings, evidence confidence, control status, "
            "capacity requirement, investment and benefit estimates. "
            "You can also record your current proposed selection.\n\n"
            "**The service returns:** initiative-level recommendations, "
            "a constrained shortlist, a lower-commitment alternative, "
            "resource trade-offs, next-proof requirements and an executive PDF.\n\n"
            "**Decision boundary:** the report is an advisory recommendation. "
            "It never grants funding, legal clearance or deployment authority."
        )
    st.markdown("#### How it works")
    st.write(
        "**1. Open an approved analysis** → **2. Enter and review initiatives** "
        "→ **3. Read the executive recommendation** → **4. Record the formal decision** "
        "→ **5. Export the executive report**."
    )
    st.caption(
        "Each additional analysis is requested separately and approved individually. "
        "Previous assessment records remain private and available to their owners."
    )
    st.page_link(
        "https://jairribeiro.com/?page=advisory-scorecard",
        label="Read the full Scorecard service description",
    )


def _analyses_home(uid: str, analyses: list[dict]) -> None:
    _title(
        "PRIVATE EXECUTIVE ADVISORY",
        "Your portfolio analyses",
        "Each analysis represents a separate investment decision. Open one to see its "
        "scope, evidence, recommendation, next action and executive report."
    )
    st.html(
        '<div class="scx-brief"><div class="scx-subtitle">What this service gives you</div>'
        '<strong>A defendable portfolio choice</strong> - what to advance, test, hold or stop; '
        'initiative-level next actions and owners; resource trade-offs; and an '
        'executive decision brief you can bring to a management review.</div>'
    )
    c1,c2,c3=st.columns(3)
    c1.metric("Approved analyses",len(analyses))
    c2.metric("With recommendations",sum(
        a["status"]=="Recommendation available" for a in analyses))
    c3.metric("Requiring inputs",sum(
        a["status"] in ("Not started","Assessment incomplete") for a in analyses))
    st.markdown("#### Select an analysis")
    for a in analyses:
        wid=str(a["ws"]["id"])
        with st.container(border=True):
            st.markdown(f"**{a['title']}**")
            st.caption(
                f"Analysis {a['rank']} · {a['status']} · "
                f"Last updated {a['updated_at'] or 'Not recorded'}"
            )
            st.write(a["context"])
            st.markdown("**Intended outcome**")
            st.write(a["outcome"])
            col1,col2,col3=st.columns(3)
            col1.metric("Initiatives",a["count"])
            col2.metric("Assessed",a["reviewed"])
            col3.metric("Recommended",a["report"]["recommended"]["count"])
            st.caption("**Next:** "+a["next_step"])
            st.button(
                "Open this analysis",type="primary",
                key="scx_open_"+wid,
                on_click=_go,args=(
                    uid,"Open analysis",wid,
                    "Initiatives & evidence" if not a["count"] else "Executive decision",
                ),
            )
    st.button(
        "Request another analysis",key="scx_home_request_"+uid,
        on_click=_go,args=(uid,"Request new analysis"),
    )


def _action_item(item: dict, n: int, uid: str, wid: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{n:02d} · {item['name']}**")
        st.caption(
            f"{item['recommendation']} · "
            f"Priority score {item['score'] if item['score'] is not None else 'Not assessed'}/100"
        )
        st.markdown("**Why this recommendation**")
        st.write(item.get("rationale") or "Assessment rationale unavailable.")
        st.markdown("**Required next step**")
        st.write(item.get("next_action") or "Confirm the next evidence requirement.")
        st.caption(
            "Accountable business owner: "+(item.get("owner") or "Not recorded")
            +" · Control: "+(item.get("gate") or "Not checked")
        )
        def go_to_edit():
            _go(uid,"Open analysis",wid,"Initiatives & evidence")
            st.session_state["scorecard_selected_"+wid]=str(item["id"])
        st.button(
            "Review initiative inputs",key="scx_edit_"+wid+"_"+str(item["id"]),
            on_click=go_to_edit,
        )


def _decision(a: dict, uid: str, token: str,
              feedback_rows: list[dict] | None) -> None:
    report=a["report"]
    summary=report["recommended"]
    _title(
        "01 · THE EXECUTIVE DECISION",
        "Recommended course of action",
        "The proposed choice, the resources it requires and the decisions "
        "leadership must make next."
    )
    if not report["rows"]:
        st.info("No initiatives entered. Open Initiatives & evidence to begin.")
        return
    verdict=report["verdict"].split(" Do not treat")[0].strip()
    st.html(
        '<div class="scx-brief"><div class="scx-subtitle">Decision proposed'
        '</div><strong>'+__import__("html").escape(verdict)+'</strong></div>'
    )
    c1,c2,c3=st.columns(3)
    c1.metric("Advance to business case",report["advanced_count"])
    c2.metric("Conduct scoped tests",report["test_count"])
    c3.metric("Hold / other",len(report["rows"])-summary["count"])
    c4,c5=st.columns(2)
    c4.metric("Planning investment",_fmt(summary["investment_sek"]))
    c5.metric("Capacity required",f'{summary["fte_months"]:.1f} FTE-months')
    st.caption(
        "Proposed within stated limits: "+
        ("Yes" if summary["fits"] else "No")
        +f" · Remaining budget: {_fmt(summary['budget_headroom'])}."
    )
    st.markdown("#### What executives should do next")
    advances=report["categories"].get("Advance to business case",[])
    tests=report["categories"].get("Time-boxed test",[])
    holds=report["categories"].get("Hold - control review",[])
    blocked=report["categories"].get("Stop / redesign",[])
    for step,heading,detail in (
        ("01","Commission the priority business cases",
         f"{len(advances)} candidate(s). Validate benefit baselines, accountable sponsors and investment cases."
         if advances else "No candidate qualifies; complete the evidence and resource assumptions."),
        ("02","Define the bounded proof",
         f"{len(tests)} test candidate(s): define measurable success, boundaries and a go/no-go date."
         if tests else "No test was selected within the configured constraints."),
        ("03","Resolve controls before commitment",
         f"{len(holds)} control review(s) and {len(blocked)} blocked initiative(s) remain outside the proposal."
         if holds or blocked else "Confirm the remaining formal approval conditions."),
    ):
        with st.container(border=True):
            st.markdown(f"**{step} · {heading}**")
            st.write(detail)
    if not summary["count"]:
        st.warning(
            "The current portfolio has no qualifying, feasible selection. "
            "Resolve the evidence, control or planning conditions before proceeding."
        )
    st.html(
        '<div class="scx-brief"><strong>Decision requested</strong><div>'
        "Confirm the proposed shortlist for further business-case and test work. "
        "Secure control, sponsor and resource sign-off separately before any spending "
        "or deployment authorization.</div></div>"
    )
    col1,col2=st.columns(2)
    with col1:
        st.button(
            "Examine initiative actions",key="scx_dec_actions_"+str(a["ws"]["id"]),
            on_click=_go,args=(uid,"Open analysis",str(a["ws"]["id"]),"Priority actions"),
            type="primary",use_container_width=True,
        )
    with col2:
        st.button(
            "Open executive report",key="scx_dec_report_"+str(a["ws"]["id"]),
            on_click=_go,args=(uid,"Open analysis",str(a["ws"]["id"]),"Executive report"),
            use_container_width=True,
        )
    if feedback_rows is not None and token and uid:
        from page_advisory_service_feedback import SCORECARD_SERVICE,render_optional_feedback
        render_optional_feedback(
            token,uid,SCORECARD_SERVICE,"executive_recommendation",
            request_id=str(a["ws"]["request_id"]),
            scorecard_id=str(a["ws"]["id"]),
            feedback_rows=feedback_rows,
        )


def _actions(a: dict, uid: str) -> None:
    _title("02 · RECOMMENDATIONS","Actions by initiative",
           "Each recommendation explains the reasoning, who owns it and "
           "what evidence is required to progress.")
    report=a["report"]
    rows=report["rows"]
    if not rows:
        st.info("Start by adding initiatives in the assessment area.")
        return
    groups={
        "Advance & test":[r for r in rows if r["included_in_proposal"]],
        "Hold & redesign":[r for r in rows if r["recommendation"] in (
            "Hold - control review","Stop / redesign","Complete assessment","Validate evidence"
        )],
        "Defer & queue":[r for r in rows if r["recommendation"] in (
            "Defer - constrained","Queue for a test","Defer / stop"
        )],
    }
    key="scx_action_group_"+str(a["ws"]["id"])
    choice=st.segmented_control(
        "Recommendation group",options=tuple(groups),
        default="Advance & test",key=key
    )
    showing=sorted(
        groups.get(choice or "Advance & test",[]),
        key=lambda r:(not r["included_in_proposal"],-(r["score"] or 0),r["name"]),
    )
    st.caption(f"{len(showing)} initiative(s) in this group.")
    if not showing:
        st.info("There are no initiatives requiring this type of action.")
    for i,r in enumerate(showing,1):
        _action_item(r,i,uid,str(a["ws"]["id"]))
    st.caption(
        "A high score never overrides an unresolved control gate. "
        "These directions are for leadership review, not automatic approval."
    )


def _options(a: dict) -> None:
    _title(
        "03 · PORTFOLIO CHOICES","Options and trade-offs",
        "Compare the recommended portfolio against a lower-commitment "
        "option and your currently selected initiatives."
    )
    report=a["report"]
    if not report["rows"]:
        st.info("Add initiative estimates to compare portfolio options.")
        return
    for name,subtitle,key in (
        ("Recommended portfolio","Resource-constrained selection","recommended"),
        ("Lower-commitment option","Business cases only; no test allocation","conservative"),
        ("Your current selection","The initiatives you manually selected","current_selection"),
    ):
        item=report[key]
        with st.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(subtitle)
            b1,b2,b3=st.columns(3)
            b1.metric("Initiatives",item["count"])
            b2.metric("Capacity",f'{item["fte_months"]:.1f} FTE-mo')
            b3.metric("One-time investment",_fmt(item["investment_sek"]))
            st.caption(
                ("Within planning limits" if item["fits"] else "Exceeds planning limits")
                +f" · Budget remaining: {_fmt(item['budget_headroom'])}"
                +f" · Capacity remaining: {item['fte_headroom']:.1f} FTE-months."
            )
    changes=report.get("changes") or {}
    if changes.get("removed"):
        st.warning(
            "Remove or hold from your current proposal: "
            +"; ".join(changes["removed"])
        )
    if changes.get("added"):
        st.info(
            "Add to the proposed shortlist: "+"; ".join(changes["added"])
        )
    with st.expander("How the alternatives are selected"):
        st.write(
            "The engine compares weighted priority, minimum evidence and mandatory "
            "control gates. It first selects eligible business cases within budget "
            "and capacity, then considers a limited number of tests. "
            "The lower-commitment option excludes those tests. "
            "Your current proposal comes from the checkboxes you selected."
        )
        st.caption("Selection method: "+report["selection_method"])
        for caveat in report["caveats"]:
            st.write("• "+str(caveat))


def _report(a: dict, token: str, uid: str,
            feedback_rows: list[dict] | None) -> None:
    _title("06 · EXECUTIVE DELIVERABLE","Decision brief and record",
           "Use the current assessment to prepare a management review, "
           "then record the actual leadership decision separately.")
    report=a["report"]
    wid=str(a["ws"]["id"])
    if not report["rows"]:
        st.info("The executive report will be available after initiatives are entered.")
        return
    st.markdown("#### Included in the downloadable brief")
    st.markdown(
        "1. **Executive summary:** proposed decision and resource envelope.\n"
        "2. **Priority actions:** what should advance or be tested and why.\n"
        "3. **Holds and exceptions:** what must be resolved before reconsideration.\n"
        "4. **Alternatives and authorization:** capacity trade-offs, controls and sign-off conditions."
    )
    c1,c2,c3=st.columns(3)
    c1.metric("Initiatives reviewed",len(report["rows"]))
    c2.metric("Proposed selection",report["recommended"]["count"])
    c3.metric("Assessment revision",a["revision"])
    st.caption(
        f"{REPORT_EDITION} · Generated from the current saved revision. "
        "The report does not assert that leadership approved the investment."
    )
    try:
        content=build_executive_pdf(report)
    except Exception:
        st.error("The report could not be generated. Your assessment is unchanged.")
        content=None
    download_key="scorecard_report_download_clicked_"+wid
    if content is not None:
        st.download_button(
            "Download executive decision brief · PDF",
            data=content,
            file_name="AI_Portfolio_Executive_Decision_Brief_"
                +REPORT_VERSION+"_Revision_"+str(a["revision"])+".pdf",
            mime="application/pdf",
            type="primary",
            on_click=lambda key=download_key:st.session_state.__setitem__(key,True),
        )
    st.divider()
    st.markdown("#### Analysis record")
    st.write("**Scope:** "+a["context"])
    st.write("**Requested outcome:** "+a["outcome"])
    st.caption(
        f"Approved {a['approved_at'] or 'date not recorded'} · "
        f"Last saved {a['updated_at'] or 'not recorded'} · Revision {a['revision']}."
    )
    st.caption(
        "Revision identifies the current saved snapshot, not a browsable archive "
        "of prior versions. Formal outcomes are recorded in Decision record."
    )
    if feedback_rows is not None and token and uid and st.session_state.get(download_key):
        from page_advisory_service_feedback import SCORECARD_SERVICE,render_optional_feedback
        render_optional_feedback(
            token,uid,SCORECARD_SERVICE,"report_download",
            request_id=str(a["ws"]["request_id"]),scorecard_id=wid,
            feedback_rows=feedback_rows,
        )


def _activity_history(a: dict, token: str) -> None:
    """Actual approval/save events and formal decisions, never invented versions."""
    _title(
        "07 · ANALYSIS HISTORY",
        "Activity and recorded decisions",
        "See when this assessment was approved and saved, and which "
        "formal business decisions have been recorded."
    )
    wid=str(a["ws"]["id"])
    left,right,third=st.columns(3)
    left.metric("Approved on",a["approved_at"] or "Not recorded")
    right.metric("Current revision",a["revision"])
    third.metric("Initiatives",a["count"])
    st.markdown("**Purpose of this assessment**")
    st.write(a["context"])
    st.markdown("**Expected deliverable**")
    st.write(a["outcome"])

    st.markdown("#### Workspace activity")
    try:
        logs=_request_json(
            "GET",_rest_url(
                "portfolio_advisory_scorecard_audit?"
                "select=action,revision,created_at"
                "&scorecard_id=eq."+quote(wid,safe="")
                +"&order=created_at.desc&limit=100"
            ),
            token=token,timeout=12,
        )
        if not isinstance(logs,list):
            raise RuntimeError("Activity history response unavailable")
    except (RuntimeError,TimeoutError,ValueError,KeyError):
        logs=None
    if logs is None:
        st.caption(
            "Saved activity could not be retrieved. Your assessment and "
            "current report remain available."
        )
    elif logs:
        for event in logs[:25]:
            action=str(event.get("action") or "").lower()
            label={
                "approve":"Access approved","save":"Assessment saved",
                "revoke":"Access revoked",
            }.get(action,"Workspace event")
            revision=event.get("revision")
            timestamp=str(event.get("created_at") or "")[:16].replace("T"," ")
            st.caption(
                f"{timestamp} · {label}"
                +(f" · Revision {revision}" if revision is not None else "")
            )
        if len(logs)>25:
            st.caption(f"Showing 25 of {len(logs)} recent activity events.")
    else:
        st.caption("No activity events are recorded for this workspace.")

    st.divider()
    st.markdown("#### Recorded management decisions")
    decided=[
        row for row in a["data"]["initiatives"]
        if str(row.get("decision") or "Unreviewed")!="Unreviewed"
    ]
    if not decided:
        st.info(
            "No final management decisions have been recorded. "
            "Review the proposed actions, then use Decision record to document "
            "the outcome, conditions and next review."
        )
    else:
        for item in decided:
            with st.container(border=True):
                st.markdown(
                    "**"+str(item.get("name") or "Unnamed initiative")+"**"
                    " · "+str(item.get("decision") or "Not recorded")
                )
                st.write(str(item.get("decision_rationale") or "No rationale entered."))
                st.caption(
                    "Decision owner: "+str(item.get("decision_owner") or "Not assigned")
                    +" · Next review: "+str(item.get("next_review") or "Not set")
                )
    st.caption(
        "This is an activity log and current decision register, not a snapshot "
        "archive. Previous versions cannot be restored from this page."
    )


def _analysis(uid: str, a: dict, token: str,
              feedback_rows: list[dict] | None) -> None:
    wid=str(a["ws"]["id"])
    st.button(
        "← All analyses",key="scx_back_"+wid,
        on_click=_go,args=(uid,"My analyses"),
    )
    _title(
        f"ANALYSIS {a['rank']} · {a['status']}",
        a["title"],
        a["context"],
    )
    st.markdown("**What this analysis is intended to deliver**")
    st.write(a["outcome"])
    with st.container(border=True):
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Initiatives",a["count"])
        m2.metric("Assessed",a["reviewed"])
        m3.metric("For leadership review",a["report"]["recommended"]["count"])
        m4.metric("Revision",a["revision"])
        st.caption("**Next action:** "+a["next_step"])
    section_key="scx_section_"+wid
    if st.session_state.get(section_key) not in SECTIONS:
        st.session_state[section_key]=(
            "Initiatives & evidence" if not a["count"] else "Executive decision"
        )
    section=st.selectbox(
        "Open analysis section",options=SECTIONS,
        key=section_key,
        help="Only the selected section is shown. Your inputs are saved separately."
    )
    st.divider()
    if section=="Executive decision":
        _decision(a,uid,token,feedback_rows)
    elif section=="Priority actions":
        _actions(a,uid)
    elif section=="Portfolio options":
        _options(a)
    elif section=="Initiatives & evidence":
        _title("04 · ASSESSMENT INPUTS","Initiatives and supporting evidence",
               "Add an initiative, then provide its accountable owner, "
               "criterion ratings, control status, resource estimates and next proof.")
        _form_initiative(
            token,a["ws"],a["data"],
            uid=uid if feedback_rows is not None else "",
            feedback_rows=feedback_rows,
        )
    elif section=="Decision record":
        _title("05 · MANAGEMENT DECISION","Record the actual leadership judgment",
               "The Scorecard proposes actions. Use this section to record "
               "the real decision, responsible owner, conditions and next review.")
        _decision_record(token,a["ws"],a["data"])
    elif section=="Executive report":
        _report(a,token,uid,feedback_rows)
    elif section=="Activity & history":
        _activity_history(a,token)
    else:
        _title("ASSESSMENT POLICY","Criteria and planning boundaries",
               "Review the seven evaluation criteria and set the capacity, "
               "investment and test limits used to form the recommendation.")
        with st.expander("What each criterion means"):
            for name,detail in CRITERIA:
                st.write("**"+name+"** — "+detail)
        _policy(token,a["ws"],a["data"])


def render_scorecard_experience(
    token: str,uid: str,workspaces: list[dict],
    feedback_rows: list[dict] | None = None,
) -> None:
    """A single focused view, never a dashboard and six tabs stacked together."""
    st.html(CSS)
    workspaces=sorted(workspaces,key=lambda row:(
        str(row.get("approved_at") or ""),str(row.get("id") or "")
    ),reverse=True)
    ids=[str(x["id"]) for x in workspaces]
    seen_key="scorecard_seen_workspace_ids_"+uid
    selected_key="scx_selected_"+uid
    previous=set(st.session_state.get(seen_key) or [])
    fresh=[wid for wid in ids if wid not in previous]
    if fresh or st.session_state.get(selected_key) not in ids:
        st.session_state[selected_key]=fresh[0] if fresh else ids[0]
    if any(
        str(w.get("id")) == st.session_state.get(selected_key)
        and w.get("analysis_request_id")
        and not (w.get("payload") or {}).get("initiatives")
        for w in workspaces
    ) and (fresh or "scx_nav_"+uid not in st.session_state):
        # On returning after approval, open the new, empty Scorecard directly.
        st.session_state["scx_nav_"+uid]="Open analysis"
    st.session_state[seen_key]=ids

    try:
        request_rows=read_analysis_requests(token,uid)
    except (RuntimeError,ValueError,TimeoutError,KeyError):
        request_rows=[]
        st.caption("Request details could not be refreshed. Existing assessments remain available.")
    by_request={str(r["id"]):r for r in request_rows if r.get("id")}
    analyses=[
        _analysis_info(w,by_request,i)
        for i,w in enumerate(reversed(workspaces),1)
    ]
    analyses.reverse()
    nav_key="scx_nav_"+uid
    nav=st.segmented_control(
        "Scorecard service",options=NAV,
        default="My analyses",key=nav_key
    )
    if nav=="How the service works":
        _service_guide()
        st.button(
            "View my approved analyses",key="scx_guide_back_"+uid,
            type="primary",on_click=_go,args=(uid,"My analyses"),
        )
    elif nav=="Request new analysis":
        _title(
            "INDIVIDUAL REVIEW · PRO BONO",
            "Request another portfolio decision",
            "A new analysis is available only after individual approval. "
            "Approval creates an empty, separate workspace."
        )
        st.write(
            "Describe the management decision, why it matters and what you need "
            "from the assessment. You will receive an individual approval decision."
        )
        anchor=str(analyses[0]["ws"]["id"])
        render_new_analysis_request(token,uid,anchor)
    elif nav=="Open analysis":
        selected=next(
            (a for a in analyses if str(a["ws"]["id"])==st.session_state.get(selected_key)),
            analyses[0],
        )
        _analysis(uid,selected,token,feedback_rows)
    else:
        _analyses_home(uid,analyses)
