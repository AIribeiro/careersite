"""Role eligibility: director ambition and mandate-equivalent functional leadership."""
from __future__ import annotations
from collections import Counter
from datetime import date, timedelta
import re

POLICY_VERSION = "ai-leadership-mandates-v1-2026-10-20"
AI = re.compile(r"\b(?:AI|artificial intelligence|GenAI|Copilot)\b", re.I)
PRIMARY = re.compile(r"\b(?:Director|Head of|Chief|VP)\W+(?:of\W+)?(?:Enterprise\W+)?(?:AI|artificial intelligence)\b|\b(?:AI|artificial intelligence)\s+(?:Transformation\s+)?(?:Director|Head)\b|\bVP Domain Head\b.{0,40}\bAI\b", re.I)
FUNCTIONAL = re.compile(r"\b(?:Senior Manager|Manager|Lead|Strategy|Transformation|Adoption|Enablement|Capability|Governance|Productivity|Operating Model|Portfolio)\b", re.I)
ADJACENT = re.compile(r"\b(?:Data|Analytics|Business Intelligence|Intelligent Automation|Enterprise Architecture|Governance)\b", re.I)
LEADERSHIP = re.compile(r"\b(?:Senior Manager|Head|Director|Lead|Chief|VP|Senior Principal)\b", re.I)
CRAFT = re.compile(r"\b(?:AI Engineer|ML Engineer|Machine Learning Engineer|MLOps|Data Scientist|Prompt Engineer|Software Engineer|Developer|Data Analyst|Solutions Architect|Pre-Sales|Program Manager|Project Manager|Technical Lead|Technical Product|Engineering Manager|AI Development)\b", re.I)
MANDATE = ("roadmap","portfolio","governance","operating model","ai strategy","business value","value realization","adoption","stakeholder","cross-functional","transformation","budget","decision rights","capability development")
SPECIALIST = re.compile(r"\bSpecialists?\b", re.I)
FUNCTIONAL_HEAD = re.compile(r"\bHead of AI\s+(?:Adoption|Enablement|Capability|Productivity)\b", re.I)
CRAFT_SCOPE = ("hands-on coding","hands-on software development","build and deploy ml models","quota-carrying sales")

def classify_title(title):
    t = " ".join(str(title or "").split())
    if CRAFT.search(t):
        return "outside_or_uncertain"
    if SPECIALIST.search(t):
        return "adjacent" if ADJACENT.search(t) else "outside_or_uncertain"
    if FUNCTIONAL_HEAD.search(t):
        return "functional"
    if PRIMARY.search(t):
        return "primary"
    if AI.search(t) and FUNCTIONAL.search(t):
        return "functional"
    if ADJACENT.search(t) and LEADERSHIP.search(t):
        return "adjacent"
    return "outside_or_uncertain"

def assess_role(title, description=None):
    lane = classify_title(title)
    content = str(description or "").casefold()
    signals = [s for s in MANDATE if s in content]
    if lane == "outside_or_uncertain":
        scope = "not_established"
    elif any(x in content for x in CRAFT_SCOPE):
        scope = "craft_conflict_review"
    elif len(signals) >= 2:
        scope = "strategic_signals_review"
    else:
        scope = "mandate_unverified"
    return {"lane":lane,"scope":scope,"signals":signals[:5],
            "conversion_candidate":lane in ("primary","functional"),
            "verified_suitable":False,"policy_version":POLICY_VERSION}

def catalog_sensitivity(rows, as_of):
    """Deduplicated title candidates, not a labor-market census or forecast."""
    day = date.fromisoformat(str(as_of)[:10])
    unique = {}
    for r in rows or []:
        if r.get("is_active") is not True or str(r.get("country_code") or "").upper() != "SE":
            continue
        title = str(r.get("title") or "")
        company = str(r.get("company_name") or "")
        if not title.strip():
            continue
        k = (re.sub(r"\W+", "", company.casefold()),re.sub(r"\W+", "", title.casefold()))
        if k not in unique or str(r.get("first_seen_at") or "") > str(unique[k].get("first_seen_at") or ""):
            unique[k] = r
    counts, recent, scope = Counter(), Counter(), Counter()
    for r in unique.values():
        item = assess_role(r.get("title"),r.get("description"))
        lane = item["lane"]
        counts[lane] += 1
        scope[item["scope"]] += 1
        try:
            first = date.fromisoformat(str(r.get("first_seen_at") or "")[:10])
            if day - timedelta(days=45) <= first <= day:
                recent[lane] += 1
        except ValueError:
            pass
    return {"policy_version":POLICY_VERSION,"sample_size":len(unique),
            "title_counts":dict(counts),"recent_45d":dict(recent),
            "scope_screen":dict(scope),"primary":counts["primary"],
            "primary_plus_functional":counts["primary"]+counts["functional"],
            "incremental_functional":counts["functional"],"verified_suitable":0,
            "status":"Title-based discovery sensitivity, not independently verified hiring demand"}

def pipeline_sensitivity(processes):
    """Uses only top processes supplied by owner-only stage model."""
    seen, counts, advanced, details = set(), Counter(), Counter(), []
    for p in processes or []:
        k = str(p.get("process_key") or (str(p.get("employer"))+"|"+str(p.get("role")))).casefold()
        if k in seen:
            continue
        seen.add(k)
        if p.get("status") in ("employer_rejection","stale_unknown","closed_unreconciled","excluded_verified"):
            continue
        lane = classify_title(p.get("role"))
        counts[lane] += 1
        if p.get("stage") not in (None,"application_only","human_response"):
            advanced[lane] += 1
        details.append({"employer":p.get("employer"),"role":p.get("role"),
                        "lane":lane,"stage":p.get("stage"),
                        "scope":"title_only_unverified"})
    return {"counts":dict(counts),"advanced":dict(advanced),"details":details,
            "scope":"top-ranked active processes only; titles need mandate verification",
            "scoring_effect":"None: existing v2 already scores AI strategy/adoption leads within family A",
            "timing_effect":"No measured adjustment without validated offer outcomes"}
