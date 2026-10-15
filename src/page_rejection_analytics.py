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
    "analysis_version,decision_date_basis,analyzed_at,last_checked_at,updated_at"
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
def _render_inferred_barrier_snapshot(session: dict, scoped: list[dict], hypotheses: list[dict] | None = None) -> None:
    """Summarize private role-fit hypotheses separately from actual employer reasons.

    The denominator is distinct rejected processes with no verified specific cause.
    Multiple hypotheses for one application never multiply the process count.
    """
    unknown_ids = {
        int(r["id"]) for r in scoped
        if r.get("id") is not None
        and str(r.get("reason_code") or "").upper() == "UNKNOWN"
    }
    if not unknown_ids:
        return

    # Use the same owner-authenticated, RLS-protected read as Research & hypotheses.
    if hypotheses is None:
        st.warning("Private hypothesis evidence is temporarily unavailable; employer-reported counts remain usable.")
        return

    supported = set()
    tentative = set()
    for hypothesis in hypotheses:
        try:
            process_id = int(hypothesis.get("rejection_id") or -1)
        except (TypeError, ValueError):
            continue
        if process_id not in unknown_ids:
            continue
        state = str(hypothesis.get("assessment_state") or "")
        if state == "supported_possible":
            supported.add(process_id)
        elif state in ("weak_possible", "investigating"):
            tentative.add(process_id)
    # Rank mutually exclusive tiers: supported > tentative > no established barrier.
    tentative -= supported
    no_barrier = unknown_ids - supported - tentative

    st.subheader("What can we infer beyond the employer's explanation?")
    st.caption(
        "Evidence from role requirements and the submitted profile can identify "
        "potential hiring barriers even when employers do not disclose their reasons."
    )
    labels = (
        "Supported possible barrier",
        "Tentative lead only",
        "No supported barrier",
    )
    counts = (len(supported), len(tentative), len(no_barrier))
    observations = [
        {"Evidence tier": label, "Processes": count}
        for label, count in zip(labels, counts)
    ]
    chart = alt.Chart(alt.Data(values=observations)).mark_bar().encode(
        x=alt.X("Processes:Q", title="Distinct rejected processes"),
        y=alt.Y("Evidence tier:N", sort=list(labels), title=None),
        tooltip=[
            alt.Tooltip("Evidence tier:N", title="Evidence tier"),
            alt.Tooltip("Processes:Q", title="Processes"),
        ],
    ).properties(height=154)
    value_labels = alt.Chart(alt.Data(values=observations)).mark_text(
        align="left", baseline="middle", dx=5
    ).encode(
        x="Processes:Q",
        y=alt.Y("Evidence tier:N", sort=list(labels)),
        text="Processes:Q",
    )
    left, right = st.columns([1.55, 1], vertical_alignment="center")
    with left:
        st.altair_chart(chart + value_labels, use_container_width=True)
    with right:
        st.markdown(
            f"**{len(supported) + len(tentative)} of {len(unknown_ids)}** "
            "unexplained decisions have an evidence-based line of inquiry."
        )
        st.write(
            f"**{len(supported)}** have a supported possible requirement mismatch; "
            f"**{len(tentative)}** have only tentative leads. "
            f"**{len(no_barrier)}** cannot yet be meaningfully attributed "
            "to a candidate–role barrier."
        )
    st.caption(
        "These are overlapping-hypothesis-safe process counts, not "
        "confirmed rejection causes or estimated probabilities. "
        "A supported candidate–role mismatch does not establish the employer's motive. "
        "Open Research & hypotheses below for sources, counterevidence and follow-up."
    )
    latest_hypothesis = max(
        (str(h.get("analyzed_at") or "") for h in hypotheses
         if int(h.get("rejection_id") or -1) in unknown_ids),
        default="",
    )
    if latest_hypothesis:
        st.caption(
            "Latest saved inference review: "
            f"{latest_hypothesis[:19].replace('T', ' ')} "
            "(source timezone). The breakdown reads Supabase live."
        )


# Candidate-side barrier categories, deliberately distinct from the employer's motive.
# The classification is one family per hypothesis; per-process deduplication prevents
# repeated synonyms inflating the count for a family.
BARRIER_FAMILIES = {
    "LANGUAGE_REQUIREMENT": "Swedish-language requirements",
    "WORK_MODEL_LOCATION": "Location and workplace model",
    "GEOGRAPHY_LANGUAGE": "Location or language (unclear)",
    "GEOGRAPHY_ELIGIBILITY": "Work-country eligibility",
    "POLICY_CLEARANCE": "Clearance and role eligibility",
    "WORK_AUTHORIZATION": "Clearance and role eligibility",
    "CRAFT_ENGINEERING": "Technical engineering depth",
    "PLATFORM_ENGINEERING_MANDATE": "Technical engineering depth",
    "CRAFT_AI_PRODUCT": "Product ownership",
    "CRAFT_PRODUCT": "Product ownership",
    "CRAFT_PRODUCT_OWNER": "Product ownership",
    "CRAFT_PRODUCT_ANALYTICS": "Specialist analytics craft",
    "CRAFT_ANALYTICS": "Specialist analytics craft",
    "CRAFT_ANALYST": "Specialist analytics craft",
    "CRAFT_DIGITAL_ANALYTICS": "Specialist analytics craft",
    "CONSULTING_DELIVERY": "Consulting and commercial scope",
    "COMMERCIAL_MANDATE_FIT": "Consulting and commercial scope",
    "GENAI_VENDOR_COMMERCIAL": "Consulting and commercial scope",
    "DOMAIN_SPECIALISM": "Industry / functional specialism",
    "DOMAIN_COMPETITION": "Industry / functional specialism",
    "REGULATED_INDUSTRY": "Industry / functional specialism",
    "REGULATED_AI_COMPLIANCE_SPECIALISM": "Regulated compliance depth",
    "REGULATED_DATA_GOVERNANCE": "Regulated compliance depth",
    "INSIGHTS_METHOD_SPECIALISM": "Industry / functional specialism",
    "LEADERSHIP_SCALE": "Seniority and mandate scope",
    "ROLE_BELOW_SENIORITY": "Seniority and mandate scope",
    "SENIORITY_UP": "Seniority and mandate scope",
    "ROLE_SCOPE_FIT": "Seniority and mandate scope",
    "PROGRAM_EXECUTION_MANDATE": "Execution-focused mandate",
    "PROCESS_IMPROVEMENT_MANDATE": "Execution-focused mandate",
    "COMPENSATION": "Compensation expectations",
    "EMPLOYMENT_MODEL": "Employment arrangement",
    "ASSESSMENT_INTERVIEW": "Interview / assessment evidence",
}


def _render_hiring_barrier_patterns(session: dict, scoped: list[dict], hypotheses: list[dict] | None = None) -> None:
    """Read owner-only hypotheses; chart distinct rejected processes per barrier."""
    unknown = {
        int(r["id"]): r for r in scoped
        if r.get("id") is not None
        and str(r.get("reason_code") or "").upper() == "UNKNOWN"
    }
    if not unknown:
        st.caption("No cases with undisclosed causes in this window.")
        return
    if hypotheses is None:
        st.warning("The saved inference hypotheses could not be read; employer-reported details remain available.")
        return
    rows = hypotheses

    # Rank per process *and* family. A supported hypothesis supersedes tentative
    # hypotheses in the same family; others remain independent possible barriers.
    ranked: dict[tuple[int, str], tuple[int, dict]] = {}
    process_level: dict[int, int] = {rid: 0 for rid in unknown}
    for row in rows:
        try:
            rid = int(row.get("rejection_id") or -1)
        except (TypeError, ValueError):
            continue
        code = str(row.get("hypothesis_code") or "").upper()
        family_label = BARRIER_FAMILIES.get(code)
        state = str(row.get("assessment_state") or "").lower()
        level = (2 if state == "supported_possible"
                 else 1 if state in ("weak_possible", "investigating") else 0)
        if rid not in unknown or not family_label or not level:
            continue
        key = (rid, family_label)
        if level > ranked.get(key, (0, {}))[0]:
            ranked[key] = level, row
        process_level[rid] = max(process_level[rid], level)

    strong = sum(level == 2 for level in process_level.values())
    tentative = sum(level == 1 for level in process_level.values())
    unestablished = sum(level == 0 for level in process_level.values())
    st.caption(
        "Distinct rejected processes with undisclosed employer motives. "
        "Supported = a source-backed possible role–profile mismatch; "
        "tentative = a weaker, investigable lead. "
        "Neither tier confirms the employer's decision criterion."
    )
    left, right = st.columns([1.8, 1], vertical_alignment="top")
    with left:
        groups: dict[str, dict[str, int]] = {}
        for (_, family_label), (level, _) in ranked.items():
            totals = groups.setdefault(
                family_label, {"Supported": 0, "Tentative": 0}
            )
            totals["Supported" if level == 2 else "Tentative"] += 1
        ordered = sorted(
            groups, key=lambda key: (
                -(groups[key]["Supported"] + groups[key]["Tentative"]),
                -groups[key]["Supported"], key,
            )
        )
        if ordered:
            chart_rows = [
                {"Barrier": name, "Evidence": tier, "Processes": groups[name][tier]}
                for name in ordered for tier in ("Supported", "Tentative")
                if groups[name][tier]
            ]
            bars = alt.Chart(alt.Data(values=chart_rows)).mark_bar().encode(
                y=alt.Y(
                    "Barrier:N", sort=ordered, title=None,
                    axis=alt.Axis(labelLimit=225, labelFontSize=12),
                ),
                x=alt.X(
                    "Processes:Q", title="Distinct hiring processes",
                    axis=alt.Axis(tickMinStep=1),
                ),
                color=alt.Color(
                    "Evidence:N", title="Evidence strength",
                    scale=alt.Scale(
                        domain=["Supported", "Tentative"],
                        range=["#39796B", "#BD9464"],
                    ),
                    legend=alt.Legend(orient="top"),
                ),
                order=alt.Order("Evidence:N", sort="ascending"),
                tooltip=[
                    alt.Tooltip("Barrier:N", title="Potential barrier"),
                    alt.Tooltip("Evidence:N", title="Strength"),
                    alt.Tooltip("Processes:Q", title="Distinct processes"),
                ],
            ).properties(height=max(250, min(560, len(ordered) * 38)))
            st.altair_chart(bars, use_container_width=True)
            st.caption(
                "A process may have more than one different barrier; "
                "bars should not be summed to calculate the rejected-process total."
            )
        else:
            st.info("No supported or tentative barrier hypotheses in the selected window.")
    with right:
        st.markdown(
            f"**{strong + tentative} of {len(unknown)}** cases have a "
            "specific, evidence-linked question worth investigating."
        )
        st.write(
            f"{strong} have at least one supported candidate–role mismatch. "
            f"{tentative} have tentative leads only; "
            f"{unestablished} still lack a grounded explanation."
        )
        if ranked:
            leading = sorted(
                groups,
                key=lambda key: (-groups[key]["Supported"],
                                 -(groups[key]["Supported"] + groups[key]["Tentative"]),
                                 key)
            )[0]
            lead_n = groups[leading]["Supported"]
            if lead_n:
                st.markdown(
                    f"**Strongest recurring signal:** {leading} "
                    f"({lead_n} supported process"
                    f"{'es' if lead_n != 1 else ''})."
                )
            else:
                st.caption(
                    "Current evidence is too tentative to identify "
                    "a recurring supported hiring barrier."
                )
        if ranked:
            next_steps = {
                "Technical engineering depth":
                    "Prioritize operating-model leadership over roles centred on production engineering.",
                "Swedish-language requirements":
                    "Check mandatory professional Swedish before applying; do not confuse preferred with required.",
                "Consulting and commercial scope":
                    "Validate account revenue, sales and delivery ownership against your documented experience.",
                "Product ownership":
                    "Confirm whether production feature delivery and product P&L are primary hiring criteria.",
                "Specialist analytics craft":
                    "Screen for hands-on analytics engineering versus enterprise analytics leadership.",
                "Location and workplace model":
                    "Clarify attendance and multi-office flexibility early; travel and relocation remain possible.",
                "Industry / functional specialism":
                    "Prove the requested domain depth explicitly or prioritize cross-industry mandates.",
                "Regulated compliance depth":
                    "Check whether specialist compliance track record is a hard requirement.",
            }
            ranked_supported = sorted(
                ((name, values["Supported"]) for name, values in groups.items()
                 if values["Supported"] > 0),
                key=lambda item: (-item[1], item[0]),
            )
            if ranked_supported:
                st.markdown("**What this suggests for future applications**")
                for name, number in ranked_supported[:2]:
                    if name in next_steps:
                        st.write(next_steps[name])
        st.caption(
            "These are evidence-strength classifications, not employer-motive "
            "probabilities or statistically proven drivers of rejection."
        )

    if ranked:
        with st.expander("Inspect roles and evidence behind each barrier", expanded=False):
            chosen = st.selectbox(
                "Potential hiring barrier", options=ordered,
                key="rejection_barrier_category",
            )
            selected = [
                (rid, level, row)
                for (rid, label), (level, row) in ranked.items()
                if label == chosen
            ]
            selected.sort(
                key=lambda v: (-v[1], str(unknown[v[0]].get("employer") or ""))
            )
            st.dataframe([
                {
                    "Employer": unknown[rid].get("employer"),
                    "Role": unknown[rid].get("role"),
                    "Evidence strength": "Supported" if level == 2 else "Tentative",
                    "Potential mismatch": h.get("explanation"),
                    "Counterevidence": h.get("counterargument"),
                    "Limitation": h.get("limitation"),
                }
                for rid, level, h in selected
            ], hide_index=True, width="stretch")
            st.caption(
                "Original vacancy references and detailed research remain "
                "under Research & hypotheses. These observations do not "
                "identify why the employer rejected an application."
            )


def render_rejection_analytics(session: dict | None) -> None:
    st.title("Rejection Analytics")
    st.caption("Owner-only · one record per hiring process · evidence first. Dates reflect observed negative outcomes where sources are verified; they do not necessarily identify the employer\'s internal decision date.")
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
               f"latest canonical rejection timestamp: {latest_analysis[:19].replace('T', ' ') or 'unknown'} (source timezone) · "
               "auto-refreshes every five minutes while open. New analyzer writes appear on the next refresh.")
    if dropped:
        st.warning(f"{dropped} source rows lack canonical process identifiers and are excluded.")

    scoped = [r for r in records if _in_window(r, today, WINDOWS[choice])]
    # All five tabs share one owner-only read of the external source evidence
    # and one of the hypotheses. Avoid duplicate network work in every tab.
    from page_rejection_inference import (
        _private_rows, EVIDENCE_FIELDS, HYPOTHESIS_FIELDS,
    )
    research_sources = None
    research_hypotheses = None
    try:
        research_sources = _private_rows(
            str(valid["access_token"]), "job_rejection_external_evidence", EVIDENCE_FIELDS
        )
    except (RuntimeError, TimeoutError, ValueError) as exc:
        st.caption(f"External-source research temporarily unavailable: {exc}")
    try:
        research_hypotheses = _private_rows(
            str(valid["access_token"]), "job_rejection_hypotheses", HYPOTHESIS_FIELDS
        )
    except (RuntimeError, TimeoutError, ValueError) as exc:
        st.caption(f"Candidate–role hypothesis review temporarily unavailable: {exc}")
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
        st.caption(f"Time filter uses recorded negative-outcome dates, not necessarily internal employer decision dates. {missing} undated outcomes are excluded; older dates without verified provenance remain marked legacy-unclassified.")
    if not scoped:
        st.info("No dated employer decisions in this window. Switch to All history to inspect undated processes.")
        return
    unresolved_date_basis = sum(str(r.get("decision_date_basis") or "") == "legacy_unclassified" for r in scoped)
    if unresolved_date_basis:
        st.caption(f"Date evidence: {unresolved_date_basis}/{n} outcomes still use historical dates with unverified source provenance. Treat fine-grained daily trends cautiously.")
    if unknown > n // 2:
        st.info(f"{unknown}/{n} employers did not disclose a specific cause. This does not imply that all {unknown} cases lack useful role-fit evidence; see the inference breakdown below.")
    _render_inferred_barrier_snapshot(valid, scoped, research_hypotheses)

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
        st.subheader("What happened in the recorded decisions?")
        counts = Counter(str(r.get("decision_outcome") or "unclassified").lower()
                         for r in scoped)
        candidate_not_selected = counts["rejected"] + counts["not_selected"]
        filled_or_cancelled = (counts["position_filled"] + counts["role_cancelled"]
                               + counts["position_cancelled"])
        a, b = st.columns([1.6, 1], vertical_alignment="center")
        with a:
            summary = [
                {"Outcome": "Candidate not selected", "Processes": candidate_not_selected},
                {"Outcome": "Position filled", "Processes": counts["position_filled"]},
                {"Outcome": "Recruitment cancelled", "Processes":
                 counts["role_cancelled"] + counts["position_cancelled"]},
            ]
            summary = [row for row in summary if row["Processes"]]
            overview_chart = alt.Chart(alt.Data(values=summary)).mark_bar(
                cornerRadiusEnd=4
            ).encode(
                x=alt.X("Processes:Q", title="Hiring processes",
                        axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("Outcome:N", sort="-x", title=None,
                        axis=alt.Axis(labelLimit=200)),
                tooltip=[
                    alt.Tooltip("Outcome:N"),
                    alt.Tooltip("Processes:Q", format=",d"),
                ],
            ).properties(height=155)
            st.altair_chart(overview_chart, use_container_width=True)
        with b:
            st.markdown(
                f"**{candidate_not_selected} of {n}** were recorded as "
                "candidate-not-selected outcomes."
            )
            st.write(
                f"**{filled_or_cancelled}** explicitly indicate the position "
                "was filled or the process cancelled. These cannot automatically "
                "be interpreted as missing skills."
            )
            st.caption(
                f"{unknown} cases lack a disclosed specific reason. "
                "The inference review examines requirements, not private "
                "employer decision criteria."
            )

        st.subheader("When were negative outcomes communicated?")
        month_counts = Counter(
            (_date(r).strftime("%Y-%m") if _date(r) else "Undated",
             "Source date not verified" if
             str(r.get("decision_date_basis") or "") == "legacy_unclassified"
             else "Source-backed date")
            for r in scoped
        )
        monthly = [
            {"Month": month, "Date evidence": evidence, "Processes": count}
            for (month, evidence), count in month_counts.items()
        ]
        months = sorted({entry["Month"] for entry in monthly
                         if entry["Month"] != "Undated"})
        if any(entry["Month"] == "Undated" for entry in monthly):
            months.append("Undated")
        timeline = alt.Chart(alt.Data(values=monthly)).mark_bar().encode(
            x=alt.X("Month:N", sort=months, title="Observed / communicated month",
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Processes:Q", title="Negative outcomes",
                    axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("Date evidence:N", title="Date provenance"),
            tooltip=["Month:N", "Date evidence:N",
                     alt.Tooltip("Processes:Q", format=",d")],
        ).properties(height=220)
        st.altair_chart(timeline, use_container_width=True)
        unverifiable = sum(
            str(r.get("decision_date_basis") or "") == "legacy_unclassified"
            for r in scoped
        )
        st.caption(
            f"{unverifiable} of {n} outcome dates use legacy, unverified "
            "date provenance. The chart shows when outcomes were recorded "
            "or communicated, not when employers internally made their decisions."
        )
        recent_30 = sum(
            bool(_date(r) and today - timedelta(days=29) <= _date(r) <= today)
            for r in records
        )
        prior_30 = sum(
            bool(_date(r) and today - timedelta(days=59) <= _date(r)
                 < today - timedelta(days=29))
            for r in records
        )
        if prior_30 >= 10 and recent_30 >= 10:
            st.write(
                f"**Recorded decision volume:** {recent_30} in the latest 30 days "
                f"versus {prior_30} in the preceding 30 days. "
                "This reflects both applications and reporting coverage, "
                "not a change in your rejection probability."
            )
    with reasons:
        st.subheader("Which hiring barriers appear repeatedly?")
        _render_hiring_barrier_patterns(valid, scoped, research_hypotheses)
        st.divider()
        st.subheader("What employers actually disclosed")
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
        with st.expander(
            "Employer-reported causes and evidence-basis diagnostics",
            expanded=False,
        ):
            st.caption(
                "This historical view measures what employers disclosed or "
                "what was independently confirmed; UNKNOWN is not a barrier category."
            )
            # Exclude UNKNOWN from cause chart; disclose its count separately.
            disclosed = [
                r for r in scoped
                if str(r.get("reason_code") or "").upper() != "UNKNOWN"
            ]
            if disclosed:
                _chart(_reasons(disclosed), "Reason", "Processes",
                       color="Basis", height=260)
            else:
                st.caption("No specific recorded causes in this reporting window.")
            st.caption(
                f"{unknown} of {n} processes still have undisclosed employer motives. "
                "The barrier chart above assesses independent candidate–role evidence."
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Recorded reason confidence**")
                conf = Counter(str(r.get("confidence") or "unknown") for r in scoped)
                _chart([
                    {"Confidence": k, "Processes": v}
                    for k, v in sorted(conf.items())
                ], "Confidence", "Processes")
            with c2:
                st.markdown("**Where negative decisions cluster**")
                fam = Counter(family(str(r.get("role") or "")) for r in scoped)
                _chart([
                    {"Role family": k, "Processes": v}
                    for k, v in fam.most_common()
                ], "Role family", "Processes")
            st.caption(
                "Role family is inferred from titles, not original vacancy "
                "requirements. Counts are not application rejection rates."
            )
        with st.expander("Employer-specific findings and supporting interpretation",
                         expanded=False):
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
        render_rejection_inference(
            valid, scoped, sources=research_sources, hypotheses=research_hypotheses
        )
