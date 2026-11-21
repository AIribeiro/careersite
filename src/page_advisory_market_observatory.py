"""AI & Data Market Signals — multi-dashboard public evidence observatory.

All inputs are drawn from the separately curated, published, RLS-protected
portfolio_market_signal_points publication layer. This module NEVER loads
private job_market_insights, applicant records, forecasts, or owner analytics.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape
import csv
from io import StringIO
import math

import altair as alt
import pandas as pd
import streamlit as st
from market_labelled_bars import labelled_bars_html

DASHBOARDS = {
    "pulse": "Executive evidence overview",
    "demand": "AI & Data leadership advertisements",
    "adoption": "Enterprise AI adoption & capabilities",
    "talent": "Skills and management pay — under review",
    "commercial": "Consulting and sector context",
    "signals": "Interpretation and evidence limits",
    "trends": "Comparable historical observations",
    "ledger": "Sources and measurement methods",
}
COLORS = {"ink":"#183149","copper":"#AD7956","blue":"#547A8F","green":"#527365","grey":"#77848C"}
CADENCE_DAYS = {
    "scb_enterprise_ai_adoption":410,
    "af_jobtech_target_demand":15,
    "brainville_consulting_market":50,
    "techsverige_market_analysis":190,
    "manpower_employment_outlook":110,
    "scb_private_management_salary":410,
    "almega_services_indicator":110,
    "ki_konjunkturbarometern":48,
    "swedbank_pmi":48,
}
CSS = """
<style>
.st-key-market_signals_workspace .ms-dashboard-lead {
 background:#F8F6F2;border:1px solid #E3DED5;border-left:3px solid #B17B58;
 padding:17px 21px;margin:15px 0;line-height:1.7;color:#3D5161
}
.st-key-market_signals_workspace .ms-dashboard-lead h4 {
 font:500 25px/1.23 Georgia,serif;color:#1B3248;margin:0 0 9px
}
.st-key-market_signals_workspace .ms-dashboard-lead p {margin:0;font-size:13px}
.st-key-market_signals_workspace .ms-dashboard-section {
 font:500 26px/1.2 Georgia,serif;color:#1B3248;margin:30px 0 8px
}
.st-key-market_signals_workspace .ms-tension {
 background:#122B41;color:#F5F6F4;padding:21px 24px;margin:16px 0;
 border-top:2px solid #BA875D;line-height:1.7
}
.st-key-market_signals_workspace .ms-tension strong{color:#EBC4A3}
.st-key-market_signals_workspace .ms-tension p{color:#E6EDF1;font-size:13px;margin:8px 0 0}
.st-key-market_signals_workspace .ms-evidence-note {
 font-size:12px;color:#5F6D79;line-height:1.7;
 border-bottom:1px solid #E1DDD5;padding:11px 0
}
@media(max-width:720px) {
 .st-key-market_signals_workspace .ms-dashboard-lead{padding:16px}
 .st-key-market_signals_workspace .ms-tension{padding:17px}
}
</style>
"""


def _point_map(points: list[dict]) -> dict[str,dict]:
    return {str(p["code"]):p for p in points}


def _codes(points: list[dict], names: list[str]) -> list[dict]:
    index=_point_map(points)
    return [index[c] for c in names if c in index]


def _number(n: object, *, decimals: int = 1) -> str:
    x=float(n)
    if not math.isfinite(x):
        raise ValueError("Non-finite curated observation.")
    return f"{x:,.{decimals}f}".rstrip("0").rstrip(".") if not x.is_integer() else f"{int(x):,}"


def _value(point: dict) -> str:
    unit=str(point.get("metric_unit") or "")
    from market_review_premium import _num
    val=_num(point["value"])
    if unit=="percent":return val+"%"
    if unit in ("SEK/month","SEK_per_month"):return val+" SEK/mo"
    if unit in ("percentage points","percent YoY"):return val+(" pp" if unit=="percentage points" else "% YoY")
    return val+" "+unit


def _when(p:dict) -> str:
    return str(p.get("period_label") or p["period_end"])


def _freshness(point:dict, on:date|None=None) -> str:
    on=on or date.today()
    verified=date.fromisoformat(str(point["verified_on"])[:10])
    allowed=CADENCE_DAYS.get(str(point.get("source_family")),90)
    if verified>on:return "Future verification — investigate"
    return "Overdue for recheck" if (on-verified).days>allowed else "Within review interval"


def _source_note(points:list[dict], *, caveat:str|None=None) -> None:
    if not points:return
    names=sorted({str(p["source_title"]) for p in points})
    period=", ".join(sorted({str(p["period_label"]) for p in points}))
    st.caption("Source: "+" / ".join(names)+". Periods: "+period+".")
    if caveat:st.caption(caveat)


def _heading(title:str, lead:str="") -> None:
    st.html('<h3 class="ms-dashboard-section">'+escape(title)+'</h3>')
    if lead:st.caption(lead)


def _intro(title:str, text:str) -> None:
    st.html('<section class="ms-dashboard-lead"><h4>'+escape(title)+
        '</h4><p>'+escape(text)+'</p></section>')


def _cards(items:list[tuple[str,dict|None,str]]) -> None:
    if not items:return
    for i in range(0,len(items),3):
        group=items[i:i+3]
        cols=st.columns(len(group),gap="small")
        for col,(title,p,scope) in zip(cols,group):
            with col:
                if p is None:
                    st.metric(title,"—")
                    st.caption("Awaiting reviewed publisher evidence.")
                    continue
                st.metric(title,_value(p),help=f"{p['source_title']} · {_when(p)}")
                st.caption(scope or f"{_when(p)} · {_freshness(p)}")


def _bars(items:list[dict], label_map:dict[str,str], *,
          title:str, unit:str, denominator:str, color:str="#183149") -> None:
    rows=[{
        "label":label_map[p["code"]],
        "value":float(p["value"]),
        "display_value":_value(p),
        "period":_when(p),
        "source":p["source_title"],
    } for p in items if p["code"] in label_map]
    if not rows:return
    # Render real, wrapping label text. Axis labelLimit only increases the
    # clipping margin and does not guarantee complete text on mobile devices.
    rows.sort(key=lambda row:row["value"],reverse=True)
    _heading(title,denominator)
    st.html(labelled_bars_html(rows,color=color,unit_label=unit))


def leadership_timeline(points:list[dict], *, include_partial:bool=False) -> list[dict]:
    """Retain one vintage per geography/full publication month, never sum nested regions."""
    qualified=[p for p in points
               if p.get("series_code")=="jobtech_ai_data_leadership_v1"
               and (include_partial or p.get("period_complete") is True)
               and p.get("metric_unit")=="advertisements"
               and p.get("period_start") and p.get("period_end")]
    unique={}
    for p in sorted(qualified,key=lambda x:(str(x["verified_on"]),str(x["code"]))):
        unique[(p["geography"],p["period_start"],p["period_end"])]=p
    return sorted(unique.values(),key=lambda p:(p["period_start"],p["geography"]))


def _executive_pulse(points:list[dict]) -> None:
    idx=_point_map(points)
    _intro(
        "Market evidence: different measures and reporting periods",
        "Enterprise adoption, senior leadership advertisements, organisational capabilities "
        "and consulting conditions measure different populations and update at different speeds. "
        "This board separates them. It does not turn unlike figures into a single market score.",
    )
    _cards([
        ("Enterprise AI use · 10+",idx.get("scb_2026_ai_10plus"),"SCB 2026 · enterprises with at least 10 employees"),
        ("Large-enterprise AI use",idx.get("scb_2026_ai_250plus"),"SCB 2026 · enterprises with 250+ employees"),
        ("AI/Data leadership adverts · Oct",idx.get("jobtech_v1_oct_se"),"JobTech v1 · Sweden · complete month"),
        ("In-house analytics personnel",idx.get("scb_2026_analytics_internal"),"SCB 2026 · 10+ employee enterprises"),
        ("Consulting assignments · YoY",idx.get("brainville_202610_assignments_yoy"),"Brainville · overall Swedish consulting market"),
        ("Available consultants · YoY",idx.get("brainville_202610_consultants_yoy"),"Brainville · overall Swedish consulting market"),
    ])
    _heading("Executive implications and questions for review")
    stories=[
      ("Adoption ≠ organisational readiness",
       "Large organisations report extensive AI use; the skills and data barriers come from a "
       "different, non-adopting survey group. Use the data to audit your own operating model, "
       "not to infer that adopters lack capability.",
       ["scb_2026_ai_250plus","scb_2026_ai_expertise_barrier"]),
      ("Activity ≠ recruitment",
       "A narrowly classified AI/Data leadership title series can rise while hiring processes "
       "remain selective. The basket observes adverts, not hires, completed interviews or offers.",
       ["jobtech_v1_sep_se","jobtech_v1_oct_se"]),
      ("Consulting demand ≠ specialist scarcity",
       "Brainville measures more listed assignments and an even faster increase in available "
       "consultants across all disciplines. The signals merit procurement scrutiny, not an "
       "assertion that AI consulting supply or prices changed.",
       ["brainville_202610_assignments_yoy","brainville_202610_consultants_yoy"]),
    ]
    for title,narrative,codes in stories:
        used=_codes(points,codes)
        if len(used)!=len(codes):continue
        st.html('<section class="ms-tension"><strong>'+escape(title)+'</strong><p>'+
            escape(narrative)+'</p></section>')
        _source_note(used)
    st.caption(
        "Method: each claim has a defined publisher and observation vintage. "
        "The charts below are explorations, not personalised offer forecasting."
    )


def _demand(points:list[dict]) -> None:
    series=leadership_timeline(points)
    if not series:
        st.warning("Reviewed AI/Data leadership-demand time series is unavailable.")
        return
    _intro(
        "Selected senior leadership advertisements over time",
        "The frozen title-basket v1 is a deliberately narrow measure of published strategic AI/Data "
        "leadership advertisements. It is not a labour-market census. Each month is deduplicated, "
        "and incomplete periods are shown separately rather than joined to the trend.",
    )
    geo_choices=[x for x in ("Sweden","Västra Götaland","Stockholm")
                 if x in {p["geography"] for p in series}]
    geos=st.multiselect("Regions to compare",geo_choices,
        default=geo_choices, key="market_observatory_demand_geography",
        help="National and regional cohorts overlap. Never sum them.")
    selected=[p for p in series if p["geography"] in geos]
    if selected:
        chart_data=pd.DataFrame([{
            "Month":pd.to_datetime(p["period_start"]),
            "Publication period":p["period_label"],
            "Advertisements":int(p["value"]),
            "Geography":p["geography"],
            "Publisher":p["source_title"],
        } for p in selected])
        chart=alt.Chart(chart_data).mark_line(point=True,strokeWidth=3).encode(
            x=alt.X("Month:T",title="Complete publication month",axis=alt.Axis(format="%b %Y")),
            y=alt.Y("Advertisements:Q",title="Qualifying advertisements",scale=alt.Scale(zero=True)),
            color=alt.Color("Geography:N",scale=alt.Scale(
                domain=geo_choices,
                range=[COLORS["ink"],COLORS["copper"],COLORS["blue"]][:len(geo_choices)])),
            tooltip=["Publication period:N","Geography:N",
                     alt.Tooltip("Advertisements:Q",format=",d")],
        ).properties(height=335)
        st.altair_chart(chart,use_container_width=True)
        latest_month=max(str(p["period_start"]) for p in selected)
        latest=[p for p in selected if str(p["period_start"])==latest_month]
        _cards([(p["geography"]+" · latest complete",p,p["period_label"]) for p in latest])
    else:st.info("Select at least one geography to display the complete-month trend.")
    partial=[p for p in leadership_timeline(points,include_partial=True) if not p["period_complete"]]
    if partial:
        with st.expander("Incomplete reporting period · separately observed"):
            st.caption("Month-to-date values are not extrapolated, treated as a complete monthly count, or compared directly with October.")
            st.dataframe([{"Geography":p["geography"],"Period":p["period_label"],
                "Qualifying ads":int(p["value"]),"Verified":p["verified_on"]}
                for p in partial],hide_index=True,use_container_width=True)
    _heading("Regional comparability")
    st.caption(
        "Sweden includes Västra Götaland and Stockholm, so the regions cannot be added to the "
        "national count. Small counts mean that a change of one or two advertisements can make "
        "a visually large percentage change. These are advertisements, not employer hires."
    )
    st.dataframe([{"Region":p["geography"],"Month":p["period_label"],"Adverts":int(p["value"]),
        "Measurement":"Complete month"} for p in series],
        hide_index=True,use_container_width=True)
    _source_note(series,caveat="Retrospective API indexing may revise historical monthly counts; classifier v1 is frozen.")


def _adoption(points:list[dict]) -> None:
    idx=_point_map(points)
    _intro(
        "Enterprise AI use and organisational capability",
        "The same enterprise survey provides several useful perspectives, but not all percentages "
        "have the same denominator. Company-size adoption, analytics capability and barriers "
        "among firms that considered AI but did not adopt it appear as distinct analyses.",
    )
    _cards([
        ("Swedish enterprises using AI",idx.get("scb_2026_ai_10plus"),"SCB · all firms with 10+ employees"),
        ("Large-enterprise AI use",idx.get("scb_2026_ai_250plus"),"SCB · 250+ employees"),
        ("Internal data analytics personnel",idx.get("scb_2026_analytics_internal"),"SCB · 10+ employees"),
    ])
    groups=[
        ("AI adoption by enterprise size",[
          ("scb_2026_ai_10to49","10–49 employees"),
          ("scb_2026_ai_50to249","50–249 employees"),
          ("scb_2026_ai_250plus","250+ employees"),
        ],"Same survey year; mutually exclusive size bands. The 10+ overall figure is not a fourth band."),
        ("Organisational data and technology capability",[
          ("scb_2026_analytics_internal","In-house analytics personnel"),
          ("scb_2026_data_analytics_use","Conducting data analysis"),
          ("scb_2026_bi_use","Business intelligence software"),
          ("scb_2026_ict_specialists","Employing IT specialists"),
        ],"Measures are not mutually exclusive and do not indicate effectiveness or maturity."),
        ("Why some companies considered—but did not adopt—AI",[
          ("scb_2026_ai_expertise_barrier","Relevant expertise missing"),
          ("scb_2026_ai_privacy_barrier","Privacy / data protection concern"),
          ("scb_2026_ai_data_quality_barrier","Data access or quality"),
        ],"Denominator: only enterprises that considered AI but chose not to use it. Multiple barriers may be reported."),
    ]
    for title,rows,denom in groups:
        items=_codes(points,[x[0] for x in rows])
        if items:
            _bars(items,dict(rows),title=title,unit="Reported share (%)",denominator=denom)
            _source_note(items)
    st.caption(
        "SCB changed sector coverage and industry classifications in 2026. "
        "Year-on-year comparisons must be evaluated before publication."
    )


def _talent(points:list[dict]) -> None:
    idx=_point_map(points)
    _intro("AI skills and management-pay indicators: publication status",
           "AI keyword mentions, occupational group coverage and managerial compensation "
           "are different signals. The former measures job-ad wording; the latter gives broad "
           "occupational salary benchmarks, not AI Director compensation.")
    tech=_codes(points,["market_context_20261116_01","market_context_20261116_02"])
    if tech:
        _heading("AI-related language outside IT occupations")
        _cards([(p["metric_label"],p,p["period_label"]) for p in tech])
        st.caption("AI keyword occurrences are not unique vacancies, completed hires or skills proficiency.")
        _source_note(tech)
    else:
        st.info("TechSverige's AI-occupation measures are queued for source review. No unapproved figures are displayed.")
    wage=_codes(points,["market_context_20261116_09","market_context_20261116_10",
                         "market_context_20261116_11","market_context_20261116_12"])
    if wage:
        _heading("Management compensation · occupational proxies")
        bands=[(p["code"],p) for p in wage]
        st.dataframe([{"Occupational proxy":p["metric_label"],
            "SEK/month":int(p["value"]),"Reference year":p["period_label"],
            "Population":p["population_note"],"Source":p["source_title"]}
            for _,p in bands],hide_index=True,use_container_width=True)
        st.caption("SSYK categories are broad. These data are NOT a salary range for AI/Data leadership roles.")
        _source_note(wage)
    else:
        st.info("SCB managerial compensation proxies are staged for publisher and editorial verification.")
    _heading("Leadership capability, not just recruitment")
    st.write(
        "Use title-basket evidence to determine whether the organisation should pursue an external "
        "hire, internal capability-building or specialist support. Specify decision rights and the "
        "measurable business outcome first; market volume cannot identify the best operating model."
    )


def _context_pair(points:list[dict], names:list[tuple[str,str]],
                  title:str, scope:str, units:str) -> None:
    selected=_codes(points,[x[0] for x in names])
    if not selected:return
    _bars(selected,dict(names),title=title,unit=units,denominator=scope,color=COLORS["blue"])
    _source_note(selected)


def _commercial(points:list[dict]) -> None:
    idx=_point_map(points)
    _intro(
        "Consulting activity and wider sector context",
        "These contextual measures explain the conditions surrounding AI and Data capability "
        "decisions. They are broader than specialist AI hiring and should not be read as direct "
        "signals of AI leadership vacancies.",
    )
    _context_pair(points,[
        ("brainville_202610_assignments_yoy","Published consulting assignments"),
        ("brainville_202610_consultants_yoy","Available consultants"),
    ],"Consulting marketplace: year-on-year changes",
    "Swedish Brainville marketplace, all disciplines · October 2026; both are growth rates of different cohorts.",
    "Change from prior year (%)")
    _context_pair(points,[
        ("market_context_20261116_16","Remote / hybrid total"),
        ("market_context_20261116_17","Hybrid only"),
        ("market_context_20261116_18","Fully remote only"),
    ],"Consulting work arrangements","Brainville listings across all consultant professions, October 2026; component shares overlap with total.",
    "Share of listed assignments (%)")
    outlook=[
        ("market_context_20261116_03","IT & Tech"),
        ("market_context_20261116_04","Services & consulting"),
        ("market_context_20261116_05","Västra Götaland · all sectors"),
        ("market_context_20261116_06","Sweden · all sectors"),
        ("market_context_20261116_07","Finance & insurance"),
        ("market_context_20261116_08","Manufacturing / automotive / defence"),
    ]
    _context_pair(points,outlook,"Employer employment intentions · Q4 2026",
      "ManpowerGroup's same Q4 employer survey. Net hiring expectation is share planning to increase minus decrease—not recruitment counts.",
      "Net employment outlook (percentage points)")
    ict=_codes(points,["market_context_20261116_13","market_context_20261116_14","market_context_20261116_15"])
    if ict:
        _heading("ICT sector: output and workforce signals")
        _cards([(p["metric_label"],p,"Almega · Q2 2026 · overall ICT industry") for p in ict])
        st.caption(
            "These come from related sector accounts and share an underlying reporting family. "
            "A divergence cannot prove that AI caused job losses."
        )
        _source_note(ict)
    ki=_codes(points,["market_context_20261116_19","market_context_20261116_20"])
    if ki:
        _context_pair(points,[
            ("market_context_20261116_19","Expected employment · next 3 months"),
            ("market_context_20261116_20","Reported employment · past 3 months"),
        ],"Services-sector expectations versus reported employment",
        "KI October 2026 services business survey. Both are net-balance survey questions, not payroll counts.",
        "Survey net balance")
    pmi=_codes(points,["market_context_20261116_21","market_context_20261116_22"])
    if pmi:
        _heading("Services activity versus workforce conditions")
        _cards([(p["metric_label"],p,p["period_label"]) for p in pmi])
        st.caption("PMI is a diffusion index, and the employment streak ends in September, not October.")
        _source_note(pmi)
    if not (idx.get("market_context_20261116_03") or idx.get("market_context_20261116_13")):
        st.info("Further hiring-outlook, ICT and services-sector dashboards are awaiting source review in Advisory Operations.")


def interpretation_pairs(points:list[dict]) -> list[dict]:
    idx=_point_map(points)
    proposals=[
        ("adoption_capability","Widespread AI use does not prove operating readiness",
         ["scb_2026_ai_250plus","scb_2026_ai_expertise_barrier"],
         "One measure concerns large AI-adopting enterprises; the other a separate non-adopting subgroup. "
         "They frame a capability question but cannot be subtracted or statistically correlated.",
         "Ask what percentage of production workflows has named owners, measurable outcomes and stewarded data."),
        ("consulting_supply","Consulting assignment growth versus consultant availability",
         ["brainville_202610_assignments_yoy","brainville_202610_consultants_yoy"],
         "These are year-on-year marketplace growth rates for different populations across all disciplines. "
         "Their gap does not measure AI consulting scarcity or placement probability.",
         "Compare internal build, targeted hiring and consulting proposals against the same outcome."),
        ("ai_outside_it","AI terminology spreads beyond tech; leadership adverts remain selective",
         ["market_context_20261116_01","jobtech_v1_oct_se"],
         "TechSverige counts AI-related keyword occurrences across occupations over several years; "
         "JobTech v1 counts a narrow set of leadership adverts in one month. They are not like-for-like.",
         "Check where process and business-domain expertise is required before defining an AI leadership role."),
        ("ict_divergence","ICT output and employment can diverge",
         ["market_context_20261116_15","market_context_20261116_14"],
         "Almega reports output and workforce change using different underlying measures in the same industry. "
         "The gap alone cannot establish that AI caused job displacement.",
         "Assess new output per changed workflow alongside actual capability and hiring needs."),
        ("intentions_ads","IT hiring intentions versus actual AI leadership adverts",
         ["market_context_20261116_03","jobtech_v1_oct_se"],
         "The Manpower IT/Tech employer survey forecasts overall Q4 staffing plans; the October "
         "JobTech sample counts selected published AI/Data leadership adverts. Different universes and dates.",
         "Use the outlook to frame risk; use role-level job postings and a tested mandate to staff AI leadership."),
    ]
    out=[]
    for key,title,codes,caveat,action in proposals:
        existing=[idx[c] for c in codes if c in idx]
        if len(existing)!=len(codes):continue
        out.append({"key":key,"title":title,"evidence":existing,"caveat":caveat,"action":action})
    return out


def _interpretations(points:list[dict]) -> None:
    _intro(
        "Interpreting related measures and their limits",
        "These comparisons bring related published figures into a business discussion. "
        "Some come from the same publisher; none proves why a change occurred or "
        "predicts a result for your organisation.",
    )
    all_pairs=interpretation_pairs(points)
    if not all_pairs:
        st.info("No supported comparisons are available in this edition.")
        return
    for item in all_pairs:
        with st.container(border=True):
            st.markdown("**"+item["title"]+"**")
            a,b=st.columns(2)
            for c,p in zip((a,b),item["evidence"][:2]):
                c.metric(p["metric_label"],_value(p))
                c.caption(f'{p["source_family"]} · {_when(p)}')
            st.write(item["caveat"])
            st.markdown("**Management question / next action:** "+item["action"])
            with st.expander("Evidence origin, populations and limitations"):
                for p in item["evidence"]:
                    st.markdown(f'[{p["source_title"]}]({p["source_url"]}) · {_when(p)}')
                    st.caption(p["population_note"]+" · "+p["caveat"])
    st.caption(
        "These are questions drawn from published observations. The figures may "
        "cover different groups and periods, so they are not statistical tests "
        "or forecasts for an individual organisation."
    )


def comparable_series(points:list[dict], series:str, geography:str) -> tuple[list[dict],list[dict]]:
    selected=[p for p in points if p.get("series_code")==series and p.get("geography")==geography]
    if not selected:return [],[]
    units={p["metric_unit"] for p in selected}
    families={p["source_family"] for p in selected}
    if len(units)!=1 or len(families)!=1:
        raise ValueError("Incompatible measurement units or publishers in one historical series.")
    complete={}
    partial={}
    for p in sorted(selected,key=lambda x:(str(x["verified_on"]),str(x["code"]))):
        key=(p["period_start"],p["period_end"])
        (complete if p["period_complete"] else partial)[key]=p
    return sorted(complete.values(),key=lambda p:p["period_start"]),sorted(partial.values(),key=lambda p:p["period_start"])


def _trend_explorer(points:list[dict]) -> None:
    _intro("Comparable measures across complete reporting periods",
           "Choose one published indicator and geography. A line appears only with two "
           "or more comparable, complete reporting periods. One observation is a snapshot, "
           "not a manufactured historical trend.")
    choices=sorted({(p["series_code"],p["geography"]) for p in points
                    if p.get("series_code") and p.get("period_end")})
    if not choices:
        st.info("No approved indicators for trend exploration.")
        return
    labels={}
    for s,g in choices:
        sample=next(p for p in points if p["series_code"]==s and p["geography"]==g)
        labels[(s,g)]=f'{sample["metric_label"]} · {g} · {sample["metric_unit"]}'
    preferred=next((i for i,c in enumerate(choices)
                    if c==("jobtech_ai_data_leadership_v1","Sweden")),0)
    selected=st.selectbox("Indicator / population",choices,index=preferred,
        format_func=lambda k:labels[k],key="market_observatory_trend_selected")
    try:
        complete,partial=comparable_series(points,*selected)
    except ValueError as exc:
        st.error(str(exc))
        return
    if len(complete)>=2:
        chart=alt.Chart(pd.DataFrame([
            {"Period":pd.to_datetime(p["period_end"]), "Value":float(p["value"]),
             "Release":p["period_label"],"Source":p["source_title"]}
            for p in complete])).mark_line(point=True,color=COLORS["ink"],strokeWidth=3).encode(
            x=alt.X("Period:T",title="Complete observation period"),
            y=alt.Y("Value:Q",title=complete[0]["metric_unit"],scale=alt.Scale(zero=False)),
            tooltip=["Release:N","Source:N",alt.Tooltip("Value:Q",format=",.2f")],
        ).properties(height=280)
        st.altair_chart(chart,use_container_width=True)
        prior,current=complete[-2:]
        st.metric("Latest independently comparable change",
                  _value(current),
                  delta=f'{float(current["value"])-float(prior["value"]):+.1f} {current["metric_unit"]}',
                  delta_color="off")
        st.caption(f"{len(complete)} complete periods. Differences are in original source units. "
                   "A change is not an estimate of future growth.")
    elif len(complete)==1:
        st.metric("Single observed value",_value(complete[0]))
        st.info("One complete observation does not establish a time trend.")
    else:
        st.info("No complete periods are available for this indicator.")
    if partial:
        st.caption("Incomplete, excluded from trend: "+", ".join(
            f"{p['period_label']} ({_value(p)})" for p in partial))
    relevant=complete+partial
    with st.expander("Observation record and publisher references",expanded=True):
        st.dataframe([{"Observation":p["period_label"],"Value":_value(p),
            "Complete period":p["period_complete"],"Verified":p["verified_on"],
            "Publisher URL":p["source_url"]}
            for p in relevant],hide_index=True,use_container_width=True,
            column_config={"Publisher URL":st.column_config.LinkColumn("Original source")})
        for p in relevant[-2:]:
            st.caption(f'{p["code"]}: {p["methodology"]} Limitation: {p["caveat"]}')


def _evidence_csv(points:list[dict]) -> bytes:
    buf=StringIO()
    w=csv.writer(buf)
    keys=("code","series_code","lens","geography","period_label","period_start","period_end",
          "period_complete","metric_label","value","metric_unit","population_note",
          "source_family","source_title","source_url","published_on","verified_on",
          "evidence_grade","methodology","caveat")
    w.writerow(keys)
    for p in points:
        items=[]
        for key in keys:
            val=p.get(key,"")
            if isinstance(val,str) and val.lstrip().startswith(("=","+","-","@")):
                val="'"+val
            items.append(val)
        w.writerow(items)
    return buf.getvalue().encode("utf-8-sig")


def _ledger(points:list[dict]) -> None:
    _intro(
        "Published observations and original source records",
        "Every published number retains a publisher, observation period, release date, "
        "verification date, population, source methodology and limitations. "
        "A completed ingestion check is not proof that a new release exists.",
    )
    lenses=sorted({p["lens"] for p in points})
    a,b,c=st.columns(3)
    with a:
        lens=st.selectbox("Evidence lens",["All"]+lenses,key="market_observatory_ledger_lens")
    regions=sorted({p["geography"] for p in points if lens=="All" or p["lens"]==lens})
    with b:
        geo=st.selectbox("Geography",["All"]+regions,key="market_observatory_ledger_region")
    families=sorted({p["source_family"] for p in points
                     if (lens=="All" or p["lens"]==lens)
                     and (geo=="All" or p["geography"]==geo)})
    with c:
        family=st.selectbox("Publisher family",["All"]+families,
                            key="market_observatory_ledger_family")
    chosen=[p for p in points if (lens=="All" or p["lens"]==lens)
            and (geo=="All" or p["geography"]==geo)
            and (family=="All" or p["source_family"]==family)]
    st.caption(f"{len(chosen)} published observations · {len({p['source_family'] for p in chosen})} publishers · "
               "not a count of independent data series.")
    st.dataframe([{
        "Indicator":p["metric_label"],"Value":_value(p),
        "Area":p["geography"],"Observation":p["period_label"],
        "Reported":p["published_on"],"Verified":p["verified_on"],
        "Review status":_freshness(p),"Evidence":p["evidence_grade"],
        "Publisher":p["source_family"],"Source URL":p["source_url"]
    } for p in chosen],hide_index=True,use_container_width=True,height=360,
    column_config={"Source URL":st.column_config.LinkColumn("Original source")})
    st.download_button(
        "Download filtered source ledger · CSV",
        _evidence_csv(chosen),"Jair_Ribeiro_Market_Signals_Source_Ledger.csv",
        mime="text/csv",key="market_observatory_source_csv",
        use_container_width=True,
    )
    if chosen:
        names={p["code"]:p for p in chosen}
        key=st.selectbox("Inspect source methodology",list(names),
            format_func=lambda k:names[k]["metric_label"]+" · "+names[k]["period_label"],
            key="market_observatory_source_detail")
        p=names[key]
        st.markdown("**"+p["metric_label"]+"**")
        st.write("**Measured population:**",p["population_note"])
        st.write("**Publisher method:**",p["methodology"])
        st.write("**Caution and inference boundary:**",p["caveat"])
        st.caption(
            f'{p["source_family"]} · Observation {p["period_start"]}–{p["period_end"]} · '
            f'Published {p["published_on"]} · Verified {p["verified_on"]} · {_freshness(p)}'
        )
        st.link_button("Open original publisher",p["source_url"])
    st.caption("Historic revisions retain their publication provenance; additional source families enter only after owner editorial approval.")



def _unionen_workforce(points:list[dict]) -> None:
    """One source, two distinct survey denominators; never an AI hiring chart."""
    from market_unionen_workforce_update import (
        CLUBS, AI_ADOPTERS, REQUIRED, BOUNDARY, SCOPE, SOURCE_REPORT,
    )
    idx=_point_map(points)
    if not set(REQUIRED).issubset(idx):
        st.warning("The selected Unionen indicators are not present in this historic edition.")
        return
    _intro(
        "A stronger business outlook is not yet stronger professional recruitment",
        "Unionen's 18 November report adds workplace-level evidence that complements "
        "the existing SCB, KI and JobTech measurements. Its figures describe "
        "responding union clubs and sector expectations, not open AI/Data positions."
    )
    _cards([
        ("Business outlook index",idx["unionen_business_outlook_index"],
         "Unionen Branschbarometern, autumn 2026 · 50 is neutral"),
        ("AI introduced at employer",idx["unionen_ai_adoption_clubs_share"],
         "Responding workplace union clubs, not SCB enterprises"),
        ("AI changed staffing",idx["unionen_ai_staffing_need_changed_share"],
         "270 clubs at AI-adopting employers, multiple answers possible"),
    ])
    _bars(_codes(points,list(CLUBS)),{k:v[1] for k,v in CLUBS.items()},
        title="AI introduction and workplace discussions",
        unit="percent of responding Unionen clubs",
        denominator="All responding Unionen clubs · distinct measures · do not compare with SCB",color=COLORS["blue"])
    _bars(_codes(points,list(AI_ADOPTERS)),{k:v[1] for k,v in AI_ADOPTERS.items()},
        title="Changes at employers already using AI",
        unit="percent of responding clubs at AI adopters",
        denominator="270-club subgroup · multiple responses permitted · cannot be added together",color=COLORS["copper"])
    _heading("Sector expectations: relevant context, not vacancy volumes")
    st.write(
        "Unionen's automotive outlook index was 45, below the neutral 50. "
        "The consulting and staffing sector reported relatively more positive "
        "professional employment expectations. These are different sector samples "
        "and do not establish the number of AI or Data positions available."
    )
    with st.expander("Causal interpretation, adjusted association and survey method",expanded=False):
        st.write(SCOPE)
        st.write(
            "An adjusted association in the survey compared 30% of AI adopters "
            "with 14% of non-adopters expecting white-collar reductions. "
            "It is not causal evidence and is less conclusive when weighted by "
            "employee headcount. The survey cannot measure individual career risk."
        )
        st.write(BOUNDARY)
        st.link_button("Read Unionen's original report",SOURCE_REPORT)

def render_market_observatory(points:list[dict], *, historical:bool=False) -> None:
    """Full edition or explicitly limited retrospective monthly source snapshot."""
    st.html(CSS)
    st.markdown("### AI & Data Market Observatory")
    if historical:
        st.caption(
            "Retrospective historical title-basket snapshot · Only evidence confirmed for "
            "the selected publication month · No later survey or consulting figures"
        )
        allowed={"demand":DASHBOARDS["demand"],
                 "trends":DASHBOARDS["trends"],"ledger":DASHBOARDS["ledger"]}
        key="market_observatory_historical_section"
    else:
        st.caption(
            "Sweden-focused · Source-led · Professional and enterprise AI/Data signals · "
            "No personal pipeline or individual employment forecasts"
        )
        # New dated editions may add a source-specific dashboard; previous
        # archives retain their original eight dashboards unchanged.
        if any(p.get("source_family")=="unionen_branschbarometern" for p in points):
            allowed={"unionen":"AI at work · Unionen autumn 2026",**DASHBOARDS}
        else:
            allowed=DASHBOARDS
        key="market_observatory_section"
    section=st.selectbox("Explore dashboard",list(allowed),
        format_func=lambda k:allowed[k],
        key=key,help=("Historical source views cannot fabricate later market measures."
            if historical else "Source-specific and decision-oriented evidence dashboards."))
    st.divider()
    if section=="unionen":_unionen_workforce(points)
    elif section=="pulse":_executive_pulse(points)
    elif section=="demand":_demand(points)
    elif section=="adoption":_adoption(points)
    elif section=="talent":_talent(points)
    elif section=="commercial":_commercial(points)
    elif section=="signals":_interpretations(points)
    elif section=="trends":_trend_explorer(points)
    elif section=="ledger":_ledger(points)
