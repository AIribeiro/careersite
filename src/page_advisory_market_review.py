"""Evidence-led AI & Data Market Review, multi-page vector PDF.

Separate from per-decision notes. All claims come from the curated, referenced,
member-readable publication snapshot, never the private career intelligence tables.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
from html import escape as xml_escape

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

INK=colors.HexColor("#152C42")
SOFT=colors.HexColor("#546D7F")
ACCENT=colors.HexColor("#B17B58")
PAPER=colors.HexColor("#F6F4EF")
LINE=colors.HexColor("#DCD6CE")
GREEN=colors.HexColor("#365E55")
CW=174*mm

def _esc(x: object) -> str:
    return xml_escape(
        str(x if x is not None else "")
        .replace("\u2013","-").replace("\u2014","-").replace("\u2019","'")
        .encode("latin-1","replace").decode("latin-1"),
        quote=False,
    )


def _styles():
    return {
        "kicker": ParagraphStyle("mr_kicker",fontName="Helvetica-Bold",fontSize=8,leading=12,
            textColor=ACCENT,spaceAfter=10),
        "title": ParagraphStyle("mr_title",fontName="Helvetica-Bold",fontSize=28,leading=33,
            textColor=INK,spaceAfter=17),
        "subtitle": ParagraphStyle("mr_subtitle",fontName="Helvetica",fontSize=14,leading=22,
            textColor=INK,spaceAfter=20),
        "section": ParagraphStyle("mr_section",fontName="Helvetica-Bold",fontSize=18,leading=23,
            textColor=INK,spaceBefore=7,spaceAfter=12),
        "h": ParagraphStyle("mr_h",fontName="Helvetica-Bold",fontSize=11,leading=16,
            textColor=INK,spaceBefore=12,spaceAfter=6),
        "p": ParagraphStyle("mr_p",fontName="Helvetica",fontSize=9.5,leading=16,
            textColor=INK,spaceAfter=10),
        "small": ParagraphStyle("mr_small",fontName="Helvetica",fontSize=7.5,leading=12,
            textColor=SOFT,spaceAfter=6),
        "cell": ParagraphStyle("mr_cell",fontName="Helvetica-Bold",fontSize=11,leading=15,
            textColor=INK),
        "numbers": ParagraphStyle("mr_num",fontName="Helvetica-Bold",fontSize=20,leading=27,
            textColor=INK,alignment=TA_CENTER),
        "number_label": ParagraphStyle("mr_numlabel",fontName="Helvetica",fontSize=8,leading=12,
            textColor=SOFT,alignment=TA_CENTER),
    }


def _frame(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(INK)
    canvas.rect(0,h-14*mm,w,14*mm,stroke=0,fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold",8)
    canvas.drawString(18*mm,h-9*mm,"JAIR RIBEIRO  /  RESEARCH & ADVISORY")
    canvas.setStrokeColor(LINE)
    canvas.line(18*mm,15*mm,w-18*mm,15*mm)
    canvas.setFont("Helvetica",8)
    canvas.setFillColor(SOFT)
    canvas.drawString(18*mm,10*mm,"jairribeiro.com  |  AI & Data Market Signals")
    canvas.drawRightString(w-18*mm,10*mm,f"{doc.page:02d}")
    canvas.restoreState()


def _statbox(value,label,styles):
    return [Paragraph(_esc(value),styles["numbers"]),
            Paragraph(_esc(label),styles["number_label"])]


def _metric_table(rows,styles):
    t=Table([[_statbox(v,k,styles) for v,k in rows]],colWidths=[CW/len(rows)]*len(rows))
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),PAPER),
        ("BOX",(0,0),(-1,-1),0.5,LINE),
        ("INNERGRID",(0,0),(-1,-1),0.5,LINE),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),14),
        ("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))
    return t


def _trend(points:list[dict]) -> Drawing:
    """Vector mini chart. A complete period is required for each plotted mark."""
    series=sorted(
        [p for p in points if p.get("series_code")=="jobtech_ai_data_leadership_v1"
         and p.get("geography")=="Sweden" and p.get("period_complete")],
        key=lambda p:p["period_start"],
    )
    if not series or len(series)<3:
        raise ValueError("Three complete publication months required for a market trend.")
    width=CW
    plot_h=142
    draw=Drawing(width,192)
    ymax=max(1.0,max(float(p["value"]) for p in series))
    baseline=38
    left=18
    right=width-12
    slot=(right-left)/len(series)
    for j in range(5):
        y=baseline+j*plot_h/4
        draw.add(Line(left,y,right,y,strokeColor=LINE,strokeWidth=.6))
        draw.add(String(left+2,y+3,str(round(ymax*j/4)),fontName="Helvetica",
                        fontSize=7,fillColor=SOFT))
    for idx,p in enumerate(series):
        n=float(p["value"])
        x=left+slot*(idx+.5)
        barwidth=min(38,slot*.55)
        height=max(1,n/ymax*plot_h)
        draw.add(Rect(x-barwidth/2,baseline,barwidth,height,fillColor=INK,strokeColor=None))
        draw.add(Rect(x-barwidth/2,baseline+height-3,barwidth,3,fillColor=ACCENT,strokeColor=None))
        draw.add(String(x-7,baseline+height+7,str(int(n)),fontName="Helvetica-Bold",
                        fontSize=9,fillColor=INK))
        draw.add(String(x-10,10,str(p["period_start"])[5:7]+"/26",
                        fontName="Helvetica",fontSize=8,fillColor=SOFT))
    return draw


def _source_rows(points:list[dict],styles):
    out=[]
    ordered=sorted(points,key=lambda p:(p["lens"],p["geography"],p["period_end"]))
    for p in ordered:
        out.append(KeepTogether([
            Paragraph(_esc(p["metric_label"])+"  -  "+_esc(p["geography"]),styles["h"]),
            Paragraph(_esc(p["value"])+" "+_esc(p["metric_unit"])+" | "+
                      _esc(p["period_label"])+" | Released "+_esc(p["published_on"])+
                      " | Verified "+_esc(p["verified_on"]),styles["small"]),
            Paragraph("Publisher and scope: "+_esc(p["source_title"])+". "+_esc(p["population_note"]),styles["small"]),
            Paragraph("Limitation: "+_esc(p["caveat"]),styles["small"]),
            Paragraph('<link href="'+xml_escape(p["source_url"],quote=True)+'" color="#205879">'+
                      _esc(p["source_url"])+'</link>',styles["small"]),
            HRFlowable(width="100%",thickness=.4,color=LINE,spaceAfter=6)
        ]))
    return out


def _additional_market_lenses(points:list[dict], styles:dict) -> list:
    """Publish-approved supplemental dashboards and evidence as a vector PDF appendix.

    Each optional observation is included only if present in the released curated
    manifest. Nothing is fetched from the private owner market database.
    """
    idx={p["code"]:p for p in points}
    sets=[
        ("AI skills beyond IT / structural demand",
         ("market_context_20261116_01","market_context_20261116_02"),
         "TechSverige counts AI-related mentions and occupation groups. "
         "These are not unique vacancies, demonstrated skills or a proxy for hiring."),
        ("Employment intentions in adjacent sectors",
         ("market_context_20261116_03","market_context_20261116_04",
          "market_context_20261116_05","market_context_20261116_06",
          "market_context_20261116_07","market_context_20261116_08"),
         "ManpowerGroup Q4 2026 staffing intentions, surveyed in July. "
         "Net outlook is the difference in shares of employers expecting higher and "
         "lower headcount, not an observed recruitment count."),
        ("Management compensation / occupational proxies",
         ("market_context_20261116_09","market_context_20261116_10",
          "market_context_20261116_11","market_context_20261116_12"),
         "SCB 2025 private-sector IT and R&D manager occupational statistics. "
         "These do not constitute AI Director compensation benchmarks."),
        ("ICT sector output and staffing",
         ("market_context_20261116_13","market_context_20261116_14",
          "market_context_20261116_15"),
         "Almega Q2 2026 ICT industry output and employment. These measures "
         "share sector sources and their divergence does not prove AI-driven displacement."),
        ("Consulting work patterns",
         ("market_context_20261116_16","market_context_20261116_17",
          "market_context_20261116_18"),
         "Brainville October 2026 marketplace classifications across all consulting "
         "disciplines, not AI/Data-specific roles."),
        ("Services-sector activity and staffing",
         ("market_context_20261116_19","market_context_20261116_20",
          "market_context_20261116_21","market_context_20261116_22"),
         "Konjunkturinstitutet survey balances and Swedbank/Silf PMI are "
         "different units and periods. They must not be numerically combined."),
    ]
    included=[(name,[idx[k] for k in keys if k in idx],caveat)
              for name,keys,caveat in sets if any(k in idx for k in keys)]
    if not included:return []
    p=lambda content,sty="p":Paragraph(_esc(content),styles[sty])
    story=[
        PageBreak(),
        p("SUPPLEMENT / FURTHER MARKET INTELLIGENCE","kicker"),
        p("Additional approved market lenses","title"),
        p("These measures expand context around enterprise AI and Data investment. "
          "Each comes from the approved edition manifest, and each retains its "
          "original unit, reporting period, population and source. "
          "They are not combined into a single market score.","p"),
    ]
    for label,records,caveat in included:
        story.append(p(label,"section"))
        for item in records:
            number=float(item["value"])
            shown=f"{int(number):,}" if number.is_integer() else f"{number:,.1f}"
            story.append(KeepTogether([
                p(item["metric_label"],"h"),
                p(shown+" "+item["metric_unit"]+"  |  "+item["period_label"],"p"),
                p("Scope: "+item["population_note"],"small"),
                p("Source: "+item["source_title"]+"  |  Released "+str(item["published_on"])+
                  "  |  Verified "+str(item["verified_on"]),"small"),
            ]))
        story.append(p(caveat,"small"))
        story.append(HRFlowable(width="100%",thickness=.55,color=LINE,spaceAfter=9))
    return story


def market_review_pdf(points:list[dict], briefs:list[dict]) -> bytes:
    """Publisher-traceable executive market review, with no unsupported real-time claims."""
    if not points or not briefs:
        raise ValueError("Curated evidence and authored interpretations required.")
    evidence={str(p["code"]):p for p in points}
    if len(evidence)!=len(points):
        raise ValueError("Duplicate market evidence identifiers.")
    for b in briefs:
        refs=b.get("evidence_codes") or []
        if len(refs)<2 or any(c not in evidence for c in refs):
            raise ValueError("Market report includes an unsupported interpretation.")
        if b["support_level"]=="independent_sources" and len({evidence[x]["source_family"] for x in refs})<2:
            raise ValueError("Claim of cross-source evidence is not supported.")
    s=_styles()
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
                          topMargin=25*mm,bottomMargin=20*mm,
                          title="AI and Data Market Review - 16 November 2026",
                          author="Jair Ribeiro | Enterprise AI & Data Leader")
    def paragraph(txt,sty="p"): return Paragraph(_esc(txt),s[sty])
    def find(code):
        x=evidence.get(code)
        if x is None: raise ValueError("Required published evidence not available: "+code)
        return x
    scb10=find("scb_2026_ai_10plus")
    scb250=find("scb_2026_ai_250plus")
    oct_se=find("jobtech_v1_oct_se")
    oct_vgr=find("jobtech_v1_oct_vgr")
    story=[
        paragraph("THE EXECUTIVE MARKET REVIEW  /  EDITION 01","kicker"),
        paragraph("AI & Data Market Signals","title"),
        paragraph("Sweden's AI adoption is expanding. What do the demand, capability and consulting signals actually support?","subtitle"),
        HRFlowable(width="100%",thickness=2,color=ACCENT,spaceAfter=20),
        _metric_table([
            (f'{int(scb10["value"])}%',"Enterprises using AI (10+)"),
            (f'{int(scb250["value"])}%',"Large enterprises using AI"),
            (f'{int(oct_se["value"])}',"Oct leadership title-basket ads"),
            (f'{int(oct_vgr["value"])}',"Of these in Västra Götaland"),
        ],s),
        Spacer(1,18),
        paragraph("The editorial position","section"),
        paragraph(
            "AI use is extensive in Swedish enterprises, but adoption alone does not establish "
            "whether a company has the leadership, Data and governance capacity to sustain business value. "
            "A small, narrowly defined JobTech leadership advertisement series is observable. "
            "It is not a census of AI vacancies and cannot prove that AI recruitment or investment is surging."
        ),
        paragraph("Four decisions worth testing","section"),
    ]
    for i,b in enumerate(briefs,1):
        story.append(paragraph(f"{i:02d}. "+b["decision_question"],"h"))
        story.append(paragraph(b["recommended_action"]))
    story.extend([
        Spacer(1,10),
        paragraph("Evidence standard", "h"),
        paragraph(
            "All observations have publisher links, dates, defined populations and limitations. "
            "Two independent source families can support a coherent interpretation without independently "
            "verifying the same statistic. No personal career analytics or individual offer forecasts are used.",
            "small",
        ),
        PageBreak(),
        paragraph("01 / Leadership demand", "kicker"),
        paragraph("A narrow hiring signal, not a job-market census","section"),
        paragraph("Full publication months, Sweden. Frozen JobTech headline-only title-basket v1; "
                  "duplicate adverts removed using the documented stable identifiers. "
                  "No projection is made from the incomplete November cohort."),
        _trend(points),
        Spacer(1,8),
        paragraph("Interpretation","h"),
        paragraph("The count was 20 in revised September 2026 and 29 in October. "
                  "The small samples and retrospective API indexing prevent a defensible market-wide "
                  "growth estimate from these two periods."),
        paragraph("Regional distinction","h"),
        paragraph("Västra Götaland counts four qualifying advertisements in revised September and five in October. "
                  "Do not infer regional demand for every senior AI role or a hiring conversion rate."),
        paragraph("A prudent next action","h"),
        paragraph("Describe the capability first: AI governance and ownership, adoption and process redesign, "
                  "AI portfolio leadership, or Data/Analytics management. Benchmark only like-for-like titles "
                  "and employment settings before drawing recruitment conclusions."),
        paragraph("Source: Arbetsförmedlingen JobTech Historical Ads and active JobSearch, original v1 classification; "
                  "rechecked 16 November 2026. Source hyperlinks and observation records are in the appendix.","small"),
        PageBreak(),
        paragraph("02 / Organisational readiness","kicker"),
        paragraph("Adoption is not a capability audit","section"),
        paragraph("The survey denominator matters. Enterprise AI use, internal analytical capability, "
                  "and barriers reported by non-adopters describe distinct groups."),
    ])
    core=[
        ("Companies reporting AI use (10+ employees)",49),
        ("Large enterprises reporting AI use (250+)",85),
        ("Businesses with own data analytics personnel",33),
        ("Non-adopters considering AI citing expertise gaps",62),
    ]
    for name,value in core:
        matches=[p for p in points if p.get("metric_label")==name]  # may use authored label
        story.append(paragraph(f"{value}%  -  {name}","h"))
        story.append(paragraph(
            "Source: SCB IT-användning i företag 2026. These percentages use the survey's "
            "published populations, which are not all identical.","small"
        ))
    story.extend([
        Spacer(1,9),
        paragraph("An executive check","section"),
        paragraph("For each material AI initiative, ask whether the operating owner is named, "
                  "the workflow outcome is measurable, the data inputs are stewarded, and "
                  "capability gaps have a funded resolution path. A technology rollout is not evidence of adoption."),
        PageBreak(),
        paragraph("03 / Commercial conditions","kicker"),
        paragraph("A broader consulting signal—not AI hiring evidence","section"),
        paragraph("Brainville's October 2026 Swedish marketplace overview shows consulting assignments "
                  "up 10.7% year on year and available consultants up 18.5% year on year. "
                  "This is the overall marketplace, not a measure of AI consultants or Director-level demand."),
        paragraph("What leaders can do","h"),
        paragraph("Run a small capability sourcing exercise against the same six-month business outcome: "
                  "internal build, recruitment and selective external support. Compare delivery responsibility, "
                  "knowledge transfer, controls and ongoing operating cost rather than extrapolating "
                  "from economy-wide consulting statistics."),
        paragraph("Confidence boundary","h"),
        paragraph("There is no defensible AI-specific consulting assignment count in the curated dataset. "
                  "Neither marketplace growth nor graduate unemployment can substitute for a verified "
                  "skills-level or engagement-level sample."),
        PageBreak(),
        paragraph("04 / Decision agenda","kicker"),
        paragraph("A practical record for your leadership team","section"),
        paragraph("Use these fields to prepare an accountable discussion; this review does not issue "
                  "a universal recommendation to hire, outsource, stop or expand an AI initiative."),
    ])
    agenda=[
        ("Business outcome and current baseline","________________________________________________________________"),
        ("Capability the organisation must own","________________________________________________________________"),
        ("Strongest alternative to external hiring","________________________________________________________________"),
        ("Evidence missing before commitment","________________________________________________________________"),
        ("Data/governance responsibility","________________________________________________________________"),
        ("Owner, next action and review date","________________________________________________________________"),
        ("Threshold that would reverse this decision","________________________________________________________________"),
    ]
    for label,blank in agenda:
        story.append(paragraph(label,"h"))
        story.append(paragraph(blank))
    story.extend(_additional_market_lenses(points,s))
    story.extend([
        Spacer(1,11),
        paragraph("APPENDIX  /  FULL VERIFIABLE EVIDENCE REGISTER","kicker"),
        PageBreak(),
        paragraph("Source and observation register","title"),
        paragraph("Every listed measure is part of the curated review snapshot. "
                  "Do not apply these figures outside their declared geography, population and time window."),
    ])
    story.extend(_source_rows(points,s))
    doc.build(story,onFirstPage=_frame,onLaterPages=_frame)
    result=out.getvalue()
    if not result.startswith(b"%PDF") or len(result)<3000:
        raise ValueError("Failed to render a valid market review PDF.")
    return result
