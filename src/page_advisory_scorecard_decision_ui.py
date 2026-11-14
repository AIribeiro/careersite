"""Executive-first, private online Scorecard recommendation and downloadable memo."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from page_advisory_scorecard_decision import recommend
from page_advisory_scorecard_report import build_executive_pdf


def _money(amount: float) -> str:
    return f"{amount:,.0f} SEK"


def _outcome_rows(report: dict) -> list[dict]:
    return [
        {
            "Initiative": r["name"],
            "Recommendation": r["recommendation"],
            "Score": r["score"],
            "Evidence": r["evidence"],
            "Control": r["gate"],
            "Reason": r["rationale"],
            "Required next step": r["next_action"],
        }
        for r in sorted(report["rows"], key=lambda x: (
            0 if x["included_in_proposal"] else 1,
            -(x["score"] or 0), x["name"].casefold(),
        ))
    ]


def _scenario_rows(report: dict) -> list[dict]:
    scenarios = (
        ("Recommended constrained portfolio", report["recommended"]),
        ("Lower-commitment / business cases only", report["conservative"]),
        ("Client's current proposal", report["current_selection"]),
    )
    return [
        {
            "Portfolio option": name,
            "Initiatives": x["count"],
            "FTE-months": x["fte_months"],
            "Investment SEK": x["investment_sek"],
            "FTE headroom": x["fte_headroom"],
            "Budget headroom SEK": x["budget_headroom"],
            "Within limits?": "Yes" if x["fits"] else "No",
        }
        for name, x in scenarios
    ]


def render_executive_recommendation(data: dict, workspace: dict, *,
                                    token: str, uid: str,
                                    feedback_rows: list[dict] | None = None) -> None:
    report = recommend(
        data,
        revision=int(workspace.get("revision") or 0),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
    st.markdown("### Executive portfolio recommendation")
    st.caption(
        "Decision-ready analysis of the current Scorecard revision. "
        "Recommendations are generated from your own assessments, "
        "subject to explicit evidence and control requirements."
    )
    if not report["rows"]:
        st.info(
            "Enter an AI initiative in the Initiatives tab to generate "
            "an executive portfolio decision."
        )
        return

    st.markdown("#### Recommended decision")
    st.markdown("**" + report["verdict"] + "**")
    if report["advanced_count"] + report["test_count"] == 0:
        st.error(
            "No initiative currently meets the evidence, control and "
            "resource requirements. Resolve the missing inputs or review "
            "the planning limits before authorizing further work."
        )

    summary = report["recommended"]
    a, b, c = st.columns(3)
    a.metric("Business cases to review", report["advanced_count"])
    b.metric("Evidence tests to scope", report["test_count"])
    c.metric("Recommended portfolio", summary["count"])
    a, b, c = st.columns(3)
    a.metric(
        "Capacity",
        f'{summary["fte_months"]:.1f} / '
        f'{float(report["settings"]["capacity_fte_months"]):.1f} FTE-mo'
    )
    b.metric("Planning investment", _money(summary["investment_sek"]))
    c.metric("Budget headroom", _money(summary["budget_headroom"]))
    st.caption(
        "Amounts and resource requirements are based on the current "
        "client-entered estimates. A recommendation is not an approval."
    )

    st.markdown("#### Executive action plan")
    advances = report["categories"].get("Advance to business case", [])
    tests = report["categories"].get("Time-boxed test", [])
    holds = report["categories"].get("Hold - control review", [])
    blocked = report["categories"].get("Stop / redesign", [])
    a, b, c = st.columns(3)
    with a:
        with st.container(border=True):
            st.markdown("**01 · Commission business cases**")
            st.write(
                f"{len(advances)} initiative(s). Validate benefit baselines, "
                "sponsorship and the financial case before requesting investment."
                if advances else
                "No initiative qualifies for business-case review yet."
            )
    with b:
        with st.container(border=True):
            st.markdown("**02 · Define the evidence test**")
            st.write(
                f"{tests[0]['name']}: agree success criteria, scope and a "
                "go/no-go checkpoint."
                if tests else
                "No candidate currently qualifies for a scoped test."
            )
    with c:
        with st.container(border=True):
            st.markdown("**03 · Resolve control decisions**")
            st.write(
                f"{len(holds)} held for review; {len(blocked)} blocked. "
                "Clear the necessary reviews before reconsidering them."
                if holds or blocked else
                "No current control holds in the assessment."
            )

    st.markdown("#### Prioritized recommendations")
    included = sorted(
        [r for r in report["rows"] if r["included_in_proposal"]],
        key=lambda r: (
            r["recommendation"] != "Advance to business case",
            -(r["score"] or 0),
            r["name"],
        ),
    )
    if included:
        st.dataframe(
            [
                {
                    "Recommended route": r["recommendation"],
                    "Initiative": r["name"],
                    "Business owner": r["owner"] or "Not recorded",
                    "Score": r["score"],
                    "Why this route": r["rationale"],
                    "Required next step": r["next_action"],
                } for r in included
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No eligible portfolio can be selected under the current conditions.")

    excluded = [
        r for r in report["rows"] if not r["included_in_proposal"]
    ]
    if excluded:
        st.markdown("#### Hold, redesign and defer")
        st.dataframe(
            [
                {
                    "Initiative": r["name"],
                    "Decision": r["recommendation"],
                    "Accountable owner": r["owner"] or "Not recorded",
                    "Next condition": r["next_action"],
                } for r in excluded
            ],
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("#### Portfolio alternatives and trade-offs")
    st.dataframe(
        _scenario_rows(report), hide_index=True, use_container_width=True
    )
    current = report["current_selection"]
    if not current["fits"]:
        st.error(
            "Your current selection exceeds at least one planning limit. "
            "The recommended portfolio fits both constraints."
            if summary["fits"] else
            "Your current selection exceeds planning limits. "
            "No eligible alternative fits the current constraints."
        )
    changes = report["changes"]
    if changes["added"]:
        st.write(
            "**Add versus current proposal:** " + "; ".join(changes["added"])
        )
    if changes["removed"]:
        st.write(
            "**Hold or remove versus current proposal:** "
            + "; ".join(changes["removed"])
        )
    st.caption(
        "Take the proposal to the portfolio decision forum. Confirm accountable "
        "sponsors, control conditions, resource commitments and the next review. "
        "Record the formal outcome separately in the Decision record tab."
    )

    with st.expander("All initiatives: verdict, rationale and required next evidence"):
        st.dataframe(_outcome_rows(report),hide_index=True,use_container_width=True)

    with st.expander("Method, assumptions and limitations"):
        st.write(
            "First select the highest cumulative weighted-priority business-case "
            "candidates with passed controls and Medium/High evidence, using both "
            "the capacity and budget limits. Then, from remaining capacity, "
            "consider up to the configured number of evidence-building tests. "
            "A control gate marked Review or Block cannot be overridden by a score."
        )
        st.caption(
            "Selection method: "+report["selection_method"]+
            ". Financial benefit estimates are shown for context, not independently "
            "verified and not a driver of the ranking. Scores are comparative, "
            "not probability of success. A test allocation uses the same full "
            "one-time investment estimate until a scoped test budget is supplied."
        )
        for caveat in report["caveats"]:
            st.write("- "+caveat)

    st.markdown("#### Executive decision report")
    st.write(
        "Download a confidential A4 decision memo with the recommended portfolio, "
        "initiative-level rationale, alternatives, constraints, next evidence and "
        "conditions for executive sign-off."
    )
    pdf_key = "scorecard_report_download_clicked_" + str(workspace["id"])
    try:
        pdf=build_executive_pdf(report)
    except Exception:
        st.error(
            "The executive PDF could not be generated in this session. "
            "Your Scorecard inputs and on-screen recommendation remain available."
        )
        pdf=None
    if pdf is not None:
        st.download_button(
            "Download executive decision report (PDF)",
            data=pdf,
            file_name="AI_Portfolio_Executive_Decision_Rev_"+str(workspace.get("revision") or 0)+".pdf",
            mime="application/pdf",
            type="primary",
            on_click=lambda key=pdf_key: st.session_state.__setitem__(key,True),
            use_container_width=False,
        )
    st.caption(
        "Export is available without providing feedback. "
        "The report represents the current revision only. "
        "It does not authorize investment, execution or use of sensitive data."
    )
    if token and uid and feedback_rows is not None and report["rows"]:
        from page_advisory_service_feedback import (
            SCORECARD_SERVICE,render_optional_feedback,
        )
        # The full, actionable recommendation is already visible above.
        render_optional_feedback(
            token,uid,SCORECARD_SERVICE,"executive_recommendation",
            request_id=str(workspace["request_id"]),
            scorecard_id=str(workspace["id"]),
            feedback_rows=feedback_rows,
        )
        if st.session_state.get(pdf_key):
            render_optional_feedback(
                token,uid,SCORECARD_SERVICE,"report_download",
                request_id=str(workspace["request_id"]),
                scorecard_id=str(workspace["id"]),
                feedback_rows=feedback_rows,
            )
