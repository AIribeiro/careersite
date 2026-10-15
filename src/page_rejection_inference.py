"""Private Rejection Analyzer v2 research coverage and causal-hypothesis review.

The module is imported only after the existing owner-session check in page_admin.
No public route, service-role key, or write operation is involved.
"""
from __future__ import annotations

from collections import Counter

import altair as alt
import streamlit as st

from site_cms import _request_json, _rest_url, ensure_owner_session


EVIDENCE_FIELDS = (
    "id,rejection_id,source_key,evidence_type,source_title,source_url,"
    "source_published_at,match_strength,matched_requisition,evidence_claim,"
    "limitations,review_status,observed_at,raw_context"
)
HYPOTHESIS_FIELDS = (
    "id,rejection_id,hypothesis_code,explanation,assessment_state,"
    "confidence,evidence_scope,support_evidence_ids,contrary_evidence_ids,"
    "direct_support_note,counterargument,limitation,actionability,"
    "recommended_action,is_primary,analyzed_at"
)


def _private_rows(token: str, table: str, fields: str) -> list[dict]:
    """All queried datasets have owner-only Supabase RLS; never use an anon key."""
    rows: list[dict] = []
    offset = 0
    while True:
        batch = _request_json(
            "GET", _rest_url(
                f"{table}?select={fields}&order=id.asc&limit=250&offset={offset}"
            ), token=token,
        )
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected private {table} response")
        rows.extend(batch)
        if len(batch) < 250:
            return rows
        offset += 250
        if offset >= 10000:
            raise RuntimeError(f"Unexpectedly large {table} response")


def render_rejection_inference(
    session: dict, scoped: list[dict], *,
    sources: list[dict] | None = None, hypotheses: list[dict] | None = None,
) -> None:
    """Show research maturity and decisions about next evidence gathering."""
    valid = ensure_owner_session(session)
    if not valid or not valid.get("access_token"):
        st.warning("Owner authentication is required for rejection research.")
        return
    # Normally data are passed from Rejection Analytics, preventing three
    # redundant owner-only queries. Keep older direct callers compatible.
    if sources is None or hypotheses is None:
        try:
            token = str(valid["access_token"])
            if sources is None:
                sources = _private_rows(
                    token, "job_rejection_external_evidence", EVIDENCE_FIELDS
                )
            if hypotheses is None:
                hypotheses = _private_rows(
                    token, "job_rejection_hypotheses", HYPOTHESIS_FIELDS
                )
        except (RuntimeError, TimeoutError, ValueError) as exc:
            st.warning(
                "Research evidence could not be loaded; canonical "
                f"decisions remain available. Details: {exc}"
            )
            return
    by_id = {
        int(row["id"]): row for row in scoped if row.get("id") is not None
    }
    source_rows = [
        row for row in sources
        if int(row.get("rejection_id") or -1) in by_id
    ]
    hyp_rows = [
        row for row in hypotheses
        if int(row.get("rejection_id") or -1) in by_id
    ]
    researched_ids = {
        int(row["rejection_id"]) for row in source_rows
    }
    exact_match_ids = {
        int(row["rejection_id"]) for row in source_rows
        if row.get("review_status") == "reviewed"
        and row.get("match_strength") in
        ("exact_requisition", "verified_original_role")
    }
    dated_original_ids = {
        int(row["rejection_id"]) for row in source_rows
        if row.get("review_status") == "reviewed"
        and row.get("match_strength") in
        ("exact_requisition", "verified_original_role")
        and isinstance(row.get("raw_context"), dict)
        and row["raw_context"].get("temporal_status") == "before_decision"
    }
    exact_date_open = exact_match_ids - dated_original_ids
    related_only = researched_ids - exact_match_ids
    not_researched = set(by_id) - researched_ids
    source_tiers = [
        {"Source maturity": "Original role + prior date verified",
         "Processes": len(dated_original_ids)},
        {"Source maturity": "Matched role; historical wording uncertain",
         "Processes": len(exact_date_open)},
        {"Source maturity": "Comparable/partial research only",
         "Processes": len(related_only)},
        {"Source maturity": "No saved external research",
         "Processes": len(not_researched)},
    ]
    st.subheader("How much of the original hiring context can we verify?")
    st.caption(
        "An exact requisition or role-title match is not proof that the same "
        "job requirements existed when the application was reviewed."
    )
    st.altair_chart(
        alt.Chart(alt.Data(values=source_tiers)).mark_bar(
            cornerRadiusEnd=4
        ).encode(
            y=alt.Y(
                "Source maturity:N", sort=[
                    "Original role + prior date verified",
                    "Matched role; historical wording uncertain",
                    "Comparable/partial research only",
                    "No saved external research",
                ],
                title=None, axis=alt.Axis(labelLimit=290),
            ),
            x=alt.X("Processes:Q", title="Distinct hiring processes",
                    axis=alt.Axis(tickMinStep=1)),
            tooltip=["Source maturity:N",
                     alt.Tooltip("Processes:Q", format=",d")],
        ).properties(height=225), use_container_width=True,
    )
    st.write(
        f"**{len(researched_ids)} of {len(scoped)}** outcomes have saved "
        f"external research, but only **{len(dated_original_ids)}** "
        "have source records explicitly verifying original-role content "
        "existed before the observed decision."
    )
    st.caption(
        "This refers to documentary evidence and timing, not proof "
        "of an employer's internal selection reasoning."
    )

    st.subheader("Which inference claims need challenge or further proof?")
    unknown_ids = {
        rid for rid, row in by_id.items()
        if str(row.get("reason_code") or "").upper() == "UNKNOWN"
    }
    usable = [
        h for h in hyp_rows
        if int(h.get("rejection_id") or -1) in unknown_ids
        and str(h.get("hypothesis_code") or "").upper() != "UNKNOWN"
    ]
    supported = {
        int(h["rejection_id"]) for h in usable
        if h.get("assessment_state") == "supported_possible"
    }
    weak = {
        int(h["rejection_id"]) for h in usable
        if h.get("assessment_state") in ("weak_possible", "investigating")
    } - supported
    ungrounded = unknown_ids - supported - weak
    rejected_hypothesis = {
        int(h["rejection_id"]) for h in usable
        if h.get("assessment_state") in ("not_supported", "contradicted")
    }
    first, second = st.columns([1.2, 1], vertical_alignment="center")
    with first:
        st.write(
            f"**{len(supported)} supported possible mismatches; "
            f"{len(weak)} tentative-only cases; "
            f"{len(ungrounded)} without a grounded candidate-side barrier.**"
        )
    with second:
        st.write(
            f"**{len(rejected_hypothesis)} cases** include a hypothesis "
            "that evidence contradicts or does not support."
        )
    st.caption(
        "Exclude ruled-out theories when advising on future applications. "
        "Multiple hypotheses can coexist for one decision, but they must "
        "not become multiple rejection records."
    )

    st.subheader("Where is the best next research opportunity?")
    pending = [
        row for row in scoped
        if str(row.get("reason_code") or "").upper() == "UNKNOWN"
    ]
    def rank(row: dict) -> tuple:
        rid = int(row["id"])
        stage = str(row.get("hiring_stage") or "").lower()
        is_interview = stage in (
            "recruiter_screen", "first_interview", "second_interview",
            "final_interview"
        )
        return (
            0 if is_interview else 1,
            0 if row.get("requisition_id") else 1,
            0 if rid not in dated_original_ids else 1,
            0 if rid not in supported else 1,
            str(row.get("employer") or ""),
        )
    pending.sort(key=rank)
    if pending:
        st.write(
            "Recover application-time vacancy requirements and interview "
            "chronology for interviewed or identifiable-requisition cases "
            "first. Recent reposts should not be used as historical facts."
        )
    else:
        st.caption("No unknown employer motives in the selected time window.")

    with st.expander("Investigate prioritized hiring processes", expanded=False):
        st.dataframe([
            {
                "Employer": row.get("employer"),
                "Role": row.get("role"),
                "Req ID": row.get("requisition_id") or "Not recorded",
                "Known stage": row.get("hiring_stage") or "Unknown",
                "JD": row.get("jd_match_status") or "Not checked",
                "Original source timed":
                    "Yes" if int(row["id"]) in dated_original_ids else "No",
                "Competing hypotheses": sum(
                    int(h.get("rejection_id") or -1) == int(row["id"])
                    and str(h.get("hypothesis_code") or "").upper() != "UNKNOWN"
                    for h in usable
                ),
            } for row in pending
        ], hide_index=True, width="stretch")
    with st.expander("Inspect source documents and historic limitations",
                     expanded=False):
        if not source_rows:
            st.caption("No externally saved source documents in this period.")
        else:
            st.dataframe([
                {
                    "Employer": by_id[int(row["rejection_id"])].get("employer"),
                    "Role": by_id[int(row["rejection_id"])].get("role"),
                    "Match strength": str(row.get("match_strength") or "").replace(
                        "_", " "
                    ),
                    "Timing": (row.get("raw_context") or {}).get(
                        "temporal_status", "Unverified"
                    ),
                    "Evidence": row.get("evidence_claim"),
                    "Limitations": row.get("limitations"),
                    "Source": row.get("source_url"),
                } for row in source_rows
            ], hide_index=True, width="stretch",
               column_config={"Source": st.column_config.LinkColumn("Source")})
    with st.expander("Inspect competing hypotheses and counterevidence",
                     expanded=False):
        if not usable:
            st.caption("No documented alternative explanations in this selection.")
        else:
            st.dataframe([
                {
                    "Employer": by_id[int(h["rejection_id"])].get("employer"),
                    "Role": by_id[int(h["rejection_id"])].get("role"),
                    "Hypothesis": h.get("hypothesis_code"),
                    "Evidence strength": str(
                        h.get("assessment_state") or ""
                    ).replace("_", " "),
                    "Confidence": h.get("confidence"),
                    "Explanation": h.get("explanation"),
                    "Against it": h.get("counterargument"),
                    "Unresolved": h.get("limitation"),
                    "Next evidence": h.get("recommended_action"),
                } for h in usable
            ], hide_index=True, width="stretch")
    st.caption(
        "Saved research is read-only here. Running Rejection Analyzer is "
        "a separate deliberate action; this page does not claim continuous "
        "mailbox monitoring."
    )
