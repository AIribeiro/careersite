"""Private per-role recruiting journeys within the owner Admin workspace."""
from __future__ import annotations

from datetime import date, datetime, timezone
from io import StringIO
import csv
import re
from uuid import uuid4

import altair as alt
import streamlit as st

from recruiting_journeys import (
    TZ, as_day, elapsed, journey, cohort_metrics, comparison_rows,
)
from site_cms import _request_json, _rest_url

TABLE = "careersite_recruiting_opportunities"
OUTCOMES = {
    "unknown": "Unknown / not documented",
    "in_progress": "In progress",
    "rejected": "Employer rejection",
    "offer": "Offer",
    "withdrawn": "Candidate withdrew",
    "closed": "Closed without known decision",
}
DATE_BASES = {
    "unknown": "No reliable application date",
    "confirmed_submission": "Confirmed submission",
    "candidate_reported": "Candidate-reported date",
    "estimated": "Estimated / imputed (not counted in precise durations)",
}


def fetch_opportunities(token: str) -> list[dict]:
    response = _request_json(
        "GET",
        _rest_url(
            f"{TABLE}?select=id,process_key,employer,role_title,application_date,"
            "application_evidence,application_date_basis,outcome,decision_date,"
            "decision_evidence,offer_date,offer_evidence,notes,updated_at"
            "&order=updated_at.desc,id.desc&limit=500"
        ),
        token=token,
    )
    return [r for r in response if isinstance(r, dict)] if isinstance(response, list) else []


def _duration(days: int | float | None) -> str:
    if days is None:
        return "—"
    return f"{days:g} days"


def _export_comparison(rows: list[dict]) -> str:
    if not rows:
        return ""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _journey_table(model: dict) -> list[dict]:
    output = []
    for event in model["events"]:
        source = event.get("source") or "—"
        output.append({
            "Date": event["date"].strftime("%d %b %Y"),
            "Milestone": event["label"],
            "Evidence state": event["state"],
            "From application": _duration(event["from_application"]),
            "From previous": _duration(event["from_previous"]),
            "Until offer": _duration(event["to_offer"]),
            "Source": source,
        })
    return output


def _milestone_visual(model: dict) -> None:
    events = model["events"]
    if not events:
        return
    points = [{
        "Date": event["date"].isoformat(),
        "Step": f"{i + 1}. {event['label']}",
        "State": event["state"],
        "Description": event["label"],
        "From application": _duration(event["from_application"]),
    } for i, event in enumerate(events)]
    labels = [r["Step"] for r in reversed(points)]
    base = alt.Chart(alt.Data(values=points)).encode(
        x=alt.X("Date:T", title="Calendar date", axis=alt.Axis(format="%d %b")),
        y=alt.Y("Step:N", sort=labels, title=None),
    )
    dots = base.mark_circle(size=145).encode(
        color=alt.Color(
            "State:N",
            legend=alt.Legend(title="Evidence status", orient="bottom"),
        ),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%d %b %Y"),
            "Description:N", "State:N", "From application:N",
        ],
    )
    st.altair_chart(
        dots.properties(height=max(190, len(points) * 42)),
        use_container_width=True,
    )


def _quality_signal(models: list[dict]) -> None:
    stats = cohort_metrics(models)
    st.subheader("Hiring-process overview")
    cols = st.columns(4)
    cols[0].metric("Linked processes", stats["processes"])
    cols[1].metric("Multi-round journeys", stats["multi_round_processes"],
                   help="At least two distinct, explicitly numbered rounds. Planned rounds count toward this indicator.")
    cols[2].metric("Completed interviews", stats["completed_interviews"],
                   help="Only interview records with explicitly confirmed attendance.")
    cols[3].metric("Verified offers", stats["offers_recorded"],
                   help="Offers with an evidenced offer date, not inferred from recruiter enthusiasm.")

    a, b, c = st.columns(3)
    a.metric("Application → first held interview",
             _duration(stats["median_days_to_first"]))
    a.caption(f"Median · {stats['first_sample']} verified application/interview pair(s)")
    b.metric("Between completed consecutive rounds",
             _duration(stats["median_days_between_completed_rounds"]))
    b.caption(f"Median · {stats['round_sample']} verified consecutive-round pair(s)")
    c.metric("Application → dated offer", _duration(stats["median_days_to_offer"]))
    c.caption(f"Median · {stats['offer_sample']} evidenced offer(s)")
    st.caption(
        "Elapsed days are calendar days, not business days. Medians use confirmed submissions and "
        "completed interviews only. Missing or estimated application dates and scheduled-but-not-held "
        "interviews never enter completed-process medians."
    )


def _role_detail(model: dict, now: datetime) -> None:
    op = model["opportunity"]
    st.markdown(f"#### {op['employer']} · {op['role_title']}")
    st.caption(
        f"Opportunity #{op['id']} · "
        f"{OUTCOMES.get(op.get('outcome'), 'Unknown')} · "
        f"{DATE_BASES.get(op.get('application_date_basis'), 'Unknown application date')}"
    )
    applied = model["application_date"]
    offer = model["offer_date"]
    app_caption = applied.strftime("%d %b %Y") if applied else "Not established"
    offer_caption = offer.strftime("%d %b %Y") if offer else "Not evidenced"
    columns = st.columns(4)
    columns[0].metric("Application", app_caption)
    columns[1].metric("Application → first held",
                      _duration(model["days_to_first_confirmed"]))
    columns[2].metric("Interviews confirmed", len(model["confirmed"]))
    columns[3].metric("Offer", offer_caption)
    st.caption(
        "The timeline distinguishes interview invitations from attended interviews. "
        "A planned second round is not a completed second round."
    )
    if not model["events"]:
        st.info("No dated milestones yet. Enter an application date or link an interview below.")
        return
    if applied and model["meetings"]:
        older = [row for row in model["meetings"]
                 if as_day(row.get("scheduled_date")) and
                 as_day(row.get("scheduled_date")) < applied]
        if older:
            st.warning(
                "Some interview invitations predate the application date. "
                "Check whether a separate requisition or an incorrect date has been linked."
            )

    _milestone_visual(model)
    st.dataframe(_journey_table(model), hide_index=True, use_container_width=True)
    numbered = sorted(model["by_round"].items())
    if numbered:
        st.markdown("**Round-by-round elapsed time**")
        summary = []
        for ordinal, event in numbered:
            summary.append({
                "Round": ordinal,
                "Date": event["date"].isoformat(),
                "Status": event["state"],
                "Applied → round": _duration(event["from_application"]),
                "Round → offer": _duration(event["to_offer"]),
            })
        st.dataframe(summary, hide_index=True, use_container_width=True)
    else:
        st.caption("Round numbers have not been established. Assign each interview its actual round in the meeting editor.")

    if not applied:
        st.info("Application date is missing. Round dates are still visible, but application-to-round intervals remain blank.")
    elif not model["application_reliable"]:
        st.info("The application date is estimated. Exact application-to-stage day counts are suppressed.")
    if not offer:
        st.caption("No dated offer is supported by the recorded evidence; offer intervals are intentionally blank.")
    if op.get("notes"):
        with st.expander("Process notes"):
            st.write(op["notes"])


def _process_editor(opportunities: list[dict], token: str, selected_id: int | None) -> None:
    with st.expander("Edit application dates, decisions or add a hiring process"):
        selector = {"Create a separate hiring process": None}
        selector.update({
            f"{o['employer']} · {o['role_title']} (#{o['id']})": o["id"]
            for o in opportunities
        })
        default = next(
            (key for key, value in selector.items() if value == selected_id),
            "Create a separate hiring process",
        )
        selected_label = st.selectbox(
            "Hiring process to edit", list(selector),
            index=list(selector).index(default), key="journey_edit_opportunity",
        )
        process_id = selector[selected_label]
        original = next((o for o in opportunities if o["id"] == process_id), {})
        with st.form(f"journey_process_edit_form_{process_id or 'new'}"):
            left, right = st.columns(2)
            with left:
                employer = st.text_input("Employer", value=original.get("employer") or "",
                                         key=f"jemp_{process_id}")
                role = st.text_input("Exact role / requisition",
                                     value=original.get("role_title") or "",
                                     key=f"jrole_{process_id}")
                old_application = as_day(original.get("application_date"))
                app_known = st.checkbox(
                    "Application date known", value=old_application is not None,
                    key=f"japp_known_{process_id}",
                )
                app_date = st.date_input(
                    "Application date", value=old_application or date.today(),
                    disabled=not app_known, key=f"japp_date_{process_id}",
                )
                date_basis = st.selectbox(
                    "Application date reliability", list(DATE_BASES),
                    format_func=lambda item: DATE_BASES[item],
                    index=list(DATE_BASES).index(
                        original.get("application_date_basis")
                        if original.get("application_date_basis") in DATE_BASES else "unknown"
                    ),
                    key=f"jbasis_{process_id}",
                )
                app_evidence = st.text_area(
                    "Application evidence reference",
                    value=original.get("application_evidence") or "",
                    help="Email confirmation, ATS receipt, source event ID or precise self-report.",
                    key=f"jappsource_{process_id}",
                )
            with right:
                outcome = st.selectbox(
                    "Hiring process status", list(OUTCOMES),
                    format_func=lambda item: OUTCOMES[item],
                    index=list(OUTCOMES).index(
                        original.get("outcome") if original.get("outcome") in OUTCOMES else "unknown"
                    ),
                    key=f"joutcome_{process_id}",
                )
                old_decision = as_day(original.get("decision_date"))
                decision_known = st.checkbox(
                    "Dated hiring decision", value=old_decision is not None,
                    key=f"jdec_known_{process_id}",
                )
                decision_date = st.date_input(
                    "Decision date", value=old_decision or date.today(),
                    disabled=not decision_known, key=f"jdec_date_{process_id}",
                )
                decision_evidence = st.text_area(
                    "Decision evidence reference",
                    value=original.get("decision_evidence") or "",
                    key=f"jdecsource_{process_id}",
                )
                old_offer = as_day(original.get("offer_date"))
                offer_known = st.checkbox(
                    "Dated offer confirmed", value=old_offer is not None,
                    key=f"joffer_known_{process_id}",
                )
                offer_date = st.date_input(
                    "Offer received on", value=old_offer or date.today(),
                    disabled=not offer_known, key=f"joffer_date_{process_id}",
                )
                offer_evidence = st.text_area(
                    "Offer evidence reference",
                    value=original.get("offer_evidence") or "",
                    help="Offer email or written offer reference. No inferred offers.",
                    key=f"joffersource_{process_id}",
                )
            notes = st.text_area(
                "Notes on this specific vacancy",
                value=original.get("notes") or "", key=f"jnotes_{process_id}",
            )
            submitted = st.form_submit_button("Save hiring process", type="primary")
        if submitted:
            error_message = None
            if not employer.strip() or not role.strip():
                error_message = "Employer and exact role are required."
            elif app_known and (date_basis == "unknown" or not app_evidence.strip()):
                error_message = "A known application date requires a reliability basis and evidence."
            elif decision_known and not decision_evidence.strip():
                error_message = "A dated decision requires its evidence reference."
            elif offer_known and (not offer_evidence.strip() or outcome != "offer"):
                error_message = "A dated offer requires evidence and the Offer status."
            elif offer_known and decision_known and offer_date > decision_date:
                # Decision may be made before offer; a later date can also mean acceptance.
                error_message = "Please record the offer date as the decision date or earlier."
            elif any(d > datetime.now(TZ).date() for d in (
                [app_date] if app_known else []
            ) + ([decision_date] if decision_known else []) +
                ([offer_date] if offer_known else [])):
                error_message = "Application, decision and offer must have occurred already."
            if error_message:
                st.error(error_message)
            else:
                payload = {
                    "employer": employer.strip(), "role_title": role.strip(),
                    "application_date": app_date.isoformat() if app_known else None,
                    "application_date_basis": date_basis if app_known else "unknown",
                    "application_evidence": app_evidence.strip() if app_known else "",
                    "outcome": outcome,
                    "decision_date": decision_date.isoformat() if decision_known else None,
                    "decision_evidence": decision_evidence.strip() if decision_known else "",
                    "offer_date": offer_date.isoformat() if offer_known else None,
                    "offer_evidence": offer_evidence.strip() if offer_known else "",
                    "notes": notes.strip(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                if process_id is None:
                    normalized = re.sub(r"[^a-z0-9]+", "-", f"{employer}-{role}".lower()).strip("-")
                    payload["process_key"] = f"{normalized[:76]}-{uuid4().hex[:10]}"
                    method, path = "POST", TABLE
                else:
                    method, path = "PATCH", f"{TABLE}?id=eq.{process_id}"
                try:
                    _request_json(method, _rest_url(path), token=token, payload=payload,
                                  prefer="return=minimal")
                except (RuntimeError, ValueError) as exc:
                    st.error(f"Could not save hiring process: {exc}")
                else:
                    st.success("Hiring process saved. Link its interviews using the meeting editor.")
                    st.rerun()


def render_role_journeys(token: str, meetings: list[dict], now: datetime,
                         opportunities: list[dict] | None = None) -> None:
    st.subheader("Role-by-role hiring journeys")
    st.caption(
        "One journey per vacancy. Every interview round connects to that vacancy's "
        "application and decision evidence, where available."
    )
    if opportunities is None:
        try:
            opportunities = fetch_opportunities(token)
        except (RuntimeError, ValueError) as exc:
            st.error(f"Hiring-process history is unavailable: {exc}")
            return
    models = [journey(op, meetings, now) for op in opportunities]
    _quality_signal(models)
    if not models:
        st.info("No hiring processes are linked yet. Add one below.")
        _process_editor([], token, None)
        return

    models.sort(
        key=lambda j: (
            0 if any(e["state"].startswith("Scheduled") for e in j["meeting_events"]) else 1,
            -(max((e["date"].toordinal() for e in j["events"]), default=0)),
            j["opportunity"]["employer"],
        )
    )
    map_by_id = {j["opportunity"]["id"]: j for j in models}
    selected_id = st.selectbox(
        "Explore a hiring journey",
        options=list(map_by_id),
        format_func=lambda item: (
            f"{map_by_id[item]['opportunity']['employer']} · "
            f"{map_by_id[item]['opportunity']['role_title']} "
            f"({len(map_by_id[item]['meeting_events'])} interview record(s))"
        ),
        key="recruiter_journey_selector",
    )
    _role_detail(map_by_id[selected_id], now)
    with st.expander("Compare timelines across all hiring processes", expanded=True):
        table_rows = comparison_rows(models)
        st.dataframe(table_rows, hide_index=True, use_container_width=True)
        st.download_button(
            "Export journey comparison (CSV)", data=_export_comparison(table_rows),
            file_name="private_role_journey_comparison.csv", mime="text/csv",
            key="recruiter_export_journey_comparison",
        )
        st.caption(
            "'Planned' means a future appointment, not interview completion. "
            "'Unverified' means a past invitation with no attendance confirmation. "
            "Each process remains separate even when an employer has multiple vacancies."
        )
    _process_editor(opportunities, token, selected_id)
    detached = [r for r in meetings if not r.get("opportunity_id")]
    if detached:
        st.caption(
            f"{len(detached)} meeting(s) remain unlinked (for example, a networking "
            "call or a vacancy whose identity is still unclear). "
            "Attach only after verifying the requisition in the meeting editor."
        )
