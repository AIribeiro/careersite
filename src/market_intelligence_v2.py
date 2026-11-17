"""Market Signals 2.0 — edition-bound executive intelligence.

Only consumes a verified Advisory member JWT and a signed-off publication
manifest. The report, decision briefs and reader app share one editorial
payload. No private career intelligence, speculative AI scores or unchecked
source records are used here.
"""
from __future__ import annotations

from html import escape as html_escape
from io import BytesIO
from math import isfinite
from urllib.parse import urlsplit
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable,
    KeepTogether,
)
from market_review_premium import (
    _sty, _P, _section, _callout, _stats, _bar_chart, _structured_table,
    _source_link, _num, _n, COPPER, BLUE, NAVY, RULE,
)

REQUIRED_TOP = (
    "title", "issue_date", "assessment", "why_it_matters",
    "what_changed", "themes", "decision_agenda", "outlook",
    "methodology_note",
)
REQUIRED_THEME = (
    "key", "title", "thesis", "evidence", "interpretation",
    "alternative", "implication", "recommendation", "monitor",
    "evidence_codes",
)
LENSES = (
    "investment", "workforce", "operating_model", "sourcing", "regional",
)
LENS_LABELS = {
    "investment": "AI investment and business priorities",
    "workforce": "Workforce and leadership capabilities",
    "operating_model": "Data and AI operating models",
    "sourcing": "Sourcing and consulting decisions",
    "regional": "Sector and regional differences",
}
STYLE = """
<style>
.ms-v2-reading{margin:18px 0 28px;padding:clamp(21px,4vw,39px);
background:#f8f6f1;border-top:3px solid #a97755;color:#193348}
.ms-v2-reading .kicker,.ms-v2-theme .kicker{font-size:11px;letter-spacing:.11em;
text-transform:uppercase;color:#936848;font-weight:750}
.ms-v2-reading h3{font:500 clamp(27px,4vw,40px)/1.17 Georgia,serif;
letter-spacing:-.025em;color:#132e42;margin:10px 0 17px}
.ms-v2-reading p,.ms-v2-theme p{font-size:15px;line-height:1.83;color:#354a59}
.ms-v2-theme{margin:17px 0 24px;padding:21px 22px;border:1px solid #e1dad0;background:#fffdf9}
.ms-v2-theme h3{font:500 clamp(23px,3vw,32px)/1.22 Georgia,serif;
color:#142f45;margin:10px 0}
.ms-v2-theme h4{font-size:12px;letter-spacing:.05em;text-transform:uppercase;
color:#965e41;margin:17px 0 5px}
.ms-v2-cite{font-size:12px;color:#52677a;padding:9px 0;border-bottom:1px solid #ded7cb;
overflow-wrap:anywhere}
.ms-v2-cite a{color:#1b5678}
@media(max-width:700px){.ms-v2-theme{padding:15px}.ms-v2-reading{padding:21px}
.ms-v2-reading p,.ms-v2-theme p{font-size:14px;line-height:1.72}}
</style>
"""


def _safe_url(value: object) -> str:
    url = str(value or "")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Unverified market evidence URL.")
    return url


def validate_editorial(payload: dict, points: list[dict], edition_slug: str) -> dict:
    """Fail closed on stale, unsupported or incomplete editorial claims."""
    if not isinstance(payload, dict) or any(not payload.get(k) for k in REQUIRED_TOP):
        raise ValueError("Executive research edition is incomplete.")
    if payload.get("edition_slug") != edition_slug:
        raise ValueError("The editorial analysis is not bound to this evidence edition.")
    by_code = {str(p.get("code")): p for p in points}
    if len(by_code) != len(points):
        raise ValueError("Duplicate evidence identifiers.")
    themes = payload["themes"]
    if not isinstance(themes, list) or len(themes) != 5:
        raise ValueError("Five distinct executive decision perspectives are required.")
    if {t.get("key") for t in themes if isinstance(t,dict)} != set(LENSES):
        raise ValueError("One or more executive decision perspectives are missing.")
    for theme in themes:
        if not isinstance(theme, dict) or any(not theme.get(k) for k in REQUIRED_THEME):
            raise ValueError("An executive analysis lacks interpretation or decision content.")
        codes=theme["evidence_codes"]
        if not isinstance(codes,list) or len(set(codes)) != len(codes) or not codes:
            raise ValueError("An analysis has missing or repeated sources.")
        for code in codes:
            if code not in by_code:
                raise ValueError("An analysis cites evidence not in the signed-off edition.")
            _safe_url(by_code[code]["source_url"])
        if len(str(theme["interpretation"])) < 100 or len(str(theme["recommendation"])) < 50:
            raise ValueError("Executive interpretation or recommendation is too thin.")
    if not isinstance(payload["decision_agenda"], list) or len(payload["decision_agenda"]) < 3:
        raise ValueError("Executive decision agenda is incomplete.")
    if not isinstance(payload["outlook"], list) or len(payload["outlook"]) < 2:
        raise ValueError("A conditional outlook requires at least two scenarios.")
    for item in payload["outlook"]:
        if any(not item.get(k) for k in ("period","reading","condition","leadership_response")):
            raise ValueError("An outlook scenario is missing its conditions.")
    for item in payload["decision_agenda"]:
        if any(not item.get(k) for k in ("decision","owner","action","horizon")):
            raise ValueError("Executive agenda entry is incomplete.")
    return payload


def load_published_editorial(token: str, edition_slug: str,
                             points: list[dict], request_json, rest_url):
    """Fetch only a published edition via the same member bearer token."""
    if not token:
        raise PermissionError("A verified Advisory member token is required.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{8,130}",edition_slug or ""):
        raise ValueError("The publication identity is invalid.")
    url=rest_url("portfolio_market_signal_editorial_v2?select=*"
                 "&edition_slug=eq."+edition_slug+
                 "&is_published=eq.true&order=published_at.desc&limit=1")
    rows=request_json("GET",url,token=token,timeout=12)
    if not isinstance(rows,list):
        raise RuntimeError("Verified executive analysis is unavailable.")
    if not rows:
        return None
    row=rows[0]
    return validate_editorial(row.get("analysis"),points,edition_slug)


def _page(canvas, doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(NAVY)
    canvas.rect(0,h-15*mm,w,15*mm,stroke=0,fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold",8)
    canvas.drawString(18*mm,h-9*mm,"JAIR RIBEIRO  /  EXECUTIVE MARKET INTELLIGENCE")
    canvas.setStrokeColor(RULE)
    canvas.line(18*mm,16*mm,w-18*mm,16*mm)
    canvas.setFillColor(colors.HexColor("#526475"))
    canvas.setFont("Helvetica",7.5)
    canvas.drawString(18*mm,10*mm,"jairribeiro.com   |   Market Signals Advisory 2.0")
    canvas.drawRightString(w-18*mm,10*mm,str(doc.page).zfill(2))
    canvas.restoreState()


def _new_document(title):
    stream=BytesIO()
    doc=SimpleDocTemplate(stream,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
       topMargin=22*mm,bottomMargin=21*mm,title=title,
       author="Jair Ribeiro | Enterprise AI & Data",)
    return stream,doc


def _p(styles,content,kind="body"):
    return _P(styles,content,kind)


def _evidence_items(points,codes):
    idx={p["code"]:p for p in points}
    return [idx[c] for c in codes]


def _value(point):
    n=_n(point)
    unit=point.get("metric_unit")
    return _num(n)+("%" if unit=="percent" else
                    "% YoY" if unit=="percent YoY" else
                    " advertisements" if unit=="advertisements" else
                    " "+str(unit or ""))


def _chapter(story,styles,theme,i,points):
    _section(story,styles,"%02d / %s"%(i,LENS_LABELS[theme["key"]]),
             theme["title"],theme["thesis"])
    for title,key in (
        ("The evidence","evidence"),
        ("Our interpretation","interpretation"),
        ("An alternative explanation","alternative"),
        ("The executive implication","implication"),
        ("Recommended decision","recommendation"),
        ("What would change our view","monitor"),
    ):
        story.append(_p(styles,title,"sub"))
        story.append(_p(styles,theme[key]))
    story.append(_p(styles,"EVIDENCE TRAIL","eyebrow"))
    for point in _evidence_items(points,theme["evidence_codes"]):
        story.append(_p(styles,point["metric_label"]+" / "+_value(point)+
           " / "+str(point["period_label"])+" / "+str(point["population_note"]),"small"))
        story.append(_source_link(styles,point,"Original publisher: "+str(point["source_title"])))


def _leadership_chart(story,styles,points):
    idx={p["code"]:p for p in points}
    names=(("Jun","jobtech_v1_jun_se"),("Jul","jobtech_v1_jul_se"),
           ("Aug","jobtech_v1_aug_se"),("Sep","jobtech_v1_sep_se"),
           ("Oct","jobtech_v1_oct_se"))
    data=[(name,_n(idx[code])) for name,code in names
          if code in idx and idx[code].get("period_complete") is True]
    if len(data)>2:
        story.append(_p(styles,"Selected leadership-title advertisements / Sweden / complete months","sub"))
        story.append(_bar_chart(styles,data,unit=" ads",colorscheme=BLUE))
        story.append(_p(styles,"A defined and deduplicated advertisement basket, not the full AI labour market or completed hires. Incomplete months are excluded.","small"))
        story.append(Spacer(1,9))


def build_executive_market_pdf(points: list[dict], editorial: dict,
                               edition_slug: str) -> bytes:
    """Standalone, versioned PDF from the exact member-visible edition."""
    validate_editorial(editorial,points,edition_slug)
    styles=_sty()
    stream,doc=_new_document("Swedish AI and Data Market Review | Executive Intelligence")
    story=[]
    story.extend([
        Spacer(1,30),
        _p(styles,"INDEPENDENT RESEARCH  /  SWEDEN  /  "+editorial["issue_date"],"eyebrow"),
        _p(styles,"Swedish AI & Data","large"),
        _p(styles,"Market Review","large"),
        _p(styles,editorial["title"],"lead"),
        HRFlowable(width="100%",thickness=2,color=COPPER,spaceBefore=5,spaceAfter=17),
        _callout(styles,"The central assessment",editorial["assessment"]),
        Spacer(1,20),
        _p(styles,"An executive publication on investment, workforce, business capabilities, sourcing and regional decisions.","body"),
        _p(styles,"Version "+str(editorial.get("version","2.0"))+"  |  "+
                editorial["issue_date"]+"  |  Signed-off evidence from "+
                str(len({p["source_family"] for p in points}))+
                " publishers  |  "+str(len(points))+" source observations","small"),
        _p(styles,"Published analysis is bound to its evidence edition. Later data releases cannot silently change these conclusions.","disclaimer"),
        PageBreak(),
    ])
    _section(story,styles,"Executive reading",
             "What is changing - and what leaders should decide")
    story.append(_p(styles,editorial["assessment"],"lead"))
    story.append(_p(styles,"Why it matters","sub"))
    story.append(_p(styles,editorial["why_it_matters"]))
    story.append(_p(styles,"What has changed","sub"))
    story.append(_p(styles,editorial["what_changed"]))
    story.append(_p(styles,"Five decisions requiring attention","sub"))
    for n,theme in enumerate(editorial["themes"],1):
        story.append(KeepTogether([
            _p(styles,"%02d / %s"%(n,theme["title"]),"sub"),
            _p(styles,theme["implication"],"small"),
        ]))
    story.append(PageBreak())
    _section(story,styles,"Market evidence",
             "The measurements behind our assessment",
             "Different indicators answer different questions. They are not a single AI maturity score or a causal model.")
    idx={p["code"]:p for p in points}
    items=[]
    for label,code in (
        ("Enterprise AI use (10+ employees)","scb_2026_ai_10plus"),
        ("Large-enterprise AI use","scb_2026_ai_250plus"),
        ("October AI/Data leadership ads","jobtech_v1_oct_se"),
    ):
        if code in idx:items.append((label,_value(idx[code])))
    if items:story.extend([_stats(styles,items),Spacer(1,19)])
    _leadership_chart(story,styles,points)
    story.append(_p(styles,
        "These figures represent different populations. Survey-reported adoption does not demonstrate business return; advertised titles are neither completed recruitment nor an economy-wide census.","body"))
    story.append(PageBreak())
    for i,theme in enumerate(editorial["themes"],1):
        _chapter(story,styles,theme,i,points)
        story.append(PageBreak())
    _section(story,styles,"Conditional outlook","What we expect - and what could prove us wrong")
    for scenario in editorial["outlook"]:
        story.extend([
            _p(styles,scenario["period"],"sub"),
            _p(styles,scenario["reading"]),
            _p(styles,"Condition: "+scenario["condition"],"small"),
            _p(styles,"Leadership response: "+scenario["leadership_response"],"small"),
        ])
    story.append(PageBreak())
    _section(story,styles,"Executive decision agenda",
             "What the leadership team should resolve")
    entries=[(x["decision"],x["owner"],x["horizon"],x["action"])
             for x in editorial["decision_agenda"]]
    story.append(_structured_table(styles,
        ["DECISION","ACCOUNTABLE FUNCTION","TIME FRAME","RECOMMENDED ACTION"],
        entries,[40*mm,38*mm,25*mm,71*mm]))
    story.append(Spacer(1,18))
    story.append(_callout(styles,"Research boundary",editorial["methodology_note"]))
    story.append(PageBreak())
    _section(story,styles,"Original evidence","Source and observation register")
    seen=set()
    for point in sorted(points,key=lambda p:(p["source_family"],p["code"])):
        if point["code"] in seen:raise ValueError("Repeated evidence record")
        seen.add(point["code"])
        story.append(KeepTogether([
            _p(styles,point["code"]+"  /  "+point["metric_label"],"sub"),
            _p(styles,_value(point)+"   |   "+str(point["geography"])+
               "   |   "+str(point["period_label"]),"small"),
            _p(styles,"Population: "+str(point["population_note"])+
               "   |   Published: "+str(point["published_on"])+
               "   |   Verified: "+str(point["verified_on"]),"tiny"),
            _source_link(styles,point,"Publisher: "+str(point["source_title"])),
        ]))
    story.append(_p(styles,
      "Source limitations, survey changes, incomplete periods and advertisement-classifier coverage govern every interpretation. Published evidence is not an individual company forecast.","disclaimer"))
    doc.build(story,onFirstPage=_page,onLaterPages=_page)
    data=stream.getvalue()
    if not data.startswith(b"%PDF") or len(data)<5000:
        raise ValueError("Executive market review failed PDF validation.")
    return data


def build_executive_decision_pdf(points: list[dict], editorial: dict,
                                 edition_slug: str, theme_key: str) -> bytes:
    validate_editorial(editorial,points,edition_slug)
    theme=next((t for t in editorial["themes"] if t["key"]==theme_key),None)
    if not theme:raise ValueError("Unknown executive decision perspective.")
    styles=_sty()
    stream,doc=_new_document("Market Signals | "+theme["title"])
    story=[
        Spacer(1,19),
        _p(styles,"MARKET SIGNALS / EXECUTIVE DECISION BRIEF","eyebrow"),
        _p(styles,theme["title"],"chapter"),
        _p(styles,theme["thesis"],"lead"),
        HRFlowable(width="100%",thickness=1.5,color=COPPER,spaceAfter=13),
    ]
    for heading,key in (
        ("Evidence","evidence"),("Our reading","interpretation"),
        ("What could explain it differently","alternative"),
        ("Business implication","implication"),
        ("Recommended action","recommendation"),
        ("What would change the recommendation","monitor"),
    ):
        story.append(_p(styles,heading,"sub"))
        story.append(_p(styles,theme[key]))
    story.append(PageBreak())
    _section(story,styles,"Source record",
             "Evidence and measurement boundaries")
    for item in _evidence_items(points,theme["evidence_codes"]):
        story.extend([
            _p(styles,item["metric_label"]+" / "+_value(item),"sub"),
            _p(styles,str(item["period_label"])+" / "+str(item["geography"])+
               " / "+str(item["population_note"]),"small"),
            _p(styles,"Caution: "+str(item["caveat"]),"small"),
            _source_link(styles,item,str(item["source_title"])),
        ])
    story.append(Spacer(1,16))
    story.append(_p(styles,"Review question","sub"))
    story.append(_p(styles,theme["monitor"]))
    story.append(_p(styles,"Research limits: "+editorial["methodology_note"],"small"))
    doc.build(story,onFirstPage=_page,onLaterPages=_page)
    data=stream.getvalue()
    if not data.startswith(b"%PDF") or len(data)<2200:
        raise ValueError("Executive decision brief failed PDF validation.")
    return data


def render_executive_intelligence(streamlit, editorial: dict,
                                  points: list[dict], edition_slug: str,
                                  member_token: str, record_event) -> None:
    """Premium native Streamlit reading experience, before raw Observatory."""
    validate_editorial(editorial,points,edition_slug)
    st=streamlit
    st.html(STYLE)
    st.html(
        '<section class="ms-v2-reading"><div class="kicker">Executive reading / '+
        html_escape(editorial["issue_date"])+'</div><h3>'+
        html_escape(editorial["title"])+'</h3><p>'+
        html_escape(editorial["assessment"])+'</p><h4>Why it matters</h4><p>'+
        html_escape(editorial["why_it_matters"])+'</p>'+
        '<h4>What has changed</h4><p>'+
        html_escape(editorial["what_changed"])+'</p></section>'
    )
    tabs=[LENS_LABELS[k] for k in LENSES]
    choice=st.selectbox("Executive decision perspective",LENSES,
             format_func=lambda k:LENS_LABELS[k],key="market_v2_theme")
    t=next(x for x in editorial["themes"] if x["key"]==choice)
    st.html('<article class="ms-v2-theme"><span class="kicker">'+
        html_escape(LENS_LABELS[choice])+'</span><h3>'+
        html_escape(t["title"])+'</h3><p><strong>'+
        html_escape(t["thesis"])+'</strong></p>'+
        ''.join('<h4>'+html_escape(label)+'</h4><p>'+html_escape(t[k])+'</p>'
                for label,k in (
                    ("What the data shows","evidence"),
                    ("Our interpretation","interpretation"),
                    ("A competing explanation","alternative"),
                    ("Business implications","implication"),
                    ("Recommended action","recommendation"),
                    ("What would change our assessment","monitor"),
                ))+'</article>')
    index={p["code"]:p for p in points}
    with st.expander("Check the evidence behind this assessment",expanded=False):
        for code in t["evidence_codes"]:
            p=index[code]
            st.html('<div class="ms-v2-cite"><strong>'+
                html_escape(p["metric_label"])+': '+
                html_escape(_value(p))+'</strong> / '+
                html_escape(p["period_label"])+' / '+
                html_escape(p["population_note"])+'<p><a href="'+
                html_escape(_safe_url(p["source_url"]),quote=True)+
                '" target="_blank" rel="noopener noreferrer">'+
                html_escape(p["source_title"])+'</a></p></div>')
    st.markdown("#### What leadership teams should do next")
    for item in editorial["decision_agenda"]:
        with st.expander(item["decision"]+"  ·  "+item["horizon"],expanded=False):
            st.write(item["action"])
            st.caption("Accountable function: "+item["owner"])
    st.markdown("#### What to monitor")
    for item in editorial["outlook"]:
        st.markdown("**"+item["period"]+"**")
        st.write(item["reading"])
        st.caption("Condition: "+item["condition"]+
                   "  |  Executive response: "+item["leadership_response"])
    st.caption(editorial["methodology_note"])
    st.markdown("#### Executive publications")
    full=build_executive_market_pdf(points,editorial,edition_slug)
    st.download_button(
        "Download complete Executive Market Review · PDF",
        data=full,mime="application/pdf",
        file_name="Jair_Ribeiro_Market_Signals_Executive_Review_"+
                  editorial["issue_date"]+".pdf",
        key="market_v2_complete_pdf",type="primary",use_container_width=True,
        on_click=record_event,args=(member_token,"pdf_review","all",edition_slug))
    focused=build_executive_decision_pdf(points,editorial,edition_slug,choice)
    st.download_button(
        "Download this Executive Decision Brief · PDF",
        data=focused,mime="application/pdf",
        file_name="Jair_Ribeiro_Market_Signals_"+choice+".pdf",
        key="market_v2_decision_pdf",use_container_width=True,
        on_click=record_event,args=(member_token,"pdf_decision",choice,edition_slug))
