"""Jobseeker reading of the signed-off Swedish AI & Data Market Review.

This is a separate editorial product over the *same* November evidence manifest.
No candidate profiles, private career-intelligence tables, personal forecasts,
new survey observations or privileged API endpoints are involved.
"""
from __future__ import annotations

from html import escape as html_escape
from io import BytesIO

from reportlab.platypus import KeepTogether, Spacer, PageBreak, CondPageBreak
from reportlab.lib.pagesizes import A4

from market_intelligence_v2 import validate_editorial, _value, _safe_url
from market_publication_design import (
    P, assemble, bars, decision_table, metric_cards, panel, section,
    source_family_methods, sources_table, styles,
)

EDITION = "sweden-ai-data-market-review-2026-11-v2-0-2"
TITLE = "Swedish AI & Data Market Review"
SUBTITLE = "Jobseeker Edition | Career decisions based on November 2026 evidence"
JOBSEEKER_ISSUE = "18 November 2026"
INTRO = (
    "Sweden's AI market produces plenty of headlines, but less evidence about "
    "which opportunities fit your next career move. This edition distinguishes "
    "a narrow sample of senior AI/Data advertisements from broader labour-market "
    "figures and turns five research readings into questions you can test in "
    "your own job search. Decide where to look, what to demonstrate and when "
    "to revise your approach."
)
VALUE = (
    "Five candidate perspectives and a practical 30-day decision framework "
    "help you test discovery channels, examine adjacent titles, present "
    "credible career evidence and assess geographic or contract options. "
    "This is a dated research snapshot, not a live vacancy database, "
    "salary benchmark or forecast of an individual's hiring prospects."
)
LIMITS = (
    "The selected JobTech figures cover senior advertisement titles only, "
    "not all AI/Data work or unique positions. The SCB national vacancies "
    "and non-advertised recruitment figures cover the whole economy, "
    "not a measured hidden AI job market. AI adoption, the barriers reported "
    "by a subset of non-adopters, business confidence and consulting-platform "
    "listings do not measure role-specific hiring demand. This report cannot "
    "establish salaries, an individual's fit, successful application channels "
    "or the probability or date of an offer."
)

STYLE = """
<style>
.ms-js-lead{background:#f8f6f1;border-top:3px solid #a97755;
 padding:clamp(20px,3vw,39px);margin:18px 0 25px;color:#173147}
.ms-js-lead .eyebrow,.ms-js-topic .eyebrow{font-size:11px;letter-spacing:.11em;
 font-weight:800;color:#946243;text-transform:uppercase}
.ms-js-lead h3,.ms-js-topic h3{font:500 clamp(27px,3.9vw,40px)/1.15 Georgia,serif;
 color:#142c41;margin:10px 0 15px}
.ms-js-lead p,.ms-js-topic p{font-size:15px;line-height:1.78;color:#354b5e}
.ms-js-topic{background:#fffefa;border:1px solid #dfd8cc;
 padding:clamp(20px,3vw,32px);margin:17px 0 22px}
.ms-js-topic h4{font-size:12px;font-weight:800;text-transform:uppercase;
 letter-spacing:.055em;color:#975f40;margin:18px 0 5px}
.ms-js-detail{border-bottom:1px solid #e1ddd4;padding:13px 0;
 font-size:13px;line-height:1.6;color:#4c6072}
.ms-js-detail strong{color:#1b344c}
.ms-js-action{background:#1b344a;color:#f9f7f1;padding:23px;margin:17px 0 21px}
.ms-js-action strong{color:#e6b18b}
.ms-js-action p{color:#e7ecf1;font-size:14px;line-height:1.7}
@media(max-width:700px){.ms-js-lead,.ms-js-topic{padding:19px}
 .ms-js-lead p,.ms-js-topic p{font-size:14px}}
</style>
"""

# Each finding is a genuinely candidate-oriented editorial judgment. All
# references must occur in the already-authorised executive edition manifest.
FINDINGS = (
    {
        "key": "visible_market",
        "title": "A job advertisement is one hiring channel, not the market",
        "signal": (
            "Statistics Sweden estimated 159,500 vacant jobs across the entire Swedish "
            "economy in Q2 2026, including about 127,500 advertised vacancies and 32,100 "
            "for which employers tried other recruitment methods. The components differ "
            "from the total because of survey rounding. They are economy-wide estimates, "
            "not AI-specific openings or completed hires."
        ),
        "reading": (
            "Some Swedish vacancies involve recruitment outside published "
            "advertisements, but the national survey does not measure a hidden AI job "
            "market or which channel produces interviews. Rather than assuming that "
            "networking outperforms applying, test suitable advertised roles, relevant "
            "existing relationships and a limited number of targeted company "
            "conversations as separate channels. Evaluate the qualified responses you "
            "actually receive."
        ),
        "action": (
            "Create a simple weekly search ledger with three columns: advertised "
            "roles, professional introductions and targeted company conversations. "
            "Record role fit, eligibility, outreach date, substantive reply, "
            "next step and interview. Compare qualified conversations, not just "
            "application volume. Keep the approach personal and relevant; avoid "
            "indiscriminate messaging."
        ),
        "alternative": (
            "The non-advertised national vacancies could be concentrated in "
            "occupations with little relevance to AI or Data professionals. "
            "Some advertised roles recruit through several channels. "
            "The survey does not tell us which channel works best for an "
            "individual or for a particular seniority level."
        ),
        "watch": (
            "Revisit the next comparable SCB vacancy release and actual responses "
            "to your outreach. Do not add SCB's national counts to a curated "
            "JobTech job-title series; they measure different things."
        ),
        "codes": ("scb_lor_2026q2_total", "scb_lor_2026q2_advertised",
                  "scb_lor_2026q2_other_channels"),
    },
    {
        "key": "role_discovery",
        "title": "Search for the responsibility, not only the AI title",
        "signal": (
            "The retrospectively reconstructed, title-classified JobTech sample records "
            "20 selected senior AI/Data advertisements in September and 29 in October "
            "2026 nationwide. It includes 13 in Stockholm and five in Västra Götaland in "
            "October. A 30-seed title basket can miss relevant positions, includes "
            "advertisements rather than confirmed distinct vacancies, and may change "
            "with retrospective API revisions."
        ),
        "reading": (
            "A small title basket cannot establish total AI/Data hiring demand, and the "
            "September-to-October difference is not evidence of sustained growth. An "
            "employer may describe AI responsibility under operations, digital, "
            "analytics, process, product or other management headings. Search by job "
            "content as well as title and verify decision rights, team scope and "
            "operating outcomes. Reject roles that conflict with your language, "
            "eligibility, location or level constraints."
        ),
        "action": (
            "Build three search baskets: explicit AI/Data leadership titles; "
            "adjacent business or digital roles with clear AI accountability; "
            "and interim or advisory mandates. Keep a written inclusion rule "
            "for each. Review roles for decision rights, team scope, adoption "
            "responsibility and business outcomes before applying."
        ),
        "alternative": (
            "Some adjacent jobs are primarily engineering, sales, delivery or "
            "general IT and will not fit a leadership candidate. A title "
            "basket may also be distorted by duplicate postings or API "
            "revisions. Broadening keywords without reviewing role content "
            "can waste time."
        ),
        "watch": (
            "Compare several complete JobTech months and broader employer role "
            "descriptions before calling a trend. The November 1-15 figures "
            "are incomplete and must not be compared with a full month."
        ),
        "codes": ("jobtech_v1_sep_se", "jobtech_v1_oct_se",
                  "jobtech_v1_oct_sto", "jobtech_v1_oct_vgr"),
    },
    {
        "key": "capability_proof",
        "title": "Show the operating capability behind the AI vocabulary",
        "signal": (
            "SCB's 2026 enterprise survey recorded AI use in 49% of enterprises with at "
            "least ten employees and 85% of large firms. Separately, 33% had staff "
            "conducting data analytics in-house. Among the narrower group of firms that "
            "considered AI but did not adopt it, 62% cited insufficient expertise, 43% "
            "privacy or data-protection concerns and 34% data-access or quality "
            "problems. These barriers can overlap and the categories cannot be added "
            "together."
        ),
        "reading": (
            "The SCB measures cover distinct populations and do not estimate employer "
            "demand for AI roles. They do identify some of the operating problems "
            "companies encounter. For a candidate, it is reasonable to test whether "
            "evidence of workflow change, data ownership, governance judgment and "
            "measurable outcomes matters more than a list of AI tools. Show only "
            "verifiable contributions and ask each hiring team what the role must "
            "actually deliver."
        ),
        "action": (
            "Rewrite two or three career examples in the same evidence sequence: "
            "business problem, your decision or contribution, operating "
            "dependencies, verifiable outcome and what you would change "
            "next time. Prepare a 30-second version for introductions and "
            "a longer one for interviews. Keep project involvement separate "
            "from measurable production impact."
        ),
        "alternative": (
            "Some businesses use external analytics teams appropriately, "
            "and firms that reject AI for data or privacy reasons may be "
            "making sound decisions. Neither the existence of internal "
            "analysts nor AI use itself certifies organisational maturity."
        ),
        "watch": (
            "Check individual job descriptions and interview questions for "
            "actual accountability and prerequisites. Do not extrapolate "
            "a national skills shortage from the non-adopter subgroup."
        ),
        "codes": ("scb_2026_ai_10plus", "scb_2026_ai_250plus",
                  "scb_2026_analytics_internal", "scb_2026_ai_expertise_barrier",
                  "scb_2026_ai_privacy_barrier", "scb_2026_ai_data_quality_barrier"),
    },
    {
        "key": "timing_geography",
        "title": "Use confidence and geography as search conditions",
        "signal": (
            "Konjunkturinstitutet's October 2026 total-business confidence "
            "indicator stood at 110.7. The net balance for employment "
            "changes in the previous three months was 2, versus 7 for "
            "the next three months' expectations. SCB estimated 3.2 "
            "vacancies per 100 employment positions in Västra Götaland "
            "and 2.9 nationally in Q2 2026, across the entire economy."
        ),
        "reading": (
            "The 110.7 indicator is a business-confidence index with a normal benchmark "
            "of 100; the staffing figures 2 and 7 are survey net balances, not hires or "
            "numbers of vacancies. Strong sentiment can coexist with cautious "
            "recruitment. Economy-wide vacancy ratios of 3.2 in Västra Götaland and 2.9 "
            "nationally are not proof of a better AI job market in one region without "
            "uncertainty analysis. Compare actual role locations and remote "
            "arrangements, not headline ratios."
        ),
        "action": (
            "Classify target roles as local onsite, national hybrid or "
            "genuinely remote. Confirm actual location, Swedish-language "
            "requirements and work eligibility before spending time on an "
            "application. Maintain a small employer watchlist and monitor "
            "their funded mandates rather than interpreting a confidence "
            "index as an imminent vacancy."
        ),
        "alternative": (
            "Some employers can hire even when broader staffing remains soft, "
            "while others defer roles despite favourable sentiment. "
            "Regional vacancy rates include occupations unrelated to the "
            "candidate's specialty and cannot rank personal offer prospects."
        ),
        "watch": (
            "Review the next KI employment-intentions reading and complete "
            "SCB vacancy data, separating measured hiring from expectations."
        ),
        "codes": ("ki_2026_10_business_confidence",
                  "ki_2026_10_staffing_past_net",
                  "ki_2026_10_staffing_future_net",
                  "scb_lor_2026q2_vgr_per100",
                  "scb_lor_2026q2_national_per100"),
    },
    {
        "key": "employment_model",
        "title": "Test permanent, interim and consulting routes separately",
        "signal": (
            "Brainville reported 10.7% year-on-year growth in Swedish listed consulting "
            "assignments during October 2026, while available consultants on its "
            "marketplace grew 18.5% year on year. These are activity measures within one "
            "marketplace spanning many consulting disciplines. They cannot be applied to "
            "national AI candidate supply, pay rates or confirmed openings."
        ),
        "reading": (
            "Consultant availability increased faster than assignment listings on "
            "Brainville, but that does not quantify national AI consultant competition "
            "or the chance of securing a relevant contract. For the right person, "
            "temporary mandates are one possible search path alongside permanent "
            "employment. Compare sponsor, responsibilities, timescale, onsite "
            "expectations, financial terms, knowledge transfer and continuity before "
            "choosing."
        ),
        "action": (
            "Create separate versions of your professional proposition for "
            "permanent and interim opportunities. For contracts, establish "
            "duration, onsite presence, expected deliverables, procurement "
            "route, insurance or legal requirements and effective compensation. "
            "Track genuine responses, not platform listing totals."
        ),
        "alternative": (
            "The platform's growth may reflect changing participation or "
            "more supply in unrelated disciplines. A permanent role may be "
            "a better fit for ongoing accountability, while a contract can "
            "offer useful access but different financial and legal risks."
        ),
        "watch": (
            "Monitor directly relevant assignments, contract conditions "
            "and actual employer conversations; do not infer AI rates or "
            "candidate competition from aggregate Brainville percentages."
        ),
        "codes": ("brainville_202610_assignments_yoy",
                  "brainville_202610_consultants_yoy"),
    },
)

EXPECTED_NUMBERS = {
    "scb_lor_2026q2_total": 159500,
    "scb_lor_2026q2_advertised": 127500,
    "scb_lor_2026q2_other_channels": 32100,
    "jobtech_v1_sep_se": 20,
    "jobtech_v1_oct_se": 29,
    "jobtech_v1_oct_sto": 13,
    "jobtech_v1_oct_vgr": 5,
    "scb_2026_ai_10plus": 49,
    "scb_2026_ai_250plus": 85,
    "scb_2026_analytics_internal": 33,
    "scb_2026_ai_expertise_barrier": 62,
    "scb_2026_ai_privacy_barrier": 43,
    "scb_2026_ai_data_quality_barrier": 34,
    "ki_2026_10_business_confidence": 110.7,
    "ki_2026_10_staffing_past_net": 2,
    "ki_2026_10_staffing_future_net": 7,
    "scb_lor_2026q2_vgr_per100": 3.2,
    "scb_lor_2026q2_national_per100": 2.9,
    "brainville_202610_assignments_yoy": 10.7,
    "brainville_202610_consultants_yoy": 18.5,
}

CANDIDATE_AGENDA = (
    ("01 / Define target mandates", "Candidate", "Days 1-3",
     "Write the problems, responsibilities and acceptable constraints for each role family before selecting job titles."),
    ("02 / Build three discovery channels", "Candidate", "Week 1",
     "Separate suitable advertisements, relevant professional conversations and targeted employer outreach; track them independently."),
    ("03 / Prepare credible evidence", "Candidate", "Week 2",
     "Document two or three achievements with the problem, your role, operational dependencies and defensible results."),
    ("04 / Test regional reach", "Candidate", "Weeks 2-3",
     "Compare local, national hybrid and verified remote options; screen language, eligibility and onsite requirements."),
    ("05 / Evaluate employment model", "Candidate", "Week 3",
     "Compare permanent roles with fixed-term contracts on scope, sponsor, income, duration and professional fit."),
    ("06 / Reassess with observed results", "Candidate", "Day 30",
     "Measure substantive replies, relevant interviews, role quality and newly verified market evidence before changing strategy."),
)

SCENARIOS = (
    {
        "period":"Late November-December 2026",
        "reading":"Business confidence is firmer than recent staffing activity. Expect mixed employer behaviour, not a guaranteed year-end hiring wave.",
        "trigger":"A comparable SCB recruitment release and KI employment readings show stronger actual vacancy and staffing measures.",
        "response":"Keep targeted conversations active; prioritize roles with a confirmed owner and funding, while maintaining a wider opportunity pipeline.",
    },
    {
        "period":"January-March 2027",
        "reading":"New-year plans may open recruitment decisions, but an automatic seasonal rebound is not established by this research.",
        "trigger":"Completed month data, verified vacancies and employer-specific recruitment steps corroborate an increase.",
        "response":"Enter the period with a clear capability proposition and warm contacts; change effort only when relevant opportunities materialize.",
    },
    {
        "period":"If hiring remains subdued",
        "reading":"Employers may put AI responsibilities in existing roles, use interim help or postpone permanent appointments.",
        "trigger":"Staffing remains flat despite positive business expectations and the relevant role pipeline does not widen.",
        "response":"Broaden suitable adjacent responsibilities, assess interim options and refine examples of operating value without relaxing hard eligibility or role-fit constraints.",
    },
)


def validate_jobseeker_edition(points: list[dict], editorial: dict, edition_slug: str) -> dict:
    """Fail closed rather than accidentally attaching the 2026 POV to a newer edition."""
    validate_editorial(editorial, points, edition_slug)
    if edition_slug != EDITION or str(editorial["version"]) != "2.0.2":
        raise ValueError("Jobseeker reading has not been approved for this edition.")
    available = {p["code"] for p in points}
    if len(available) != len(points):
        raise ValueError("Duplicate jobseeker evidence identifiers.")
    # A static research narrative quotes numbers; never allow it to silently
    # disagree with a later revision of the underlying signed-off source rows.
    idx = {p["code"]: p for p in points}
    for code, expected in EXPECTED_NUMBERS.items():
        if code not in idx or abs(float(idx[code]["value"]) - expected) > 1e-7:
            raise ValueError("Published evidence drift: manual review needed for " + code)
    for finding in FINDINGS:
        if not set(finding["codes"]).issubset(available):
            raise ValueError("Jobseeker reading cites evidence outside the published manifest.")
        for code in finding["codes"]:
            item=next(x for x in points if x["code"] == code)
            _safe_url(item["source_url"])
    return editorial


def jobseeker_market_pdf(points: list[dict], editorial: dict, edition_slug: str) -> bytes:
    """Full A4 candidate edition with the existing publication design and source register."""
    validate_jobseeker_edition(points, editorial, edition_slug)
    idx={p["code"]:p for p in points}
    sty=styles()
    cover={
        "title":TITLE,
        "subtitle":SUBTITLE,
        "stamp":"JAIR RIBEIRO  /  INDEPENDENT MARKET INTELLIGENCE",
        "question_label":"THE CANDIDATE QUESTION",
        "assessment":INTRO,
        "question":"What can a candidate change this month without assuming a hiring forecast?",
        "edition":"JOBSEEKER EDITION 1.0 / SWEDEN",
        "issue":JOBSEEKER_ISSUE,
        "metrics":[
            (f'{int(float(idx["scb_lor_2026q2_total"]["value"])):,}',
             "Whole-economy vacancies","Sweden | Q2 2026 | SCB estimate"),
            (str(int(float(idx["jobtech_v1_oct_se"]["value"]))),
             "Selected senior AI/Data adverts","October 2026 | JobTech title basket"),
            (_value(idx["scb_2026_ai_10plus"]),
             "Enterprises reporting AI use","2026 | Swedish firms with 10+ staff"),
        ],
    }
    story=[]
    section(story,"01 / The candidate reading",
            "A busy market is not the same as an easy job search", INTRO, sty=sty)
    story.append(panel("What this report is for",
        "A better search strategy, not an offer prediction", VALUE, sty=sty))
    story.append(Spacer(1,14))
    story.append(P("How to interpret the figures", "h2", sty=sty))
    story.append(P(
        "Jobseeker Edition 1.0 was prepared on 18 November 2026 from the "
        "signed-off 17 November research snapshot of Executive Edition 2.0.2. "
        "All measured indicators retain their population and dates. Candidate "
        "actions are editorial options to test, not proven career outcomes.",
        "body",sty=sty))
    story.append(P("What the evidence cannot establish", "h2",sty=sty))
    story.append(P(LIMITS,"body_small",sty=sty))
    story.append(metric_cards([
        (f'{int(float(idx["scb_lor_2026q2_total"]["value"])):,}',"Vacant jobs, all occupations","SCB, Q2 2026"),
        (f'{int(float(idx["scb_lor_2026q2_other_channels"]["value"])):,}',"Other recruitment channels","SCB, Q2 2026"),
        (str(int(float(idx["jobtech_v1_oct_se"]["value"]))),"Selected senior AI/Data adverts","JobTech, October 2026"),
    ],sty=sty))
    story.append(Spacer(1,17))
    story.append(P("Five candidate decision perspectives", "h2",sty=sty))
    for i,x in enumerate(FINDINGS,1):
        story.append(P(f"{i:02d} / {x['title']}","body_compact",sty=sty))
    story.append(Spacer(1,12))
    story.append(CondPageBreak(235))

    section(story,"02 / The discovery problem",
        "Why a job-board search can misread demand",
        "National vacancies, selected senior title advertisements and "
        "actual appointments are different measures.",sty=sty)
    story.append(bars([
        ("Advertised",float(idx["scb_lor_2026q2_advertised"]["value"])),
        ("Other channels",float(idx["scb_lor_2026q2_other_channels"]["value"])),
    ],sty=sty))
    story.append(P(
        "SCB estimates for the entire economy, Q2 2026. These are vacancies "
        "and recruitment channels, not AI-related completed hires. Rounding "
        "explains why component estimates may not sum exactly to the total.",
        "caption",sty=sty))
    story.append(Spacer(1,13))
    story.append(bars([
        ("September senior titles",float(idx["jobtech_v1_sep_se"]["value"])),
        ("October senior titles",float(idx["jobtech_v1_oct_se"]["value"])),
    ],sty=sty))
    story.append(P(
        "Only a selected JobTech senior AI/Data title basket, complete months "
        "with retrospectively revised API data. No national specialist-hiring "
        "trend can be established from this comparison.", "caption",sty=sty))
    story.append(Spacer(1,13))
    story.append(panel("A candidate's test",
        "Separate the channels and track useful responses",
        "The market data cannot tell you where your next interview will come "
        "from. A personal response ledger can. Test search channels for four "
        "weeks, looking for qualified conversations and relevant roles.",
        dark=True,sty=sty))

    for i,x in enumerate(FINDINGS,1):
        story.append(CondPageBreak(270))
        section(story,f"{i+2:02d} / Candidate perspective",
                x["title"],x["signal"],sty=sty)
        story.append(P("What this means for a job search","h2",sty=sty))
        story.append(P(x["reading"],"body",sty=sty))
        story.append(panel("Your next move",
            "A practical candidate action",x["action"],dark=True,sty=sty))
        story.append(Spacer(1,12))
        story.append(P("Another explanation to consider","h2",sty=sty))
        story.append(P(x["alternative"],"body_compact",sty=sty))
        story.append(P("What should change your interpretation?","h2",sty=sty))
        story.append(P(x["watch"],"body_compact",sty=sty))
        story.append(P("Evidence IDs: "+", ".join(x["codes"]),
                      "caption",sty=sty))
        story.append(Spacer(1,10))

    story.append(PageBreak())
    section(story,"08 / Your 30-day plan",
            "Use market evidence to improve search decisions",
            "A structured candidate activity plan, not an automated career "
            "assessment or a guarantee of an interview.",sty=sty)
    story.append(decision_table(list(CANDIDATE_AGENDA),sty=sty))
    story.append(Spacer(1,17))
    story.append(P("A useful personal scorecard","h2",sty=sty))
    story.append(P(
        "Record eligible roles reviewed, targeted applications, relevant "
        "professional conversations, substantive employer replies, screening "
        "calls and interviews. Add the reason a role was excluded. These are "
        "your own operating measures; this report does not collect them.",
        "body",sty=sty))
    story.append(panel("Interview preparation",
        "Three questions worth asking",
        "Which business outcome would this position own in six months? "
        "What decision rights, staff and budget support the mandate? "
        "What evidence would convince the hiring team that the role is working?",
        sty=sty))

    story.append(Spacer(1,12))
    story.append(CondPageBreak(230))
    section(story,"09 / Conditional outlook",
        "What could change the search conditions",
        "These are scenarios with observable triggers, not probability estimates "
        "or predictions of an individual hiring date.",sty=sty)
    for item in SCENARIOS:
        story.append(KeepTogether([
            P(item["period"],"h2",sty=sty),
            P(item["reading"],"body_compact",sty=sty),
            panel("Review trigger","Evidence and candidate response",
                  "Trigger: "+item["trigger"]+" Candidate response: "+item["response"],sty=sty),
            Spacer(1,12),
        ]))

    story.append(PageBreak())
    section(story,"10 / Evidence and limits",
        "Trace the same November evidence to its sources",
        "This edition uses exactly the same approved observations, release "
        "dates and source methods as the executive report. Jobseeker "
        "recommendations are editorial judgments, not measured employment outcomes.",
        sty=sty)
    for item in editorial["coverage_cautions"]:
        story.append(KeepTogether([
            P(item["title"],"h2",sty=sty),
            P(item["text"],"body_small",sty=sty),
        ]))
    story.append(Spacer(1,12))
    story.append(P("Full methodological note","h2",sty=sty))
    story.append(P(editorial["methodology_note"],"body_small",sty=sty))
    story.append(CondPageBreak(170))
    story.append(P("Methods and source-family limits","h2",sty=sty))
    story.append(source_family_methods(points,sty=sty))
    story.append(Spacer(1,16))
    story.append(P("Signed-off observation register","h2",sty=sty))
    story.append(sources_table(points,_value,sty=sty,
                 include_provenance=True,compact_provenance=True))
    story.append(Spacer(1,8))
    story.append(P("Independent research by Jair Ribeiro | jairribeiro.com",
                   "caption",sty=sty))
    return assemble(story,cover,
       "Jair Ribeiro | Swedish AI & Data Job Market Review | Candidate Edition 1.0",
       min_bytes=10000,
       interior_kicker="MARKET SIGNALS / JOBSEEKER RESEARCH",
       interior_footer="Independent market research")


def render_jobseeker_intelligence(st, editorial: dict, points: list[dict],
                                  edition_slug: str, token: str, record_event) -> None:
    """Member-only reader experience sharing the existing published release."""
    validate_jobseeker_edition(points, editorial, edition_slug)
    st.html(STYLE)
    st.html(
        '<section class="ms-js-lead"><div class="eyebrow">Candidate edition / '+
        html_escape(editorial["issue_date"])+'</div><h3>'+
        html_escape(TITLE)+'</h3><p><strong>'+html_escape(SUBTITLE)+
        '</strong></p><p>'+html_escape(INTRO)+
        '</p><p>'+html_escape(VALUE)+'</p></section>'
    )
    with st.expander("Evidence scope — what the figures cannot tell you",expanded=False):
        st.write(LIMITS)
    st.caption("Jobseeker Edition 1.0 · Prepared 18 November 2026 · Evidence snapshot 17 November 2026")
    st.markdown("#### Download the Jobseeker Edition")
    st.caption(
        "Complete candidate-focused A4 report with five analyses, a 30-day "
        "search plan, three conditional scenarios and the same traceable "
        "source register as the Executive Edition. Free for registered readers."
    )
    pdf=jobseeker_market_pdf(points,editorial,edition_slug)
    st.download_button(
        "Download complete Jobseeker Market Review · PDF",
        data=pdf,mime="application/pdf",
        file_name="Jair_Ribeiro_Swedish_AI_Data_Job_Market_Review_2026-11.pdf",
        type="primary",use_container_width=True,key="market_jobseeker_complete_pdf",
        on_click=record_event,args=(token,"pdf_review","jobseeker",edition_slug)
    )
    idx={x["code"]:x for x in points}
    st.markdown("#### Five candidate decisions")
    choice=st.selectbox("Explore a jobseeker perspective",
        [x["key"] for x in FINDINGS],
        format_func=lambda key:next(x["title"] for x in FINDINGS if x["key"]==key),
        key="market_jobseeker_theme")
    item=next(x for x in FINDINGS if x["key"]==choice)
    st.html(
        '<article class="ms-js-topic"><span class="eyebrow">Candidate perspective</span>'
        '<h3>'+html_escape(item["title"])+'</h3>'
        '<h4>What the published evidence shows</h4><p>'+
        html_escape(item["signal"])+'</p>'
        '<h4>What it means for your search</h4><p>'+
        html_escape(item["reading"])+'</p>'
        '<h4>Alternative explanation</h4><p>'+
        html_escape(item["alternative"])+'</p>'
        '<h4>When to reconsider</h4><p>'+
        html_escape(item["watch"])+'</p></article>'
    )
    st.html('<section class="ms-js-action"><strong>THE NEXT PRACTICAL STEP</strong>'
        '<p>'+html_escape(item["action"])+'</p></section>')
    with st.expander("Check the original observations and methods",expanded=False):
        for code in item["codes"]:
            p=idx[code]
            st.html(
                '<div class="ms-js-detail"><strong>'+
                html_escape(p["metric_label"])+' · '+html_escape(_value(p))+
                '</strong><br>'+html_escape(p["period_label"])+
                ' · '+html_escape(p["population_note"])+
                '<br><a href="'+html_escape(_safe_url(p["source_url"]),quote=True)+
                '" target="_blank" rel="noopener noreferrer">'+
                html_escape(p["source_title"])+
                '</a><br>Method: '+html_escape(p["methodology"])+
                '<br>Limit: '+html_escape(p["caveat"])+
                '</div>'
            )
    st.markdown("#### Your 30-day candidate agenda")
    for label, owner, timing, action in CANDIDATE_AGENDA:
        with st.expander(label+" · "+timing,expanded=False):
            st.write(action)
    st.markdown("#### Three possible market conditions")
    for scenario in SCENARIOS:
        with st.expander(scenario["period"],expanded=False):
            st.write(scenario["reading"])
            st.caption("What to monitor: "+scenario["trigger"])
            st.write("Your response: "+scenario["response"])
    with st.expander("Methodology and evidence boundaries",expanded=False):
        for caveat in editorial["coverage_cautions"]:
            st.markdown("**"+caveat["title"]+"**")
            st.write(caveat["text"])
        st.write(editorial["methodology_note"])
    st.caption(
        "Independent candidate-oriented interpretation by Jair Ribeiro. "
        "Same signed-off November data as Executive Edition 2.0.2. "
        "Not individual recruitment advice, a vacancy census, an employer "
        "recommendation or a hiring forecast."
    )
