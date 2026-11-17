"""Public, source-grounded historical Market Observatory demonstration.

Oldest usable complete months in the approved title basket are June-August
2026. The SCB and Brainville edition evidence was published later and is
deliberately NOT retroactively imported into this historical sample.

This public sample makes no authenticated database calls and contains no
personal job-search, employer-contact or career information.
"""
from __future__ import annotations

from functools import lru_cache
from datetime import date
from html import escape
from io import BytesIO

import streamlit as st
from reportlab.graphics.shapes import Drawing,Rect,String,Line
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,
    HRFlowable,PageBreak,KeepTogether
)

from site_components import nav,footer
from page_public_services import SERVICES_CSS

INK=colors.HexColor("#152E44")
PAPER=colors.HexColor("#F6F3EC")
ACCENT=colors.HexColor("#AB7753")
MUTED=colors.HexColor("#566979")
RULE=colors.HexColor("#DDD7CE")
WIDTH=174*mm
JOBTECH_URL="https://historical.api.jobtechdev.se/search"
DEMO_SOURCE_CHECKED="2026-11-16"
DEMO_CREATED="2026-11-17"

# Approved historical observations, extracted from the publicly reviewed
# JobTech v1 basket; manually frozen for demo reproducibility.
EARLIEST_COMPLETE_MONTHS=(
    ("June 2026", "Sweden",12),("June 2026","Stockholm",6),
    ("June 2026","Västra Götaland",2),
    ("July 2026","Sweden",15),("July 2026","Stockholm",8),
    ("July 2026","Västra Götaland",2),
    ("August 2026","Sweden",10),("August 2026","Stockholm",6),
    ("August 2026","Västra Götaland",1),
)
MONTHS=("June 2026","July 2026","August 2026")
REGIONS=("Sweden","Stockholm","Västra Götaland")

DEMO_CSS="""
<style>
.market-demo-hero {background:#11283D;color:#fff;padding:clamp(43px,7vw,83px) 0}
.market-demo-hero .eyebrow {color:#E6B690;font-size:11px;letter-spacing:.17em;font-weight:800;text-transform:uppercase}
.market-demo-hero h1 {font:500 clamp(34px,5vw,64px)/1.13 Georgia,serif;color:white;
 margin:16px 0;max-width:970px;white-space:normal!important;overflow-wrap:anywhere}
.market-demo-hero p {max-width:780px;color:#D6E0E8;font-size:17px;line-height:1.7}
.market-demo-content {background:#FCFAF6;padding:clamp(38px,6vw,64px) 0}
.market-demo-content h2 {font:500 clamp(27px,3.2vw,43px)/1.2 Georgia,serif;
 color:#1B3347;white-space:normal!important}
.market-demo-content p {font-size:15px;line-height:1.8;color:#516475;max-width:850px}
.market-demo-facts {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;margin:28px 0}
.market-demo-facts div {background:#fff;border:1px solid #D8D4CD;padding:24px;min-width:0}
.market-demo-facts strong {display:block;color:#1B344C;font:500 41px/1.2 Georgia,serif}
.market-demo-facts span {font-size:12px;color:#5C7082}
.market-demo-method {border-left:3px solid #AD7956;background:#F0ECE5;padding:21px 25px}
.market-demo-method p {font-size:13px;margin:4px 0;line-height:1.8}
.market-demo-hero-links{display:flex;gap:12px 25px;flex-wrap:wrap;align-items:center;margin:25px 0 0!important}
.market-demo-hero-links a{font-size:13px;font-weight:800;line-height:1.5;color:#f0c8a9!important;text-decoration:underline;text-underline-offset:5px}
.market-demo-hero-links a:hover,.market-demo-hero-links a:focus-visible{color:#fff!important}
.market-demo-inline-download{margin:24px 0 0!important}
.market-demo-inline-download a{color:#193a53!important;font-weight:800;font-size:14px;text-decoration:underline;text-underline-offset:5px}
.market-demo-inline-download a:focus-visible{outline:2px solid #a97755;outline-offset:4px}
#market-demo-pdf{scroll-margin-top:20px}
.market-demo-breadcrumb{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 31px;color:#d5dfe7;font-size:12px;line-height:1.6}
.market-demo-breadcrumb a{color:#edbb96!important;text-decoration:none!important;font-weight:700}
.market-demo-breadcrumb a:hover,.market-demo-breadcrumb a:focus-visible{text-decoration:underline!important}
.market-demo-breadcrumb [aria-current=page]{color:#fff}
.st-key-market_demo_native_download{max-width:1120px;margin:2px auto 44px;padding:clamp(22px,3vw,38px);background:#fffefa;border:1px solid #ddd6ca;border-top:3px solid #ad7956}
.st-key-market_demo_native_download .market-demo-download-kicker{font-size:10px;letter-spacing:.15em;color:#996743;font-weight:800}
.st-key-market_demo_native_download .market-demo-download-title{font:500 clamp(27px,3vw,40px)/1.19 Georgia,serif;color:#1b3347;margin:12px 0}
.st-key-market_demo_native_download .market-demo-download-lead{font-size:14px;line-height:1.75;color:#506678;max-width:800px;margin:0 0 20px}
.st-key-market_demo_native_download [data-testid=stDownloadButton] button{min-height:50px;background:#163249!important;color:#fff!important;border-color:#163249!important;font-weight:750}
.st-key-market_demo_native_download [data-testid=stDownloadButton] button:hover{background:#2b516b!important}
.site .market-demo-end{background:#f4f0e9;padding:clamp(45px,6vw,77px) 0;border-top:1px solid #ded6ca}
.site .market-demo-end .market-demo-end-kicker{font-size:11px;color:#956744;letter-spacing:.14em;font-weight:800;text-transform:uppercase;margin:0 0 12px}
.site .market-demo-end h2{font:500 clamp(29px,3.6vw,46px)/1.15 Georgia,serif;color:#193249;margin:0 0 12px}
.site .market-demo-end .market-demo-end-lead{font-size:15px;line-height:1.75;color:#536678;max-width:760px;margin:0 0 28px}
.site .market-demo-end-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.site .market-demo-next-card{display:block;min-width:0;padding:clamp(22px,3vw,32px);background:#fffefa;border:1px solid #d9d2c8;text-decoration:none!important}
.site .market-demo-next-card:hover,.site .market-demo-next-card:focus-visible{border-color:#ad7956}
.site .market-demo-next-card--featured{background:#183348;border-color:#183348}
.site .market-demo-next-card small{font-size:10px;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:#976947}
.site .market-demo-next-card--featured small{color:#edbb99}
.site .market-demo-next-card h3{font:500 clamp(22px,2.5vw,30px)/1.23 Georgia,serif;color:#1b3347;margin:14px 0}
.site .market-demo-next-card--featured h3{color:#fff}
.site .market-demo-next-card p{font-size:13px;line-height:1.68;color:#526579;margin:0 0 22px}
.site .market-demo-next-card--featured p{color:#d0dae2}
.site .market-demo-next-link{font-size:13px;font-weight:800;color:#996744}
.site .market-demo-next-card--featured .market-demo-next-link{color:#edbc98}
.site .market-demo-end-home{display:inline-flex;margin-top:26px;color:#2f5168!important;font-size:13px;font-weight:700;text-decoration:underline;text-underline-offset:4px}

@media(max-width:710px) {.market-demo-facts,.site .market-demo-end-grid {grid-template-columns:1fr}.market-demo-breadcrumb{gap:7px;margin-bottom:23px}.st-key-market_demo_native_download{margin:2px 0 37px;padding:22px 17px}}
</style>
"""


def _P(styles,text,kind="body"):
    return Paragraph(escape(str(text)),styles[kind])


def _styles():
    return {
        "kicker":ParagraphStyle("smpk",fontName="Helvetica-Bold",fontSize=8,leading=12,
                textColor=ACCENT,spaceAfter=9),
        "hero":ParagraphStyle("smph",fontName="Times-Roman",fontSize=33,leading=40,
                textColor=INK,spaceAfter=16),
        "chapter":ParagraphStyle("smpc",fontName="Times-Roman",fontSize=24,leading=30,
                textColor=INK,spaceAfter=13),
        "section":ParagraphStyle("smps",fontName="Helvetica-Bold",fontSize=12,leading=17,
                textColor=INK,spaceBefore=13,spaceAfter=7),
        "body":ParagraphStyle("smpb",fontName="Helvetica",fontSize=9.4,leading=16,
                textColor=INK,spaceAfter=11),
        "small":ParagraphStyle("smpx",fontName="Helvetica",fontSize=8,leading=13,
                textColor=MUTED,spaceAfter=8),
        "table":ParagraphStyle("smpt",fontName="Helvetica",fontSize=9,leading=13,textColor=INK),
    }


def _frame(canv,doc):
    canv.saveState()
    w,h=A4
    canv.setFillColor(INK)
    canv.rect(0,h-15*mm,w,15*mm,fill=1,stroke=0)
    canv.setFont("Helvetica-Bold",8)
    canv.setFillColor(colors.white)
    canv.drawString(18*mm,h-9.7*mm,"JAIR RIBEIRO   /   HISTORICAL MARKET OBSERVATORY")
    canv.setFillColor(MUTED)
    canv.setFont("Helvetica",7.7)
    canv.drawString(18*mm,10*mm,"jairribeiro.com  |  Public research sample")
    canv.drawRightString(w-18*mm,10*mm,f"ARCHIVE DEMO   /   {doc.page:02d}")
    canv.setStrokeColor(RULE)
    canv.line(18*mm,15*mm,w-18*mm,15*mm)
    canv.restoreState()


def _historical_national_chart(months:list[str], lookup:dict) -> Drawing:
    """Print-ready labelled bars for the original national cohort only."""
    width=WIDTH
    height=122
    bar_bottom=28
    max_count=max(1,max(int(lookup.get((m,"Sweden"),0)) for m in months))
    chart=Drawing(width,height)
    chart.add(Line(0,bar_bottom,width,bar_bottom,strokeColor=RULE))
    slot=width/max(1,len(months))
    for i,month in enumerate(months):
        n=int(lookup.get((month,"Sweden"),0))
        x=slot*(i+.5)
        bar_h=80*n/max_count
        chart.add(Rect(x-21,bar_bottom,42,max(1,bar_h),fillColor=INK,strokeColor=None))
        chart.add(Rect(x-21,bar_bottom+bar_h-3,42,3,fillColor=ACCENT,strokeColor=None))
        chart.add(String(x-6,bar_bottom+bar_h+7,str(n),fontName="Helvetica-Bold",
                         fontSize=11,fillColor=INK))
        chart.add(String(x-17,8,date.fromisoformat(month+"-01").strftime("%b %Y"),
                         fontName="Helvetica",fontSize=8,fillColor=MUTED))
    return chart


def _records_for_month(points:list[dict],month_label:str) -> dict[str,int]:
    out={}
    for point in points:
        if str(point["period_label"]).startswith(month_label.split()[0]) and (
            month_label.split()[1] in str(point["period_label"])
        ):
            out[str(point["geography"])]=int(point["value"])
    return out


def _strict_historical_points(points:list[dict]) -> list[dict]:
    if not points:
        raise ValueError("Historic report requires actual verified observations.")
    names=set()
    for p in points:
        code=str(p.get("code") or "")
        if not code or code in names:
            raise ValueError("Historic report contains duplicate or missing identifiers.")
        names.add(code)
        if (p.get("source_family")!="af_jobtech_target_demand"
           or p.get("series_code")!="jobtech_ai_data_leadership_v1"
           or p.get("period_complete") is not True
           or p.get("metric_unit")!="advertisements"
           or not str(p.get("source_url","")).startswith("https://")):
            raise ValueError("Historic report cannot include later or incompatible evidence.")
    return points


def historical_market_pdf(points:list[dict],*,month_label:str) -> bytes:
    """Independent historical analysis: executive content first, audit last.

    A narrow JobTech title basket must never be presented as broad national
    AI recruitment. All numerical comparisons are generated from the exact
    approved input vintage; no current market figures or private user data
    enter the public report.
    """
    from market_publication_design import (
        P, assemble, bars, decision_table, metric_cards, panel,
        section, sources_table, styles,
    )
    points=_strict_historical_points(points)
    months=sorted({str(p["period_start"])[:7] for p in points})
    lookup={(str(p["period_start"])[:7],str(p["geography"])):int(p["value"])
            for p in points}
    if any(("Sweden" not in {p["geography"] for p in points
              if str(p["period_start"])[:7]==month}) for month in months):
        raise ValueError("A complete national observation is required.")
    series=[(date.fromisoformat(m+"-01").strftime("%B %Y"),
             lookup[(m,"Sweden")]) for m in months]
    first,last=series[0][1],series[-1][1]
    single=len(series)==1
    date_span=month_label.replace("–","-")
    sample_trend=(
        "The selected national advertisement basket records "
        +", ".join(str(n) for _,n in series)
        +" qualifying advertisements across the archived complete months."
        if not single else
        "This edition contains one complete month and establishes a dated "
        "observation, not a trend."
    )
    cover={
        "title":"AI & Data Market Review",
        "subtitle":(date_span+" | The senior leadership hiring signal - "
                    "what a narrow historical sample can really tell us"),
        "assessment":(
            sample_trend+" The numbers help challenge a hiring assumption, "
            "but they cannot establish total AI vacancies, candidate scarcity "
            "or completed recruitment. A useful executive response is to "
            "define the capability first, then compare how to obtain it."
        ),
        "edition":"PUBLIC RESEARCH / HISTORICAL EDITION",
        "issue":"17 NOVEMBER 2026",
        "question":"Are we short of AI leadership capacity, or have we defined the work and the search too narrowly?",
        "metrics":[
            (str(series[0][1]),"First observed month",series[0][0]+" | Selected ads"),
            (str(max(n for _,n in series)),"Highest monthly count",
             "Within the defined sample only"),
            (str(series[-1][1]),"Last observed month",series[-1][0]+" | Selected ads"),
        ],
    }
    sty=styles()
    story=[]

    # PAGE 2: the argument and the evidence must be adjacent. A title page
    # followed by multiple caution pages would make the sample unworthy of
    # an executive's time.
    section(story,"01 / Executive reading",
        "The signal is small. The management question is not.",
        "A three-month record of selected AI and Data leadership advertisements "
        "is enough to challenge assumptions - not enough to declare a national "
        "hiring boom or shortage.",sty=sty)
    story.append(metric_cards([
        (str(n),"Selected advertisements",m+" | Sweden")
        for m,n in (series+[series[-1]]*3)[:3]
    ],sty=sty))
    story.append(Spacer(1,18))
    story.append(P("Selected national leadership-title advertisements",
                   "h2",sty=sty))
    if single:
        story.append(panel("Evidence discipline","One month is not a market trend",
          "The count is a dated baseline. To assess direction, compare it with "
          "other complete months captured through the same title classifier.",
          sty=sty))
    else:
        story.append(bars([(m.split()[0],n) for m,n in series],
                          suffix=" ads",sty=sty))
        story.append(Spacer(1,11))
        story.append(panel("Executive interpretation",
            "Do not confuse the change in advertised titles with the demand for AI capability",
            "A rise or fall inside a small, headline-classified sample can reflect "
            "role naming, advertising channels, timing, indexing changes or a real "
            "shift in recruiting. The counts alone cannot distinguish these explanations.",
            sty=sty))
    story.append(Spacer(1,15))
    story.append(P("What this changes in a leadership discussion","h2",sty=sty))
    story.append(P(
        "When executives see AI adoption accelerating, it is tempting to assume "
        "that the market for dedicated AI leaders must be expanding at the same pace. "
        "This evidence does not support that shortcut. Before approving new headcount, "
        "name the enterprise decisions the role would own, the outcomes it must "
        "change and the alternative ways the capability could be secured.",
        "body",sty=sty))
    story.append(PageBreak())

    # PAGE 3: regional evidence and multiple interpretations.
    section(story,"02 / Geography and interpretation",
        "A regional count is a sourcing constraint, not a talent forecast",
        "National and regional advertisements belong to the same dataset; "
        "Stockholm and Västra Götaland are subsets of Sweden, not additional "
        "vacancies to be added to the national count.",sty=sty)
    records=[]
    for m in months:
        label=date.fromisoformat(m+"-01").strftime("%b %Y")
        national=lookup[(m,"Sweden")]
        stockholm=lookup.get((m,"Stockholm"))
        vgr=lookup.get((m,"Västra Götaland"))
        records.append((label,national,stockholm,vgr))
    head=[P(x,"table_head",sty=sty) for x in
          ("MONTH","SWEDEN","STOCKHOLM","VÄSTRA GÖTALAND")]
    table_rows=[head]
    for month,n,sto,vgr in records:
        table_rows.append([
            P(month,"table_bold",sty=sty),
            P(str(n),"table",sty=sty),
            P(str(sto) if sto is not None else "Not observed","table",sty=sty),
            P(str(vgr) if vgr is not None else "Not observed","table",sty=sty),
        ])
    regional=Table(table_rows,colWidths=[43*mm,32*mm,42*mm,55*mm])
    regional.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#142B3D")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),
         [colors.white,colors.HexColor("#F5F2EC")]),
        ("LINEBELOW",(0,1),(-1,-1),.4,colors.HexColor("#DADFDC")),
        ("TOPPADDING",(0,0),(-1,-1),13),
        ("BOTTOMPADDING",(0,0),(-1,-1),13),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(regional)
    story.append(Spacer(1,19))
    story.append(panel("Our reading",
       "Smaller local counts warrant a wider search design, not a scarcity claim",
       "A small monthly number does not measure the number of qualified people, "
       "unadvertised searches or the ability to operate across sites. Treat "
       "geography as a negotiable business requirement where the work permits it.",
       sty=sty))
    story.append(Spacer(1,16))
    for h,b in [
        ("Alternative explanation: the role is advertised under another name",
         "Enterprise AI responsibility may sit inside operations, analytics, "
         "product, digital or process improvement rather than a job title that "
         "explicitly contains AI."),
        ("Alternative explanation: recruitment is not publicly advertised",
         "Executive search, internal appointment and specialist contract channels "
         "are not captured by the title-basket totals."),
        ("What would strengthen the finding",
         "Several complete comparable months, broader role classification, "
         "independent recruitment evidence and actual appointment data would "
         "provide firmer support than one small series."),
    ]:
        story.append(KeepTogether([P(h,"h2",sty=sty),
                                   P(b,"body_compact",sty=sty)]))
    story.append(PageBreak())

    # PAGE 4: decision support, rather than a generic disclaimer catalogue.
    section(story,"03 / Management decisions",
        "Four decisions worth making before the next recruitment request",
        "Use the historical figures as a challenge to the hiring case, then "
        "introduce your organisation's own operational and workforce evidence.",
        sty=sty)
    story.append(decision_table([
        ("Define the missing capability","CEO / AI sponsor","Now",
         "Write the outcome and decision rights first: governance, investment "
         "prioritisation, adoption, data ownership, or technical delivery. "
         "Do not let the job title substitute for the mandate."),
        ("Make sourcing options comparable","CHRO / Capability owner","Next 30 days",
         "Compare a permanent appointment, internal development and a defined "
         "external engagement against the same six-month business result."),
        ("Challenge geography and presence","HR / Business operations","Before advertising",
         "Document which responsibilities require physical proximity or a "
         "specific language, and widen the search where those constraints "
         "are not operationally necessary."),
        ("Establish the reversal test","CFO / Hiring sponsor","Next review",
         "Specify which recruitment, performance or business evidence "
         "would make you change the hiring plan rather than defending the "
         "original assumption."),
    ],sty=sty))
    story.append(Spacer(1,18))
    story.append(panel("Boardroom question",
        "Are we short of AI leaders - or have we defined the work and the search too narrowly?",
        "The practical output is a capability decision with accountable ownership, "
        "a sourcing comparison and an evidence threshold for revisiting the choice.",
        sty=sty))
    story.append(Spacer(1,16))
    story.append(P("A practical starting rule","h2",sty=sty))
    story.append(metric_cards([
        ("BUILD","Permanent capability","Own repeated, decision-critical work internally."),
        ("CONTRACT","Time-bound expertise","Require a handover, exit terms and retained accountability."),
        ("TEST","Unproven mandate","Validate the business outcome before committing to a position."),
    ],sty=sty))
    story.append(PageBreak())

    # PAGE 5: transparency remains complete, but is no longer the product.
    section(story,"04 / Evidence and audit",
        "Source and audit trail",
        "This register reproduces every included observation. Its scope is "
        "limited to JobTech's frozen senior AI/Data title basket; no subsequent "
        "SCB adoption or consulting-market publication has been backdated.",
        sty=sty)
    # A grouped audit table is easier to read than repeating the same
    # publisher nine times. It still contains each approved observation code.
    audit=[[P("PERIOD","table_head",sty=sty),
            P("THREE GEOGRAPHIES / FROZEN SOURCE IDENTIFIERS","table_head",sty=sty)]]
    for month in months:
        label=date.fromisoformat(month+"-01").strftime("%B %Y")
        bucket=sorted(
            [p for p in points if str(p["period_start"])[:7]==month],
            key=lambda p:("Sweden","Stockholm","Västra Götaland").index(p["geography"])
            if p["geography"] in REGIONS else 9
        )
        summary="  |  ".join(
            p["geography"]+": "+str(int(p["value"]))+" ads"
            for p in bucket
        )
        codes="  /  ".join(p["code"] for p in bucket)
        audit.append([
            P(label,"table_bold",sty=sty),
            [P(summary,"table",sty=sty),P(codes,"table_small",sty=sty)]
        ])
    ledger=Table(audit,colWidths=[42*mm,130*mm],repeatRows=1)
    ledger.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#142B3D")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),
         [colors.white,colors.HexColor("#F5F2EC")]),
        ("LINEBELOW",(0,1),(-1,-1),.5,colors.HexColor("#DADFDC")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),13),
        ("BOTTOMPADDING",(0,0),(-1,-1),13),
        ("LEFTPADDING",(0,0),(-1,-1),9),
        ("RIGHTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(ledger)
    story.append(Spacer(1,11))
    story.append(Paragraph(
      '<link href="'+JOBTECH_URL+'" color="#1F5773">'
      'JobTech Historical Ads - original publisher query</link>',
      sty["source"]))
    story.append(Spacer(1,12))
    story.append(P("The measurement boundary","h2",sty=sty))
    story.append(P(
        "Headline-only role classification, source deduplication and later API "
        "indexing can affect the displayed count. An advertisement is not a "
        "filled position. No contemporaneous measures of enterprise AI use, "
        "analytics capability, salaries, qualified candidates or AI-specific "
        "consulting availability are contained in this historical series.",
        "body_compact",sty=sty))
    story.append(P(
        "This research reconstruction was prepared on 17 November 2026 "
        "from archived observations reviewed on 16 November 2026. "
        "It must not be described as a report published in June, July or August. "
        "The full current edition uses separately verified, later-period sources.",
        "body_compact",sty=sty))
    story.append(P("Method: 30 high-signal search seeds, a headline-only senior "
        "role classifier and deduplication by source original_id or fallback "
        "fingerprint. Query provenance: JobTech Historical Ads / "
        "historical.api.jobtechdev.se/search.","caption",sty=sty))
    story.append(P(
       "For current market decisions, Executive Edition 2.0 adds independently "
       "verified AI adoption, recruitment, business confidence and sourcing "
       "evidence. The complete report and focused decision briefs are available "
       "through the Advisory account at jairribeiro.com.",
       "body_small",sty=sty))
    return assemble(story,cover,
        "Jair Ribeiro | Historical AI and Data Market Review | "+date_span,
        min_bytes=4500)


def _sample_points() -> list[dict]:
    mapping={"June 2026":"2026-06","July 2026":"2026-07","August 2026":"2026-08"}
    region_code={"Sweden":"se","Stockholm":"sto","Västra Götaland":"vgr"}
    month_code={"2026-06":"jun","2026-07":"jul","2026-08":"aug"}
    rows=[]
    for label,geo,val in EARLIEST_COMPLETE_MONTHS:
        month=mapping[label]
        rows.append({
          "code":"jobtech_v1_"+month_code[month]+"_"+region_code[geo],
          "series_code":"jobtech_ai_data_leadership_v1",
          "period_label":label,"period_start":month+"-01",
          "period_end":{"2026-06":"2026-06-30","2026-07":"2026-07-31","2026-08":"2026-08-31"}[month],
          "period_complete":True,
          "geography":geo,"value":val,"metric_unit":"advertisements",
          "source_family":"af_jobtech_target_demand",
          "source_title":"Arbetsförmedlingen JobTech Historical Ads / JobSearch",
          "source_url":JOBTECH_URL,
          "verified_on":DEMO_SOURCE_CHECKED,
        })
    return rows


@lru_cache(maxsize=1)
def public_historical_demo_pdf() -> bytes:
    return historical_market_pdf(_sample_points(),month_label="June-August 2026")


def public_market_demo_html() -> str:
    return (
      SERVICES_CSS+DEMO_CSS+nav("advisory")+
      """<main class="site">
        <section class="market-demo-hero"><div class="container">
          <nav class="market-demo-breadcrumb" aria-label="Advisory breadcrumb">
            <a href="?page=advisory" target="_self" data-hq-event="market_demo_breadcrumb_advisory">Advisory</a>
            <span aria-hidden="true">/</span>
            <a href="?page=advisory-market-signals" target="_self" data-hq-event="market_demo_breadcrumb_market_signals">Market Signals</a>
            <span aria-hidden="true">/</span>
            <span aria-current="page">Historical sample</span>
          </nav>
          <p class="eyebrow">Public research sample / JobTech</p>
          <h1>Historical AI &amp; Data Leadership Advertisements</h1>
          <p>Before you create an account, take a look at a short example of our research.
          It examines selected senior AI &amp; Data job advertisements in Sweden
          from June to August 2026, and explains what those figures can—and cannot—tell us.</p>
          <p class="market-demo-hero-links">
            <a href="#market-demo-pdf" data-hq-event="market_demo_pdf_jump">Download the free historical PDF ↓</a>
            <a href="?page=advisory-access&amp;view=market-signals" target="_self"
               data-hq-event="market_demo_full_review_hero">Access the current Executive Market Review →</a>
          </p>
        </div></section>
        <section class="market-demo-content"><div class="container">
          <h2>Scope and observations · June–August 2026</h2>
          <p>We prepared this five-page example in November 2026 using older JobTech records.
          It was not published during the summer, and it covers a selected set of
          job titles rather than the whole AI &amp; Data labour market.</p>
          <div class="market-demo-facts">
            <div><strong>12</strong><span>Selected Swedish job advertisements · June 2026</span></div>
            <div><strong>15</strong><span>Selected Swedish job advertisements · July 2026</span></div>
            <div><strong>10</strong><span>Selected Swedish job advertisements · August 2026</span></div>
          </div>
          <div class="market-demo-method"><p><strong>Scope of the historical data.</strong>
            We counted a defined selection of senior AI &amp; Data job advertisements.
            The numbers are not all vacancies or completed hires. We reviewed this
            historical selection in November 2026. Later SCB and Brainville research
            is not included in the summer figures.</p></div>
          <p class="market-demo-inline-download"><a href="#market-demo-pdf"
            data-hq-event="market_demo_pdf_jump_content">Download the five-page historical review ↓</a></p>
        </div></section>
       </main>"""
    )


def split_public_market_demo_at_download(document: str) -> tuple[str,str]:
    """Return two balanced HTML fragments with the native PDF between them.

    The common Where-to-next navigator and the portfolio footer must remain
    below the PDF rather than being emitted before the Streamlit button.
    This is intentionally scoped to the historical sample; other public pages
    continue using the standard single-document path.
    """
    anchor = '<section class="about-next portfolio-next" id="advisory-market-demo-continue"'
    if document.count(anchor) != 1:
        raise ValueError("Historical sample closing navigation is unavailable.")
    idx = document.index(anchor)
    if "</main>" not in document[idx:]:
        raise ValueError("Historical sample markup has no closing main.")
    if document.count('<footer class="footer">') > 1:
        raise ValueError("Historical sample must have one site-wide footer.")
    before = document[:idx] + "</main>"
    after = '<main class="site">' + document[idx:]
    # The historical route itself has no footer. The original native PDF
    # renderer used to append it after the button; retain that exact standard
    # footer in the second HTML fragment, after the shared navigator.
    if '<footer class="footer">' not in after:
        after += footer()
    return before, after


def render_public_market_demo_download() -> None:
    """Free historical PDF in native Streamlit, before shared navigation."""
    st.html('<div id="market-demo-pdf" aria-hidden="true"></div>')
    with st.container(key="market_demo_native_download"):
        st.html(
            '<div class="market-demo-download-kicker">FREE HISTORICAL RESEARCH / PDF</div>'
            '<h2 class="market-demo-download-title">Download the June–August 2026 research sample</h2>'
            '<p class="market-demo-download-lead">'
            'The five-page review includes monthly and regional figures, a chart, '
            'alternative explanations, executive discussion questions and original '
            'source references. No registration is required.</p>'
        )
        st.download_button(
            "Download five-page historical market review · PDF",
            data=public_historical_demo_pdf(),
            file_name="Jair_Ribeiro_Market_Observatory_Public_Demo_Jun_Aug_2026.pdf",
            mime="application/pdf",
            key="public_market_observatory_pdf",
            type="primary",
            use_container_width=True,
        )
        st.caption(
            "Historical scope: JobTech senior AI & Data advertisements, "
            "June–August 2026. Prepared November 2026."
        )
    st.html(
        '<div class="site">'
        '<section class="market-demo-end" aria-labelledby="market-demo-next-title">'
        '<div class="container">'
        '<p class="market-demo-end-kicker">CURRENT EXECUTIVE RESEARCH</p>'
        '<h2 id="market-demo-next-title">Looking for the complete November market assessment?</h2>'
        '<p class="market-demo-end-lead">This free PDF is an older, narrowly focused '
        'research sample—not the full Executive Market Review 2.0. '
        'The current report examines AI adoption, workforce demand, business '
        'conditions, sourcing choices and regional differences, with recommendations '
        'and supporting evidence. A verified Advisory account gives access to '
        'the full PDF and five executive decision briefs.</p>'
        '<a class="market-demo-next-card market-demo-next-card--featured" '
        'href="?page=advisory-access&amp;view=market-signals" target="_self" '
        'data-hq-event="market_demo_open_full_observatory">'
        '<small>COMPLETE EXECUTIVE MARKET REVIEW 2.0</small>'
        '<h3>Read and download the current research</h3>'
        '<span class="market-demo-next-link">Access the full report · Free account →</span>'
        '</a>'
        '</div></section></div>'
    )
