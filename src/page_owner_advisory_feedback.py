"""Owner-only satisfaction reporting for Executive Advisory and online Scorecards.

Decision Usefulness is measured from the executive-recommendation checkpoint.
These are voluntary response metrics, not a representative customer survey.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

import streamlit as st

from page_advisory_service_feedback import STAGE_QUESTIONS
from site_cms import _request_json, _rest_url


def read_owner_feedback(token: str) -> list[dict]:
    rows = _request_json(
        "POST",
        _rest_url("rpc/portfolio_advisory_feedback_owner_list_v1"),
        token=token,
        payload={"p_limit":1000},
        timeout=14,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Feedback reporting is unavailable")
    return rows


def review_feedback(token: str, feedback_id: str, status: str,
                    note: str) -> dict:
    if status not in ("reviewed", "follow_up", "resolved"):
        raise ValueError("Invalid review status")
    if len(note) > 1200:
        raise ValueError("Owner note is too long")
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_feedback_owner_review_v1"),
        token=token,
        payload={
            "p_id":feedback_id,
            "p_status":status,
            "p_note":note,
        },
        timeout=15,
    )
    if not isinstance(result, dict) or result.get("status") != status:
        raise RuntimeError("Review update could not be confirmed")
    return result


def summarize_feedback(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    stages = []
    for stage, (title, _) in STAGE_QUESTIONS.items():
        block = [r for r in rows if r.get("stage") == stage]
        vals = [int(r["rating"]) for r in block if isinstance(r.get("rating"), int)]
        stages.append({
            "Interaction": title,
            "Responses":len(vals),
            "Average /5": round(mean(vals),2) if vals else None,
            "Low (1–2)": sum(v <= 2 for v in vals),
        })
    by_period: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in rows:
        rating = r.get("rating")
        date = str(r.get("created_at") or "")[:7]
        if isinstance(rating, int) and len(date) == 7:
            by_period[(date, str(r.get("stage") or ""))].append(rating)
    monthly = [
        {"Month":month,"Interaction":STAGE_QUESTIONS.get(stage,(stage,""))[0],
         "Responses":len(vals),"Average /5":round(mean(vals),2),
         "Low (1–2)":sum(v <= 2 for v in vals)}
        for (month,stage),vals in sorted(by_period.items(),reverse=True)
    ]
    return stages,monthly


def render_owner_feedback(token: str, people: list[dict]) -> None:
    st.markdown("### Service satisfaction and Decision Usefulness")
    st.caption(
        "Optional feedback, recorded against the actual service and interaction "
        "stage. Ratings range from 1 to 5; missing answers are not zero. "
        "Small samples are directional only."
    )
    try:
        rows = read_owner_feedback(token)
    except (RuntimeError, TimeoutError, ValueError, KeyError):
        st.warning("Satisfaction reporting is temporarily unavailable.")
        return
    if not rows:
        st.info("No feedback recorded yet. Clients can complete their Advisory "
                "work even if they never rate the experience.")
        return
    decision = [
        int(r["rating"]) for r in rows
        if r.get("service_key")=="ai_portfolio_prioritization_scorecard"
        and r.get("stage")=="executive_recommendation"
        and isinstance(r.get("rating"), int)
    ]
    unhappy = [
        r for r in rows if isinstance(r.get("rating"), int)
        and r["rating"]<=2 and r.get("owner_status") not in ("resolved",)
    ]
    a,b,c,d = st.columns(4)
    a.metric("Feedback responses",len(rows))
    b.metric("Decision Usefulness",f"{mean(decision):.2f} / 5" if decision else "No ratings")
    c.metric("Decision usefulness ratings",len(decision))
    d.metric("Low ratings to review",len(unhappy))
    st.markdown("#### Satisfaction by interaction stage")
    stage_rows,monthly = summarize_feedback(rows)
    st.dataframe(stage_rows,hide_index=True,use_container_width=True)
    st.caption("Decision Usefulness comes from the executive recommendation question. "
               "Report usefulness measures potential decision applicability separately.")
    st.markdown("#### Trend by month and stage")
    if monthly:
        st.dataframe(monthly,hide_index=True,use_container_width=True)
    people_by_user={str(p.get("user_id")):p for p in people}
    attention=sorted(
        [r for r in rows if int(r.get("rating") or 5)<=3
         and r.get("owner_status")!="resolved"],
        key=lambda r:(int(r.get("rating") or 5),str(r.get("created_at") or "")),
    )
    st.markdown("#### Recent feedback (including positive comments)")
    st.dataframe([
        {
            "Stage":STAGE_QUESTIONS.get(str(r.get("stage")),("Other",))[0],
            "Service":str(r.get("service_key") or "").replace("_"," ").title(),
            "Rating":r.get("rating"),
            "Comment":str(r.get("comment") or "")[:180],
            "Follow-up requested":"Yes" if r.get("contact_ok") else "No",
            "Submitted":str(r.get("created_at") or "")[:10],
        } for r in rows[:100]
    ],hide_index=True,use_container_width=True)
    st.markdown("#### Friction and follow-up")
    if not attention:
        st.caption("No unresolved ratings of 3 or below.")
        return
    st.dataframe([
        {
            "Client":str(people_by_user.get(str(r.get("user_id")),{}).get("email") or "Advisory member"),
            "Stage":STAGE_QUESTIONS.get(str(r.get("stage")),("Other",))[0],
            "Rating":r.get("rating"),
            "Feedback":str(r.get("comment") or "")[:180],
            "What would help":str(r.get("followup_answer") or "")[:180],
            "Contact permitted":"Yes" if r.get("contact_ok") else "No",
            "Review status":r.get("owner_status"),
            "Submitted":str(r.get("created_at") or "")[:10],
        } for r in attention[:100]
    ],hide_index=True,use_container_width=True)
    selected=st.selectbox(
        "Review a low or uncertain rating",
        [str(r["id"]) for r in attention],
        format_func=lambda rid:(
            next((str(r.get("created_at") or "")[:10]+" · "+
                  STAGE_QUESTIONS.get(str(r.get("stage")),("Feedback",))[0]+
                  " · "+str(r.get("rating"))+"/5"
                  for r in attention if str(r["id"])==rid),rid)
        ),
        key="owner_feedback_review_choice",
    )
    record=next((r for r in attention if str(r["id"])==selected),None)
    if record is None:
        return
    st.caption(
        "Client contact is " + (
            "permitted for this feedback." if record.get("contact_ok")
            else "not requested. Review internally without sending an unsolicited message."
        )
    )
    with st.form("owner_feedback_review_"+selected):
        allowed_statuses = (
            ["reviewed","follow_up","resolved"] if record.get("contact_ok")
            else ["reviewed","resolved"]
        )
        status=st.selectbox(
            "Review status",allowed_statuses,index=0,
        )
        note=st.text_area(
            "Private follow-up note (optional)",
            value=str(record.get("owner_note") or ""),
            max_chars=1200,height=92,
            help="Records your response or the friction identified. Do not store protected client details.",
        )
        saved=st.form_submit_button("Save feedback review")
    if saved:
        try:
            review_feedback(token,selected,status,note)
            st.success("Feedback review recorded with an audit entry.")
            st.rerun()
        except (RuntimeError, TimeoutError, ValueError, KeyError):
            st.error("Feedback review could not be confirmed.")
