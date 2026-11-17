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
    """Full executive research, not a stitched dashboard export.

    One edition manifest drives the website, this complete publication, and
    five focused decision briefs. The PDF design is shared with the free
    historical report, without changing either edition's factual scope.
    """
    from reportlab.platypus import CondPageBreak
    from market_publication_design import (
        P, assemble, bars, decision_table, metric_cards, panel, section,
        sources_table, styles,
    )
    validate_editorial(editorial,points,edition_slug)
    idx={p["code"]:p for p in points}
    for code in ("scb_2026_ai_10plus","scb_2026_ai_250plus",
                 "scb_lor_2026q2_total","jobtech_v1_oct_se"):
        if code not in idx:
            raise ValueError("Executive publication is missing a signed-off cover indicator.")
    s=styles()
    cover={
      "title":"AI & Data Market Review",
      "subtitle":editorial["title"],
      "assessment":editorial["assessment"],
      "question":"Where should capital, talent and governance move first - and what would change our mind?",
      "edition":"EXECUTIVE EDITION 2.0 / SWEDEN",
      "issue":editorial["issue_date"],
      "metrics":[
        (_value(idx["scb_2026_ai_10plus"]),"Enterprises using AI",
         "Sweden 2026 | Firms with 10+ staff"),
        (_value(idx["scb_2026_ai_250plus"]),"Large firms using AI",
         "2026 | Enterprises with 250+ staff"),
        (str(int(float(idx["jobtech_v1_oct_se"]["value"]))),"Senior AI/Data adverts",
         "October 2026 | Selected title basket"),
      ],
    }
    story=[]
    section(story,"01 / Executive reading",
        "What is changing - and what leaders should decide",
        editorial["assessment"],sty=s)
    story.append(panel("Why this matters",
        "AI adoption and market recruitment are different business signals",
        editorial["why_it_matters"],sty=s))
    story.append(Spacer(1,16))
    story.append(P("What changed since the earlier research","h2",sty=s))
    story.append(P(editorial["what_changed"],"body",sty=s))
    story.append(P("Five decision perspectives","h2",sty=s))
    for i,t in enumerate(editorial["themes"],1):
        story.append(KeepTogether([
            P(f"{i:02d} / {t['title']}","h2",sty=s),
            P(t["thesis"],"body_compact",sty=s)
        ]))
    story.append(Spacer(1,14))
    story.append(CondPageBreak(285))

    section(story,"02 / The evidence",
        "Read different measurements together - without adding them",
        "These indicators cover different populations and time frames. "
        "Their value lies in the questions they raise together, not in an "
        "invented national AI market score.",sty=s)
    story.append(metric_cards([
        (_value(idx["scb_2026_ai_10plus"]),"AI use across enterprises",
         "Swedish firms, 10+ staff | 2026"),
        (_value(idx["scb_2026_ai_250plus"]),"AI use among large firms",
         "250+ employees | 2026"),
        (str(int(float(idx["jobtech_v1_oct_se"]["value"]))),
         "Selected senior AI/Data adverts",
         "October 2026 | National basket"),
    ],sty=s))
    story.append(Spacer(1,18))
    months=(("June","jobtech_v1_jun_se"),("July","jobtech_v1_jul_se"),
            ("August","jobtech_v1_aug_se"),("September","jobtech_v1_sep_se"),
            ("October","jobtech_v1_oct_se"))
    chart=[(n,float(idx[code]["value"])) for n,code in months
           if code in idx and idx[code].get("period_complete") is True]
    if len(chart)>2:
        story.append(P("Selected AI/Data leadership-title advertisements",
                       "h2",sty=s))
        story.append(bars(chart,suffix=" ads",sty=s))
        story.append(P(
          "Complete months only. This is a deduplicated, defined title basket: "
          "not all AI-related vacancies, completed appointments or a market-wide "
          "recruitment census.","caption",sty=s))
        story.append(Spacer(1,11))
    if all(x in idx for x in ("scb_lor_2026q2_advertised",
                             "scb_lor_2026q2_other_channels")):
        story.append(P("Recruitment beyond public job advertisements",
                       "h2",sty=s))
        story.append(bars([
          ("Advertised opportunities",float(idx["scb_lor_2026q2_advertised"]["value"])),
          ("Other recruitment channels",float(idx["scb_lor_2026q2_other_channels"]["value"])),
        ],sty=s))
        story.append(P(
          "SCB whole-economy Q2 2026 survey estimates. These are not AI-specific "
          "opportunities and must not be added to JobTech title counts.",
          "caption",sty=s))
    story.append(Spacer(1,18))
    story.append(CondPageBreak(310))

    for i,t in enumerate(editorial["themes"],1):
        story.append(CondPageBreak(255))
        section(story,f"0{i+2} / {LENS_LABELS[t['key']]}",
            t["title"],t["thesis"],sty=s)
        story.append(P("What the evidence says","h2",sty=s))
        story.append(P(t["evidence"],"body",sty=s))
        story.append(P("Our reading","h2",sty=s))
        story.append(P(t["interpretation"],"body",sty=s))
        story.append(panel("An explanation to test",
            "What else could produce the same observation?",t["alternative"],sty=s))
        story.append(Spacer(1,12))
        story.append(P("Business implication","h2",sty=s))
        story.append(P(t["implication"],"body",sty=s))
        story.append(panel("Executive decision",
            "What leadership should do",t["recommendation"],dark=True,sty=s))
        story.append(Spacer(1,12))
        story.append(P("Evidence that would change the recommendation",
                       "h2",sty=s))
        story.append(P(t["monitor"],"body_compact",sty=s))
        story.append(P(
          "Referenced observations: "+", ".join(t["evidence_codes"])+
          ". Original sources and exact measurement dates appear in the "
          "final source register.","caption",sty=s))
        story.append(Spacer(1,16))

    story.append(PageBreak())
    section(story,"08 / Outlook",
        "Conditional outlook: watch what actually changes",
        "Scenarios are not probability forecasts. Each reading is tied to "
        "an observable condition and a specific leadership response.",sty=s)
    for t in editorial["outlook"]:
        story.append(KeepTogether([
            P(t["period"],"h2",sty=s),
            P(t["reading"],"body",sty=s),
            panel("If the evidence changes","Condition and leadership response",
              "Condition: "+t["condition"]+
              " | Leadership response: "+t["leadership_response"],sty=s),
            Spacer(1,10),
        ]))
    # Keep the next agenda with the downside scenario if space permits.
    # A forced new page previously left one scenario almost alone.
    story.append(Spacer(1,18))
    story.append(CondPageBreak(275))

    section(story,"09 / Executive decision agenda",
        "Decisions to take into the next executive meeting",
        "Use the market evidence to challenge a decision, then supply your "
        "organisation's own operational, financial and workforce information "
        "before making the commitment.",sty=s)
    agenda=[(x["decision"],x["owner"],x["horizon"],x["action"])
            for x in editorial["decision_agenda"]]
    story.append(decision_table(agenda,sty=s))
    # Avoid a page carrying only a repeated methodology panel.
    story.append(PageBreak())

    section(story,"10 / Research transparency",
        "Source and observation register",
        "The complete evidence ledger is included for independent checking. "
        "Each observation retains its original period, geography, value and "
        "clickable source. The editorial discussion and PDF use this same "
        "signed-off edition; later source releases cannot alter it.",sty=s)
    story.append(P(
       "Research method and limits: "+editorial["methodology_note"],
       "body_small",sty=s))
    story.append(Spacer(1,9))
    story.append(sources_table(points,_value,sty=s))
    story.append(Spacer(1,13))
    story.append(P(
       "Source measurements describe different populations. Survey uptake "
       "is not return on investment; digital roadmap budgets are not company "
       "AI spending; vacancy advertisements are not hiring outcomes. "
       "Partial months are not extrapolated.",
       "body_small",sty=s))
    return assemble(story,cover,
      "Jair Ribeiro | Swedish AI and Data Market Review | Executive Edition 2.0",
      min_bytes=10000)


def build_executive_decision_pdf(points: list[dict], editorial: dict,
                                 edition_slug: str, theme_key: str) -> bytes:
    """Focused independent research with a decision, challenge and evidence."""
    from market_publication_design import (
        P, assemble, decision_table, metric_cards, panel, section,
        sources_table, styles,
    )
    validate_editorial(editorial,points,edition_slug)
    theme=next((t for t in editorial["themes"] if t["key"]==theme_key),None)
    if theme is None:
        raise ValueError("Unknown executive decision perspective.")
    evidence=_evidence_items(points,theme["evidence_codes"])
    if not evidence:
        raise ValueError("Decision brief has no authenticated source evidence.")
    s=styles()
    def condensed_value(point):
        number=float(point["value"])
        unit=str(point.get("metric_unit") or "")
        if not isfinite(number):
            raise ValueError("Non-finite evidence cannot appear on the cover.")
        if abs(number)>=10000 and unit in {"vacancies","advertisements"}:
            return f"{number/1000:,.1f}k"
        label=f"{int(number):,}" if number.is_integer() else f"{number:,.1f}"
        return label+("%" if unit=="percent" else "")
    metrics=[]
    for item in (evidence+[evidence[-1]]*3)[:3]:
        unit=str(item.get("metric_unit") or "").replace("percent","")
        note=(unit+" | " if unit.strip() else "")+str(item["period_label"])
        metrics.append((condensed_value(item),
          str(item.get("metric_label") or "Verified market observation")[:58],
          note[:70]))
    cover={
        "title":"Executive Decision Brief",
        "subtitle":theme["title"],
        "assessment":theme["thesis"]+" "+theme["implication"],
        "question":"Which decision would you revisit if the next evidence release contradicts your assumption?",
        "edition":"MARKET SIGNALS / "+theme_key.upper(),
        "issue":editorial["issue_date"],
        "metrics":metrics,
    }
    story=[]
    section(story,"01 / Executive decision",
        theme["title"],theme["thesis"],sty=s)
    story.append(P("Evidence, not assumption","h2",sty=s))
    story.append(P(theme["evidence"],"body",sty=s))
    story.append(P("Our independent interpretation","h2",sty=s))
    story.append(P(theme["interpretation"],"body",sty=s))
    story.append(panel("Challenge the interpretation",
        "An alternative explanation",theme["alternative"],sty=s))
    story.append(Spacer(1,12))
    story.append(P("What this means for business","h2",sty=s))
    story.append(P(theme["implication"],"body",sty=s))
    story.append(PageBreak())

    section(story,"02 / Decision playbook",
        "From the market signal to an accountable management choice",
        "A specific capability or investment decision should have an owner, "
        "an action and a review condition - not simply a preferred headline.",
        sty=s)
    story.append(panel("Recommended action",
        "The decision worth taking now",theme["recommendation"],dark=True,sty=s))
    story.append(Spacer(1,18))
    story.append(decision_table([
        ("Frame the choice","Executive sponsor","Now",theme["implication"]),
        ("Take the first step","Capability / business owner","Next 30 days",
         theme["recommendation"]),
        ("Review the decision","Strategy / HR / AI leadership","Next evidence release",
         theme["monitor"]),
    ],sty=s))
    # The monitoring condition is already recorded in the decision table.
    # Repeating it here pushes a lone paragraph to an almost empty page.
    story.append(PageBreak())

    section(story,"03 / Evidence trail",
        "Original source record",
        "All cited evidence is retained here with its scope and publisher. "
        "The reading above is an editorial judgement, not a causal claim "
        "drawn automatically from disconnected indicators.",sty=s)
    story.append(sources_table(evidence,_value,sty=s))
    story.append(Spacer(1,13))
    story.append(P(
       "Before acting, test the recommendation against your organisation's "
       "own performance baseline, workforce capabilities, risk posture and "
       "operational constraints.", "body_small",sty=s))
    return assemble(story,cover,
        "Jair Ribeiro | Executive Decision Brief | "+theme["title"],
        min_bytes=5000)


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
    st.markdown("#### Download the complete executive market review")
    st.caption(
        "Complete November research report: five executive analyses, "
        "conditional outlook, leadership decisions, charts and original evidence. "
        "PDF included with your Advisory account."
    )
    full=build_executive_market_pdf(points,editorial,edition_slug)
    st.download_button(
        "Download complete Executive Market Review · PDF",
        data=full,mime="application/pdf",
        file_name="Jair_Ribeiro_Market_Signals_Executive_Review_"+
                  editorial["issue_date"]+".pdf",
        key="market_v2_complete_pdf",type="primary",use_container_width=True,
        on_click=record_event,args=(member_token,"pdf_review","all",edition_slug))
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
    st.markdown("#### Download this executive decision brief")
    st.caption("Focused PDF for the selected executive decision perspective.")
    focused=build_executive_decision_pdf(points,editorial,edition_slug,choice)
    st.download_button(
        "Download this Executive Decision Brief · PDF",
        data=focused,mime="application/pdf",
        file_name="Jair_Ribeiro_Market_Signals_"+choice+".pdf",
        key="market_v2_decision_pdf",use_container_width=True,
        on_click=record_event,args=(member_token,"pdf_decision",choice,edition_slug))
