"""Private per-assessment executive exports; generated only after Advisory Auth/RLS read."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
import unicodedata

from fpdf import FPDF
from briefing_renewal_excel import _Sheet, _NS, _REL, _PKG, _CT, _STYLES
from page_advisory_renewal_logic import MODEL_VERSION, assess

NAVY=(13,34,51)
INK=(35,52,65)
MUTED=(91,105,113)
GOLD=(181,126,82)
LIGHT=(241,245,246)
PAPER=(250,249,246)


def _safe(text: object) -> str:
    value=" ".join(str(text if text is not None else "").split())
    return unicodedata.normalize("NFKD",value).encode("latin-1","replace").decode("latin-1")


def report_pdf(inputs: dict, result: dict, decision: dict | None = None,
               *, synthetic: bool = False, created: str = "") -> bytes:
    if result.get("recommendation") == "COMPLETE INPUTS":
        raise ValueError("A completed case is required for a final report.")
    c,inc,alt=(inputs[k] for k in ("context","incumbent","alternative"))
    p=FPDF(orientation="P",unit="mm",format="A4")
    p.set_auto_page_break(auto=True,margin=20)
    p.set_margins(19,19,19)
    p.add_page()
    def top(kicker: str):
        p.set_fill_color(*NAVY);p.rect(0,0,210,39,"F")
        p.set_text_color(234,204,174);p.set_font("Helvetica","B",8);p.set_xy(19,12)
        p.cell(170,5,kicker)
        p.set_text_color(255,255,255);p.set_font("Helvetica","",15);p.set_xy(19,20)
        p.cell(170,10,"AI PORTFOLIO RENEWAL  /  EXECUTIVE DECISION")
        p.set_y(47)
    def section(label: str):
        if p.get_y()>249: p.add_page();p.set_y(22)
        p.ln(4);p.set_font("Helvetica","B",10);p.set_text_color(*NAVY)
        p.cell(0,8,_safe(label),new_x="LMARGIN",new_y="NEXT")
        p.set_draw_color(*GOLD);p.line(19,p.get_y(),191,p.get_y());p.ln(3)
    def paragraph(value: object,sz=9):
        p.set_font("Helvetica","",sz);p.set_text_color(*INK)
        p.multi_cell(172,5,_safe(value));p.ln(2)
    def line(label: str, value: object):
        p.set_font("Helvetica","B",8);p.set_text_color(*MUTED)
        p.cell(55,6,_safe(label)[:42])
        p.set_font("Helvetica","",9);p.set_text_color(*INK)
        p.multi_cell(115,6,_safe(value))
    top("PRIVATE MEMBER REPORT  |  " + ("SYNTHETIC DEMONSTRATION" if synthetic else "CONFIDENTIAL EXECUTIVE INPUT"))
    p.set_font("Helvetica","",9);p.set_text_color(*MUTED)
    p.multi_cell(170,5,_safe(c.get("name","")) + "   |   " + _safe(datetime.now(timezone.utc).strftime("%d %b %Y UTC")))
    p.ln(3)
    p.set_fill_color(*LIGHT);p.rect(19,p.get_y(),172,26,"F")
    y=p.get_y()
    p.set_xy(24,y+5);p.set_text_color(*NAVY);p.set_font("Helvetica","B",22)
    p.cell(80,14,result["recommendation"])
    p.set_xy(111,y+7);p.set_font("Helvetica","",9)
    p.cell(75,6,"DETERMINISTIC RECOMMENDATION")
    p.set_y(y+31)
    paragraph(result["reasons"][0],10)
    section("01  /  THE BUSINESS DECISION")
    line("Outcome",c["outcome"]);line("Baseline",c["baseline"])
    line("Owner and authority",str(c["owner"])+" / "+str(c["authority"]))
    line("Horizon",str(c["horizon_months"])+" months / "+str(c["currency"]))
    section("02  /  FORWARD-LOOKING COMPARISON")
    t=result["pass_two"];money=str(c["currency"])
    line("Incumbent",inc["name"])
    line("Net prospective value",f"{t['incumbent_net']:,.0f} {money}")
    line("Alternative",alt["name"]+" / "+str(alt["route"]).replace("_"," "))
    line("Net prospective value",f"{t['alternative_net']:,.0f} {money}")
    line("Alternative less incumbent",f"{t['delta']:,.0f} {money}")
    line("Specialist days",f"{t['incumbent_specialist_days']:g} incumbent / {t['alternative_specialist_days']:g} alternative")
    section("03  /  THE TWO-PASS CHALLENGE")
    line("Clean sheet",result["pass_one"]["direction"])
    line("Real-world",result["pass_two"]["direction"])
    paragraph("The first pass excludes switching costs; the second includes them and applies mandatory-duty, control, ownership, evidence and readiness gates.")
    section("04  /  WHAT SHOULD HAPPEN NEXT")
    paragraph(result["next_action"])
    for reason in result["reasons"][1:]:
        paragraph("- "+reason,8.5)
    p.add_page()
    top("CASE EVIDENCE & ACCOUNTABILITY  /  " + MODEL_VERSION)
    section("05  /  RISK, EVIDENCE AND READINESS")
    for tag,o in (("Incumbent",inc),("Alternative",alt)):
        line(tag+" evidence",o["evidence"])
        line(tag+" readiness",f"Adoption {o['adoption']}; operations {o['operations']}; data {o['data']}")
        line(tag+" controls",o["controls"]+"; accountable operator "+("Yes" if o["operating_owner"] else "No"))
    line("Mandatory obligation","Yes" if c["mandatory_obligation"] else "No")
    line("Material unpriced value","Yes" if c["material_nonfinancial"] else "No")
    section("06  /  UNCERTAINTY & EVIDENCE TO GATHER")
    for note in result.get("uncertainty",[]) or ["None explicitly flagged in the submitted categories."]:
        paragraph("- "+note)
    section("07  /  AUTHORIZED EXECUTIVE DECISION")
    if decision:
        line("Authorized action",decision.get("authorized_action","Not recorded"))
        line("Authority",decision.get("authorized_by",""))
        line("Review date",decision.get("next_review",""))
        paragraph("Executive rationale: "+str(decision.get("rationale","")))
        if decision.get("authorized_action") != result["recommendation"]:
            paragraph("DIVERGENCE: Executive choice differs from the calculated recommendation. Reasons are recorded above.")
    else:
        paragraph("Not yet authorized. The model result is not a funding decision.")
        line("Authority",c["authority"])
        line("Proposed review",c.get("review_date","To be agreed"))
    section("08  /  METHOD & LIMITS")
    paragraph("Based on Jair Ribeiro's AI Portfolio Renewal Challenge. Only remaining future benefit, future delivery/run cost, constrained specialist capacity and actual switching costs enter the financial comparison. Past sunk expenditure is excluded.")
    paragraph("10% is a configurable management materiality default, not a calibrated standard. Nonfinancial benefits are never converted into arbitrary scores. No tax, discounting, probability distributions or regulatory certification is assumed.")
    paragraph("Source: jairribeiro.com/?page=briefing&article=would-you-fund-the-same-ai-initiatives-today",8)
    footer_y=max(p.get_y()+7,257)
    if footer_y<280:
        p.set_y(footer_y);p.set_font("Helvetica","I",7);p.set_text_color(*MUTED)
        p.multi_cell(172,4,"Jair Ribeiro  |  Enterprise AI leadership  |  Private decision support; human authorization required.")
    result_bytes=bytes(p.output())
    if not result_bytes.startswith(b"%PDF") or len(result_bytes)<3000:
        raise RuntimeError("Invalid executive PDF.")
    return result_bytes


def report_xlsx(inputs: dict, result: dict, decision: dict | None = None,
                *, synthetic: bool=False) -> bytes:
    """Workbook contains actual case values, editable inputs and formula-led finances.

    The categorical action is a versioned snapshot. Changes to Excel inputs
    recalculate the cash comparison; open the site for rule-engine re-evaluation.
    """
    if result["recommendation"]=="COMPLETE INPUTS":
        raise ValueError("Complete the assessment before exporting.")
    c,inc,alt=(inputs[k] for k in ("context","incumbent","alternative"))
    read=_Sheet("READ ME")
    read.title("AI PORTFOLIO RENEWAL / CASE EXPORT")
    read.band(3,("SYNTHETIC EXAMPLE | " if synthetic else "PRIVATE CLIENT CASE | ")+str(c["name"])[:90])
    read.section(6,"READ THIS FIRST")
    read.rule(8,"Shared case","The incumbent and alternative address the same outcome and horizon; all money is in "+str(c["currency"])+".")
    read.rule(11,"Edit inputs","Change pale-blue financial inputs; CALCULATIONS formulas will recalculate in Excel.")
    read.rule(14,"Recommendation","The action in DECISION RECORD is a frozen, versioned website decision. Reopen the assessment online after changing any inputs.")
    read.rule(17,"Boundaries","No past spending, unpriced nonfinancial benefit, or presumed risk multiplier is counted as business benefit.")
    read.rule(20,"Human authorization","The final executive call is separate from the model recommendation and can be different.")
    read.band(24,"Method: https://jairribeiro.com/?page=briefing&article=would-you-fund-the-same-ai-initiatives-today",2)
    sheet=_Sheet("INPUTS")
    sheet.title("CASE INPUTS / SHARED HORIZON")
    sheet.section(4,"BUSINESS CONTEXT")
    fields=[(6,"Initiative",c["name"]),(7,"Function",c["function"]),(8,"Outcome",c["outcome"]),
            (9,"Baseline",c["baseline"]),(10,"Decision authority",c["authority"]),(11,"Currency",c["currency"]),
            (12,"Horizon months",float(c["horizon_months"])),(13,"Opportunity cost per specialist day",float(c["opportunity_cost_day"])),
            (14,"Materiality as decimal",float(c.get("materiality",0.10))),
            (15,"Next commitment requested",float(c["next_commitment"])),
            (16,"Mandatory obligation", "Yes" if c["mandatory_obligation"] else "No"),
            (17,"Unpriced nonfinancial value","Yes" if c["material_nonfinancial"] else "No")]
    for row,label,val in fields:
        sheet.text(f"A{row}",label,3)
        if isinstance(val,float): sheet.num(f"D{row}",val,4)
        else: sheet.text(f"D{row}",val,4)
    sheet.section(19,"COMPETING ROUTES / FUTURE TOTALS ONLY")
    sheet.text("D20","INCUMBENT",3);sheet.text("F20","ALTERNATIVE",3)
    metrics=[(21,"Route name","name"),(22,"Prospective business benefit","benefit"),
             (23,"Remaining delivery and run cost","remaining_cost"),(24,"Scarce specialist days","specialist_days"),
             (25,"Switching / transition cost","transition_cost"),(26,"Evidence maturity","evidence"),
             (27,"Adoption readiness","adoption"),(28,"Operations readiness","operations"),
             (29,"Data readiness","data"),(30,"Control status","controls"),
             (31,"Operating owner","operating_owner"),(32,"Mandatory duty met","mandatory_meets")]
    for row,label,key in metrics:
        sheet.text(f"A{row}",label,3)
        for col,opt in (("D",inc),("F",alt)):
            val=opt.get(key)
            if type(val) is bool: val="Yes" if val else "No"
            if isinstance(val,(float,int)):sheet.num(f"{col}{row}",val,4)
            else:sheet.text(f"{col}{row}",val or "",4)
    for col in ("D","F"):
        for row,opts in ((26,["hypothesis","pilot","operational"]),(27,["not_ready","partial","ready"]),
                          (28,["not_ready","partial","ready"]),(29,["not_ready","partial","ready"]),
                          (30,["blocked","mitigate","clear"]),(31,["Yes","No"]),(32,["Yes","No"])):
            sheet.dropdown(f"{col}{row}",opts)
    calc=_Sheet("CALCULATIONS")
    calc.title("TWO PASS / FINANCIAL COMPARISON")
    calc.band(3,"Formula-based workbook; no probability multiplier or hidden proprietary scoring.")
    calc.section(5,"PASS ONE / CLEAN SHEET")
    calc.text("D7","INCUMBENT",3);calc.text("F7","ALTERNATIVE",3)
    calc.text("A9","Future prospective net value",3)
    for col in ("D","F"):
        calc.fx(f"{col}9",f"=INPUTS!{col}22-INPUTS!{col}23-INPUTS!{col}24*INPUTS!$D$13",8)
    calc.text("A11","Alternative less incumbent",3);calc.fx("F11","=F9-D9",8)
    calc.section(14,"PASS TWO / REAL TRANSITION COSTS")
    calc.text("A16","Net value after transition",3)
    for col in ("D","F"):calc.fx(f"{col}16",f"={col}9-INPUTS!{col}25",8)
    calc.text("A18","Alternative less incumbent",3);calc.fx("F18","=F16-D16",8)
    calc.text("A20","Materiality band in currency",3);calc.fx("F20","=MAX(ABS(D16),ABS(F16),1)*INPUTS!$D$14",8)
    calc.text("A22","Financial direction, not authorization",3)
    calc.fx("F22",'=IF(AND(D16<=0,F16<=0),"STOP CANDIDATE",IF(ABS(F18)<=F20,"CLOSE / TEST",IF(F18>0,"ALTERNATIVE","INCUMBENT")))')
    calc.band(26,"The site adds mandatory obligations, controls, operational owner, evidence, adoption and human review gates. Excel does not substitute for that decision engine.",3)
    dec=_Sheet("DECISION RECORD")
    dec.title("ACCOUNTABLE EXECUTIVE DECISION")
    dec.section(5,"VERSIONED WEBSITE RECOMMENDATION")
    for row,label,value in [(7,"Model version",result["version"]),(9,"Calculated recommendation",result["recommendation"]),
         (11,"Executive next action",result["next_action"]),(14,"Authorized executive choice",(decision or {}).get("authorized_action","Not recorded")),
         (16,"Authorized by",(decision or {}).get("authorized_by",c["authority"])),
         (18,"Next review",(decision or {}).get("next_review",c.get("review_date",""))),
         (20,"Executive rationale",(decision or {}).get("rationale","Not recorded"))]:
        dec.text(f"A{row}",label,3);dec.text(f"D{row}",value,4)
    dec.section(24,"REASONING")
    for i,text in enumerate(result["reasons"][:6]):
        dec.band(26+i*2,str(i+1)+". "+text,2)
    method=_Sheet("METHOD")
    method.title("DECISION RULES / NOT AN INVESTMENT AUTHORITY")
    for r,label,why in [
        (6,"Validate","Any missing, contradictory or invalid input means COMPLETE INPUTS."),
        (9,"Mandatory duties","Neither negative short-term return nor a cheaper alternative automatically displaces a required service."),
        (12,"Control and ownership","Unacceptable blockers or a missing operating owner for the preferred option mean HOLD."),
        (15,"Nonfinancial value","Material unpriced considerations require documented human review; no arbitrary weights."),
        (18,"Prospective value","Incremental benefits less remaining costs, days x opportunity cost, and real transition expense."),
        (21,"Evidence","Hypotheses and incomplete operating/adoption/data readiness prompt TEST rather than a confident funding decision."),
        (24,"Threshold","User-editable 10% default. Financially close cases prompt TEST; it is not scientifically validated."),
        (27,"Execution","Decision authority records RENEW, REPLACE, TEST, STOP or HOLD separately from the model."),
        (30,"Scope","No discounting, taxes, uncertainty distributions, legal certification or value prediction is supplied."),
    ]:method.rule(r,label,why)
    pages=[read,sheet,calc,dec,method]
    wb=['<?xml version="1.0" encoding="utf-8"?>',f'<workbook xmlns="{_NS}" xmlns:r="{_REL}"><bookViews><workbookView activeTab="0"/></bookViews><sheets>']
    for n,s in enumerate(pages,1):wb.append(f'<sheet name="{escape(s.name)}" sheetId="{n}" r:id="rId{n}"/>')
    wb.append('</sheets><calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>')
    rel=[f'<Relationship Id="rId{n}" Type="{_REL}/worksheet" Target="worksheets/sheet{n}.xml"/>' for n in range(1,len(pages)+1)]
    rel.append(f'<Relationship Id="rId{len(pages)+1}" Type="{_REL}/styles" Target="styles.xml"/>')
    types=['<?xml version="1.0" encoding="utf-8"?>',f'<Types xmlns="{_CT}">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    for i in range(1,len(pages)+1):
        types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    types.append('</Types>')
    output=BytesIO()
    with ZipFile(output,'w',compression=ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml","".join(types))
        z.writestr("_rels/.rels",'<?xml version="1.0" encoding="utf-8"?>'+f'<Relationships xmlns="{_PKG}"><Relationship Id="rId1" Type="{_REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml","".join(wb))
        z.writestr("xl/_rels/workbook.xml.rels",f'<Relationships xmlns="{_PKG}">'+ "".join(rel)+"</Relationships>")
        z.writestr("xl/styles.xml",_STYLES)
        for i,s in enumerate(pages,1):z.writestr(f"xl/worksheets/sheet{i}.xml",s.xml())
    payload=output.getvalue()
    if len(payload)<3500 or not payload.startswith(b"PK"):
        raise RuntimeError("Workbook integrity validation failed.")
    return payload
