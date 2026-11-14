"""Premium executive decision report from an approved AI Portfolio Scorecard.

The report contains only user-entered portfolio facts and deterministic
recommendations. It never records or implies an investment approval.
"""
from __future__ import annotations

from typing import Any
import unicodedata
from fpdf import FPDF

NAVY = (13,31,50)
NAVY2 = (26,51,72)
COPPER = (188,126,86)
INK = (29,46,63)
GREY = (90,107,120)
PALE = (239,243,245)
LINE = (218,225,229)
WHITE = (255,255,255)
TEAL = (27,100,108)
LIGHT_COPPER = (249,242,237)
LEFT = 18
RIGHT = 192
CONTENT = 174


def _clean(value: Any) -> str:
    text = str(value if value is not None else "")
    for src, dst in (
        ("\u2014"," - "), ("\u2013","-"), ("\u2019","'"),
        ("\u2018","'"), ("\u201c",'"'), ("\u201d",'"'),
        ("\u2022","-"), ("\u2192","->"), ("\u00a0"," "),
    ):
        text = text.replace(src,dst)
    return unicodedata.normalize("NFKD",text).encode(
        "latin-1",errors="replace"
    ).decode("latin-1")


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} SEK"
    except (TypeError,ValueError):
        return "Not available"


def _number(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError,ValueError):
        return "N/A"


class _DecisionPDF(FPDF):
    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0,0,210,26,"F")
        self.set_fill_color(*COPPER)
        self.rect(0,26,210,1.2,"F")
        self.set_xy(LEFT,6)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica","B",10.6)
        self.cell(0,7,"JAIR RIBEIRO",new_x="LMARGIN",new_y="NEXT")
        self.set_xy(LEFT,16)
        self.set_font("Helvetica","",7)
        self.set_text_color(205,215,223)
        self.cell(0,5,"EXECUTIVE AI ADVISORY   /   PORTFOLIO DECISION INTELLIGENCE")
        self.set_y(35)

    def footer(self):
        self.set_y(-19)
        self.set_draw_color(*LINE)
        self.line(LEFT,self.get_y(),RIGHT,self.get_y())
        self.set_xy(LEFT,self.get_y()+3)
        self.set_font("Helvetica","",7.2)
        self.set_text_color(*GREY)
        self.cell(
            0,6,
            "Executive decision support  |  Approval and deployment subject to formal governance"
        )
        self.set_x(-34)
        self.set_font("Helvetica","B",8)
        self.cell(16,6,f"{self.page_no()} / {{nb}}",align="R")


def _label(pdf: FPDF, text: str, x: float = LEFT,
           y: float | None = None, color=COPPER, size=8):
    if y is not None:
        pdf.set_y(y)
    pdf.set_x(x)
    pdf.set_font("Helvetica","B",size)
    pdf.set_text_color(*color)
    pdf.cell(0,5,_clean(text.upper()),new_x="LMARGIN",new_y="NEXT")


def _multiline(pdf: FPDF, text: Any, x=LEFT, y=None, w=CONTENT,
               size=9.3, color=INK, weight="", line=5.4):
    if y is not None:
        pdf.set_y(y)
    pdf.set_x(x)
    pdf.set_font("Helvetica",weight,size)
    pdf.set_text_color(*color)
    pdf.multi_cell(
        w,line,_clean(text),align="L",new_x="LMARGIN",new_y="NEXT"
    )
    return pdf.get_y()


def _height(pdf: FPDF, text: Any, w=CONTENT, size=9.3,
            weight="", line=5.4):
    pdf.set_font("Helvetica",weight,size)
    return float(pdf.multi_cell(
        w,line,_clean(text),align="L",dry_run=True,output="HEIGHT"
    ))


def _ensure(pdf: FPDF, required: float):
    if pdf.get_y()+required > 267:
        pdf.add_page()


def _section(pdf: FPDF, number: str, title: str):
    _ensure(pdf,23)
    pdf.ln(4)
    _label(pdf,number,color=COPPER,size=7.2)
    pdf.set_x(LEFT)
    pdf.set_font("Helvetica","B",15)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(
        CONTENT,8,_clean(title),align="L",
        new_x="LMARGIN",new_y="NEXT"
    )
    pdf.ln(2)


def _kpi(pdf: FPDF, x: float, y: float, width: float,
         name: str, value: str, detail: str):
    pdf.set_draw_color(*LINE)
    pdf.set_fill_color(250,251,252)
    pdf.rect(x,y,width,25,"DF")
    _label(pdf,name,x+4,y+3,color=GREY,size=6.4)
    pdf.set_xy(x+4,y+10)
    pdf.set_font("Helvetica","B",14)
    pdf.set_text_color(*NAVY)
    pdf.cell(width-8,7,_clean(value))
    pdf.set_xy(x+4,y+18)
    pdf.set_font("Helvetica","",6.8)
    pdf.set_text_color(*GREY)
    pdf.cell(width-8,5,_clean(detail))


def _priority_card(pdf: FPDF, item: dict, index: int):
    title = str(item.get("name") or "Unnamed initiative")
    status = str(item.get("recommendation") or "Review")
    score = item.get("score")
    owner = str(item.get("owner") or "Owner not recorded")
    rationale = str(item.get("rationale") or "Rationale not recorded")
    action = str(item.get("next_action") or "Confirm next evidence")
    w = CONTENT-15
    rh = _height(pdf,"WHY: "+rationale,w=w,size=8.7,line=4.95)
    ah = _height(pdf,"NEXT ACTION: "+action,w=w,size=8.7,line=4.95)
    h = 26+rh+ah
    _ensure(pdf,h+4)
    y = pdf.get_y()
    pdf.set_fill_color(250,251,252)
    pdf.set_draw_color(*LINE)
    pdf.rect(LEFT,y,CONTENT,h,"DF")
    pdf.set_fill_color(*TEAL if status in (
        "Advance to business case","Time-boxed test"
    ) else COPPER)
    pdf.rect(LEFT,y,2,h,"F")
    pdf.set_xy(LEFT+7,y+4)
    pdf.set_font("Helvetica","B",10.4)
    pdf.set_text_color(*NAVY)
    title_short = title if len(title)<64 else title[:60]+"..."
    pdf.cell(138,5.3,_clean(f"{index:02d}  {title_short}"))
    pdf.set_xy(LEFT+147,y+4)
    pdf.set_font("Helvetica","B",9)
    pdf.cell(
        20,5.3,f"{score if score is not None else '-'}/100",align="R"
    )
    pdf.set_xy(LEFT+7,y+11)
    pdf.set_font("Helvetica","",7.5)
    pdf.set_text_color(*GREY)
    route = "BUSINESS CASE" if status=="Advance to business case" else "SCOPED TEST"
    pdf.cell(
        0,4.5,
        _clean(f"{route}  |  Owner: {owner}  |  Evidence: {item.get('evidence') or 'Unrated'}")
    )
    _multiline(pdf,"WHY: "+rationale,LEFT+7,y+18,w,8.7,INK,line=4.95)
    _multiline(
        pdf,"NEXT ACTION: "+action,LEFT+7,pdf.get_y()+1,
        w,8.7,TEAL,line=4.95
    )
    pdf.set_y(y+h+4)


def _exception_table(pdf: FPDF, rows: list[dict]):
    if not rows:
        _multiline(pdf,"No initiatives require hold, redesign or deferral.",size=9)
        return
    y = pdf.get_y()+1
    pdf.set_fill_color(*NAVY2)
    pdf.rect(LEFT,y,CONTENT,10,"F")
    for x,w,title in (
        (LEFT+4,59,"INITIATIVE / OWNER"),
        (LEFT+69,38,"DECISION"),
        (LEFT+110,60,"REQUIRED NEXT ACTION"),
    ):
        pdf.set_xy(x,y+2)
        pdf.set_font("Helvetica","B",7.2)
        pdf.set_text_color(*WHITE)
        pdf.cell(w,6,title)
    pdf.set_y(y+10)
    for index,item in enumerate(rows):
        name = str(item.get("name") or "Unnamed")
        owner = str(item.get("owner") or "Owner not recorded")
        status = str(item.get("recommendation") or "Reassess")
        action = str(item.get("next_action") or "Record the next evidence requirement")
        if len(action)>218:
            action=action[:215].rstrip()+"..."
        width_name=56
        width_status=39
        width_action=61
        hn=(
            _height(pdf,name,width_name,8.4,"B",4.5)
            + _height(pdf,owner,width_name,7.0,"",4.1)
        )
        hs=_height(pdf,status,width_status,8.1,"B",4.4)
        ha=_height(pdf,action,width_action,7.9,"",4.4)
        h=max(24,7+max(hn,hs,ha))
        _ensure(pdf,h+3)
        y=pdf.get_y()
        pdf.set_fill_color(*(WHITE if index%2 else (247,249,250)))
        pdf.rect(LEFT,y,CONTENT,h,"F")
        pdf.set_draw_color(*LINE)
        pdf.line(LEFT,y+h,RIGHT,y+h)
        _multiline(pdf,name,LEFT+4,y+4,width_name,8.4,NAVY,"B",4.5)
        _multiline(
            pdf,owner,LEFT+4,pdf.get_y(),width_name,7.0,GREY,line=4.1
        )
        _multiline(
            pdf,status,LEFT+68,y+4,width_status,8.1,TEAL,"B",4.4
        )
        _multiline(
            pdf,action,LEFT+110,y+4,width_action,7.9,INK,line=4.4
        )
        pdf.set_y(y+h)
    pdf.ln(5)
    _multiline(
        pdf,
        "Detailed evidence references, controls and decision history remain in the private Scorecard workspace.",
        size=8,color=GREY,line=4.6
    )


def _option_row(pdf: FPDF, y: float, title: str,
                option: dict, highlight=False):
    pdf.set_fill_color(*(PALE if highlight else WHITE))
    pdf.rect(LEFT,y,CONTENT,18,"F")
    pdf.set_text_color(*(NAVY if highlight else INK))
    pdf.set_font("Helvetica","B" if highlight else "",8.5)
    pdf.set_xy(LEFT+4,y+4)
    pdf.cell(61,10,_clean(title))
    pdf.set_xy(LEFT+68,y+4)
    pdf.cell(23,10,str(option.get("count",0)),align="C")
    pdf.set_xy(LEFT+92,y+4)
    pdf.cell(31,10,_number(option.get("fte_months")),align="R")
    pdf.set_xy(LEFT+126,y+4)
    pdf.cell(38,10,_money(option.get("investment_sek")),align="R")
    pdf.set_xy(LEFT+166,y+4)
    pdf.cell(7,10,"YES" if option.get("fits") else "NO",align="R")


def _executive_narrative(decision: dict) -> str:
    current=decision["current_selection"]
    rec=decision["recommended"]
    capacity=float(decision["settings"].get("capacity_fte_months") or 0)
    budget=float(decision["settings"].get("budget_sek") or 0)
    over_fte=max(0,current["fte_months"]-capacity)
    over_budget=max(0,current["investment_sek"]-budget)
    if over_fte or over_budget:
        intro=(
            f"The current selection exceeds the planning envelope by "
            f"{_number(over_fte)} FTE-months and {_money(over_budget)}. "
        )
    else:
        intro="The current selection fits the stated planning envelope. "
    if not rec["count"]:
        return (
            intro+"No candidate currently clears the evidence, control and "
            "resource conditions. Hold commitment until the blocking inputs "
            "have been resolved."
        )
    removed=decision.get("changes",{}).get("removed",[])
    delta=(
        " Exclude "+", ".join(removed[:2])
        +" from the current selection pending reassessment."
        if removed else ""
    )
    cases=decision.get("advanced_count",0)
    tests=decision.get("test_count",0)
    return (
        intro
        +f"The recommended candidate portfolio uses {_number(rec['fte_months'])} "
        +f"of {_number(capacity)} FTE-months and {_money(rec['investment_sek'])} "
        +f"of {_money(budget)}. It advances {cases} to business-case review and "
        +f"{tests} to a scoped evidence test."
        +delta
    )


def build_executive_pdf(decision: dict) -> bytes:
    """Generate a decision-first four-section report without modifying client data."""
    pdf=_DecisionPDF(orientation="P",unit="mm",format="A4")
    pdf.set_margins(LEFT,35,LEFT)
    pdf.set_auto_page_break(auto=True,margin=22)
    pdf.alias_nb_pages()
    pdf.add_page()

    _label(pdf,"BOARD / EXECUTIVE DECISION BRIEF",size=7.5)
    pdf.set_font("Helvetica","B",22)
    pdf.set_text_color(*NAVY)
    pdf.set_x(LEFT)
    pdf.multi_cell(
        CONTENT,10,"Executive Portfolio Decision",align="L",
        new_x="LMARGIN",new_y="NEXT"
    )
    _multiline(
        pdf,
        "AI Portfolio Prioritization Scorecard"
        +f"  |  Prepared {decision.get('generated_at') or 'Date not supplied'}"
        +f"  |  Revision {decision.get('revision') if decision.get('revision') is not None else 'N/A'}",
        size=8.4,color=GREY,line=5
    )
    pdf.ln(4)
    rec=decision["recommended"]
    current=decision["current_selection"]
    low=decision["conservative"]
    statement=str(decision.get("verdict") or "No recommendation is available.")
    y=pdf.get_y()
    statement_h=_height(pdf,statement,w=159,size=13.7,weight="B",line=7)
    h=max(37,statement_h+24)
    pdf.set_fill_color(*NAVY2)
    pdf.rect(LEFT,y,CONTENT,h,"F")
    _label(pdf,"Recommended direction",LEFT+8,y+6,color=(225,180,146),size=7.2)
    _multiline(
        pdf,statement,LEFT+8,y+16,159,
        size=13.7,color=WHITE,weight="B",line=7
    )
    pdf.set_y(y+h+6)

    y=pdf.get_y()
    cardwidth=(CONTENT-10)/3
    _kpi(
        pdf,LEFT,y,cardwidth,"PROPOSED PORTFOLIO",
        str(rec.get("count",0)),"initiatives for review"
    )
    _kpi(
        pdf,LEFT+cardwidth+5,y,cardwidth,"CAPACITY",
        _number(rec.get("fte_months"))+" FTE-mo",
        _number(rec.get("fte_headroom"))+" remaining"
    )
    _kpi(
        pdf,LEFT+2*cardwidth+10,y,cardwidth,"PLANNING INVESTMENT",
        _money(rec.get("investment_sek")),
        _money(rec.get("budget_headroom"))+" left"
    )
    pdf.set_y(y+30)

    _section(pdf,"01  /  EXECUTIVE SUMMARY","What the portfolio analysis means")
    _multiline(pdf,_executive_narrative(decision),size=9.9,line=5.8)
    pdf.ln(4)
    decision_request=(
        "Endorse this prioritized shortlist for business-case preparation "
        "and scoped proof. Require sponsor, capacity and control sign-off "
        "before any investment or deployment decision."
    )
    y=pdf.get_y()
    h=max(27,_height(pdf,decision_request,w=159,size=9.5,line=5.3)+13)
    pdf.set_fill_color(*LIGHT_COPPER)
    pdf.rect(LEFT,y,CONTENT,h,"F")
    _label(pdf,"Decision requested",LEFT+7,y+3,size=7.5)
    _multiline(
        pdf,decision_request,LEFT+7,y+11,159,
        size=9.5,weight="B",line=5.3
    )
    pdf.set_y(y+h+6)

    _section(pdf,"02  /  MANAGEMENT ACTIONS","What leadership does next")
    advancing=decision.get("categories",{}).get("Advance to business case",[])
    tests=decision.get("categories",{}).get("Time-boxed test",[])
    holds=decision.get("categories",{}).get("Hold - control review",[])
    actions=[
        (
            "01","BUSINESS CASES",
            f"Commission evidence and benefit cases for {len(advancing)} priority initiatives."
            if advancing else "Complete assessment before prioritization."
        ),
        (
            "02","CONTROLLED TEST",
            str(tests[0]["name"])+": agree proof and go/no-go criteria."
            if tests else "Revisit when a test candidate qualifies."
        ),
        (
            "03","CONTROL REVIEW",
            str(holds[0]["name"])+": close the open control gate."
            if holds else "Confirm outstanding specialist approvals."
        ),
    ]
    y=pdf.get_y()+1
    gap=4
    cw=(CONTENT-2*gap)/3
    for i,(number,title,description) in enumerate(actions):
        x=LEFT+i*(cw+gap)
        pdf.set_fill_color(*PALE)
        pdf.rect(x,y,cw,28,"F")
        pdf.set_fill_color(*COPPER)
        pdf.rect(x,y,1,28,"F")
        _label(pdf,number+"  /  "+title,x+4,y+4,color=TEAL,size=6.8)
        brief=description if len(description)<110 else description[:107]+"..."
        _multiline(
            pdf,brief,x+4,y+11,cw-8,
            size=7.6,color=INK,line=4.2
        )
    pdf.set_y(y+29)

    pdf.add_page()
    _label(pdf,"PORTFOLIO ACTION REGISTER",size=7.5)
    pdf.set_font("Helvetica","B",18)
    pdf.set_text_color(*NAVY)
    pdf.set_x(LEFT)
    pdf.multi_cell(
        CONTENT,9,"What to advance and test",align="L",
        new_x="LMARGIN",new_y="NEXT"
    )
    _multiline(
        pdf,
        "Actions below are requests for evidence and formal business-case review. "
        "They are not spending approvals.",
        size=9,color=GREY,line=5.3
    )
    pdf.ln(3)
    priority=[
        item for item in decision.get("rows",[])
        if item.get("recommendation") in (
            "Advance to business case","Time-boxed test"
        )
    ]
    priority.sort(key=lambda item:(
        item.get("recommendation")!="Advance to business case",
        -(item.get("score") or 0),item.get("name") or ""
    ))
    if not priority:
        _multiline(
            pdf,
            "There are no eligible candidates for commitment under the "
            "current controls and planning limits.",size=10
        )
    for index,item in enumerate(priority,1):
        _priority_card(pdf,item,index)

    pdf.add_page()
    _label(pdf,"EXCEPTIONS AND CONTROL GATES",size=7.5)
    pdf.set_font("Helvetica","B",18)
    pdf.set_text_color(*NAVY)
    pdf.set_x(LEFT)
    pdf.multi_cell(
        CONTENT,9,"What to hold, redesign or defer",align="L",
        new_x="LMARGIN",new_y="NEXT"
    )
    _multiline(
        pdf,
        "These are explicit portfolio choices. An unresolved gate is "
        "not overridden by a high score.",
        size=9,color=GREY,line=5.3
    )
    pdf.ln(3)
    other=[
        item for item in decision.get("rows",[])
        if item.get("recommendation") not in (
            "Advance to business case","Time-boxed test"
        )
    ]
    priority_order={
        "Hold - control review":0,"Stop / redesign":1,
        "Validate evidence":2,"Complete assessment":3,
        "Defer - constrained":4,"Queue for a test":5,"Defer / stop":6,
    }
    other.sort(key=lambda item:(
        priority_order.get(item.get("recommendation"),10),
        -(item.get("score") or 0),item.get("name") or ""
    ))
    _exception_table(pdf,other)

    pdf.add_page()
    _label(pdf,"DECISION OPTIONS AND GOVERNANCE",size=7.5)
    pdf.set_font("Helvetica","B",18)
    pdf.set_text_color(*NAVY)
    pdf.set_x(LEFT)
    pdf.multi_cell(
        CONTENT,9,"Trade-offs and conditions",align="L",
        new_x="LMARGIN",new_y="NEXT"
    )
    _section(pdf,"03  /  OPTIONS","Compare the planning alternatives")
    y=pdf.get_y()
    pdf.set_fill_color(*NAVY2)
    pdf.rect(LEFT,y,CONTENT,10,"F")
    for x,width,heading in (
        (LEFT+4,61,"PORTFOLIO OPTION"),(LEFT+69,23,"ITEMS"),
        (LEFT+92,31,"FTE-MO"),(LEFT+126,38,"INVESTMENT"),
        (LEFT+163,10,"FIT"),
    ):
        pdf.set_xy(x,y+2)
        pdf.set_font("Helvetica","B",7)
        pdf.set_text_color(*WHITE)
        pdf.cell(
            width,6,heading,
            align="R" if heading!="PORTFOLIO OPTION" else "L"
        )
    y+=10
    for title,item,highlight in (
        ("Recommended",rec,True),
        ("Business cases only",low,False),
        ("Current selection",current,False),
    ):
        _option_row(pdf,y,title,item,highlight)
        y+=18
    pdf.set_y(y+6)

    changes=decision.get("changes") or {}
    if changes.get("removed"):
        _label(pdf,"Remove or defer from current selection",size=7.5)
        _multiline(pdf,"; ".join(changes["removed"]),size=9)
    if changes.get("added"):
        _label(pdf,"Add to the proposed shortlist",size=7.5)
        _multiline(pdf,"; ".join(changes["added"]),size=9)

    _section(
        pdf,"04  /  GO / NO-GO CONDITIONS",
        "What must be true before authorizing work"
    )
    conditions=[
        "Business sponsor accepts ownership of the intended outcome and baseline.",
        "Capacity owner confirms people and funding for the proposed scope.",
        "Privacy, security, legal and operational control reviews are complete where applicable.",
        "Any scoped test has defined success, stop and escalation criteria.",
        "An authorized decision-maker separately records the funding or deployment decision.",
    ]
    for index,item in enumerate(conditions,1):
        _ensure(pdf,14)
        _multiline(pdf,f"{index:02d}.  {item}",size=9.2,line=5.25)
        pdf.ln(1)
    if decision.get("caveats"):
        pdf.ln(3)
        _label(
            pdf,"Outstanding conditions from the current assessments",
            size=7.5
        )
        for item in decision["caveats"]:
            _multiline(
                pdf,"- "+str(item),size=8.5,color=INK,line=5.0
            )

    _section(
        pdf,"05  /  REVIEW AND ACCOUNTABILITY",
        "How to use this report"
    )
    _multiline(
        pdf,
        "Use this as the agenda for the next portfolio investment or steering review. "
        "Challenge the underlying assumptions, confirm decision owners, and record "
        "the final outcome in the Scorecard Decision Record tab. Re-generate this "
        "memo after materially changing evidence, capacity or control status.",
        size=9.2,line=5.6
    )
    pdf.ln(3)
    _multiline(
        pdf,
        "Method: seven weighted scoring criteria, mandatory evidence and control "
        "gates, followed by constrained selection against capacity and investment. "
        "Business-case candidates are prioritized before a bounded number of tests. "
        "Selection: "+str(decision.get("selection_method") or "Not specified")
        +". Benefits are client estimates, not validated forecasts. "
        "No approval is inferred from this report.",
        size=8,color=GREY,line=5
    )
    return bytes(pdf.output())
