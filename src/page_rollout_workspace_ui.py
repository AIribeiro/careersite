"""Private executive UI elements for the Rollout Readiness Decision Advisor.

The view is read-only presentation; all data and auth checks remain in the
parent service. Static cards are not fake controls. Navigation uses Streamlit.
"""
from __future__ import annotations

from html import escape

WORKSPACE_CSS = """
<style>
.rl-workspace{max-width:1120px;margin:6px 0 18px;color:#182e43}
.rl-workspace *{box-sizing:border-box}
.rl-workspace .eyebrow{font:800 10px/1.45 Arial,sans-serif;
 text-transform:uppercase;letter-spacing:.17em;color:#a36c46}
.rl-workspace .hero{background:linear-gradient(130deg,#0e2136,#253c51);
 color:#fdfbf8;padding:clamp(24px,4vw,44px);border-bottom:4px solid #b68060}
.rl-workspace .hero .eyebrow{color:#e6b18c}
.rl-workspace h2{font:500 clamp(28px,3.5vw,43px)/1.13 Georgia,serif;
 letter-spacing:-.03em;margin:10px 0;color:inherit}
.rl-workspace .hero p{font-size:15px;line-height:1.65;max-width:690px;
 color:#d8e0e7;margin:10px 0 0}
.rl-workspace .summarybar{display:flex;flex-wrap:wrap;gap:18px;
 padding:14px 20px;background:#f8f4ec;border:1px solid #e0d7ca;border-top:0}
.rl-workspace .summarybar span{font:600 12px/1.5 Arial,sans-serif;color:#3d5266}
.rl-workspace .section-head{margin:24px 0 14px}
.rl-workspace .section-head h3{font:500 clamp(22px,2.6vw,30px)/1.2 Georgia,serif;
 letter-spacing:-.02em;margin:5px 0 8px;color:#182d42}
.rl-workspace .section-head p{font-size:13px;color:#607084;line-height:1.6;
 max-width:750px;margin:0}
.rl-workspace .three-col{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
 gap:12px;margin:14px 0}
.rl-workspace .three-col article{background:#fffdfa;border:1px solid #ddd7cc;
 padding:20px;min-width:0}
.rl-workspace .three-col strong{display:block;font:500 21px/1.25 Georgia,serif;
 color:#193047;margin:7px 0}
.rl-workspace .three-col p{font-size:13px;color:#556778;line-height:1.6;margin:0}
.rl-workspace .steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
 gap:12px;margin:18px 0 20px}
.rl-workspace .steps>div{background:#f6f4ef;border:1px solid #e0dcd5;padding:15px}
.rl-workspace .steps b{display:block;color:#a46c4b;font-size:12px;margin-bottom:5px}
.rl-workspace .steps strong{display:block;color:#173049;font-size:14px;margin-bottom:5px}
.rl-workspace .steps span{font-size:12px;color:#536678;line-height:1.5}
.rl-workspace .verdict{background:#fffdfa;border:1px solid #d9d5cd;
 border-left:5px solid #b07751;padding:clamp(19px,3vw,30px);margin:10px 0 14px}
.rl-workspace .verdict--halt{border-left-color:#a45d49}
.rl-workspace .verdict h2{font:500 clamp(25px,3.1vw,37px)/1.17 Georgia,serif;
 margin:7px 0 14px;color:#19314a}
.rl-workspace .verdict p{font-size:14px;line-height:1.7;margin:0;color:#374d60;max-width:900px}
.rl-workspace .verdict .decision{font:800 11px/1.4 Arial,sans-serif;
 text-transform:uppercase;letter-spacing:.13em;color:#9d5b42}
.rl-workspace .small-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
 gap:10px;margin:10px 0 22px}
.rl-workspace .small-metrics>div{background:#f7f3ec;border:1px solid #e5ddd0;padding:17px}
.rl-workspace .small-metrics strong{font:650 clamp(23px,2.8vw,32px)/1.2 Georgia,serif;
 display:block;color:#1a344c;margin-bottom:6px}
.rl-workspace .small-metrics span{font:700 10px/1.4 Arial,sans-serif;
 letter-spacing:.075em;text-transform:uppercase;color:#657587}
.rl-workspace .dimensions{background:#fffdfa;border:1px solid #e4ded5;padding:18px 20px}
.rl-workspace .dimension{display:grid;grid-template-columns:minmax(145px,1fr) minmax(0,2fr) 44px;
 align-items:center;gap:15px;margin:12px 0}
.rl-workspace .dimension span{font-size:12px;color:#394e61}
.rl-workspace .dimension .track{height:7px;border-radius:5px;background:#e7e3dc;overflow:hidden}
.rl-workspace .dimension .bar{height:100%;background:#a77b5d}
.rl-workspace .dimension strong{font-size:12px;text-align:right;color:#263b50}
.rl-workspace .provenance{background:#fbf5e8;border:1px solid #e9dcc8;
 padding:11px 15px;font-size:12px;color:#765536;line-height:1.5;margin:10px 0}
.rl-workspace .callout{background:#f1f4f4;border-left:3px solid #8ca1a4;
 padding:16px 19px;margin:18px 0;color:#3c5465;font-size:13px;line-height:1.65}
.rl-workspace .callout strong{display:block;color:#203c52;font-size:13px;margin-bottom:5px}
.st-key-native_advisory_content [data-testid="stPills"] button{white-space:nowrap}
@media(max-width:760px),(max-device-width:760px){
 .rl-workspace .three-col,.rl-workspace .steps{grid-template-columns:1fr}
 .rl-workspace .small-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}
 .rl-workspace .small-metrics>div{padding:11px}
 .rl-workspace .summarybar{gap:5px 12px}
 .rl-workspace .dimension{grid-template-columns:minmax(118px,1fr) minmax(0,1.2fr) 37px;gap:9px}
}
@media(max-width:420px),(max-device-width:420px){
 .rl-workspace .small-metrics{grid-template-columns:1fr 1fr}
 .rl-workspace .small-metrics>div:last-child{grid-column:span 2}
}
</style>
"""


def _s(value:object,limit:int=500)->str:
    return escape(str(value if value is not None else "")[:limit],quote=True)


def render_service_overview(approved:bool, reports:list[dict])->None:
    from streamlit import html
    last=reports[0] if reports else None
    html(WORKSPACE_CSS+f"""
<div class="rl-workspace">
 <section class="hero">
  <span class="eyebrow">Private executive decision advisory</span>
  <h2>From a successful pilot to a responsible scale decision.</h2>
  <p>Answer one focused readiness assessment. Get a reasoned recommendation
  on whether to advance, pause or validate more evidence, with the precise
  conditions your leadership team should resolve next.</p>
 </section>
 <div class="summarybar">
  <span>ACCESS · {"Individually approved" if approved else "Approval required"}</span>
  <span>FORMAT · One-session assessment</span>
  <span>HISTORY · {len(reports)} saved decision{"s" if len(reports)!=1 else ""}</span>
 </div>
 <div class="section-head"><span class="eyebrow">What you receive</span>
  <h3>One business decision. Three concrete outputs.</h3>
  <p>This is a decision advisory service, not a rollout tracker or a long-term project dashboard.</p>
 </div>
 <div class="three-col">
  <article><span class="eyebrow">01 · The verdict</span><strong>Proceed, test further or pause</strong>
   <p>Decision supported by readiness evidence, with critical risk gates taking precedence over averages.</p></article>
  <article><span class="eyebrow">02 · The priorities</span><strong>Three executive actions</strong>
   <p>Recommended accountable roles, timing, approval evidence and what would change the decision.</p></article>
  <article><span class="eyebrow">03 · The report</span><strong>A private decision brief</strong>
   <p>Five-dimension readiness profile, decision rationale and downloadable executive PDF.</p></article>
 </div>
 <div class="section-head"><span class="eyebrow">How it works</span>
  <h3>Focused input. Decision-ready output.</h3></div>
 <div class="steps">
  <div><b>01</b><strong>Describe the rollout</strong><span>Share the initiative, current stage, target scope and consequence of errors.</span></div>
  <div><b>02</b><strong>Answer 18 conditions</strong><span>Five short categories covering value, operations, governance, adoption and scale.</span></div>
  <div><b>03</b><strong>Review your recommendation</strong><span>Read the decision, resolve three priorities and download the private brief.</span></div>
 </div>
 <div class="callout"><strong>What the service does not do</strong>
  It does not certify regulatory compliance, authorize an AI deployment or replace an independent risk review.
  Assessment ratings are self-reported. Your data remains within the existing private Advisory access controls.</div>
</div>""")


def render_case_heading(record:dict)->None:
    from streamlit import html
    answers=record.get("answers") or {}
    ctx=answers.get("context") or {}
    is_demo=isinstance(answers.get("demo"),dict) and answers["demo"].get("is_demo") is True
    html(WORKSPACE_CSS+f"""
<div class="rl-workspace">
 <div class="section-head">
  <span class="eyebrow">Selected assessment · {_s(record.get("created_at","")[:10])}</span>
  <h3>{_s(ctx.get("use_case") or "AI rollout assessment",125)}</h3>
  <p>{_s(ctx.get("stage") or "")} · {_s(ctx.get("scope") or "")} · {_s(ctx.get("criticality") or "")} consequence</p>
 </div>
 {"<div class='provenance'><strong>Synthetic owner QA scenario.</strong> Figures and evidence references are fictional and must not be treated as actual client evidence.</div>" if is_demo else ""}
</div>""")


def render_verdict(result:dict,data:dict)->None:
    from streamlit import html
    from page_rollout_premium_pdf import _summary,build_action_plan
    plans=build_action_plan(data,result)
    summary=_summary(data,result,plans)
    count=len(result.get("critical_gates") or [])
    confidence=result.get("confidence","Unspecified")
    verdict=result.get("label","REVIEW REQUIRED")
    palette="verdict verdict--halt" if verdict in ("PAUSE SCALING","EVIDENCE INCOMPLETE") else "verdict"
    metrics="".join(
        f'<div><strong>{_s(value)}</strong><span>{_s(label)}</span></div>'
        for value,label in (
           (str(result.get("overall","—"))+"/100","Indicative readiness"),
           (str(count),"Critical release conditions"),
           (confidence,"Evidence confidence")
        )
    )
    dimensions="".join(
        f'<div class="dimension"><span>{_s(name)}</span>'
        f'<div class="track"><div class="bar" style="width:{max(0,min(int(score),100))}%"></div></div>'
        f'<strong>{int(score)}%</strong></div>'
        for name,score in result.get("dimensions",{}).items()
    )
    html(WORKSPACE_CSS+f"""
<div class="rl-workspace">
 <div class="{palette}">
  <span class="decision">Executive recommendation · {_s(verdict)}</span>
  <h2>{_s(result.get("verdict"),260)}</h2>
  <p>{_s(summary,1300)}</p>
 </div>
 <div class="small-metrics">{metrics}</div>
 <div class="section-head"><span class="eyebrow">Your readiness profile</span>
  <h3>Strengths, constraints and evidence.</h3>
  <p>Readiness percentages describe self-reported maturity. A high overall score cannot override an unresolved release gate.</p></div>
 <div class="dimensions">{dimensions}</div>
 <div class="callout"><strong>What the recommendation means</strong>
  {_s("Do not extend the rollout until critical release conditions have been reviewed and approved."
    if count else result.get("insight","Review the proposed next stage and acceptance evidence."),500)}
  Use the <strong>Action plan</strong> view for accountable next steps and the <strong>Evidence & report</strong> view for the assessment record.
 </div>
</div>""")
