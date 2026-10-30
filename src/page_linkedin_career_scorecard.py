"""Owner-only, evidence-led LinkedIn career intelligence."""
from __future__ import annotations
import html
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib import parse, request
import streamlit as st
from site_analytics import ANALYTICS_URL
from site_analytics_public import owner_hiring_headers

def _read(table, fields):
    query = parse.urlencode({"select": fields, "limit": 1000})
    url = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/{table}?{query}"
    with request.urlopen(request.Request(url, headers=owner_hiring_headers()), timeout=12) as response:
        rows = json.load(response)
    if not isinstance(rows, list):
        raise ValueError("Unexpected LinkedIn reporting data")
    return rows

def _date(value):
    try:
        result = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result
    except (ValueError, TypeError):
        return None

def _within(row, field, start, end):
    date = _date(row.get(field))
    return date is not None and (start is None or date >= start) and (end is None or date < end)

def _score(person):
    role = str(person.get("role_title") or "").lower()
    location = str(person.get("geography") or "").lower()
    organization = str(person.get("organization") or "")
    points = 0
    reasons = []
    if any(t in role for t in ("chief", "vp ", "vice president", "director", "head of", "ceo", "partner")):
        points += 3
        reasons.append("Senior decision-maker")
    elif any(t in role for t in ("lead", "manager", "strategist")):
        points += 2
        reasons.append("Relevant functional leader")
    if any(t in role for t in ("ai", "data", "technology", "digital", "talent", "people", "recruit")):
        points += 2
        reasons.append("Career-relevant remit")
    if "sweden" in location or "stockholm" in location or "gothenburg" in location:
        points += 2
        reasons.append("Swedish market")
    if organization:
        points += 1
    return points, ", ".join(reasons) or "Relevance requires verification"

def _panel(title, body, accent=False):
    border = "#d5b49c" if accent else "#dedbd5"
    return f'<div class="lc-panel" style="border-color:{border}"><div class="lc-eyebrow">{html.escape(title)}</div><div class="lc-body">{body}</div></div>'

def render_linkedin_career_scorecard():
    st.markdown("""<style>
    .lc-hero{padding:24px 28px;background:linear-gradient(120deg,#19212a,#29343e);color:#fff;border-radius:15px;margin:10px 0 18px}
    .lc-kicker{color:#dfb596;font-size:.73rem;letter-spacing:.14em;font-weight:700;text-transform:uppercase}
    .lc-hero h1{font-size:clamp(1.5rem,3vw,2.25rem);font-weight:650;margin:9px 0}
    .lc-hero p{color:#d7dce0;margin:0;font-size:.93rem;line-height:1.55}
    .lc-panel{background:#fffdfa;border:1px solid #dedbd5;border-radius:13px;padding:19px 20px;min-height:122px}
    .lc-eyebrow{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:#79716b;font-weight:750}
    .lc-body{font-size:1rem;line-height:1.55;color:#252d32;margin-top:10px}
    .lc-number{font-size:2rem;font-weight:700;letter-spacing:-.05em;line-height:1.1}
    .lc-muted{font-size:.8rem;color:#746f6b;margin-top:8px}
    .lc-person{padding:14px 17px;border:1px solid #e2ddd7;background:#fffdfa;border-radius:11px;margin-bottom:9px}
    .lc-person strong{font-size:1rem;color:#242b32}
    .lc-person-heading{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
    .lc-person-name{color:#242b32!important;font-size:1.02rem;font-weight:700;text-decoration:none!important;border-bottom:1px solid transparent;transition:color .15s,border-color .15s}
    .lc-person-name:hover,.lc-person-name:focus{color:#925b3d!important;border-bottom-color:#925b3d}
    .lc-person-name span{font-size:.83rem;opacity:.65;margin-left:3px}
    .lc-verify{font-size:.74rem!important;color:#857d76!important;margin-top:9px!important}
    .lc-person p{font-size:.82rem;color:#655f5b;margin:5px 0}
    .lc-chip{font-size:.69rem;font-weight:700;color:#76543c;background:#f4e8dc;padding:4px 8px;border-radius:20px}
    .lc-insight{background:linear-gradient(115deg,#202b35,#34424b);border:1px solid #3d4b52;border-radius:16px;padding:23px 26px;margin:12px 0 24px;color:white}
    .lc-insight h2{font-size:1.32rem;color:#fff;margin:9px 0 8px;font-weight:650}
    .lc-insight p{color:#d9e0e1;font-size:.93rem;line-height:1.55;margin:0;max-width:850px}
    .lc-company-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:10px;margin:12px 0 18px}
    .lc-company{display:flex;flex-direction:column;gap:9px;background:#fffdfa;border:1px solid #e4ded6;border-radius:12px;padding:15px 17px;min-height:115px}
    .lc-company strong{font-size:.96rem;color:#28333b;font-weight:700}
    .lc-company small{font-size:.75rem;color:#847d76}
    .lc-company-status{font-size:.69rem;color:#81746c;font-weight:650}
    .lc-company-status.lc-live{color:#326b56}
    </style>""", unsafe_allow_html=True)
    st.markdown("""<div class="lc-hero"><div class="lc-kicker">Private career intelligence</div>
    <h1>LinkedIn Career Conversion</h1>
    <p>From professional visibility to meaningful relationships and hiring opportunities. Focus on the next decision, not vanity metrics.</p></div>""", unsafe_allow_html=True)
    period = st.segmented_control("Evidence window", ["Today", "Yesterday", "This week", "30 days", "90 days", "All history"], default="90 days", key="linkedin_scorecard_period")
    now = datetime.now(ZoneInfo("Europe/Stockholm"))
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "Today":
        start, end = midnight, midnight + timedelta(days=1)
    elif period == "Yesterday":
        start, end = midnight - timedelta(days=1), midnight
    elif period == "This week":
        start, end = midnight - timedelta(days=midnight.weekday()), midnight + timedelta(days=1)
    elif period == "All history":
        start, end = None, None
    else:
        start, end = now - timedelta(days=30 if period == "30 days" else 90), None
    try:
        people_all = _read("linkedin_visibility_people", "id,full_name,role_title,organization,geography,verification_status,profile_url,first_seen_at")
        actions_all = _read("linkedin_visibility_confirmed_actions", "id,person_id,action_type,occurred_at,evidence_basis")
        suggestions_all = _read("linkedin_visibility_connection_suggestions", "id,person_id,suggested_on")
        recommendations_all = _read("linkedin_visibility_recommendations", "id,post_id,suggested_on")
        runs_all = _read("linkedin_visibility_runs", "id,run_at,searches_attempted,verified_posts_found")
    except (OSError, ValueError, RuntimeError, PermissionError):
        st.error("Verified LinkedIn evidence is temporarily unavailable. The dashboard will not invent missing values.")
        return
    people = [x for x in people_all if _within(x, "first_seen_at", start, end)]
    actions = [x for x in actions_all if _within(x, "occurred_at", start, end)]
    suggestions = [x for x in suggestions_all if _within(x, "suggested_on", start, end)]
    recommendations = [x for x in recommendations_all if _within(x, "suggested_on", start, end)]
    runs = [x for x in runs_all if _within(x, "run_at", start, end)]
    def count(*terms):
        return sum(any(term in str(a.get("action_type") or "").lower() for term in terms) for a in actions)
    confirmed = count("reply", "accepted", "conversation", "referral", "introduction", "interview")
    interviews = count("interview")
    verified = sum("verified" in str(p.get("verification_status") or "").lower() for p in people)
    st.markdown("### Relationship intelligence")
    if confirmed:
        headline = "Relationships are progressing"
        narrative = "Confirmed professional responses exist. Prioritize the people already engaging rather than increasing outreach volume."
    elif actions:
        headline = "Activity without a confirmed response"
        narrative = "Review outstanding conversations before contacting more people. The available evidence does not yet show a relationship outcome."
    else:
        headline = "Build the first meaningful conversation"
        narrative = "Relevant people have been identified, but no confirmed conversation is recorded. The priority is a credible introduction, not more impressions."
    st.markdown(
        '<div class="lc-insight"><div class="lc-kicker">Current assessment</div><h2>' + html.escape(headline) +
        '</h2><p>' + html.escape(narrative) + '</p></div>',
        unsafe_allow_html=True,
    )
    organizations = {}
    for person in people_all:
        employer = str(person.get("organization") or "").strip()
        if employer and "verified" in str(person.get("verification_status") or "").lower():
            organizations.setdefault(employer, []).append(person)
    contacted = {a.get("person_id") for a in actions_all}
    active_employers = [org for org, members in organizations.items() if any(p.get("id") in contacted for p in members)]
    st.markdown("### Relationship coverage")
    st.caption("Where professional access exists, and where it is still only a research lead.")
    if organizations:
        tiles = []
        for org, members in sorted(organizations.items(), key=lambda item: (-any(p.get("id") in contacted for p in item[1]), item[0].lower())):
            involved = any(p.get("id") in contacted for p in members)
            label = "Interaction recorded" if involved else "Research only"
            tiles.append('<div class="lc-company"><span class="lc-company-status ' + ("lc-live" if involved else "") + '">' + label + '</span><strong>' + html.escape(org) + '</strong><small>' + ("Review recorded interaction" if involved else "No confirmed relationship yet") + '</small></div>')
        st.markdown('<div class="lc-company-grid">' + "".join(tiles) + '</div>', unsafe_allow_html=True)
    else:
        st.info("No verified employer relationships available yet.")
    st.caption("Company presence is not proof of a vacancy or access to a hiring decision-maker.")
    st.subheader("Who deserves attention next?")
    st.caption("Indicative relevance ranking based on recorded seniority, AI/data remit and Swedish-market proximity. This is not evidence of hiring authority, an open vacancy or personal interest.")
    suggested_ids = {s.get("person_id") for s in suggestions}
    engaged_ids = {a.get("person_id") for a in actions}
    candidates = []
    for p in people:
        if "verified" not in str(p.get("verification_status") or "").lower():
            continue
        score, rationale = _score(p)
        candidates.append((score, p, rationale))
    candidates.sort(key=lambda x: (-x[0], str(x[1].get("full_name") or "")))
    if not candidates:
        st.info("No verified profiles in this period. Broaden the evidence window or improve discovery coverage.")
    else:
        for score, person, rationale in candidates[:6]:
            pid = person.get("id")
            state = "Interaction recorded" if pid in engaged_ids else ("Outreach suggested" if pid in suggested_ids else "Research and qualify")
            name = html.escape(str(person.get("full_name") or "Unnamed profile"))
            role = html.escape(str(person.get("role_title") or "Role not verified"))
            org = html.escape(str(person.get("organization") or "Organization not verified"))
            link = str(person.get("profile_url") or "").strip()
            is_direct = link.startswith(("https://www.linkedin.com/in/", "https://linkedin.com/in/"))
            if not is_direct:
                link = "https://www.linkedin.com/search/results/people/?" + parse.urlencode({"keywords": str(person.get("full_name") or "")})
            destination = html.escape(link, quote=True)
            title = "Open verified LinkedIn profile" if is_direct else "Search LinkedIn for this person; exact profile URL not verified"
            st.markdown(
                f'<div class="lc-person">'
                f'<div class="lc-person-heading"><a class="lc-person-name" href="{destination}" target="_blank" rel="noopener noreferrer" title="{html.escape(title)}">{name} <span aria-hidden="true">↗</span></a>'
                f'<span class="lc-chip">{html.escape(state)}</span></div>'
                f'<p>{role} · {org}</p><p>{html.escape(rationale)}</p>'
                f'{"<p class=lc-verify>LinkedIn search · exact profile pending verification</p>" if not is_direct else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.subheader("What to do next")
    if not actions:
        steps = [
            ("01 · Qualify", "Review the highest-relevance profiles and confirm their current roles and relevance to Swedish enterprise AI hiring."),
            ("02 · Engage", "Select a few genuinely relevant conversations. Record outreach only after it actually happens."),
            ("03 · Establish attribution", "Capture confirmed replies, referrals and interviews so the next review can measure career progress."),
        ]
    else:
        steps = [
            ("01 · Close the evidence gap", "Check outcomes of already-recorded outreach before initiating more contacts."),
            ("02 · Prioritize responses", "Focus on decision-makers and recruiters who have demonstrated engagement."),
            ("03 · Connect to hiring outcomes", "Record introductions, recruiter conversations and interviews only when attributable evidence exists."),
        ]
    cols = st.columns(3)
    for col,(label,body) in zip(cols,steps):
        with col:
            st.markdown(_panel(label,html.escape(body)),unsafe_allow_html=True)
    with st.expander("Evidence quality and activity detail", expanded=False):
        st.write(f"Discovery runs: {len(runs)} · Comment recommendations: {len(recommendations)} · Confirmed comments: {count('comment')}")
        st.caption("Recommendations are not published comments. Profile discovery is not a connection. Stage counts do not represent a validated cohort funnel.")
        if actions:
            st.dataframe(sorted(actions,key=lambda a:str(a.get("occurred_at") or ""),reverse=True),hide_index=True,use_container_width=True)
        else:
            st.write("No confirmed actions recorded for this period.")
    st.caption("Data boundary: LinkedIn profile views, search appearances, follower changes, recruiter approaches, time spent and hiring attribution outside the ledger are unavailable. No conversion rate or ROI is calculated without a defensible denominator.")
