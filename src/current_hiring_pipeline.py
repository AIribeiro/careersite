"""Owner-only current recruiting status, independent of the legacy forecast snapshot.

The source tables distinguish formal applications from exploratory employer access.
No networking interaction is promoted to an interview, vacancy or offer.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

from site_cms import _request_json, _rest_url


def fetch_current_pipeline(token: str) -> dict:
    """One owner-gated RPC: private priority/map tables are never read via REST."""
    if not token:
        raise ValueError("Owner access required")
    response = _request_json(
        "POST",
        _rest_url("rpc/careersite_owner_current_hiring_pipeline_v1"),
        token=token,
        payload={},
        timeout=20,
    )
    if not isinstance(response, dict) or not all(
        isinstance(response.get(key), list)
        for key in ("opportunities", "priorities", "statuses", "strategic", "unreviewed_active", "sync_runs")
    ):
        raise RuntimeError("Current owner-only hiring summary is unavailable")
    return response


STAGE_LABELS = {
    "video_assessment_completed": "Video assessment completed",
    "intro_meeting_scheduled": "Introduction scheduled · not yet held",
    "ats_received": "Application received",
    "applied_no_interview": "Application · no interview confirmed",
    "qualified_recruiter_client_status_unknown": "Recruiter qualified · client decision unverified",
    "representation_authorized_client_submission_unknown": "Representation authorized · submission unverified",
    "exploratory_recruiter_outreach": "Exploratory recruiter outreach",
    "applied_geography_mismatch": "Application · location constraint",
    "application_dormant": "Application · no recent response",
    "application_eligibility_unknown": "Application · eligibility unverified",
}


def current_rows(sources: dict) -> list[dict]:
    """Select the newest review per exact requisition; exclude dormant and closed."""
    opportunities = {str(row.get("id")): row for row in sources["opportunities"]}
    statuses = {}
    for item in sorted(sources["statuses"], key=lambda x: str(x.get("updated_at") or ""), reverse=True):
        if item.get("source_type") == "managed":
            statuses.setdefault(str(item.get("source_ref")), item)
    seen = set()
    rows = []
    # The RPC is a current snapshot with potential historical reviews.
    # Resolve each requisition against its latest review, not row-return order.
    latest_first = sorted(
        sources["priorities"],
        key=lambda item: (
            str(item.get("reviewed_at") or item.get("reviewed_on") or ""),
            -int(item.get("rank_position") or 9999),
        ),
        reverse=True,
    )
    for review in latest_first:
        key = str(review.get("opportunity_id"))
        if key in seen:
            continue
        seen.add(key)
        op = opportunities.get(key)
        if not op or str(op.get("outcome") or "").lower() in {
            "rejected", "closed", "withdrawn", "offer_accepted", "hired"
        }:
            continue
        band = str(review.get("priority_band") or "")
        if band not in {"P1", "P2", "P3"} or review.get("rank_position") is None:
            continue
        status = statuses.get(key, {})
        if str(status.get("status") or "").lower() in {
            "ignored", "rejected", "withdrawn", "closed"
        }:
            continue
        stage_key = str(review.get("pipeline_state") or "")
        stage = STAGE_LABELS.get(stage_key, stage_key.replace("_", " ").capitalize())
        if status.get("status") == "recruiter_replied" and stage_key in {
            "ats_received", "applied_no_interview"
        }:
            stage = "Recruiter replied · no interview confirmed"
        if status.get("status") == "recruiter_replied" and stage_key == "video_assessment_completed":
            stage = "Video assessment completed · recruiter responded"
        review_timestamp = _parse_timestamp(review.get("reviewed_at") or review.get("reviewed_on"))
        status_timestamp = _parse_timestamp(status.get("updated_at"))
        review_lags_response = bool(
            review_timestamp and status_timestamp and status_timestamp > review_timestamp
        )
        rows.append({
            "rank_needs_review": review_lags_response,
            "reviewed_at": review.get("reviewed_at") or review.get("reviewed_on"),
            "status_updated_at": status.get("updated_at"),
            "id": key,
            "employer": str(op.get("employer") or ""),
            "role": str(op.get("role_title") or ""),
            "band": band,
            "rank": int(review["rank_position"]),
            "stage": stage,
            "evidence": str(status.get("status_note") or review.get("evidence_note") or ""),
            "event_date": str(status.get("status_on") or op.get("application_date") or ""),
            "next_action": str(review.get("next_action") or ""),
        })
    return sorted(rows, key=lambda row: (
        {"P1": 0, "P2": 1, "P3": 2}.get(row["band"], 3),
        row["rank"],
    ))


def strategic_rows(sources: dict) -> list[dict]:
    """Real executive contact with no verified vacancy stays outside hiring counts."""
    return [
        row for row in sources["strategic"]
        if row.get("access_status") == "direct_executive_conversation"
        and row.get("hiring_signal") == "exploratory_executive_interest_no_open_role"
    ]


_STYLE = """
<style>
.current-pipeline{display:grid;gap:8px;margin:12px 0 16px}
.current-pipeline__row{display:grid;grid-template-columns:1.4fr 1.2fr 1.7fr;gap:14px;
padding:13px 15px;border:1px solid rgba(120,136,155,.22);border-radius:12px;
background:rgba(130,150,170,.035);align-items:start}
.current-pipeline__name{font-weight:750;font-size:.91rem;line-height:1.25}
.current-pipeline__role{font-size:.78rem;opacity:.8;margin-top:3px}
.current-pipeline__stage{font-weight:650;font-size:.8rem;line-height:1.35}
.current-pipeline__meta{font-size:.72rem;opacity:.72;margin-top:5px}
.current-pipeline__evidence{font-size:.76rem;opacity:.85;line-height:1.42}
.current-pipeline__next{font-size:.75rem;line-height:1.4;margin-top:6px;opacity:.8}
.current-pipeline__tag{font-size:.69rem;font-weight:700;letter-spacing:.04em;opacity:.75}
@media(max-width:760px){
.current-pipeline__row{grid-template-columns:minmax(0,1fr);gap:8px;padding:12px}
.current-pipeline__evidence{max-width:100%;overflow-wrap:anywhere}
}
</style>
"""


def _parse_timestamp(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (ValueError, TypeError):
        return None


def _stockholm_time(value: object) -> str:
    dt = _parse_timestamp(value)
    if not dt:
        return "Unknown"
    return dt.astimezone(ZoneInfo("Europe/Stockholm")).strftime("%d %b %Y %H:%M %Z")


def freshness_status(sources: dict, now: datetime | None = None) -> dict:
    """Database reads, changed records and external checks are separate clocks."""
    now = now or datetime.now(timezone.utc)
    snapshots = sources.get("source_watermarks") or {}
    latest = max(
        (dt for dt in (_parse_timestamp(x) for x in snapshots.values()) if dt),
        default=None,
    )
    checks = [x for x in (sources.get("sync_runs") or [])
              if x.get("source_name") in ("gmail", "outlook")]
    last_mailbox_check = max(
        (t for t in (_parse_timestamp(x.get("checked_at")) for x in checks) if t),
        default=None,
    )
    both_checked = {x.get("source_name") for x in checks
                    if x.get("check_status") == "checked"
                    and (_parse_timestamp(x.get("checked_at")) or datetime.min.replace(tzinfo=timezone.utc))
                    >= now - timedelta(hours=36)}
    return {
        "generated_at": sources.get("generated_at"),
        "latest_source_change": latest,
        "last_mailbox_check": last_mailbox_check,
        "source_check_stale": both_checked != {"gmail", "outlook"},
        "source_check_partial": any(x.get("check_status") != "checked" for x in checks),
        "unreviewed": len(sources.get("unreviewed_active") or []),
    }


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _short(value: object, size: int = 185) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= size else text[:size - 1].rsplit(" ", 1)[0] + "…"


def _row_html(row: dict) -> str:
    when = _safe(row.get("event_date"))
    meta = ("Recorded " + when) if when else "Date unverified"
    if row.get("rank_needs_review"):
        meta += " · Priority review older than recruiter update"
    return (
        '<div class="current-pipeline__row">'
        '<div><div class="current-pipeline__name">' + _safe(row["employer"]) +
        '</div><div class="current-pipeline__role">' + _safe(row["role"]) +
        '</div><div class="current-pipeline__meta">' + _safe(row["band"]) + " priority</div></div>"
        '<div><div class="current-pipeline__stage">' + _safe(row["stage"]) +
        '</div><div class="current-pipeline__meta">' + meta + '</div></div>'
        '<div><div class="current-pipeline__evidence">' + _safe(_short(row["evidence"])) +
        '</div><div class="current-pipeline__next"><strong>Next:</strong> ' +
        _safe(_short(row["next_action"], 170)) + '</div></div></div>'
    )


def _render_rows(rows: list[dict]) -> None:
    if rows:
        st.markdown(
            _STYLE + '<div class="current-pipeline">' +
            "".join(_row_html(row) for row in rows) + '</div>',
            unsafe_allow_html=True,
        )


def render_current_pipeline(sources: dict) -> bool:
    """Return True when at least one current pipeline or strategic row exists."""
    rows = current_rows(sources)
    strategic = strategic_rows(sources)
    st.subheader("Current opportunities and conversations")
    st.caption(
        "Owner-only Supabase records. Status is based on stored evidence; "
        "P1/P2/P3 is a human priority assessment, not an offer probability. "
        "Executive networking is not an application or interview."
    )
    health = freshness_status(sources)
    st.caption(
        "Database read: " + _stockholm_time(health["generated_at"]) +
        " · Last stored recruiting change: " +
        _stockholm_time(health["latest_source_change"])
    )
    if health["last_mailbox_check"]:
        st.caption("Last recorded mailbox check: " +
                   _stockholm_time(health["last_mailbox_check"]) +
                   " · Database refresh does not scan new emails.")
    else:
        st.caption("Mailbox verification: no recorded check yet.")
    if health["source_check_stale"]:
        st.warning("Mailbox verification is missing, partial or older than 36 hours. "
                   "Recorded statuses may be accurate, but are not confirmed current.")
    elif health["source_check_partial"]:
        st.warning("A mailbox check was partial or failed; inspect the source-sync record.")

    if strategic:
        st.markdown("**Strategic conversations · no advertised vacancy confirmed**")
        for entry in strategic:
            st.markdown(
                '<div class="current-pipeline__row" style="display:block">'
                '<div class="current-pipeline__name">' + _safe(entry.get("employer")) +
                ' · exploratory executive discussion</div>'
                '<div class="current-pipeline__meta">Contact: ' +
                _safe(entry.get("contact_name") or "Unverified") +
                ' · Conversation proposed, booking not verified</div>'
                '<div class="current-pipeline__evidence" style="margin-top:8px">' +
                _safe(_short(entry.get("activity_status"), 290)) + '</div>'
                '<div class="current-pipeline__next"><strong>Next:</strong> ' +
                _safe(_short(entry.get("next_action"), 230)) +
                '</div></div>',
                unsafe_allow_html=True,
            )
    p1 = [row for row in rows if row["band"] == "P1"]
    if p1:
        st.markdown(f"**Active priorities · {len(p1)} P1 processes**")
        _render_rows(p1)
    other = [row for row in rows if row["band"] in {"P2", "P3"}]
    if other:
        with st.expander(f"Other monitored applications · {len(other)}"):
            _render_rows(other)
    unreviewed = sources.get("unreviewed_active") or []
    if unreviewed:
        with st.expander(f"New opportunities awaiting priority assessment · {len(unreviewed)}"):
            for item in unreviewed:
                st.markdown("**" + _safe(item.get("employer")) + "** · " +
                            _safe(item.get("role_title")) +
                            " — recorded active; no confirmed interview or priority rank.")
    needs_review = [row for row in rows if row.get("rank_needs_review")]
    if needs_review:
        st.caption(
            f"{len(needs_review)} priority assessment(s) predate newer status evidence; "
            "stages reflect new status, but priority ranks need review."
        )
    if not rows and not strategic and not unreviewed:
        st.info("No recent, evidence-backed active opportunity was found in the current review.")
    return bool(rows or strategic or unreviewed)



@st.fragment(run_every="5m")
def render_current_pipeline_auto(token: str, model_latest: str = "") -> None:
    """Read-through every five minutes while open and when the owner clicks refresh."""
    st.button(
        "Check Supabase now",
        key="hiring_live_manual_refresh",
        help="Reload stored recruiting records. This does not scan Gmail, Outlook or LinkedIn.",
    )
    try:
        sources = fetch_current_pipeline(token)
    except (RuntimeError, TimeoutError, ValueError, PermissionError):
        st.error("Live hiring data could not be retrieved. Cached statuses are not shown as current.")
        return

    render_current_pipeline(sources)
    last_priority = max(
        (str(x.get("reviewed_on") or "") for x in sources.get("priorities", [])),
        default="",
    )
    last_source = max(
        (str(value or "")[:10]
         for value in (sources.get("source_watermarks") or {}).values()),
        default="",
    )
    if model_latest and max(last_priority, last_source) > str(model_latest)[:10]:
        st.info(
            "The separate forecast model may not yet account for newer employer evidence. "
            "Its timing and credibility figures are provisional."
        )
    st.caption(
        "Auto-checks Supabase every 5 minutes while this page remains open, "
        "and also on reopening or manual refresh."
    )
