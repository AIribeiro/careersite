"""Authenticated, downloadable executive AI portfolio decision advisor.

Pure OOXML authoring keeps the application dependency-light. The workbook has
editable inputs, Excel formulas, input dropdowns, decision gates, a synthetic
example, and complete instructions. It is generated inside the verified
Streamlit reader session; there is no public static .xlsx asset.

The editorial scoring model is a decision aid, not automatic funding approval.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
import re

SLUG = "would-you-fund-the-same-ai-initiatives-today"
FILE_NAME = "AI_Portfolio_Renewal_Decision_Advisor.xlsx"
MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT = "http://schemas.openxmlformats.org/package/2006/content-types"

# Style ID legend: 1 navy title, 2 navy section, 3 gray label,
# 4 editable blue, 5 body text, 6 rich result, 7 pale-blue note,
# 8 numeric result, 9 percentage input, 10 muted help.
_STYLES = '''<?xml version="1.0" encoding="utf-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="6">
 <font><sz val="11"/><name val="Aptos"/></font>
 <font><b/><sz val="20"/><color rgb="FFFFFFFF"/><name val="Aptos Display"/></font>
 <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font>
 <font><b/><sz val="10"/><color rgb="FF19364B"/><name val="Aptos"/></font>
 <font><sz val="10"/><color rgb="FF19364B"/><name val="Aptos"/></font>
 <font><b/><sz val="18"/><color rgb="FF09273F"/><name val="Aptos Display"/></font>
</fonts>
<fills count="6">
 <fill><patternFill patternType="none"/></fill>
 <fill><patternFill patternType="gray125"/></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FF09273F"/><bgColor indexed="64"/></patternFill></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FF183F56"/><bgColor indexed="64"/></patternFill></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FFE7F3F5"/><bgColor indexed="64"/></patternFill></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FFF1F5F7"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
 <border><left/><right/><top/><bottom/><diagonal/></border>
 <border><left style="thin"><color rgb="FFC3D6DC"/></left>
 <right style="thin"><color rgb="FFC3D6DC"/></right>
 <top style="thin"><color rgb="FFC3D6DC"/></top>
 <bottom style="thin"><color rgb="FFC3D6DC"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="11">
 <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
 <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
 <xf numFmtId="0" fontId="3" fillId="5" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="4" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="5" fillId="4" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
 <xf numFmtId="0" fontId="4" fillId="4" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
 <xf numFmtId="3" fontId="3" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
 <xf numFmtId="10" fontId="4" fillId="4" borderId="1" xfId="0"/>
 <xf numFmtId="0" fontId="4" fillId="5" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


class _Sheet:
    def __init__(self, title):
        self.name = title
        self.cells: dict[int, list[tuple[int, str]]] = defaultdict(list)
        self.merges: list[str] = []
        self.validations: list[tuple[str, list[str]]] = []
        self.heights: dict[int, int] = {}

    def _put(self, ref, fragment):
        match = re.fullmatch(r"([A-H])([1-9][0-9]*)", ref)
        if match is None:
            raise ValueError("Invalid worksheet address")
        col = ord(match.group(1)) - 64
        row = int(match.group(2))
        self.cells[row].append((col, fragment))

    def text(self, ref, value, style=5):
        v = escape(str(value))
        # Quoted plain text only; no external formulas from user content.
        self._put(ref, f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{v}</t></is></c>')

    def num(self, ref, value, style=4):
        v = str(float(value)) if isinstance(value, float) else str(value)
        self._put(ref, f'<c r="{ref}" s="{style}"><v>{v}</v></c>')

    def fx(self, ref, formula, style=5):
        if not formula.startswith("="):
            raise ValueError("Excel formulas must begin with =")
        f = escape(formula[1:])
        self._put(ref, f'<c r="{ref}" s="{style}"><f>{f}</f><v></v></c>')

    def title(self, value):
        self.text("A1", value, 1)
        self.merges.append("A1:H2")
        self.heights[1] = 36
        self.heights[2] = 25

    def section(self, row, text):
        self.text(f"A{row}", text, 2)
        self.merges.append(f"A{row}:H{row}")
        self.heights[row] = 26

    def band(self, row, text, end=1, style=7):
        self.text(f"A{row}", text, style)
        self.merges.append(f"A{row}:H{row+end-1}")
        for n in range(row, row+end):
            self.heights[n] = 29

    def rule(self, row, label, explanation):
        self.text(f"A{row}", label, 3)
        self.text(f"D{row}", explanation, 5)
        self.merges.append(f"D{row}:H{row+1}")
        self.heights[row] = self.heights[row+1] = 28

    def dropdown(self, ref, values):
        self.validations.append((ref, values))

    def xml(self):
        rows = []
        for row in sorted(self.cells):
            items = "".join(frag for _,frag in sorted(self.cells[row]))
            ht = self.heights.get(row, 24)
            rows.append(f'<row r="{row}" ht="{ht}" customHeight="1">{items}</row>')
        merges = ("<mergeCells count=\"" + str(len(self.merges)) + "\">" +
                  "".join(f'<mergeCell ref="{x}"/>' for x in self.merges) +
                  "</mergeCells>") if self.merges else ""
        data_validations = ""
        if self.validations:
            validations = []
            for cell, options in self.validations:
                # Excel in-cell list; user selection, not arbitrary free text.
                words = escape('"' + ",".join(options) + '"')
                validations.append(f'<dataValidation type="list" allowBlank="1" showDropDown="0" sqref="{cell}"><formula1>{words}</formula1></dataValidation>')
            data_validations = '<dataValidations count="' + str(len(validations)) + '">' + ''.join(validations) + '</dataValidations>'
        cols = '<cols><col min="1" max="1" width="37" customWidth="1"/><col min="2" max="3" width="12" customWidth="1"/><col min="4" max="4" width="30" customWidth="1"/><col min="5" max="5" width="3" customWidth="1"/><col min="6" max="6" width="30" customWidth="1"/><col min="7" max="7" width="3" customWidth="1"/><col min="8" max="8" width="56" customWidth="1"/></cols>'
        return ('<?xml version="1.0" encoding="utf-8"?>'
                f'<worksheet xmlns="{_NS}">'
                '<sheetViews><sheetView workbookViewId="0"><pane ySplit="3" topLeftCell="A4" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
                '<sheetFormatPr defaultRowHeight="22"/>'
                + cols + '<sheetData>' + ''.join(rows) + '</sheetData>' + merges
                + data_validations + '<pageMargins left="0.3" right="0.3" top="0.45" bottom="0.45" header="0.2" footer="0.2"/>'
                '</worksheet>')


def _build_input_sheet():
    s = _Sheet("INPUTS")
    s.title("01 / FRAME THE NEXT AI INVESTMENT")
    s.band(3, "Editable pale-blue cells drive the recommendation. Use the same business outcome, period and currency for both options.")
    s.section(5, "DECISION CONTEXT")
    for row, label, note in (
        (6,"Business outcome to improve","A measurable outcome, not a technology feature."),
        (7,"Incumbent AI initiative","Current initiative seeking additional commitment."),
        (8,"Best credible alternative","Another AI route or a simpler process improvement."),
        (9,"Accountable executive","Decision authority for releasing or redirecting capacity."),
        (10,"Currency","All financial inputs must use the same currency."),
        (11,"Comparison horizon (months)","Enter all projected benefits and costs for this period."),
        (12,"Opportunity cost per specialist day","Enter 0 only if you deliberately leave specialist capacity unpriced."),
        (13,"Materiality threshold (%)","Editable default 10%: close financial cases trigger TEST."),
        (14,"Mandatory legal/service obligation?","If Yes, duties cannot be lost in a stop/replacement."),
        (15,"Alternative meets mandatory duty?","Choose N/A when no duty applies."),
        (16,"Decision date","Optional metadata."),
        (17,"Next executive review date","Record when the choice is revisited."),
        (18,"Material nonfinancial/avoided-risk value?","If Yes, a negative monetary result cannot alone justify stopping."),
    ):
        s.text(f"A{row}", label,3); s.text(f"H{row}", note,10)
        if row in (11,13):continue
        if row in (16,17):continue
        # Blank typed input areas remain editable.
        s.text(f"D{row}", "",4)
    s.num("D11",12,4)
    s.num("D13",0.10,9)
    for cell, options in (
        ("D10",["SEK","EUR","USD","GBP","BRL","Other"]),
        ("D14",["Yes","No"]),
        ("D15",["Yes","No","Not assessed","N/A"]),
        ("D18",["Yes","No"]),
    ):s.dropdown(cell,options)
    s.section(19,"COMPARABLE FORWARD-LOOKING OPTIONS")
    s.text("A20","DECISION INPUT",3)
    s.text("D20","INCUMBENT",3)
    s.text("F20","ALTERNATIVE",3)
    s.text("H20","INTERPRETATION",3)
    metrics=(
        (21,"Future incremental business benefit","Incremental benefit over the common period."),
        (22,"Future delivery and running cost","Remaining cost only, not past sunk expenditure."),
        (23,"Scarce specialist days","Use the same constrained resources for both options."),
        (24,"Evidence quality","Hypothesis, pilot evidence or operational evidence."),
        (25,"Operating owner confirmed?","Who will own the result in live operations?"),
        (26,"Risk/control status","A blocked selected option requires HOLD."),
        (27,"Operational adoption readiness","Partial/not ready triggers a bounded TEST."),
        (28,"Future switching/exit costs","Real transition costs for alternative; incumbent defaults to zero."),
        (29,"Outcome KPI and baseline","Optional but strongly recommended for executive review."),
        (30,"Most material unknown","Optional: define a falsifiable TEST."),
    )
    for row,label,detail in metrics:
        s.text(f"A{row}",label,3);s.text(f"H{row}",detail,10)
        if row != 28:s.text(f"D{row}","",4)
        else:s.num("D28",0,4)
        s.text(f"F{row}","",4)
    for col in ("D","F"):
        for row,options in (
            (24,["Hypothesis","Pilot evidence","Operational evidence"]),
            (25,["Yes","No"]),
            (26,["Clear","Needs mitigation","Blocked"]),
            (27,["Ready","Partial","Not ready"]),
        ):s.dropdown(f"{col}{row}",options)
    s.section(32,"CALCULATED PASS ONE / PROSPECTIVE VALUE")
    for row,label in ((33,"Future net benefit"),(34,"Alternative minus incumbent"),(35,"Materiality band"),(36,"Pass-one direction"),(37,"Input completeness")):
        s.text(f"A{row}",label,3)
    s.fx("D33",'=IF(OR(D21="",D22="",D23="",$D$12=""),"",D21-D22-D23*$D$12-D28)',8)
    s.fx("F33",'=IF(OR(F21="",F22="",F23="",F28="",$D$12=""),"",F21-F22-F23*$D$12-F28)',8)
    s.fx("F34",'=IF(OR(D33="",F33=""),"",F33-D33)',8)
    s.fx("F35",'=IF(OR(D33="",F33=""),"",MAX(ABS(D33),ABS(F33))*$D$13)',8)
    s.fx("F36",'=IF(OR(D33="",F33=""),"NO DATA",IF(AND(D33<=0,F33<=0),"STOP CANDIDATE",IF(ABS(F34)<=F35,"BROADLY EQUAL",IF(F34>0,"ALTERNATIVE","INCUMBENT"))))')
    empty = ["D6","D7","D8","D9","D10","D11","D12","D13","D14","D18"] + [f"{c}{r}" for c in ("D","F") for r in (21,22,23,24,25,26,27)] + ["F28"]
    incomplete = [f'{c}=""' for c in empty]+['AND(D14="Yes",D15="")']
    invalid = ["D11<=0","D12<0","D13<0","D13>=1"]+[f"{c}{r}<0" for c in ("D","F") for r in (21,22,23)]+["F28<0"]
    s.fx("F37",'=IF(OR('+','.join(incomplete)+'),"INCOMPLETE",IF(OR('+','.join(invalid)+'),"INVALID VALUES","READY"))')
    s.band(39,"PASS TWO applies evidence, adoption, ownership, risk and mandatory-duty checks. These qualitative gates are not arbitrary score multipliers.",2)
    s.band(42,"Do not use past expenditure as a benefit. A model recommendation is not an executive authorization.",2,10)
    return s


def _build_decision_sheet():
    s=_Sheet("DECISION")
    s.title("02 / EXECUTIVE RECOMMENDATION")
    s.band(3,"Live Excel formulas update after choices and numbers in INPUTS. Recalculation is automatic in Microsoft Excel.")
    s.section(5,"THE RECOMMENDATION")
    s.text("A7","RECOMMENDED ACTION",3)
    s.fx("D7",(
        '=IF(INPUTS!F37<>"READY","COMPLETE INPUTS",'
        'IF(AND(INPUTS!D14="Yes",OR(INPUTS!F36="STOP CANDIDATE",'
        'AND(INPUTS!D15<>"Yes",OR(INPUTS!F36="ALTERNATIVE",INPUTS!F36="BROADLY EQUAL")))),"HOLD",'
        'IF(INPUTS!F36="STOP CANDIDATE",IF(INPUTS!D18="Yes","HOLD","STOP"),'
        'IF(INPUTS!F36="BROADLY EQUAL","TEST",'
        'IF(INPUTS!F36="ALTERNATIVE",'
        'IF(OR(INPUTS!F26="Blocked",INPUTS!F25="No"),"HOLD",'
        'IF(OR(INPUTS!F24="Hypothesis",INPUTS!F26="Needs mitigation",INPUTS!F27<>"Ready"),"TEST","REPLACE")),'
        'IF(OR(INPUTS!D26="Blocked",INPUTS!D25="No"),"HOLD",'
        'IF(OR(INPUTS!D24="Hypothesis",INPUTS!D26="Needs mitigation",INPUTS!D27<>"Ready"),"TEST","RENEW")))))))'),6)
    s.merges.append("D7:H8")
    s.text("A10","WHY THIS RESULT?",3)
    s.fx("D10",(
       '=IF(D7="COMPLETE INPUTS","Complete all mandatory INPUTS cells; the model will not guess the missing information.",'
       'IF(D7="HOLD",IF(AND(INPUTS!D14="Yes",OR(INPUTS!F36="STOP CANDIDATE",'
       'AND(INPUTS!D15<>"Yes",OR(INPUTS!F36="ALTERNATIVE",INPUTS!F36="BROADLY EQUAL")))),'
       '"A mandatory service or legal duty may be breached. Obtain qualified review before a stop or switch.",'
       'IF(AND(INPUTS!D18="Yes",INPUTS!F36="STOP CANDIDATE"),'
       '"A material nonfinancial benefit or avoided risk remains unpriced. Negative cash estimates cannot alone justify stopping.",'
       '"The financially preferred option has an operating-owner or control blocker. Escalate before funding.")),'
       'IF(D7="TEST",IF(INPUTS!F36="BROADLY EQUAL","The prospective value gap is below the materiality threshold.",'
       '"The preferred option still has uncertainty in evidence, adoption or controls."),'
       'IF(D7="STOP","Neither option has positive prospective monetary value, and no mandatory or unpriced value is flagged.",'
       'IF(D7="REPLACE","The alternative materially exceeds the incumbent on future net value after switching costs, with the required gates clear.",'
       '"The incumbent has the stronger prospective case, with evidence, operating ownership and controls clear.")))))'))
    s.merges.append("D10:H12")
    s.text("A14","NEXT MOVE",3)
    s.fx("D14",(
       '=IF(D7="COMPLETE INPUTS","Complete both options and record material risks and obligations.",'
       'IF(D7="HOLD","Resolve the explicit human oversight, risk or mandatory-duty gate before authorizing change.",'
       'IF(D7="TEST","Design a bounded experiment with one outcome KPI, a decision owner and a review date.",'
       'IF(D7="STOP","Plan an orderly exit, preserving essential service, people and knowledge.",'
       'IF(D7="REPLACE","Confirm transition and redirect capacity from the incumbent to the alternative.",'
       '"Approve only a bounded continuation, with its next evidence gate.")))))'))
    s.merges.append("D14:H16")
    s.section(18,"FORWARD-LOOKING NUMBERS / SHARED CURRENCY AND HORIZON")
    for row,label,ref in (
        (20,"Incumbent net benefit","D33"),
        (21,"Alternative net benefit","F33"),
        (22,"Alternative minus incumbent","F34"),
        (23,"Materiality band","F35"),
        (24,"Pass-one preference","F36"),
    ):
        s.text(f"A{row}",label,3)
        s.fx(f"D{row}",f'=IF(INPUTS!{ref}="","",INPUTS!{ref})',8 if row<24 else 5)
    s.section(27,"FINAL EXECUTIVE DECISION / COMPLETE AFTER THE REVIEW")
    log=(
        (29,"Executive's authorized decision","Record the actual leadership call; it may differ from the formula."),
        (30,"Rationale / trade-offs","Include evidence and material dissent."),
        (31,"Named decision owner","Who can release or stop resources?"),
        (32,"Next review date","When will the decision be reopened?"),
        (33,"Evidence and KPI required","What must be proven before another commitment?"),
        (34,"Work to stop or redirect","Make the opportunity cost visible."),
        (35,"Trigger to reopen the decision","Risk, benefit, cost, adoption or duty threshold."),
    )
    for row,label,info in log:
        s.text(f"A{row}",label,3);s.text(f"D{row}","",4);s.text(f"H{row}",info,10)
    s.dropdown("D29",["RENEW","REPLACE","TEST","STOP","HOLD"])
    s.band(38,"Human sign-off is required. The workbook does not establish regulatory compliance, predict returns or issue spending authority.",2,7)
    return s


def _build_intro_sheet():
    s=_Sheet("START HERE")
    s.title("AI PORTFOLIO RENEWAL / DECISION ADVISOR")
    s.band(3,"An executive tool for challenging the next AI investment, not defending sunk costs.")
    s.section(5,"HOW TO USE THIS WORKBOOK")
    for r,label,details in (
      (7,"1 / Define","On INPUTS, define one measurable outcome and two plausible routes to it. Use a common currency and time horizon."),
      (10,"2 / Quantify","Enter future benefits, remaining costs, scarce specialist days and switching costs. Do not include sunk spending."),
      (13,"3 / Qualify","Select evidence quality, confirmed operating owner, risk/control status, adoption readiness and mandatory duties."),
      (16,"4 / Interpret","DECISION recommends RENEW, REPLACE, TEST, STOP, HOLD or COMPLETE INPUTS from explicit rules."),
      (19,"5 / Authorize","Record the executive decision, owner, displaced work and next review. The model cannot approve investment."),
      (22,"6 / Learn","EXAMPLE demonstrates the math; METHOD makes thresholds, assumptions and limitations transparent."),
    ):s.rule(r,label,details)
    s.section(27,"HOW TO READ THE OUTCOME")
    for r,label,details in (
      (29,"RENEW","Incumbent remains the stronger future investment and selected-option gates are clear."),
      (32,"REPLACE","Alternative materially exceeds the incumbent on future value and safeguards are clear."),
      (35,"TEST","Evidence is insufficient, adoption is uncertain or the financial difference is not meaningful."),
      (38,"STOP","Both options have non-positive prospective value, without mandatory or material unpriced obligations."),
      (41,"HOLD","Mandatory duty, risk control, operating owner or unpriced strategic value requires human judgment."),
      (44,"COMPLETE INPUTS","Data are missing, negative or inconsistent. No recommendation is issued."),
    ):s.rule(r,label,details)
    s.section(48,"USAGE CAUTIONS")
    s.band(50,"Editable cells are pale blue. Financial inputs are absolute amounts in one chosen currency, not thousands. Benefits, costs and days must cover the same horizon. The default 10% materiality band is adjustable, not scientifically calibrated.",3,10)
    s.band(55,"Based on Jair Ribeiro's published Executive AI Briefing, Would You Fund the Same AI Initiatives Today? See METHOD for references. This is a management exercise, not an independently validated financial, legal or risk model.",3,7)
    return s


def _build_example_sheet():
    s=_Sheet("EXAMPLE")
    s.title("WORKED EXAMPLE / SERVICE KNOWLEDGE ASSISTANT")
    s.band(3,"Synthetic illustration only. It is not based on a measured client project.")
    s.section(5,"SAME OUTCOME / TWO ROUTES")
    s.band(7,"Improve internal service resolution quality and handling time: expand an AI assistant versus repair knowledge ownership and case routing.",2)
    s.text("A10","12-MONTH EXAMPLE / SEK",3)
    s.text("D10","AI assistant",3);s.text("F10","Process redesign",3)
    for row,label,a,b in (
      (11,"Incremental future benefit",500000,420000),
      (12,"Remaining delivery / run cost",400000,210000),
      (13,"Scarce specialist days",80,70),
      (14,"Opportunity cost per day",1000,1000),
      (15,"Future switch / exit cost",0,25000),
    ):
        s.text(f"A{row}",label,3);s.num(f"D{row}",a,8);s.num(f"F{row}",b,8)
    s.text("A17","Prospective net benefit",3)
    s.fx("D17","=D11-D12-D13*D14-D15",8)
    s.fx("F17","=F11-F12-F13*F14-F15",8)
    s.text("A18","Alternative advantage",3)
    s.fx("F18","=F17-D17",8)
    s.section(21,"WHAT AN EXECUTIVE SHOULD CONCLUDE")
    s.band(23,"The alternative has higher illustrative forward net value. With reliable pilot evidence, a confirmed owner, a ready operation and clear controls, the conditional recommendation is REPLACE.",3)
    s.band(27,"If evidence is hypothetical, risk remains blocked or adoption is unready, the answer changes to TEST or HOLD. The qualitative gates matter as much as the arithmetic.",3,7)
    return s


def _build_method_sheet():
    s=_Sheet("METHOD")
    s.title("METHODOLOGY / LIMITS AND SOURCES")
    s.band(3,"Transparent management rules, not a black-box score. Executive approval is always separate.")
    s.section(5,"PASS ONE / THE FUTURE INVESTMENT CASE")
    for r,label,detail in (
      (7,"Net prospective benefit","Future incremental benefit - future costs - specialist days x your opportunity-cost assumption - transition costs."),
      (10,"Comparability","Both options must address the same business outcome and period. Use the same currency."),
      (13,"Materiality band","Default 10% of the larger absolute net benefit. A smaller gap generates TEST."),
      (16,"Sunk cost","Irrecoverable prior investment cannot justify future funding. Reusable assets and future switching costs do count."),
    ):s.rule(r,label,detail)
    s.section(20,"PASS TWO / OWNERSHIP, RISK AND CAPACITY")
    for r,label,detail in (
      (22,"RENEW or REPLACE","Only for a material advantage supported by credible evidence, owner, readiness and clear controls."),
      (25,"TEST","Preferred option is hypothetical, controls need mitigation or operating adoption is not ready."),
      (28,"HOLD","Mandatory service continuity, unpriced avoided risk or a selected-option blocker prevents automatic approval."),
      (31,"STOP","Only when both net monetary cases are non-positive, and no mandatory or material unpriced value was declared."),
    ):s.rule(r,label,detail)
    s.section(35,"PROVENANCE")
    s.band(37,"Jair Ribeiro, Would You Fund the Same AI Initiatives Today? https://jairribeiro.com/?page=briefing&article=would-you-fund-the-same-ai-initiatives-today",2)
    s.band(40,"HM Treasury Green Book (2026): https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026",2)
    s.band(43,"NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework",2)
    s.band(46,"ISO 21504:2022 portfolio-management guidance: https://www.iso.org/standard/82867.html",2)
    s.band(49,"The underlying portfolio principles are established; these categorical gates and materiality assumptions are the author's proposed decision aid, not an independently tested predictive algorithm.",3,10)
    return s


@lru_cache(maxsize=1)
def build_decision_advisor_xlsx() -> bytes:
    """Generate a macro-free five-sheet XLSX; caller MUST verify reader session."""
    sheets=[_build_intro_sheet(),_build_input_sheet(),_build_decision_sheet(),_build_example_sheet(),_build_method_sheet()]
    workbook = ['<?xml version="1.0" encoding="utf-8"?>',
                f'<workbook xmlns="{_NS}" xmlns:r="{_REL}"><bookViews><workbookView activeTab="0"/></bookViews><sheets>']
    for idx,sheet in enumerate(sheets,1):
        workbook.append(f'<sheet name="{escape(sheet.name)}" sheetId="{idx}" r:id="rId{idx}"/>')
    workbook.append('</sheets><calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>')
    rels=[f'<Relationship Id="rId{i}" Type="{_REL}/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,6)]
    rels.append(f'<Relationship Id="rId6" Type="{_REL}/styles" Target="styles.xml"/>')
    content_types=['<?xml version="1.0" encoding="utf-8"?>',
                   f'<Types xmlns="{_CT}">',
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                   '<Default Extension="xml" ContentType="application/xml"/>',
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    for i in range(1,6):
        content_types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append('</Types>')
    output=BytesIO()
    with ZipFile(output,'w',compression=ZIP_DEFLATED,compresslevel=9) as zipfile:
        zipfile.writestr('[Content_Types].xml',''.join(content_types))
        zipfile.writestr('_rels/.rels',
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<Relationships xmlns="{_PKG}"><Relationship Id="rId1" Type="{_REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        zipfile.writestr('xl/workbook.xml',''.join(workbook))
        zipfile.writestr('xl/_rels/workbook.xml.rels',
                         f'<?xml version="1.0" encoding="utf-8"?><Relationships xmlns="{_PKG}">'+''.join(rels)+'</Relationships>')
        zipfile.writestr('xl/styles.xml',_STYLES)
        for idx,sheet in enumerate(sheets,1):
            zipfile.writestr(f'xl/worksheets/sheet{idx}.xml',sheet.xml())
    payload=output.getvalue()
    if not payload.startswith(b'PK') or len(payload)<5000 or len(payload)>900_000:
        raise RuntimeError('Workbook generation failed integrity checks.')
    return payload
