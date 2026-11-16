"""Owner-only editorial control centre for AI & Data Market Signals.

All writes are authenticated through owner-only, audit-logged database RPCs.
The interface never writes the evidence or analysis tables directly.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from html import escape
from urllib.parse import quote

import streamlit as st

from site_cms import _request_json, _rest_url
from advisory_service_visibility import service_visibility

SECTIONS = {
    "overview": "Executive overview",
    "coverage": "Analytics coverage & intake",
    "sources": "Source assurance",
    "evidence": "Evidence catalogue",
    "analysis": "Executive interpretations",
    "editions": "Editorial editions",
    "engagement": "Audience & downloads",
    "audit": "Editorial audit",
}
MUTATION_TABLES = {
    "source": ("portfolio_market_signal_source_controls", "source_family"),
    "point": ("portfolio_market_signal_points", "code"),
    "brief": ("portfolio_market_signal_briefs", "slug"),
    "edition": ("portfolio_market_signal_editions", "slug"),
}
LENSES = ("leadership", "adoption", "capability", "consulting", "context")
GRADES = ("primary", "derived", "contextual")
SUPPORT = ("independent_sources", "single_source", "context_only")
MARKET_ADMIN_CSS = """
<style>
.ms-admin-hero{background:linear-gradient(118deg,#10283F,#24465B);color:#fff;
 padding:clamp(22px,3.7vw,37px);margin:7px 0 18px}
.ms-admin-hero span{font-weight:800;letter-spacing:.13em;font-size:10px;color:#F0B991}
.ms-admin-hero h2{font:500 clamp(27px,3.8vw,39px)/1.13 Georgia,serif;
 color:white;margin:11px 0}
.ms-admin-hero p{color:#DFE7ED;font-size:13px;line-height:1.65;max-width:850px}
.ms-admin-context{border-left:3px solid #B47A55;background:#F8F5EF;
 color:#243D50;padding:12px 16px;line-height:1.65;font-size:13px;margin:14px 0}
.ms-admin-kicker{text-transform:uppercase;letter-spacing:.11em;font-size:11px;
 font-weight:800;color:#956744;margin:15px 0 5px}
@media(max-width:720px){.ms-admin-hero{padding:21px 17px}}
</style>
"""


def _get(token: str, query: str, *, limit: int = 300) -> list[dict]:
    # Every query is an owner-only RLS-protected editorial table.
    raw = _request_json("GET", _rest_url(query), token=token, timeout=15)
    if not isinstance(raw, list):
        raise RuntimeError("Market management returned an invalid owner catalogue.")
    if len(raw) > limit:
        raise RuntimeError("The returned market catalogue exceeds the configured limit.")
    return raw


def _load(token: str) -> dict:
    return {
        "sources": _get(token, "portfolio_market_signal_source_controls?select=*&order=display_name.asc&limit=50", limit=50),
        "points": _get(token, "portfolio_market_signal_points?select=*&order=period_end.desc,code.asc&limit=500", limit=500),
        "briefs": _get(token, "portfolio_market_signal_briefs?select=*&order=published_on.desc,slug.asc&limit=100", limit=100),
        "editions": _get(token, "portfolio_market_signal_editions?select=*&order=issue_date.desc&limit=100", limit=100),
    }


def _pipeline(token: str) -> list[dict]:
    raw = _request_json("POST", _rest_url("rpc/portfolio_market_signals_owner_pipeline_v1"),
                        token=token, payload={}, timeout=15)
    if not isinstance(raw, list):
        raise RuntimeError("Publisher pipeline status cannot be verified.")
    return raw


def _preflight(token: str, slug: str | None = None) -> dict:
    raw = _request_json("POST", _rest_url("rpc/portfolio_market_signals_release_check_v1"),
                        token=token, payload={"p_slug": slug}, timeout=15)
    if not isinstance(raw, dict) or type(raw.get("ready")) is not bool:
        raise RuntimeError("Release validation returned an invalid response.")
    return raw


def _act(token: str, action: str, payload: dict, rationale: str) -> dict:
    if len(rationale.strip()) < 12:
        raise ValueError("Explain the source verification or editorial reason (at least 12 characters).")
    response = _request_json(
        "POST", _rest_url("rpc/portfolio_market_signals_owner_action_v1"),
        token=token,
        payload={"p_action": action, "p_payload": payload, "p_rationale": rationale.strip()},
        timeout=20,
    )
    if not isinstance(response, dict) or response.get("action") != action or response.get("changed") is not True:
        raise RuntimeError("The requested editorial change was not confirmed.")
    table,key = MUTATION_TABLES[str(response["entity_type"])]
    ident = str(response["key"])
    query = f"{table}?select=*&{key}=eq.{quote(ident,safe='')}&limit=1"
    readback = _get(token,query,limit=1)
    if len(readback) != 1 or str(readback[0].get(key)) != ident:
        raise RuntimeError("The editorial change could not be verified after saving.")
    if action.endswith("_publish") and str(response["entity_type"]) in ("point","brief") and readback[0]["is_published"] is not True:
        raise RuntimeError("Published state not reflected in a fresh read.")
    if action.endswith("_withdraw"):
        if str(response["entity_type"])=="edition" and readback[0]["status"]!="withdrawn":
            raise RuntimeError("Edition withdrawal not confirmed.")
        if str(response["entity_type"]) in ("point","brief") and readback[0]["is_published"] is not False:
            raise RuntimeError("Editorial withdrawal not confirmed.")
    return response


def _revise_edition(token: str, payload: dict, reason: str) -> None:
    if len(reason.strip()) < 12:
        raise ValueError("Provide a specific editorial change reason.")
    response = _request_json(
        "POST",_rest_url("rpc/portfolio_market_signals_revise_edition_v1"),
        token=token,timeout=20,
        payload={
            "p_slug":payload["slug"],"p_title":payload["title"],
            "p_issue_date":payload["issue_date"],
            "p_evidence_codes":payload["evidence_codes"],
            "p_brief_slugs":payload["brief_slugs"],
            "p_editorial_note":payload["editorial_note"],
            "p_reason":reason,
        },
    )
    if not isinstance(response,dict) or response.get("changed") is not True:
        raise RuntimeError("The edition revision could not be confirmed.")
    rows=_get(token,
        "portfolio_market_signal_editions?select=slug,title,status&slug=eq."+
        quote(payload["slug"],safe="")+"&limit=1",limit=1)
    if len(rows)!=1 or rows[0]["title"]!=payload["title"] or rows[0]["status"]!="draft":
        raise RuntimeError("Edition revision read-back failed.")


def _perform(token: str, action: str, payload: dict, reason: str) -> bool:
    try:
        result=_act(token,action,payload,reason)
    except (RuntimeError,ValueError,KeyError,TimeoutError,OSError) as exc:
        st.error("No confirmed change: "+str(exc)[:280])
        return False
    st.session_state["market_signals_admin_flash"] = (
        f"{action.replace('_',' ').title()} confirmed and read back from Supabase."
    )
    st.rerun()
    return True


def _date(value: object, fallback: date | None = None) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError,TypeError):
        return fallback or date.today()


def _review_pdf_compatible(evidence_codes: list[str]) -> bool:
    """Mirror the database full-PDF template guard for immediate owner feedback.

    The trigger in Supabase is authoritative if templates or releases differ.
    """
    selected=set(evidence_codes)
    required={
        "scb_2026_ai_10plus","scb_2026_ai_250plus",
        "scb_2026_analytics_internal","scb_2026_ai_expertise_barrier",
        "jobtech_v1_sep_se","jobtech_v1_oct_se",
        "jobtech_v1_sep_vgr","jobtech_v1_oct_vgr",
        "brainville_202610_assignments_yoy",
        "brainville_202610_consultants_yoy",
    }
    complete={
        "jobtech_v1_jun_se","jobtech_v1_jul_se","jobtech_v1_aug_se",
        "jobtech_v1_sep_se","jobtech_v1_oct_se",
    }
    return required.issubset(selected) and len(complete.intersection(selected))>=3


def _status(day: object, cadence: int) -> str:
    if not day:
        return "Unverified"
    since=(date.today()-_date(day)).days
    if since < 0:
        return "Future-dated — investigate"
    return "Overdue" if since>cadence else "Within interval"


def _core_status(data: dict, pipeline: list[dict]) -> dict:
    points=data["points"]; briefs=data["briefs"]; editions=data["editions"]
    families={p["source_family"] for p in points if p["is_published"]}
    controls={s["source_family"]:s for s in data["sources"]}
    ready_sources=sum(s["review_status"]=="approved" for s in data["sources"])
    stale=sum(_status(p.get("verified_on"),int(controls.get(p["source_family"],{}).get("recheck_days",90)))!="Within interval"
        for p in points if p["is_published"])
    unsupported=0
    by_code={p["code"]:p for p in points}
    for brief in briefs:
        if not brief["is_published"]:continue
        codes=brief.get("evidence_codes") or []
        cited=[by_code[c] for c in codes if c in by_code]
        if len(cited)!=len(codes) or len(cited)<2 or any(not p["is_published"] for p in cited):
            unsupported+=1
        elif brief["support_level"]=="independent_sources" and len({p["source_family"] for p in cited})<2:
            unsupported+=1
    return {
        "published_points":sum(bool(p["is_published"]) for p in points),
        "draft_points":sum(not p["is_published"] for p in points),
        "published_briefs":sum(bool(b["is_published"]) for b in briefs),
        "draft_briefs":sum(not b["is_published"] for b in briefs),
        "approved_sources":ready_sources,
        "total_sources":len(data["sources"]),
        "overdue_points":stale,"unsupported_briefs":unsupported,
        "published_editions":sum(e["status"]=="published" for e in editions),
        "families":len(families),
    }


def _hero() -> None:
    st.html(MARKET_ADMIN_CSS+
        '<div class="ms-admin-hero"><span>EDITORIAL CONTROL CENTRE / ADVISORY OPERATIONS</span>'
        '<h2>AI &amp; Data Market Signals</h2>'
        '<p>Control the evidence, not just the visibility switch. Track source reliability, '
        'stage verified observations, review executive interpretation, release editions, '
        'measure readership and preserve the audit trail.</p></div>'
    )


def _overview(token: str, data: dict, pipeline: list[dict], indicators: dict) -> None:
    st.subheader("Publication command centre")
    try:
        visible=service_visibility().get("market-signals")
    except (RuntimeError,KeyError,ValueError,TimeoutError,OSError):
        visible=None
    if visible is False:
        st.warning("Service is hidden from regular visitors. Administrators can still preview.")
    elif visible is True:
        st.info("Service is enabled for regular members. Check release assurance before making new claims.")
    else:
        st.error("Public visibility cannot be confirmed.")
    a,b,c,d=st.columns(4)
    a.metric("Published evidence",indicators["published_points"])
    b.metric("Executive analyses",indicators["published_briefs"])
    c.metric("Sources approved",f'{indicators["approved_sources"]}/{indicators["total_sources"]}')
    d.metric("Published editions",indicators["published_editions"])
    if indicators["overdue_points"]:
        st.warning(f'{indicators["overdue_points"]} published observations exceed their source review interval.')
    if indicators["unsupported_briefs"]:
        st.error(f'{indicators["unsupported_briefs"]} published analyses have unsupported or missing cited evidence.')
    if indicators["approved_sources"]<indicators["total_sources"]:
        st.warning("Editorial source approval is incomplete. A new edition cannot pass the release gate.")
    if indicators["published_editions"]==0:
        st.info("No formally released edition has been recorded yet. Existing charts may be present, but the initial edition still needs a documented quality sign-off.")
    try:
        gate=_preflight(token)
    except (RuntimeError,ValueError,TimeoutError,KeyError):
        st.error("The editorial release gate could not be read.")
    else:
        st.markdown("#### Current publication quality gate")
        st.json(gate,expanded=False)
        if gate.get("ready"):
            st.success("The current evidence/analysis collection passes the structural release gate.")
        else:
            st.warning("Current evidence fails at least one release condition. Review source approvals and cited evidence.")
    st.markdown("#### Source pipeline: ingestion versus publication")
    if pipeline:
        st.dataframe([{
            "Source":r["display_name"],"Editorial review":r["review_status"],
            "Last upstream check":str(r.get("last_checked_at") or "—")[:16],
            "Last upstream success":str(r.get("last_success_at") or "—")[:16],
            "Latest collected period":str(r.get("latest_ingested_observation") or "—"),
            "Latest curated verification":str(r.get("latest_published_verification") or "—"),
            "Publication coverage":int(r.get("published_points") or 0),
        } for r in pipeline],hide_index=True,use_container_width=True)
    st.html('<div class="ms-admin-context"><strong>Release principle:</strong> '
        'An upstream refresh is not a publication approval. Publisher authenticity, methodology, '
        'population, revision history, licensing and independent interpretation must be reviewed '
        'before a new edition is released.</div>')


def _analytics_coverage(token: str, data: dict) -> None:
    st.subheader("Internal analytics → public intelligence coverage")
    st.caption(
        "The Swedish Job Market workspace contains personal outcomes and broad economic indicators. "
        "Only curated source evidence can enter this service. Drafts are not readable by members "
        "until verified and approved in the dedicated editorial workflow."
    )
    points=data["points"]
    rows=[]
    lens_names={
        "leadership":"AI/Data leadership demand",
        "adoption":"AI skills and enterprise adoption",
        "capability":"Analytics capabilities and compensation proxies",
        "consulting":"Consulting market context",
        "context":"IT/Tech and service-sector conditions",
    }
    for lens,label in lens_names.items():
        selected=[p for p in points if p["lens"]==lens]
        reviewed=[p for p in selected if p["is_published"]]
        pending=[p for p in selected if not p["is_published"]]
        rows.append({
            "Service dashboard":label,"Published":len(reviewed),"Awaiting review":len(pending),
            "Publisher families":len({p["source_family"] for p in selected}),
            "Latest observed":max((str(p["period_end"]) for p in selected),default="—"),
        })
    st.dataframe(rows,hide_index=True,use_container_width=True)
    st.markdown("#### Publication pipeline by provider")
    grouped=defaultdict(lambda:{"approved":0,"draft":0,"items":[]})
    for p in points:
        row=grouped[p["source_family"]]
        row["approved" if p["is_published"] else "draft"]+=1
        if not p["is_published"]:row["items"].append(p)
    controls={s["source_family"]:s for s in data["sources"]}
    st.dataframe([{
        "Publisher":family,
        "Editorial approval":controls.get(family,{}).get("review_status","Not registered"),
        "Published observations":vals["approved"],
        "Unpublished evidence drafts":vals["draft"],
        "Next step":("Original source recheck + release review"
                     if controls.get(family,{}).get("review_status")!="approved" else
                     "Evidence-level source review and publication"),
    } for family,vals in sorted(grouped.items())],
    hide_index=True,use_container_width=True)
    with st.expander("View all pending AI/Data/context observations",expanded=True):
        candidates=sorted((p for p in points if not p["is_published"]),
                          key=lambda x:(x["source_family"],x["metric_label"]))
        st.dataframe([{
            "Indicator":p["metric_label"],"Family":p["source_family"],
            "Lens":p["lens"],"Period":p["period_label"],"Source":p["source_url"],
            "Review status":"Unpublished draft",
        } for p in candidates],hide_index=True,use_container_width=True,
            column_config={"Source":st.column_config.LinkColumn("Original publisher")})
        st.caption(
            "Each draft must be rechecked against its original issuer before entering the "
            "public dashboards. No annual figure may become a monthly chart and no overall "
            "IT/Tech hiring intention may be relabelled as a specialist AI hiring count."
        )
    st.markdown("#### Explicitly excluded from public Market Signals")
    st.write(
        "Individual employer applications, interview pipeline, recruiter interactions, "
        "personal market-to-search correlations, portfolio-to-interview correlations, "
        "individual offer dates and probabilities, and generic national unemployment dashboards."
    )
    st.caption(
        "The curated numbers are a reviewed subset of internal observations, not every one "
        "of the internal 28 source families or the entire Swedish labour market."
    )


def _sources(token: str, data: dict, pipeline: list[dict]) -> None:
    st.subheader("Source assurance and provenance")
    st.caption("Mark approved only after reviewing the original publisher. This records editorial verification; it does not trigger an upstream refresh or automatically rewrite a data observation.")
    if not pipeline:
        st.error("Source pipeline could not be checked.")
        return
    by_family={s["source_family"]:s for s in data["sources"]}
    for row in pipeline:
        key=row["source_family"]
        control=by_family[key]
        newest=row.get("latest_published_verification")
        freshness=_status(newest,int(row["recheck_days"]))
        with st.expander(f'{row["display_name"]} · {row["review_status"].replace("_"," ").title()} · {freshness}',
                         expanded=row["review_status"]!="approved"):
            a,b,c=st.columns(3)
            a.metric("Published observations",row.get("published_points") or 0)
            b.metric("Verification interval",str(row["recheck_days"])+" days")
            c.metric("Last verified on",str(newest or "—")[:10])
            st.caption(
                f'Latest upstream check: {str(row.get("last_checked_at") or "unknown")[:16]} · '
                f'Upstream success: {str(row.get("last_success_at") or "unknown")[:16]} · '
                f'Last observed period: {row.get("latest_ingested_observation") or "unknown"}'
            )
            example=next((p for p in data["points"] if p["source_family"]==key),None)
            if example:
                st.link_button("Open original publisher",example["source_url"])
                st.write("Publication method:",example.get("methodology") or "")
                st.write("Evidence caution:",example.get("caveat") or "")
            st.caption("Last reviewer note: "+str(row.get("reviewer_note") or "—"))
            with st.form("market_source_review_"+key):
                review=st.selectbox("Editorial status",["needs_review","approved","blocked"],
                    index=["needs_review","approved","blocked"].index(control["review_status"]),
                    key="market_source_status_"+key)
                reason=st.text_area(
                    "Source verification record (publisher, observations, sample and licensing)",
                    value=str(control.get("reviewer_note") or ""),max_chars=1200,
                    key="market_source_reason_"+key,height=100,
                )
                confirm=st.checkbox("I have checked the original publisher and its measurement scope",
                                    key="market_source_confirm_"+key)
                sent=st.form_submit_button("Save source review",type="primary",disabled=not confirm)
            if sent:
                _perform(token,"source_review",{"source_family":key,"review_status":review},reason)

    with st.expander("Register another AI/Data source family"):
        st.caption("Adding a source to the editorial register does not add an ingestion pipeline or expose its data.")
        with st.form("market_add_source"):
            key=st.text_input("New source family identifier",placeholder="source_provider_metric",max_chars=100)
            name=st.text_input("Publisher / dataset title",max_chars=160)
            cadence=st.number_input("Expected verification interval (days)",min_value=1,max_value=800,value=30)
            note=st.text_area("Reason for onboarding and expected evidence",max_chars=1200)
            submitted=st.form_submit_button("Register as needs review")
        if submitted:
            _perform(token,"source_register",{"source_family":key.strip(),
                "display_name":name.strip(),"recheck_days":int(cadence)},note)


def _point_fields(prefix: str, base: dict, families: list[str], *, can_edit_code: bool) -> dict:
    code=st.text_input("Immutable evidence code",value=str(base.get("code") or ""),
            disabled=not can_edit_code,key=prefix+"_code",max_chars=90,
            placeholder="scb_2027_ai_enterprise_10plus")
    series=st.text_input("Comparable series key",value=str(base.get("series_code") or ""),
            key=prefix+"_series",max_chars=120)
    a,b,c=st.columns(3)
    with a:
        lens=st.selectbox("Analytical lens",LENSES,
            index=LENSES.index(base["lens"]) if base.get("lens") in LENSES else 0,key=prefix+"_lens")
    with b:
        family=st.selectbox("Publisher family",families,
            index=families.index(base["source_family"]) if base.get("source_family") in families else 0,
            key=prefix+"_family")
    with c:
        grade=st.selectbox("Evidence type",GRADES,
            index=GRADES.index(base["evidence_grade"]) if base.get("evidence_grade") in GRADES else 0,
            key=prefix+"_grade")
    a,b=st.columns(2)
    with a:
        geography=st.text_input("Geography",value=str(base.get("geography") or "Sweden"),
            key=prefix+"_geo",max_chars=100)
        start=st.date_input("Observation start",value=_date(base.get("period_start")),
            key=prefix+"_start")
        end=st.date_input("Observation end",value=_date(base.get("period_end")),
            key=prefix+"_end")
    with b:
        label=st.text_input("Reporting period",value=str(base.get("period_label") or ""),
            key=prefix+"_period",max_chars=130)
        published=st.date_input("Source publication date",value=_date(base.get("published_on")),
            key=prefix+"_published")
        verified=st.date_input("Personally verified on",value=_date(base.get("verified_on")),
            key=prefix+"_verified")
    complete=st.checkbox("Complete reporting period",value=bool(base.get("period_complete",True)),
            key=prefix+"_complete")
    metric=st.text_input("Metric label",value=str(base.get("metric_label") or ""),
            key=prefix+"_metric",max_chars=200)
    a,b=st.columns([1,2])
    with a:
        amount=st.number_input("Value",value=float(base.get("value") or 0),
            format="%.3f",key=prefix+"_value")
        unit=st.text_input("Unit",value=str(base.get("metric_unit") or "percent"),
            key=prefix+"_unit",max_chars=45)
    with b:
        population=st.text_area("Exact population / denominator",
            value=str(base.get("population_note") or ""),key=prefix+"_population",height=105)
    title=st.text_input("Original source title",value=str(base.get("source_title") or ""),
            key=prefix+"_source_title",max_chars=230)
    url=st.text_input("Primary HTTPS publication URL",value=str(base.get("source_url") or ""),
            key=prefix+"_url",max_chars=800)
    methodology=st.text_area("Reproducible method and verification approach",
        value=str(base.get("methodology") or ""),key=prefix+"_method",height=115)
    caveat=st.text_area("Known limitations and alternative readings",
        value=str(base.get("caveat") or ""),key=prefix+"_caveat",height=105)
    group=st.text_input("Comparison cohort / group",value=str(base.get("comparison_group") or ""),
        key=prefix+"_group",max_chars=120)
    return {
        "code":code.strip(),"series_code":series.strip(),"lens":lens,"source_family":family,
        "evidence_grade":grade,"geography":geography.strip(),"period_label":label.strip(),
        "period_start":start.isoformat(),"period_end":end.isoformat(),"period_complete":complete,
        "published_on":published.isoformat(),"verified_on":verified.isoformat(),
        "metric_label":metric.strip(),"value":amount,"metric_unit":unit.strip(),
        "population_note":population.strip(),"source_title":title.strip(),
        "source_url":url.strip(),"methodology":methodology.strip(),"caveat":caveat.strip(),
        "comparison_group":group.strip(),
    }


def _evidence(token: str,data: dict) -> None:
    st.subheader("Evidence catalogue and publication")
    st.caption("Published observations are read-only. Create a new code for revisions; only drafts may be amended. Withdrawing evidence cited by a published analysis is blocked.")
    points=data["points"]; families=[s["source_family"] for s in data["sources"]]
    search=st.text_input("Find evidence",key="market_evidence_search",
        placeholder="Source, indicator, geography, period or code").casefold()
    filtered=[p for p in points if search in " ".join(str(p.get(x) or "")
             for x in ("code","metric_label","source_family","period_label","geography","lens")).casefold()]
    st.caption(f"{len(filtered)} matching observations · {len(points)} total")
    st.dataframe([{
        "Code":p["code"],"Status":"Published" if p["is_published"] else "Draft",
        "Lens":p["lens"],"Region":p["geography"],"Measure":p["metric_label"],
        "Value":p["value"],"Period":p["period_label"],"Verified":p["verified_on"],
        "Publisher":p["source_family"],
    } for p in filtered],hide_index=True,use_container_width=True,height=300)
    if points:
        by_code={p["code"]:p for p in points}
        selected=st.selectbox("Review observation",list(by_code),
            format_func=lambda code:f'{code} · {by_code[code]["metric_label"][:65]}',
            key="market_evidence_selected")
        p=by_code[selected]
        st.markdown("#### Observation detail")
        st.caption(
            f'{p["geography"]} · {p["period_label"]} · '
            f'{p["value"]} {p["metric_unit"]} · '
            f'{"Published" if p["is_published"] else "Draft"}'
        )
        st.write("**Denominator:**",p["population_note"])
        st.write("**Method:**",p["methodology"])
        st.write("**Limitations:**",p["caveat"])
        st.link_button("Inspect original publication",p["source_url"])
        citations=[b["slug"] for b in data["briefs"] if b["is_published"] and selected in b["evidence_codes"]]
        if citations:
            st.info("Referenced by published analyses: "+", ".join(citations))
        with st.form("market_evidence_visibility"):
            reason=st.text_area("Publication or withdrawal reason",key="market_evidence_review_reason",
                placeholder="Publisher verified, original denominator checked, revised release reason…")
            confirmation=st.checkbox("I have verified its source, date, unit, denominator and limitations",
                key="market_evidence_visibility_confirm")
            a,b=st.columns(2)
            with a:
                publish=st.form_submit_button("Publish observation",disabled=p["is_published"] or not confirmation,type="primary")
            with b:
                withdraw=st.form_submit_button("Withdraw observation",disabled=not p["is_published"] or not confirmation)
        if publish:
            _perform(token,"point_publish",{"code":selected},reason)
        if withdraw:
            _perform(token,"point_withdraw",{"code":selected},reason)

    st.divider()
    st.markdown("#### Prepare evidence")
    action=st.radio("Editing approach",["Create new observation","Edit unpublished draft",
                                       "Create correction based on existing"],
                    key="market_evidence_edit_mode",horizontal=True)
    target={}
    can_edit=True
    rpc_action="point_create"
    if action=="Edit unpublished draft":
        drafts=[p for p in points if not p["is_published"]]
        if not drafts:
            st.info("There are no unpublished observations to edit.")
            return
        selected_draft=st.selectbox("Draft",drafts,format_func=lambda p:p["code"],key="market_evidence_draft",
                                  )
        target=selected_draft
        can_edit=False
        rpc_action="point_revise"
    elif action=="Create correction based on existing" and points:
        template=st.selectbox("Copy structure from",points,format_func=lambda p:p["code"],
                            key="market_evidence_template")
        target={**template,"code":""}
    with st.form("market_evidence_editor"):
        submitted_fields=_point_fields("market_evidence_form",target,families,can_edit_code=can_edit)
        reason=st.text_area("Editorial verification record / revision reason",
                            key="market_evidence_reason",max_chars=1200)
        submit=st.form_submit_button("Save as unpublished draft",type="primary")
    if submit:
        if _date(submitted_fields["period_end"]) < _date(submitted_fields["period_start"]):
            st.error("Observation period end must not precede start.")
        elif _date(submitted_fields["published_on"]) > _date(submitted_fields["verified_on"]):
            st.error("Source cannot be verified before its publication.")
        elif not submitted_fields["source_url"].startswith("https://"):
            st.error("Publisher link must use HTTPS.")
        else:
            _perform(token,rpc_action,submitted_fields,reason)


def _brief_fields(prefix: str,base: dict,points: list[dict],*,allow_slug: bool) -> dict:
    slug=st.text_input("Immutable analysis slug",value=str(base.get("slug") or ""),
        disabled=not allow_slug,key=prefix+"_slug",max_chars=100,
        placeholder="ai-capability-vs-adoption-2026")
    version=st.text_input("Editorial version",value=str(base.get("version") or "1.0"),
        key=prefix+"_ver",max_chars=24)
    title=st.text_input("Executive analysis title",value=str(base.get("title") or ""),
        key=prefix+"_title",max_chars=200)
    thesis=st.text_area("Clear thesis",value=str(base.get("thesis") or ""),
        key=prefix+"_thesis",height=90)
    interpretation=st.text_area("Original interpretation (what sources support)",
        value=str(base.get("interpretation") or ""),key=prefix+"_interpret",height=155)
    question=st.text_area("Executive decision question",
        value=str(base.get("decision_question") or ""),key=prefix+"_question",height=76)
    action=st.text_area("Actionable first decision step",
        value=str(base.get("recommended_action") or ""),key=prefix+"_action",height=120)
    counter=st.text_area("Counterevidence / plausible alternative explanation",
        value=str(base.get("counterevidence") or ""),key=prefix+"_counter",height=110)
    limitations=st.text_area("Explicit inference boundaries and limitations",
        value=str(base.get("limitations") or ""),key=prefix+"_limits",height=110)
    support=st.selectbox("Interpretation support",SUPPORT,
        index=SUPPORT.index(base["support_level"]) if base.get("support_level") in SUPPORT else 0,
        key=prefix+"_support")
    available={p["code"]:p for p in points if p["is_published"]}
    selected=[c for c in base.get("evidence_codes",[]) if c in available]
    codes=st.multiselect("Supporting published evidence codes",list(available),
        default=selected,key=prefix+"_evidence",
        format_func=lambda c:c+" · "+available[c]["metric_label"][:65])
    issue=st.date_input("Analysis publication date",value=_date(base.get("published_on")),
        key=prefix+"_issue")
    return {"slug":slug.strip(),"version":version.strip(),"title":title.strip(),
        "thesis":thesis.strip(),"interpretation":interpretation.strip(),
        "decision_question":question.strip(),"recommended_action":action.strip(),
        "counterevidence":counter.strip(),"limitations":limitations.strip(),
        "support_level":support,"evidence_codes":codes,"published_on":issue.isoformat()}


def _analysis(token: str,data: dict) -> None:
    st.subheader("Executive interpretation desk")
    st.caption("Every published interpretation must reference measurable evidence and present competing explanations. Distinct publishers corroborate context, not causation.")
    briefs=data["briefs"]; points=data["points"]
    by_code={p["code"]:p for p in points}
    st.dataframe([{"Analysis":b["title"],"Version":b["version"],
        "Status":"Published" if b["is_published"] else "Draft",
        "Sources":len({by_code[c]["source_family"] for c in b["evidence_codes"] if c in by_code}),
        "Evidence records":len(b["evidence_codes"]),
        "Level":b["support_level"],"Edition":str(b["published_on"])}
        for b in briefs],hide_index=True,use_container_width=True)
    if briefs:
        selected=st.selectbox("Inspect executive analysis",briefs,format_func=lambda b:b["title"],
            key="market_brief_selected")
        st.markdown("#### "+selected["title"])
        st.write("**Editorial position:**",selected["thesis"])
        st.write("**Evidence-based reading:**",selected["interpretation"])
        st.write("**Decision:**",selected["decision_question"])
        st.write("**First action:**",selected["recommended_action"])
        st.write("**Counterargument:**",selected["counterevidence"])
        st.write("**Limits:**",selected["limitations"])
        with st.expander("Cited publisher observations"):
            for code in selected["evidence_codes"]:
                p=by_code.get(code)
                if p:
                    st.markdown(f'[{escape(code)}]({p["source_url"]}) · {p["metric_label"]} · {p["value"]}')
                else:
                    st.error("Broken evidence link: "+code)
        with st.form("market_brief_review_actions"):
            reason=st.text_area("Why approve or withdraw this interpretation?",
                key="market_brief_review_reason")
            confirm=st.checkbox("Evidence lineage and counterarguments personally checked",
                key="market_brief_confirm")
            a,b=st.columns(2)
            with a:
                publish=st.form_submit_button("Publish analysis",disabled=selected["is_published"] or not confirm,type="primary")
            with b:
                withdraw=st.form_submit_button("Withdraw analysis",disabled=not selected["is_published"] or not confirm)
        if publish:
            _perform(token,"brief_publish",{"slug":selected["slug"]},reason)
        if withdraw:
            _perform(token,"brief_withdraw",{"slug":selected["slug"]},reason)
    st.divider()
    st.markdown("#### Author a new interpretation")
    mode=st.radio("Editor",["New version","Edit unpublished draft"],
                 horizontal=True,key="market_brief_editor_mode")
    base={}
    allow_slug=True
    action="brief_create"
    if mode=="Edit unpublished draft":
        drafts=[b for b in briefs if not b["is_published"]]
        if not drafts:
            st.info("No unpublished interpretation drafts.")
            return
        base=st.selectbox("Unpublished analysis",drafts,format_func=lambda b:b["title"],
            key="market_brief_draft")
        allow_slug=False
        action="brief_revise"
    with st.form("market_analysis_form"):
        fields=_brief_fields("market_analysis_form",base,points,allow_slug=allow_slug)
        note=st.text_area("Editorial reason and supporting verification steps",
            key="market_analysis_edit_reason",max_chars=1200)
        sent=st.form_submit_button("Save unpublished analysis draft",type="primary")
    if sent:
        supporting={by_code[c]["source_family"] for c in fields["evidence_codes"]
                    if c in by_code}
        if len(fields["evidence_codes"])<2:
            st.error("At least two published evidence records are required.")
        elif fields["support_level"]=="independent_sources" and len(supporting)<2:
            st.error("Independent sources requires evidence from two source families.")
        elif not fields["counterevidence"] or not fields["limitations"]:
            st.error("Explicit counterarguments and limitations are mandatory.")
        else:
            _perform(token,action,fields,note)


def _editions(token: str,data: dict) -> None:
    st.subheader("Editorial editions and release gate")
    st.caption("Publish an accountable, versioned market review after source approvals, evidence verification and interpretation checks. Replacing a published edition requires an explicit withdrawal.")
    editions=data["editions"];points=data["points"];briefs=data["briefs"]
    st.dataframe([{"Edition":e["title"],"Slug":e["slug"],"State":e["status"],
        "Issue date":e["issue_date"],"Evidence":len(e["evidence_codes"]),
        "Analyses":len(e["brief_slugs"]),
        "Released":str(e.get("published_at") or "")[:16]}
        for e in editions],hide_index=True,use_container_width=True)
    if editions:
        e=st.selectbox("Review edition",editions,format_func=lambda x:x["title"]+" · "+x["status"],
                key="market_editions_selected")
        try:
            gate=_preflight(token,e["slug"])
        except (RuntimeError,ValueError,TimeoutError):
            st.error("Could not verify release readiness.")
            gate=None
        if gate:
            if gate["ready"]:
                st.success("Edition passes the structural and source-verification release gate.")
            else:
                st.warning("Edition is not ready for publication.")
            st.json(gate,expanded=False)
        pdf_compatible=_review_pdf_compatible(e.get("evidence_codes") or [])
        if not pdf_compatible:
            st.error(
                "The full market-review PDF cannot be generated from this edition's selected "
                "evidence. Keep the original 2026 source metrics and at least three complete "
                "JobTech months, or update the PDF template before release."
            )
        else:
            st.caption("Current full-review PDF template: required source metrics and chart periods present.")
        st.write("**Editorial note:**",e.get("editorial_note") or "—")
        with st.form("market_edition_publication"):
            note=st.text_area("Publication decision / withdrawal rationale",
                key="market_edition_decision_reason",max_chars=1200)
            reviewed=st.checkbox("Publisher evidence, interpretation, links, PDF and mobile presentation verified",
                key="market_edition_reviewed")
            a,b=st.columns(2)
            with a:
                publish=st.form_submit_button("Publish edition",type="primary",
                    disabled=e["status"]!="draft" or not reviewed or not pdf_compatible or not bool(gate and gate["ready"]))
            with b:
                withdraw=st.form_submit_button("Withdraw edition",
                    disabled=e["status"]!="published" or not reviewed)
        if publish:
            _perform(token,"edition_publish",{"slug":e["slug"]},note)
        if withdraw:
            _perform(token,"edition_withdraw",{"slug":e["slug"]},note)

    st.divider()
    st.markdown("#### Prepare a new edition or revise a draft")
    mode=st.radio("Edition work",["Create edition","Revise draft"],
                   key="market_edition_mode",horizontal=True)
    existing={}
    draft_edit=False
    if mode=="Revise draft":
        drafts=[e for e in editions if e["status"]=="draft"]
        if not drafts:
            st.info("No draft editions available for revision.")
            return
        existing=st.selectbox("Choose draft edition",drafts,
            format_func=lambda x:x["title"],key="market_edition_draft")
        draft_edit=True
    published_points=[p for p in points if p["is_published"]]
    published_briefs=[b for b in briefs if b["is_published"]]
    with st.form("market_edition_editor"):
        slug=st.text_input("Edition identifier",value=str(existing.get("slug") or ""),
            placeholder="ai-data-review-2026-11",disabled=draft_edit,
            key="market_edition_slug")
        title=st.text_input("Issue title",value=str(existing.get("title") or "AI & Data Market Review — "),
            key="market_edition_title")
        issue=st.date_input("Edition date",value=_date(existing.get("issue_date")),
            key="market_edition_issue")
        selection=st.multiselect("Included, published evidence",published_points,
            default=[p for p in published_points if p["code"] in existing.get("evidence_codes",[])]
            if existing else published_points,
            format_func=lambda p:p["code"],key="market_edition_points")
        analyses=st.multiselect("Included executive analyses",published_briefs,
            default=[b for b in published_briefs if b["slug"] in existing.get("brief_slugs",[])]
            if existing else published_briefs,
            format_func=lambda b:b["title"],key="market_edition_briefs")
        editorial=st.text_area("Editorial scope, revision notes and decision for readers",
            value=str(existing.get("editorial_note") or ""),key="market_edition_note")
        reason=st.text_area("Why create/revise this release?",key="market_edition_reason")
        save=st.form_submit_button("Save draft edition",type="primary")
    if save:
        payload={"slug":slug.strip(),"title":title.strip(),
            "issue_date":issue.isoformat(),
            "evidence_codes":[p["code"] for p in selection],
            "brief_slugs":[b["slug"] for b in analyses],
            "editorial_note":editorial.strip()}
        if len(payload["evidence_codes"])<2 or len(payload["brief_slugs"])<1:
            st.error("Choose at least two published observations and one approved interpretation.")
        elif draft_edit:
            try:
                _revise_edition(token,payload,reason)
            except (RuntimeError,ValueError,KeyError,TimeoutError,OSError) as exc:
                st.error("Draft revision was not confirmed: "+str(exc)[:250])
            else:
                st.session_state["market_signals_admin_flash"]="Draft edition updated and verified."
                st.rerun()
        else:
            _perform(token,"edition_create",payload,reason)
    st.html('<div class="ms-admin-context"><strong>Editorial release versus visibility:</strong> '
        'Publishing an edition records a formally checked content vintage. The separate '
        'Advisory service switch determines whether ordinary readers can access it. '
        'Neither action rewrites historical observations.</div>')


def _engagement(token: str) -> None:
    st.subheader("Audience and editorial performance")
    st.caption("Only whitelisted interactions are recorded. This view does not contain individual decisions, private career pipelines or the content of reader inputs.")
    try:
        events=_get(token,"portfolio_market_signal_member_events?select=user_id,event,lens,detail,created_at&order=created_at.desc&limit=3000",
                    limit=3000)
    except (RuntimeError,ValueError,TimeoutError):
        st.error("Member usage statistics are unavailable. Do not interpret missing events as zero readership.")
        return
    if len(events)>=3000:
        st.warning("Metrics cover only the latest 3,000 events; historical totals may be incomplete.")
    day_cut=(datetime.now(timezone.utc)-timedelta(days=30)).date().isoformat()
    recent=[e for e in events if str(e["created_at"])[:10]>=day_cut]
    counts=Counter(e["event"] for e in recent)
    a,b,c,d=st.columns(4)
    a.metric("Distinct active readers · 30d",len({e["user_id"] for e in recent}))
    b.metric("Service opens · 30d",counts["open"])
    c.metric("Decision brief PDFs",counts["pdf_decision"])
    d.metric("Full market-review PDFs",counts["pdf_review"])
    if not events:
        st.info("No instrumented service events recorded yet. Older portfolio activity may exist outside this dedicated market tracker.")
        return
    st.markdown("#### Interaction mix")
    st.dataframe([{"Event":k.replace("_"," ").title(),"Interactions":v} for k,v in
        counts.most_common()],hide_index=True,use_container_width=True)
    lenses=Counter(e["lens"] for e in recent if e["event"]=="lens" and e["lens"])
    if lenses:
        st.markdown("#### Interest by market lens")
        st.bar_chart(dict(lenses),horizontal=True)
    st.markdown("#### Recent anonymous activity")
    st.dataframe([{
        "When":str(e["created_at"])[:16],"Action":e["event"],
        "Lens":e["lens"],"Detail":e["detail"],
    } for e in events[:100]],hide_index=True,use_container_width=True)
    st.caption("Activity is anonymous in this presentation; unique-reader counts are computed from owner-only IDs without displaying identities.")


def _audit(token: str) -> None:
    st.subheader("Editorial change history")
    st.caption("Append-only journal of source approvals, publication decisions, revisions and withdrawals. Each operation records an actor, timestamp and explanation.")
    try:
        audit=_get(token,"portfolio_market_signal_admin_audit?"
            "select=id,action,entity_type,entity_key,rationale,created_at"
            "&order=created_at.desc&limit=350",limit=350)
    except (RuntimeError,ValueError,TimeoutError):
        st.error("The editorial audit log is not readable.")
        return
    if not audit:
        st.info("No editorial management actions have been recorded through the owner console.")
        return
    st.dataframe([{
        "When":str(e["created_at"])[:19],"Action":e["action"].replace("_"," ").title(),
        "Record":e["entity_type"]+" · "+e["entity_key"],"Reason":e["rationale"]
    } for e in audit],hide_index=True,use_container_width=True)
    if len(audit)>=350:
        st.warning("Showing the latest 350 changes; the full append-only history remains in Supabase.")


def render_owner_market_signals(token: str) -> None:
    """Invoked only within verified-owner Advisory Operations."""
    if not token:
        st.error("Owner session unavailable.")
        return
    _hero()
    notice=st.session_state.pop("market_signals_admin_flash",None)
    if notice: st.success(str(notice))
    try:
        data=_load(token)
        pipeline=_pipeline(token)
    except (RuntimeError,ValueError,KeyError,TimeoutError,OSError) as exc:
        st.error("The Market Signals management catalogue cannot be verified. "
                 "No editorial changes can be made.")
        st.caption(str(exc)[:180])
        return
    kpi=_core_status(data,pipeline)
    section=st.selectbox(
        "Management workspace",
        list(SECTIONS),
        format_func=lambda x:SECTIONS[x],
        key="market_signals_admin_area",
        help="Separate workflows prevent one long, crowded administrative page.",
    )
    st.divider()
    if section=="overview":_overview(token,data,pipeline,kpi)
    elif section=="coverage":_analytics_coverage(token,data)
    elif section=="sources":_sources(token,data,pipeline)
    elif section=="evidence":_evidence(token,data)
    elif section=="analysis":_analysis(token,data)
    elif section=="editions":_editions(token,data)
    elif section=="engagement":_engagement(token)
    elif section=="audit":_audit(token)
