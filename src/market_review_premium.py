"""Premium executive AI & Data market research PDF.

Observations come exclusively from the signed-off reader-visible edition
manifest. Interpretations identify their evidential limits; no private hiring
or personal career data is used.

Edition 01: Swedish market, 16 November 2026.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape
from io import BytesIO
from math import isfinite
from urllib.parse import urlsplit

from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, LongTable, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

NAVY = colors.HexColor("#10263A")
BLUE = colors.HexColor("#26465C")
TEAL = colors.HexColor("#43706B")
COPPER = colors.HexColor("#A56C4A")
GOLD = colors.HexColor("#D7A781")
PAPER = colors.HexColor("#F5F2EC")
PALE = colors.HexColor("#E9E4DB")
RULE = colors.HexColor("#D7D2CA")
MUTED = colors.HexColor("#526475")
WHITE = colors.HexColor("#FFFFFF")
PRINT_WIDTH = 174 * mm

# Intentionally no automatically computed market health or maturity score.
# These are observed signals, not measurements of individual organisations.

SOURCE_LABEL = {
    "scb_enterprise_ai_adoption": "SCB",
    "af_jobtech_target_demand": "JobTech v1",
    "brainville_consulting_market": "Brainville",
}

SOURCE_COMPARABILITY = {
    "scb_enterprise_ai_adoption":
        "SCB Enterprise ICT Use 2026. Survey-reported AI and analytics measures. "
        "Business-size groups differ, and non-adopter barriers use a restricted subgroup. "
        "The 2026 SNI classification and survey-industry coverage changed.",
    "af_jobtech_target_demand":
        "Arbetsformedlingen JobSearch and Historical Ads, frozen headline-only "
        "AI/Data leadership title basket v1. Deduplicated advertisement records; "
        "retrospective indexing can revise counts. Not completed hires or a census "
        "of senior AI/Data positions.",
    "brainville_consulting_market":
        "Brainville Sweden, October 2026. Marketplace year-on-year growth rates "
        "for listed consulting assignments and available consultants across "
        "all disciplines. Not specialist AI/Data consulting supply or prices.",
}


def _xml(value: object) -> str:
    """Protect ReportLab paragraph markup; preserve Swedish/European text."""
    return escape(str("" if value is None else value), quote=False)


def _clean(value: object) -> str:
    return (str("" if value is None else value)
            .replace("\u2013", "-").replace("\u2014", "-")
            .replace("\u2019", "'").replace("\u00a0", " "))


def _href(url: object) -> str:
    source=str(url or "")
    parsed=urlsplit(source)
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid evidence source hyperlink.")
    return escape(source, quote=True)


def _n(p: dict) -> float:
    value=float(p["value"])
    if not isfinite(value):
        raise ValueError("A reported market observation is not finite.")
    return value


def _num(value: float) -> str:
    value=float(value)
    return f"{int(value):,}" if value.is_integer() else f"{value:,.1f}"


def _measure(p: dict) -> str:
    unit=str(p.get("metric_unit") or "")
    v=_num(_n(p))
    if unit=="percent":return v+"%"
    if unit=="percent YoY":return v+"% YoY"
    if unit=="percentage points":return v+" pp"
    if unit=="advertisements":return v+" ads"
    if unit=="SEK/month":return v+" SEK/mo"
    return v+" "+unit


def _sty():
    base={
      "eyebrow":ParagraphStyle("mr2_eyebrow",fontName="Helvetica-Bold",fontSize=7.8,
           leading=11.2,textColor=COPPER,spaceBefore=0,spaceAfter=7),
      "large":ParagraphStyle("mr2_large",fontName="Times-Roman",fontSize=35,
           leading=40,textColor=NAVY,spaceAfter=10),
      "lead":ParagraphStyle("mr2_lead",fontName="Times-Roman",fontSize=15.1,
           leading=21,textColor=BLUE,spaceAfter=17),
      "chapter":ParagraphStyle("mr2_chapter",fontName="Times-Roman",fontSize=25.5,
           leading=30,textColor=NAVY,spaceBefore=1,spaceAfter=14),
      "sub":ParagraphStyle("mr2_sub",fontName="Helvetica-Bold",fontSize=11.6,
           leading=16,textColor=NAVY,spaceBefore=13,spaceAfter=7),
      "body":ParagraphStyle("mr2_body",fontName="Helvetica",fontSize=9.25,
           leading=15.25,textColor=NAVY,spaceAfter=10),
      "small":ParagraphStyle("mr2_small",fontName="Helvetica",fontSize=8.1,
           leading=12.7,textColor=MUTED,spaceAfter=7),
      "tiny":ParagraphStyle("mr2_tiny",fontName="Helvetica",fontSize=7,
           leading=10.6,textColor=MUTED,spaceAfter=3),
      "label":ParagraphStyle("mr2_label",fontName="Helvetica-Bold",fontSize=8.2,
           leading=11.4,textColor=NAVY,spaceAfter=2),
      "value":ParagraphStyle("mr2_value",fontName="Times-Roman",fontSize=24,
           leading=27.5,textColor=NAVY,alignment=TA_CENTER),
      "value_label":ParagraphStyle("mr2_value_label",fontName="Helvetica",fontSize=7.5,
           leading=11.1,textColor=MUTED,alignment=TA_CENTER),
      "table_h":ParagraphStyle("mr2_tableh",fontName="Helvetica-Bold",fontSize=7.5,
           leading=11,textColor=WHITE),
      "table":ParagraphStyle("mr2_table",fontName="Helvetica",fontSize=7.3,
           leading=11,textColor=NAVY),
      "table_b":ParagraphStyle("mr2_table_b",fontName="Helvetica-Bold",fontSize=7.4,
           leading=11,textColor=NAVY),
      "quote":ParagraphStyle("mr2_quote",fontName="Times-Italic",fontSize=13.5,
           leading=19.5,textColor=BLUE,spaceAfter=5),
      "disclaimer":ParagraphStyle("mr2_disclaimer",fontName="Helvetica",fontSize=7.2,
           leading=11.5,textColor=MUTED,spaceAfter=5),
    }
    return base


def _P(styles, value, kind="body", *, raw=False):
    return Paragraph(str(value) if raw else _xml(value), styles[kind])


def _frame(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(NAVY)
    canvas.rect(0,h-15*mm,w,15*mm,stroke=0,fill=1)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold",8)
    canvas.drawString(18*mm,h-9.3*mm,"JAIR RIBEIRO   /   EXECUTIVE MARKET INTELLIGENCE")
    canvas.setStrokeColor(RULE)
    canvas.line(18*mm,16*mm,w-18*mm,16*mm)
    canvas.setFont("Helvetica",7.8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18*mm,11*mm,"jairribeiro.com    |    AI & Data Market Review")
    canvas.drawRightString(w-18*mm,11*mm,f"EDITION 01   /   {doc.page:02d}")
    canvas.restoreState()


def _section(story,styles,code,title,intro=None):
    story.extend([
        _P(styles,code.upper(),"eyebrow"),
        _P(styles,title,"chapter"),
    ])
    if intro:story.append(_P(styles,intro,"lead"))


def _callout(styles, label, body, *, theme="paper"):
    base=WHITE if theme=="white" else PAPER
    inner=Table([[
        [_P(styles,label.upper(),"eyebrow"),_P(styles,body,"body")]
    ]], colWidths=[PRINT_WIDTH-20])
    inner.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),base),
        ("BOX",(0,0),(-1,-1),0.55,RULE),
        ("LINEBEFORE",(0,0),(0,-1),3,COPPER),
        ("LEFTPADDING",(0,0),(-1,-1),12),
        ("RIGHTPADDING",(0,0),(-1,-1),13),
        ("TOPPADDING",(0,0),(-1,-1),12),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    return inner


def _stats(styles, items):
    if not items:return Spacer(1,4)
    cells=[]
    for name,value in items:
        cells.append([
            _P(styles,value,"value"),
            Spacer(1,5),
            _P(styles,name,"value_label"),
        ])
    table=Table([cells], colWidths=[PRINT_WIDTH/len(cells)]*len(cells))
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),PAPER),
        ("LINEABOVE",(0,0),(-1,0),1.2,COPPER),
        ("INNERGRID",(0,0),(-1,-1),.5,RULE),
        ("BOX",(0,0),(-1,-1),.5,RULE),
        ("TOPPADDING",(0,0),(-1,-1),13),
        ("BOTTOMPADDING",(0,0),(-1,-1),13),
        ("LEFTPADDING",(0,0),(-1,-1),7),
        ("RIGHTPADDING",(0,0),(-1,-1),7),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    return table


def _bar_chart(styles, rows, *, ceiling=None, unit="", colorscheme=BLUE):
    """Accessible vector bar panel with full text labels, numbers and common scale."""
    if not rows:return _P(styles,"No approved comparable data available.","small")
    values=[float(value) for label,value in rows]
    if not all(isfinite(v) and v>=0 for v in values):
        raise ValueError("This evidence chart requires non-negative finite values.")
    maximum=max(float(ceiling or max(values) or 1),1)
    bar_width=76*mm
    left_width=69*mm
    value_width=29*mm
    table_rows=[]
    for label,value in rows:
        v=float(value)
        scale=min(1.,v/maximum)
        chart=Drawing(bar_width,13)
        chart.add(Rect(0,2,bar_width,9,fillColor=PALE,strokeColor=None))
        chart.add(Rect(0,2,max(0.5,bar_width*scale),9,fillColor=colorscheme,strokeColor=None))
        value_label=_num(v)+unit
        table_rows.append([
            _P(styles,label,"table"),
            chart,
            _P(styles,value_label,"table_b"),
        ])
    t=LongTable(table_rows,colWidths=[left_width,bar_width,value_width],hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LINEBELOW",(0,0),(-1,-1),.4,RULE),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),10),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("BACKGROUND",(0,0),(-1,-1),WHITE),
    ]))
    return t


def _structured_table(styles,headers,records,widths):
    cells=[[_P(styles,h,"table_h") for h in headers]]
    for row in records:
        cells.append([_P(styles,x,"table") for x in row])
    t=LongTable(cells,colWidths=widths,repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),BLUE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,PAPER]),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.,GOLD),
        ("LINEBELOW",(0,1),(-1,-1),.3,RULE),
        ("LEFTPADDING",(0,0),(-1,-1),7),
        ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),7),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    return t


def _source_link(styles,point,short):
    url=_href(point["source_url"])
    return _P(styles,f'<link href="{url}" color="#265A7C">{_xml(short)}</link>',"small",raw=True)


def _approved(points,briefs):
    if not points or not briefs:
        raise ValueError("A published evidence set and executive interpretations are required.")
    idx={}
    for p in points:
        code=str(p.get("code") or "")
        if not code or code in idx:
            raise ValueError("Missing or repeated market evidence code.")
        _n(p)
        _href(p.get("source_url"))
        if str(p.get("published_on") or "")>str(p.get("verified_on") or ""):
            raise ValueError("Source verification precedes source publication.")
        idx[code]=p
    seen=set()
    for b in briefs:
        slug=str(b.get("slug") or "")
        if not slug or slug in seen:
            raise ValueError("An executive analysis has a missing or duplicate slug.")
        seen.add(slug)
        refs=b.get("evidence_codes") or []
        if len(refs)<2 or len(set(refs))!=len(refs) or any(x not in idx for x in refs):
            raise ValueError("Unsupported or duplicate executive analysis evidence references.")
        if (b.get("support_level")=="independent_sources"
            and len({idx[c]["source_family"] for c in refs})<2):
            raise ValueError("Independent-source interpretation is not independently supported.")
    return idx


def _get(idx,code):
    return idx.get(code)


def _getval(idx,code):
    p=_get(idx,code)
    return _num(_n(p)) if p else "n/a"


def _jobtech(idx):
    valid=[
        p for p in idx.values()
        if p.get("source_family")=="af_jobtech_target_demand"
        and p.get("series_code")=="jobtech_ai_data_leadership_v1"
        and p.get("metric_unit")=="advertisements"
    ]
    series=defaultdict(dict)
    partial=[]
    for p in valid:
        if not p.get("period_complete"):
            partial.append(p)
            continue
        k=str(p.get("period_start") or "")
        geo=str(p.get("geography") or "")
        earlier=series[k].get(geo)
        # Keep last verified vintage for each monthly geography.
        if earlier is None or str(earlier.get("verified_on"))<=str(p.get("verified_on")):
            series[k][geo]=p
    periods=sorted(series)
    return periods,series,partial


def _source_families(idx):
    out=defaultdict(list)
    for p in idx.values():
        out[str(p["source_family"])].append(p)
    return out


def _issue_date(briefs,edition):
    explicit=str((edition or {}).get("issue_date") or "")
    if explicit:
        try:return date.fromisoformat(explicit[:10]).strftime("%d %B %Y").lstrip("0")
        except ValueError:pass
    published=[str(b.get("published_on"))[:10] for b in briefs if b.get("published_on")]
    try:return date.fromisoformat(max(published)).strftime("%d %B %Y").lstrip("0")
    except (ValueError,TypeError):
        return "16 November 2026"


def _evidence_label(styles,idx,codes):
    labels=[]
    for code in codes:
        p=idx.get(code)
        if p:labels.append(SOURCE_LABEL.get(p["source_family"],p["source_family"]))
    return _P(styles,"EVIDENCE  /  "+", ".join(sorted(set(labels))) if labels
              else "EVIDENCE  /  Not available","eyebrow")


def build_market_review_pdf(points:list[dict],briefs:list[dict],
                            edition:dict|None=None) -> bytes:
    """Build a researched, printable executive edition from the released manifest.

    Optional edition contains *metadata*, never new observations.
    The main public caller only supplies reader-visible RLS-filtered records.
    """
    idx=_approved(points,briefs)
    families=_source_families(idx)
    issue=_issue_date(briefs,edition)
    styles=_sty()
    out=BytesIO()
    doc=SimpleDocTemplate(
        out,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
        topMargin=22*mm,bottomMargin=21*mm,
        title=f"AI & Data Market Review | Edition 01 | {issue}",
        author="Jair Ribeiro | Enterprise AI & Data",
        subject="Source-linked market research for enterprise AI and data leadership",
    )
    story=[]
    def p(txt,style="body"):
        return _P(styles,txt,style)
    def sub(txt):
        story.append(p(txt,"sub"))
    def evidence(txt):
        story.append(p(txt,"small"))
    def page():
        story.append(PageBreak())
    def chart(rows,ceiling=None,unit="",tone=BLUE):
        story.append(_bar_chart(styles,rows,ceiling=ceiling,unit=unit,colorscheme=tone))
        story.append(Spacer(1,11))

    # 01. Cover. Editorial judgment is qualified as an interpretation.
    story.extend([
        Spacer(1,25),
        p("INDEPENDENT RESEARCH  /  SWEDEN  /  EDITION 01","eyebrow"),
        p("AI & Data", "large"),
        p("Market Review", "large"),
        p("What the available evidence supports - and what it cannot establish.","lead"),
        HRFlowable(width="100%",thickness=2,color=COPPER,spaceBefore=5,spaceAfter=18),
        p("Executive research for leaders deciding where to invest in AI, "
          "which Data and Analytics capabilities to build, and how to source "
          "specialist leadership. Based on verified, dated Swedish observations "
          "rather than market forecasts or promotional claims.","body"),
        _stats(styles,[
            ("Enterprise AI use (10+)",_getval(idx,"scb_2026_ai_10plus")+"%"),
            ("Large firms using AI",_getval(idx,"scb_2026_ai_250plus")+"%"),
            ("Oct leadership adverts",_getval(idx,"jobtech_v1_oct_se")),
        ]),
        Spacer(1,25),
        _callout(styles,"The central reading",
             "AI use is visible across Swedish enterprises. This does not tell us "
             "whether organisations are making money, changing workflows or building "
             "durable capability. A narrow AI/Data leadership advertisement series "
             "and broader consulting-market activity are useful context, but neither "
             "provides a measure of specialist skills scarcity or actual hiring."),
        Spacer(1,15),
        p(f"Published {issue}  |  {len(idx)} published observations  |  "
          f"{len(briefs)} executive analyses  |  {len(families)} publisher families","small"),
        p("Scope: only the formally approved edition dataset. Additional staged "
          "indicators are excluded until they pass source review. Method and complete "
          "observation register appear at the end of this document.","disclaimer"),
    ])
    page()

    # 02. Executive summary.
    _section(story,styles,"Executive reading","Four market realities. Four decisions.")
    story.append(p("This is a decision-support publication, not a market forecast. "
        "It weighs direct measurements, derived advertisement counts and "
        "contextual observations separately. The practical question is not "
        "'Is AI growing?' but 'Which capabilities are we responsible for building?'"))
    summaries=[
        ("01 / Adoption is measurable; value is not",
         f"SCB reports {_getval(idx,'scb_2026_ai_10plus')}% AI use among surveyed "
         "enterprises with at least 10 employees. The metric tells us about "
         "reported use, not whether productivity, quality, risk or profit improved.",
         "Demand a baseline, accountable workflow owner and evidence of changed work before scaling expenditure."),
        ("02 / Capability measures need separate denominators",
         "SCB also reports Data and Analytics activity and cites reasons why some "
         "non-adopters declined AI. The barriers describe a subgroup, not all "
         "Swedish businesses or all current AI adopters.",
         "Locate capability gaps in your own workflows, data controls and roles before attributing them to the market."),
        ("03 / Recruitment observations are narrow",
         f"JobTech v1 records {_getval(idx,'jobtech_v1_sep_se')} Swedish title-basket "
         f"advertisements for revised September and {_getval(idx,'jobtech_v1_oct_se')} "
         "for October. These are small samples of published adverts, not filled positions.",
         "Specify the responsibilities and employment model before inferring that an AI leadership role is scarce."),
        ("04 / Consulting signals are broad-market context",
         f"Brainville reports assignments up {_getval(idx,'brainville_202610_assignments_yoy')}% "
         f"and available consultants up {_getval(idx,'brainville_202610_consultants_yoy')}% "
         "year on year in its general Swedish marketplace.",
         "Compare make, hire and contract options on accountabilities and delivery outcomes, not marketplace growth alone."),
    ]
    for title,explanation,action in summaries:
        story.append(KeepTogether([
            p(title,"sub"),p(explanation),p("EXECUTIVE RESPONSE  /  "+action,"small"),
        ]))
    story.append(_callout(styles,"Conclusion",
        "No approved source establishes that AI is causing a national hiring boom, "
        "that consulting specialists are scarce, or that widespread AI adoption "
        "has produced measurable enterprise value. The evidence does support "
        "more disciplined internal decisions about capability, governance and sourcing."))
    page()

    # 03. Method and source coverage.
    _section(story,styles,"Research discipline","What is included - and what is not.")
    story.append(p("Edition 01 contains three distinct research families. They were "
        "reviewed for their original scope, publication vintage and interpretation "
        "limits. They do not form a statistically representative sample of the "
        "whole AI, Data and Analytics economy."))
    family_rows=[]
    for code,kind,scope in [
      ("scb_enterprise_ai_adoption","Official enterprise survey",
       "AI use, analytics and barriers; 2026, Sweden"),
      ("af_jobtech_target_demand","Derived title-basket analysis",
       "Advertised senior AI/Data titles; Jun-Oct complete, Nov partial"),
      ("brainville_consulting_market","First-party marketplace reporting",
       "Consulting assignment and supply growth; Oct 2026"),
    ]:
        pts=families.get(code,[])
        if pts:family_rows.append((SOURCE_LABEL[code],kind,str(len(pts))+" observations",scope))
    story.append(_structured_table(styles,
       ["SOURCE","EVIDENCE TYPE","COVERAGE","MEASUREMENT"],
       family_rows,[29*mm,40*mm,32*mm,73*mm]))
    story.append(Spacer(1,17))
    sub("How the research treats evidence")
    methodology=[
        ("Observed fact","A reported figure with publisher, unit, population and vintage."),
        ("Derived measure","A reproducible filter over a larger public dataset, with exclusions and deduplication."),
        ("Editorial interpretation","A reasoned conclusion that may be challenged and cannot claim more certainty than its inputs."),
        ("Action proposal","A leadership experiment or decision process. It is advice, not a measured market fact."),
    ]
    story.append(_structured_table(styles,["CATEGORY","MEANING"],methodology,[44*mm,130*mm]))
    story.append(Spacer(1,12))
    story.append(p("Important constraints","sub"))
    for item in [
      "SCB changed survey sector coverage and classifications in 2026. Historical comparisons require a separate like-for-like check.",
      "The JobTech v1 basket is a narrow title selection. Search results may be indexed or revised retrospectively; a live replay was not successfully completed at publication.",
      "Brainville's marketplace figures cover many consulting disciplines, not the number, price or skills of AI/Data specialists.",
      "The latest November JobTech observations cover only 1-15 November and are not comparable with complete months or extrapolated into a forecast.",
      "A publisher may appear across several indicators; 30 observations do not mean 30 independent sources. Twenty-four additional staged records are outside this edition.",
    ]:
        story.append(p("- "+item,"small"))
    page()

    # 04. Enterprise AI adoption.
    _section(story,styles,"01  /  Enterprise AI adoption","A visible technology, an unproven return.",
        "AI adoption is widespread enough that leaders should distinguish "
        "access to tools from sustained changes in how work is performed.")
    adoption=[
      ("10-49 employees","scb_2026_ai_10to49"),
      ("50-249 employees","scb_2026_ai_50to249"),
      ("250+ employees","scb_2026_ai_250plus"),
    ]
    a=[(label,_n(idx[code])) for label,code in adoption if code in idx]
    if a:
        sub("Reported AI use by enterprise size (2026)")
        chart(a,ceiling=100,unit="%",tone=BLUE)
    if "scb_2026_ai_10plus" in idx:
        story.append(_stats(styles,[("All enterprises (10+ employees)",
             _getval(idx,"scb_2026_ai_10plus")+"%")]))
        story.append(Spacer(1,12))
    story.extend([
        p("What the data says","sub"),
        p("The same SCB survey shows higher reported AI use in larger "
          "enterprise-size bands. The difference is descriptive. It cannot, "
          "on its own, demonstrate that large firms are more productive, "
          "manage risk better, or realise more value from AI."),
        p("An alternative interpretation","sub"),
        p("Large firms may have greater access to software, training or "
          "specialist functions, but the survey measures reported use, not "
          "quality of deployment or results. Smaller firms may use AI "
          "intensively in fewer workflows; this dataset cannot adjudicate that."),
        p("What an executive should do","sub"),
        p("Ask for three things before approving further spend: a named process "
          "and outcome owner; a before-and-after workflow measure; and evidence "
          "that the new way of working is repeatable. Count changed decisions "
          "and controls, not just accounts or licenses."),
    ])
    if "scb_2026_ai_10plus" in idx:
        story.append(_source_link(styles,idx["scb_2026_ai_10plus"],
             "Original: SCB IT-anvandning i foretag 2026 (5 November 2026)."))
    page()

    # 05. Data and Analytics capability, distinct SCB cohort.
    _section(story,styles,"02  /  Data & Analytics capabilities",
        "Analytics activity is not the same as operating capability.",
        "The survey supplies useful context about Data practice, but these "
        "measures are not interchangeable and must not be combined into a "
        "fictional AI readiness index.")
    cap=[
      ("Enterprises conducting data analysis","scb_2026_data_analytics_use"),
      ("Enterprises with in-house analytics personnel","scb_2026_analytics_internal"),
      ("Enterprises using BI software","scb_2026_bi_use"),
    ]
    rows=[(label,_n(idx[c])) for label,c in cap if c in idx]
    if rows:
        sub("Separate published shares, enterprises with 10+ employees")
        chart(rows,ceiling=100,unit="%",tone=TEAL)
    story.extend([
        p("The credible reading","sub"),
        p("Conducting data analysis, employing analytical staff and using BI "
          "software describe different activities and capabilities. The same "
          "company may appear in more than one measure. Subtracting the "
          "percentages would not estimate a Data maturity gap, an AI capability "
          "deficit or a hiring requirement."),
        p("Why this matters for AI programmes","sub"),
        p("Where AI depends on business data, accountable definitions, "
          "quality checks, authorised access and escalation paths are "
          "operating requirements. The survey supports asking whether these "
          "conditions exist. It does not answer that question for any "
          "specific organisation."),
        p("Practical decision","sub"),
        p("Select one materially important AI-supported workflow. Inspect the "
          "source data, ownership, exception handling and measured outcome. "
          "Decide whether the constraint lies in data stewardship, process "
          "design, user skills, system architecture or sponsorship before "
          "choosing another technology initiative."),
    ])
    if "scb_2026_analytics_internal" in idx:
        story.append(_source_link(styles,idx["scb_2026_analytics_internal"],
                       "Original SCB Data and Analytics indicators."))
    page()

    # 06. Barriers in NON-ADOPTER sub-population only.
    _section(story,styles,"03  /  Barriers to adoption",
        "The strongest reported barrier is expertise - in a specific subgroup.",
        "These shares describe enterprises that considered AI but decided not to "
        "use it. They must never be presented as shares of all Swedish firms.")
    barrier=[
      ("Lack of relevant expertise","scb_2026_ai_expertise_barrier"),
      ("Privacy and data protection concerns","scb_2026_ai_privacy_barrier"),
      ("Data access or quality","scb_2026_ai_data_quality_barrier"),
    ]
    rows=[(label,_n(idx[c])) for label,c in barrier if c in idx]
    if rows:
        sub("Reasons cited by enterprises considering but not adopting AI")
        chart(rows,ceiling=100,unit="%",tone=COPPER)
    story.extend([
        p("An honest interpretation","sub"),
        p("Skills, privacy concerns and access to reliable data are all visible "
          "obstacles in this subgroup. Responses can overlap. Their sum "
          "does not have to equal 100%, and none of these percentages "
          "measures the causal return from a new policy, training programme "
          "or data platform."),
        p("What would contradict a simplistic reading?","sub"),
        p("Many current AI adopters could already have adequate controls; "
          "other businesses may avoid AI rationally because expected benefits "
          "do not justify operational risk. The survey cannot isolate those "
          "cases or establish that every stated concern should be overcome."),
        p("Decision test","sub"),
        p("Rather than issuing broad mandates, ask a business owner to choose "
          "a use case where the expected advantage is explicit. Have the data "
          "and privacy owners identify one pass/fail condition, and the "
          "workforce lead specify the minimum safe operating proficiency."),
        _callout(styles,"A fair governance question",
            "Which control would make a useful AI application acceptable, "
            "and which unresolved risk should stop or defer it? "
            "Governance is accountable decision-making, not a default "
            "argument for either unfettered rollout or permanent prohibition."),
    ])
    page()

    # 07. JobTech title basket national trend.
    periods,series,partial=_jobtech(idx)
    national=[(str(series[m]["Sweden"].get("period_label") or m)[:22],
                _n(series[m]["Sweden"])) for m in periods if "Sweden" in series[m]]
    _section(story,styles,"04  /  Leadership recruitment",
        "An observable title-basket - not a labour-market boom.",
        "This derived measure counts a deliberately selected set of advertised "
        "AI/Data leadership titles. It is useful for following a consistent "
        "definition, not estimating all hiring or labour scarcity.")
    if national:
        sub("Sweden: complete publication months, frozen JobTech classifier v1")
        chart(national,ceiling=max(1,max(x[1] for x in national)),tone=BLUE)
    if len(national)>=2:
        story.append(p(
          "From "+national[0][0]+" ("+_num(national[0][1])+") to "+
          national[-1][0]+" ("+_num(national[-1][1])+"), counts fluctuate "
          "within a small observed series. A percentage jump between two "
          "months would be visually dramatic but substantively easy to "
          "overstate. Historical revisions can also alter the comparisons."))
    else:
        story.append(p("The reviewed set includes too few complete months for "
          "a defensible trend. No trend extrapolation is shown."))
    story.extend([
        p("Alternative explanations","sub"),
        p("Counts can change because employers alter job titles, re-post "
          "advertisements, change recruitment channels or move roles outside "
          "this title classifier. None of these explanations is measured here. "
          "An increase in adverts does not tell us how many were filled."),
        p("What to test in a hiring proposal","sub"),
        p("Separate governance/accountability, operating-model leadership, "
          "Data ownership, commercial AI adoption and hands-on engineering. "
          "Then compare internal succession, a specialist permanent hire, "
          "a time-bound adviser and a supplier against the same mandate."),
    ])
    source=next((p for p in idx.values()
                 if p.get("source_family")=="af_jobtech_target_demand"),None)
    if source:story.append(_source_link(styles,source,
           "JobTech public records and Historical Ads source."))
    page()

    # 08. Geographic signals and partial month.
    _section(story,styles,"05  /  Location & timing",
        "Regional comparisons need the right denominator.",
        "National counts include regional counts. Regions must not be "
        "summed into Sweden, and small regional totals are not reliable "
        "estimates of all vacancies in a labour market.")
    regional=[]
    for m in periods:
        group=series[m]
        if "Sweden" not in group:continue
        regional.append((
           str(group["Sweden"]["period_label"])[:24],
           _num(_n(group["Sweden"])),
           _num(_n(group["Stockholm"])) if "Stockholm" in group else "-",
           _num(_n(group["Västra Götaland"])) if "Västra Götaland" in group else "-",
        ))
    if regional:
        story.append(_structured_table(styles,
            ["COMPLETE MONTH","SWEDEN","STOCKHOLM","VASTRA GOTALAND"],
            regional,[58*mm,34*mm,39*mm,43*mm]))
    story.append(Spacer(1,16))
    sub("The incomplete November observation")
    if partial:
        selected=sorted(partial,key=lambda p:(p.get("geography") or ""))
        txt="; ".join(
            f"{p['geography']}: {_num(_n(p))} adverts"
            for p in selected
        )
        story.append(p("The edition contains a 1-15 November observation: "
                       +txt+". This is not a full month, has no monthly "
                       "run-rate adjustment, and is excluded from the complete-month chart."))
    else:
        story.append(p("No compatible partial-period observations are published in "
                       "the selected edition. A missing partial period is not zero activity."))
    story.extend([
        p("Geography does not equal addressable talent","sub"),
        p("A workplace may recruit remotely or across regions, and some "
          "work can be assigned to teams outside the advertised region. "
          "The data do not measure the availability or willingness of "
          "qualified candidates, nor the time required to fill a role."),
        p("Decision to make","sub"),
        p("Write the actual geographic constraint of your role. Is physical "
          "presence operationally necessary, contractually required or "
          "merely customary? Test a realistic regional and remote hiring "
          "approach before declaring a specialist shortage."),
    ])
    page()

    # 09. Consulting conditions.
    _section(story,styles,"06  /  Consulting & external capability",
        "Marketplace activity is not a price or scarcity index.",
        "A broad marketplace can expand both listed opportunities and "
        "available consultant profiles. These measures cannot identify "
        "the market balance for a specific AI/Data capability.")
    consulting=[
      ("Published consulting assignments, year on year",
       "brainville_202610_assignments_yoy"),
      ("Available consultants, year on year",
       "brainville_202610_consultants_yoy"),
    ]
    rows=[(label,_n(idx[c])) for label,c in consulting if c in idx]
    if rows:
        sub("Brainville, Sweden, October 2026; all consulting disciplines")
        chart(rows,ceiling=max(1,max(v for _,v in rows)),unit="%",tone=TEAL)
    story.extend([
        p("What can be concluded","sub"),
        p("In the publisher's observed marketplace, both the number of "
          "assignments and the pool of available consultants increased "
          "compared with October 2025. Because the two percentages have "
          "different denominators, their difference is not a statistically "
          "valid measure of oversupply, prices or future contract rates."),
        p("What cannot be concluded","sub"),
        p("We cannot identify the number of AI architects, data stewards "
          "or enterprise AI executives seeking contracts, nor their "
          "fees, experience, allocation or time to project. The evidence "
          "also does not establish that organisations should contract "
          "rather than recruit."),
        p("Practical sourcing discipline","sub"),
        p("When comparing suppliers and internal teams, ask each for "
          "a deliverable tied to the same operating outcome. Score "
          "transferability of knowledge, data/control ownership, "
          "ongoing support, security obligations and exit costs. "
          "Price should be evaluated against these conditions, "
          "not against a broad marketplace growth rate."),
    ])
    if rows:
        story.append(_source_link(styles,idx[consulting[0][1]],
           "Brainville October 2026 original market commentary."))
    page()

    # 10. Synthesis without false correlation.
    _section(story,styles,"07  /  Cross-source synthesis",
        "These observations belong to different questions.",
        "A persuasive narrative can be assembled from unrelated percentages. "
        "A credible executive research review should first test whether "
        "the observations are actually comparable.")
    matrix=[
      ("AI adoption is widespread",
       "SCB enterprise survey",
       "Where is reported use happening?",
       "Whether it improves business results."),
      ("Analytics practices exist",
       "SCB analytics/BI measures",
       "Which capabilities are observable?",
       "How mature or useful each capability is."),
      ("Senior AI/Data adverts are visible",
       "JobTech derived title classifier",
       "How a narrowly selected advert basket varies.",
       "Total hires, unadvertised roles or talent shortage."),
      ("Consulting activity is changing",
       "Brainville marketplace",
       "How two broad marketplace cohorts move.",
       "AI-specific supply, fees or capability depth."),
    ]
    story.append(_structured_table(styles,
      ["OBSERVATION","MEASUREMENT","CAN INFORM","CANNOT PROVE"],
      matrix,[38*mm,37*mm,49*mm,50*mm]))
    story.append(Spacer(1,15))
    sub("A balanced reading")
    story.append(p("Two plausible conditions can coexist: AI tools are widely "
      "used, and some organisations still lack an operating design that "
      "makes them valuable. Equally, some organisations may already have "
      "that design. Aggregate survey data cannot adjudicate between them. "
      "The title-basket figures add a view of recruitment advertising, "
      "not a causal explanation of adoption. Broad consulting trends "
      "add procurement context, not a measure of specialist capacity."))
    sub("The decision-making implication")
    story.append(p("A leader should use market evidence to challenge assumptions, "
      "then collect organisation-specific evidence before making the "
      "investment decision. That is more defensible than treating an "
      "industry statistic as a forecast for the company's own outcome."))
    story.append(_callout(styles,"Executive safeguard",
        "Do not infer a shortage from one job-board series, a maturity gap "
        "from subtracting different survey percentages, or a consulting "
        "price trend from two broad-market year-on-year growth rates."))
    page()

    # 11. Authored executive analysis with direct evidence cited.
    _section(story,styles,"08  /  Independent executive interpretation",
        "The question behind each data point.")
    story.append(p("The following interpretations use the edition's authored "
        "analysis records. These are judgments to challenge, not findings "
        "that were directly measured by the publishers. Each includes "
        "the alternative explanation and the boundary of confidence."))
    for i,b in enumerate(briefs,1):
        title=f"{i:02d} / {b.get('title') or 'Executive perspective'}"
        block=[
            p(title,"sub"),
            p(b.get("thesis") or "No published thesis."),
            p("DECISION QUESTION","eyebrow"),
            p(b.get("decision_question") or "The decision is undefined.","body"),
            p("EVIDENCE-LED READING","eyebrow"),
            p(b.get("interpretation") or "No interpretation recorded.","small"),
            p("WHAT COULD CHANGE THE READING","eyebrow"),
            p(b.get("counterevidence") or "No alternative evidence recorded.","small"),
            p("NEXT ACTION","eyebrow"),
            p(b.get("recommended_action") or "No action documented.","small"),
            p("LIMITS: "+str(b.get("limitations") or "Unknown."),"tiny"),
            p("CITED RECORDS: "+", ".join(str(x) for x in b["evidence_codes"]),"tiny"),
        ]
        # Keep heading and thesis together, then let long analyses split.
        story.extend(block)
        story.append(HRFlowable(width="100%",thickness=.5,color=RULE,spaceBefore=6,spaceAfter=9))
    page()

    # 12. Practical actions and decision rights.
    _section(story,styles,"09  /  Leadership decision agenda",
        "Decisions, owners and evidence - not a blanket recommendation.",
        "This is a repeatable discussion framework, not a prescribed "
        "ranking of AI initiatives. Record thresholds before making "
        "a new investment or hiring commitment.")
    agenda=[
      ("1 / Identify the operating outcome",
       "Business executive + process owner",
       "Current workflow baseline, expected service/quality/cost/risk change.",
       "Who owns the result, and what improvement justifies a trial?"),
      ("2 / Locate the limiting capability",
       "Data leader + AI owner",
       "Source-data controls, process maturity, skills and adoption readiness.",
       "Is the constraint technical, operational, regulatory or organisational?"),
      ("3 / Compare the sourcing options",
       "Capability owner + procurement/HR",
       "Internal development, recruitment and time-bound external support against one brief.",
       "Which option transfers capability and preserves accountable ownership?"),
      ("4 / Set the review conditions",
       "Sponsor + risk owner",
       "Leading indicators, outcome measure and failure/stop criteria.",
       "What evidence would cause us to pause, switch approach or stop?"),
    ]
    story.append(_structured_table(styles,
         ["DECISION","ACCOUNTABLE ROLE","MINIMUM EVIDENCE","QUESTION TO RESOLVE"],
         agenda,[36*mm,32*mm,56*mm,50*mm]))
    story.append(Spacer(1,17))
    sub("Suggested 30-day leadership sequence")
    for title,body in [
      ("Week 1 / Establish the baseline",
       "Select one material workflow and define the before state, expected outcomes and risk threshold."),
      ("Week 2 / Confirm the operating gap",
       "Ask business, Data, security and workforce owners to test assumptions against actual records."),
      ("Week 3 / Request comparable options",
       "Evaluate build, hire and partner options against one common scope and exit criteria."),
      ("Week 4 / Make a reversible commitment",
       "Approve a bounded test with an owner, review date and explicit scale/stop decision."),
    ]:
        story.append(KeepTogether([p(title,"sub"),p(body)]))
    page()

    # 13. Scenario watchlist (explicitly not forecasts).
    _section(story,styles,"10  /  What to monitor next",
        "A watchlist of plausible interpretations, not predictions.",
        "The current evidence is insufficient to forecast the AI/Data labour "
        "market or the ROI of a particular programme. These scenarios "
        "describe questions to monitor as new comparable data arrives.")
    watch=[
      ("Broader use, uneven business value",
       "New SCB survey and organisation-level performance evidence.",
       "Do different enterprise groups convert AI availability into measured work outcomes?"),
      ("Leadership titles shift",
       "Further complete JobTech v1 months plus a separately versioned, broader role basket.",
       "Is the narrow series changing, or are comparable roles appearing under other titles?"),
      ("More consulting capacity, uncertain specialism",
       "Discipline-specific assignment and verified consultant skill samples.",
       "Does capacity for enterprise AI governance and Data leadership change?"),
      ("Organisational constraints persist",
       "Repeated measurement of data controls, skills and workflow ownership.",
       "Which barriers are material in your own business rather than in a survey subgroup?"),
    ]
    for scenario,signal,question in watch:
        story.append(KeepTogether([
            p(scenario,"sub"),
            p("RECHECK: "+signal,"small"),
            p("DECISION QUESTION: "+question,"small"),
        ]))
    story.append(_callout(styles,"Publication discipline",
        "New observations must pass source checks and editorial review "
        "before a later edition uses them. New evidence may reverse "
        "the interpretation; it should not silently rewrite this edition."))
    page()

    # 14+. Comprehensive full observation register.
    _section(story,styles,"Appendix A / Source and observation register",
        "All approved data in the edition.")
    story.append(p("The tables below enumerate every approved observation passed to "
       "the report, including completed and partial periods. Codes identify "
       "the exact evidence records used by the dashboard and executive "
       "interpretations. A row is not an independent publisher or a market forecast."))
    for source_code in [
       "scb_enterprise_ai_adoption",
       "af_jobtech_target_demand",
       "brainville_consulting_market",
    ]:
        records=sorted(families.get(source_code,[]),
               key=lambda x:(str(x.get("period_start","")),str(x.get("geography","")),
                             str(x.get("code",""))))
        if not records:continue
        story.append(Spacer(1,12))
        sub(SOURCE_LABEL.get(source_code,source_code)+" / "+str(len(records))+" evidence records")
        story.append(p(SOURCE_COMPARABILITY.get(source_code,"Source methodology is documented per observation."),"small"))
        story.append(_source_link(styles,records[0],
              "Original publisher / source interface - open reference"))
        rows=[]
        for observation in records:
            label=str(observation.get("metric_label") or observation["code"])
            short_code=str(observation["code"])
            when=(str(observation.get("period_label") or "")+
                (" / PARTIAL" if not observation.get("period_complete",True) else ""))
            rows.append((
               label+"\n"+short_code,
               when,
               str(observation.get("geography") or ""),
               _measure(observation),
            ))
        # Table helper converts \n to paragraph spacing separately.
        record_rows=[]
        for label,when,geo,value in rows:
            pieces=label.split("\n",1)
            record_rows.append((
                pieces[0]+" | "+pieces[1],when,geo,value
            ))
        story.append(_structured_table(styles,[
          "INDICATOR / RECORD CODE","PERIOD","GEOGRAPHY","VALUE"],
          record_rows,[74*mm,43*mm,35*mm,22*mm]))
        story.append(Spacer(1,8))
    page()

    # Final page - methods and explicit interpretation boundaries.
    _section(story,styles,"Appendix B / Interpretation and reproducibility",
        "How to challenge this review.")
    for label,body in [
      ("Evidence hierarchy",
       "SCB responses are an official statistical publication; "
       "JobTech v1 counts are this product's derived, reproducible title filter; "
       "Brainville values are its own platform sample. No single category "
       "is interchangeable with another."),
      ("What was checked",
       "The publication manifest, source identities, dates, compatible "
       "reporting units, complete-month periods, evidence-code references "
       "and scope of every authored interpretation were checked in the "
       "editorial release process."),
      ("What was excluded",
       "An unconfirmed SCB IT-specialist figure was withheld. Additional "
       "unapproved skills, wage and services indicators are deliberately "
       "absent. This document does not use private career, recruiter or "
       "portfolio conversion data."),
      ("Update and revision policy",
       "Corrections require a new evidence version and a dated report "
       "release. Archived or partial JobTech readings cannot silently "
       "replace complete-month observations."),
      ("What you should not infer",
       "No causal link between AI adoption and hiring; no quantified "
       "AI consultant shortage; no salary distribution for AI executives; "
       "no evidence that usage proves business ROI; no sector-wide "
       "AI employment forecast."),
      ("Attribution",
       "Jair Ribeiro | Enterprise AI & Data leadership. "
       "Publisher links and evidence-record identifiers appear "
       "in Appendix A. Research conclusions are analytical "
       "interpretations, not statements by the underlying publishers."),
    ]:
        story.append(KeepTogether([p(label,"sub"),p(body)]))
    story.extend([
        Spacer(1,20),
        HRFlowable(width="100%",thickness=1,color=ACCENT,spaceAfter=9),
        p("EDITORIAL PRINCIPLE","eyebrow"),
        p("A useful market report should make a leader more careful with a "
          "decision - not merely more confident about a statistic.","quote"),
        p("This report is independent research and is not legal, recruitment "
          "or investment advice. Observations apply only to their stated "
          "population and time window.","disclaimer"),
    ])

    doc.build(story,onFirstPage=_frame,onLaterPages=_frame)
    result=out.getvalue()
    if not result.startswith(b"%PDF") or len(result)<3500:
        raise ValueError("Market Review PDF did not render correctly.")
    return result
