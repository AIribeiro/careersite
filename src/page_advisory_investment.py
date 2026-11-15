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
.st-key-investment_decision_area .inv-panel{background:#fffdfa;border:1px solid #e2dcd2;padding:23px 26px;margin:14px 0 22px;color:#20394d}
.st-key-investment_decision_area .inv-panel h3{font:500 27px/1.25 Georgia,serif;margin:8px 0;color:#173047}
.st-key-investment_decision_area .inv-panel p{color:#52667a;font-size:14px;line-height:1.7;margin:7px 0}
.st-key-investment_decision_area .inv-eyebrow{font:700 10px/1.5 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase;color:#a16b4b}
.st-key-investment_decision_area .inv-report{border:1px solid #d9d6d0;background:#fff;color:#213a4f;padding:27px;margin:14px 0}
.st-key-investment_decision_area .inv-report .inv-verdict{font:500 36px/1.1 Georgia,serif;color:#122e45;margin:12px 0 8px}
.st-key-investment_decision_area .inv-report .inv-head{font:500 23px/1.3 Georgia,serif;margin:0 0 15px}
.st-key-investment_decision_area .inv-report p{line-height:1.65;font-size:14px;color:#4a6072}
.st-key-investment_decision_area .inv-report .inv-meta{font:700 11px Arial,sans-serif;color:#99714e;letter-spacing:.08em}
.st-key-investment_decision_area [data-testid="stForm"]{border:1px solid #ded7cc;background:#fffefa;padding:12px}
@media(max-width:700px){.st-key-investment_decision_area .inv-panel,.st-key-investment_decision_area .inv-report{padding:18px}}
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
    from io import BytesIO
    from fpdf import FPDF

    def clean(value: object) -> str:
        s = " ".join(str(value if value is not None else "").split())
        for a, b in {"\u2014":" - ", "\u2013":"-", "\u2019":"'", "\u201c":'"',
                     "\u201d":'"', "\u2022":" - "}.items():
            s = s.replace(a, b)
        return s.encode("latin-1", "replace").decode("latin-1")

    p = FPDF("P", "mm", "A4")
    p.set_auto_page_break(auto=True, margin=18)
    p.set_margins(19, 18, 19)
    p.add_page()
    p.set_fill_color(16, 37, 56)
    p.rect(0, 0, 210, 64, "F")
    p.set_xy(19, 14)
    p.set_text_color(229, 185, 145)
    p.set_font("Helvetica", "B", 9)
    p.cell(0, 7, "JAIR RIBEIRO  /  EXECUTIVE AI ADVISORY")
    p.ln(12)
    p.set_x(19)
    p.set_text_color(255, 255, 255)
    p.set_font("Helvetica", "B", 21)
    p.multi_cell(172, 10, "AI Investment Decision")
    p.set_x(19)
    p.set_font("Helvetica", "", 10)
    p.cell(0, 7, "INDEPENDENT EXECUTIVE DECISION BRIEF")
    p.set_xy(19, 76)

    def section(head: str, text: str, height: int = 6) -> None:
        if p.get_y() > 252:
            p.add_page()
        p.set_text_color(149, 99, 70)
        p.set_font("Helvetica", "B", 9)
        p.cell(0, 7, clean(head.upper()))
        p.ln(8)
        p.set_text_color(31, 53, 73)
        p.set_font("Helvetica", "", 10)
        p.multi_cell(172, height, clean(text)[:850])
        p.ln(4)

    p.set_text_color(75, 92, 105)
    p.set_font("Helvetica", "", 10)
    p.multi_cell(172, 5, clean(data["name"])[:120] + "  |  Assessment " + clean(created_at[:10]))
    p.ln(6)
    p.set_text_color(21, 47, 65)
    p.set_font("Helvetica", "B", 28)
    p.cell(0, 12, clean(result["verdict"]))
    p.ln(15)
    p.set_font("Helvetica", "B", 13)
    p.multi_cell(172, 7, clean(result["headline"]))
    p.ln(4)
    section("The recommendation", result["reason"])
    section("Business outcomes to validate", result["decision_lens"])
    section("Critical consideration", result["primary_constraint"])
    section("Evidence confidence", result["confidence"] + ". Self-reported, not independently verified.")
    if result["constraints"]:
        section("Open decision conditions", "; ".join(result["constraints"][:3]))
    if p.get_y() > 213:
        p.add_page()
    p.set_text_color(149, 99, 70)
    p.set_font("Helvetica", "B", 9)
    p.cell(0, 7, "THREE PRIORITY ACTIONS")
    p.ln(9)
    for i, item in enumerate(result["actions"], 1):
        if p.get_y() > 252:
            p.add_page()
        p.set_text_color(25, 52, 71)
        p.set_font("Helvetica", "B", 10)
        p.multi_cell(172, 6, str(i) + ".  " + clean(item["text"])[:220])
        p.set_text_color(91, 108, 124)
        p.set_font("Helvetica", "", 9)
        p.multi_cell(172, 5, "Suggested owner: " + clean(item["owner"]) +
                     "  |  Evidence gate: " + clean(item["trigger"]))
        p.ln(4)
    section("Next review trigger", result["review_trigger"])
    p.set_text_color(101, 111, 120)
    p.set_font("Helvetica", "I", 8)
    p.multi_cell(172, 5, "Decision aid based on self-reported information. No funding, legal, "
                 "risk or production authorization is implied. Rule set: " + MODEL_VERSION + ".")
    return bytes(p.output())


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
    st.html('<div class="inv-panel"><span class="inv-eyebrow">NEW DECISION / 4–6 MINUTES</span>'
            '<h3>What should happen with this AI opportunity?</h3>'
            '<p>Choose the closest answer for each condition. Use the evidence available '
            'today, not the target state. The result will state what has not been verified.</p></div>')
    with st.form("investment_single_decision_form", clear_on_submit=False):
        name = st.text_input("AI opportunity", max_chars=120,
                             placeholder="e.g. AI-assisted service case routing")
        tabs = st.tabs(["01 · Business case", "02 · Delivery readiness",
                        "03 · Governance & authority"])
        choices = {}
        for tab, keys in zip(tabs, (QUESTIONS[:6], QUESTIONS[6:11], QUESTIONS[11:])):
            with tab:
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
        st.session_state["investment_current_report"] = record_id
        st.session_state["investment_new_assessment"] = False
        st.rerun()


def _report_ui(token: str, uid: str, record: dict) -> None:
    raw = record.get("answers")
    try:
        data = validate(raw)
        result = assess(data)
    except (ValueError, TypeError):
        st.error("This record is invalid. Please start a new assessment.")
        return
    rid = str(record["id"])
    stamp = str(record.get("created_at") or "")[:10]
    st.html(
        '<section class="inv-report">'
        '<span class="inv-eyebrow">EXECUTIVE DECISION BRIEF / ' + escape(stamp) + '</span>'
        '<h3>' + escape(data["name"]) + '</h3>'
        '<div class="inv-verdict">' + escape(result["verdict"]) + '</div>'
        '<div class="inv-head">' + escape(result["headline"]) + '</div>'
        '<p>' + escape(result["reason"]) + '</p>'
        '<p><strong>Critical consideration.</strong> ' + escape(result["primary_constraint"]) + '</p>'
        '<p><strong>Relevant outcome measures.</strong> ' + escape(result["decision_lens"]) + '</p>'
        '<p class="inv-meta">EVIDENCE CONFIDENCE · ' + escape(result["confidence"]) + '</p>'
        '</section>'
    )
    st.markdown("#### Three actions that should happen next")
    for i, item in enumerate(result["actions"], 1):
        with st.container(border=True):
            st.markdown(f"**{i:02d} · {item['text']}**")
            st.caption("Suggested owner: " + item["owner"] + " · Evidence gate: " + item["trigger"])
    st.markdown("#### Condition for reconsideration")
    st.write(result["release_condition"])
    with st.expander("Review the evidence and decision rules", expanded=False):
        st.caption("Selections are self-reported, not independently verified. "
                   "An INVEST verdict means advance to formal approval, not permission to spend.")
        st.write("**Observed limitations**")
        for entry in result["constraints"]:
            st.write("• " + entry)
        if data["context"]:
            st.write("**Your context note (not used to calculate the verdict)**")
            st.write(data["context"])
        st.caption("Rule set " + MODEL_VERSION + " · Original selections are retained privately.")
    st.caption("This service does not replace legal, privacy, risk, security or investment approval.")
    try:
        report = _pdf_report(data, result, str(record.get("created_at") or ""))
        st.download_button("Download executive decision report (PDF)",
                           report, file_name="ai-investment-executive-decision.pdf",
                           mime="application/pdf", key="investment_pdf_" + rid,
                           use_container_width=True)
    except (RuntimeError, ValueError, TypeError, UnicodeError):
        st.error("The PDF could not be generated. The decision remains available above.")
    if record.get("feedback_rating") is not None:
        st.caption("Your optional report feedback has been recorded.")
        return
    with st.expander("Optional feedback on this recommendation", expanded=False):
        with st.form("investment_feedback_" + rid):
            rating = st.select_slider(
                "Was the recommendation clear and credible?", options=[1, 2, 3, 4, 5], value=3)
            useful = st.radio("Did it help identify your next decision or action?",
                              ("Yes", "Partly", "No"), horizontal=True, index=None)
            sent = st.form_submit_button("Submit feedback")
        if sent:
            if useful is None:
                st.warning("Select an answer about usefulness, or close this optional form.")
            else:
                try:
                    result_update = _request_json(
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
                    if not isinstance(result_update, list) or len(result_update) != 1:
                        raise RuntimeError("Feedback was not saved.")
                    st.success("Feedback recorded.")
                    st.rerun()
                except (RuntimeError, TimeoutError, KeyError):
                    st.error("Feedback could not be saved. You can retry.")


def render_private_investment(session: dict, user: dict) -> None:
    """Called exclusively from the verified, active Advisory member shell."""
    token = str(session.get("access_token") or "")
    uid = str(user.get("id") or "")
    if not token or not uid or not user.get("email_confirmed_at"):
        st.error("A verified Advisory account is required to use this service.")
        return
    st.html(PRIVATE_CSS)
    with st.container(key="investment_decision_area"):
        st.html('<div class="inv-panel"><span class="inv-eyebrow">EXECUTIVE DECISION SERVICE / FREE</span>'
                '<h3>AI Investment Decision Advisor</h3>'
                '<p>Assess a single AI opportunity. Your report gives one verdict, its reasoning, '
                'evidence confidence and three actions. Every assessment is private to your account.</p></div>')
        try:
            history = _history(token, uid)
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            st.error("Could not load your private decisions. Try again later.")
            return
        if history:
            options = {str(item["id"]): item for item in history}
            current = st.session_state.get("investment_current_report")
            if current not in options:
                current = next(iter(options))
            selected = st.selectbox("Previous executive assessments", list(options),
                                    index=list(options).index(current),
                                    format_func=lambda x: (
                                        str(options[x].get("created_at") or "")[:10] + " · " +
                                        str((options[x].get("answers") or {}).get("name") or "Assessment")
                                    ), key="investment_history_selector")
            _report_ui(token, uid, options[selected])
            if st.button("Assess another AI opportunity", key="investment_new_button"):
                st.session_state["investment_new_assessment"] = True
                st.rerun()
        if not history or st.session_state.get("investment_new_assessment"):
            st.divider()
            _input_ui(token, uid)
