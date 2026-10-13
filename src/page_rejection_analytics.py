"""Private, evidence-weighted rejection intelligence for the owner workspace."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from statistics import median
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

from job_search_metrics import canonical_events, day, family, seniority, process_key
from page_job_search_analytics import fetch_job_records
from site_cms import _request_json, _rest_url, ensure_owner_session

FIELDS = (
    "id,process_key,employer,role,requisition_id,decision_date,decision_at,"
    "decision_outcome,hiring_stage,one_line_explanation,reason_code,reason_basis,"
    "confidence,evidence_summary,employer_feedback_excerpt,jd_match_status,"
    "source_event_ids,mailbox_evidence,mailbox_coverage,cv_version,"
    "analysis_version,analyzed_at,last_checked_at,updated_at"
)
OUTCOMES = {"rejected", "not_selected", "position_filled", "role_cancelled", "position_cancelled"}
LABELS = {
    "UNKNOWN": "Cause unknown",
    "PROCESS_COMPETITION": "Comparative selection",
    "POSITION_FILLED": "Position filled",
    "INTERNAL_CANDIDATE_SELECTED": "Internal candidate",
    "ROLE_BELOW_SENIORITY": "Mandate below seniority",
    "CRAFT_PRODUCT": "Product craft",
    "CRAFT_ENGINEERING": "Engineering craft",
    "DOMAIN_SPECIALISM": "Domain specialism",
    "GEOGRAPHY_LANGUAGE": "Location or language",
}
BASIS = {
    "employer_stated": "Employer-stated",
    "employer_relative": "Employer-relative",
    "jd_cv_inference": "Verified JD–CV inference",
    "insufficient_evidence": "Insufficient evidence",
}
WINDOWS = {"Today": 1, "7 days": 7, "30 days": 30, "90 days": 90, "All history": None}


def _fetch_rejections(token: str) -> list[dict]:
    """Read private rows only with the authenticated owner's bearer token."""
    rows: list[dict] = []
    offset = 0
    while True:
        batch = _request_json(
            "GET",
            _rest_url(
                f"job_rejection_analysis?select={FIELDS}&order=id.asc&limit=250&offset={offset}"
            ),
            token=token,
        )
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected rejection-analysis response.")
        rows.extend(batch)
        if len(batch) < 250:
            return rows
        offset += 250
        if offset >= 10000:
            raise RuntimeError("Too many rejection records for this report.")


def _canonical(rows: list[dict]) -> tuple[list[dict], int]:
    """Process-grain deduplication; analysis re-runs never create extra decisions."""
    by_key: dict[str, dict] = {}
    invalid = 0
    for row in rows:
        key = str(row.get("process_key") or "").strip()
        if not key:
            invalid += 1
            continue
        if str(row.get("decision_outcome") or "").lower() not in OUTCOMES:
            continue
        previous = by_key.get(key)
        if previous is None or (
            str(row.get("updated_at") or row.get("analyzed_at") or ""), int(row.get("id") or 0)
        ) > (
            str(previous.get("updated_at") or previous.get("analyzed_at") or ""),
            int(previous.get("id") or 0),
        ):
            by_key[key] = row
    return list(by_key.values()), invalid


def _date(row: dict):
    return day(row.get("decision_date")) or day(row.get("decision_at"))


def _in_window(row: dict, today: date, length: int | None) -> bool:
    if length is None:
        return True  # Undated historical decisions remain visible in All history.
    dt = _date(row)
    return bool(dt and today - timedelta(days=length - 1) <= dt <= today)


def _source_ref(row: dict) -> bool:
    ref = row.get("mailbox_evidence")
    if not ref:
        return False
    if isinstance(ref, list):
        return any(isinstance(v, dict) and any(v.get(k) for k in
                   ("message_id", "thread_id", "id", "web_link", "source_id")) for v in ref)
    if isinstance(ref, dict):
        return bool(any(ref.get(k) for k in
                    ("message_id", "thread_id", "id", "web_link", "source_id"))
                    or any(_source_ref({"mailbox_evidence": v}) for v in ref.values()
                           if isinstance(v, (dict, list))))
    return False


def _pct(n: int, total: int) -> str:
    return f"{n / total:.1%}" if total else "—"


def _chart(rows: list[dict], x: str, y: str, *, color: str | None = None, height=245):
    if not rows:
        st.caption("No qualifying evidence in this selection.")
        return
    # Inline Altair data has no Pandas dtype metadata. Vega-Lite v6 cannot
    # infer shorthand tooltip field types from alt.Data(values=rows).
    # Explicitly type every tooltip to prevent the Streamlit ValueError.
    tooltips = [
        alt.Tooltip(f"{x}:N", title=x),
        alt.Tooltip(f"{y}:Q", title=y, format=",d"),
    ]
    if color:
        tooltips.append(alt.Tooltip(f"{color}:N", title=color))
    try:
        chart = alt.Chart(alt.Data(values=rows)).mark_bar(cornerRadiusEnd=5).encode(
            x=alt.X(f"{x}:N", title=None, sort=None, axis=alt.Axis(labelLimit=180)),
            y=alt.Y(f"{y}:Q", title="Processes", axis=alt.Axis(tickMinStep=1)),
            tooltip=tooltips,
            **({"color": alt.Color(f"{color}:N", title="Evidence basis")} if color else {}),
        )
        st.altair_chart(chart.properties(height=height), width="stretch")
    except (ValueError, TypeError, KeyError) as exc:
        # Prefer an accessible exact-count table over a broken Analytics tab.
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption("Chart unavailable in this display; exact counts are shown above.")


def _reasons(records: list[dict]) -> list[dict]:
    counts = Counter(
        (LABELS.get(str(r.get("reason_code") or ""), str(r.get("reason_code") or "Unclassified")),
         BASIS.get(str(r.get("reason_basis") or ""), "Unspecified"))
        for r in records
    )
    return [{"Reason": name, "Basis": basis, "Processes": n}
            for (name, basis), n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]


def _quality(records: list[dict]) -> dict[str, int]:
    return {
        "Undated": sum(_date(r) is None for r in records),
        "Stage unknown": sum(str(r.get("hiring_stage") or "unknown").lower() in
                             ("unknown", "unavailable", "not_recorded") for r in records),
        "JD not verified": sum(str(r.get("jd_match_status") or "").lower() not in
                               ("verified", "full_verified", "fully_verified", "exact_verified")
                               for r in records),
        "No direct mailbox reference": sum(not _source_ref(r) for r in records),
        "Unknown motivation": sum(str(r.get("reason_code") or "").upper() == "UNKNOWN"
                                  for r in records),
    }


def _momentum(events: list[dict], today: date, days: int) -> dict[str, int]:
    """Operational, not rejection-table counts. Conservative employer-role groups."""
    start = today - timedelta(days=days - 1)
    named: dict[tuple[str, str], dict[str, bool]] = {}
    for event in canonical_events(events):
        when = day(event.get("event_date"))
        key = process_key(event)
        if not key or not when or not start <= when <= today:
            continue
        if not (event.get("is_human_interaction") or event.get("is_recruiter_interaction")
                or event.get("is_interview")):
            continue
        bucket = named.setdefault(key, {"human": False, "interview": False})
        bucket["human"] |= bool(event.get("is_human_interaction")
                                or event.get("is_recruiter_interaction"))
        bucket["interview"] |= bool(event.get("is_interview"))
    return {
        "human": sum(x["human"] for x in named.values()),
        "interview": sum(x["interview"] for x in named.values()),
        "qualified": len(named),
    }


def _linked_application_days(rejections: list[dict], events: list[dict]) -> list[int]:
    """Only matched source IDs with documented submission dates; never use ingestion dates."""
    by_id = {str(x.get("id")): x for x in canonical_events(events)}
    elapsed = []
    for r in rejections:
        decision = _date(r)
        if not decision:
            continue
        matched = [
            by_id.get(str(event_id))
            for event_id in (r.get("source_event_ids") or [])
        ]
        matches = []
        for e in matched:
            if not e or not e.get("is_application"):
                continue
            basis = str(e.get("date_basis") or "").lower()
            if not any(v in basis for v in
                       ("exact", "receipt", "confirmation", "confirmed", "applied on",
                        "tracked application date", "direct user confirmation")):
                continue
            applied = day(e.get("event_date"))
            if applied and applied <= decision:
                matches.append(applied)
        # More than one dated application reference makes the candidate round ambiguous.
        if len(set(matches)) == 1:
            elapsed.append((decision - matches[0]).days)
    return elapsed


def _matched_application_cohort(records: list[dict], events: list[dict],
                                today: date) -> dict[str, int | float | None]:
    """A documented minimum, never a complete job-search rejection rate.

    The denominator consists only of dated, deduplicated employer/role
    application groups in the operational table since June. A rejection
    counts only when its employer and role match exactly and its decision
    follows that application. Different requisitions with the same title
    can still be conflated, so expose the sample size and its limitations.
    """
    applications: dict[tuple[str, str], date] = {}
    for event in canonical_events(events):
        if event.get("is_application") is not True:
            continue
        applied = day(event.get("event_date"))
        key = process_key(event)
        if not applied or not date(2026, 6, 1) <= applied <= today or not key:
            continue
        if key not in applications or applied < applications[key]:
            applications[key] = applied
    linked: set[tuple[str, str]] = set()
    for decision in records:
        if str(decision.get("decision_outcome") or "").lower() not in OUTCOMES:
            continue
        key = process_key(decision)
        when = _date(decision)
        if key in applications and when and applications[key] <= when <= today:
            linked.add(key)
    n = len(applications)
    return {"application_pairs": n, "linked_negative": len(linked),
            "minimum_pct": round(100 * len(linked) / n, 1) if n else None,
            "unmatched_decisions": sum(
                bool(_date(d) and date(2026, 6, 1) <= _date(d) <= today
                     and process_key(d) not in linked)
                for d in records)}


def _recommendations(records: list[dict], today: date,
                     momentum90: dict | None) -> list[dict]:
    total = len(records)
    count = Counter(str(r.get("reason_code") or "").upper() for r in records)
    bases = Counter(str(r.get("reason_basis") or "") for r in records)
    q = _quality(records)
    results: list[dict] = []
    if not total:
        return [{"Area": "Coverage", "Action": "Run the Rejection Analyzer and confirm it can save process records.", "Evidence": "No qualifying decisions yet", "Priority": 1}]
    if count["UNKNOWN"] / total >= .5:
        results.append({"Area": "Feedback collection",
                        "Action": "Ask for concrete decision criteria after meaningful recruiter and interview interactions. Do not rewrite the CV from silent rejections.",
                        "Evidence": f"{count['UNKNOWN']}/{total} causes unknown ({_pct(count['UNKNOWN'], total)})",
                        "Priority": 1})
    if q["Stage unknown"] / total >= .3:
        results.append({"Area": "Process reconciliation",
                        "Action": "Recover documented interview stages and identifiers before drawing stage-conversion conclusions.",
                        "Evidence": f"{q['Stage unknown']}/{total} decision stages unresolved",
                        "Priority": 1})
    if q["JD not verified"] / total >= .5:
        results.append({"Area": "Targeting and CV evidence",
                        "Action": "Verify original requisition-level JDs before diagnosing recurring skill or domain gaps. Keep existing target criteria unless better evidence emerges.",
                        "Evidence": f"{q['JD not verified']}/{total} JDs lack strict verification",
                        "Priority": 1})
    if q["No direct mailbox reference"] / total >= .5:
        results.append({"Area": "Source traceability",
                        "Action": "Link precise Outlook/Gmail message IDs to analyzed decisions; retain correspondence inside the private database.",
                        "Evidence": f"{q['No direct mailbox reference']}/{total} records lack direct mailbox references",
                        "Priority": 2})
    if count["PROCESS_COMPETITION"] >= 3 and bases["employer_relative"] >= 3:
        results.append({"Area": "Interview and follow-up",
                        "Action": "For comparable selection outcomes, ask which roadmap priorities distinguished the selected candidate. Only change interview narratives after the requirements recur.",
                        "Evidence": f"{count['PROCESS_COMPETITION']} comparative outcomes; exact distinguishing requirements unverified",
                        "Priority": 2})
    if count["ROLE_BELOW_SENIORITY"] >= 3:
        results.append({"Area": "Role screening",
                        "Action": "Screen mandate, decision rights and salary scope before applying to similar roles.",
                        "Evidence": f"{count['ROLE_BELOW_SENIORITY']} employer-supported seniority mismatches",
                        "Priority": 2})
    elif count["ROLE_BELOW_SENIORITY"]:
        results.append({"Area": "Role screening (single case)",
                        "Action": "For roles resembling the recorded lower-seniority mandate, check scope and compensation early. Do not label this a broad pattern.",
                        "Evidence": f"{count['ROLE_BELOW_SENIORITY']} disclosed case; insufficient for a recurring-pattern claim",
                        "Priority": 3})
    if count["POSITION_FILLED"] + count["INTERNAL_CANDIDATE_SELECTED"]:
        n = count["POSITION_FILLED"] + count["INTERNAL_CANDIDATE_SELECTED"]
        results.append({"Area": "Interpretation discipline",
                        "Action": "Track closures and internal selections separately from candidate-fit concerns; preserve targeting unless independent evidence suggests otherwise.",
                        "Evidence": f"{n} disclosed filled/internal outcomes",
                        "Priority": 3})
    if momentum90 and momentum90["qualified"] > 0:
        results.append({"Area": "Opportunity momentum",
                        "Action": "Protect time for progressing conversations and follow-ups; judge pipeline health alongside negative decisions.",
                        "Evidence": f"{momentum90['qualified']} distinct employer-role groups with documented human or interview activity in 90 days (provisional grouping)",
                        "Priority": 2})
    return sorted(results, key=lambda r: (r["Priority"], r["Area"]))


@st.fragment(run_every="5m")
def render_rejection_analytics(session: dict | None) -> None:
    st.title("Rejection Analytics")
    st.caption("Owner-only · canonical hiring processes · evidence first. Decisions are dated by employer action, never analyzer refresh time.")
    valid = ensure_owner_session(session)
    if not valid or not valid.get("access_token"):
        st.warning("Owner authentication is required to access private hiring correspondence.")
        return
    st.session_state["cms_auth"] = valid
    now = datetime.now(ZoneInfo("Europe/Stockholm"))
    today = now.date()
    try:
        records, dropped = _canonical(_fetch_rejections(str(valid["access_token"])))
    except (RuntimeError, TimeoutError, ValueError) as exc:
        st.error(f"Private rejection records cannot be loaded: {exc}")
        return

    left, right = st.columns([3, 1], vertical_alignment="bottom")
    with left:
        choice = st.selectbox("Decision reporting window", list(WINDOWS),
                              index=4, key="rejection_window")
    with right:
        if st.button("Refresh evidence", width="stretch", key="rejection_refresh"):
            st.rerun(scope="fragment")
    latest_analysis = max((str(r.get("analyzed_at") or "") for r in records), default="")
    st.caption(f"Live database read · checked {now:%d %b %Y, %H:%M} Stockholm · "
               f"latest saved analyzer timestamp: {latest_analysis[:19].replace('T', ' ') or 'unknown'} (source timezone) · "
               "auto-refreshes every five minutes while open. New analyzer writes appear on the next refresh.")
    if dropped:
        st.warning(f"{dropped} source rows lack canonical process identifiers and are excluded.")

    scoped = [r for r in records if _in_window(r, today, WINDOWS[choice])]
    n = len(scoped)
    unknown = sum(str(r.get("reason_code") or "").upper() == "UNKNOWN" for r in scoped)
    confirmed = sum(str(r.get("confidence") or "").lower() == "confirmed" for r in scoped)
    stated = sum(r.get("reason_basis") == "employer_stated" for r in scoped)
    dated_global = sum(_date(r) is not None for r in records)
    m = st.columns(5)
    for cell, title, value in zip(
        m,
        ("Negative decisions", "Unknown causes", "Confirmed reasons", "Employer-stated", "Dated · all history"),
        (str(n), _pct(unknown, n), _pct(confirmed, n), _pct(stated, n),
         f"{dated_global}/{len(records)}"),
    ):
        cell.metric(title, value)
    if WINDOWS[choice] is not None:
        missing = len(records) - dated_global
        st.caption(f"Time filter uses employer decision dates only. {missing} undated historical decisions are excluded from this window, never reassigned to the analyzer run date.")
    if not scoped:
        st.info("No dated employer decisions in this window. Switch to All history to inspect undated processes.")
        return
    if unknown > n // 2:
        st.info(f"Most causes remain unknown ({unknown}/{n}). This measures limited employer feedback, not demonstrated weaknesses in your profile.")

    try:
        events = fetch_job_records(str(valid["access_token"]))
        momentum30 = _momentum(events, today, 30)
        momentum90 = _momentum(events, today, 90)
    except (RuntimeError, TimeoutError, ValueError):
        events = []
        momentum30 = momentum90 = None
    st.subheader("Are credible employer conversations still happening?")
    if momentum90 is not None:
        st.write(
            f"Last 30 days: **{momentum30['qualified']}** documented employer-role groups with "
            f"human recruiter or interview interaction. Last 90 days: **{momentum90['qualified']}**. "
            "These are observed engagement signals—not current open opportunities, "
            "offer probabilities or distinct requisition counts."
        )
    else:
        st.caption("Current momentum cannot be assessed until operational job-search events are available.")

    st.subheader("Observed rejection share · matched application cohort")
    if events:
        linked = _matched_application_cohort(records, events, today)
        cells = st.columns(3)
        pct = linked["minimum_pct"]
        cells[0].metric("Minimum documented share",
                        f"{pct:.1f}%" if pct is not None else "—")
        cells[1].metric("Matched negative outcomes",
                        f"{linked['linked_negative']} / {linked['application_pairs']}")
        cells[2].metric("Unmatched dated decisions",
                        linked["unmatched_decisions"])
        st.caption(
            "For tracked applications dated from June 2026: one employer+role "
            "group per application and a matching dated negative decision on or "
            "after submission. This is a lower bound **within the matched tracker**, "
            "not your actual rejection rate. Missing application links, multiple "
            "requisitions, undated rejections and recent unresolved applications "
            "prevent a complete cohort outcome rate. Never divide all rejection "
            "records by application event-row counts."
        )
    else:
        st.caption("A linked rejection rate cannot be calculated because the application evidence is unavailable.")

    overview, reasons, stages, evidence, research = st.tabs(
        ["Decision overview", "Reasons and patterns", "Pipeline and timing", "Evidence and next actions", "Research & hypotheses"]
    )
    with overview:
        st.subheader("What actually happened")
        outcomes = Counter(str(r.get("decision_outcome") or "unclassified") for r in scoped)
        c1, c2 = st.columns([1, 1.2])
        with c1:
            _chart([{"Outcome": k.replace("_", " ").title(), "Processes": v}
                    for k, v in sorted(outcomes.items())], "Outcome", "Processes")
        with c2:
            st.markdown("**Interpretation**")
            st.write(f"{confirmed} of {n} processes have a confirmed explanation; "
                     f"{stated} contain an employer-stated reason. A comparative selection "
                     "can be confirmed even when the precise distinguishing requirement remains unknown.")
        st.subheader("Decision timeline")
        monthly = Counter(_date(r).strftime("%Y-%m") if _date(r) else "Undated"
                          for r in scoped)
        months = sorted(x for x in monthly if x != "Undated")
        if "Undated" in monthly:
            months.append("Undated")
        _chart([{"Month": month, "Processes": monthly[month]} for month in months],
               "Month", "Processes")
        st.caption("The Undated bar is excluded from monthly trend inference. Incomplete current months are not compared with full prior months as if equivalent.")
        recent_30 = sum(bool(_date(r) and today - timedelta(days=29) <= _date(r) <= today)
                        for r in records)
        prior_30 = sum(bool(_date(r) and today - timedelta(days=59) <= _date(r) < today - timedelta(days=29))
                       for r in records)
        if prior_30 >= 10 and recent_30 >= 10:
            st.metric("Decision volume · latest 30d vs previous 30d",
                      f"{recent_30} vs {prior_30}",
                      help="Recorded decision counts in two equally long windows, not a comparison of application rejection rates.")
            st.caption(
                "More recorded decisions can result from application volume, "
                "reporting coverage or employers processing older applications. "
                "Do not interpret the difference as worsening job-market fit."
            )
    with reasons:
        explained = [r for r in scoped
                     if str(r.get("reason_basis") or "") in
                        ("employer_relative", "employer_stated")]
        supported = Counter(str(r.get("reason_code") or "") for r in explained)
        leading_code, leading_n = supported.most_common(1)[0] if supported else (None, 0)
        cause_cols = st.columns(3)
        cause_cols[0].metric(
            "Most frequent explained category",
            LABELS.get(leading_code, leading_code or "Unavailable"),
            help="Category among employer-relative or employer-stated outcomes, not a verified individual skill deficiency."
        )
        cause_cols[1].metric("Decisions in that category", f"{leading_n}/{n}")
        cause_cols[2].metric("Employer-stated explanations",
                             f"{stated}/{n}")
        if leading_code == "PROCESS_COMPETITION":
            st.info(
                "Comparative selection is the leading explained category. "
                "It means the employer advanced other candidates; it does not "
                "identify a specific missing qualification."
            )
        if supported.get("ROLE_BELOW_SENIORITY", 0) == 1:
            st.caption(
                "One employer explicitly described a seniority mismatch. "
                "One case cannot justify broad CV or role-targeting changes."
            )
        st.subheader("Reason by evidence basis")
        st.caption("Reason basis says what supports the explanation. Confidence is not a job-offer probability.")
        _chart(_reasons(scoped), "Reason", "Processes", color="Basis", height=315)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Confidence")
            conf = Counter(str(r.get("confidence") or "unknown") for r in scoped)
            _chart([{"Confidence": k, "Processes": v} for k,v in sorted(conf.items())],
                   "Confidence", "Processes")
        with c2:
            st.subheader("Where outcomes cluster")
            fam = Counter(family(str(r.get("role") or "")) for r in scoped)
            _chart([{"Role family": k, "Processes": v} for k,v in fam.most_common()],
                   "Role family", "Processes")
        st.caption("Role-family categories come from title heuristics, not verified vacancy JDs. Counts alone are not rejection rates: application denominators differ.")
        with st.expander("Employer-specific findings and supporting interpretation", expanded=True):
            shown = [r for r in scoped if str(r.get("reason_code") or "").upper() != "UNKNOWN"]
            st.dataframe([{"Employer": r.get("employer"), "Role": r.get("role"),
                           "Decision": str(_date(r) or "Undated"), "Reason": LABELS.get(r.get("reason_code"), r.get("reason_code")),
                           "Evidence basis": BASIS.get(r.get("reason_basis"), r.get("reason_basis")),
                           "Confidence": r.get("confidence"),
                           "Explanation": r.get("one_line_explanation")}
                          for r in shown], hide_index=True, width="stretch")
    with stages:
        st.subheader("Hiring stages before decisions")
        stage_counts = Counter(str(r.get("hiring_stage") or "unknown") for r in scoped)
        _chart([{"Stage": k.replace("_", " ").title(), "Processes": v}
                for k,v in stage_counts.most_common()], "Stage", "Processes", height=265)
        unknown_stage = stage_counts.get("unknown", 0)
        st.caption(f"{unknown_stage}/{n} stages explicitly unknown. No stage is imputed from rejection wording.")
        st.subheader("Credible opportunity momentum")
        if momentum30 is None or momentum90 is None:
            st.warning("Operational application events unavailable. Momentum, conversion and latency are not estimated.")
        if momentum30 and momentum90:
            a,b,c = st.columns(3)
            a.metric("Human-engaged groups · 30d", momentum30["human"])
            b.metric("Interview-related groups · 30d", momentum30["interview"])
            c.metric("Human/interview groups · 90d", momentum90["qualified"])
            st.caption("Derived from deduplicated operational events. Employer+role grouping is provisional where requisition IDs are missing; these are not verified unique hiring rounds.")
            latency = _linked_application_days(scoped, events)
            if latency:
                st.metric("Median verified application-to-decision", f"{median(latency):g} days",
                          help=f"{len(latency)} processes with directly linked, uniquely dated application source events.")
            else:
                st.caption("Time-to-decision unavailable: no unambiguous matched application dates in this selection.")
            st.caption("Application rejection rate and interview conversion by application cohort require requisition-level reconciliation. They are deliberately not calculated from raw rejection rows.")
        else:
            st.caption("Human-interaction momentum is unavailable without operational evidence.")
    with evidence:
        q = _quality(scoped)
        st.subheader("Evidence coverage and unresolved records")
        cols = st.columns(4)
        for col, label in zip(cols, ("Undated", "Stage unknown", "JD not verified",
                                     "No direct mailbox reference")):
            col.metric(label, f"{q[label]}/{n}")
        st.caption("Partially matched JDs cannot substantiate a skills-gap claim. Mailbox evidence stays owner-only.")
        mom = momentum90
        st.subheader("Recommendations generated from current evidence")
        recs = _recommendations(scoped, today, mom)
        for r in recs:
            with st.container(border=True):
                st.markdown(f"**{r['Area']}**")
                st.write(r["Action"])
                st.caption(f"Evidence: {r['Evidence']}")
        with st.expander("Inspect processes needing evidence review"):
            review = sorted((r for r in scoped if (
                str(r.get("reason_code") or "").upper() == "UNKNOWN"
                or not _date(r)
                or str(r.get("hiring_stage") or "unknown").lower() == "unknown"
                or str(r.get("jd_match_status") or "") != "verified")),
                key=lambda r: (bool(_date(r)), str(r.get("employer") or "")))
            st.dataframe([{
                "Employer": r.get("employer"), "Role": r.get("role"),
                "Decision": str(_date(r) or "Undated"),
                "Cause": LABELS.get(r.get("reason_code"), r.get("reason_code")),
                "Stage": r.get("hiring_stage") or "Unknown",
                "JD match": r.get("jd_match_status") or "Not checked",
                "Evidence": "Referenced" if _source_ref(r) else "Needs source link",
            } for r in review], hide_index=True, width="stretch")
        st.caption("No background mailbox monitoring is implied: this dashboard reflects the latest saved Rejection Analyzer results. The analyzer itself runs when invoked.")

    with research:
        from page_rejection_inference import render_rejection_inference
        render_rejection_inference(valid, scoped)
