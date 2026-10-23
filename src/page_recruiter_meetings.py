"""Owner-only recruiter meeting intelligence.

This is a manually maintained, provenance-aware calendar *snapshot*, not a
background connector to Outlook or Google Calendar. Only explicit calendar
meetings and independently evidenced interviews belong in this ledger.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from calendar import monthrange
from io import StringIO
import csv
from urllib.parse import quote
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from site_cms import _request_json, _rest_url

TABLE = "careersite_recruiter_meetings"
TZ = ZoneInfo("Europe/Stockholm")
TYPES = {
    "interview": "Interview",
    "recruiter_screening": "Recruiter screening",
    "hiring_manager": "Hiring leader",
    "networking": "Professional introduction",
    "other": "Other",
}
ATTENDANCE = {
    "unverified": "Not verified",
    "attended": "Attended · confirmed",
    "cancelled": "Cancelled",
    "no_show": "Did not take place",
}
OUTCOMES = {
    "unknown": "Not recorded",
    "awaiting_feedback": "Awaiting feedback",
    "next_stage": "Next stage",
    "rejected": "Employer rejection",
    "offer": "Offer",
    "withdrawn": "Candidate withdrew",
    "closed": "Process closed",
}
FOLLOWUPS = {
    "unknown": "Not reviewed",
    "pending": "Follow-up pending",
    "sent": "Sent",
    "not_needed": "No follow-up needed",
}


def _now() -> datetime:
    return datetime.now(TZ)


def _fetch(token: str) -> list[dict]:
    rows = _request_json(
        "GET",
        _rest_url(
            f"{TABLE}?select=id,source_kind,title,employer,role_title,"
            "contact_name,meeting_type,stage,scheduled_date,starts_at,ends_at,"
            "attendance,outcome,follow_up_status,follow_up_due,follow_up_sent_at,"
            "calendar_url,evidence_note,calendar_captured_at,updated_at,opportunity_id"
            "&order=scheduled_date.desc,starts_at.desc.nullslast&limit=500"
        ),
        token=token,
    )
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def _local_start(row: dict) -> datetime | None:
    value = row.get("starts_at")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(TZ)
    except (ValueError, TypeError):
        return None


def _meeting_day(row: dict) -> date:
    return date.fromisoformat(str(row["scheduled_date"])[:10])


def _checkpoint_day(row: dict) -> date | None:
    """A follow-up date is a personal checkpoint, not a scheduled interview."""
    if row.get("follow_up_status") not in ("pending", "sent"):
        return None
    raw = row.get("follow_up_due")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except (TypeError, ValueError):
        return None


def _when(row: dict) -> str:
    stamp = _local_start(row)
    return stamp.strftime("%d %b %Y · %H:%M") if stamp else _meeting_day(row).strftime("%d %b %Y") + " · time TBC"


def _phase(row: dict, now: datetime) -> str:
    if row.get("attendance") == "cancelled":
        return "Cancelled"
    if row.get("attendance") == "no_show":
        return "Did not take place"
    if row.get("attendance") == "attended":
        return "Attended · verified"
    stamp = _local_start(row)
    if stamp:
        return "Upcoming" if stamp >= now else "Past · unverified"
    return "Upcoming · time TBC" if _meeting_day(row) >= now.date() else "Past · unverified"


def _upcoming(row: dict, now: datetime) -> bool:
    return _phase(row, now).startswith("Upcoming")


def _cohort(rows: list[dict], months: int) -> list[dict]:
    if months == 0:
        return rows
    cutoff = _now().date() - timedelta(days=months * 30)
    return [r for r in rows if _meeting_day(r) >= cutoff]


def _csv(rows: list[dict]) -> str:
    buf = StringIO()
    columns = [
        "scheduled_date", "employer", "role_title", "title", "contact_name",
        "meeting_type", "stage", "starts_at", "ends_at", "attendance",
        "outcome", "follow_up_status", "follow_up_due", "source_kind",
    ]
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _insights(rows: list[dict], now: datetime) -> None:
    next_week = [
        r for r in rows if _upcoming(r, now)
        and 0 <= (_meeting_day(r) - now.date()).days <= 7
    ]
    missed = [
        r for r in rows if not _upcoming(r, now)
        and r.get("attendance") == "unverified"
        and r.get("attendance") not in ("cancelled", "no_show")
    ]
    due = [
        r for r in rows if r.get("follow_up_status") == "pending"
        and r.get("follow_up_due") and date.fromisoformat(r["follow_up_due"]) <= now.date()
    ]
    firms = defaultdict(list)
    for item in rows:
        if item.get("employer"):
            firms[item["employer"]].append(item)
    repeated = sorted(((k, len(v)) for k, v in firms.items() if len(v) >= 2), key=lambda v: -v[1])

    st.subheader("What needs attention")
    if next_week:
        st.markdown(
            f"**{len(next_week)} meeting(s) in the next seven days.** "
            "Confirm joining details and interview preparation."
        )
    else:
        st.caption("No recorded recruiter meetings in the next seven days.")
    if due:
        st.warning(f"{len(due)} follow-up(s) are due or overdue based on entered deadlines.")
        for row in due[:5]:
            st.write(f"• {row['employer'] or row['title']} · due {row['follow_up_due']}")
    else:
        st.caption("No follow-ups with a recorded due date are outstanding.")
    if missed:
        st.info(
            f"{len(missed)} past calendar entry/entries still lack attendance verification. "
            "They are not counted as confirmed meetings."
        )
    if repeated:
        label = ", ".join(f"{k} ({v})" for k, v in repeated[:5])
        st.caption(f"Repeat interactions by employer: {label}. "
                   "Repeat invitations indicate contact depth, not a predicted offer.")
    st.caption("No calendar date, invitation, or silence is treated as a hiring decision.")


def _month_calendar(rows: list[dict], now: datetime) -> None:
    st.subheader("Recruiter calendar")
    st.markdown("""
<style>
div[class*="st-key-recruiter_calendar_event_"] {
    background-color: #f4dfca;
    border: 2px solid #b96732 !important;
    border-radius: 0.65rem;
}
div[class*="st-key-recruiter_calendar_event_"] p {
    color: #4b2d19 !important;
}
div[class*="st-key-recruiter_calendar_checkpoint_"] {
    background-color: #e1ebf4;
    border: 2px solid #547a9b !important;
    border-radius: 0.65rem;
}
div[class*="st-key-recruiter_calendar_checkpoint_"] p {
    color: #233d54 !important;
}
</style>
""", unsafe_allow_html=True)
    available = sorted(
        {(_meeting_day(r).year, _meeting_day(r).month) for r in rows}
        | {(d.year, d.month) for r in rows if (d := _checkpoint_day(r)) is not None}
        | {(now.year, now.month)}
    )
    labels = {f"{date(y, m, 1):%B %Y}": (y, m) for y, m in available}
    current = f"{now:%B %Y}"
    month_label = st.selectbox(
        "Calendar month", options=list(labels), index=list(labels).index(current)
        if current in labels else len(labels) - 1, key="meeting_calendar_month"
    )
    year, month = labels[month_label]
    first_weekday, count = monthrange(year, month)
    lookup = defaultdict(list)
    checkpoints = defaultdict(list)
    for item in rows:
        if item.get("attendance") == "cancelled":
            continue
        d = _meeting_day(item)
        if d.year == year and d.month == month:
            lookup[d.day].append(item)
        checkpoint = _checkpoint_day(item)
        if checkpoint and checkpoint.year == year and checkpoint.month == month:
            checkpoints[checkpoint.day].append(item)
    for week in range((first_weekday + count + 6) // 7):
        cols = st.columns(7, gap="small")
        for weekday, col in enumerate(cols):
            day = week * 7 + weekday - first_weekday + 1
            with col:
                if week == 0:
                    st.caption(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[weekday])
                if 1 <= day <= count:
                    events = lookup.get(day, [])
                    followups = checkpoints.get(day, [])
                    cell_kind = "event" if events else ("checkpoint" if followups else "empty")
                    with st.container(border=True, height=124,
                                      key=f"recruiter_calendar_{cell_kind}_{year}_{month}_{day}"):
                        st.markdown(f"**{day}**")
                        for item in events[:2]:
                            stamp = _local_start(item)
                            clock = stamp.strftime("%H:%M") if stamp else "TBC"
                            status = " · Attended" if item.get("attendance") == "attended" else ""
                            st.caption(f"{clock} · {item.get('employer') or item['title']}{status}")
                        for item in followups[:max(0, 2 - len(events))]:
                            name = item.get("employer") or item["title"]
                            label = ("Response checkpoint" if item.get("follow_up_status") == "sent"
                                     else "Follow-up due")
                            st.caption(f"{label} · {name}")
                        extras = len(events) + len(followups) - 2
                        if extras > 0:
                            st.caption(f"+{extras} more")
                else:
                    st.write(" ")
    st.caption(
        "Orange = meeting date; blue = follow-up or response checkpoint, not a "
        "booked meeting. Dates and times use Europe/Stockholm."
    )

def _charts(rows: list[dict], now: datetime) -> None:
    st.subheader("Interaction patterns")
    past = [r for r in rows if _meeting_day(r) <= now.date()
            and r.get("attendance") not in ("cancelled", "no_show")]
    counts = Counter(_meeting_day(r).strftime("%Y-%m") for r in past)
    if counts:
        data = [{"Month": m, "Calendar entries": counts[m]} for m in sorted(counts)]
        chart = alt.Chart(alt.Data(values=data)).mark_bar(color="#c56f3d").encode(
            x=alt.X("Month:N", sort=sorted(counts), title=None),
            y=alt.Y("Calendar entries:Q", title="Entries", axis=alt.Axis(tickMinStep=1)),
            tooltip=["Month:N", "Calendar entries:Q"],
        ).properties(height=205)
        st.altair_chart(chart, use_container_width=True)
    st.caption(
        "Monthly counts show documented calendar/interview records, not confirmed attendance "
        "or application conversion. Coverage starts with the imported source history."
    )

    employer_counts = Counter(r.get("employer") or "Unspecified" for r in rows)
    top = [{"Employer": firm, "Entries": count} for firm, count in
           employer_counts.most_common(8)]
    if top:
        chart = alt.Chart(alt.Data(values=top)).mark_bar(color="#60758a").encode(
            x=alt.X("Entries:Q", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Employer:N", sort="-x", title=None),
            tooltip=["Employer:N", "Entries:Q"],
        ).properties(height=max(175, len(top) * 31))
        st.altair_chart(chart, use_container_width=True)


def _agenda(rows: list[dict], now: datetime) -> None:
    st.subheader("Upcoming conversations")
    next_rows = sorted((r for r in rows if _upcoming(r, now)),
                       key=lambda r: (_meeting_day(r), _local_start(r) or now.replace(hour=0)))
    if not next_rows:
        st.info("No future recruiting conversations have been recorded.")
        return
    for row in next_rows:
        with st.container(border=True):
            a, b = st.columns([4, 1.1])
            with a:
                st.markdown(f"**{row.get('employer') or row['title']}** · {_when(row)}")
                st.caption(
                    f"{row.get('role_title') or row['title']} · "
                    f"{TYPES.get(row.get('meeting_type'), 'Meeting')}"
                    + (f" · Round {row['stage']}" if row.get("stage") else "")
                )
                if row.get("contact_name"):
                    st.caption(f"Contact: {row['contact_name']}")
                if not row.get("starts_at"):
                    st.caption("Exact start time has not been confirmed from a calendar event.")
            with b:
                url = str(row.get("calendar_url") or "")
                if url.startswith(("https://", "http://")):
                    st.link_button("Open invitation", url, use_container_width=True)
                if st.button("Review", key=f"edit-meeting-{row['id']}", use_container_width=True):
                    st.session_state["recruiter_selected_meeting"] = int(row["id"])
                    st.rerun()


def _history(rows: list[dict], now: datetime) -> None:
    st.subheader("Meeting history and evidence")
    c1, c2 = st.columns([2.2, 1])
    with c1:
        query_text = st.text_input(
            "Find an employer, contact or role", placeholder="Search meeting history",
            key="meeting_search",
        ).lower().strip()
    with c2:
        status_filter = st.selectbox(
            "Record status", ["All records", "Confirmed attended", "Past not verified", "Upcoming"],
            key="meeting_status_filter",
        )
    filtered = []
    for row in rows:
        if query_text and query_text not in " ".join(
            str(row.get(x) or "") for x in
            ("title", "employer", "role_title", "contact_name")
        ).lower():
            continue
        phase = _phase(row, now)
        if status_filter == "Confirmed attended" and row.get("attendance") != "attended":
            continue
        if status_filter == "Past not verified" and phase != "Past · unverified":
            continue
        if status_filter == "Upcoming" and not phase.startswith("Upcoming"):
            continue
        filtered.append(row)
    if filtered:
        formatted = [{
            "When (Stockholm)": _when(r),
            "Employer": r.get("employer") or "—",
            "Role": r.get("role_title") or r["title"],
            "Interaction": TYPES.get(r.get("meeting_type"), "Other"),
            "Round": r.get("stage") or "—",
            "Evidence status": _phase(r, now),
            "Follow-up": FOLLOWUPS.get(r.get("follow_up_status"), "Unknown"),
            "Outcome": OUTCOMES.get(r.get("outcome"), "Unknown"),
            "Source": r.get("source_kind", "—"),
        } for r in filtered]
        st.dataframe(formatted, hide_index=True, use_container_width=True)
        st.download_button(
            "Export selected records (CSV)", data=_csv(filtered),
            file_name="private_recruiter_meetings.csv", mime="text/csv",
            key="download_meeting_records",
        )
    else:
        st.info("No meeting records match these filters.")


def _write(token: str, payload: dict, selected_id: int | None) -> None:
    if selected_id is None:
        _request_json("POST", _rest_url(TABLE), token=token, payload=payload,
                      prefer="return=minimal")
    else:
        _request_json(
            "PATCH",
            _rest_url(f"{TABLE}?id=eq.{selected_id}"),
            token=token, payload={**payload, "updated_at": datetime.now(timezone.utc).isoformat()},
            prefer="return=minimal",
        )


def _editor(rows: list[dict], token: str, now: datetime,
            opportunities: list[dict] | None = None) -> None:
    with st.expander("Review a meeting, record the outcome, or add a missing interaction",
                     expanded=bool(st.session_state.get("recruiter_selected_meeting"))):
        choices = {"Add a new meeting": None}
        choices.update({
            f"{_when(r)} — {r.get('employer') or r['title']} (#{r['id']})": int(r["id"])
            for r in rows
        })
        requested = st.session_state.get("recruiter_selected_meeting")
        matching = next((label for label, item_id in choices.items() if item_id == requested),
                        "Add a new meeting")
        selected = st.selectbox(
            "Select a record", list(choices), index=list(choices).index(matching),
            key="recruiter_editor_picker",
        )
        identifier = choices[selected]
        original = next((r for r in rows if r["id"] == identifier), None)
        original = original or {}
        with st.form("recruiter_meeting_form"):
            a, b = st.columns(2)
            with a:
                employer = st.text_input("Employer", value=original.get("employer") or "")
                role = st.text_input("Role / mandate", value=original.get("role_title") or "")
                title = st.text_input("Meeting title", value=original.get("title") or "")
                contact = st.text_input("Recruiter / interviewer", value=original.get("contact_name") or "")
                when = st.date_input(
                    "Meeting date", value=_meeting_day(original) if original else now.date()
                )
                old_local = _local_start(original)
                has_time = st.checkbox(
                    "Verified start time", value=old_local is not None
                )
                at_time = st.time_input(
                    "Start time (Stockholm)", value=old_local.time().replace(tzinfo=None)
                    if old_local else time(11, 0), disabled=not has_time
                )
                choices = {None: "Unlinked / not a hiring process"}
                choices.update({o["id"]: f"{o['employer']} · {o['role_title']} (#{o['id']})"
                                for o in (opportunities or [])})
                linked_options = list(choices)
                original_process = original.get("opportunity_id")
                linked_id = st.selectbox(
                    "Hiring process / vacancy", options=linked_options,
                    index=linked_options.index(original_process)
                    if original_process in linked_options else 0,
                    format_func=lambda v: choices[v],
                    help="Link interviews to the same exact vacancy. Different roles at the same employer must stay separate.",
                )
                meeting_type = st.selectbox(
                    "Interaction type", list(TYPES),
                    format_func=lambda v: TYPES[v],
                    index=list(TYPES).index(original.get("meeting_type", "interview"))
                    if original.get("meeting_type") in TYPES else 0,
                )
                stage = st.number_input(
                    "Round / stage (0 = unknown)", min_value=0, max_value=9,
                    value=int(original.get("stage") or 0), step=1,
                )
            with b:
                attendance = st.selectbox(
                    "Attendance verification", list(ATTENDANCE),
                    format_func=lambda v: ATTENDANCE[v],
                    index=list(ATTENDANCE).index(original.get("attendance", "unverified")),
                )
                outcome = st.selectbox(
                    "Recorded hiring outcome", list(OUTCOMES),
                    format_func=lambda v: OUTCOMES[v],
                    index=list(OUTCOMES).index(original.get("outcome", "unknown")),
                )
                followup = st.selectbox(
                    "Follow-up status", list(FOLLOWUPS),
                    format_func=lambda v: FOLLOWUPS[v],
                    index=list(FOLLOWUPS).index(original.get("follow_up_status", "unknown")),
                )
                due_flag = st.checkbox(
                    "A follow-up due date is known", value=bool(original.get("follow_up_due"))
                )
                due = st.date_input(
                    "Follow-up due", value=date.fromisoformat(original["follow_up_due"])
                    if original.get("follow_up_due") else now.date(),
                    disabled=not due_flag,
                )
                note = st.text_area(
                    "Evidence / interview notes", value=original.get("evidence_note") or "",
                    height=145,
                    help="Record concrete feedback, not assumptions about employer intent.",
                )
                url = st.text_input("Calendar invitation URL", value=original.get("calendar_url") or "")
            submitted = st.form_submit_button(
                "Save meeting record", type="primary", use_container_width=True
            )
        if submitted:
            if not title.strip() or not employer.strip():
                st.error("Employer and meeting title are required.")
            else:
                start = datetime.combine(when, at_time, TZ).astimezone(timezone.utc) \
                    if has_time else None
                # Preserve the original duration when editing an existing calendar event.
                old_start = _local_start(original)
                old_end = original.get("ends_at")
                duration = None
                if old_start and old_end:
                    end_dt = datetime.fromisoformat(str(old_end).replace("Z", "+00:00"))
                    duration = end_dt - old_start.astimezone(timezone.utc)
                payload = {
                    "employer": employer.strip(), "role_title": role.strip(),
                    "title": title.strip(), "contact_name": contact.strip(),
                    "meeting_type": meeting_type, "stage": int(stage) or None,
                    "opportunity_id": linked_id,
                    "scheduled_date": when.isoformat(),
                    "starts_at": start.isoformat() if start else None,
                    "ends_at": (start + duration).isoformat() if start and duration else None,
                    "attendance": attendance, "outcome": outcome,
                    "follow_up_status": followup,
                    "follow_up_due": due.isoformat() if due_flag else None,
                    "follow_up_sent_at": original.get("follow_up_sent_at"),
                    "calendar_url": url.strip() or None,
                    "evidence_note": note.strip(),
                }
                if identifier is None:
                    payload["source_kind"] = "manual"
                try:
                    _write(token, payload, identifier)
                except (RuntimeError, ValueError) as exc:
                    st.error(f"Could not save the meeting: {exc}")
                else:
                    st.session_state.pop("recruiter_selected_meeting", None)
                    st.success("Meeting record saved.")
                    st.rerun()


def render_recruiter_meetings(session: dict) -> None:
    """Render only after the unified Admin has validated the owner session."""
    token = str(session["access_token"])
    now = _now()
    st.title("Recruiter interactions")
    st.caption(
        "History, forthcoming conversations and recruiting follow-through in one private view. "
        "Timezone: Europe/Stockholm."
    )
    try:
        all_rows = _fetch(token)
        from page_recruiting_journeys import fetch_opportunities
        opportunities = fetch_opportunities(token)
    except (RuntimeError, ValueError) as exc:
        st.error(f"Meeting data is unavailable: {exc}")
        return

    changes = [
        str(x.get("updated_at"))
        for x in [*all_rows, *opportunities] if x.get("updated_at")
    ]
    if changes:
        try:
            last = max(
                datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(TZ)
                for s in changes
            )
            st.caption(
                f"Saved records last updated {last:%d %b %Y at %H:%M} Stockholm time. "
                "These records are read when this page reloads; Outlook and Gmail are "
                "not continuously synchronized."
            )
        except (TypeError, ValueError):
            pass
    if st.button("Reload latest saved records", key="recruiter_reload_records"):
        st.rerun()

    if not all_rows:
        st.info("No recruiter meetings have been captured. Use the editor below to add one.")
        from page_recruiting_journeys import render_role_journeys
        render_role_journeys(token, [], now, opportunities)
        _editor([], token, now, opportunities)
        return

    c1, c2 = st.columns([2.2, 1])
    with c1:
        months = st.selectbox(
            "Reporting period", [0, 3, 6, 12],
            format_func=lambda x: "All recorded history" if x == 0 else f"Last {x} months + future",
            key="recruiter_meetings_period",
        )
    with c2:
        st.caption("Evidence scope")
        st.caption("Calendar snapshot + hiring records")
    rows = _cohort(all_rows, months)
    future = [r for r in rows if _upcoming(r, now)]
    confirmed = [r for r in rows if r.get("attendance") == "attended"]
    past_unverified = [r for r in rows if _phase(r, now) == "Past · unverified"]
    orgs = len({(r.get("employer") or "").strip().lower() for r in rows if r.get("employer")})
    metrics = st.columns(4)
    metrics[0].metric("Recorded interactions", len(rows))
    metrics[1].metric("Upcoming", len(future))
    metrics[2].metric("Confirmed attended", len(confirmed),
                      help="Requires explicit attendance evidence, not just a past calendar invite.")
    metrics[3].metric("Employers engaged", orgs,
                      help="Distinct named organizations with sourced interaction records.")
    st.caption(
        f"{len(past_unverified)} past records require attendance review. "
        "Calendar invitations are not proof of attendance; interactions are not job applications."
    )
    imported = [r["calendar_captured_at"] for r in all_rows if r.get("calendar_captured_at")]
    if imported:
        stamp = max(imported)
        st.caption(
            "Outlook calendar snapshot captured " + str(stamp)[:16].replace("T", " ") +
            " UTC. This page does not have a live calendar connector: new or changed invitations "
            "must be imported or entered, and statuses checked against recruiting correspondence."
        )

    role_tab, calendar_tab = st.tabs(["Role journeys", "Calendar & interaction history"])
    with role_tab:
        from page_recruiting_journeys import render_role_journeys
        render_role_journeys(token, all_rows, now, opportunities)
    with calendar_tab:
        _agenda(rows, now)
        _insights(rows, now)
        _month_calendar(rows, now)
        _charts(rows, now)
        _history(rows, now)
        _editor(all_rows, token, now, opportunities)
