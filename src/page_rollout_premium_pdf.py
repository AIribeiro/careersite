"""Two-page, executive-grade PDF for the live Enterprise AI Rollout Advisor.

The underlying verdict is supplied by the existing deterministic assessment.
All actions, conditions and supporting figures are derived from submitted answers.
Timings and responsible roles are proposals, not customer commitments.
"""
from __future__ import annotations

from datetime import date
from fpdf import FPDF

NAVY = (15, 34, 53)
INK = (29, 44, 59)
MUTED = (91, 108, 124)
COPPER = (174, 117, 78)
PAPER = (251, 249, 246)
PALE = (244, 240, 234)
RULE = (222, 226, 228)
AMBER = (158, 96, 48)
GREEN = (39, 106, 84)
ALERT = (157, 67, 46)
VERSION = "2.0"

# Specific interventions for each of the eighteen assessment conditions.
# owner and timing are always recommendations, never asserted commitments.
CATALOG = {
 "oversight": ("Formalize human oversight and intervention authority",
  "Service Operations / Risk & Safety", "10 business days",
  "Name who may override outputs, investigate incidents, suspend usage and approve restart.",
  "Signed RACI, escalation pathway and completed response exercise.",
  "Intervention authority approved and demonstrated."),
 "regulation": ("Confirm regulatory and liability readiness",
  "Legal & Compliance", "20 business days",
  "Assess applicable AI, privacy, sector and product-liability duties in target markets.",
  "Signed applicability review, exception register and required approvals.",
  "Material legal and regulatory obligations accepted."),
 "security": ("Close security and data protection conditions",
  "CISO / Privacy Lead", "20 business days",
  "Validate access, vendor controls and data protection against the planned rollout scope.",
  "Approved security and privacy assessment with documented exceptions.",
  "No material unresolved security or privacy gate."),
 "reliability": ("Prove operating reliability at intended scale",
  "Technology / Operations", "20 business days",
  "Exercise failures, escalation and recovery using realistic production scenarios.",
  "Signed reliability test results, incident response and fallback evidence.",
  "Operational reliability gate demonstrated."),
 "owner": ("Establish accountable business ownership",
  "Executive Sponsor / Business Operations", "10 business days",
  "Assign a leader for adoption outcomes, process ownership and operational decisions.",
  "Approved business RACI, outcome measures and escalation authority.",
  "Accountability for adoption and results evidenced."),
 "exit": ("Approve release, stop and rollback thresholds",
  "Executive Sponsor / Technology", "30 business days",
  "Define measurable stop conditions, fallback triggers and staged-release authority.",
  "Signed rollout gates, rollback rehearsal and revalidation criteria.",
  "Release and reversal controls tested and approved."),
 "capacity": ("Validate the next rollout wave capacity",
  "Platform Owner / Technology", "20 business days",
  "Test concurrency, peak latency, cost and knowledge freshness at the next user volume.",
  "Load-test evidence, cost envelope and capacity sign-off.",
  "Capacity shown sufficient for proposed next wave."),
 "workflow": ("Prove operational workflows end to end",
  "Process Owner / Regional Operations", "20 business days",
  "Test redesigned work, exceptions and escalation in representative target teams.",
  "Approved work instructions and cross-team acceptance record.",
  "Critical process steps accepted by affected owners."),
 "fallback": ("Rehearse service fallback and incident recovery",
  "Operations / Service Desk", "15 business days",
  "Run a failure exercise and confirm users can return to approved manual procedures.",
  "Signed fallback exercise and production-support runbook.",
  "Service continuity demonstrated."),
 "usage": ("Validate sustained adoption and work impact",
  "Business Adoption Lead", "30 business days",
  "Measure meaningful repeat use, workflow change and business results after initial launch.",
  "Behavioral adoption dashboard and documented user evidence.",
  "Adoption supported by longitudinal business evidence."),
 "learning": ("Finish role-based user preparation",
  "Business Adoption Lead / HR", "20 business days",
  "Test role-specific training, local job aids and support across target user groups.",
  "Training acceptance, support ownership and completion evidence.",
  "Affected roles prepared for the next wave."),
 "employees": ("Test the solution with representative users",
  "Operations / Workforce Leads", "20 business days",
  "Observe real tasks with representative employees, including exceptions and escalation.",
  "User-test results, issues and approved workflow adjustments.",
  "Representative users validate the intended work."),
 "economics": ("Validate full scaling economics",
  "Finance / Business Owner", "20 business days",
  "Reconcile full operating costs, benefits assumptions and cost sensitivity by market.",
  "Finance-approved economic case with downside sensitivity.",
  "Expected value remains credible at intended scale."),
 "data": ("Confirm data ownership and readiness",
  "Data Steward / Business Owner", "20 business days",
  "Check source currency, quality, access and accountability for critical data inputs.",
  "Data quality record, access review and named stewardship.",
  "Critical production data conditions demonstrated."),
 "baseline": ("Validate the existing business baseline",
  "Business Owner / Finance", "15 business days",
  "Set an agreed comparator for productivity, quality, cost and errors.",
  "Signed baseline and measurement definition.",
  "The benefit case can be independently tested."),
 "outcome": ("Verify actual pilot business outcomes",
  "Business Owner / Finance", "20 business days",
  "Compare pilot outcomes against baseline, separating correlation and causation.",
  "Documented pilot benefits and evidence limitations.",
  "Business improvement is credible, not assumed."),
 "sponsor": ("Confirm executive sponsorship and funding authority",
  "Executive Sponsor", "10 business days",
  "Confirm decision rights, funding ownership and benefit accountability.",
  "Approved sponsorship and investment mandate.",
  "Executive accountability documented."),
 "accountability": ("Agree explicit staged rollout decision rights",
  "Executive Sponsor / Program Owner", "15 business days",
  "Define who can advance, pause, reject or reopen each planned release.",
  "Approved release gates, ownership and exception handling.",
  "Scaling decisions have assigned authority."),
}

DEFAULT_ACTION = (
 "Validate the next deployment condition", "Business Owner / Risk Lead",
 "20 business days", "Confirm evidence and open constraints before authorizing further deployment.",
 "Owner-approved evidence and a documented next-stage decision.",
 "Decision condition reviewed and accepted."
)
PRIORITY_HINTS = ("exit", "capacity", "workflow", "fallback", "economics", "usage",
                  "learning", "data", "employees", "accountability", "baseline",
                  "outcome", "sponsor")


def _clean(value: object, limit: int = 750) -> str:
    """Render safely with fpdf2's built-in Helvetica without broken glyphs."""
    text = str(value if value is not None else "")
    trans = {"\u2014":" - ", "\u2013":"-", "\u2019":"'", "\u2018":"'",
             "\u201c":'"', "\u201d":'"', "\u2022":"-", "\u00a0":" "}
    for a,b in trans.items():
        text = text.replace(a,b)
    text = " ".join(text.split())
    return text.encode("latin-1", "replace").decode("latin-1")[:limit]


def _font(pdf: FPDF, size: float = 9, bold: bool = False, color=INK) -> None:
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.set_text_color(*color)


def _single(pdf: FPDF, x: float, y: float, text: object,
            size: float = 9, bold: bool = False, color=INK,
            max_w: float | None = None) -> None:
    _font(pdf, size, bold, color)
    s = _clean(text)
    if max_w is not None:
        while s and pdf.get_string_width(s) > max_w:
            s = s[:-1]
        if s != _clean(text):
            s = s.rstrip(" .") + "..."
    pdf.set_xy(x, y)
    pdf.cell(0, 5, s)


def _paragraph(pdf: FPDF, x: float, y: float, width: float, text: object,
               size: float = 9, line_h: float = 4.8, color=INK) -> float:
    _font(pdf, size, False, color)
    pdf.set_xy(x,y)
    pdf.multi_cell(width, line_h, _clean(text), new_x="LMARGIN",new_y="NEXT")
    return pdf.get_y()


def _base(pdf: FPDF, page: int, is_demo: bool) -> None:
    pdf.set_fill_color(*PAPER)
    pdf.rect(0,0,210,297,"F")
    pdf.set_fill_color(*NAVY)
    pdf.rect(0,0,210,51 if page==1 else 34,"F")
    _single(pdf,16,8,"JAIR RIBEIRO / EXECUTIVE AI ADVISORY",8.5,True,(226,206,185))
    if page==1:
        _single(pdf,16,19,"Enterprise AI Rollout",22,True,(255,255,255))
        _single(pdf,16,34,"EXECUTIVE DECISION BRIEF",11,True,(237,239,242))
        _single(pdf,175,36,"EDITION 02",7,True,(225,209,192))
    else:
        _single(pdf,16,18,"DECISION EXECUTION / RELEASE CONDITIONS",11,True,(255,255,255))
    pdf.set_draw_color(*RULE)
    pdf.line(16,280,194,280)
    _single(pdf,16,283,"jairribeiro.com  |  Private Executive Advisory",7.4,False,MUTED)
    _single(pdf,174,283,f"{page} / 2",7.4,True,MUTED)
    if is_demo:
        _single(pdf,16,290,"SYNTHETIC OWNER QA - NOT CLIENT EVIDENCE",7,True,ALERT)


def _section(pdf: FPDF, x: float, y: float, title: str):
    _single(pdf,x,y,title.upper(),9.2,True,COPPER)
    pdf.set_draw_color(*RULE)
    pdf.line(x,y+6,194,y+6)


def _gate_keys(data: dict) -> list[str]:
    responses = data["responses"]
    high = data["context"]["criticality"]=="High"
    gates = ("reliability","security","oversight","regulation","owner")
    return [key for key in gates if responses[key] < (3 if high and key in gates[:-1] else 2)]


def build_action_plan(data: dict, result: dict) -> list[dict]:
    """Three clearly accountable suggested actions, each tied to actual ratings."""
    from collections import OrderedDict
    responses=data["responses"]
    keys = _gate_keys(data)
    remaining = [key for key in PRIORITY_HINTS if responses[key]<3 and key not in keys]
    # Prioritize lower scores, then the defined business-impact order.
    remaining.sort(key=lambda key:(responses[key], PRIORITY_HINTS.index(key)))
    for key in remaining:
        if len(keys)>=3:break
        keys.append(key)
    if len(keys)<3:
        for key in PRIORITY_HINTS:
            if key not in keys:
                keys.append(key)
            if len(keys)>=3:break
    plan=[]
    for i,key in enumerate(keys[:3],1):
        title,owner,due,action,evidence,condition=CATALOG.get(key,DEFAULT_ACTION)
        plan.append(dict(number=i,key=key,title=title,owner=owner,due=due,
                         action=action,evidence=evidence,condition=condition,
                         critical=key in _gate_keys(data)))
    return plan


def _verdict_text(label: str) -> str:
    return {
     "PAUSE SCALING":"Do not authorize wider rollout until critical conditions are resolved.",
     "EVIDENCE INCOMPLETE":"Defer authorization until the missing readiness evidence is collected.",
     "CONTROLLED EXPANSION":"Authorize only a bounded next-stage test, not enterprise-wide deployment.",
     "CONDITIONAL GO":"Advance only within defined limits and subject to documented conditions.",
     "PHASED GO":"Consider a phased next step subject to independent business and risk approval.",
    }.get(label,"Reassess deployment only after documented executive review.")


def _summary(data:dict,result:dict,actions:list[dict]) -> str:
    dimensions=result["dimensions"]
    strong=sorted(dimensions, key=lambda k: (-dimensions[k],k))[:2]
    weakest=min(dimensions,key=lambda k:dimensions[k])
    label=result["label"]
    base=(f"Self-reported readiness is {result['overall']}/100. "
          f"The strongest dimensions are {strong[0]} ({dimensions[strong[0]]}%) "
          f"and {strong[1]} ({dimensions[strong[1]]}%). "
          f"The least-ready area is {weakest} ({dimensions[weakest]}%). ")
    if label=="PAUSE SCALING":
        controls=", ".join(a["title"].lower() for a in actions if a["critical"])
        base+=(f"Despite encouraging pilot indicators, wider release is blocked by "
               f"insufficiently demonstrated critical conditions: {controls}. "
               "Continue only within the already controlled scope while authorized reviewers close these gates.")
    elif label=="EVIDENCE INCOMPLETE":
        base+="Insufficient evidence prevents a defensible scaling decision. Verify key inputs before committing further deployment."
    elif label=="PHASED GO":
        base+="This supports consideration of a staged deployment, not automatic authority to launch. Apply the indicated safeguards at each release gate."
    else:
        base+="The next stage requires explicit limits, owners and acceptance evidence before wider release."
    return base


def _metric(pdf:FPDF,x:float,y:float,w:float,value:str,label:str):
    pdf.set_fill_color(*PALE)
    pdf.rect(x,y,w,22,"F")
    _single(pdf,x+4,y+2.5,value,15,True,NAVY,max_w=w-8)
    _single(pdf,x+4,y+14,label,7.1,False,MUTED,max_w=w-8)


def _summary_data_signals(data:dict) -> list[tuple[str,str]]:
    pilot=data.get("pilot_indicators")
    if isinstance(pilot,dict):
        try:
            b=float(pilot["baseline_median_find_minutes"])
            a=float(pilot["pilot_median_find_minutes"])
            if b>0 and a>=0 and a<=b:
                decrease=round((b-a)*100/b)
                return [
                    (f"{decrease}%","SIMULATED RETRIEVAL IMPROVEMENT"),
                    (f"{int(pilot['weekly_active_pilot_percent'])}%","SIMULATED WEEKLY ACTIVE USE"),
                    (f"{float(pilot['citation_traceability_percent']):.1f}%","SIMULATED CITATION TRACEABILITY"),
                ]
        except (KeyError,TypeError,ValueError,OverflowError):
            pass
    return [
        ("18", "READINESS CONDITIONS REVIEWED"),
        (result_placeholder(data), "EVIDENCE BASIS"),
        ("5", "DECISION DIMENSIONS"),
    ]


def result_placeholder(data:dict)->str:
    return "SELF-REPORTED"


def _confidence_note(result:dict)->str:
    return (
        f"{result['confidence']} confidence | {result['unassessed']} of 18 conditions unassessed. "
        "Ratings reflect submitted statements, not independent verification. "
        "Actual authorization remains with the client's responsible executives and control owners."
    )


def render_premium_rollout_pdf(result:dict,data:dict) -> bytes:
    """Render two A4 pages. Never uses a canned result unrelated to answers."""
    responses=data["responses"]
    if len(responses)!=18:
        raise ValueError("Incomplete rollout assessment")
    actions=build_action_plan(data,result)
    is_demo=bool(isinstance(data.get("demo"),dict) and data["demo"].get("is_demo") is True)
    context=data["context"]
    pdf=FPDF(format="A4",unit="mm")
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(16,16,16)
    pdf.set_title("Enterprise AI Rollout | Executive Decision Brief v2")
    pdf.set_author("Jair Ribeiro | Executive AI Advisory")

    # PAGE 1: management decision and the business case.
    pdf.add_page()
    _base(pdf,1,is_demo)
    _single(pdf,16,56,_clean(context.get("use_case"),105),11,True,NAVY,max_w=178)
    _single(pdf,16,64,f"{context.get('stage')}  /  {context.get('scope')}  /  {context.get('criticality')} consequence",
            8.2,False,MUTED,max_w=176)
    if is_demo:
        pdf.set_fill_color(252,235,226)
        pdf.rect(16,73,178,11,"F")
        _single(pdf,20,75,"SYNTHETIC QA CASE - ALL PILOT FIGURES AND EVIDENCE REFERENCES ARE FICTIONAL",
                7.2,True,ALERT,max_w=170)
    pdf.set_fill_color(239,241,241)
    pdf.rect(16,88,178,40,"F")
    pdf.set_fill_color(*(ALERT if result["label"] in ("PAUSE SCALING","EVIDENCE INCOMPLETE") else GREEN))
    pdf.rect(16,88,3.2,40,"F")
    _single(pdf,23,91,"EXECUTIVE VERDICT",7.8,True,MUTED)
    _single(pdf,23,99,result["label"],16,True,NAVY,max_w=148)
    _paragraph(pdf,23,111,161,_verdict_text(result["label"]),9.2,5.3,INK)
    _section(pdf,16,134,"Executive summary")
    _paragraph(pdf,16,144,178,_summary(data,result,actions),9.1,4.8,INK)
    _section(pdf,16,185,"Readiness profile")
    names=list(result["dimensions"].items())
    for i,(name,score) in enumerate(names):
        y=195+i*8.6
        _single(pdf,16,y,name,8.2,False,INK,max_w=76)
        pdf.set_fill_color(*RULE)
        pdf.rect(96,y+1.2,74,3.2,"F")
        pdf.set_fill_color(*((ALERT if score<50 else COPPER) if score<75 else GREEN))
        pdf.rect(96,y+1.2,max(0,min(74,74*float(score)/100)),3.2,"F")
        _single(pdf,174,y-0.2,f"{int(score)}%",8.1,True,NAVY)
    _section(pdf,16,242,"Decision evidence")
    signals=_summary_data_signals(data)
    for i,(value,label) in enumerate(signals[:3]):
        _metric(pdf,16+i*60,251,56,value,label)

    # PAGE 2: prioritized action plan, release criteria, and decision boundary.
    pdf.add_page()
    _base(pdf,2,is_demo)
    _single(pdf,16,40,"What must happen next",16,True,NAVY)
    _single(pdf,16,49,
        "Recommended owners and timelines are advisory proposals, not existing commitments.",
        8.4,False,MUTED,max_w=178)
    for i,entry in enumerate(actions):
        y=60+i*50
        pdf.set_fill_color(245,243,238)
        pdf.rect(16,y,178,47,"F")
        pdf.set_fill_color(*COPPER)
        pdf.rect(16,y,3,47,"F")
        _single(pdf,22,y+3.4,f"0{entry['number']}",9.5,True,COPPER)
        _single(pdf,34,y+3.1,entry["title"],10.5,True,NAVY,max_w=154)
        _single(pdf,34,y+12,
                f"PROPOSED OWNER  {entry['owner']}    |    TARGET  {entry['due']}",
                7.4,True,MUTED,max_w=155)
        _single(pdf,22,y+20,"ACTION",7,True,COPPER)
        _paragraph(pdf,51,y+19.2,133,entry["action"],8.05,4.1,INK)
        _single(pdf,22,y+29.5,"EVIDENCE",7,True,COPPER)
        _paragraph(pdf,51,y+28.7,133,entry["evidence"],8.05,4.1,INK)
        _single(pdf,22,y+39,"RELEASE GATE",7,True,COPPER)
        _single(pdf,51,y+38.6,entry["condition"],7.9,False,INK,max_w=132)

    _section(pdf,16,212,"Conditions for reconsideration")
    for i,entry in enumerate(actions):
        y=222+i*8.5
        pdf.set_draw_color(*COPPER)
        pdf.rect(16,y+0.4,3.5,3.5)
        _single(pdf,23,y-0.4,entry["condition"],8.3,False,INK,max_w=168)
    _single(pdf,16,251,
            "Reassessment makes a new decision possible; it does not automatically authorize rollout.",
            8.3,True,NAVY,max_w=177)
    pdf.set_draw_color(*RULE)
    pdf.line(16,258,194,258)
    _single(pdf,16,260,"EVIDENCE CONFIDENCE / DECISION BOUNDARY",7.7,True,COPPER)
    _paragraph(pdf,16,266,178,_confidence_note(result),7.4,3.8,MUTED)
    if len(pdf.pages)!=2:
        raise RuntimeError("The executive brief must render as exactly two pages")
    return bytes(pdf.output())
