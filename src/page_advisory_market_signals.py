"""AI & Data Market Signals — curated, evidence-led Advisory member product.

Only reads the dedicated, RLS-protected publication tables through the verified
member JWT. It never reads the private career, job-search or forecast datasets.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape as html_escape
from io import BytesIO, StringIO
from urllib.parse import urlsplit
import csv
import math

import altair as alt
import pandas as pd
import streamlit as st
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

from site_cms import _request_json, _rest_url
from site_components import nav, footer
from page_public_services import SERVICES_CSS

PALETTE = {
    "navy": "#11273C", "ink": "#22394D", "copper": "#B17B58",
    "muted": "#607182", "paper": "#F8F7F3", "white": "#FFFFFF",
    "line": "#DCD8D0",
}
LENSES = {
    "leadership": "AI & Data leadership demand",
    "adoption": "AI adoption",
    "capability": "Data & AI capabilities",
    "consulting": "Consulting conditions",
}
SOURCE_CADENCE_DAYS = {
    "af_jobtech_target_demand": 15,
    "af_jobsearch_current": 15,
    "brainville_consulting_market": 50,
    "scb_enterprise_ai_adoption": 410,
}
MARKET_STYLE = """
<style>
.st-key-market_signals_workspace [data-testid="stMetric"] {
 background:#FFFDF9;border:1px solid #DDD8CF;border-top:2px solid #AD7855;
 padding:14px 16px;border-radius:4px;
}
.st-key-market_signals_workspace [data-testid="stMetricLabel"] {color:#53677B}
.st-key-market_signals_workspace [data-testid="stMetricValue"] {color:#142B42}
.st-key-market_signals_workspace [data-testid="stPills"] {
 overflow-x:auto;max-width:100%;padding:8px;background:#FFFDF9;border:1px solid #E3DDD5;
}
.st-key-market_signals_workspace [data-testid="stPills"] button {
 min-height:42px;white-space:nowrap;font-weight:700;
}
.market-hero {background:linear-gradient(120deg,#10253A,#203D53);color:#fff;
 padding:clamp(28px,4vw,51px);margin:7px 0 21px}
.market-hero .eyebrow {text-transform:uppercase;letter-spacing:.17em;font-size:10px;
 color:#E5B58F;font-weight:800}
.market-hero h2 {color:#fff;font:500 clamp(35px,4.9vw,59px)/1.1 Georgia,serif;
 letter-spacing:-.035em;margin:14px 0 12px}
.market-hero p {color:#D3DEE6;font-size:15px;line-height:1.7;max-width:820px}
.market-head {padding:12px 0 5px}
.market-head h3 {color:#1A3248;font:500 clamp(23px,3vw,34px)/1.15 Georgia,serif;
 margin:8px 0}
.market-head p {color:#596B7B;line-height:1.65}
.market-kicker {text-transform:uppercase;font-size:10px;font-weight:800;
 color:#976B4E;letter-spacing:.14em}
.market-thesis {padding:20px 23px;border-left:4px solid #AC7854;
 background:#FFFDF9;margin:12px 0;color:#213B52;line-height:1.75}
.market-thesis h3 {margin:0 0 8px;font:500 25px Georgia,serif;color:#142B42}
.market-evidence {margin:12px 0 17px;padding:16px 20px;border:1px solid #DDD8CE;
 background:#F6F3ED;color:#35495B;font-size:13px;line-height:1.7}
.market-evidence strong{color:#203D55}
.market-source {padding:15px 18px;border-bottom:1px solid #DED8CD;background:#FFFEFC;
 overflow-wrap:anywhere}
.market-source strong {font-size:13px;color:#20394F}
.market-source small {display:block;color:#687784;margin-top:4px;line-height:1.6}
.market-source a {color:#1B577C;text-decoration:underline}
.market-outcome{padding:20px 22px;background:#142B42;color:#F9F6F1;
 line-height:1.7;margin:12px 0 20px}
.market-outcome strong{color:#F0C4A1}
.market-outcome p{color:#E0E6EB}
@media(max-width:700px),(max-device-width:700px){
 .market-hero{padding:24px 18px}
 .market-thesis,.market-outcome{padding:16px 17px}
 .st-key-market_signals_workspace .stHorizontalBlock {flex-wrap:wrap!important}
 .st-key-market_signals_workspace .stColumn {min-width:min(100%,260px)!important}
}
</style>
"""


def advisory_market_signals() -> str:
    """Public trust-first value proposition; never exposes the member data endpoint."""
    return f'''{SERVICES_CSS}
<style>
.site .ms-hero{{background:linear-gradient(125deg,#0D2033,#22425A);color:#fff;padding:92px 0 80px}}
.site .ms-hero h1{{font:500 clamp(43px,6vw,76px)/1.07 Georgia,serif;letter-spacing:-.03em;max-width:800px}}
.site .ms-hero p{{color:#D5DEE7;max-width:780px;font-size:17px;line-height:1.75}}
.site .ms-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.site .ms-card{{background:#fffefa;border:1px solid #ded8d0;border-top:3px solid #b47d55;padding:30px}}
.site .ms-card h3{{font:500 28px/1.2 Georgia,serif;color:#193149;margin:12px 0}}
.site .ms-card p{{color:#506276;line-height:1.75;font-size:14px}}
.site .ms-trust{{background:#eae6dd;padding:26px;border-left:4px solid #b47d55;color:#284055}}
.site .ms-actions{{display:flex;gap:11px;flex-wrap:wrap;margin-top:24px}}
.site .ms-actions a{{display:inline-flex;align-items:center;min-height:49px;padding:13px 20px;
 background:#DBA783;color:#10253A!important;font-size:13px;font-weight:850;text-decoration:none!important}}
.site .ms-actions a.ms-secondary{{background:transparent;border:1px solid #95A3B0;color:#fff!important}}
@media(max-width:750px){{.site .ms-grid{{grid-template-columns:1fr}}.site .ms-hero{{padding:57px 0}}}}
</style>
{nav("advisory")}
<main class="site advisory-page">
<section class="ms-hero"><div class="container">
<span class="service-eyebrow">JAIR RIBEIRO ADVISORY / VERIFIED MARKET INTELLIGENCE</span>
<h1>AI &amp; Data Market Signals</h1>
<p>Understand where AI adoption, leadership demand and Data capabilities are moving.
Go beyond headlines with source-linked evidence, an interactive dashboard and
decision materials designed for leadership discussions.</p>
<div class="ms-actions">
<a href="?page=advisory-access&amp;view=market-signals" target="_self"
data-hq-event="market_signals_register">Register free · Explore the intelligence</a>
<a href="?page=advisory-access&amp;view=market-signals&amp;signin=1" target="_self"
class="ms-secondary" data-hq-event="market_signals_signin">Sign in</a></div>
<p style="font-size:12px;margin-top:20px">Sweden first · Source periods and verification dates shown · No personal career data · No paywall</p>
</div></section>
<section class="service-section service-section--white"><div class="container">
<p class="service-eyebrow">Four evidence lenses</p><h2>Market signals connected to leadership decisions.</h2>
<div class="ms-grid">
<article class="ms-card"><span class="service-eyebrow">01 / ADOPTION</span><h3>Where is AI entering business?</h3>
<p>Official enterprise adoption figures, population definitions, survey limitations and year-on-year context.</p></article>
<article class="ms-card"><span class="service-eyebrow">02 / LEADERSHIP</span><h3>What demand is visible?</h3>
<p>Curated AI and Data leadership advertisement trends, by region and complete publication month; not a general job board.</p></article>
<article class="ms-card"><span class="service-eyebrow">03 / CAPABILITY</span><h3>What could prevent scale?</h3>
<p>In-house analytics, expertise, data quality, privacy and operating ownership, with clear survey denominators.</p></article>
<article class="ms-card"><span class="service-eyebrow">04 / CONDITIONS</span><h3>What is the wider hiring context?</h3>
<p>Consulting and sector signals, explicitly labelled as context rather than AI-specific labour-market statistics.</p></article>
</div></div></section>
<section class="service-section"><div class="container">
<p class="service-eyebrow">What readers receive</p><h2>Evidence you can take into the next decision.</h2>
<div class="ms-grid">
<div class="ms-card"><h3>Explore &amp; challenge</h3><p>Interactive filters, accessible charts, source health,
a transparent evidence ledger and an explicit distinction between observed facts and interpretation.</p></div>
<div class="ms-card"><h3>Download &amp; decide</h3><p>Executive-grade market reviews, fully cited source appendices and printable
leadership decision records, generated from the same verified evidence seen on screen.</p></div>
</div>
<div class="ms-trust" style="margin-top:26px">
<strong>Evidence standard</strong><p>Official statistics and first-party market research are kept separate from
our derived title-basket analysis. Independent sources strengthen contextual interpretation but cannot establish causation.
Missing, incomplete or stale evidence is explicitly marked—never filled with a guess.</p></div>
</div></section></main>{footer()}'''


def _checked_url(value: str) -> str:
    value = str(value or "")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Market evidence source is not a trusted HTTPS URL.")
    return value


def _load_curated(token: str) -> tuple[list[dict], list[dict]]:
    if not token:
        raise PermissionError("A verified Advisory session is required.")
    p = _request_json(
        "GET",
        _rest_url("portfolio_market_signal_points?select=*&is_published=eq.true&order=period_end.asc&limit=150"),
        token=token, timeout=12,
    )
    b = _request_json(
        "GET",
        _rest_url("portfolio_market_signal_briefs?select=*&is_published=eq.true&order=published_on.desc&limit=30"),
        token=token, timeout=12,
    )
    if not isinstance(p, list) or not isinstance(b, list) or not p or not b:
        raise RuntimeError("Verified market evidence is unavailable.")
    seen = set()
    for item in p:
        key = str(item.get("code") or "")
        if not key or key in seen:
            raise ValueError("Market evidence catalogue contains a missing or duplicate identifier.")
        seen.add(key)
        _checked_url(str(item.get("source_url") or ""))
        if item.get("value") is None or item.get("evidence_grade") not in {"primary","derived","contextual"}:
            raise ValueError("Market evidence failed completeness checks.")
        if not item.get("period_start") or not item.get("period_end") or not item.get("verified_on"):
            raise ValueError("Market evidence lacks a date or verification stamp.")
    by_code = {p["code"]: p for p in p}
    for brief in b:
        codes = brief.get("evidence_codes")
        if not isinstance(codes, list) or len(codes) < 2 or any(c not in by_code for c in codes):
            raise ValueError("An executive interpretation references unavailable evidence.")
        families = {by_code[c]["source_family"] for c in codes}
        if brief.get("support_level") == "independent_sources" and len(families) < 2:
            raise ValueError("Independent verification claimed without two source families.")
        if not brief.get("counterevidence") or not brief.get("limitations"):
            raise ValueError("An executive interpretation is missing its limitations.")
    return p, b


INITIAL_PREVIEW_CODES = frozenset({
    "brainville_202610_assignments_yoy","brainville_202610_consultants_yoy",
    "jobtech_v1_jun_se","jobtech_v1_jun_vgr","jobtech_v1_jun_sto",
    "jobtech_v1_jul_se","jobtech_v1_jul_vgr","jobtech_v1_jul_sto",
    "jobtech_v1_aug_se","jobtech_v1_aug_vgr","jobtech_v1_aug_sto",
    "jobtech_v1_sep_se","jobtech_v1_sep_vgr","jobtech_v1_sep_sto",
    "jobtech_v1_oct_se","jobtech_v1_oct_vgr","jobtech_v1_oct_sto",
    "jobtech_v1_nov15_se","jobtech_v1_nov15_vgr","jobtech_v1_nov15_sto",
    "scb_2026_ai_10plus","scb_2026_ai_250plus",
    "scb_2026_ai_10to49","scb_2026_ai_50to249",
    "scb_2026_ai_data_quality_barrier","scb_2026_ai_expertise_barrier",
    "scb_2026_ai_privacy_barrier","scb_2026_analytics_internal",
    "scb_2026_bi_use","scb_2026_data_analytics_use",
    "scb_2026_ict_specialists",
})

def _release_snapshot(token: str, points: list[dict], briefs: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Bind published editions to the same approved evidence as the executive PDFs.

    The initial 2026 catalogue remains a clearly marked pre-release preview
    until the owner completes the first formal editorial source approval.
    """
    response=_request_json(
        "POST",_rest_url("rpc/portfolio_market_signals_current_release_v1"),
        token=token,payload={},timeout=10,
    )
    if not isinstance(response,dict) or type(response.get("published")) is not bool:
        raise RuntimeError("Verified editorial release state unavailable.")
    if not response["published"]:
        # The pre-release preview is a frozen, historically disclosed catalogue.
        # Publishing a later point cannot silently add it to member dashboards;
        # new datasets require a signed-off versioned edition manifest.
        preview=[p for p in points if p["code"] in INITIAL_PREVIEW_CODES]
        preview_codes={p["code"] for p in preview}
        preview_briefs=[b for b in briefs
                        if set(b["evidence_codes"]).issubset(preview_codes)]
        if len(preview)!=len(INITIAL_PREVIEW_CODES) or not preview_briefs:
            raise ValueError("Frozen pre-release catalogue cannot be verified.")
        return preview,preview_briefs,response
    codes=response.get("evidence_codes")
    slugs=response.get("brief_slugs")
    if not isinstance(codes,list) or not isinstance(slugs,list) or len(codes)<2 or not slugs:
        raise ValueError("Published edition has an incomplete evidence manifest.")
    point_map={p["code"]:p for p in points}
    brief_map={b["slug"]:b for b in briefs}
    if len(set(codes))!=len(codes) or len(set(slugs))!=len(slugs):
        raise ValueError("Published edition includes duplicate references.")
    if any(x not in point_map for x in codes) or any(x not in brief_map for x in slugs):
        raise ValueError("The published edition refers to missing data or analysis.")
    selected_points=[point_map[c] for c in codes]
    selected_briefs=[brief_map[c] for c in slugs]
    selected_codes=set(codes)
    for brief in selected_briefs:
        if not set(brief["evidence_codes"]).issubset(selected_codes):
            raise ValueError("Executive analysis cites evidence outside its published edition.")
    if len({p["source_family"] for p in selected_points})<2:
        raise ValueError("A published edition requires independent source families.")
    return selected_points,selected_briefs,response


def _freshness(point: dict, today: date | None = None) -> str:
    today = today or date.today()
    verified = date.fromisoformat(str(point["verified_on"])[:10])
    allowed = SOURCE_CADENCE_DAYS.get(point.get("source_family"), 90)
    return "Review overdue" if (today - verified).days > allowed else "Verified"


def _value(point: dict) -> str:
    number = float(point["value"])
    shown = f"{int(number):,}" if number.is_integer() else f"{number:,.1f}"
    unit = str(point["metric_unit"])
    return shown + ("%" if unit == "percent" else " " + unit)


def _head(kicker: str, title: str, copy: str = "") -> None:
    st.html(
        '<section class="market-head"><span class="market-kicker">'
        + html_escape(kicker) + '</span><h3>' + html_escape(title) + '</h3>'
        + ('<p>' + html_escape(copy) + '</p>' if copy else "") + '</section>'
    )


def _plot(points: list[dict], lens: str, geography: str) -> None:
    selected = [p for p in points if p["lens"] == lens and p["geography"] == geography]
    if lens == "leadership":
        complete = sorted(
            (p for p in selected if p["period_complete"]),
            key=lambda p: p["period_end"]
        )
        if not complete:
            st.warning("There are no complete monthly observations for this geography.")
            return
        table = pd.DataFrame({
            "Period": [p["period_label"] for p in complete],
            "Month": pd.to_datetime([p["period_start"] for p in complete]),
            "Advertisements": [int(p["value"]) for p in complete],
        })
        chart = alt.Chart(table).mark_line(
            color=PALETTE["navy"], point={"filled": True, "fill": PALETTE["copper"], "size": 82},
            strokeWidth=3,
        ).encode(
            x=alt.X("Month:T", title="Publication month", axis=alt.Axis(format="%b %Y")),
            y=alt.Y("Advertisements:Q", title="Qualifying advertisements", scale=alt.Scale(zero=True)),
            tooltip=["Period:N", alt.Tooltip("Advertisements:Q", format=",d")],
        ).properties(height=290)
        st.altair_chart(chart, use_container_width=True)
        partial = sorted(
            (p for p in selected if not p["period_complete"]),
            key=lambda p: p["period_end"]
        )
        if partial:
            last = partial[-1]
            st.caption(
                f"Latest incomplete period: {last['period_label']} — {_value(last)}. "
                "Excluded from the full-month trend because the windows differ."
            )
        st.caption(
            "Frozen JobTech headline-only title basket v1, not total vacancies or completed hires. "
            "Small samples, indexed coverage and retrospective API revisions restrict conclusions."
        )
    else:
        latest = {}
        for p in sorted(selected, key=lambda x: x["period_end"]):
            latest[p["series_code"]] = p
        rows = list(latest.values())
        if not rows:
            st.warning("No source-supported observations are available for this selection.")
            return
        df = pd.DataFrame({
            "Measure": [p["metric_label"] for p in rows],
            "Value": [float(p["value"]) for p in rows],
            "Unit": [p["metric_unit"] for p in rows],
            "Period": [p["period_label"] for p in rows],
        })
        chart = alt.Chart(df).mark_bar(color=PALETTE["navy"], cornerRadiusEnd=3).encode(
            x=alt.X("Value:Q", title="Reported value", scale=alt.Scale(zero=True)),
            y=alt.Y("Measure:N", sort="-x", title=None),
            tooltip=["Measure:N", alt.Tooltip("Value:Q", format=".1f"), "Unit:N", "Period:N"],
        ).properties(height=max(250, 38*len(rows)))
        st.altair_chart(chart, use_container_width=True)
        if lens == "consulting":
            st.caption("Brainville figures cover all consulting disciplines, not AI/Data-specific consulting.")
        if lens in ("adoption","capability"):
            st.caption(
                "SCB enterprise survey 2026. Bar denominators differ for adoption rates and "
                "barriers among non-adopters; do not compare them as shares of the same population."
            )


def _safe_csv(points: list[dict]) -> bytes:
    output = StringIO()
    w = csv.writer(output)
    w.writerow(["metric","value","unit","geography","period","period_complete","population",
                "source_family","source_title","source_url","published_on","verified_on",
                "evidence_grade","methodology","caveat"])
    for p in points:
        cells = [p.get(k,"") for k in (
            "metric_label","value","metric_unit","geography","period_label",
            "period_complete","population_note","source_family","source_title","source_url",
            "published_on","verified_on","evidence_grade","methodology","caveat"
        )]
        w.writerow(["'"+str(v) if str(v).startswith(("=","+","-","@")) and not isinstance(v,(int,float)) else v for v in cells])
    return output.getvalue().encode("utf-8-sig")


def _pdf_safe(text: object) -> str:
    """Keep PDF library's base font predictable while retaining text semantics."""
    return html_escape(str(text if text is not None else "").replace("\u2013", "-")
                       .replace("\u2014", "-").replace("\u2019", "'").replace("\u2022", "-")
                       .encode("latin-1","replace").decode("latin-1"))


def executive_pdf(points: list[dict], brief: dict, geography: str) -> bytes:
    """Source-linked A4 market analysis + executive decision record; no private user inputs."""
    by_code = {p["code"]:p for p in points}
    support = [by_code[c] for c in brief["evidence_codes"]]
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
        topMargin=24*mm, bottomMargin=19*mm,
        title="AI & Data Market Signals - Executive Decision Brief",
        author="Jair Ribeiro | Enterprise AI & Data Leader",
    )
    title = ParagraphStyle("title",fontName="Helvetica-Bold",fontSize=24,leading=29,textColor=colors.HexColor(PALETTE["navy"]),spaceAfter=16)
    h = ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=12,leading=17,textColor=colors.HexColor(PALETTE["navy"]),spaceBefore=12,spaceAfter=7)
    body = ParagraphStyle("body",fontName="Helvetica",fontSize=9.5,leading=15,textColor=colors.HexColor(PALETTE["ink"]),spaceAfter=9)
    small = ParagraphStyle("small",fontName="Helvetica",fontSize=7.8,leading=11,textColor=colors.HexColor(PALETTE["muted"]),spaceAfter=5)
    copper = colors.HexColor(PALETTE["copper"])
    story = [
        Paragraph("AI &amp; DATA MARKET SIGNALS",small),
        HRFlowable(width="100%",thickness=2,color=copper),
        Spacer(1,13),
        Paragraph("Executive market decision brief",title),
        Paragraph(_pdf_safe(brief["title"]),h),
        Paragraph(_pdf_safe(brief["thesis"]),body),
        Paragraph("Edition: "+_pdf_safe(brief["published_on"]) +
                  " | Primary geography: Sweden | Selected geography: "+_pdf_safe(geography),small),
        Paragraph("What the evidence says",h),
        Paragraph(_pdf_safe(brief["interpretation"]),body),
        Paragraph("The executive decision",h),
        Paragraph(_pdf_safe(brief["decision_question"]),body),
        Paragraph("Proposed first action",h),
        Paragraph(_pdf_safe(brief["recommended_action"]),body),
        Paragraph("What could challenge this reading?",h),
        Paragraph(_pdf_safe(brief["counterevidence"]),body),
        Paragraph("Confidence boundary",h),
        Paragraph(_pdf_safe(brief["limitations"]),body),
        Paragraph(
            "Independent source families: "+
            str(len({p["source_family"] for p in support}))+
            ". This describes independent evidence streams, not proof of causation. "
            "All statistics retain original populations and observation windows.",small),
        PageBreak(),
        Paragraph("Evidence record",title),
        Paragraph(
            "The following metrics are the specific supporting observations for this decision. "
            "They are not broad claims about every vacancy, business or AI investment.",body)
    ]
    for i,p in enumerate(support,1):
        link = _checked_url(p["source_url"])
        block = [
            Paragraph(f"{i:02d} / "+_pdf_safe(p["metric_label"]),h),
            Paragraph(_pdf_safe(_value(p))+" | "+_pdf_safe(p["geography"])+" | "+
                      _pdf_safe(p["period_label"]),body),
            Paragraph("Population: "+_pdf_safe(p["population_note"]),small),
            Paragraph("Publisher: "+_pdf_safe(p["source_title"]) +
                      " | Released "+_pdf_safe(p["published_on"]) +
                      " | Verified "+_pdf_safe(p["verified_on"]),small),
            Paragraph("Caution: "+_pdf_safe(p["caveat"]),small),
            Paragraph('<link href="'+html_escape(link,quote=True)+'" color="#1B557A">'+
                      _pdf_safe(link)+'</link>',small),
            Spacer(1,4),
        ]
        story.append(KeepTogether(block))
    story.extend([
        PageBreak(), Paragraph("Leadership decision record",title),
        Paragraph("This record is a structured working tool, not an automated investment verdict.",body),
    ])
    fields = [
        ("Decision to be taken",brief["decision_question"]),
        ("What internal outcome should change?","_____________________________________________________________"),
        ("Decision owner and accountable business function","_____________________________________________________________"),
        ("Current baseline and strongest alternative","_____________________________________________________________"),
        ("Evidence missing before commitment","_____________________________________________________________"),
        ("What would change the recommendation?","_____________________________________________________________"),
        ("First 30-day action and owner","_____________________________________________________________"),
        ("Next review date / stop-or-scale threshold","_____________________________________________________________"),
    ]
    for label,value in fields:
        story.append(Paragraph(_pdf_safe(label),h))
        story.append(Paragraph(_pdf_safe(value),body))
        story.append(Spacer(1,5))
    story.extend([
        Spacer(1,12),
        Paragraph("Prepared from verified and curated market observations. "
                  "No private career intelligence, individual interviews or personal hiring forecasts are included.",small),
    ])
    def frame(canvas, document):
        canvas.saveState()
        w,h= A4
        canvas.setFillColor(colors.HexColor(PALETTE["navy"]))
        canvas.rect(0,h-13*mm,w,13*mm,stroke=0,fill=1)
        canvas.setFont("Helvetica-Bold",8)
        canvas.setFillColor(colors.white)
        canvas.drawString(18*mm,h-8*mm,"JAIR RIBEIRO  /  MARKET INTELLIGENCE")
        canvas.setStrokeColor(colors.HexColor(PALETTE["line"]))
        canvas.line(18*mm,14*mm,w-18*mm,14*mm)
        canvas.setFont("Helvetica",8)
        canvas.setFillColor(colors.HexColor(PALETTE["muted"]))
        canvas.drawString(18*mm,9*mm,"jairribeiro.com  /  Evidence-led Executive Advisory")
        canvas.drawRightString(w-18*mm,9*mm,f"{document.page}")
        canvas.restoreState()
    doc.build(story,onFirstPage=frame,onLaterPages=frame)
    result = buf.getvalue()
    if not result.startswith(b"%PDF") or len(result) < 2000:
        raise ValueError("Market brief PDF failed output validation.")
    return result


def _record_market_event(token: str, event: str, lens: str = "", detail: str = "") -> None:
    """Best-effort anonymous usage event. Never submit user notes or private responses."""
    if not token or event not in {"open","lens","decision","pdf_decision","pdf_review","csv_evidence"}:
        return
    try:
        _request_json(
            "POST", _rest_url("rpc/portfolio_market_signals_record_event_v1"),
            token=token, timeout=6,
            payload={"p_event":event,"p_lens":lens[:50],"p_detail":detail[:120]},
        )
    except (RuntimeError,ValueError,TimeoutError,KeyError,OSError):
        # Observability must never block verified evidence access.
        pass


def render_private_market_signals(session: dict, user: dict) -> None:
    """Only called after Advisory profile, password, membership and role checks."""
    token = str(session.get("access_token") or "")
    with st.container(key="market_signals_workspace"):
        st.html(MARKET_STYLE)
        st.html(
            '<section class="market-hero"><span class="eyebrow">'
            'JAIR RIBEIRO ADVISORY / MARKET INTELLIGENCE</span>'
            '<h2>AI &amp; Data Market Signals</h2>'
            '<p>Evidence before interpretation. Understand the market, challenge the assumptions, '
            'and make a better capability decision.</p></section>'
        )
        try:
            points, briefs = _load_curated(token)
            points, briefs, release = _release_snapshot(token,points,briefs)
        except (RuntimeError, PermissionError, ValueError, KeyError, TimeoutError, OSError) as exc:
            st.error("The verified market evidence is temporarily unavailable. "
                     "No cached or invented figures will be shown. Please retry.")
            return
        if release.get("published"):
            st.success(
                "Verified editorial edition: "+str(release.get("title") or "")+
                " · "+str(release.get("issue_date") or "")+
                ". Charts and downloads are restricted to this edition's approved evidence."
            )
        else:
            st.warning(
                "Initial editorial edition is still under source-by-source review. "
                "These dated observations remain an exploratory preview and must not be "
                "represented as a formally released market report."
            )
        viewer_key = "market_signals_open_" + str(user.get("id") or "member")
        if not st.session_state.get(viewer_key):
            _record_market_event(token,"open")
            st.session_state[viewer_key] = True
        family_count = len({p["source_family"] for p in points})
        periods = [str(p["verified_on"])[:10] for p in points]
        st.caption(
            f"Curated observations: {len(points)}  ·  Source families: {family_count}  ·  "
            f"Latest evidence verification: {max(periods)}  ·  Geography: Sweden"
        )
        overdue = [p for p in points if _freshness(p) == "Review overdue"]
        if overdue:
            st.warning(
                f"{len(overdue)} observations have passed their source-specific recheck interval. "
                "Their last verified values are retained with dates; the tool will not present them as current."
            )
        from page_advisory_market_observatory import render_market_observatory
        render_market_observatory(points)
        lens = str(st.session_state.get("market_observatory_section") or "pulse")
        geo = "Sweden"
        if st.session_state.get("market_signals_previous_lens") != lens:
            _record_market_event(token,"lens",lens)
            st.session_state["market_signals_previous_lens"] = lens
        _head("EDITORIAL INTERPRETATION","What the observed signals mean for the decisions ahead",
              "The dashboard shows factual evidence; this companion analysis records executive judgement, counterarguments and the next practical decision.")
        selected_brief = st.selectbox(
            "Decision theme",range(len(briefs)),format_func=lambda ix:briefs[ix]["title"],
            key="market_signals_decision",
        )
        brief=briefs[selected_brief]
        if st.session_state.get("market_signals_previous_decision") != brief["slug"]:
            _record_market_event(token,"decision",str(lens),str(brief["slug"]))
            st.session_state["market_signals_previous_decision"] = brief["slug"]
        grade=brief["support_level"]
        grade_label=("Two or more independent source families" if grade=="independent_sources"
                     else "Single-source analysis" if grade=="single_source" else "Context only")
        st.html(
            '<article class="market-thesis"><span class="market-kicker">'+html_escape(grade_label)+
            '</span><h3>'+html_escape(brief["title"])+'</h3><p>'+html_escape(brief["thesis"])+
            '</p></article>'
        )
        st.write(brief["interpretation"])
        st.html('<section class="market-outcome"><strong>DECISION TO MAKE</strong><p>'+
                html_escape(brief["decision_question"])+'</p><strong>FIRST ACTION</strong><p>'+
                html_escape(brief["recommended_action"])+'</p></section>')
        with st.expander("Challenge the conclusion · counterevidence and limitations",expanded=True):
            st.markdown("**What could change this reading**")
            st.write(brief["counterevidence"])
            st.markdown("**What these data cannot establish**")
            st.write(brief["limitations"])
            if grade=="independent_sources":
                st.caption("Independent source families offer contextual triangulation, not independent replication of the same metric.")
        by_code={p["code"]:p for p in points}
        support=[by_code[c] for c in brief["evidence_codes"]]
        _head("EVIDENCE TRAIL","Trace every claim to its origin")
        for p in support:
            source=_checked_url(p["source_url"])
            st.html(
                '<div class="market-source"><strong>'+html_escape(p["metric_label"])+
                ' · '+html_escape(_value(p))+'</strong><small>'+
                html_escape(p["geography"]+' · '+p["period_label"]+' · '+p["population_note"])+
                '</small><small>Source: <a href="'+html_escape(source,quote=True)+
                '" target="_blank" rel="noopener noreferrer">'+html_escape(p["source_title"])+
                '</a> · Published '+html_escape(p["published_on"])+' · Verified '+
                html_escape(p["verified_on"])+' · '+html_escape(_freshness(p))+
                '</small></div>'
            )
        _head("YOUR MATERIALS","Take this analysis into the leadership meeting",
              "The PDF includes an executive interpretation, evidence appendix with links, and a printable decision record.")
        try:
            data=executive_pdf(points,brief,geo)
        except (ValueError, KeyError, OSError):
            st.error("The report cannot be generated reliably from the current evidence.")
        else:
            st.download_button(
                "Download executive market decision brief · PDF",
                data=data,
                file_name="Jair_Ribeiro_AI_Data_Market_Decision_Brief.pdf",
                mime="application/pdf",
                key="market_signals_pdf",type="primary",
                use_container_width=True,
                on_click=_record_market_event,
                args=(token,"pdf_decision",str(lens),str(brief["slug"])),
            )
        st.markdown("#### Complete Market Review")
        st.caption(
            "The full executive edition includes a vector leadership-demand trend, "
            "AI and Data capability analysis, consulting context, leadership agenda and "
            "a source register listing observation dates and publisher links."
        )
        try:
            from page_advisory_market_review import market_review_pdf
            market_pdf=market_review_pdf(points,briefs)
        except (ValueError, KeyError, OSError) as exc:
            st.error("The complete market review cannot be validated for export.")
        else:
            st.download_button(
                "Download complete AI & Data Market Review · PDF",
                data=market_pdf,
                file_name="Jair_Ribeiro_AI_Data_Market_Review_2026_11.pdf",
                mime="application/pdf",
                key="market_review_pdf",
                use_container_width=True,
                on_click=_record_market_event,
                args=(token,"pdf_review","all","market-review"),
            )
        st.caption("Market Signals edition 1.0 · Independent research interpretation by Jair Ribeiro. "
                   "Not investment, recruitment or legal advice. Source populations, releases and methods govern the figures.")
