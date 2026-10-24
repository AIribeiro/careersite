"""Private, evidence-led hiring follow-up decision desk.

Advisory only: Supabase is the source of truth. No mailbox synchronization or
outbound email occurs when this page is opened.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import re

import streamlit as st
from site_cms import _request_json, _rest_url

VIEW = "careersite_followup_queue_v1"
STATE = "careersite_followup_actions"
ACTION_NAMES = {
    "follow_up_now": "Follow up now",
    "upcoming": "Upcoming",
    "wait": "Wait",
    "hold": "Hold / review",
}
ACTION_ORDER = {"follow_up_now": 0, "upcoming": 1, "wait": 2, "hold": 3}
EXCLUDED_OUTCOMES = {"rejected", "cancelled", "canceled", "withdrawn"}


def _is_eligible(row: dict) -> bool:
    """Track every opportunity unless its outcome explicitly excludes it."""
    return str(row.get("outcome") or "unknown").strip().lower() not in EXCLUDED_OUTCOMES
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _fetch(token: str) -> list[dict]:
    result = _request_json(
        "GET",
        _rest_url(f"{VIEW}?select=*&order=opportunity_id.asc&limit=500"),
        token=token,
    )
    if not isinstance(result, list):
        raise RuntimeError("Follow-up queue did not return a list.")
    return [r for r in result if isinstance(r, dict)]


def _upsert(token: str, identifier: int, payload: dict) -> None:
    body = {"opportunity_id": identifier, **payload}
    _request_json(
        "POST", _rest_url(f"{STATE}?on_conflict=opportunity_id"),
        token=token, payload=body, prefer="resolution=merge-duplicates,return=minimal",
    )


def _day(value: object) -> str:
    if not value:
        return "—"
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d %b %Y")
    except ValueError:
        return str(value)[:10]


def _num(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _dates(row: dict) -> str:
    if row.get("next_interview_date"):
        return "Next interview " + _day(row["next_interview_date"])
    if row.get("action") in ("upcoming", "follow_up_now"):
        return "Recommended checkpoint " + _day(row.get("due_date"))
    if row.get("due_date"):
        return "Review checkpoint " + _day(row["due_date"]) + " (not a send recommendation)"
    return "No verified follow-up due date"


def _editor(row: dict, token: str) -> None:
    identifier = int(row["opportunity_id"])
    with st.expander("Contact and evidence controls", expanded=False):
        with st.form(f"followup_contact_{identifier}"):
            one, two = st.columns(2)
            with one:
                recipient_name = st.text_input(
                    "Recipient name", value=row.get("recipient_name") or "",
                    key=f"fu_name_{identifier}",
                )
                recipient_email = st.text_input(
                    "Verified recipient email", value=row.get("recipient_email") or "",
                    key=f"fu_email_{identifier}",
                )
                recipient_role = st.selectbox(
                    "Recipient", ["recruiter", "hiring_manager", "other"],
                    index=["recruiter", "hiring_manager", "other"].index(
                        row.get("recipient_role") or "recruiter"
                    ) if (row.get("recipient_role") or "recruiter") in
                    ("recruiter", "hiring_manager", "other") else 0,
                    key=f"fu_kind_{identifier}",
                )
            with two:
                source = st.text_input(
                    "Where was this contact verified?",
                    value=row.get("email_source") or "",
                    key=f"fu_src_{identifier}",
                )
                expected = st.date_input(
                    "Employer-promised reply deadline (optional)",
                    value=date.fromisoformat(row["expected_reply_by"])
                    if row.get("expected_reply_by") else None,
                    format="DD/MM/YYYY",
                    key=f"fu_expected_{identifier}",
                )
                expected_source = st.text_input(
                    "Evidence for promised deadline",
                    value=row.get("expected_reply_evidence") or "",
                    key=f"fu_promise_{identifier}",
                )
            context = st.text_input(
                "Optional verified sentence for the follow-up draft",
                value=row.get("context_line") or "", key=f"fu_ctx_{identifier}",
                help="One grounded sentence only. Do not invent outcomes or commitments.",
            )
            st.caption(
                "The source check reflects a deliberate review of Outlook/Gmail; "
                "saving contact details here does not independently check your mail."
            )
            checked = st.checkbox(
                "I checked current employer correspondence before saving",
                value=False, key=f"fu_checked_{identifier}"
            )
            save = st.form_submit_button("Save verified details")
        if save:
            if recipient_email.strip() and not EMAIL_RE.fullmatch(recipient_email.strip()):
                st.error("Please enter a valid recipient email address.")
                return
            if expected and not expected_source.strip():
                st.error("Record the employer source for a promised response date.")
                return
            payload = {
                "recipient_name": recipient_name.strip() or None,
                "recipient_email": recipient_email.strip() or None,
                "recipient_role": recipient_role,
                "email_source": source.strip() or None,
                "expected_reply_by": expected.isoformat() if expected else None,
                "expected_reply_evidence": expected_source.strip() or None,
                "context_line": context.strip() or None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if checked:
                payload["source_checked_at"] = datetime.now(timezone.utc).isoformat()
            try:
                _upsert(token, identifier, payload)
            except RuntimeError as exc:
                st.error(f"Could not save follow-up details: {exc}")
            else:
                st.success("Contact and follow-up parameters saved.")
                st.rerun()


def _draft(row: dict, token: str) -> None:
    identifier = int(row["opportunity_id"])
    st.markdown(f"**To:** {row.get('recipient_name') or 'Unconfirmed'} "
                f"({row.get('recipient_email') or 'email not verified'})")
    st.markdown(f"**Subject:** {row.get('email_subject') or ''}")
    st.code(row.get("email_body") or "", language=None, wrap_lines=True)
    st.caption("Copy the text and send it manually in the existing email thread where possible.")
    if row.get("verify_correspondence_first"):
        st.warning(
            "The last mailbox check is more than seven days old (or missing). "
            "Recheck received and sent messages before using this draft."
        )
    with st.form(f"followup_sent_{identifier}"):
        confirm = st.checkbox(
            "I have already sent this status follow-up myself (not just copied it).",
            value=False,
        )
        submitted = st.form_submit_button(
            "Record follow-up as sent", disabled=bool(row.get("verify_correspondence_first")),
        )
    if submitted:
        if not confirm:
            st.error("Please confirm that you already sent the email.")
            return
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            _upsert(token, identifier, {
                "last_followup_sent_at": timestamp,
                "last_candidate_message_at": timestamp,
                "followups_sent_count": _num(row.get("followups_sent_count")) + 1,
                "updated_at": timestamp,
            })
        except RuntimeError as exc:
            st.error(f"Could not record this sent follow-up: {exc}")
        else:
            st.success("Sent follow-up recorded. The next checkpoint has been recalculated.")
            st.rerun()


def render_followup_manager(session: dict) -> None:
    token = str(session["access_token"])
    st.title("Live hiring follow-up manager")
    st.caption(
        "Owner-only · all applications except rejected, cancelled or withdrawn · "
        "Swedish business-day timing · manual email delivery. "
        "Snapshot-driven: opening this page does not sync Outlook or Gmail."
    )
    if st.button("Refresh decisions", key="followup_refresh"):
        st.rerun()
    try:
        records = _fetch(token)
    except (RuntimeError, ValueError) as exc:
        st.error(f"Follow-up manager is unavailable: {exc}")
        return
    tracked = sorted(
        [r for r in records if _is_eligible(r)],
        key=lambda r: (ACTION_ORDER.get(r.get("action"), 9), r.get("due_date") or "9999-12-31"),
    )
    counts = {key: sum(r.get("action") == key for r in tracked) for key in ACTION_NAMES}
    cols = st.columns(4)
    for col, (action, label) in zip(cols, ACTION_NAMES.items()):
        col.metric(label, counts[action])

    confirmed = sum(str(r.get("outcome") or "").strip().lower() == "in_progress" for r in tracked)
    unresolved = len(tracked) - confirmed
    app_only = sum(not r.get("interview_date") for r in tracked)
    st.caption(
        f"{len(tracked)} tracked applications · {confirmed} confirmed in progress · "
        f"{unresolved} unconfirmed/other outcomes · {app_only} without a verified completed interview."
    )
    market = next((r for r in tracked if r.get("market_snapshot_date")), None)
    if market:
        st.caption(
            f"Market adjustment: +{market.get('market_lag_days', 0)} business day(s) "
            f"from saved {market['market_snapshot_date']} hiring-delay pressure. "
            "This does not predict individual recruiter behavior."
        )
    st.info(
        "Employer commitments outrank default windows. Already-sent thank-yous "
        "do not count as chasing emails. Unconfirmed applications remain in this manager; "
        "an unknown status does not establish that the vacancy is still open. "
        "A missing recipient or stale evidence requires review, not an automatic email."
    )
    if not tracked:
        st.warning("No non-rejected, non-cancelled, non-withdrawn applications are recorded.")
        return
    show = st.segmented_control(
        "Process filter", ["All tracked", "Action required", "Waiting", "Needs review", "Applications only"],
        default="All tracked", key="followup_filter", width="stretch"
    ) or "All tracked"
    filtered = [
        r for r in tracked
        if show == "All tracked"
        or (show == "Action required" and r.get("action") == "follow_up_now")
        or (show == "Waiting" and r.get("action") in ("upcoming", "wait"))
        or (show == "Needs review" and r.get("action") == "hold")
        or (show == "Applications only" and not r.get("interview_date"))
    ]
    for row in filtered:
        status = ACTION_NAMES.get(row.get("action"), "Check")
        title = (f"{row['employer']} · {row['role_title']} — {status}")
        with st.container(border=True):
            st.markdown("**" + title + "**")
            outcome = str(row.get("outcome") or "unknown").strip().lower()
            if outcome == "unknown":
                st.caption("Outcome unconfirmed · requires evidence check; not assumed rejected or still hiring")
            elif outcome not in {"in_progress"}:
                st.caption("Saved outcome: " + outcome + " · review any outstanding administrative steps")
            st.caption(
                f"{_dates(row)} · {row.get('decision_reason') or 'No reason saved'} "
                f"· Process ID {row['opportunity_id']}"
            )
            if row.get("interview_date"):
                st.caption(
                    f"Last verified interview: {_day(row['interview_date'])} "
                    f"· Round {row.get('stage') or '?'}"
                )
            elif row.get("application_date"):
                st.caption("Application: " + _day(row["application_date"]) + " · no completed interview recorded")
            else:
                st.caption("Application/meeting date not fully verified; check source records")
            if row.get("source_checked_at"):
                st.caption("Correspondence checked: " + _day(row["source_checked_at"]))
            if row.get("action") == "follow_up_now":
                if row.get("verify_correspondence_first"):
                    st.warning("Draft requires an updated mailbox check.")
                else:
                    _draft(row, token)
            elif row.get("action") == "upcoming":
                st.caption("Email draft becomes available when the calculated date is due.")
            elif row.get("action") == "wait":
                st.caption("Do not send a process-status request before the scheduled interview.")
            else:
                st.caption("Review the application status, find a verified recipient, or confirm old interview evidence before sending.")
            _editor(row, token)
    st.divider()
    st.caption(
        "Method: 5 workdays after advanced interviews; 7 after first interviews; "
        "10 after a dated application; a verified recipient is required to send. A fresh elevated "
        "market-delay indicator adds at most one workday. An explicit employer "
        "reply date uses a three-workday grace period. Recent outgoing messages "
        "and repeat follow-ups impose a cooldown. Weekends and curated Swedish "
        "holidays are excluded. Unknown-status applications stay visible, but stale and "
        "unverified cases are held for review. These dates are advisory, not employer promises."
    )
