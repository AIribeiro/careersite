"""Short, optional, contextual customer feedback across Executive AI Advisory.

Never gate the recommendation or download behind a survey. One response per
actual interaction is stored in a private RLS-protected Supabase table.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import quote

import streamlit as st

from site_cms import _request_json, _rest_url

PROMPTS = {
    ("advisory", "onboarding"): "How straightforward was creating your Advisory account?",
    ("advisory", "conversation"): "How useful was this advisory exchange?",
    ("scorecard", "decision"): "How useful was the Scorecard for your decision?",
    ("rollout", "assessment"): "How relevant and clear was this assessment?",
    ("rollout", "recommendation"): "How useful was the recommendation for your next decision?",
    ("rollout", "download"): "How ready is this report for a leadership discussion?",
}

def _prior(token: str, uid: str, service: str, stage: str, interaction: str) -> bool:
    endpoint = (
        "portfolio_advisory_feedback?select=id"
        "&user_id=eq." + quote(uid, safe="") +
        "&service_key=eq." + quote(service, safe="") +
        "&stage=eq." + quote(stage, safe="") +
        "&interaction_key=eq." + quote(interaction, safe="") + "&limit=1"
    )
    rows = _request_json("GET", _rest_url(endpoint), token=token, timeout=10)
    if not isinstance(rows, list):
        raise RuntimeError("Feedback state unavailable")
    return bool(rows)

def _submit(token: str, uid: str, service: str, stage: str,
            interaction: str, request_id: str | None, rating: int, comment: str) -> None:
    if (service, stage) not in PROMPTS or rating not in (1, 2, 3, 4, 5):
        raise ValueError("Unsupported feedback response")
    payload = {
        "user_id": uid,
        "request_id": request_id,
        "service_key": service,
        "stage": stage,
        "interaction_key": interaction,
        "rating": rating,
        "comment": comment.strip()[:1000],
    }
    rows = _request_json("POST", _rest_url("portfolio_advisory_feedback"),
                         token=token, payload=payload,
                         prefer="return=representation", timeout=12)
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Feedback could not be confirmed")

def render_feedback(session: dict, user: dict, service: str, stage: str,
                    interaction: str, request_id: str | None = None) -> None:
    """A single optional 5-point micro-survey following an actual milestone."""
    if (service, stage) not in PROMPTS:
        return
    uid = str(user.get("id") or "")
    token = str(session.get("access_token") or "")
    if not uid or not token or not interaction:
        return
    key = "csat_" + service + "_" + stage + "_" + interaction.replace("-", "")[:36]
    try:
        if _prior(token, uid, service, stage, interaction):
            return
    except (RuntimeError, TimeoutError, ValueError, KeyError):
        # Satisfaction is never a blocking dependency for Advisory.
        return
    with st.expander("Help improve this advisory experience · optional", expanded=False):
        st.caption("A brief private rating. It does not affect your access or recommendation.")
        with st.form(key):
            st.markdown("**" + PROMPTS[(service, stage)] + "**")
            rating = st.radio(
                "Satisfaction", [1, 2, 3, 4, 5], index=None,
                horizontal=True, key=key+"_rating",
                help="1 = not useful / very difficult; 5 = highly useful / very straightforward.",
            )
            comment = st.text_area(
                "What should be improved? (optional)",
                max_chars=1000, height=78, key=key+"_comment",
            )
            send = st.form_submit_button("Submit private feedback")
        if send:
            if rating is None:
                st.warning("Choose a rating from 1 to 5.")
            else:
                try:
                    _submit(token, uid, service, stage, interaction,
                            request_id, int(rating), comment)
                    st.success("Thank you. Your feedback was recorded.")
                except (ValueError, RuntimeError, TimeoutError, KeyError):
                    st.error("Feedback could not be stored. This does not affect your advisory access.")

def render_owner_feedback(token: str) -> None:
    """Owner-only satisfaction view, including dissatisfied-client follow-up."""
    st.markdown("### Customer satisfaction")
    st.caption("Private, voluntary ratings. CSAT is the share of responses rated 4 or 5; "
               "these are respondent scores, not a population-wide estimate.")
    try:
        rows = _request_json(
            "GET", _rest_url("portfolio_advisory_feedback?select=*"
                             "&order=created_at.desc&limit=1000"),
            token=token, timeout=15,
        )
        if not isinstance(rows, list):
            raise RuntimeError("Invalid private feedback response")
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        st.error("Could not load private satisfaction reporting.")
        return
    if not rows:
        st.info("No client satisfaction responses yet.")
        return
    answered = [r for r in rows if isinstance(r.get("rating"), int)]
    if not answered:
        st.info("No scored feedback yet.")
        return
    positives = sum(r["rating"] >= 4 for r in answered)
    k = st.columns(3)
    k[0].metric("Client responses", len(answered))
    k[1].metric("CSAT · 4–5", f"{100*positives/len(answered):.0f}%")
    k[2].metric("Needs attention · 1–2", sum(r["rating"] <= 2 for r in answered))
    groups = defaultdict(list)
    for row in answered:
        groups[(str(row.get("service_key") or ""),
                str(row.get("stage") or ""))].append(row["rating"])
    display = []
    for (service, stage), scores in sorted(groups.items()):
        display.append({
            "Service": service.title(), "Interaction": stage.replace("_"," ").title(),
            "Responses": len(scores), "Mean / 5": round(sum(scores)/len(scores),2),
            "CSAT": f"{100*sum(x>=4 for x in scores)/len(scores):.0f}%",
        })
    st.dataframe(display, hide_index=True, use_container_width=True)
    st.markdown("#### Follow-up signals")
    lower = [r for r in answered if r["rating"] <= 2]
    if not lower:
        st.caption("No ratings of 1 or 2 so far.")
    for row in lower[:30]:
        with st.expander(
            f"{row.get('created_at','')[:10]} · {row.get('service_key','')} / "
            f"{row.get('stage','')} · {row.get('rating')}/5"
        ):
            st.write(str(row.get("comment") or "No additional comment."))
            st.caption("Client user ID: " + str(row.get("user_id") or "") +
                       " · Advisory request: " + str(row.get("request_id") or "not specified"))
    st.caption("Most recent 1,000 responses; client feedback is never published publicly.")
