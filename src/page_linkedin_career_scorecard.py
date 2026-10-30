from __future__ import annotations
import json
from urllib import request, parse
import streamlit as st
from site_analytics import ANALYTICS_URL
from site_analytics_public import owner_hiring_headers

def _rows(table, columns):
    url = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/{table}?" + parse.urlencode({"select": columns, "limit": 1000})
    with request.urlopen(request.Request(url, headers=owner_hiring_headers()), timeout=12) as response:
        return json.load(response)

def render_linkedin_career_scorecard():
    st.title("LinkedIn Career Conversion")
    st.caption("Owner-only career analytics · Evidence-first relationship tracking")
    try:
        people = _rows("linkedin_visibility_people", "id,full_name,role_title,organization,verification_status")
        actions = _rows("linkedin_visibility_confirmed_actions", "id,person_id,action_type,occurred_at,evidence_basis")
        suggested = _rows("linkedin_visibility_connection_suggestions", "id,person_id")
        recommended = _rows("linkedin_visibility_recommendations", "id,post_id")
    except Exception:
        st.warning("LinkedIn evidence is currently unavailable. No activity has been estimated.")
        return
    def n(*types):
        return sum(any(t in str(a.get("action_type","")).lower() for t in types) for a in actions)
    for col, (label, value) in zip(st.columns(4), [
        ("Discovered profiles", len(people)),
        ("Connection suggestions", len(suggested)),
        ("Confirmed interactions", len(actions)),
        ("Substantive conversations", n("conversation")),
    ]):
        col.metric(label, value)
    st.caption("All recorded history. Suggestions are not confirmed actions.")
    st.subheader("Relationship progression")
    for label, value in [
        ("Profiles discovered", len(people)),
        ("Outreach recommended", len(suggested)),
        ("Contact initiated", n("invitation","message","comment")),
        ("Replied or accepted", n("reply","accepted")),
        ("Substantive conversations", n("conversation")),
        ("Referrals", n("referral","introduction")),
        ("LinkedIn-attributed interviews", n("interview")),
    ]:
        left, right = st.columns([4,1])
        left.write(label)
        right.metric(label="", value=value, label_visibility="collapsed")
    st.subheader("Activity evidence")
    a,b = st.columns(2)
    a.metric("Comment recommendations",len(recommended))
    b.metric("Confirmed comments",n("comment"))
    if actions:
        st.dataframe(sorted(actions,key=lambda r: str(r.get("occurred_at","")),reverse=True),hide_index=True,use_container_width=True)
    else:
        st.info("No confirmed relationship activity has been recorded yet.")
    st.subheader("30-day evaluation")
    st.write("Compare qualified conversations, referrals and interviews with the baseline once reliable time-spent and hiring-attribution evidence is available.")
    st.caption("LinkedIn profile views, search appearances and recruiter approaches are not observable through the current connector. Missing values must never be presented as zero.")
