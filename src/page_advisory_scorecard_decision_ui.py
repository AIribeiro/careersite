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

    if any("DEMONSTRATION ONLY" in caveat for caveat in report["caveats"]):
        st.warning(
            "DEMO — Fictional initiatives and financial assumptions. "
            "This is a test of decision logic, not an investment recommendation for a real company."
        )

    st.markdown("#### Recommended decision")
    st.markdown("**" + report["verdict"] + "**")
    if report["advanced_count"] + report["test_count"] == 0:
        st.error(
            "No initiative qualifies within the present evidence, control and "
            "resource conditions. Complete the missing assessments or review the "
            "planning envelope; do not issue a funding or deployment approval."
        )

    summary = report["recommended"]
    a,b,c = st.columns(3)
    a.metric("Business cases to review",report["advanced_count"])
    b.metric("Scoped tests to consider",report["test_count"])
    c.metric("Proposed initiatives",summary["count"])
    a,b,c = st.columns(3)
    a.metric("Capacity",f'{summary["fte_months"]:.1f} / {float(report["settings"]["capacity_fte_months"]):.1f} FTE-mo')
    b.metric("Planning investment",_money(summary["investment_sek"]))
    c.metric("Budget headroom",_money(summary["budget_headroom"]))
    st.caption(
        "Resource figures are the client-entered planning estimates, including "
        "full estimated investment for a test candidate; they are not verified "
        "pilot costs or approved allocations."
    )

    st.markdown("#### What to advance, test, hold or stop")
    headings = (
        ("Advance to business-case review", "Advance to business case",
         "Build a formal investment case; do not assume funding is approved."),
        ("Time-boxed evidence test", "Time-boxed test",
         "Prove a specific uncertainty with defined scope and a go/no-go gate."),
        ("Hold pending control review", "Hold - control review",
         "Resolve safeguards and specialist review before considering deployment."),
        ("Stop or redesign", "Stop / redesign",
         "The blocked control gate overrides the score."),
    )
    for heading, status, message in headings:
        rows=report["categories"].get(status,[])
        if not rows:
            continue
        st.markdown(f"**{heading} · {len(rows)}**")
        st.caption(message)
        for r in rows:
            with st.container(border=True):
                st.markdown(
                    f'**{r["name"]}** · {r["score"] if r["score"] is not None else "N/A"}/100'
                )
                st.write(r["rationale"])
                st.caption("Next action: " + r["next_action"])

    st.markdown("#### Three portfolio options")
    st.dataframe(_scenario_rows(report),hide_index=True,use_container_width=True)
    current = report["current_selection"]
    if not current["fits"]:
        st.error(
            "Your current selection exceeds at least one planning limit. "
            "The recommended candidate portfolio fits both configured limits."
            if summary["fits"] else
            "The current selection exceeds planning limits. "
            "No qualifying alternative could be fitted."
        )
    change=report["changes"]
    if change["added"]:
        st.write("**Add compared with your current selection:** "+
                 "; ".join(change["added"]))
    if change["removed"]:
        st.write("**Defer or remove from your current selection:** "+
                 "; ".join(change["removed"]))

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
