from __future__ import annotations

"""An original, decision-ready AI adaptation of the seven precision-question lenses.

This guide is rendered as first-party HTML, independent of CMS-generated article
layouts. The original published CMS article remains available as source context.
"""

from html import escape
from briefings_visual import briefing_icon

LENSES = (
    {
        "name": "Go / No Go", "icon": "target", "phase": "Relevance",
        "purpose": "Establish whether there is a decision worth making—and whether AI is the right response.",
        "core": (
            "What business decision or process needs to improve, and why now?",
            "What is the cost of leaving the process as it is?",
            "Would a simpler rule, process change or conventional automation solve it?",
        ),
        "power": "If this proposal were cancelled today, what measurable business problem would remain?",
        "request": "A named process owner, the current baseline and the cost of doing nothing.",
        "warning": "The proposal begins with a model, vendor or demo rather than a business problem.",
        "gate": "Proceed only when the problem and expected value justify investigation.",
    },
    {
        "name": "Clarify Meaning", "icon": "search", "phase": "Precision",
        "purpose": "Remove the ambiguity behind familiar AI labels before the team agrees to a solution.",
        "core": (
            "What will AI actually do: inform, recommend, draft or execute?",
            "Which task, user and decision boundary are in scope?",
            "What does 'accurate', 'autonomous' or 'ready to scale' mean here?",
        ),
        "power": "Show me one real case from input to outcome, including where a person intervenes.",
        "request": "A plain-language use case, a sample workflow and explicit human decision rights.",
        "warning": "Different stakeholders describe different levels of autonomy or expected outcomes.",
        "gate": "Define the job, the boundary and the approver before committing resources.",
    },
    {
        "name": "Challenge Assumptions", "icon": "shield", "phase": "Challenge",
        "purpose": "Test the beliefs on which the business case depends, not just the technology claim.",
        "core": (
            "What must be true about our data, users and workflow for this to pay off?",
            "Which assumption is both uncertain and capable of invalidating the case?",
            "What would a skeptical operations manager say we have missed?",
        ),
        "power": "What finding would make us stop, redesign or choose a non-AI option?",
        "request": "The three most consequential assumptions, each with an owner and a falsification test.",
        "warning": "The team lists benefits confidently but cannot name conditions for failure.",
        "gate": "Test the highest-risk assumption before expanding the experiment.",
    },
    {
        "name": "Critical Check", "icon": "check", "phase": "Evidence",
        "purpose": "Separate demonstrations, opinions and forecasts from evidence fit for investment.",
        "core": (
            "What is observed, what is estimated and what is still an assertion?",
            "Which representative cases and failure scenarios were evaluated?",
            "Compared with what baseline—and who verified the results?",
        ),
        "power": "Would this evidence still hold with real users, messy data and exceptions?",
        "request": "Source provenance, an evaluation set, quality thresholds and a comparison with today's process.",
        "warning": "A curated demo or model accuracy metric is presented as proof of operational value.",
        "gate": "Do not approve scale on evidence that cannot survive a realistic test.",
    },
    {
        "name": "Explore Causes", "icon": "workflow", "phase": "Diagnosis",
        "purpose": "Find the actual constraint in the end-to-end process before treating a symptom with AI.",
        "core": (
            "Where does delay, cost, rework or poor quality originate?",
            "Is the bottleneck a knowledge gap, policy, hand-off, data defect or decision?",
            "Which upstream condition would make this AI feature unnecessary?",
        ),
        "power": "If we removed the symptom, would the underlying process still fail?",
        "request": "A process map, root-cause hypothesis and evidence about the true constraint.",
        "warning": "AI is being placed on top of a broken hand-off or unreliable source system.",
        "gate": "Fix or account for root causes; then test whether AI adds incremental value.",
    },
    {
        "name": "Consider Effects", "icon": "layers", "phase": "Consequences",
        "purpose": "Examine second-order effects as well as the attractive first-order benefit.",
        "core": (
            "What changes for employees, customers and downstream teams if this succeeds?",
            "Where can an incorrect recommendation, automation or data exposure cause harm?",
            "What are the likely, best and adverse outcomes over three and twelve months?",
        ),
        "power": "What new work, controls or dependency will we create by removing the old one?",
        "request": "A risk-and-dependency view, escalation path and human override or rollback design.",
        "warning": "Only time saved is counted; review effort, exceptions and accountability are excluded.",
        "gate": "Accept the trade-off explicitly and identify who owns each material consequence.",
    },
    {
        "name": "Drive to Action", "icon": "chart", "phase": "Commitment",
        "purpose": "Convert the discussion into a small, testable decision with ownership and an exit rule.",
        "core": (
            "What decision are we taking today: stop, fix, test, invest or scale?",
            "Who is accountable, which resources are approved and when will we review?",
            "What change in adoption, cost, quality, speed or productivity will count as success?",
        ),
        "power": "If this were reviewed in six weeks, what evidence would earn the next investment?",
        "request": "A decision record, one accountable owner, a review date and measurable continue/stop gates.",
        "warning": "Everyone agrees to 'explore AI' but nobody owns a test, measure or next decision.",
        "gate": "Leave the room with a decision, owner, evidence threshold and review date.",
    },
)

SEVEN_QUESTIONS_CSS = r'''<style>
.site .aiq-guide-reader{background:#f4f0e8}
.site .aiq-guide-reader *{min-width:0}
.site .aiq-guide-reader .aiq-guide-container{width:min(1100px,calc(100% - 40px));margin-inline:auto}
.site .aiq-guide-reader .aiq-guide-top{padding:35px 0 29px}
.site .aiq-guide-reader .aiq-thesis{border-left:4px solid #b77953;background:#fffdf8;padding:24px 28px;box-shadow:0 9px 24px rgba(16,30,42,.035)}
.site .aiq-guide-reader .aiq-thesis h2{font:500 clamp(27px,3.4vw,40px)/1.16 Georgia,serif;color:#142a3f;margin:8px 0 11px}
.site .aiq-guide-reader .aiq-thesis p{font:400 15px/1.7 Arial,sans-serif;color:#435363;margin:0;max-width:940px}
.site .aiq-guide-reader .aiq-kicker{display:block;color:#a65f3b;font:800 10px/1.45 Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase}
.site .aiq-guide-reader .aiq-path{margin:22px 0 0;padding:22px 23px;background:#14283a;color:#fff}
.site .aiq-guide-reader .aiq-path-head{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
.site .aiq-guide-reader .aiq-path-head strong{font:500 21px/1.3 Georgia,serif;color:#fff}
.site .aiq-guide-reader .aiq-path-head span{font:400 12px/1.5 Arial,sans-serif;color:#c1ccd4}
.site .aiq-guide-reader .aiq-path-links{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:7px;margin-top:18px}
.site .aiq-guide-reader .aiq-path-links a{display:flex;flex-direction:column;justify-content:space-between;gap:9px;min-height:86px;padding:12px 10px;border:1px solid #547085;color:#e9f0f4!important;background:#1d3549;text-decoration:none!important;font:700 11px/1.35 Arial,sans-serif;overflow-wrap:normal;word-break:normal}
.site .aiq-guide-reader .aiq-path-links a:hover,.site .aiq-guide-reader .aiq-path-links a:focus-visible{background:#30516b;outline:2px solid #e4b693;outline-offset:1px}
.site .aiq-guide-reader .aiq-path-links em{font:800 10px/1.3 Arial,sans-serif;color:#e9b791;font-style:normal}
.site .aiq-guide-reader .aiq-lenses{padding:19px 0 48px}
.site .aiq-guide-reader .aiq-lens{margin:0 0 15px;background:#fffdf8;border:1px solid #d8d7d1;border-left:4px solid #bf8967;box-shadow:0 5px 21px rgba(15,37,53,.035);scroll-margin-top:94px;overflow:visible}
.site .aiq-guide-reader .aiq-lens-head{display:flex;gap:17px;align-items:flex-start;padding:23px 28px 18px;border-bottom:1px solid #e2dfd8}
.site .aiq-guide-reader .aiq-lens-number{flex:0 0 42px;display:grid;place-items:center;width:42px;height:42px;background:#142c40;color:#f3c5a5;font:800 17px/1 Arial,sans-serif}
.site .aiq-guide-reader .aiq-lens-name{flex:1}
.site .aiq-guide-reader .aiq-lens-name h2{font:500 clamp(25px,3vw,33px)/1.15 Georgia,serif;margin:3px 0 7px;color:#14293b}
.site .aiq-guide-reader .aiq-lens-name p{font:400 14px/1.65 Arial,sans-serif;margin:0;color:#57616b;max-width:850px}
.site .aiq-guide-reader .aiq-lens-head .briefing-icon{flex:0 0 24px;color:#a66c4d;margin-top:9px}
.site .aiq-guide-reader .aiq-lens-body{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:0}
.site .aiq-guide-reader .aiq-core{padding:24px 29px 27px}
.site .aiq-guide-reader .aiq-core ul{list-style:none;margin:13px 0 0;padding:0;display:grid;gap:11px}
.site .aiq-guide-reader .aiq-core li{position:relative;padding-left:23px;color:#263d50;font:600 14px/1.57 Arial,sans-serif;overflow-wrap:break-word;word-break:normal}
.site .aiq-guide-reader .aiq-core li:before{content:"";position:absolute;left:0;top:.53em;width:8px;height:8px;border:2px solid #b67953;border-radius:50%}
.site .aiq-guide-reader .aiq-power{padding:24px 28px 27px;background:#edf0ef;border-left:1px solid #d8dfde}
.site .aiq-guide-reader .aiq-power blockquote{margin:12px 0 21px;padding:0;color:#18364c;font:500 clamp(17px,2vw,21px)/1.43 Georgia,serif}
.site .aiq-guide-reader .aiq-power p{margin:0;color:#3d515d;font:400 13px/1.65 Arial,sans-serif}
.site .aiq-guide-reader .aiq-power p strong{color:#16374d}
.site .aiq-guide-reader .aiq-gates{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0;border-top:1px solid #dfded8}
.site .aiq-guide-reader .aiq-gates>div{padding:18px 29px 21px}
.site .aiq-guide-reader .aiq-gates>div+div{border-left:1px solid #dfded8}
.site .aiq-guide-reader .aiq-gates p{font:400 13px/1.62 Arial,sans-serif;color:#445460;margin:7px 0 0}
.site .aiq-guide-reader .aiq-gates .aiq-red{color:#9a533a}
.site .aiq-guide-reader .aiq-gates .aiq-green{color:#336b59}
.site .aiq-guide-reader .aiq-example{margin:0 0 15px;background:#142c40;color:#f6f6f3;padding:28px 32px}
.site .aiq-guide-reader .aiq-example h2{font:500 28px/1.2 Georgia,serif;color:#fff;margin:8px 0 11px}
.site .aiq-guide-reader .aiq-example p{font:400 14px/1.68 Arial,sans-serif;color:#dae3e8;margin:0}
.site .aiq-guide-reader .aiq-example strong{color:#f2c5a3}
.site .aiq-guide-reader .aiq-example-steps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;margin:19px 0 0}
.site .aiq-guide-reader .aiq-example-steps div{padding:13px 15px;background:#203e54;border:1px solid #446177}
.site .aiq-guide-reader .aiq-example-steps span{display:block;color:#edbe9c;font:800 10px/1.4 Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase}
.site .aiq-guide-reader .aiq-example-steps p{margin:5px 0 0;font-size:12px}
.site .aiq-guide-reader .aiq-playbook{padding:28px 31px;background:#e8e0d5;border:1px solid #d4c8b8}
.site .aiq-guide-reader .aiq-playbook h2{font:500 31px/1.17 Georgia,serif;margin:9px 0 11px;color:#192e40}
.site .aiq-guide-reader .aiq-playbook>p{margin:0 0 18px;font-size:14px;line-height:1.6;color:#4a5862}
.site .aiq-guide-reader .aiq-playbook-steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}
.site .aiq-guide-reader .aiq-playbook-steps>div{padding:16px;background:#fffdf8;border-top:3px solid #b67c58}
.site .aiq-guide-reader .aiq-playbook-steps strong{display:block;font:750 14px/1.4 Arial,sans-serif;color:#1a3447}
.site .aiq-guide-reader .aiq-playbook-steps span{display:block;margin:7px 0;color:#92563a;font-size:11px;font-weight:800}
.site .aiq-guide-reader .aiq-playbook-steps p{margin:0;font:400 12px/1.6 Arial,sans-serif;color:#4c5c64}
.site .aiq-guide-reader .aiq-decision-record{margin-top:15px;padding:25px 30px;background:#fffdf8;border:1px solid #d7d6d1}
.site .aiq-guide-reader .aiq-decision-record h3{font:500 24px/1.18 Georgia,serif;color:#1d3344;margin:7px 0}
.site .aiq-guide-reader .aiq-record-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px 20px;padding:13px 0 0}
.site .aiq-guide-reader .aiq-record-list p{padding:8px 0;border-bottom:1px solid #e1dfd8;margin:0;font:400 13px/1.6 Arial,sans-serif;color:#40515e}
.site .aiq-guide-reader .aiq-record-list strong{color:#172d41}
.site .aiq-guide-reader .aiq-credit{font:400 11px/1.65 Arial,sans-serif;color:#68727b;margin:21px 0 0}
.site .aiq-guide-reader .aiq-research{padding:0 0 45px}
.site .aiq-guide-reader .aiq-research .briefing-reader-detail{margin-top:0}
.site .aiq-guide-reader .aiq-research .briefing-reader-research{min-width:0;overflow-wrap:break-word}
.site .aiq-guide-reader .briefing-reader-share{margin-top:18px}
@media(max-width:1050px){
 .site .aiq-guide-reader .aiq-path-links{grid-template-columns:repeat(4,minmax(0,1fr))}
 .site .aiq-guide-reader .aiq-path-links a{min-height:70px}
}
@media(max-width:780px){
 .site .aiq-guide-reader .aiq-lens-body{grid-template-columns:minmax(0,1fr)}
 .site .aiq-guide-reader .aiq-power{border-left:0;border-top:1px solid #d8dfde}
 .site .aiq-guide-reader .aiq-playbook-steps{grid-template-columns:repeat(2,minmax(0,1fr))}
 .site .aiq-guide-reader .aiq-gates{grid-template-columns:minmax(0,1fr)}
 .site .aiq-guide-reader .aiq-gates>div+div{border-left:0;border-top:1px solid #dfded8}
}
@media(max-width:520px){
 .site .aiq-guide-reader .aiq-guide-container{width:calc(100% - 26px)}
 .site .aiq-guide-reader .aiq-guide-top{padding-top:21px}
 .site .aiq-guide-reader .aiq-thesis{padding:20px}
 .site .aiq-guide-reader .aiq-path{padding:18px}
 .site .aiq-guide-reader .aiq-path-links{grid-template-columns:repeat(2,minmax(0,1fr))}
 .site .aiq-guide-reader .aiq-lens-head{padding:20px 18px;gap:10px}
 .site .aiq-guide-reader .aiq-lens-head .briefing-icon{display:none}
 .site .aiq-guide-reader .aiq-core,.site .aiq-guide-reader .aiq-power{padding:20px}
 .site .aiq-guide-reader .aiq-gates>div{padding:17px 20px}
 .site .aiq-guide-reader .aiq-example{padding:20px}
 .site .aiq-guide-reader .aiq-example-steps,.site .aiq-guide-reader .aiq-record-list{grid-template-columns:minmax(0,1fr)}
 .site .aiq-guide-reader .aiq-playbook{padding:20px}
 .site .aiq-guide-reader .aiq-playbook-steps{grid-template-columns:minmax(0,1fr)}
 .site .aiq-guide-reader .aiq-decision-record{padding:20px}
}
</style>'''


def _questions(questions: tuple[str, ...]) -> str:
    return "".join(f"<li>{escape(question)}</li>" for question in questions)


def _lens(index: int, lens: dict) -> str:
    n = f"{index:02d}"
    return (
        f'<article class="aiq-lens" id="aiq-lens-{index}" data-analytics-section="aiq-lens-{index}">'
        '<header class="aiq-lens-head">'
        f'<span class="aiq-lens-number" aria-label="Question lens {index}">{n}</span>'
        '<div class="aiq-lens-name">'
        f'<span class="aiq-kicker">{escape(lens["phase"])}</span>'
        f'<h2>{escape(lens["name"])}</h2><p>{escape(lens["purpose"])}</p></div>'
        + briefing_icon(lens["icon"]) + '</header>'
        '<div class="aiq-lens-body"><div class="aiq-core">'
        '<span class="aiq-kicker">Core questions · ask the team</span>'
        f'<ul>{_questions(lens["core"])}</ul></div>'
        '<aside class="aiq-power"><span class="aiq-kicker">Power prompt · challenge the room</span>'
        f'<blockquote>“{escape(lens["power"])}”</blockquote>'
        f'<p><strong>Evidence to request:</strong> {escape(lens["request"])}</p></aside></div>'
        '<div class="aiq-gates"><div><span class="aiq-kicker aiq-red">Warning signal</span>'
        f'<p>{escape(lens["warning"])}</p></div>'
        '<div><span class="aiq-kicker aiq-green">Decision rule</span>'
        f'<p>{escape(lens["gate"])}</p></div></div></article>'
    )


def seven_questions_body() -> str:
    path = "".join(
        f'<a href="#aiq-lens-{index}" aria-label="Go to {escape(lens["name"], quote=True)}">'
        f'<em>{index:02d}</em><span>{escape(lens["name"])}</span></a>'
        for index, lens in enumerate(LENSES, 1)
    )
    lenses = "".join(_lens(index, lens) for index, lens in enumerate(LENSES, 1))
    return (
        '<div class="aiq-guide-container">'
        '<section class="aiq-guide-top" data-analytics-section="aiq-decision-framing">'
        '<div class="aiq-thesis"><span class="aiq-kicker">The executive premise</span>'
        '<h2>Seven lenses. One defensible decision.</h2>'
        '<p>When an AI proposal reaches the leadership table, your job is not to ask for a better demo. '
        'It is to establish relevance, precision, assumptions, evidence, causes, consequences and an '
        'accountable next move. Use all seven for an investment review, or select the two or three '
        'that expose the weakness in a live discussion.</p></div>'
        '<nav class="aiq-path" aria-label="Jump to the seven decision lenses">'
        '<div class="aiq-path-head"><strong>The executive questioning sequence</strong>'
        '<span>Start with the decision. Finish with commitment.</span></div>'
        f'<div class="aiq-path-links">{path}</div></nav></section>'
        '<section class="aiq-lenses" aria-label="Seven AI decision questions">'
        f'{lenses}'
        '<aside class="aiq-example" data-analytics-section="aiq-example">'
        '<span class="aiq-kicker" style="color:#f3c3a2">Applied example · illustrative scenario</span>'
        '<h2>An AI assistant for service-case triage</h2>'
        '<p>Imagine a proposal to add an AI assistant to a backlog of service cases. '
        'The first question is not which model to deploy. It is whether the backlog comes from '
        'poor case routing, missing data or a shortage of decision capacity. '
        'The seven lenses change the investment conversation:</p>'
        '<div class="aiq-example-steps">'
        '<div><span>01–02 · Frame</span><p>Specify the queue-time problem; separate recommendation from autonomous routing.</p></div>'
        '<div><span>03–04 · Test</span><p>Validate data quality and compare representative cases against today’s manual baseline.</p></div>'
        '<div><span>05–06 · Anticipate</span><p>Check whether upstream defects cause the backlog and how wrong routing will be corrected.</p></div>'
        '<div><span>07 · Commit</span><p>Authorize a bounded test only with an owner, measured adoption, error threshold and review date.</p></div>'
        '</div></aside>'
        '<section class="aiq-playbook" data-analytics-section="aiq-meeting-playbook">'
        '<span class="aiq-kicker">Put it to work</span><h2>A 15-minute executive decision review</h2>'
        '<p>Do not ask all twenty-one core questions aloud. Use the sequence to choose the few that can change today’s decision.</p>'
        '<div class="aiq-playbook-steps">'
        '<div><strong>Frame the choice</strong><span>Minutes 0–3</span><p>Go / No Go and Clarify Meaning. Establish the outcome and what AI may do.</p></div>'
        '<div><strong>Pressure-test the case</strong><span>Minutes 3–8</span><p>Challenge Assumptions and Critical Check. Demand one falsifiable claim and credible evidence.</p></div>'
        '<div><strong>Examine the system</strong><span>Minutes 8–12</span><p>Explore Causes and Consider Effects. Identify root cause, dependencies and downside.</p></div>'
        '<div><strong>Make the call</strong><span>Minutes 12–15</span><p>Drive to Action. Decide stop, fix, test, invest or scale; assign the next review.</p></div>'
        '</div></section>'
        '<section class="aiq-decision-record" data-analytics-section="aiq-decision-record">'
        '<span class="aiq-kicker">Takeaway · decision record</span>'
        '<h3>What should be written down before the meeting ends?</h3>'
        '<div class="aiq-record-list">'
        '<p><strong>Business decision:</strong> what we are approving or declining</p>'
        '<p><strong>Process and baseline:</strong> what will improve and from where</p>'
        '<p><strong>Accountable owner:</strong> one name with decision rights</p>'
        '<p><strong>Assumption to test:</strong> what could invalidate the case</p>'
        '<p><strong>Evidence threshold:</strong> adoption, cost, quality, speed or productivity</p>'
        '<p><strong>Guardrail:</strong> failure condition, escalation and rollback</p>'
        '<p><strong>Next action:</strong> specific owner, resource and deliverable</p>'
        '<p><strong>Review gate:</strong> date and criteria to stop, adjust or expand</p>'
        '</div></section>'
        '<p class="aiq-credit">Editorial note: the seven questioning categories were inspired by '
        'Vervago’s Precision Questions &amp; Answers framework. The AI-specific questions, '
        'decision gates and examples here are original executive interpretations, '
        'not a reproduction of that framework.</p>'
        '</section></div>'
    )
