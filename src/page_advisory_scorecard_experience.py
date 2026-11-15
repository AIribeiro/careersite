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

SCORECARD_EXPERIENCE_VERSION = "executive_workspace_v3_20261115"

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
.scx-portfolio-board {margin:.8rem 0 .75rem}
.scx-portfolio-top {display:flex;justify-content:space-between;align-items:baseline;gap:.6rem;flex-wrap:wrap;margin-bottom:.6rem}
.scx-portfolio-top h3 {font-size:1.12rem;color:#193147;margin:0;font-weight:700}
.scx-portfolio-total {font-size:.81rem;color:#536c7b;font-weight:600}
.scx-portfolio-counts {display:flex;gap:.4rem 1rem;flex-wrap:wrap;color:#556978;font-size:.82rem;margin-bottom:.7rem}
.scx-portfolio-counts strong {color:#193147}
.scx-portfolio-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.52rem}
.scx-portfolio-item {border:1px solid #dce3e7;border-left:3px solid #a4b5c0;border-radius:7px;padding:.62rem .75rem;background:#fff;min-width:0;display:flex;justify-content:space-between;gap:.6rem;align-items:center}
.scx-portfolio-item--advance {border-left-color:#28777b}
.scx-portfolio-item--test {border-left-color:#b48150}
.scx-portfolio-item--hold {border-left-color:#9a7e58}
.scx-portfolio-item--stop {border-left-color:#a66062}
.scx-portfolio-copy {min-width:0;flex:1}
.scx-portfolio-name {font-size:.86rem;line-height:1.35;color:#182f41;font-weight:650;overflow-wrap:anywhere}
.scx-portfolio-owner {font-size:.72rem;line-height:1.3;color:#697984;margin-top:.16rem;overflow-wrap:anywhere}
.scx-portfolio-result {text-align:right;min-width:98px;max-width:38%}
.scx-portfolio-score {font-size:.87rem;line-height:1.25;font-weight:700;color:#1b3448}
.scx-portfolio-route {font-size:.72rem;line-height:1.3;color:#576d7b;margin-top:.2rem;overflow-wrap:anywhere}
.scx-portfolio-foot {font-size:.75rem;line-height:1.4;color:#637485;margin-top:.6rem}
.scx-compact-kpis {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;border:1px solid #dae2e6;border-radius:8px;overflow:hidden;margin:.55rem 0 .45rem;background:#dae2e6}
.scx-compact-kpi {padding:.48rem .65rem;background:#f8fafb;min-width:0}
.scx-compact-kpi-label {font-size:.72rem;color:#617282;line-height:1.3}
.scx-compact-kpi-value {font-size:1.13rem;color:#17344b;font-weight:720;line-height:1.35;margin-top:.1rem;font-variant-numeric:tabular-nums}
@media(max-width:700px) {
 .scx-portfolio-grid {grid-template-columns:1fr}
 .scx-compact-kpis {grid-template-columns:repeat(2,minmax(0,1fr))}
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
        st.session_state["scx_primary_"+analysis_id]=(
            "verdict" if section=="Executive decision" else
            "actions" if section=="Priority actions" else "evidence"
        )
        if section not in ("Executive decision","Priority actions"):
            st.session_state["scx_detail_"+analysis_id]=section


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


def _service_guide(approved: bool = False, saved_count: int = 0) -> None:
    """Same service introduction and three-output visual hierarchy as Rollout."""
    from page_advisory_shared_ui import service_overview
    service_overview(
        hero="From competing AI opportunities to a defensible portfolio choice.",
        description=(
            "Assess competing AI initiatives against value, delivery capacity, "
            "evidence and governance. Make the trade-offs visible before "
            "leadership commits scarce people or investment."
        ),
        access="Individually approved" if approved else "Approval required · Pro bono",
        assessment_format="One portfolio per approved analysis",
        saved_count=saved_count,
        outputs=(
            ("The verdict", "What should advance, test or stop",
             "An executive portfolio recommendation that respects resource and risk limits."),
            ("The priorities", "Actions for each decision",
             "Named accountability functions, evidence gaps, resource trade-offs and release conditions."),
            ("The report", "A private portfolio decision brief",
             "The reasoning, alternatives and a downloadable executive PDF for leadership review."),
        ),
        steps=(
            ("Request your assessment",
             "Describe the portfolio decision you need. Individual approval creates a new workspace."),
            ("Compare the opportunities",
             "Record initiative owners, evidence, seven criteria, risk gates and capacity needs."),
            ("Review the recommendation",
             "Evaluate alternatives, document the formal decision and download the executive brief."),
        ),
        boundary=(
            "Free pro-bono access is individually approved. A Scorecard "
            "recommends investment priorities but does not authorize funding, "
            "legal compliance or production deployment. Previous assessment records remain private."
        ),
    )
    with st.expander("Exactly what inputs and outputs are included"):
        st.markdown(
            "**You provide:** each initiative, business sponsor and owner, "
            "seven scored decision criteria, supporting evidence, control readiness "
            "and capacity/investment estimates.\n\n"
            "**You receive:** a constrained executive shortlist, initiative-level "
            "actions and justifications, comparison scenarios and a downloadable brief.\n\n"
            "**Important:** decisions remain with your accountable leadership."
        )
    st.page_link(
        "https://jairribeiro.com/?page=advisory-scorecard",
        label="Read the complete Scorecard service description",
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
    query=st.text_input(
        "Find an analysis",placeholder="Search decision title or business context",
        key="scx_history_search_"+uid,
    )
    statuses=tuple(sorted({a["status"] for a in analyses}))
    status_filter=st.selectbox(
        "Assessment status",("All statuses",)+statuses,
        key="scx_history_status_"+uid,
    )
    visible=[
        a for a in analyses
        if query.strip().casefold() in (
            a["title"]+" "+a["context"]+" "+a["outcome"]
        ).casefold()
        and (status_filter=="All statuses" or a["status"]==status_filter)
    ]
    st.caption(f"{len(visible)} of {len(analyses)} approved analyses match.")
    if not visible:
        st.info("No analyses match the current filters.")
    page_size=5
    page_count=(len(visible)+page_size-1)//page_size
    page=(st.selectbox(
        "History page",list(range(1,page_count+1)),
        format_func=lambda n:f"Page {n} of {page_count}",
        key="scx_history_page_"+uid,
    ) if page_count>1 else 1)
    for a in visible[(page-1)*page_size:page*page_size]:
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
        # A saved, nonempty portfolio with a generated executive report
        # qualifies as a first completed assessment. Viewing an empty
        # workspace or requesting approval never counts as completion.
        if st.session_state.get("scorecard_onboarding_first_report_logged") != uid:
            from site_onboarding_measurement import record_first_value
            if record_first_value(token, uid, "advisory", "first_assessment"):
                st.session_state["scorecard_onboarding_first_report_logged"] = uid
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


def _portfolio_snapshot(a: dict, uid: str) -> None:
    """Always-visible initiative register before the decision navigation.

    Uses only current approved workspace data; recommendations are advisory
    and each item can be opened through the native selection control below.
    """
    import html

    wid=str(a["ws"]["id"])
    rows=list(a["report"].get("rows") or [])
    counts={
        "business_cases":sum(r.get("recommendation")=="Advance to business case" for r in rows),
        "tests":sum(r.get("recommendation")=="Time-boxed test" for r in rows),
        "other":sum(r.get("recommendation") not in (
            "Advance to business case","Time-boxed test") for r in rows),
    }
    kpis=[
        ("Initiatives",a["count"]),("Assessed",a["reviewed"]),
        ("For review",a["report"]["recommended"]["count"]),
        ("Revision",a["revision"]),
    ]
    st.html(
        '<div class="scx-compact-kpis" aria-label="Portfolio assessment overview">'
        +''.join(
            '<div class="scx-compact-kpi"><div class="scx-compact-kpi-label">'
            +html.escape(str(label))+'</div><div class="scx-compact-kpi-value">'
            +html.escape(str(value))+'</div></div>'
            for label,value in kpis
        )+'</div>'
    )
    st.html(
        '<div class="scx-portfolio-board">'
        '<div class="scx-portfolio-top"><h3>Initiatives in this portfolio</h3>'
        '<span class="scx-portfolio-total">'+str(len(rows))+' registered</span></div>'
        '<div class="scx-portfolio-counts">'
        '<span><strong>'+str(counts["business_cases"])+'</strong> business-case candidates</span>'
        '<span><strong>'+str(counts["tests"])+'</strong> scoped tests</span>'
        '<span><strong>'+str(counts["other"])+'</strong> held, deferred or requiring review</span>'
        '</div></div>'
    )
    if not rows:
        st.info(
            "This analysis has no initiatives yet. Add the first one to begin "
            "the assessment and build your executive recommendation."
        )
        st.button(
            "Add first initiative",key="scx_port_first_"+wid,type="primary",
            on_click=_go,args=(uid,"Open analysis",wid,"Initiatives & evidence"),
        )
        return
    priority={
        "Advance to business case":0,"Time-boxed test":1,
        "Hold - control review":2,"Stop / redesign":3,
        "Validate evidence":4,"Complete assessment":5,
        "Defer - constrained":6,"Queue for a test":7,
        "Defer / stop":8,
    }
    ranked=sorted(
        rows,key=lambda row:(
            priority.get(str(row.get("recommendation") or ""),9),
            -(row.get("score") or 0),
            str(row.get("name") or "").casefold(),
        )
    )
    selected_key="scx_portfolio_selected_"+wid
    valid_ids={str(r["id"]) for r in ranked}
    if st.session_state.get(selected_key) not in valid_ids:
        st.session_state[selected_key]=str(ranked[0]["id"])
    page_limit=10
    full_key="scx_portfolio_full_"+wid
    show_all=bool(st.session_state.get(full_key,False))
    visible=ranked if show_all else ranked[:page_limit]
    def status_class(status: str) -> str:
        if status=="Advance to business case":return "advance"
        if status=="Time-boxed test":return "test"
        if status=="Hold - control review":return "hold"
        if status=="Stop / redesign":return "stop"
        return "other"
    cards=[]
    for row in visible:
        status=str(row.get("recommendation") or "Assessment needed")
        name=html.escape(str(row.get("name") or "Unnamed initiative"))
        owner=html.escape(str(row.get("owner") or "Owner not assigned"))
        score=row.get("score")
        score_label=(str(score)+"/100") if score is not None else "Not scored"
        cards.append(
            '<div class="scx-portfolio-item scx-portfolio-item--'
            +status_class(status)+'">'
            '<div class="scx-portfolio-copy"><div class="scx-portfolio-name">'
            +name+'</div><div class="scx-portfolio-owner">'
            +owner+'</div></div><div class="scx-portfolio-result">'
            '<div class="scx-portfolio-score">'+html.escape(score_label)+'</div>'
            '<div class="scx-portfolio-route">'+html.escape(status)+'</div></div></div>'
        )
    st.html(
        '<div class="scx-portfolio-grid" role="list" aria-label="Current initiatives and recommendations">'
        +''.join(cards)+'</div>'
        '<div class="scx-portfolio-foot">These are preliminary portfolio recommendations, '
        'not funding or deployment approvals. Select an initiative to review its full evidence.</div>'
    )
    if len(ranked)>page_limit:
        st.toggle(
            f"Show all {len(ranked)} initiatives",
            key=full_key,
        )
    choice,button=st.columns([3,1],vertical_alignment="bottom")
    with choice:
        st.selectbox(
            "Review a specific initiative",
            [str(r["id"]) for r in ranked],
            format_func=lambda value:next(
                (str(r.get("name") or "Unnamed initiative")
                 for r in ranked if str(r["id"])==value),value
            ),
            key=selected_key,
        )
    def open_selected() -> None:
        st.session_state["scorecard_selected_"+wid]=st.session_state[selected_key]
        _go(uid,"Open analysis",wid,"Initiatives & evidence")
    with button:
        st.button(
            "Open initiative",key="scx_portfolio_open_"+wid,
            type="primary",use_container_width=True,on_click=open_selected,
        )


def _analysis(uid: str, a: dict, token: str,
              feedback_rows: list[dict] | None) -> None:
    wid=str(a["ws"]["id"])
    st.button(
        "← All analyses",key="scx_back_"+wid,
        on_click=_go,args=(uid,"My analyses"),
    )
    from page_advisory_shared_ui import case_header
    case_header(
        title=a["title"],
        date=a["updated_at"][:10],
        context=a["context"],
        status=a["status"]+" · "+str(a["count"])+
               " initiatives · revision "+str(a["revision"]),
    )
    _portfolio_snapshot(a,uid)
    with st.expander("Purpose of this assessment and intended deliverable"):
        st.markdown("**What this analysis is intended to deliver**")
        st.write(a["outcome"])
        st.caption(
            "This analysis compares initiatives within stated resource limits. "
            "Recommendations are not approvals to spend or deploy."
        )
    st.caption("**Next action:** "+a["next_step"])
    # Rollout-standard three-way decision navigation. Portfolio-only controls
    # live under Evidence & report, rather than creating eight top-level tabs.
    section_key="scx_section_"+wid
    if st.session_state.get(section_key) not in SECTIONS:
        st.session_state[section_key]=(
            "Initiatives & evidence" if not a["count"] else "Executive decision"
        )
    primary_key="scx_primary_"+wid
    detail_key="scx_detail_"+wid
    detail_sections=(
        "Portfolio options","Initiatives & evidence","Decision record",
        "Executive report","Activity & history","Assessment criteria",
    )
    def select_main() -> None:
        current=st.session_state.get(primary_key)
        if current=="verdict":
            st.session_state[section_key]="Executive decision"
        elif current=="actions":
            st.session_state[section_key]="Priority actions"
        elif current=="evidence":
            detail=st.session_state.get(detail_key)
            st.session_state[section_key]=(
                detail if detail in detail_sections else "Initiatives & evidence"
            )
    def select_detail() -> None:
        detail=st.session_state.get(detail_key)
        if detail in detail_sections:
            st.session_state[section_key]=detail
    if st.session_state.get(primary_key) not in ("verdict","actions","evidence"):
        selected=st.session_state[section_key]
        st.session_state[primary_key]=(
            "verdict" if selected=="Executive decision" else
            "actions" if selected=="Priority actions" else "evidence"
        )
    st.pills(
        "Decision brief sections", ("verdict","actions","evidence"),
        format_func=lambda x: {
            "verdict":"Verdict & portfolio",
            "actions":"Executive actions",
            "evidence":"Evidence & report",
        }[x],
        key=primary_key, selection_mode="single", required=True,
        on_change=select_main, label_visibility="collapsed",
        wrap=False, width="stretch",
    )
    if st.session_state.get(primary_key)=="evidence":
        if st.session_state.get(detail_key) not in detail_sections:
            previous=st.session_state.get(section_key)
            st.session_state[detail_key]=(
                previous if previous in detail_sections else "Initiatives & evidence"
            )
        st.pills(
            "Portfolio review tools",detail_sections,
            key=detail_key, selection_mode="single",required=True,
            on_change=select_detail,label_visibility="collapsed",
            wrap=False,width="stretch",
        )
        section=st.session_state[detail_key]
    else:
        section=(
            "Executive decision" if st.session_state[primary_key]=="verdict"
            else "Priority actions"
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
    from page_rollout_workspace_ui import WORKSPACE_CSS
    st.html(WORKSPACE_CSS + CSS)
    st.markdown("### AI Portfolio Prioritization Scorecard")
    st.caption("Private executive decision service · A constrained portfolio review")
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
    NAV_LABELS = {
        "How the service works": "About this service",
        "Request new analysis": "Request assessment",
        "Open analysis": "Decision brief",
        "My analyses": "My history",
    }
    visible_order = (
        "How the service works", "Request new analysis",
        "Open analysis", "My analyses",
    )
    nav=st.pills(
        "Scorecard service sections", options=visible_order,
        format_func=lambda option: NAV_LABELS[option],
        default="How the service works", key=nav_key,
        selection_mode="single", required=True,
        label_visibility="collapsed", wrap=False, width="stretch",
    )
    if nav=="How the service works":
        _service_guide(approved=True,saved_count=len(analyses))
        if analyses:
            latest=analyses[0]
            latest_id=str(latest["ws"]["id"])
            st.markdown("### Your latest portfolio decision")
            with st.container(border=True):
                st.caption((latest["updated_at"] or "Recent assessment") +
                           " · " + latest["status"])
                st.markdown("#### " + latest["title"])
                st.write(latest["context"])
                st.caption("**Next action:** " + latest["next_step"])
                left,right=st.columns(2)
                with left:
                    st.button(
                        "Open executive decision brief",type="primary",
                        key="scx_guide_latest_"+uid,use_container_width=True,
                        on_click=_go,args=(
                            uid,"Open analysis",latest_id,
                            "Executive decision" if latest["count"] else "Initiatives & evidence",
                        ),
                    )
                with right:
                    st.button(
                        "Browse decision history",key="scx_guide_history_"+uid,
                        use_container_width=True,on_click=_go,args=(uid,"My analyses"),
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
