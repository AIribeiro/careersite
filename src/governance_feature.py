"""A responsive, source-grounded featured AI & Data Governance infographic."""

GOVERNANCE_FEATURE = r'''
<style>
.site .gf{isolation:isolate;position:relative;background:radial-gradient(ellipse at 5% 6%,#104764 0%,transparent 32%),linear-gradient(130deg,#051525,#092b45);color:#eefaff;padding:clamp(64px,7vw,112px) 0;content-visibility:auto;contain-intrinsic-size:auto 1850px}
.site .gf *{box-sizing:border-box}
.site .gf .gw{width:min(1480px,calc(100% - 44px));margin:auto}
.site .gf .intro{display:flex;gap:50px;align-items:end;justify-content:space-between;margin-bottom:34px}
.site .gf .ey{font:800 11px Inter,sans-serif;letter-spacing:.18em;color:#6ae4fc;text-transform:uppercase;margin:0}
.site .gf h2{color:#fff;font:750 clamp(40px,5.5vw,76px)/1.03 Inter,sans-serif;letter-spacing:-.055em;margin:17px 0 0}
.site .gf h2 em{font-style:normal;color:#69dff6}
.site .gf .deck{color:#b5d4e3;font:450 clamp(15px,1.45vw,19px)/1.6 Inter,sans-serif;max-width:390px;margin:0}
.site .gf .infographic{margin:0;border:1px solid #397999;border-radius:24px;background:linear-gradient(130deg,#09283d,#061b30 60%,#0a3249);padding:clamp(20px,3vw,47px);box-shadow:0 32px 85px rgba(0,0,0,.27)}
.site .gf .meta{display:flex;justify-content:space-between;gap:12px;color:#75dcef;font:800 10px Inter,sans-serif;letter-spacing:.17em;text-transform:uppercase;margin:0 0 23px}
.site .gf .two{display:grid;grid-template-columns:1fr 1fr;gap:15px}
.site .gf .foundation{background:rgba(17,112,153,.18);border:1px solid #326b88;border-radius:16px;padding:24px;min-width:0}
.site .gf .foundation h3{font:750 23px Inter,sans-serif;color:white;margin:0 0 12px}
.site .gf .foundation p{font:480 14px/1.7 Inter,sans-serif;color:#b9d7e6;margin:0}
.site .gf .foundation h3:before{content:"";display:inline-block;width:14px;height:14px;border:2px solid #73ebff;border-radius:4px;margin-right:12px}
.site .gf .converge{display:flex;align-items:center;gap:16px;text-align:center;justify-content:center;margin:25px 0 14px;font:800 12px Inter,sans-serif;letter-spacing:.1em;color:#63dff7;text-transform:uppercase}
.site .gf .converge:before,.site .gf .converge:after{content:"";height:1px;flex:1;max-width:200px;background:#225b7a}
.site .gf .account{border-radius:11px;border:1px solid #2f7a99;background:#0c3c59;color:#d7f3fa;padding:16px;text-align:center;font:650 15px/1.55 Inter,sans-serif}
.site .gf .account b{color:#6eebff}
.site .gf .label{font:800 11px/1.5 Inter,sans-serif;letter-spacing:.13em;text-transform:uppercase;color:#69e4f9;margin:0 0 15px}
.site .gf .operating{display:grid;grid-template-columns:minmax(190px,.95fr) minmax(420px,1.9fr) minmax(205px,1fr);gap:15px;margin-top:27px}
.site .gf .panel{border:1px solid #2a5672;border-radius:16px;background:rgba(4,28,48,.6);padding:21px 19px;min-width:0}
.site .gf ul,.site .gf ol{padding:0;margin:0;list-style:none}
.site .gf .panel li{padding:10px 0;border-bottom:1px solid #204560}
.site .gf .panel li:last-child{border:0}
.site .gf .panel li strong{display:block;color:#eefbff;font:750 14px/1.3 Inter,sans-serif}
.site .gf .panel li span{display:block;margin-top:6px;color:#a7c4d3;font:450 12px/1.5 Inter,sans-serif}
.site .gf .principles li strong{color:#b7eeff}
.site .gf .cycle{padding:23px 8px 15px;text-align:center;background:radial-gradient(circle at 50% 48%,rgba(12,111,144,.24),transparent 66%),#061f35}
.site .gf .cycle p.sub{color:#9dbfd0;font:450 12px/1.5 Inter,sans-serif;margin:0}
.site .gf .stage{position:relative;width:100%;max-width:590px;aspect-ratio:1;margin:0 auto}
.site .gf .ring{position:absolute;inset:5%;width:90%;height:90%;overflow:visible}
.site .gf .ring circle{fill:none;stroke:#2389ad;stroke-width:2;stroke-dasharray:5 8}
.site .gf .ring path{fill:none;stroke:#39d4ee;stroke-width:4;stroke-linecap:round}
.site .gf .node{position:absolute;left:var(--x);top:var(--y);transform:translate(-50%,-50%);width:31%;min-height:82px;background:linear-gradient(145deg,#e8fbff,#b8dfef);color:#0b354c;border-radius:13px;border:1px solid #80d9ef;padding:10px 8px;box-shadow:0 10px 20px #0003}
.site .gf .node b{font:800 14px Inter,sans-serif}
.site .gf .node small{font:900 11px Inter,sans-serif;color:#12748f;margin-right:7px}
.site .gf .node span{display:block;font:500 11px/1.35 Inter,sans-serif;margin-top:5px}
.site .gf .core{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:41%;aspect-ratio:1;border-radius:50%;border:2px solid #50e7fa;background:#092c43;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;box-shadow:0 0 38px #00c8f326}
.site .gf .core small{font:850 10px Inter,sans-serif;letter-spacing:.1em;color:#78ecfd}
.site .gf .core strong{color:#fff;font:850 clamp(18px,1.65vw,25px)/1.06 Inter,sans-serif;margin:8px 0}
.site .gf .core span{font:550 12px/1.4 Inter,sans-serif;color:#b9e6f0}
.site .gf .cycle .footnote{font:550 11px/1.6 Inter,sans-serif;color:#8eafc4;margin:0 14px}
.site .gf .bottom{display:grid;grid-template-columns:1fr 1.14fr .9fr;gap:15px;margin-top:15px}
.site .gf .bottom .panel li{border:1px solid #29516b;border-radius:8px;background:#11354a;padding:9px 11px;margin-bottom:7px}
.site .gf .bottom .panel li:last-child{margin-bottom:0;border:1px solid #29516b}
.site .gf .bottom .panel li strong{font-size:12px;color:#e8faff}
.site .gf .bottom .panel li span{margin-top:2px;font-size:11px}
.site .gf .bottom .approval li{display:flex;align-items:start;gap:10px}
.site .gf .approval i{font:900 11px Inter,sans-serif;font-style:normal;flex:0 0 23px;height:23px;border-radius:50%;background:#aee8f4;color:#0b3449;display:grid;place-items:center}
.site .gf .response li{border-left:3px solid #6de3f2!important}
.site .gf .response li:last-child{border-left-color:#dbab7a!important}
.site .gf .signals{border:1px solid #46adcb;border-radius:16px;background:#0b354e;margin-top:15px;padding:25px 14px}
.site .gf .signals h3{font:750 13px Inter,sans-serif;letter-spacing:.11em;text-align:center;margin:0 0 23px;color:#d5f6fc}
.site .gf .four{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))}
.site .gf .four div{text-align:center;border-right:1px solid #37728c;padding:0 12px}
.site .gf .four div:last-child{border:0}
.site .gf .four strong{font:850 clamp(20px,2.2vw,30px) Inter,sans-serif;color:#68eafd}
.site .gf .four span{display:block;color:#c2dce8;font:480 12px/1.5 Inter,sans-serif;margin-top:10px}
.site .gf .takeaway{background:linear-gradient(90deg,#c8f3fc,#80e0f4,#c4f2fd);color:#082b40;border-radius:12px;padding:19px 22px;margin:15px 0 0;text-align:center;font:750 clamp(17px,1.65vw,23px)/1.4 Inter,sans-serif}
.site .gf figcaption{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #2a5972;margin-top:24px;padding-top:18px;gap:15px}
.site .gf figcaption strong{font:750 20px Inter,sans-serif;color:#fff}
.site .gf figcaption small{display:block;margin-top:5px;color:#9fc5d4;font:500 12px Inter,sans-serif}
.site .gf figcaption .badge{border-radius:20px;border:1px solid #398fa7;padding:8px 14px;color:#76e3f7;font:800 10px Inter,sans-serif;letter-spacing:.13em}
.site .gf .after{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:27px}
.site .gf .after p{max-width:900px;font:480 15px/1.7 Inter,sans-serif;color:#b9d0dd;margin:0}
.site .gf .after a{border:1px solid #3b829b;padding:13px 16px;color:#c7effa;text-decoration:none;font:700 12px Inter,sans-serif;white-space:nowrap}
.site .gf .after a:hover{background:#124b63}
@media(max-width:1160px){
.site .gf .operating{grid-template-columns:1fr 1fr}
.site .gf .cycle{grid-column:1/-1;grid-row:1}
.site .gf .bottom{grid-template-columns:1fr 1fr}
.site .gf .bottom .response{grid-column:1/-1}
.site .gf .stage{max-width:580px}
}
@media(max-width:740px){
.site .gf{padding:54px 0}.site .gf .gw{width:calc(100% - 28px)}
.site .gf .intro{display:block}.site .gf .deck{margin:17px 0 0}
.site .gf .infographic{padding:17px;border-radius:15px}
.site .gf .two,.site .gf .operating,.site .gf .bottom{grid-template-columns:1fr}
.site .gf .cycle{grid-column:auto;grid-row:1}
.site .gf .bottom .response{grid-column:auto}
.site .gf .foundation{padding:18px}
.site .gf .meta{font-size:9px}.site .gf .after{display:block}
.site .gf .after a{display:block;text-align:center;white-space:normal;margin-top:20px}
.site .gf .four{grid-template-columns:1fr 1fr;row-gap:22px}
.site .gf .four div:nth-child(2){border:0}
}
@media(max-width:480px){
.site .gf .ring{display:none}
.site .gf .stage{aspect-ratio:auto;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding-top:115px}
.site .gf .node{position:static;transform:none;width:auto;min-height:89px}
.site .gf .core{left:0;top:0;transform:none;width:100%;height:107px;aspect-ratio:auto;border-radius:13px}
.site .gf .core strong{font-size:19px}.site .gf .core span{font-size:11px}
.site .gf .cycle .footnote{margin-top:12px}
.site .gf figcaption strong{font-size:17px}.site .gf figcaption small{font-size:10px}
}
</style>
<section id="governance-operating-model" class="gf" aria-labelledby="gf-title">
<div class="gw">
<header class="intro"><div><p class="ey">The governance operating system</p><h2 id="gf-title">AI &amp; Data Governance.<br><em>Designed to operate.</em></h2></div>
<p class="deck">From trusted data to accountable AI at scale. A visual operating model for the decisions, controls and ownership that make responsible use possible.</p></header>
<figure class="infographic" aria-label="Executive AI and Data Governance infographic connecting trusted data and AI governance with accountable decisions, a six-stage operating lifecycle, named owners, evidence and continuous assurance">
<div class="meta"><span>Executive operating model</span><span>Jair Ribeiro · AI Leadership</span></div>
<div class="two"><article class="foundation"><h3>Data Governance</h3><p>Ownership · Stewardship · Quality · Business definitions · Lineage · Access · Privacy · Retention</p></article><article class="foundation"><h3>AI Governance</h3><p>Use-case ownership · Risk classification · Human oversight · System evidence · Transparency · Monitoring · Incident response · Change control</p></article></div>
<div class="converge">Two disciplines, one operating conversation</div>
<div class="account"><b>SHARED ACCOUNTABILITY</b> &nbsp; Business purpose + Data + System behavior + Decision owner + Evidence</div>
<div class="operating">
<aside class="panel principles"><h3 class="label">01 / Four principles</h3><ol><li><strong>Boundaries</strong><span>What is the system permitted to do?</span></li><li><strong>Accountability</strong><span>Who owns the business consequence?</span></li><li><strong>Evidence</strong><span>What proof justifies wider use?</span></li><li><strong>Traceability</strong><span>Can outcomes be reconstructed?</span></li></ol></aside>
<div class="panel cycle"><h3 class="label">02 / Continuous governance lifecycle</h3><p class="sub">From purpose and risk to accountable operation</p>
<div class="stage">
<svg class="ring" viewBox="0 0 600 600" aria-hidden="true" focusable="false">
<defs><marker id="gov-arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7 Z" fill="#39d4ee"/></marker></defs>
<circle cx="300" cy="300" r="240"/>
<g marker-end="url(#gov-arrow)"><path d="M370 69 A240 240 0 0 1 499 165"/><path d="M537 271 A240 240 0 0 1 494 446"/><path d="M430 501 A240 240 0 0 1 234 533"/><path d="M166 501 A240 240 0 0 1 64 334"/><path d="M62 267 A240 240 0 0 1 166 101"/><path d="M232 70 A240 240 0 0 1 270 62"/></g>
</svg>
<div class="node" style="--x:50%;--y:11%"><small>01</small><b>Frame</b><span>Purpose and consequence</span></div><div class="node" style="--x:81%;--y:29%"><small>02</small><b>Classify</b><span>Risk and data sensitivity</span></div><div class="node" style="--x:81%;--y:70%"><small>03</small><b>Assign</b><span>Business, technical and data owners</span></div><div class="node" style="--x:50%;--y:89%"><small>04</small><b>Evidence</b><span>Controls and proof</span></div><div class="node" style="--x:19%;--y:70%"><small>05</small><b>Decide</b><span>Release or scale</span></div><div class="node" style="--x:19%;--y:29%"><small>06</small><b>Monitor</b><span>Learn and reassess</span></div>
<div class="core"><small>ACCOUNTABLE</small><strong>Executive<br>decision</strong><span>Release · Scale<br>Constrain · Stop</span></div>
</div>
<p class="footnote">Monitor and reassess when a material change means the original approval may no longer apply.</p></div>
<aside class="panel"><h3 class="label">03 / Six decision owners</h3><ul><li><strong>Business owner</strong><span>Purpose, value and business consequence</span></li><li><strong>Data owner / steward</strong><span>Meaning, quality, access and permitted use</span></li><li><strong>Product / technology owner</strong><span>Behavior, security and technical readiness</span></li><li><strong>Appropriate risk authority</strong><span>Residual exposure and escalation</span></li><li><strong>Portfolio / governance authority</strong><span>Scale, constrain, revise or stop</span></li><li><strong>Named operating owner</strong><span>Thresholds, incidents and reassessment</span></li></ul></aside>
</div>
<div class="bottom">
<section class="panel"><h3 class="label">04 / Operating mechanisms</h3><ul><li><strong>Trusted inputs</strong><span>Sources, quality, lineage and access</span></li><li><strong>Decision ownership</strong><span>Accountable owner and escalation</span></li><li><strong>Control by consequence</strong><span>Risk tier, evidence and oversight</span></li><li><strong>Traceability</strong><span>Versions and decision records</span></li><li><strong>Monitoring</strong><span>Drift, incidents and review thresholds</span></li><li><strong>Change control</strong><span>New model, data, users or purpose</span></li></ul></section>
<section class="panel approval"><h3 class="label">05 / Seven questions before “go”</h3><ol><li><i aria-hidden="true">1</i><div><strong>Purpose</strong><span>What workflow changes, and what if wrong?</span></div></li><li><i aria-hidden="true">2</i><div><strong>Data</strong><span>Are sources owned, understood and permitted?</span></div></li><li><i aria-hidden="true">3</i><div><strong>Accountability</strong><span>Who owns the outcome and can stop use?</span></div></li><li><i aria-hidden="true">4</i><div><strong>Boundaries</strong><span>Where is human judgment mandatory?</span></div></li><li><i aria-hidden="true">5</i><div><strong>Evidence</strong><span>What proof supports release and risk acceptance?</span></div></li><li><i aria-hidden="true">6</i><div><strong>Traceability</strong><span>Can material outcomes be reconstructed?</span></div></li><li><i aria-hidden="true">7</i><div><strong>Monitoring</strong><span>Which signals trigger intervention?</span></div></li></ol></section>
<section class="panel response"><h3 class="label">06 / Change and response</h3><ol><li><strong>Detect change</strong><span>Data, behavior, use or context shifts</span></li><li><strong>Escalate</strong><span>Notify the named decision authority</span></li><li><strong>Reassess</strong><span>Revisit controls and approval evidence</span></li><li><strong>Continue · restrict · stop</strong><span>Document the revised decision</span></li></ol></section>
</div>
<div class="signals"><h3>EXECUTIVE ASSURANCE · FOUR OBSERVABLE SIGNALS</h3><div class="four"><div><strong>KNOW</strong><span>Where material AI is used and why</span></div><div><strong>OWN</strong><span>Who owns the consequence</span></div><div><strong>EXPLAIN</strong><span>Evidence behind material outcomes</span></div><div><strong>RESPOND</strong><span>When and how to intervene</span></div></div></div>
<p class="takeaway">Governance is not a one-time approval. It is a continuous system of accountable decisions.</p>
<figcaption><div><strong>Jair Ribeiro</strong><small>Enterprise AI Adoption · Governance · Business Transformation</small></div><span class="badge">AI LEADER</span></figcaption>
</figure>
<div class="after"><p>A practical connection between data responsibility, AI use, consequence-based controls and continuous executive oversight. These are accountable functions, not prescribed job titles.</p><a href="#governance-evidence" data-hq-event="governance_model_experience">Explore the experience behind the model ↗</a></div>
</div></section>'''
