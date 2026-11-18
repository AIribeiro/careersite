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
SUBTITLE = "Jobseeker Edition | AI and Data careers in a changing Swedish market"
JOBSEEKER_ISSUE = "18 November 2026"
INTRO = (
    "AI is becoming part of more kinds of work in Sweden: technical development, "
    "data analysis, governance and everyday business operations. That creates "
    "different directions for professional growth, but it does not guarantee "
    "more vacancies. This report draws on official Swedish research and a "
    "carefully defined sample of senior advertisements to explain what is "
    "changing, where the evidence stops, and how professionals can respond."
)
VALUE = (
    "Whether you are starting out, changing specialty, returning to work or "
    "moving towards leadership, explore how your existing experience connects "
    "to AI and Data. Understand the capabilities organisations struggle with, "
    "compare practical career pathways and recruitment channels, and build "
    "evidence of your own work. A four-week plan offers a starting point, "
    "not a formula that guarantees an interview."
)
LIMITS = (
    "This November 2026 research report is not a live job board, salary guide "
    "or ranking of AI and Data careers. SCB vacancy estimates cover all "
    "occupations. The JobTech sample covers selected senior titles only. "
    "Enterprise AI adoption and capability barriers are not counts of vacancies. "
    "No credible all-level AI/Data vacancy total or hiring probability can be "
    "calculated from this evidence."
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
.ms-js-pathways,.ms-js-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}
.ms-js-pathways article{background:#fbfaf7;border:1px solid #dfd8cc;padding:19px;min-width:0}
.ms-js-pathways article span{font-size:10px;letter-spacing:.1em;color:#966543;font-weight:800}
.ms-js-pathways article h4{font:500 21px/1.25 Georgia,serif;color:#173147;margin:10px 0}
.ms-js-pathways article p{font-size:13px;line-height:1.65;color:#405366}
.ms-js-metrics>div{background:#f5f2ed;border-top:3px solid #b88b68;padding:19px}
.ms-js-metrics strong{display:block;color:#173147;font:500 34px Georgia,serif}
.ms-js-metrics span{display:block;color:#405366;font-size:12px;line-height:1.5}
.ms-js-disclaimer{font-size:12px;color:#667786;line-height:1.6}
@media(max-width:700px){.ms-js-pathways,.ms-js-metrics{grid-template-columns:1fr}.ms-js-lead,.ms-js-topic{padding:19px}
 .ms-js-lead p,.ms-js-topic p{font-size:14px}}
</style>
"""

# Each finding is a genuinely candidate-oriented editorial judgment. All
# references must occur in the already-authorised executive edition manifest.
FINDINGS = (
    {
        "key": "visible_market",
        "title": "Looking for work? Use more than job ads",
        "signal": (
            "Statistics Sweden estimated 159,500 vacant jobs across the whole Swedish economy "
            "in Q2 2026. About 127,500 were advertised; for approximately 32,100, employers "
            "looked for applicants through other channels. The figures are rounded survey "
            "estimates. They do not count only AI and Data jobs or show how many people were "
            "hired."
        ),
        "reading": (
            "Job sites are a useful place to start, but some recruitment takes place through "
            "other channels. The national figures do not show whether networking works better "
            "for AI and Data candidates. Try three realistic routes: apply to suitable "
            "advertised jobs, speak with people you already know professionally, and contact a "
            "few employers whose work interests you. Judge each route by the relevant replies "
            "you receive."
        ),
        "action": (
            "Keep a weekly list of jobs you applied for, useful conversations and employers "
            "you contacted. Note the date, whether the role suits your skills, and what "
            "happened next. After four weeks, see which activities led to real responses. "
            "Quality matters more than sending the most applications."
        ),
        "alternative": (
            "Many vacancies filled through other recruitment channels may be in occupations "
            "unrelated to AI or Data. Some employers advertise and recruit through contacts at "
            "the same time. The survey cannot tell you which method works best for your "
            "background."
        ),
        "watch": (
            "Check new SCB vacancy figures when they are published. For your own search, pay "
            "more attention to genuine replies and interviews than national totals."
        ),
        "codes": ("scb_lor_2026q2_total", "scb_lor_2026q2_advertised",
                  "scb_lor_2026q2_other_channels"),
    },
    {
        "key": "role_discovery",
        "title": "Look beyond jobs with 'AI' or 'Data' in the title",
        "signal": (
            "A small, retrospectively assembled JobTech sample found 20 advertisements for "
            "selected senior AI and Data titles across Sweden in September 2026, and 29 in "
            "October. Of the October advertisements, 13 were indexed in Stockholm and five in "
            "Västra Götaland. These are advertisements, not confirmed unique vacancies, and "
            "the sample covers only selected senior job titles. Historical API records may "
            "change."
        ),
        "reading": (
            "Employers sometimes give related work different job titles. A role in analytics, "
            "digital services, operations, product development or process improvement may "
            "involve useful AI and Data skills even when the title does not say so. Read the "
            "responsibilities and requirements before deciding to apply. The JobTech sample "
            "focuses on senior jobs, so it tells us little about entry-level openings, "
            "internships or every possible Data role."
        ),
        "action": (
            "Choose two or three kinds of work you could do. Write down related job titles and "
            "the skills each requires, then search for those titles as well as 'AI' and "
            "'Data'. Compare job descriptions and check location, language, work eligibility "
            "and experience requirements before applying."
        ),
        "alternative": (
            "A wider search will also show jobs that are too technical, too senior or outside "
            "your interests. Some advertised roles may appear more than once in databases. "
            "Looking beyond a title helps only when the actual work fits your background."
        ),
        "watch": (
            "Review complete months and actual job descriptions before assuming demand is "
            "increasing. The figures for 1–15 November 2026 cover only half a month."
        ),
        "codes": ("jobtech_v1_sep_se", "jobtech_v1_oct_se",
                  "jobtech_v1_oct_sto", "jobtech_v1_oct_vgr"),
    },
    {
        "key": "capability_proof",
        "title": "Show what you can do with data and AI",
        "signal": (
            "In SCB's 2026 survey, 49% of enterprises with at least ten employees reported "
            "using AI, compared with 85% of large enterprises. Separately, 33% reported having "
            "staff who analysed data in-house. Among businesses that considered AI but did not "
            "adopt it, 62% mentioned a lack of expertise, 43% privacy or data-protection "
            "concerns and 34% problems accessing or using data. Businesses could report more "
            "than one barrier."
        ),
        "reading": (
            "These survey answers do not tell us how many AI jobs are open. They do show some "
            "issues employers may need to manage, including skills, data quality and safe use. "
            "When you describe your experience, give a real example of a problem you worked on "
            "and what you contributed. If you are starting out, examples from courses, "
            "internships, volunteering or personal projects can show what you have learned; "
            "label them accurately and do not claim workplace results you cannot verify."
        ),
        "action": (
            "Prepare two short examples from work, studies or projects. For each, explain the "
            "problem, what you did, which tools or methods you used and what you observed or "
            "learned. If you can verify an outcome, mention it. Use one example in your CV or "
            "profile and practise explaining it clearly in an interview."
        ),
        "alternative": (
            "Not every employer needs its own AI team, and a business may have good reasons "
            "not to use AI for a particular task. The survey cannot tell us what skills a "
            "specific vacancy requires."
        ),
        "watch": (
            "Compare your examples with the requirements in real job advertisements and the "
            "questions employers ask. Keep learning priorities tied to the kind of work you "
            "want."
        ),
        "codes": ("scb_2026_ai_10plus", "scb_2026_ai_250plus",
                  "scb_2026_analytics_internal", "scb_2026_ai_expertise_barrier",
                  "scb_2026_ai_privacy_barrier", "scb_2026_ai_data_quality_barrier"),
    },
    {
        "key": "timing_geography",
        "title": "Check where jobs are—and what employers require",
        "signal": (
            "Konjunkturinstitutet reported a business-confidence index of 110.7 in October "
            "2026, compared with a normal benchmark of 100. Its survey balances for past and "
            "expected staffing changes were 2 and 7, respectively; these are not numbers of "
            "people hired. In Q2 2026, SCB estimated 3.2 vacancies per 100 jobs in Västra "
            "Götaland and 2.9 nationally, across all types of work."
        ),
        "reading": (
            "Business optimism does not guarantee more jobs in your field. Nor does a higher "
            "overall vacancy rate mean AI or Data jobs will be easier to find in one region. "
            "Before investing time in an application, check where the work must be done, how "
            "often you need to be on site, whether Swedish is required and whether you meet "
            "the eligibility conditions. Compare actual roles rather than ranking locations by "
            "national statistics."
        ),
        "action": (
            "Make three lists: jobs you can travel to, jobs elsewhere in Sweden that allow "
            "hybrid work, and genuinely remote jobs. Check the employer's location and "
            "language requirements in each advertisement. Keep a small list of companies to "
            "follow for relevant openings."
        ),
        "alternative": (
            "Some businesses hire while the economy is quiet; others delay recruitment when "
            "confidence is positive. Regional vacancy rates include many occupations outside "
            "AI and Data."
        ),
        "watch": (
            "Follow confirmed openings and the next published staffing and vacancy figures. "
            "Keep survey expectations separate from real job advertisements and employer "
            "responses."
        ),
        "codes": ("ki_2026_10_business_confidence",
                  "ki_2026_10_staffing_past_net",
                  "ki_2026_10_staffing_future_net",
                  "scb_lor_2026q2_vgr_per100",
                  "scb_lor_2026q2_national_per100"),
    },
    {
        "key": "employment_model",
        "title": "Compare permanent jobs and contract work",
        "signal": (
            "In October 2026, Brainville reported 10.7% more consulting assignments listed on "
            "its Swedish platform than a year earlier. The number of consultants shown as "
            "available rose 18.5% over the same period. Brainville covers many kinds of "
            "consulting work, not only AI and Data; these figures do not measure national AI "
            "job openings, pay or competition."
        ),
        "reading": (
            "A permanent job, a fixed-term role and independent contract work offer different "
            "conditions. Consulting may suit some experienced specialists, but platform totals "
            "do not show that a suitable assignment is available to you. If you are entering "
            "the field, structured training and support in a regular role may matter more. "
            "Choose what fits your skills, financial needs and circumstances."
        ),
        "action": (
            "Compare permanent and fixed-term roles on pay, learning opportunities, location, "
            "working hours and job security. If you also consider consulting, check the "
            "assignment length, expected work, payment terms and any tax or insurance "
            "requirements. Track relevant offers and discussions rather than total marketplace "
            "listings."
        ),
        "alternative": (
            "Changes in Brainville's listings may reflect which companies and consultants use "
            "the platform, or shifts in unrelated fields. Growth on one platform does not show "
            "a wider AI contracting trend."
        ),
        "watch": (
            "Look for assignments or jobs that genuinely match your skills. Check their "
            "conditions and talk with employers or clients before drawing conclusions about "
            "the market."
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

# Five simple job-search choices. Guidance to test, not measured hiring outcomes.
DECISION_MAP = (
    ("Where should I look?", "Try suitable advertised jobs, conversations with people in your field and a few direct contacts with relevant employers. Note real replies."),
    ("Which roles fit my skills?", "Look beyond job titles. Check the tasks, skills, language and experience each employer asks for."),
    ("How can I show what I can do?", "Prepare two real examples from work, studies or projects. Explain what you did and what you learned or achieved."),
    ("Which locations work for me?", "Compare roles you can travel to with realistic hybrid and remote options. Check language and eligibility requirements."),
    ("Should I consider temporary or contract work?", "Compare permanent and fixed-term roles for pay, training, stability and job fit. Check extra requirements before contracting."),
)

CANDIDATE_AGENDA = (
    ("01 / Decide what work you want", "Jobseeker", "Days 1-3",
     "Choose two or three types of role that match your skills and interests. Note location, language and working conditions."),
    ("02 / Use more than one search route", "Jobseeker", "Week 1",
     "Search suitable job ads, talk with people in your field and contact a few relevant employers. Track the responses."),
    ("03 / Prepare examples of your skills", "Jobseeker", "Week 2",
     "Choose two examples from jobs, studies or projects. Explain the problem, your contribution and what you learned or achieved."),
    ("04 / Check location and language", "Jobseeker", "Weeks 2-3",
     "Compare roles near you with verified hybrid or remote options. Check language, travel and eligibility rules."),
    ("05 / Compare types of work", "Jobseeker", "Week 3",
     "Review permanent, fixed-term and, where suitable, contract opportunities for pay, stability and learning."),
    ("06 / Review what is working", "Jobseeker", "Day 30",
     "Count suitable applications, genuine replies and interviews. Adjust your next month based on what happened."),
)

SCENARIOS = (
    {
        "period":"Late November-December 2026",
        "reading":"Business confidence was stronger than reported staffing activity. Employers may keep recruiting selectively; this research cannot predict a wave of jobs before year-end.",
        "trigger":"New SCB vacancy data and KI staffing surveys show a clear improvement in comparable measures.",
        "response":"Keep looking at suitable advertised jobs and maintaining useful contacts. Prioritise vacancies with clear responsibilities and a real hiring process.",
    },
    {
        "period":"January-March 2027",
        "reading":"New budgets may lead some employers to advertise roles early in 2027, but the November data cannot establish a hiring rebound.",
        "trigger":"Several complete months of job ads and direct employer updates show more relevant openings.",
        "response":"Prepare a clear CV and examples of your skills. Keep in touch with relevant people and review actual opportunities before changing your approach.",
    },
    {
        "period":"If hiring remains subdued",
        "reading":"Employers may add AI tasks to existing roles, recruit selectively or use temporary help instead of opening new permanent jobs.",
        "trigger":"Relevant job advertisements and employer replies remain limited even if business confidence improves.",
        "response":"Look at related roles you can genuinely perform, consider fixed-term work where suitable and improve how you explain your skills. Keep your minimum requirements.",
    },
)


READING_HELP = (
    ("Job vacancy", "A position an employer is trying to fill; this does not mean someone was hired."),
    ("Selected job-ad sample", "A small group of adverts matching chosen senior job titles, not every AI or Data role."),
    ("Survey estimate", "A figure from survey responses, rather than a count of every employer or worker."),
    ("Business confidence", "How businesses describe conditions and expectations, not a list of companies hiring."),
    ("Consulting marketplace", "A site listing contract assignments and consultants, not the whole labour market."),
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
        "question_label":"THE JOB SEARCH QUESTION",
        "assessment":INTRO,
        "question":"Where can you look next, and how can you show your skills?",
        "edition":"JOBSEEKER EDITION 1.0 / SWEDEN",
        "issue":JOBSEEKER_ISSUE,
        "metrics":[
            (f'{int(float(idx["scb_lor_2026q2_total"]["value"])):,}',
             "Vacancies, all job types","Sweden | Q2 2026 | SCB estimate"),
            (str(int(float(idx["jobtech_v1_oct_se"]["value"]))),
             "Selected senior AI/Data ads","October 2026 | JobTech title basket"),
            (_value(idx["scb_2026_ai_10plus"]),
             "Enterprises reporting AI use","2026 | Swedish firms with 10+ staff"),
        ],
    }
    story=[]
    section(story,"01 / Understanding your job market",
            "What the Swedish job market can tell you", INTRO, sty=sty)
    story.append(panel("What you can use this report for",
        "Plan your search with evidence and realistic expectations", VALUE, sty=sty))
    story.append(Spacer(1,14))
    story.append(P("A quick guide to the numbers", "h2", sty=sty))
    story.append(P(
        "This jobseeker guide was prepared on 18 November 2026 using the same "
        "research reviewed for the Executive Edition on 17 November. Each "
        "number comes from a particular survey or selected set of adverts. "
        "The suggestions are ideas to test, not proven ways to secure an interview.",
        "body",sty=sty))
    story.append(P("What these numbers do not cover", "h2",sty=sty))
    story.append(P(LIMITS,"body_small",sty=sty))
    story.append(P("Three professional pathways to examine","h2",sty=sty))
    story.append(P(
        "Build: engineering, software, analytical and AI development work. "
        "Operate: data quality, governance, risk and reliable services. "
        "Apply: use AI and analytics within an established professional field. "
        "These are useful ways to think about career options, not a measured "
        "ranking of roles or their hiring demand.", "body",sty=sty))
    story.append(P("Five common terms explained","h2",sty=sty))
    for term, meaning in READING_HELP:
        story.append(P(term+": "+meaning,"body_compact",sty=sty))
    story.append(Spacer(1,10))
    story.append(metric_cards([
        (f'{int(float(idx["scb_lor_2026q2_total"]["value"])):,}',"Vacancies across all types of work","SCB, Q2 2026"),
        (f'{int(float(idx["scb_lor_2026q2_other_channels"]["value"])):,}',"Vacancies recruited without adverts","SCB, Q2 2026"),
        (str(int(float(idx["jobtech_v1_oct_se"]["value"]))),"Selected senior AI/Data ads","JobTech, October 2026"),
    ],sty=sty))
    story.append(Spacer(1,17))
    # A five-part preview is one reading unit: never leave one item orphaned
    # at the foot of the page while the other four start the next page.
    preview=[P("Five ways to plan your job search","h2",sty=sty)]
    for i,x in enumerate(FINDINGS,1):
        preview.append(P(f"{i:02d} / {x['title']}","body_compact",sty=sty))
    story.append(KeepTogether(preview))
    story.append(Spacer(1,12))
    story.append(CondPageBreak(290))
    story.append(P("Five questions for your job search","h2",sty=sty))
    story.append(decision_table([
        (question,"Jobseeker","Over four weeks",action)
        for question,action in DECISION_MAP
    ],sty=sty,header_left="YOUR QUESTION",header_right="WHAT TO TRY",
       show_context=False))
    story.append(Spacer(1,12))
    story.append(P(
        "Try these steps and review what happens. The research does not "
        "measure which application channel works best, the number of all "
        "AI/Data jobs, salary offers or your chance of receiving an offer.",
        "caption",sty=sty))

    story.append(CondPageBreak(245))
    section(story,"02 / AI use and professional capability",
        "Business AI adoption and hiring are different measures",
        "Statistics Sweden's enterprise research provides context for AI and "
        "Data work, without measuring specialist job openings.",sty=sty)
    story.append(bars([
        ("AI use, enterprises 10+",float(idx["scb_2026_ai_10plus"]["value"])),
        ("AI use, large enterprises",float(idx["scb_2026_ai_250plus"]["value"])),
        ("Internal analytics personnel",float(idx["scb_2026_analytics_internal"]["value"])),
    ],sty=sty))
    story.append(P(
        "SCB 2026 percentages; enterprise sizes and measures differ. "
        "AI use does not establish recruitment demand, and survey changes "
        "limit historical comparison.", "caption",sty=sty))
    story.append(Spacer(1,10))
    story.append(P("Obstacles reported by some AI non-adopters","h2",sty=sty))
    story.append(bars([
        ("Lack of expertise",float(idx["scb_2026_ai_expertise_barrier"]["value"])),
        ("Privacy concerns",float(idx["scb_2026_ai_privacy_barrier"]["value"])),
        ("Data access or quality",float(idx["scb_2026_ai_data_quality_barrier"]["value"])),
    ],sty=sty))
    story.append(P(
        "SCB 2026: only enterprises that considered AI but did not adopt it. "
        "Multiple answers allowed; these are not vacancy counts.", "caption",sty=sty))
    story.append(Spacer(1,12))
    section(story,"03 / Finding opportunities",
        "Why job advertisements show only part of the picture",
        "Official vacancy figures cover every occupation. JobTech covers selected "
        "senior AI/Data advertisements; neither shows who was actually hired.",sty=sty)
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
    story.append(panel("Try this for four weeks",
        "Keep track of where relevant replies come from",
        "National statistics cannot predict where your next interview will come "
        "from. Keep a short record of applications, professional conversations "
        "and direct approaches. See which lead to useful replies.",
        dark=True,sty=sty))

    for i,x in enumerate(FINDINGS,1):
        story.append(CondPageBreak(270))
        section(story,f"{i+3:02d} / Career decision",
                x["title"],x["signal"],sty=sty)
        story.append(P("How this could help your search","h2",sty=sty))
        story.append(P(x["reading"],"body",sty=sty))
        story.append(panel("Try this next",
            "A practical step you can take",x["action"],dark=True,sty=sty))
        story.append(Spacer(1,12))
        story.append(P("What else could explain the figures?","h2",sty=sty))
        story.append(P(x["alternative"],"body_compact",sty=sty))
        story.append(P("What to check next","h2",sty=sty))
        story.append(P(x["watch"],"body_compact",sty=sty))
        story.append(P("Evidence IDs: "+", ".join(x["codes"]),
                      "caption",sty=sty))
        story.append(Spacer(1,10))

    story.append(PageBreak())
    section(story,"09 / Your four-week job-search plan",
            "Turn the research into a simple four-week plan",
            "Start with a few tasks each week. See which ones help you find suitable "
            "work, and adapt the plan to your circumstances.",sty=sty)
    story.append(decision_table(list(CANDIDATE_AGENDA),sty=sty,
        header_left="WEEK / TASK",header_right="YOUR NEXT STEP"))
    story.append(Spacer(1,17))
    story.append(P("How to see whether your search is working","h2",sty=sty))
    story.append(P(
        "Each week, count jobs you considered, suitable applications, conversations, "
        "employer replies and interviews. Note why you ruled out a job. "
        "This record is yours; the report does not collect your search activity.",
        "body",sty=sty))
    story.append(panel("Before an interview",
        "Three useful questions to ask an employer",
        "What would you like the person in this job to achieve in six months? "
        "What training, tools and people will help them succeed? "
        "How will you know they are doing the job well?",
        sty=sty))

    story.append(Spacer(1,12))
    story.append(CondPageBreak(230))
    section(story,"10 / What might happen next",
        "Possible changes in hiring conditions",
        "These are possible situations to watch, not predictions of when "
        "you will find work.",sty=sty)
    for item in SCENARIOS:
        story.append(KeepTogether([
            P(item["period"],"h2",sty=sty),
            P(item["reading"],"body_compact",sty=sty),
            panel("What to watch","What the new evidence could mean for you",
                  "Check: "+item["trigger"]+" What you can do: "+item["response"],sty=sty),
            Spacer(1,12),
        ]))

    story.append(PageBreak())
    section(story,"11 / Sources and important limitations",
        "Where the figures come from",
        "This guide uses the same approved observations, source dates and "
        "methods as the executive report. The job-search suggestions "
        "are practical interpretations, not measured hiring results.",
        sty=sty)
    for item in editorial["coverage_cautions"]:
        story.append(KeepTogether([
            P(item["title"],"h2",sty=sty),
            P(item["text"],"body_small",sty=sty),
        ]))
    story.append(Spacer(1,12))
    story.append(P("How the research was prepared","h2",sty=sty))
    story.append(P(editorial["methodology_note"],"body_small",sty=sty))
    story.append(CondPageBreak(170))
    story.append(P("Detailed source methods and limitations","h2",sty=sty))
    story.append(source_family_methods(points,sty=sty))
    story.append(Spacer(1,16))
    story.append(P("Complete list of checked observations","h2",sty=sty))
    story.append(sources_table(points,_value,sty=sty,
                 include_provenance=True,compact_provenance=True))
    story.append(Spacer(1,8))
    story.append(P("Independent research by Jair Ribeiro | jairribeiro.com",
                   "caption",sty=sty))
    return assemble(story,cover,
       "Jair Ribeiro | Swedish AI & Data Market Review | Jobseeker Edition 1.0",
       min_bytes=10000,
       interior_kicker="MARKET SIGNALS / JOBSEEKER RESEARCH",
       interior_footer="Independent market research")


def render_jobseeker_intelligence(st, editorial: dict, points: list[dict],
                                  edition_slug: str, token: str, record_event) -> None:
    """Member-only reader experience sharing the existing published release."""
    validate_jobseeker_edition(points, editorial, edition_slug)
    st.html(STYLE)
    st.html(
        '<section class="ms-js-lead"><div class="eyebrow">Jobseeker edition / '+
        html_escape(editorial["issue_date"])+'</div><h3>'+
        html_escape(TITLE)+'</h3><p><strong>'+html_escape(SUBTITLE)+
        '</strong></p><p>'+html_escape(INTRO)+
        '</p><p>'+html_escape(VALUE)+'</p></section>'
    )
    with st.expander("What these figures cover",expanded=False):
        st.write(LIMITS)
    st.caption("Jobseeker Edition 1.0 · Prepared 18 November 2026 · Evidence snapshot 17 November 2026")
    st.markdown("#### Download your free jobseeker report")
    st.caption(
        "The report covers career pathways, enterprise AI use, capability "
        "barriers, five evidence-based topics, a four-week plan and sources. "
        "Your free account includes both report editions."
    )
    pdf=jobseeker_market_pdf(points,editorial,edition_slug)
    st.download_button(
        "Download the jobseeker report · PDF",
        data=pdf,mime="application/pdf",
        file_name="Jair_Ribeiro_Swedish_AI_Data_Job_Market_Review_2026-11.pdf",
        type="primary",use_container_width=True,key="market_jobseeker_complete_pdf",
        on_click=record_event,args=(token,"pdf_review","jobseeker",edition_slug)
    )
    idx={x["code"]:x for x in points}
    with st.expander("New to these market figures? Five terms explained",expanded=False):
        for term, meaning in READING_HELP:
            st.markdown("**"+term+"** — "+meaning)
    st.markdown("#### Five questions to guide your search")
    for question, action in DECISION_MAP:
        with st.expander(question,expanded=False):
            st.write(action)
    st.markdown("#### Three ways your experience can connect to AI and Data")
    st.html(
        '<div class="ms-js-pathways">'
        '<article><span>01 / BUILD</span><h4>Develop systems</h4>'
        '<p>Explore data engineering, analysis, software and AI development '
        'roles by checking real technical requirements.</p></article>'
        '<article><span>02 / OPERATE</span><h4>Make work dependable</h4>'
        '<p>Consider data quality, governance, privacy and operational '
        'responsibility where these match your experience.</p></article>'
        '<article><span>03 / APPLY</span><h4>Use AI in your profession</h4>'
        '<p>Look for meaningful AI work within existing business and '
        'professional roles, not only in titles containing AI.</p></article>'
        '</div><p class="ms-js-disclaimer">These pathways are a way to explore '
        'work, not vacancy rankings or measured hiring demand.</p>'
    )
    st.markdown("#### What Swedish enterprise research shows")
    st.html(
        '<div class="ms-js-metrics">'
        '<div><strong>49%</strong><span>Enterprises (10+ employees) using AI</span></div>'
        '<div><strong>33%</strong><span>Enterprises with analytics personnel</span></div>'
        '<div><strong>62%</strong><span>Non-adopting subgroup citing missing expertise</span></div>'
        '</div><p class="ms-js-disclaimer">Statistics Sweden 2026. '
        'Different survey groups; none of these figures counts job openings.</p>'
    )
    st.markdown("#### Five topics to help your job search")
    choice=st.selectbox("Which topic would you like to explore?",
        [x["key"] for x in FINDINGS],
        format_func=lambda key:next(x["title"] for x in FINDINGS if x["key"]==key),
        key="market_jobseeker_theme")
    item=next(x for x in FINDINGS if x["key"]==choice)
    st.html(
        '<article class="ms-js-topic"><span class="eyebrow">Jobseeker topic</span>'
        '<h3>'+html_escape(item["title"])+'</h3>'
        '<h4>What the figures show</h4><p>'+
        html_escape(item["signal"])+'</p>'
        '<h4>How this may help</h4><p>'+
        html_escape(item["reading"])+'</p>'
        '<h4>Another explanation</h4><p>'+
        html_escape(item["alternative"])+'</p>'
        '<h4>What to check next</h4><p>'+
        html_escape(item["watch"])+'</p></article>'
    )
    st.html('<section class="ms-js-action"><strong>WHAT YOU CAN TRY NEXT</strong>'
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
    st.markdown("#### Your four-week job-search plan")
    for label, owner, timing, action in CANDIDATE_AGENDA:
        with st.expander(label+" · "+timing,expanded=False):
            st.write(action)
    st.markdown("#### Three possible job-market situations")
    for scenario in SCENARIOS:
        with st.expander(scenario["period"],expanded=False):
            st.write(scenario["reading"])
            st.caption("Keep an eye on: "+scenario["trigger"])
            st.write("What you could do: "+scenario["response"])
    with st.expander("Source details and limitations",expanded=False):
        for caveat in editorial["coverage_cautions"]:
            st.markdown("**"+caveat["title"]+"**")
            st.write(caveat["text"])
        st.write(editorial["methodology_note"])
    st.caption(
        "Research and job-search guidance by Jair Ribeiro, based on the same "
        "November 2026 data as Executive Edition 2.0.2. This is not a "
        "list of live vacancies or a prediction of an offer."
    )
