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
    .lc-person p{font-size:.82rem;color:#655f5b;margin:5px 0}
    .lc-chip{font-size:.69rem;font-weight:700;color:#76543c;background:#f4e8dc;padding:4px 8px;border-radius:20px}
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
    st.subheader("Executive readout")
    if not actions:
        assessment = ("Relationship outcomes are not yet measurable", "The discovery ledger has candidates, but no confirmed outreach or responses. This is an evidence gap, not proof that LinkedIn is ineffective.")
    elif confirmed == 0:
        assessment = ("Activity recorded; relationship progress unconfirmed", "There are logged actions but no recorded replies, conversations or interviews. Check outcomes before changing the strategy.")
    else:
        assessment = ("Verified relationship progress is visible", "Some relationship outcomes are recorded. Review who responded and whether any introductions or interviews followed.")
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown(_panel(assessment[0], html.escape(assessment[1]), True), unsafe_allow_html=True)
    with right:
        st.markdown(_panel("Career conversion signal", f'<div class="lc-number">{interviews if interviews else "—"}</div><div class="lc-muted">Verified LinkedIn-attributed interviews. {"No attribution recorded yet" if not interviews else "Recorded evidence"}</div>'), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(_panel("Relevant network mapped", f'<div class="lc-number">{verified}</div><div class="lc-muted">Verified profiles in selected window · {len(people)} total identified</div>'), unsafe_allow_html=True)
    with c2:
        st.markdown(_panel("Outreach pipeline", f'<div class="lc-number">{len(set(s.get("person_id") for s in suggestions))}</div><div class="lc-muted">Distinct people recommended for contact · not messages sent</div>'), unsafe_allow_html=True)
    with c3:
        st.markdown(_panel("Verified engagement", f'<div class="lc-number">{len(actions)}</div><div class="lc-muted">Recorded actions · {confirmed} relationship outcome signals</div>'), unsafe_allow_html=True)

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
            st.link_button(str(person.get("full_name") or "LinkedIn profile"), link, help="Open verified profile" if is_direct else "Find person on LinkedIn; direct URL not verified", key=f"lc_profile_{pid}")
            st.markdown(f'<div class="lc-person"><span class="lc-chip">{html.escape(state)}</span><p>{role} · {org}</p><p>{html.escape(rationale)}</p></div>', unsafe_allow_html=True)
            if not is_direct:
                st.caption("LinkedIn people search · exact profile URL not yet verified")
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
