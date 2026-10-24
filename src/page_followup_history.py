"""A durable per-process timeline of recruiter interactions and repeated follow-ups."""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st
from site_cms import _request_json, _rest_url

EVENT_TABLE = "careersite_followup_events"
SUMMARY_VIEW = "careersite_followup_history_counts_v1"
TYPES = {
    "followup_sent": "Status follow-up sent",
    "recruiter_reply": "Recruiter / hiring manager replied",
    "candidate_message": "Other candidate message / thank-you",
    "interview_invited": "Interview invitation",
    "interview_scheduled": "Interview scheduled / rescheduled",
    "interview_completed": "Interview completed",
    "reference_check": "Reference check",
    "recruiter_call": "Recruiter call",
    "status_change": "Status changed",
    "note": "Other update / note",
}
CHANNELS = {
    "outlook": "Outlook",
    "gmail": "Gmail",
    "linkedin": "LinkedIn",
    "calendar": "Calendar",
    "phone": "Phone",
    "video": "Video call",
    "in_person": "In person",
    "other": "Other",
}
DIRECTION = {"followup_sent": "outbound", "recruiter_reply": "inbound",
    "candidate_message": "outbound", "interview_completed": "two_way",
    "reference_check": "two_way", "recruiter_call": "two_way"}
STOCKHOLM = ZoneInfo("Europe/Stockholm")


def fetch_history(token: str, source_type: str, source_ref: str) -> list[dict]:
    if source_type not in ("managed", "analytics", "jobwise", "evidence") or not source_ref:
        return []
    path = (
        f"{EVENT_TABLE}?select=id,event_on,occurred_at,event_type,direction,channel,"
        f"contact_name,summary,evidence_ref,confidence,source_system"
        f"&source_type=eq.{source_type}&source_ref=eq.{source_ref}"
        f"&order=event_on.desc,id.desc&limit=300"
    )
    result = _request_json("GET", _rest_url(path), token=token)
    if not isinstance(result, list):
        raise RuntimeError("Interaction history could not be loaded.")
    return result


def fetch_history_counts(token: str) -> dict[tuple[str, str], dict]:
    result = _request_json(
        "GET", _rest_url(f"{SUMMARY_VIEW}?select=*&limit=1000"), token=token
    )
    if not isinstance(result, list):
        raise RuntimeError("Follow-up history counts unavailable.")
    return {(r["source_type"], str(r["source_ref"])): r for r in result}


def record_event(token: str, row: dict, event_on: date, event_type: str,
                 channel: str, contact: str, summary: str, evidence: str) -> None:
    source_type = str(row.get("source_type") or "")
    source_ref = str(row.get("source_ref") or "")
    if source_type not in ("managed", "analytics", "jobwise", "evidence") or not source_ref:
        raise ValueError("Missing exact process identity")
    if event_type not in TYPES or channel not in CHANNELS:
        raise ValueError("Unsupported interaction or channel")
    today = datetime.now(STOCKHOLM).date()
    if not date(2020,1,1) <= event_on <= today:
        raise ValueError("Select a real date, not later than today.")
    if not summary.strip():
        raise ValueError("Describe what was actually said or done.")
    payload = {
        "source_type": source_type, "source_ref": source_ref,
        "event_on": event_on.isoformat(), "event_type": event_type,
        "direction": DIRECTION.get(event_type, "none"),
        "channel": channel, "contact_name": contact.strip() or None,
        "summary": summary.strip()[:2500],
        "evidence_ref": evidence.strip()[:1800] or None,
        "confidence": "user_recorded", "source_system": "manual",
    }
    _request_json(
        "POST", _rest_url(EVENT_TABLE), token=token,
        payload=payload, prefer="return=minimal",
    )


def _row_title(item: dict) -> str:
    code = item.get("event_type") or "other"
    return TYPES.get(code, code.replace("_", " ").capitalize())


def history_editor(token: str, row: dict, *, prefix: str = "managed") -> None:
    source_type = str(row.get("source_type") or "")
    source_ref = str(row.get("source_ref") or "")
    key = f"{prefix}_{source_type}_{source_ref}"
    with st.expander("Interaction history · follow-ups and replies", expanded=False):
        try:
            events = fetch_history(token, source_type, source_ref)
        except RuntimeError as exc:
            st.warning(f"History unavailable: {exc}")
            return
        followups = sum(e.get("event_type") == "followup_sent" for e in events)
        replies = sum(e.get("event_type") == "recruiter_reply" for e in events)
        interviews = sum(e.get("event_type") == "interview_completed" for e in events)
        cols = st.columns(4)
        for c,title,val in zip(cols,("Interactions", "Status chasers", "Replies", "Completed interviews"),
                               (len(events),followups,replies,interviews)):
            c.metric(title,val)
        if events:
            for e in events[:50]:
                label = _row_title(e)
                timestamp = str(e.get("occurred_at") or e.get("event_on") or "")[:16]
                # When timestamp is date only, do not suggest a verified clock time.
                who = e.get("contact_name")
                details = (" · " + str(who)) if who else ""
                st.markdown(f"**{e.get('event_on') or 'Unknown date'} · {label}**" + details)
                st.caption(
                    f"{str(e.get('channel') or 'other').capitalize()} · "
                    f"{e.get('direction') or 'none'} · {e.get('confidence') or 'unverified'}"
                    + (f" · {e['evidence_ref']}" if e.get("evidence_ref") else "")
                )
                st.write(str(e.get("summary") or ""))
                st.divider()
            if len(events)>50:
                st.caption(f"Showing 50 of {len(events)} interactions. More events are retained.")
        else:
            st.caption("No dated interactions yet. Add the first verified conversation or follow-up.")
        st.markdown("**Add interaction**")
        with st.form(f"add_interaction_{key}", border=False):
            a,b=st.columns([1.6,1])
            with a:
                kind=st.selectbox("Event",options=list(TYPES),
                    format_func=lambda x:TYPES[x],key=f"hist_type_{key}")
            with b:
                on=st.date_input("Date",value=datetime.now(STOCKHOLM).date(),
                    max_value=datetime.now(STOCKHOLM).date(),format="DD/MM/YYYY",
                    key=f"hist_date_{key}")
            a,b=st.columns(2)
            with a:
                channel=st.selectbox("Channel",options=list(CHANNELS),
                    format_func=lambda x:CHANNELS[x],key=f"hist_channel_{key}")
            with b:
                contact=st.text_input("Person (optional)",key=f"hist_contact_{key}")
            summary=st.text_area("What happened?",height=75,key=f"hist_summary_{key}",
                placeholder="Briefly describe the actual reply, discussion or message sent")
            evidence=st.text_input("Evidence (optional)",key=f"hist_evidence_{key}",
                placeholder="Message subject, Outlook/LinkedIn reference or calendar event")
            saved=st.form_submit_button("Add to history",type="primary")
        if saved:
            try:
                record_event(token,row,on,kind,channel,contact,summary,evidence)
            except (ValueError,RuntimeError) as exc:
                st.error(f"Unable to save interaction: {exc}")
            else:
                st.success("Interaction added. Previous events remain unchanged.")
                st.rerun()
        st.caption(
            "Historical notes and sent-message evidence are distinct. Adding a follow-up to "
            "the timeline does not claim a message was sent by the app or increment the "
            "current send counter; mark actual sends in Contact controls after confirmation. "
            "Events are append-only to preserve each attempt."
        )
