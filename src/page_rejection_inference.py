"""Private Rejection Analyzer v2 research coverage and causal-hypothesis review.

The module is imported only after the existing owner-session check in page_admin.
No public route, service-role key, or write operation is involved.
"""
from __future__ import annotations

from collections import Counter
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


def render_rejection_inference(session: dict, scoped: list[dict]) -> None:
    """Render on the authenticated owner's Rejection Analytics page only."""
    valid = ensure_owner_session(session)
    if not valid or not valid.get("access_token"):
        st.warning("Owner authentication is required for rejection research.")
        return
    try:
        token = str(valid["access_token"])
        sources = _private_rows(token, "job_rejection_external_evidence", EVIDENCE_FIELDS)
        hypotheses = _private_rows(token, "job_rejection_hypotheses", HYPOTHESIS_FIELDS)
    except (RuntimeError, TimeoutError, ValueError) as exc:
        st.warning(f"Rejection v2 research data are temporarily unavailable: {exc}")
        return

    by_id = {int(r["id"]): r for r in scoped if r.get("id") is not None}
    source_rows = [s for s in sources if int(s.get("rejection_id") or -1) in by_id]
    hyp_rows = [h for h in hypotheses if int(h.get("rejection_id") or -1) in by_id]
    exact = {int(e["rejection_id"]) for e in source_rows
             if e.get("review_status") == "reviewed" and
             e.get("match_strength") in ("exact_requisition", "verified_original_role")}
    before_decision = {int(e["rejection_id"]) for e in source_rows
        if e.get("review_status") == "reviewed"
        and isinstance(e.get("raw_context"), dict)
        and e["raw_context"].get("temporal_status") == "before_decision"
        and e.get("match_strength") in ("exact_requisition", "verified_original_role")}
    confirmed = sum(r.get("reason_basis") == "employer_stated" for r in scoped)
    medium_or_higher = {int(h["rejection_id"]) for h in hyp_rows
                        if h.get("assessment_state") == "supported_possible"
                        and h.get("confidence") in ("medium", "high")}
    weak = {int(h["rejection_id"]) for h in hyp_rows
            if h.get("assessment_state") == "weak_possible"}
    unknown = sum(str(r.get("reason_code") or "") == "UNKNOWN" for r in scoped)

    st.subheader("Research and competing explanations")
    st.caption(
        "Original vacancy research can establish a role requirement; it cannot "
        "establish what motivated an undisclosed employer decision. "
        "Confidence means evidential strength, never a probability of employer motive."
    )
    cols = st.columns(6)
    cols[0].metric("Employer-stated reasons", f"{confirmed}/{len(scoped)}")
    cols[1].metric("Exact role / ID match", len(exact))
    cols[2].metric("Pre-decision sources", len(before_decision))
    cols[3].metric("Supported hypotheses", len(medium_or_higher))
    cols[4].metric("Low-confidence leads", len(weak))
    cols[5].metric("Reasons still unknown", unknown)
    st.caption(
        "All metrics use distinct hiring-process counts within the selected window. "
        "Pre-decision sources explicitly document a prior posting; a later copy, exact "
        "requisition ID or unverified publication date is not proof of historic wording. "
        "Low-confidence leads do not count as supported explanations."
    )

    tab_sources, tab_hypotheses, tab_queue = st.tabs(
        ["Verified sources", "Competing explanations", "Research priorities"]
    )
    with tab_sources:
        if not source_rows:
            st.info("No source-linked external research in this reporting window.")
        else:
            rows = []
            for s in source_rows:
                r = by_id[int(s["rejection_id"])]
                rows.append({
                    "Employer": r.get("employer"), "Role": r.get("role"),
                    "Source match": str(s.get("match_strength") or "").replace("_", " "),
                    "Evidence claim": s.get("evidence_claim"),
                    "Published": s.get("source_published_at") or "Not verified",
                    "Source timing": (s.get("raw_context") or {}).get("temporal_status", "Not verified"),
                    "Limitation": s.get("limitations"), "Original source": s.get("source_url"),
                })
            st.dataframe(
                rows, hide_index=True, width="stretch",
                column_config={"Original source": st.column_config.LinkColumn("Original source")},
            )
            st.caption(
                "For reposted adverts, a matching requisition does not prove that "
                "the exact wording existed when the candidate applied."
            )

    with tab_hypotheses:
        if not hyp_rows:
            st.info("No saved competing hypotheses in this reporting window.")
        else:
            rows = []
            for h in sorted(hyp_rows, key=lambda v: (
                    by_id[int(v["rejection_id"])].get("employer") or "",
                    not bool(v.get("is_primary")), v.get("hypothesis_code") or "")):
                r = by_id[int(h["rejection_id"])]
                rows.append({
                    "Employer": r.get("employer"), "Role": r.get("role"),
                    "Hypothesis": h.get("hypothesis_code"),
                    "Status": str(h.get("assessment_state") or "").replace("_", " "),
                    "Confidence": h.get("confidence"),
                    "Explanation": h.get("explanation"),
                    "What argues against it": h.get("counterargument"),
                    "What is missing": h.get("limitation"),
                    "Next action": h.get("recommended_action") or "No justified action",
                })
            st.dataframe(rows, hide_index=True, width="stretch")
            st.caption(
                "Only explicit, specific employer feedback may be labelled confirmed. "
                "An UNKNOWN primary explanation can coexist with investigable alternatives."
            )

    with tab_queue:
        id_sources = Counter(int(e["rejection_id"]) for e in source_rows)
        id_hypotheses = Counter(int(h["rejection_id"]) for h in hyp_rows)
        # Operational queue ranking only; this is NOT a candidate-fit or causal score.
        pending = [
            r for r in scoped if str(r.get("reason_code") or "") == "UNKNOWN"
        ]
        pending.sort(key=lambda r: (
            int(int(r["id"]) in exact),
            -int(bool(r.get("requisition_id"))),
            -int(str(r.get("hiring_stage") or "") not in ("unknown", "unavailable")),
            -int(bool(r.get("cv_version"))),
            str(r.get("employer") or ""),
        ))
        st.caption(
            "Research exact requisitions first, recover original submitted CVs, then "
            "seek direct feedback from confirmed recruiter/interview interactions. "
            "Ranking reflects evidence-recovery potential, not predicted rejection cause."
        )
        rows = [{
            "Employer": r.get("employer"), "Role": r.get("role"),
            "Requisition": r.get("requisition_id") or "Missing",
            "Known stage": r.get("hiring_stage") or "Unknown",
            "JD": r.get("jd_match_status") or "Not checked",
            "CV evidence": "Version recorded" if r.get("cv_version") else "Not recorded",
            "External sources": id_sources[int(r["id"])],
            "Hypotheses": id_hypotheses[int(r["id"])],
        } for r in pending[:30]]
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        else:
            st.success("No unknown-cause records in this window.")
        st.caption(
            "Research does not run from this page; it displays verified records written "
            "by Rejection Analyzer v2. Automated scheduled checks require a separate task."
        )
