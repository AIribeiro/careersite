"""Administrator-only one-click market publisher check and calculation audit.

The button runs provider requests, replays the *frozen* headline-title-basket
for the last complete month, recomputes the current published edition's chart
inputs, and records a transparent owner-only run. It never silently changes
signed-off observations or previously published monthly editions.

NOTE: A successful website availability request is NOT evidence that its
statistics have been re-measured. The nine publisher statuses carry that
distinction explicitly; unapproved families remain excluded from publication.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date,datetime,timezone,timedelta
from hashlib import sha256
from urllib.parse import urlencode,urlsplit,urljoin
import json
import re

import requests

from site_cms import _request_json,_rest_url

USER_AGENT="JairRibeiro-MarketObservatory/1.0 (source audit)"
ALLOWED_HOSTS={
    "www.scb.se","scb.se","historical.api.jobtechdev.se",
    "jobsearch.api.jobtechdev.se","www.brainville.com","brainville.com",
    "www.almega.se","almega.se","www.konj.se","konj.se",
    "www.manpowergroup.se","manpowergroup.se","www.swedbank.se","swedbank.se",
    "techsverige.se","www.techsverige.se"
}
ARTICLE_OVERRIDE={
 "scb_enterprise_ai_adoption":
    "https://www.scb.se/hitta-statistik/statistik-efter-amne/forskning-och-det-digitala-samhallet/det-digitala-samhallet/it-anvandning-i-foretag/pong/statistiknyhet/it-anvandning-i-foretag-2026/",
 "brainville_consulting_market":"https://www.brainville.com/sv/Blog/Post/1923",
}

# Frozen JobTech title-basket v1 queries and exclusion/role patterns. Method
# change requires an expressly versioned release; never silently add titles.
JOBTECH_SEEDS=(
 "AI Lead","AI Head","AI Director","AI Manager","AI Strategy",
 "AI Transformation","AI Governance","AI Adoption","AI Enablement",
 "AI Capability","AI Portfolio","Responsible AI","AI Automation",
 "AI Innovation","AI Productivity","AI Upskilling","GenAI Lead",
 "Data AI Lead","Data AI Head","Data AI Director","Data AI Manager",
 "Head Data","Director Data","Head Analytics","Director Analytics",
 "Manager Data Analytics","Data Governance","AI strateg",
 "AI ansvarig","Verksamhetsutvecklare AI",
)
EXCLUDE=re.compile(
 r"\b(engineer|engineering|developer|utvecklare|scientist|researcher|research|forsk\w*|"
 r"architect|arkitekt|programmer|software|mlops|machine learning|data engineer|"
 r"data scientist|product owner|product manager|product lead|project manager|"
 r"program manager|scrum|analyst|tekniker|technician|sales|business development|"
 r"presales|pre-sales|marketing|growth|content|retail|workstream|controller|"
 r"service manager|tech lead|technical lead|team lead)\b",re.I
)


def _allows(url:str) -> bool:
    parsed=urlsplit(url)
    return (parsed.scheme=="https" and parsed.hostname in ALLOWED_HOSTS
            and parsed.username is None and parsed.password is None
            and parsed.port in (None,443))


def _safe_get(url:str, *, params:dict|None=None,timeout:int=18) -> requests.Response:
    if not _allows(url):
        raise ValueError("Unapproved publisher URL blocked.")
    current=url
    for _ in range(4):
        response=requests.get(current,params=params,allow_redirects=False,
            headers={"user-agent":USER_AGENT,"accept":"text/html, application/json"},
            timeout=(5,timeout))
        if response.status_code in (301,302,303,307,308):
            target=urljoin(current,response.headers.get("Location") or "")
            if not _allows(target):
                raise ValueError("Publisher redirect leaves approved domain set.")
            current=target
            params=None
            continue
        return response
    raise ValueError("Publisher redirect chain exceeds safety limit.")


def _source_check(source:dict) -> dict:
    key=str(source["source_family"])
    url=ARTICLE_OVERRIDE.get(key) or str(source.get("source_url") or "")
    summary={
        "source_family":key,
        "review_status":str(source.get("review_status") or "unknown"),
        "source_url":url,
        "source_check":"publisher_page_probe_only",
        "status":"failed",
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "extracted_new_metrics":False,
        "description":"Publisher reachability is not a fresh numeric release.",
    }
    if not url:
        summary["error"]="No registered original-source URL."
        return summary
    try:
        r=_safe_get(url,timeout=16)
        summary["http_status"]=r.status_code
        if r.status_code!=200:
            summary["error"]=f"Publisher returned HTTP {r.status_code}."
            return summary
        content=r.content[:1024*1024]
        summary["response_sha256"]=sha256(content).hexdigest()
        summary["bytes_inspected"]=len(content)
        summary["status"]="reachable"
        summary["description"]=(
            "Original publisher page reachable. Numeric observations remain "
            "unchanged until an issuer-specific parser and editorial checks "
            "validate the new publication."
        )
    except (requests.RequestException,ValueError,OSError) as exc:
        summary["error"]=str(exc)[:240]
    return summary


def _classify(headline:str) -> bool:
    h=re.sub(r"\s+"," ",str(headline or "")).strip()
    if not h or EXCLUDE.search(h):
        return False
    ai=bool(re.search(r"\b(ai|artificial intelligence|genai|generative ai)\b",h,re.I)
       or re.search(r"\bai[-\s]?strateg\b",h,re.I))
    strategic=bool(re.search(
       r"\b(strategy|strateg|transformation|governance|adoption|enablement|capability|"
       r"portfolio|value|productivity|responsible|automation|innovation|upskilling|"
       r"center of excellence|centre of excellence|coe|verksamhetsutvecklare|ansvarig)\b",h,re.I))
    senior_ai=bool(re.search(r"\b(head|director|lead|leader|chef)\b",h,re.I))
    ai_manager=bool(re.search(r"\b(ai|genai|generative ai)\s+manager\b",h,re.I)
        or re.search(r"\bmanager\s+(?:of\s+)?(?:ai|genai|generative ai)\b",h,re.I))
    data_ai=bool(re.search(r"(data\s*(?:&|and|och)?\s*ai|ai\s*(?:&|and|och)?\s*data)",h,re.I))
    data_analytics=bool(re.search(r"\b(data|analytics)\b",h,re.I))
    senior_data=bool(re.search(r"\b(head|director|chef)\b",h,re.I) and data_analytics)
    manager_data=bool(re.search(r"\bmanager\b",h,re.I) and
        re.search(r"(data\s*(?:&|and)\s*analytics|analytics\s*(?:&|and)\s*data)",h,re.I))
    governance=bool(re.search(r"\bdata\s+governance\b",h,re.I)
            and re.search(r"\b(lead|head|director|manager|chef|ansvarig)\b",h,re.I))
    swedish=bool(re.search(
        r"\b(ai[-\s]?strateg|verksamhetsutvecklare.*\bai\b|ai.*ansvarig|ansvarig.*\bai\b)",h,re.I))
    return (ai and (strategic or senior_ai or ai_manager)) or (
       data_ai and bool(re.search(r"\b(lead|head|director|manager|chef|ansvarig)\b",h,re.I))
    ) or senior_data or manager_data or governance or swedish


def _jobtech_query(src:str,seed:str,start:str,end:str) -> list[dict]:
    # JobTech publisher may revise or timeout. Never guess missing pages.
    base=(
      "https://historical.api.jobtechdev.se/search"
      if src=="historical" else
      "https://jobsearch.api.jobtechdev.se/search"
    )
    params={
      "published-after":start,"published-before":end,
      "q":seed,"limit":100,"offset":0,"resdet":"full","sort":"pubdate-asc",
    }
    response=_safe_get(base,params=params,timeout=20)
    if response.status_code!=200:
        raise RuntimeError(f"JobTech {src} query failed HTTP {response.status_code}")
    first=response.json()
    total=int((first.get("total") or {}).get("value") or 0)
    if total>2000:
        raise RuntimeError("JobTech query exceeds complete pagination limit: "+seed)
    hits=list(first.get("hits") or [])
    for off in range(100,total,100):
        params["offset"]=off
        page=_safe_get(base,params=params,timeout=20)
        if page.status_code!=200:
            raise RuntimeError(f"JobTech pagination failed for {seed} at {off}.")
        hits.extend(page.json().get("hits") or [])
    return hits


def _jobtech_latest_complete(points:list[dict]) -> dict:
    """Re-run frozen title basket for most recent complete approved month."""
    active=[p for p in points if
            p.get("series_code")=="jobtech_ai_data_leadership_v1"
            and p.get("geography")=="Sweden" and p.get("period_complete")]
    if not active:
        return {"ok":False,"error":"No complete approved JobTech vintage to replay."}
    latest=max(active,key=lambda p:str(p.get("period_start")))
    start=str(latest["period_start"])[:10]
    month=date.fromisoformat(start)
    end=(date(month.year+1,1,1) if month.month==12
         else date(month.year,month.month+1,1)).isoformat()
    tasks=[(origin,seed) for origin in ("historical","current") for seed in JOBTECH_SEEDS]
    data=[]
    errors=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(_jobtech_query,origin,seed,start,end):(origin,seed)
                 for origin,seed in tasks}
        for future in as_completed(futures):
            src,seed=futures[future]
            try:data.extend(future.result())
            except (RuntimeError,ValueError,requests.RequestException,OSError) as exc:
                errors.append(f"{src}:{seed}: {str(exc)[:100]}")
    if errors:
        return {"ok":False,"month":start[:7],"queries_attempted":len(tasks),
                "queries_failed":len(errors),"errors":errors[:6],
                "note":"Incomplete provider replay; no comparison or publication allowed."}
    unique={}
    for hit in data:
        if not _classify(hit.get("headline") or ""):continue
        oid=str(hit.get("original_id") or "").strip()
        key=("o:"+oid if oid else
             "f:"+"|".join(str(x or "") for x in (
                 hit.get("headline"),(hit.get("employer") or {}).get("name"),
                 hit.get("publication_date"))).lower())
        unique.setdefault(key,hit)
    rows=list(unique.values())
    def region(pattern):
        return sum(bool(re.search(pattern,str((r.get("workplace_address") or {}).get("region") or ""),re.I))
                   for r in rows)
    values={
      "Sweden":len(rows),
      "Stockholm":region("stockholm"),
      "Västra Götaland":region("västra götaland|vastra gotaland"),
    }
    known={str(p["geography"]):int(float(p["value"])) for p in points
           if str(p.get("period_start"))[:7]==start[:7]
           and p.get("series_code")=="jobtech_ai_data_leadership_v1"
           and p.get("period_complete")}
    return {
      "ok":True,"month":start[:7],"queries_attempted":len(tasks),
      "queries_failed":0,"computed":values,"published_snapshot":known,
      "matches_published":values==known,
      "proposed_changes":({k:{"published":known.get(k),"replayed":v}
                          for k,v in values.items() if known.get(k)!=v}),
      "note":"Candidate replay only; never overwrites a signed-off edition."
    }


def _recalculate(points:list[dict],briefs:list[dict],edition:dict) -> dict:
    manifest=list(edition.get("evidence_codes") or [])
    references=list(edition.get("brief_slugs") or [])
    source={p["code"]:p for p in points if p.get("is_published")}
    narrative={b["slug"]:b for b in briefs if b.get("is_published")}
    issues=[]
    if len(manifest)!=len(set(manifest)):issues.append("Duplicate evidence in edition manifest.")
    if any(x not in source for x in manifest):issues.append("Missing approved source observation.")
    if any(x not in narrative for x in references):issues.append("Missing published executive analysis.")
    for key in references:
        b=narrative.get(key)
        if not b:continue
        refs=b.get("evidence_codes") or []
        if not set(refs).issubset(manifest):issues.append("Unsupported interpretation: "+key)
        families={source[c]["source_family"] for c in refs if c in source}
        if b.get("support_level")=="independent_sources" and len(families)<2:
            issues.append("Unsupported independent-source interpretation: "+key)
    selected=[source[c] for c in manifest if c in source]
    if not selected:issues.append("No validated edition evidence.")
    records=[{
       "code":p["code"],"value":str(p["value"]),"unit":p["metric_unit"],
       "period":p["period_label"],"geography":p["geography"],
       "source_family":p["source_family"],"verified_on":str(p["verified_on"])
    } for p in selected]
    records.sort(key=lambda x:x["code"])
    canonical=json.dumps(records,ensure_ascii=True,sort_keys=True,separators=(",",":"))
    groups={}
    for p in selected:
        family=p["source_family"]
        groups[family]=groups.get(family,0)+1
    monthly=sorted([
        {"period":str(p["period_start"])[:7],"region":p["geography"],"ads":int(float(p["value"]))}
        for p in selected
        if p.get("series_code")=="jobtech_ai_data_leadership_v1"
        and p.get("period_complete")
    ],key=lambda x:(x["period"],x["region"]))
    return {
      "ok":not issues,"errors":issues,"edition_slug":edition.get("slug"),
      "observation_count":len(selected),
      "analysis_count":len(references),
      "source_family_counts":groups,
      "complete_monthly_leadership":monthly,
      "publisher_denominators_preserved":True,
      "evidence_checksum_sha256":sha256(canonical.encode()).hexdigest(),
      "comparison_policy":"Never mix survey subgroups, consulting denominators or nested regions.",
      "publication_unchanged":True,
    }


def run_admin_market_refresh(token:str, data:dict) -> dict:
    """One click checks all nine source families and recalculates the edition.

    A partial or failed provider response is written as such; missing extracts
    never become zero or silently update reader-facing published statistics.
    """
    if not token:raise PermissionError("Administrator session required.")
    role=_request_json("POST",_rest_url("rpc/portfolio_advisory_my_role_v1"),
                       token=token,payload={},timeout=12)
    if role!="admin":raise PermissionError("Only verified market administrators may refresh.")
    sources=_request_json("POST",
        _rest_url("rpc/portfolio_market_signal_refresh_sources_v1"),
        token=token,payload={},timeout=15)
    if not isinstance(sources,list) or not sources:
        raise RuntimeError("Source registry cannot be read. No refresh recorded.")
    editions=[e for e in data.get("editions",[]) if e.get("status")=="published"]
    if not editions:
        raise RuntimeError("No published edition for analytical recalculation.")
    edition=max(editions,key=lambda e:str(e.get("published_at") or ""))
    points=data["points"];briefs=data["briefs"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses=list(pool.map(_source_check,sources))
    replay=_jobtech_latest_complete(points)
    for row in responses:
        if row["source_family"]=="af_jobtech_target_demand":
            row["source_check"]="frozen_classifier_complete_month_replay"
            row["numeric_replay"]=replay
            row["extracted_new_metrics"]=bool(replay.get("ok"))
            # Endpoint availability alone is insufficient to call a failed replay successful.
            if not replay.get("ok"):
                row["status"]="failed"
                row["error"]="JobTech v1 complete-month replay did not finish."
    calculations=_recalculate(points,briefs,edition)
    calculations["jobtech_replay"]=replay
    calculations["ok"]=bool(calculations["ok"]) and (
       replay.get("ok") is True or
       # Replay failure must be visible but cannot invalidate the immutable
       # existing signed-off snapshot's independent arithmetic.
       calculations["observation_count"]==len(edition.get("evidence_codes") or [])
    )
    proposal_count=len(replay.get("proposed_changes") or {})
    payload={
       "source_results":responses,"calculations":calculations,
       "release_slug":edition["slug"],"proposal_count":proposal_count,
       "note":"All registered publisher pages checked. Frozen JobTech v1 replay attempted. "
              "Current signed-off edition recalculated; no unreviewed observations "
              "were promoted to reader-facing data."
    }
    receipt=_request_json("POST",
         _rest_url("rpc/portfolio_market_signal_record_refresh_v1"),
         token=token,payload={"p_result":payload},timeout=20)
    if not isinstance(receipt,dict) or receipt.get("recorded") is not True:
        raise RuntimeError("Refresh was executed but could not be confirmed in audit.")
    return {"receipt":receipt,"source_results":responses,"calculations":calculations}
