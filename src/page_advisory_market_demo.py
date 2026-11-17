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
    """Printable research snapshot for one historic month or June-Aug sample."""
    points=_strict_historical_points(points)
    unique_months=sorted(set(
        str(p["period_start"])[:7] for p in points
    ))
    s=_styles()
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
       topMargin=23*mm,bottomMargin=21*mm,
       title="Historical AI & Data Market Observatory - "+month_label,
       author="Jair Ribeiro | Enterprise AI & Data")
    story=[]
    def add(txt,style="body"):story.append(_P(s,txt,style))
    def page():story.append(PageBreak())
    def section(title,lead):
        add(title,"chapter");add(lead)
    add("PUBLIC HISTORICAL RESEARCH SAMPLE  /  VERSION 01","kicker")
    add("AI & Data Market Observatory","hero")
    add(month_label+" | The earliest verified leadership-advertisement history","chapter")
    story.append(HRFlowable(width="100%",thickness=2,color=ACCENT,spaceAfter=21))
    add("This is a genuine historical example of the evidence standard used by "
        "the AI & Data Market Signals service. It covers only an approved, narrow "
        "basket of JobTech leadership advertisements. It does not recreate the "
        "full AI, Data and Analytics market at that time.")
    add("The observations were originally published in the stated historical "
        "months, but this research reconstruction was prepared on 17 November "
        "2026 from extracted records reviewed on 16 November 2026. "
        "It must not be described as a report published in June, July or August.")
    add("Three distinctions that matter","section")
    for item in [
        "Advertisement count is not a filled position, job offer or census of all AI-related work.",
        "Stockholm and Västra Götaland are contained within the national Sweden count. They cannot be added to it.",
        "The classification is headline-only and deliberately excludes many technical and product roles; later indexing can revise historical records.",
    ]:add("- "+item)
    page()

    add("01 / What the archived evidence measures","kicker")
    section("Leadership advertisements, narrowly defined",
        "The same frozen AI/Data leadership title-basket version 1 was applied to "
        "the approved JobTech publication-month observations. The small sample "
        "is useful for disciplined comparison, not a broad recruiting market forecast.")
    months=unique_months
    lookup={(str(p["period_start"])[:7],str(p["geography"])):int(p["value"])
            for p in points}
    rows=[["Month","Sweden","Stockholm","Västra Götaland"]]
    for month in months:
        rows.append([date.fromisoformat(month+"-01").strftime("%B %Y"),
            *[str(lookup.get((month,region),"—")) for region in REGIONS]])
    t=Table([[ _P(s,x,"table") for x in row] for row in rows],
       colWidths=[53*mm,36*mm,40*mm,45*mm],repeatRows=1)
    t.setStyle(TableStyle([
       ("BACKGROUND",(0,0),(-1,0),PAPER),
       ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PAPER]),
       ("LINEBELOW",(0,0),(-1,-1),.6,RULE),
       ("TOPPADDING",(0,0),(-1,-1),12),
       ("BOTTOMPADDING",(0,0),(-1,-1),12),
       ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(t);story.append(Spacer(1,13))
    if len(months)>1:
        add("National title-basket trend · complete months only","section")
        story.append(_historical_national_chart(months,lookup))
        story.append(Spacer(1,12))
    if len(months)>1:
        add("Reading a small series","section")
        add("The national sequence is "+", ".join(
            str(lookup.get((month,"Sweden"),"not recorded")) for month in months
        )+" qualifying advertisements across the archived complete months. "
        "The changes are observations inside a tightly defined sample, "
        "not a signal that all Swedish AI leadership hiring grew or contracted.")
    else:
        add("Reading a single month","section")
        add("One complete monthly observation establishes a dated baseline, "
            "not a trend. A reliable comparison requires at least one further "
            "complete and comparably classified month.")
    add("What would weaken this interpretation?","section")
    add("Different role titles, agency-only assignments, employer-specific "
        "advertising channels and retrospective API indexing may change "
        "what is visible. No conclusion about skills scarcity or the "
        "speed of hiring follows from these counts.")
    page()

    add("02 / What an AI or Data leader can do with this","kicker")
    section("An executive discussion, not a forecast",
        "A market review becomes useful when it changes how decisions are framed. "
        "The archived data can challenge overgeneralised claims about senior "
        "AI hiring, but your organisation still needs its own evidence.")
    tests=[
        ("Define the capability",
         "Describe the actual leadership work: operating model, governance, "
         "portfolio choices, adoption, data stewardship or technical delivery."),
        ("Clarify the search geography",
         "What would be gained or lost by permitting remote, hybrid or "
         "adjacent-region candidates? The archived region counts do not "
         "measure available candidates."),
        ("Test an alternative",
         "Compare a permanent hire, internal development and external "
         "support against the same accountable six-month outcome."),
        ("Set a reversal condition",
         "What would make you abandon the original talent assumption? "
         "Define the evidence before a costly hiring commitment."),
    ]
    for title,body in tests:
        story.append(KeepTogether([_P(s,title,"section"),_P(s,body)]))
    add("Management meeting question","section")
    add("Are we facing a shortage of leaders, or have we defined the "
        "responsibilities and sourcing constraints too narrowly?")
    page()

    add("03 / What this historical data cannot show","kicker")
    section("A deliberate boundary is part of credible research.",
        "The full member Observatory has additional later-published measures. "
        "Those are intentionally absent from this historical public sample.")
    for label,what in [
        ("Enterprise AI adoption","No SCB 2026 enterprise AI release is included or backdated to these historic months."),
        ("Data and Analytics capability","No contemporaneous measures of internal analytics staff, BI or data quality."),
        ("AI leadership hiring outcomes","No count of filled vacancies, total executive positions, salary or candidate supply."),
        ("Consulting availability","No Brainville October 2026 source is presented as evidence for earlier months."),
        ("Causal market conclusions","Nothing in this narrow title series identifies why advertised roles appeared."),
    ]:
        story.append(KeepTogether([_P(s,label,"section"),_P(s,what)]))
    add("How the complete subscription-free service differs","section")
    add("Verified members can examine later approved editions, enterprise "
        "adoption, capability and consulting evidence, source comparisons, "
        "independent executive analysis and research PDFs. Each source "
        "enters only after a dated editorial release.")
    page()

    add("Appendix / Source and audit trail","kicker")
    section("Trace every historical observation",
        "This is the full record set used by the sample. Each row has the "
        "same narrow definition and an original source URL.")
    rows=[["Publication month","Geography","Adverts","Evidence code"]]
    for p in sorted(points,key=lambda x:(str(x["period_start"]),str(x["geography"]))):
        rows.append([
            str(p["period_label"]),str(p["geography"]),str(int(p["value"])),str(p["code"])
        ])
    tab=Table([[_P(s,x,"small") for x in row] for row in rows],
        colWidths=[47*mm,38*mm,19*mm,70*mm],repeatRows=1)
    tab.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[PAPER,colors.white]),
        ("LINEBELOW",(0,0),(-1,-1),.4,RULE),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(tab);story.append(Spacer(1,15))
    story.append(Paragraph(
      '<link href="'+JOBTECH_URL+'" color="#295A79">Original JobTech Historical Ads query interface</link>',
      s["small"]))
    add("Classifier: Jair high-signal AI/Data leadership title basket v1; "
        "30 curated search seeds, headline-only strategic/senior role filter, "
        "deduplication by source original_id or fallback fingerprint. "
        "Live and historical job APIs were unioned in the original extraction; "
        "retrospective changes may occur.")
    add("Evidence checked: 16 November 2026. Demo issued: 17 November 2026. "
        "Other provider sources were not included. No private personal "
        "career intelligence was used.")
    add("Jair Ribeiro | Enterprise AI & Data leadership. "
        "This independent historical research sample is for contextual "
        "executive discussion, not recruiting, legal or investment advice.","small")
    doc.build(story,onFirstPage=_frame,onLaterPages=_frame)
    blob=out.getvalue()
    if not blob.startswith(b"%PDF") or len(blob)<3200:
        raise ValueError("Historical sample report failed PDF verification.")
    return blob


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
          <p class="eyebrow">A look inside / Public research example</p>
          <h1>See how we examine the market—not just the headline.</h1>
          <p>Before you create an account, take a look at a short example of our research.
          It examines selected senior AI &amp; Data job advertisements in Sweden
          from June to August 2026, and explains what those figures can—and cannot—tell us.</p>
        </div></section>
        <section class="market-demo-content"><div class="container">
          <h2>A closer look at leadership job adverts · June–August 2026</h2>
          <p>We prepared this five-page example in November 2026 using older JobTech records.
          It was not published during the summer, and it covers a selected set of
          job titles rather than the whole AI &amp; Data labour market.</p>
          <div class="market-demo-facts">
            <div><strong>12</strong><span>Selected Swedish job advertisements · June 2026</span></div>
            <div><strong>15</strong><span>Selected Swedish job advertisements · July 2026</span></div>
            <div><strong>10</strong><span>Selected Swedish job advertisements · August 2026</span></div>
          </div>
          <div class="market-demo-method"><p><strong>What these figures cover.</strong>
            We counted a defined selection of senior AI &amp; Data job advertisements.
            The numbers are not all vacancies or completed hires. We reviewed this
            historical selection in November 2026. Later SCB and Brainville research
            is not included in the summer figures.</p></div>
          
        </div></section>
       </main>"""
    )


def render_public_market_demo_download() -> None:
    """Native no-login PDF download, then contextual Advisory navigation and shared footer."""
    with st.container(key="market_demo_native_download"):
        st.html(
            '<div class="market-demo-download-kicker">A PREVIEW OF THE RESEARCH</div>'
            '<h2 class="market-demo-download-title">Read the historical market sample</h2>'
            '<p class="market-demo-download-lead">'
            'A five-page PDF with the figures, a chart, alternative explanations, '
            'questions for a leadership discussion and the source records. '
            'You can read it without creating an account.</p>'
        )
        st.download_button(
            "Download the five-page research sample · PDF",
            data=public_historical_demo_pdf(),
            file_name="Jair_Ribeiro_Market_Observatory_Public_Demo_Jun_Aug_2026.pdf",
            mime="application/pdf",
            key="public_market_observatory_pdf",
            type="primary",
            use_container_width=True,
        )
        st.caption(
            "Source: frozen JobTech v1 June–August 2026 observations; "
            "archival review 16 November 2026; issued 17 November 2026."
        )
    st.html(
        '<div class="site">'
        '<section class="market-demo-end" aria-labelledby="market-demo-next-title"><div class="container">'
        '<p class="market-demo-end-kicker">WHERE TO GO NEXT</p>'
        '<h2 id="market-demo-next-title">Explore the full research when you're ready.</h2>'
        '<p class="market-demo-end-lead">This example covers only the earliest reviewed job-advertisement history. '
        'The November 2026 review adds figures about AI use, data and analytics '
        'and consulting activity, with a fuller discussion of business decisions.</p>'
        '<nav class="market-demo-end-grid" aria-label="Continue within Advisory">'
        '<a class="market-demo-next-card" href="?page=advisory-market-signals" target="_self" '
        'data-hq-event="market_demo_back_to_service">'
        '<small>ABOUT THE SERVICE</small><h3>See what Market Signals offers</h3>'
        '<p>Explore the research topics, what is published and what is still being '
        'checked before you create an account.</p>'
        '<span class="market-demo-next-link">Back to the Market Signals overview →</span></a>'
        '<a class="market-demo-next-card market-demo-next-card--featured" '
        'href="?page=advisory-access&amp;view=market-signals" target="_self" '
        'data-hq-event="market_demo_open_full_observatory">'
        '<small>READ THE FULL REPORT</small><h3>Read the complete November review</h3>'
        '<p>Read the November research report, explore published figures and download '
        'decision briefs. A free account is required.</p>'
        '<span class="market-demo-next-link">Open the full research →</span></a>'
        '</nav>'
        '<a class="market-demo-end-home" href="?page=advisory" target="_self" '
        'data-hq-event="market_demo_all_advisory">Browse all Advisory services →</a>'
        '</div></section>'
        + footer() + '</div>'
    )
