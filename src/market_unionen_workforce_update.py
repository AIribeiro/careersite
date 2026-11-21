"""Unionen autumn 2026 workforce evidence for a dated, source-bound Market Signals release.

No national AI vacancy estimates, causal AI displacement or SCB-to-Unionen
rate comparisons are made. All values bind to approved edition points.
"""
from __future__ import annotations
from html import escape
from reportlab.platypus import PageBreak, Spacer

NEW_SLUG = "sweden-ai-data-market-review-2026-11-unionen-2-1"
OLD_SLUG = "sweden-ai-data-market-review-2026-11-v2-0-2"
REPORT_DATE = "21 November 2026"
SOURCE = ("https://www.unionen.se/opinion/"
    "unionens-konjunkturprognos-stark-ekonomi-men-tjanstemannajobben-slapar-efter")
SOURCE_REPORT = "https://www.unionen.se/filer/rapport/unionen-om-konjunkturen-hosten-2026"

# Indicator / value / precise observation group. These are not percentage shares
# of the same market and are not combined with the SCB enterprise survey.
CLUBS = {
    "unionen_ai_adoption_clubs_share": (83, "Responding clubs reporting employer AI use"),
    "unionen_ai_negotiated_clubs_share": (16, "Clubs reporting AI negotiations or planned negotiations"),
}
AI_ADOPTERS = {
    "unionen_ai_staffing_need_changed_share": (42, "AI changed staffing requirements"),
    "unionen_ai_data_it_new_roles_share": (24, "New AI, Data or IT specialist roles reported"),
    "unionen_ai_nonreplaced_positions_share": (13, "Positions not refilled"),
    "unionen_ai_redundancy_clubs_share": (13, "Redundancies attributed to AI by respondents"),
}
CONTEXT = {
    "unionen_business_outlook_index": 56,
    "unionen_automotive_sentiment_index": 45,
    "unionen_ai_adopter_planned_professional_cuts_adjusted": 30,
    "unionen_non_ai_adopter_planned_professional_cuts_adjusted": 14,
}
REQUIRED = {**dict((k,v[0]) for k,v in CLUBS.items()),
            **dict((k,v[0]) for k,v in AI_ADOPTERS.items()),**CONTEXT}
SCOPE = (
    "Unionen Branschbarometern, fieldwork 24 September-9 October 2026; "
    "responses from 468 workplace union clubs representing 421 firms. "
    "The headline sample's firms collectively employ around 526,000 people; "
    "that is not the number of respondents or a national employer census. "
    "Response rate: 27%. AI staffing-change questions drew on 270 clubs "
    "at employers that reported adopting AI, with multiple answers permitted."
)
BOUNDARY = (
    "This is a survey of responding private-sector workplace union clubs. "
    "It is not a representative employer census, an estimate of AI/Data "
    "vacancies or an observed count of workers affected. SCB enterprise AI-use "
    "figures use a different population and method; the percentages are not "
    "directly comparable. The reported relationship between AI adoption and "
    "planned white-collar reductions is an association, not evidence that "
    "AI caused those cuts; its certainty weakens under employee weighting."
)
CONCLUSION = (
    "More orders and more positive business expectations are not yet translating "
    "into a comparable increase in white-collar employment expectations. "
    "At some workplaces, adopting AI coincides with both new specialist "
    "responsibilities and fewer positions elsewhere. The sensible response "
    "is to evaluate the tasks, skills and accountability a business will need, "
    "and to check actual recruitment evidence before assuming new vacancies."
)

def verify_release(points: list[dict], slug: str) -> bool:
    if slug != NEW_SLUG:
        return False
    by={p["code"]:p for p in points}
    if len(by)!=len(points):
        raise ValueError("Repeated observation codes in Unionen Market Signals release")
    for code,expected in REQUIRED.items():
        p=by.get(code)
        if p is None or float(p.get("value"))!=float(expected):
            raise ValueError("Unionen source observation missing or drifted: "+code)
        if p.get("source_family")!="unionen_branschbarometern":
            raise ValueError("Unionen observation has an inconsistent source family: "+code)
        if str(p.get("published_on"))[:10]!="2026-11-18":
            raise ValueError("Unionen report publication date mismatch: "+code)
        if str(p.get("period_end"))[:10]!="2026-10-09":
            raise ValueError("Unionen survey reference period mismatch: "+code)
    return True

def pdf_section(story: list, points: list[dict], slug: str, *, sty: dict, audience: str) -> None:
    """Add authentic analysis pages, bound to the exact selected source observations."""
    if not verify_release(points,slug):
        return
    from market_publication_design import P, bars, panel, section
    story.append(PageBreak())
    section(
        story,"RESEARCH UPDATE / UNIONEN / 21 NOVEMBER 2026",
        "More business activity, slower professional hiring",
        "Unionen's autumn workplace survey adds a useful view of professional "
        "employment to the SCB, KI and JobTech evidence. Business expectations "
        "have improved, while the responding clubs do not expect an overall "
        "increase in white-collar employment over the coming six months.",
        sty=sty
    )
    story.append(panel(
        "A separate survey population","Unionen business outlook index: 56",
        "The neutral index value is 50. The survey covers union representatives "
        "at private-sector workplaces. A positive business outlook is not a "
        "count of jobs created or a forecast of AI/Data vacancies.",sty=sty
    ))
    story.append(Spacer(1,13))
    story.append(P("AI at responding workplace union clubs","h2",sty=sty))
    story.append(bars([(name,float(value)) for value,name in CLUBS.values()],sty=sty))
    story.append(P(
        "83% reported employer AI adoption; 16% reported negotiating or "
        "planning negotiations about AI. These are percentages of responding "
        "clubs and should not be compared numerically with the separate SCB "
        "enterprise AI survey.","caption",sty=sty))
    story.append(Spacer(1,12))
    story.append(P("Employment effects reported at AI-adopting employers","h2",sty=sty))
    story.append(bars([(name,float(value)) for value,name in AI_ADOPTERS.values()],sty=sty))
    story.append(P(
        "Unionen's AI-effects question was answered by 270 clubs at AI-adopting "
        "employers. Multiple answers were allowed. New roles, non-replacement and "
        "redundancies can occur at different teams in the same firm; the "
        "percentages must not be added together or interpreted as employee counts.",
        "caption",sty=sty))
    story.append(Spacer(1,13))
    story.append(P("What the evidence does and does not establish","h2",sty=sty))
    story.append(P(BOUNDARY,"body_small",sty=sty))
    story.append(Spacer(1,11))
    if audience=="executive":
        story.append(panel(
            "Executive decision","Plan work and workforce change together",
            "Ask where AI is changing work, which tasks and exceptions still need "
            "people, whether employees are being retrained and who decides when "
            "a role is redesigned. Separate planned staffing changes from "
            "measured productivity and actual recruitment before allocating "
            "new positions or external support.",sty=sty))
        story.append(P(
            "Sector detail: Unionen reported an automotive outlook index of "
            "45, below its neutral 50, while consulting and staffing was "
            "relatively more positive about professional employment. Neither "
            "measure counts senior AI roles or consulting assignments.","body",sty=sty))
    else:
        story.append(panel(
            "Career decision","Follow responsibilities, not market slogans",
            "Look for roles where your skills solve an employer's specific "
            "problem, including AI and data work inside established professions. "
            "Compare permanent openings with suitable fixed-term and consulting "
            "work, and ask how employers are changing their teams. "
            "A survey finding is not a promise that a vacancy exists.",sty=sty))
        story.append(P(
            "Unionen's sector detail offers reasons to check consulting "
            "opportunities while staying selective about industries facing "
            "weak recruitment conditions, including automotive. The survey "
            "does not rank career paths or establish individual job prospects.",
            "body",sty=sty))
    story.append(Spacer(1,11))
    story.append(P(
        "Publisher: Unionen, Fler ordrar. Fler och battre jobb?, released "
        "18 November 2026. Fieldwork: 24 September-9 October. "
        "Original report and announcement: "+SOURCE_REPORT+" | "+SOURCE,
        "caption",sty=sty
    ))

def reader_panel(st, points: list[dict], slug: str, audience: str) -> None:
    if not verify_release(points,slug):
        return
    title=("Workforce changes behind Sweden's AI adoption"
        if audience=="executive" else
        "What AI is changing in professional work")
    st.markdown("#### New research | Unionen, 18 November 2026")
    st.html(
      '<section class="ms-unionen-research" style="border:1px solid #ddd8d0;'
      'border-top:4px solid #b58a68;background:#fbfaf7;padding:clamp(22px,3vw,36px);'
      'margin:13px 0 23px">'
      '<div style="font-size:11px;letter-spacing:.13em;font-weight:800;'
      'color:#986647">UNIONEN / WORKPLACE SURVEY / AUTUMN 2026</div>'
      '<h3 style="font:500 clamp(25px,3vw,37px)/1.18 Georgia,serif;'
      'color:#193449;margin:12px 0">'+escape(title)+'</h3>'
      '<p style="font-size:15px;line-height:1.75;color:#344c61">'+
      escape(CONCLUSION)+'</p>'
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));'
      'gap:10px;margin:21px 0">'
      '<div style="background:#eee9e1;padding:17px"><strong style="display:block;'
      'font:500 31px Georgia,serif;color:#193449">83%</strong><span>'
      'Clubs reporting AI adoption</span></div>'
      '<div style="background:#eee9e1;padding:17px"><strong style="display:block;'
      'font:500 31px Georgia,serif;color:#193449">42%</strong><span>'
      'At AI-adopting firms, clubs reporting changed staffing needs</span></div>'
      '<div style="background:#eee9e1;padding:17px"><strong style="display:block;'
      'font:500 31px Georgia,serif;color:#193449">24%</strong><span>'
      'At AI-adopting firms, clubs reporting new specialist roles</span></div>'
      '</div><p style="font-size:12px;line-height:1.65;color:#667786">'
      'Different survey subgroups. Multiple responses were possible for staffing '
      'effects. These figures count responding clubs, not jobs or employees.</p>'
      '</section>'
    )
    with st.expander("Survey method, employment outcomes and source",expanded=False):
        st.write(SCOPE)
        st.write(BOUNDARY)
        st.write(
          "Among clubs at AI-adopting workplaces, 13% reported positions "
          "not replaced and 13% reported redundancies attributed to AI. "
          "The 30% versus 14% adjusted association with planned "
          "white-collar cuts does not establish causation and becomes "
          "less certain when weighted by employee headcount."
        )
        st.markdown("[Read Unionen's original report]("+SOURCE_REPORT+")")
