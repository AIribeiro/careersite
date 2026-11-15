"""Public and private Executive AI Investment Decision Advisor.

The public page uses the portfolio's shared design. The authenticated service
reuses the existing Advisory account and its Supabase JWT, with per-user RLS.
"""
from __future__ import annotations

from html import escape
from urllib.parse import quote
from datetime import datetime, timezone

import streamlit as st

from page_advisory_investment_logic import FIELDS, MODEL_VERSION, assess, validate
from page_advisory_investment_experience import present_assessment, categorize_evidence
from page_public_services import SERVICES_CSS
from page_advisory_scorecard import SCORECARD_CSS
from site_components import nav, footer
from site_cms import _request_json, _rest_url


SERVICE_CSS = """
<style>
.site .investment-product .sc-hero{background:linear-gradient(118deg,#0c2034 0%,#182e42 75%,#233f54 100%)}
.site .investment-product .investment-eyebrow{font:700 11px Arial,sans-serif;letter-spacing:.14em;color:#e5b58f}
.site .investment-product .investment-decision{border-left:3px solid #e5b58f;padding:18px 24px;background:#233e55;max-width:680px;margin:28px 0}
.site .investment-product .investment-decision b{font:500 26px Georgia,serif;color:#fff}
.site .investment-product .investment-decision p{margin:9px 0 0;color:#d2dfe7;font-size:14px}
.site .investment-product .investment-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:25px 0}
.site .investment-product .investment-steps article{border:1px solid #dedbd5;background:#fff;padding:26px}
.site .investment-product .investment-steps small{color:#aa714e;font-weight:700;letter-spacing:.08em}
.site .investment-product .investment-steps h3{margin:11px 0 9px}
.site .investment-product .investment-steps p{font-size:14px;margin:0}
.site .investment-product .investment-auth{background:#fff;border:1px solid #ddd8d0;padding:26px 28px}
.site .investment-product .investment-auth h3{margin:0 0 10px}
@media(max-width:760px){.site .investment-product .investment-steps{grid-template-columns:1fr}.site .investment-product .investment-auth{padding:22px}}
</style>
"""
PRIVATE_CSS = """
<style>
.st-key-investment_decision_area{
 --inv-navy:#10273c;--inv-ink:#223a4e;--inv-mute:#586b78;
 --inv-copper:#ad7754;--inv-paper:#fbfaf7;--inv-rule:#e1e5e6;
}
.st-key-investment_decision_area .inv-hero{
 padding:29px 31px;background:linear-gradient(115deg,#10273c 0%,#203b52 100%);
 border:1px solid #283f51;color:#fff;margin:3px 0 18px
}
.st-key-investment_decision_area .inv-eyebrow{
 font:750 10px/1.5 Arial,sans-serif;letter-spacing:.17em;color:var(--inv-copper);
 text-transform:uppercase
}
.st-key-investment_decision_area .inv-hero .inv-eyebrow{color:#e5b38e}
.st-key-investment_decision_area .inv-hero h2{
 color:#fff;font:500 clamp(26px,3vw,38px)/1.15 Georgia,serif;margin:10px 0 9px;
}
.st-key-investment_decision_area .inv-hero p{
 color:#d5e1e9;max-width:780px;font-size:14px;line-height:1.7;margin:0
}
.st-key-investment_decision_area .inv-context{
 background:#f5f2ec;border-left:3px solid #ad7754;padding:15px 19px;
 margin:15px 0 21px
}
.st-key-investment_decision_area .inv-context strong{
 color:#142f45;font:500 clamp(18px,2vw,24px)/1.25 Georgia,serif;
 display:block;margin:5px 0
}
.st-key-investment_decision_area .inv-context p{font-size:12px;color:#586b78;margin:0}
.st-key-investment_decision_area [data-testid="stPills"]{
 padding:7px;background:#f1f0ec;border:1px solid #e5ded4;
 margin:0 0 17px
}
.st-key-investment_decision_area [data-testid="stPills"] button{
 min-height:42px;font-weight:700
}
.st-key-investment_decision_area .inv-decision{
 background:#fff;border:1px solid #dddfe0;border-top:4px solid #ad7754;
 padding:28px 30px;margin-bottom:17px;color:#263f52
}
.st-key-investment_decision_area .inv-decision h3{
 font:500 clamp(24px,3vw,33px)/1.22 Georgia,serif;color:#163047;margin:8px 0 15px
}
.st-key-investment_decision_area .inv-decision .inv-verdict{
 font:750 clamp(29px,4vw,44px)/1.1 Arial,sans-serif;color:#12314b;
 letter-spacing:.035em;margin:14px 0 10px
}
.st-key-investment_decision_area .inv-decision p{
 font-size:14px;line-height:1.76;color:#42596a;margin:8px 0
}
.st-key-investment_decision_area .inv-rail{
 display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:14px 0 21px
}
.st-key-investment_decision_area .inv-rail article{
 padding:16px;background:#f6f4ef;border:1px solid #e4dfd7;min-width:0
}
.st-key-investment_decision_area .inv-rail small{
 color:#966c52;font:750 9px/1.5 Arial,sans-serif;letter-spacing:.09em;
 text-transform:uppercase;display:block
}
.st-key-investment_decision_area .inv-rail strong{
 display:block;font:700 13px/1.5 Arial,sans-serif;color:#223c50;margin-top:6px
}
.st-key-investment_decision_area .inv-section-title{
 margin:20px 0 12px;color:#173047;font:500 clamp(21px,2.5vw,28px)/1.25 Georgia,serif
}
.st-key-investment_decision_area .inv-action{
 border:1px solid #deddd7;background:#fff;margin:13px 0;padding:22px 24px;
 border-left:3px solid #ad7754
}
.st-key-investment_decision_area .inv-action h4{
 margin:9px 0 11px;font:650 16px/1.5 Arial,sans-serif;color:#203c52
}
.st-key-investment_decision_area .inv-action .inv-proof{
 background:#f5f7f8;padding:12px 14px;color:#243d50;font-size:13px;
 line-height:1.6;margin-top:13px
}
.st-key-investment_decision_area .inv-action p{
 color:#5b6a78;font-size:13px;margin:7px 0
}
.st-key-investment_decision_area .inv-evidence{
 display:grid;grid-template-columns:minmax(160px,.42fr) minmax(0,1fr);
 padding:12px 0;border-bottom:1px solid #e2e4e6;gap:18px
}
.st-key-investment_decision_area .inv-evidence b{font-size:12px;color:#273d4f}
.st-key-investment_decision_area .inv-evidence span{font-size:13px;color:#536878}
.st-key-investment_decision_area .inv-note{
 padding:16px 20px;background:#f5f2ec;border-left:3px solid #b78965;
 font-size:13px;line-height:1.7;color:#3d5061;margin:12px 0
}
.st-key-investment_decision_area .inv-history-intro{
 background:#fff;border:1px solid #e0ded7;padding:20px 23px;margin-bottom:16px
}
.st-key-investment_decision_area .inv-history-intro p{
 font-size:14px;color:#5a6977;line-height:1.7;margin:7px 0 0
}
.st-key-investment_decision_area .inv-case-item{
 border-bottom:1px solid #dedbd5;padding:4px 0 10px;margin:3px 0 5px
}
.st-key-investment_decision_area .inv-case-item strong{
 color:#173047;font:500 21px/1.3 Georgia,serif;display:block;margin:4px 0 6px
}
.st-key-investment_decision_area .inv-case-item p{
 font-size:13px;color:#596d7a;margin:5px 0
}
.st-key-investment_decision_area .inv-case-tags{
 display:flex;flex-wrap:wrap;gap:8px;margin:11px 0 8px
}
.st-key-investment_decision_area .inv-case-tags span{
 padding:6px 10px;border:1px solid #dcd9d2;background:#f5f2eb;
 font:700 11px/1.3 Arial,sans-serif;color:#243e53
}
.st-key-investment_decision_area [data-testid="stForm"]{
 background:#fffdfa;border:1px solid #e0dbd2;padding:15px
}
@media(max-width:700px){
 .st-key-investment_decision_area .inv-hero{padding:23px 20px}
 .st-key-investment_decision_area .inv-decision{padding:21px 19px}
 .st-key-investment_decision_area .inv-rail{grid-template-columns:1fr}
 .st-key-investment_decision_area .inv-action{padding:18px 16px}
 .st-key-investment_decision_area .inv-evidence{grid-template-columns:1fr;gap:4px}
 .st-key-investment_decision_area .inv-history-intro{padding:16px 17px}
}
</style>
"""


def advisory_investment() -> str:
    """Dedicated public explanation; account entry uses common Advisory auth."""
    return f'''{SERVICES_CSS}{SCORECARD_CSS}{SERVICE_CSS}{nav("advisory")}
<main class="scorecard-page investment-product">
<section class="sc-hero"><div class="container">
 <span class="sc-kicker">Executive AI Advisory / Self-service decision review</span>
 <h1>AI Investment Decision Advisor.</h1>
 <p class="sc-lead">Should you invest, experiment, hold or stop an AI opportunity?</p>
 <p>Examine one proposed AI use against business evidence, operational conditions, competing alternatives and governance obligations. Receive a reasoned executive decision brief: the verdict, the constraint and three actions that matter next.</p>
 <div class="investment-decision"><span class="investment-eyebrow">THE EXECUTIVE OUTPUT</span><br>
 <b>One recommendation. The reasoning behind it.</b>
 <p>Invest / Experiment / Hold / Stop — supported by the evidence you provide, not an AI-generated confidence score.</p></div>
 <div class="sc-actions">
  <a class="sc-btn" href="?page=advisory-access&amp;view=decision" target="_self" data-hq-event="investment_register">Register free · Start assessment</a>
  <a class="sc-btn alt" href="?page=advisory-access&amp;view=decision&amp;signin=1" target="_self" data-hq-event="investment_signin">Already registered? Sign in</a>
 </div>
 <p style="font-size:13px;margin-top:19px">Free for verified Executive Advisory accounts. No separate service approval or payment details. No confidential documents needed.</p>
</div></section>
<section class="sc-wrap" id="investment-method">
 <span class="sc-kicker">The decision in front of you</span>
 <h2>A useful verdict requires more than an attractive business case.</h2>
 <p>AI can be technically feasible and still be the wrong investment. This review tests the relative case for AI, the baseline behind expected value, the capacity to deliver and the conditions for responsible operation. It is a single-opportunity decision aid, not a portfolio ranking or an implementation tracker.</p>
 <div class="investment-steps">
  <article><small>01 / BUSINESS CASE</small><h3>What is worth solving?</h3><p>State the outcome, compare non-AI alternatives and clarify whether projected value is evidenced.</p></article>
  <article><small>02 / READINESS</small><h3>What is established?</h3><p>Review data rights, technical feasibility, people, ownership, adoption and scarce capacity.</p></article>
  <article><small>03 / AUTHORITY</small><h3>What could prevent progress?</h3><p>Assess oversight, consequence, legal obligations and the release conditions that must be met.</p></article>
 </div>
 <div class="sc-boundary"><p><strong>How the verdict is reached.</strong> Explicit control and evidence rules override superficial scores. A material prohibition, lack of accountability or unverified high-impact controls can prevent investment even when expected benefits appear attractive. Weak evidence lowers recommendation confidence.</p></div>
</section>
<section class="sc-wrap sc-dark" style="max-width:none"><div style="max-width:1100px;margin:auto">
 <span class="sc-kicker">Your decision brief</span>
 <h2>A clear executive position and what must happen next.</h2>
 <div class="sc-grid-2">
  <article class="sc-card"><span class="sc-num">Verdict</span><h3>Invest / Experiment / Hold / Stop</h3><p>One recommendation for the opportunity and the reason it is justified.</p></article>
  <article class="sc-card"><span class="sc-num">Confidence</span><h3>What is proven?</h3><p>Self-reported evidence and the missing facts that could change the decision.</p></article>
  <article class="sc-card"><span class="sc-num">Actions</span><h3>Three priorities</h3><p>Named roles and concrete evidence gates; no arbitrary delivery promises.</p></article>
  <article class="sc-card"><span class="sc-num">Report</span><h3>Private decision record</h3><p>Review the recommendation online and download a concise PDF for leadership discussion.</p></article>
 </div></div></section>
<section class="sc-wrap">
 <span class="sc-kicker">Access and confidentiality</span>
 <h2>Free registration. A private assessment.</h2>
 <p>Approximately five minutes with guided selections and an optional short context note. Register or sign in using the same Executive Advisory account as the other services. Your assessments remain in your private workspace. This service does not require individual pro-bono approval.</p>
 <div class="investment-auth">
   <h3>Executive Advisory account</h3>
   <p>One verified account for your decision history, report downloads and available Advisory services. Registration is free and does not enroll you in editorial emails.</p>
   <div class="sc-actions">
    <a class="sc-btn" href="?page=advisory-access&amp;view=decision" target="_self">Register free</a>
    <a class="sc-btn light" href="?page=advisory-access&amp;view=decision&amp;signin=1" target="_self">Sign in</a>
   </div>
 </div>
 <p class="sc-note" style="margin-top:20px">The output reflects the user's own selections. It is not an independent audit, investment authorization, legal advice or permission to deploy. Keep all inputs non-confidential; seek specialist review where required.</p>
</section>
</main>{footer()}'''


def _history(token: str, uid: str) -> list[dict]:
    url = _rest_url(
        "portfolio_advisory_investment_decisions?select=id,answers,model_version,"
        "feedback_rating,feedback_usefulness,created_at&user_id=eq."
        + quote(uid, safe="") + "&order=created_at.desc&limit=40"
    )
    rows = _request_json("GET", url, token=token, timeout=12)
    if not isinstance(rows, list):
        raise RuntimeError("Assessment history is unavailable.")
    return rows


def _submit(token: str, uid: str, raw: dict) -> str:
    checked = validate(raw)
    assess(checked)  # Reject invalid inputs before a write.
    rows = _request_json(
        "POST", _rest_url("portfolio_advisory_investment_decisions?select=id"),
        token=token,
        payload={"user_id": uid, "answers": checked, "model_version": MODEL_VERSION},
        prefer="return=representation", timeout=16,
    )
    if not isinstance(rows, list) or len(rows) != 1 or not rows[0].get("id"):
        raise RuntimeError("Assessment persistence could not be confirmed.")
    return str(rows[0]["id"])


def _pdf_report(data: dict, result: dict, created_at: str) -> bytes:
    """Public service's premium executive document, centrally formatted."""
    from page_advisory_investment_report import generate_decision_pdf
    return generate_decision_pdf(data, result, created_at)


QUESTIONS = (
    ("objective", "Intended business outcome"),
    ("stage", "Current opportunity stage"),
    ("autonomy", "Level of AI authority"),
    ("non_ai", "Comparison with a non-AI alternative"),
    ("value", "Strength of expected business benefit"),
    ("baseline", "Evidence for the current operating baseline"),
    ("data", "Data rights, access, ownership and quality"),
    ("feasibility", "Delivery and operating feasibility"),
    ("capacity", "Funding and specialist capacity"),
    ("owner", "Accountability for the business outcome"),
    ("adoption", "Change to the operating workflow"),
    ("control", "Oversight, incident response and control evidence"),
    ("exposure", "Consequence of an incorrect AI outcome"),
    ("legal", "Applicable legal and regulatory obligations"),
)


def _input_ui(token: str, uid: str) -> None:
    st.html('<div class="inv-note"><strong>How to complete the assessment.</strong> '
            'Give the opportunity a clear non-confidential name. Make the guided selections '
            'in all three sections, using current evidence rather than intended future '
            'capabilities. You will receive one verdict and three priority actions.</div>')
    with st.form("investment_single_decision_form", clear_on_submit=False):
        name = st.text_input("AI opportunity", max_chars=120,
                             placeholder="e.g. AI-assisted service case routing")
        tabs = st.tabs(["01 · Business case", "02 · Delivery readiness",
                        "03 · Governance & authority"])
        choices = {}
        descriptions = (
            "Define the problem, alternative approaches and current evidence of value.",
            "State what is operationally proven: people, data, ownership and adoption.",
            "State AI authority, consequences and the status of specialist controls.",
        )
        for tab, keys, description in zip(
            tabs, (QUESTIONS[:6], QUESTIONS[6:11], QUESTIONS[11:]), descriptions
        ):
            with tab:
                st.caption(description)
                for key, label in keys:
                    choices[key] = st.selectbox(
                        label, FIELDS[key], index=None,
                        placeholder="Select the closest evidence-based answer",
                        key="investment_choice_" + key,
                    )
        with st.expander("Optional context (not required)", expanded=False):
            st.caption("This note is retained for your reference. The verdict uses the structured selections, not free-text interpretation.")
            context = st.text_area("Brief non-confidential context", max_chars=500,
                                   placeholder="Only a detail that materially affects the decision.")
        acknowledgement = st.checkbox(
            "I understand the assessment relies on my selections and is not an "
            "independent verification, investment approval or authorization to deploy."
        )
        submitted = st.form_submit_button("Generate my executive decision brief",
                                          type="primary", use_container_width=True)
    if submitted:
        if not acknowledgement:
            st.warning("Confirm the limits of this self-service decision aid.")
            return
        try:
            raw = {"name": name, "context": context, "choices": choices}
            assess(raw)
            record_id = _submit(token, uid, raw)
        except ValueError as exc:
            st.warning(str(exc))
            return
        except (RuntimeError, TimeoutError, KeyError):
            st.error("Your assessment could not be saved. Check your connection and try again.")
            return
        st.session_state["investment_selected_record"] = record_id
        st.session_state["investment_current_report"] = record_id
        st.session_state["investment_next_section"] = "decision"
        st.session_state["investment_next_detail"] = "verdict"
        st.query_params["investment_section"] = "decision"
        st.query_params["investment_detail"] = "verdict"
        st.query_params["investment_record"] = record_id
        st.rerun()


# Use the four main stages and three report subviews established by the
# Rollout Readiness Advisor. Existing calls are mapped to these same routes.
WORKSPACE_SECTIONS = ("overview", "assess", "decision", "history")
WORKSPACE_LABELS = {
    "overview": "About this service",
    "assess": "New assessment",
    "decision": "Decision brief",
    "history": "My history",
}
REPORT_SECTIONS = ("verdict", "actions", "evidence")
REPORT_LABELS = {
    "verdict": "Verdict & evidence",
    "actions": "Executive actions",
    "evidence": "Evidence & report",
}
LEGACY_DESTINATIONS = {
    "My assessments": ("history", ""),
    "Executive decision": ("decision", "verdict"),
    "Action plan": ("decision", "actions"),
    "Evidence & inputs": ("decision", "evidence"),
    "New assessment": ("assess", ""),
}


def _go_to(section: str, record_id: str = "") -> None:
    """Route internal navigation using the same hierarchy as Rollout."""
    section, detail = LEGACY_DESTINATIONS.get(section, (section, ""))
    if section not in WORKSPACE_SECTIONS:
        return
    st.session_state["investment_next_section"] = section
    st.query_params["investment_section"] = section
    if detail:
        st.session_state["investment_next_detail"] = detail
        st.query_params["investment_detail"] = detail
    if record_id:
        st.session_state["investment_selected_record"] = record_id
        st.session_state["investment_current_report"] = record_id
        st.query_params["investment_record"] = record_id


def _investment_nav_changed() -> None:
    section = st.session_state.get("investment_workspace_nav")
    if section in WORKSPACE_SECTIONS:
        st.query_params["investment_section"] = section


def _investment_report_nav_changed() -> None:
    detail = st.session_state.get("investment_report_nav")
    if detail in REPORT_SECTIONS:
        st.query_params["investment_detail"] = detail


def _workspace_nav(history: list[dict]) -> str:
    target = st.session_state.pop("investment_next_section", None)
    requested = str(st.query_params.get("investment_section") or "overview")
    if target in WORKSPACE_SECTIONS:
        requested = target
    if requested not in WORKSPACE_SECTIONS:
        requested = "overview"
    if st.session_state.get("investment_workspace_nav") != requested:
        st.session_state["investment_workspace_nav"] = requested
    st.pills(
        "Investment service sections", WORKSPACE_SECTIONS,
        format_func=lambda key: WORKSPACE_LABELS[key],
        selection_mode="single", required=True, on_change=_investment_nav_changed,
        key="investment_workspace_nav", label_visibility="collapsed",
        wrap=False, width="stretch",
    )
    return requested


def _report_nav() -> str:
    target = st.session_state.pop("investment_next_detail", None)
    requested = str(st.query_params.get("investment_detail") or "verdict")
    if target in REPORT_SECTIONS:
        requested = target
    if requested not in REPORT_SECTIONS:
        requested = "verdict"
    if st.session_state.get("investment_report_nav") != requested:
        st.session_state["investment_report_nav"] = requested
    st.pills(
        "Decision brief sections", REPORT_SECTIONS,
        format_func=lambda key: REPORT_LABELS[key],
        key="investment_report_nav", selection_mode="single",
        required=True, on_change=_investment_report_nav_changed,
        label_visibility="collapsed", wrap=False, width="stretch",
    )
    return requested


def _case_heading(record: dict, view: dict) -> None:
    from page_advisory_shared_ui import case_header
    case_header(
        title=view["name"],
        date=str(record.get("created_at") or "")[:10],
        context=view["scope"],
        status=view["verdict"] + " · " + view["confidence"] +
               " evidence confidence (self-reported)",
        synthetic=bool((record.get("answers") or {}).get("demo")),
    )


def _service_guide(history: list[dict]) -> None:
    from page_advisory_shared_ui import service_overview
    service_overview(
        hero="Should you invest, experiment, hold or stop?",
        description=(
            "Evaluate one AI opportunity against its business case, "
            "non-AI alternatives, organizational readiness and risk. "
            "Receive a reasoned decision and explicit conditions for the next commitment."
        ),
        access="Included with verified Advisory registration",
        assessment_format="One focused self-service assessment",
        saved_count=len(history),
        outputs=(
            ("The verdict", "A defensible investment position",
             "Invest, Experiment, Hold or Stop, with the decision's limits and principal uncertainty."),
            ("The priorities", "Three executive actions",
             "A specific action, suggested accountable function and evidence required for closure."),
            ("The report", "A private executive decision brief",
             "The supporting 14 selections, explanation and downloadable two-page PDF."),
        ),
        steps=(
            ("Describe the opportunity",
             "Give the AI use a non-confidential name and choose its business purpose."),
            ("Answer 14 conditions",
             "Three short sections on value, operational readiness, and governance."),
            ("Review your recommendation",
             "Inspect the verdict and actions, check inputs and save the executive report."),
        ),
        boundary=(
            "This is a free self-service decision aid. It does not approve spending, "
            "certify compliance, verify submitted evidence or authorize live AI deployment. "
            "No separate approval is required for registered Advisory members."
        ),
    )
    if history:
        latest=history[0]
        try:
            current=present_assessment(latest.get("answers") or {})
        except (ValueError, TypeError, KeyError):
            current=None
        if current:
            st.markdown("### Your latest decision")
            with st.container(border=True):
                st.caption(str(latest.get("created_at") or "")[:10]+" · "+current["name"])
                st.markdown("#### "+current["verdict"])
                st.write(current["next_step"])
                a,b=st.columns(2)
                with a:
                    st.button(
                        "Open executive decision brief", type="primary",
                        key="investment_home_latest", use_container_width=True,
                        on_click=_go_to,
                        args=("Executive decision", str(latest["id"])),
                    )
                with b:
                    st.button(
                        "Browse decision history", key="investment_home_history",
                        use_container_width=True, on_click=_go_to,
                        args=("My assessments",),
                    )
    st.button(
        "Start a new investment assessment", key="investment_home_new",
        on_click=_go_to, args=("New assessment",),
    )


def _assessment_library(history: list[dict]) -> None:
    st.html(
        '<div class="inv-history-intro">'
        '<span class="inv-eyebrow">PRIVATE DECISION LIBRARY</span>'
        '<h3 class="inv-section-title">Your AI investment assessments</h3>'
        '<p>Each record concerns one AI opportunity. Compare its purpose, current stage, '
        'recommended position and critical evidence gap before opening it. '
        'Past assessments are retained as submitted; a new assessment creates a new record.</p>'
        '</div>'
    )
    valid = []
    for item in history:
        try:
            valid.append((item, present_assessment(item.get("answers") or {})))
        except (TypeError, ValueError, KeyError):
            continue
    st.caption(f"{len(valid)} saved assessments · Newest first · Private to your account")
    if not valid:
        st.info("No valid saved assessments yet. Start with a single AI opportunity.")
        st.button("Create my first assessment", type="primary",
                  on_click=_go_to, args=("New assessment",))
        return

    a, b = st.columns([1.7, 1])
    with a:
        keyword = st.text_input("Find an opportunity", key="inv_library_search",
                                placeholder="Search a use-case name")
    with b:
        filter_verdict = st.selectbox(
            "Decision", ("All decisions", "INVEST", "EXPERIMENT", "HOLD", "STOP"),
            key="inv_library_filter",
        )
    selected = [
        (record, meta) for record, meta in valid
        if keyword.casefold() in meta["name"].casefold()
        and (filter_verdict == "All decisions" or meta["verdict"] == filter_verdict)
    ]
    if not selected:
        st.info("No assessments match these filters. Adjust the search or decision filter.")
        return

    per_page = 5
    total_pages = (len(selected) + per_page - 1) // per_page
    page = st.selectbox("Records page", list(range(1, total_pages + 1)),
                        format_func=lambda n: f"Page {n} of {total_pages}",
                        key="inv_library_page") if total_pages > 1 else 1
    st.caption(f"Showing {len(selected)} matching assessment(s)")
    for record, meta in selected[(page - 1) * per_page:page * per_page]:
        rid = str(record.get("id") or "")
        stamp = str(record.get("created_at") or "")[:10]
        with st.container(border=True):
            left, right = st.columns([3.3, 1], vertical_alignment="center")
            with left:
                st.html(
                    '<div class="inv-case-item">'
                    '<span class="inv-eyebrow">RECORD · ' + escape(stamp) + '</span>'
                    '<strong>' + escape(meta["name"]) + '</strong>'
                    '<p>' + escape(meta["scope"]) + '</p>'
                    '</div>'
                )
                st.html(
                    '<div class="inv-case-tags">'
                    '<span>VERDICT · ' + escape(meta["verdict"]) + '</span>'
                    '<span>EVIDENCE · ' + escape(meta["confidence"]) +
                    ' (self-reported)</span></div>'
                )
                note = meta["data"].get("context", "").strip()
                if note:
                    st.caption("Case context supplied: " + note[:170] + ("…" if len(note) > 170 else ""))
                st.caption("Main issue: " + meta["why"])
            with right:
                st.button("Open decision", key="inv_open_" + rid, type="primary",
                          use_container_width=True, on_click=_go_to,
                          args=("Executive decision", rid))
                st.button("View actions", key="inv_actions_" + rid,
                          use_container_width=True, on_click=_go_to,
                          args=("Action plan", rid))
    st.divider()
    st.button("Assess a different opportunity", type="secondary",
              on_click=_go_to, args=("New assessment",))


def _report_download(record: dict, view: dict) -> None:
    rid = str(record.get("id") or "")
    try:
        report = _pdf_report(view["data"], view["result"],
                             str(record.get("created_at") or ""))
        st.download_button(
            "Download the executive decision brief (PDF)",
            report, file_name="ai-investment-decision-" + rid[:8] + ".pdf",
            mime="application/pdf", key="investment_pdf_" + rid,
            use_container_width=True,
        )
    except (RuntimeError, ValueError, TypeError, UnicodeError, OSError):
        st.error("The PDF could not be produced. Your saved assessment is still available.")


def _feedback_panel(token: str, uid: str, record: dict) -> None:
    rid = str(record["id"])
    if record.get("feedback_rating") is not None:
        st.caption("Report feedback received. Thank you for assessing its usefulness.")
        return
    with st.expander("Optional feedback · Was this decision useful?", expanded=False):
        with st.form("investment_feedback_" + rid):
            rating = st.select_slider(
                "Was the recommendation clear and credible?",
                options=[1, 2, 3, 4, 5], value=3)
            useful = st.radio(
                "Did it help identify your next decision or action?",
                ("Yes", "Partly", "No"), horizontal=True, index=None)
            submitted = st.form_submit_button("Submit feedback")
        if submitted:
            if useful is None:
                st.warning("Select an answer about usefulness or close the optional form.")
                return
            try:
                updated = _request_json(
                    "PATCH",
                    _rest_url("portfolio_advisory_investment_decisions?id=eq."
                              + quote(rid, safe="") + "&user_id=eq."
                              + quote(uid, safe="") + "&select=id"),
                    token=token,
                    payload={"feedback_rating": int(rating),
                             "feedback_usefulness": useful,
                             "feedback_at": datetime.now(timezone.utc).isoformat()},
                    prefer="return=representation", timeout=12,
                )
                if not isinstance(updated, list) or len(updated) != 1:
                    raise RuntimeError("Feedback confirmation failed.")
                st.success("Feedback recorded.")
                st.rerun()
            except (RuntimeError, TimeoutError, KeyError, ValueError):
                st.error("Feedback could not be saved. You can retry.")


def _decision_page(token: str, uid: str, record: dict, view: dict) -> None:
    from page_advisory_investment_report import _executive_summary
    st.html(
        '<section class="inv-decision">'
        '<span class="inv-eyebrow">EXECUTIVE POSITION · SELF-REPORTED EVIDENCE</span>'
        '<div class="inv-verdict">' + escape(view["verdict"]) + '</div>'
        '<h3>' + escape(view["next_step"]) + '</h3>'
        '<p>' + escape(_executive_summary(view["data"], view["result"])) + '</p>'
        '</section>'
    )
    case_note = view["data"].get("context", "").strip()
    if case_note:
        st.html(
            '<div class="inv-note"><strong>What is being assessed.</strong><br>' +
            escape(case_note[:340]) +
            ('…' if len(case_note) > 340 else '') +
            '<p><small>Context supplied by the assessor; not independently verified ' 
            'or interpreted by the decision rules. Full note in Evidence &amp; inputs.</small></p></div>'
        )
    st.html(
        '<div class="inv-rail">'
        '<article><small>Business case</small><strong>' +
        escape(view["value_statement"]) + '</strong></article>'
        '<article><small>Control position</small><strong>' +
        escape(view["risk_statement"]) + '</strong></article>'
        '<article><small>Evidence confidence</small><strong>' +
        escape(view["confidence"]) + ' · Not independently verified</strong></article>'
        '</div>'
    )
    st.html('<h3 class="inv-section-title">What this decision means</h3>')
    st.html(
        '<div class="inv-note">'
        '<strong>Decision boundary.</strong> ' + escape(view["boundary"]) +
        '<p><strong>Most significant limitation.</strong> ' + escape(view["why"]) + '</p>'
        '</div>'
    )
    st.caption("Recommendation based on the 14 answers recorded for this opportunity. "
               "The optional context note does not affect the verdict.")
    a, b = st.columns([1, 1])
    with a:
        st.button("Review the three actions", type="primary",
                  use_container_width=True, on_click=_go_to,
                  args=("Action plan",))
    with b:
        st.button("Inspect the assessment evidence",
                  use_container_width=True, on_click=_go_to,
                  args=("Evidence & inputs",))
    st.divider()
    _report_download(record, view)
    _feedback_panel(token, uid, record)


def _actions_page(view: dict) -> None:
    st.html(
        '<span class="inv-eyebrow">EXECUTIVE ACTION PLAN</span>'
        '<h3 class="inv-section-title">Three requirements before the next decision</h3>'
        '<div class="inv-note"><strong>Current position:</strong> ' +
        escape(view["next_step"]) + '<br><strong>Boundary:</strong> ' +
        escape(view["boundary"]) + '</div>'
    )
    st.caption("The roles below are suggested accountability functions, not named "
               "people or recorded task assignments. The report does not invent deadlines.")
    for i, action in enumerate(view["actions"], 1):
        st.html(
            '<article class="inv-action">'
            '<span class="inv-eyebrow">PRIORITY ' + f"{i:02d}" + ' / REQUIRED ACTION</span>'
            '<h4>' + escape(action["text"]) + '</h4>'
            '<p><strong>Suggested accountable function:</strong> ' +
            escape(action["owner"]) + '</p>'
            '<div class="inv-proof"><strong>Evidence required to close this action</strong><br>' +
            escape(action["trigger"]) + '</div>'
            '</article>'
        )
    st.html(
        '<div class="inv-note"><strong>Reassessment gate:</strong> ' +
        escape(view["result"]["release_condition"]) +
        '<p>When these conditions change, create a new assessment so the earlier '
        'decision remains available for comparison.</p></div>'
    )
    a, b = st.columns(2)
    with a:
        st.button("Review supporting evidence", on_click=_go_to,
                  args=("Evidence & inputs",), use_container_width=True)
    with b:
        st.button("Create a new assessment", on_click=_go_to,
                  args=("New assessment",), use_container_width=True)


def _evidence_page(view: dict) -> None:
    st.html(
        '<span class="inv-eyebrow">TRANSPARENT DECISION RECORD</span>'
        '<h3 class="inv-section-title">What this assessment actually contains</h3>'
        '<div class="inv-note">Fourteen recorded selections grouped below. '
        'This is a structured, self-reported decision assessment—not an independent '
        'audit or a verification of the business case.</div>'
    )
    tabs = st.tabs(["01 · Business case", "02 · Delivery readiness",
                    "03 · Governance & authority"])
    for tab, (name, rows) in zip(tabs, categorize_evidence(view["data"])):
        with tab:
            st.caption(name + " · Submitted answers")
            st.html(
                '<div>' + "".join(
                    '<div class="inv-evidence"><b>' + escape(label) +
                    '</b><span>' + escape(str(value)) + '</span></div>'
                    for label, value in rows
                ) + '</div>'
            )
    st.html('<h3 class="inv-section-title">Why the recommendation is limited</h3>')
    if view["result"]["constraints"]:
        for item in view["result"]["constraints"]:
            st.write("• " + item)
    else:
        st.write("No material gaps were reported in the structured selections.")
    with st.expander("Optional context supplied with this case", expanded=False):
        context = view["data"].get("context", "")
        st.write(context if context else "No context note was supplied.")
        st.caption("The context note is kept for reference but is not evaluated "
                   "by the decision rules.")
    with st.expander("How the verdict is determined", expanded=False):
        st.write("**1. Mandatory constraints first.** Known prohibitions, a better "
                 "non-AI alternative, or unlawful/unreliable data may lead to STOP.")
        st.write("**2. Readiness gates.** Missing ownership, capacity, data assessments "
                 "or essential controls can result in HOLD.")
        st.write("**3. Business evidence.** Demonstrated value, readiness, accountability, "
                 "controls and maturity determine whether a case advances to formal "
                 "investment review or remains an EXPERIMENT.")
        st.caption("Evidence confidence uses a count of positive self-reported "
                   "indicators; it does not confirm their accuracy. Rule set: " +
                   str(view["result"]["model_version"]))
    st.caption("To update the decision, create a new assessment with revised evidence. "
               "Earlier records remain intact.")


def render_private_investment(session: dict, user: dict) -> None:
    """Dedicated self-service pages within the existing authenticated Advisory shell."""
    token = str(session.get("access_token") or "")
    uid = str(user.get("id") or "")
    if not token or not uid or not user.get("email_confirmed_at"):
        st.error("A verified Advisory account is required to use this service.")
        return
    st.html(PRIVATE_CSS)
    with st.container(key="investment_decision_area"):
        st.html(
            '<header class="inv-hero">'
            '<span class="inv-eyebrow">EXECUTIVE AI ADVISORY / PRIVATE WORKSPACE</span>'
            '<h2>AI Investment Decision Advisor</h2>'
            '<p>One AI opportunity. One defensible recommendation. The evidence '
            'and actions required for your next leadership decision.</p>'
            '</header>'
        )
        try:
            history = _history(token, uid)
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            st.error("Your private assessments could not be loaded. Please try again.")
            return
        records = {str(item.get("id")): item for item in history if item.get("id")}
        selection = (st.session_state.get("investment_selected_record") or
                     st.session_state.get("investment_current_report"))
        if selection not in records:
            selection = next(iter(records), "")
        st.session_state["investment_selected_record"] = selection
        section = _workspace_nav(history)
        if section == "My assessments":
            _assessment_library(history)
            return
        if section == "New assessment":
            st.html(
                '<div class="inv-history-intro">'
                '<span class="inv-eyebrow">NEW EXECUTIVE ASSESSMENT</span>'
                '<h3 class="inv-section-title">Assess one AI opportunity</h3>'
                '<p>Complete three short sections and receive a reasoned position: '
                'Invest, Experiment, Hold or Stop. Your answers and report are '
                'saved privately; this does not authorize funding or production.</p>'
                '</div>'
            )
            _input_ui(token, uid)
            return
        if not selection:
            st.info("Select a saved assessment or create a new one.")
            st.button("Create an assessment", on_click=_go_to,
                      args=("New assessment",), type="primary")
            return
        record = records[selection]
        try:
            view = present_assessment(record.get("answers") or {})
        except (TypeError, ValueError, KeyError):
            st.error("The selected assessment cannot be interpreted. "
                     "Choose another record from My assessments.")
            st.button("View assessment library", on_click=_go_to,
                      args=("My assessments",))
            return
        _case_heading(record, view)
        if section == "Executive decision":
            _decision_page(token, uid, record, view)
        elif section == "Action plan":
            _actions_page(view)
        elif section == "Evidence & inputs":
            _evidence_page(view)
