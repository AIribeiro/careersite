"""Privacy-safe interpretation of coarse rejection aggregates shown in public Analytics.

The source is a thresholded SQL RPC. No employer, process, mailbox or JD row
is ever read from the public application.
"""
from __future__ import annotations


def rejection_overview_readout(report: dict) -> dict:
    """Describe what the evidence supports without inferring individual causes."""
    if report.get("available") is not True:
        return {"status": "unavailable", "message": "Rejection evidence is not available as a public aggregate."}

    total = max(0, int(report.get("analyzed_processes") or 0))
    unknown = min(total, max(0, int(report.get("unknown_causes") or 0)))
    confirmed = min(total, max(0, int(report.get("confirmed_explanations") or 0)))
    dates_missing = min(total, max(0, int(report.get("undated_decisions") or 0)))
    stage_missing = min(total, max(0, int(report.get("unknown_stages") or 0)))
    verified_jds = min(total, max(0, int(report.get("verified_jds") or 0)))
    if total < 20:
        return {"status": "unavailable", "message": "Too few distinct negative hiring processes for a public interpretation."}

    unknown_share = unknown / total
    confirmed_share = confirmed / total
    dated_coverage = (total - dates_missing) / total

    if unknown_share >= 0.70:
        interpretation = (
            "Most negative hiring decisions do not disclose why the employer decided as it did. "
            "They cannot establish a recurring capability gap or justify broad CV changes."
        )
        action = (
            "Keep targeting credible AI/Data leadership mandates. Request specific feedback "
            "after substantive recruiter and interview conversations before changing positioning."
        )
        strength = "Evidence limitation is dominant"
    elif confirmed_share >= 0.30 and unknown_share <= 0.40:
        interpretation = (
            "More decisions now have confirmed explanations. The underlying reasons still need "
            "to be compared across roles before treating them as a repeated pattern."
        )
        action = (
            "Review recurring employer-stated reasons in the private report; change targeting "
            "only when independent examples support the same requirement."
        )
        strength = "Better explanation coverage"
    else:
        interpretation = (
            "Some negative decisions have explanations, but the evidence remains mixed. "
            "A selection decision alone does not establish a gap."
        )
        action = (
            "Review directly supported repeated reasons and seek feedback on unexplained "
            "late-stage outcomes. Avoid attributing unknown decisions to qualifications."
        )
        strength = "Mixed explanation coverage"

    cautions: list[str] = []
    if stage_missing / total > 0.50:
        cautions.append(f"{stage_missing} processes lack a known hiring stage")
    if dated_coverage < 0.80:
        cautions.append(f"{dates_missing} decisions have no verified date")
    if verified_jds == 0:
        cautions.append("no job descriptions pass strict verification")
    return {
        "status": "ok",
        "interpretation": interpretation,
        "action": action,
        "evidence_status": strength,
        "cautions": cautions,
        "unknown_share": unknown_share,
        "confirmed_share": confirmed_share,
        "total": total,
    }
