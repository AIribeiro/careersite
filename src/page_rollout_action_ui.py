"""Executive action-plan presentation for the one-session Rollout Readiness Advisor.

Presentation only: the deterministic scoring rules, recommendation catalog,
and downloadable PDF use the same assessment inputs and remain authoritative.
Untrusted scenario data is escaped before entering the private Streamlit HTML.
"""
from __future__ import annotations

from html import escape

from page_rollout_premium_pdf import CATALOG, _gate_keys, build_action_plan

ACTION_PLAN_CSS = """
<style>
.rl-plan {max-width:1080px;margin:23px 0 29px;font-family:inherit;color:#172b40}
.rl-plan *{box-sizing:border-box}
.rl-plan .rl-plan-top{display:flex;align-items:flex-end;justify-content:space-between;
  gap:18px;margin:0 0 19px}
.rl-plan .rl-eyebrow{font-size:10px;letter-spacing:.17em;font-weight:800;
  text-transform:uppercase;color:#a56d4b;display:block;margin-bottom:6px}
.rl-plan h3{font-family:Georgia,serif;font-size:clamp(22px,2.6vw,31px);
  font-weight:500;letter-spacing:-.025em;line-height:1.14;margin:0 0 9px;color:#14283e}
.rl-plan .rl-plan-intro{font-size:13px;line-height:1.55;color:#607083;margin:0}
.rl-plan .rl-stat{border:1px solid #decfc3;padding:10px 15px;background:#faf7f1;
  flex:0 0 auto;text-align:center;min-width:128px}
.rl-plan .rl-stat strong{font-size:23px;font-weight:750;color:#9d4f3b;
  display:block;line-height:1.1}
.rl-plan .rl-stat span{font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  font-weight:750;color:#617082}
.rl-plan .rl-stack{display:grid;gap:13px}
.rl-plan .rl-card{background:#fffefa;border:1px solid #ddd7cf;
  border-left:4px solid #b87956;padding:20px 23px 16px;
  box-shadow:0 4px 19px rgba(24,36,50,.045)}
.rl-plan .rl-card--gate{border-left-color:#a45446}
.rl-plan .rl-card-head{display:grid;grid-template-columns:46px minmax(0,1fr);gap:13px}
.rl-plan .rl-num{font-family:Georgia,serif;color:#b57e5d;font-size:29px;
  line-height:1.08;font-weight:500}
.rl-plan .rl-meta{display:flex;align-items:center;flex-wrap:wrap;gap:7px 12px;margin:1px 0 5px}
.rl-plan .rl-status{font-size:10px;font-weight:800;letter-spacing:.06em;
  text-transform:uppercase;color:#725e4c}
.rl-plan .rl-status--gate{color:#995247}
.rl-plan .rl-date{font-size:11px;color:#627184}
.rl-plan h4{font-family:Georgia,serif;font-size:clamp(17px,1.9vw,21px);
  font-weight:500;line-height:1.2;letter-spacing:-.015em;color:#142b42;margin:0 0 11px}
.rl-plan .rl-facts{display:grid;grid-template-columns:minmax(170px,.8fr) minmax(0,1.4fr);
  gap:15px;padding:14px 0 12px;border-top:1px solid #ece7e0;margin-left:59px}
.rl-plan .rl-facts > div{min-width:0}
.rl-plan .rl-label{font-size:10px;letter-spacing:.085em;text-transform:uppercase;
  color:#7a8792;font-weight:800;display:block;margin-bottom:6px}
.rl-plan .rl-facts p{font-size:13px;line-height:1.42;color:#2c3f51;margin:0;font-weight:560}
.rl-plan .rl-facts .rl-condition{background:#f5f1eb;border-left:2px solid #b47e5c;
  padding:10px 12px;margin-top:-8px}
.rl-plan .rl-facts .rl-condition p{font-weight:700;color:#1d3449}
.rl-plan .rl-details{border-top:1px solid #ece7e0;margin-left:59px;padding-top:10px}
.rl-plan .rl-details summary{cursor:pointer;font-size:12px;font-weight:750;color:#865c44;
  line-height:1.55;list-style-position:inside}
.rl-plan .rl-details summary:hover{text-decoration:underline}
.rl-plan .rl-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;
  margin:13px 0 5px;padding:13px;background:#faf8f4}
.rl-plan .rl-detail-grid p{font-size:12px;line-height:1.55;color:#43556a;margin:0}
.rl-plan .rl-decision-strip{margin-top:14px;padding:15px 19px;
  border:1px solid #d8dfe1;background:#eef2f2}
.rl-plan .rl-decision-strip strong{font-size:13px;color:#233a4d;display:block;margin-bottom:5px}
.rl-plan .rl-decision-strip p{font-size:12px;line-height:1.6;color:#516174;margin:0}
.rl-plan .rl-extra{margin:9px 0 0;padding-left:20px;font-size:12px;color:#516174}
.rl-plan .rl-footnote{font-size:11px;color:#687789;margin:12px 0 0;line-height:1.5}
@media(max-width:720px), (max-device-width:720px){
 .rl-plan .rl-plan-top{align-items:flex-start;flex-direction:column}
 .rl-plan .rl-stat{min-width:0;text-align:left;display:flex;align-items:center;gap:9px;padding:8px 12px}
 .rl-plan .rl-stat strong{font-size:19px}
 .rl-plan .rl-card{padding:16px 14px 13px}
 .rl-plan .rl-card-head{grid-template-columns:34px minmax(0,1fr);gap:9px}
 .rl-plan .rl-num{font-size:23px}
 .rl-plan .rl-facts{margin-left:43px;grid-template-columns:1fr;gap:12px}
 .rl-plan .rl-details{margin-left:43px}
 .rl-plan .rl-detail-grid{grid-template-columns:1fr;gap:12px}
 .rl-plan .rl-facts .rl-condition{margin-top:0}
}
@media(max-width:390px), (max-device-width:390px){
 .rl-plan .rl-facts,.rl-plan .rl-details{margin-left:0}
 .rl-plan h4{font-size:17px}
}
</style>
"""


def _safe(value: object, limit: int = 350) -> str:
    """Escape all dynamic input before injecting in st.markdown(unsafe_allow_html=True)."""
    return escape(str(value if value is not None else "")[:limit], quote=True)


def action_plan_html(data: dict, result: dict) -> str:
    """Render a structured, responsive summary; keep execution detail expandable."""
    plan = build_action_plan(data, result)
    gates = _gate_keys(data)
    if not plan or len(plan)!=3:
        raise ValueError("The action plan must contain three decision-ready recommendations")
    if len(gates) != len(result.get("critical_gates",[])):
        raise ValueError("Critical gate count must match the governing assessment verdict")
    cards=[]
    for step in plan:
        is_gate=bool(step["critical"])
        status="Release blocker" if is_gate else "Next-stage safeguard"
        classes="rl-card rl-card--gate" if is_gate else "rl-card"
        cards.append(f"""
<article class="{classes}">
 <div class="rl-card-head">
  <span class="rl-num" aria-label="Priority {_safe(step['number'])}">{int(step['number']):02d}</span>
  <div>
   <div class="rl-meta">
    <span class="rl-status{' rl-status--gate' if is_gate else ''}">{status}</span>
    <span class="rl-date">Suggested timing: {_safe(step['due'])}</span>
   </div>
   <h4>{_safe(step['title'])}</h4>
  </div>
 </div>
 <div class="rl-facts">
  <div><span class="rl-label">Accountable role · proposed</span>
       <p>{_safe(step['owner'])}</p></div>
  <div class="rl-condition"><span class="rl-label">What changes the decision</span>
       <p>{_safe(step['condition'])}</p></div>
 </div>
 <details class="rl-details">
  <summary>View execution and approval evidence</summary>
  <div class="rl-detail-grid">
   <div><span class="rl-label">Required action</span><p>{_safe(step['action'],650)}</p></div>
   <div><span class="rl-label">Evidence to accept</span><p>{_safe(step['evidence'],650)}</p></div>
  </div>
 </details>
</article>""")
    remaining = gates[3:]
    extras = ""
    if remaining:
        labels = "".join("<li>"+_safe(CATALOG.get(k, (k,))[0])+"</li>" for k in remaining)
        extras = f'<p>Additional release gates also require closure:</p><ul class="rl-extra">{labels}</ul>'
    if gates:
        summary = (
            f"{len(gates)} critical release condition{'s' if len(gates)!=1 else ''} "
            "must be resolved before the decision can change."
        )
        meta = f'<div class="rl-stat"><strong>{len(gates):02d}</strong><span>Critical gates</span></div>'
        conclusion = "The next review requires approved closure evidence for all critical gates. Completion of the three actions alone does not authorize deployment."
    else:
        summary = "Three focused priorities for the next controlled decision."
        meta = '<div class="rl-stat"><strong>03</strong><span>Next actions</span></div>'
        conclusion = "Reassess these conditions at the next release decision. Readiness scores are not authorization to deploy."
    return ACTION_PLAN_CSS+f"""
<section class="rl-plan" aria-label="Executive action plan">
 <div class="rl-plan-top">
  <div><span class="rl-eyebrow">Executive action plan · Decision requirements</span>
   <h3>Three priorities. Clear release conditions.</h3>
   <p class="rl-plan-intro">{_safe(summary)}</p>
  </div>
  {meta}
 </div>
 <div class="rl-stack">{''.join(cards)}</div>
 <div class="rl-decision-strip">
  <strong>Next executive decision</strong>
  <p>{_safe(conclusion)}</p>{extras}
 </div>
 <p class="rl-footnote">Suggested roles and timings are advisory recommendations, not confirmed client commitments. Detailed action evidence appears only when expanded.</p>
</section>""".strip()


def render_action_plan(data: dict, result: dict) -> None:
    import streamlit as st
    st.markdown(action_plan_html(data,result),unsafe_allow_html=True)
