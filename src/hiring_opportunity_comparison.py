"""Compact, accessible, evidence-first comparison of active hiring processes.

HTML is escaped because employer and role labels come from recruiting records.
This is a presentation layer: it must not infer new hiring stages or probabilities.
"""
from __future__ import annotations

from datetime import date
from html import escape
from math import isfinite

from meeting_to_offer import estimate_mto


def opportunity_evidence_score(process: dict) -> float | None:
    """Return a finite 0–100 process credibility index; never invent a missing score."""
    raw = process.get("credibility_index")
    if raw is None or isinstance(raw, bool):
        return None
    try:
        score = float(raw)
    except (ValueError, TypeError, OverflowError):
        return None
    if not isfinite(score):
        return None
    return min(100.0, max(0.0, score))


def _stage_tone(stage: str) -> str:
    if stage == "verified_offer":
        return "offer"
    if stage.startswith("subsequent_interview"):
        return "later"
    if stage.startswith("first_interview"):
        return "first"
    return "early"


def _mark_for_employer(name: str) -> tuple[str, str]:
    key = name.casefold()
    if "leovegas" in key:
        return "LV", "leo"
    if "kpmg" in key:
        return "K", "kpmg"
    if "betsson" in key:
        return "B", "betsson"
    if "skillhuset" in key:
        return "S", "skill"
    letters = [word[0] for word in name.split() if word and word[0].isalpha()]
    return "".join(letters[:2]).upper() or "•", "neutral"


# MTO is estimated from role family and recorded interviewer authority.
# The shared estimator intentionally has no employer-name exceptions.
def meetings_to_offer_estimate(process: dict) -> tuple[int, int, str]:
    """Backward-compatible role-baseline accessor; see estimate_mto for evidence."""
    result = estimate_mto(process)
    return result.total_low, result.total_high, result.explanation


def _meeting_progress_html(
    process: dict,
    meeting_counts: dict[str, int] | None,
    meeting_details: dict[str, list[dict]] | None = None,
    process_plans: dict[str, dict] | None = None,
) -> str:
    key = str(process.get("process_key") or "").strip().casefold()
    if meeting_counts is None:
        count = None  # The ledger could not be loaded.
    elif key in meeting_counts:
        count = meeting_counts[key]
    elif str(process.get("stage") or "").endswith("interview_completed"):
        count = None  # Do not silently reconcile disparate evidence.
    else:
        count = 0
    estimate = estimate_mto(
        process, completed=count,
        meetings=(meeting_details or {}).get(key),
        employer_plan=(process_plans or {}).get(key),
    )
    low, high = estimate.total_low, estimate.total_high
    completed_label = "— verified" if count is None else f"{count} held" if count else "0 verified"
    range_label = f"~{low}–{high}" if low != high else f"~{low}"
    remaining = (
        "Remaining unknown" if estimate.remaining_low is None
        else f"{estimate.remaining_low}–{estimate.remaining_high} remaining"
        if estimate.remaining_low != estimate.remaining_high
        else f"{estimate.remaining_low} remaining"
    )
    explanation = (
        f"Meetings to offer (MTO): {low}–{high} estimated total meetings, "
        f"including {completed_label}. {remaining}. "
        f"Evidence: {estimate.evidence_level.replace('_', ' ')}; "
        f"confidence: {estimate.confidence}. {estimate.explanation} "
        "Cancellations, invitations, assessments and follow-up emails do not count."
    )
    return (
        f'<span class="op-compare__mto" title="{escape(explanation, quote=True)}" '
        f'aria-label="{escape(explanation, quote=True)}">'
        f'<strong>{escape(completed_label)}</strong> <span aria-hidden="true">/</span> '
        f'MTO {escape(range_label)}'
        f'<span class="op-compare__mto-more"> · {escape(remaining)}</span></span>'
    )


def _next_interview_label(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        human = date.fromisoformat(value).strftime("%d %b %Y")
    except ValueError:
        return ""
    return f'<span class="op-next">Confirmed next interview · {escape(human)}</span>'


# Scoped styles avoid changing other Streamlit and portfolio analytics sections.
_COMPARISON_STYLE = """
<style>
.op-compare{margin:.8rem 0 .45rem;background:#fff;border:1px solid #e2e6ec;border-radius:16px;overflow:hidden;box-shadow:0 6px 28px rgba(20,30,50,.045);color:#182036;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Arial,sans-serif}
.op-compare *{box-sizing:border-box}
.op-compare__intro{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:18px 20px 15px}
.op-compare__title{margin:0!important;color:#141b31!important;font-size:1.11rem!important;line-height:1.26!important;font-weight:750!important;letter-spacing:-.02em}
.op-compare__detail{margin:4px 0 0!important;color:#69758a!important;font-size:.79rem!important;line-height:1.35!important}
.op-compare__count{white-space:nowrap;border:1px solid #e5e9f0;border-radius:999px;background:#f5f7fa;padding:5px 10px;font-size:.73rem;font-weight:700;color:#526078}
.op-compare__table{width:100%}
.op-compare__head,.op-compare__row{display:grid;grid-template-columns:32px minmax(0,2fr) minmax(142px,1.1fr) 86px minmax(125px,1fr);column-gap:15px;align-items:center;padding-left:18px;padding-right:18px}
.op-compare__head{min-height:35px;background:#f7f8fb;border-top:1px solid #edf0f5;border-bottom:1px solid #edf0f5;font-size:.64rem;letter-spacing:.065em;text-transform:uppercase;color:#788298;font-weight:800}
.op-compare__row{min-height:74px;padding-top:11px;padding-bottom:11px;border-bottom:1px solid #edf0f4}
.op-compare__row:last-child{border-bottom:0}
.op-compare__row:hover{background:#fbfcfe}
.op-compare__rank{display:grid;place-items:center;width:27px;height:27px;border-radius:50%;background:#eff2f6;color:#586479;font-size:.75rem;font-weight:800;font-variant-numeric:tabular-nums}
.op-compare__row:first-of-type .op-compare__rank{color:#b85a2c;background:#fff0e7}
.op-compare__identity{display:flex;align-items:center;min-width:0;gap:11px}
.op-compare__mark{flex:0 0 35px;width:35px;height:35px;display:grid;place-items:center;border-radius:9px;border:1px solid #e3e8ef;background:#f2f4f8;color:#333e56;font-size:.73rem;font-weight:850;letter-spacing:-.035em}
.op-compare__mark--leo{background:#fff0e8;color:#cf5b24;border-color:#ffdcc9}
.op-compare__mark--kpmg{background:#eaf2ff;color:#2056b6;border-color:#d9e7fc}
.op-compare__mark--betsson{background:#fff1e5;color:#de6517;border-color:#ffe1ca}
.op-compare__mark--skill{background:#eef0f4;color:#253451}
.op-compare__employer{display:block;font-size:.83rem;line-height:1.25;font-weight:780;color:#182036;overflow-wrap:anywhere}
.op-compare__role{display:block;margin-top:3px;font-size:.73rem;line-height:1.3;color:#67758b;overflow-wrap:anywhere}
.op-compare__stage{display:block;min-width:0}
.op-compare__pill{display:inline-flex;align-items:flex-start;gap:7px;max-width:100%;border-radius:8px;padding:7px 9px;border:1px solid #ebeef2;background:#f2f4f7;color:#657186;font-size:.71rem;font-weight:700;line-height:1.25}
.op-compare__dot{display:inline-block;flex:0 0 7px;width:7px;height:7px;border-radius:50%;margin-top:3px;background:currentColor}
.op-compare__pill--later{background:#fff0e8;border-color:#ffe3d2;color:#bc5c2c}
.op-compare__pill--first{background:#eaf3ff;border-color:#dae9fc;color:#235da5}
.op-compare__pill--offer{background:#e7f6eb;border-color:#c9ead2;color:#287543}
.op-next{display:block;margin-top:4px;color:#69778b;font-size:.66rem;line-height:1.25}
.op-compare__mto{display:block;margin-top:5px;color:#718095;font-size:.66rem;line-height:1.3;white-space:normal;font-variant-numeric:tabular-nums}
.op-compare__mto strong{font-weight:750;color:#34455c}
.op-compare__mto-more{color:#8793a3;font-size:.64rem}
.op-compare__score{white-space:nowrap;font-variant-numeric:tabular-nums}
.op-compare__number{font-size:1.12rem;line-height:1.1;font-weight:800;color:#17203a;letter-spacing:-.025em}
.op-compare__denominator{margin-left:3px;font-size:.72rem;color:#8190a2}
.op-compare__track{height:9px;width:100%;border-radius:999px;background:#edf0f4;overflow:hidden}
.op-compare__fill{height:100%;min-width:0;background:linear-gradient(90deg,#c25d2d,#eb7a38);border-radius:999px}
.op-compare__missing{font-size:.75rem;color:#8691a0}
@media(max-width:760px){
 .op-compare__intro{padding:15px 14px;align-items:flex-start}
 .op-compare__title{font-size:1rem!important}
 .op-compare__detail{font-size:.7rem!important}
 .op-compare__head{display:none}
 .op-compare__row{grid-template-columns:29px minmax(0,1fr) 79px;grid-template-areas:"rank identity score" ". stage stage" ". bar bar";column-gap:9px;row-gap:7px;padding:12px 13px;min-height:0}
 .op-compare__rank{grid-area:rank}
 .op-compare__identity{grid-area:identity;gap:8px}
 .op-compare__mark{flex-basis:30px;width:30px;height:30px}
 .op-compare__stage{grid-area:stage}
 .op-compare__score{grid-area:score;text-align:right}
 .op-compare__bar{grid-area:bar}
 .op-compare__number{font-size:1rem}
 .op-compare__track{height:7px}
 .op-compare__count{font-size:.64rem;padding:5px 7px}
}
@media(prefers-reduced-motion:reduce){.op-compare *{transition:none!important;animation:none!important}}
</style>
"""


def opportunity_comparison_html(processes: list[dict], stage_names: dict[str, str], meeting_counts: dict[str, int] | None = None, meeting_details: dict[str, list[dict]] | None = None, process_plans: dict[str, dict] | None = None) -> str:
    """Build ranked rows from the supplied live forecast without static company scores."""
    rows: list[str] = []
    for position, process in enumerate(processes, 1):
        company = str(process.get("employer") or "Employer not recorded")
        role = str(process.get("role") or "Role not recorded")
        stage = str(process.get("stage") or "")
        stage_title = stage_names.get(stage, stage.replace("_", " ").capitalize() or "Unverified")
        tone = _stage_tone(stage)
        mark, mark_tone = _mark_for_employer(company)
        score = opportunity_evidence_score(process)
        if score is None:
            score_html = '<span class="op-compare__missing">Not scored</span>'
            bar_html = '<div class="op-compare__track" aria-label="No verified score"></div>'
        else:
            score_html = (
                f'<span class="op-compare__number">{score:.1f}</span>'
                '<span class="op-compare__denominator">/ 100</span>'
            )
            bar_html = (
                f'<div class="op-compare__track" role="progressbar" '
                f'aria-label="Evidence strength for {escape(company, quote=True)}" '
                f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score:.1f}">'
                f'<div class="op-compare__fill" style="width:{score:.1f}%"></div>'
                '</div>'
            )
        rows.append(
            '<div class="op-compare__row" role="row">'
            f'<span class="op-compare__rank" role="cell">{position}</span>'
            '<div class="op-compare__identity" role="cell">'
            f'<span class="op-compare__mark op-compare__mark--{mark_tone}" aria-hidden="true">{escape(mark)}</span>'
            '<div>'
            f'<span class="op-compare__employer">{escape(company)}</span>'
            f'<span class="op-compare__role">{escape(role)}</span>'
            '</div></div>'
            '<div class="op-compare__stage" role="cell">'
            f'<span class="op-compare__pill op-compare__pill--{tone}">'
            '<span class="op-compare__dot" aria-hidden="true"></span>'
            f'<span>{escape(stage_title)}</span></span>'
            f'{_next_interview_label(process.get("next_interview"))}'
            f'{_meeting_progress_html(process, meeting_counts, meeting_details, process_plans)}'
            '</div>'
            f'<div class="op-compare__score" role="cell">{score_html}</div>'
            f'<div class="op-compare__bar" role="cell">{bar_html}</div>'
            '</div>'
        )
    count = len(rows)
    return (
        _COMPARISON_STYLE
        + '<section class="op-compare" aria-label="Current hiring opportunities">'
        + '<div class="op-compare__intro"><div>'
        + '<h3 class="op-compare__title">Where current opportunities stand</h3>'
        + '<p class="op-compare__detail">Compare verified hiring stages, interview meetings and evidence strength.</p>'
        + '</div>'
        + f'<span class="op-compare__count">{count} active {"process" if count == 1 else "processes"}</span>'
        + '</div>'
        + '<div class="op-compare__table" role="table" aria-label="Ranked active hiring processes">'
        + '<div class="op-compare__head" role="row">'
        + '<span role="columnheader">#</span><span role="columnheader">Company &amp; role</span>'
        + '<span role="columnheader">Stage</span>'
        + '<span role="columnheader">Evidence strength</span>'
        + '<span role="columnheader">Progress</span></div>'
        + "".join(rows)
        + '</div></section>'
    )
