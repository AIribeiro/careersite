from __future__ import annotations

"""Build and expose the reviewed canonical public CV used by every website download CTA."""

from pathlib import Path

from fpdf import FPDF

import site_assets
from career_facts import (
    CERTIFICATIONS_URL,
    IBM_DATES,
    IBM_TITLE,
    KIMBERLY_DATES,
    KIMBERLY_SCOPE,
    KIMBERLY_TITLE,
    MSX_COMPANY,
    MSX_CONTEXT,
    MSX_PUBLIC_DATES,
    MSX_ROADMAP,
    MSX_TITLE,
    PORTFOLIO_CV_URL,
    PRESENCE_URL,
    PROFILE_AI_LEADERSHIP_YEARS,
    PROFILE_TECH_YEARS,
    SELECTED_CREDENTIALS,
    VOLVO_AI_INITIATIVES,
    VOLVO_AI_LEARNING_SESSIONS,
    VOLVO_CURRENT_DATES,
    VOLVO_CURRENT_TITLE,
    VOLVO_SENIOR_AI_DATES,
    VOLVO_SENIOR_AI_TITLE,
    VOLVO_WORKFLOW_SCOPE,
)

ACCENT = (24, 91, 117)
TEXT = (31, 41, 51)
MUTED = (93, 111, 123)
RULE = (214, 224, 229)

LINKEDIN_DISPLAY = "LinkedIn Profile"
LINKEDIN_URL = "https://www.linkedin.com/in/jairribeiro"
CV_SITE_DISPLAY = "AI Leadership Portfolio"
CV_SITE_URL = PORTFOLIO_CV_URL
CERTIFICATIONS_DISPLAY = "View additional certifications and credentials"
PRESENCE_DISPLAY = "Explore speaking and thought leadership"
CV_FILENAME = "Jair_Ribeiro_CV.pdf"


class _CVPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("DejaVu", "", 6.8)
        self.set_text_color(136, 151, 162)
        self.cell(0, 4, "Jair Ribeiro | Enterprise AI & Data Leadership")
        self.set_y(-10)
        self.cell(0, 4, f"{self.page_no()} / 2", align="R")


def build_public_cv() -> bytes:
    pdf = _CVPDF(format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(16, 13, 16)
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

    def top_rule() -> None:
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.55)
        pdf.line(16, 7.5, 194, 7.5)

    def section(title: str, before: float = 3.2) -> None:
        pdf.ln(before)
        pdf.set_font("DejaVu", "B", 8.15)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 4.35, title.upper(), new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y() + 0.2
        pdf.set_draw_color(*RULE)
        pdf.set_line_width(0.2)
        pdf.line(16, y, 194, y)
        pdf.set_y(y + 2.15)

    def body(
        text: str,
        size: float = 8.25,
        line: float = 4.25,
        color: tuple[int, int, int] = TEXT,
        bold: bool = False,
    ) -> None:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "B" if bold else "", size)
        pdf.set_text_color(*color)
        pdf.multi_cell(178, line, text, new_x="LMARGIN", new_y="NEXT")

    def bullet(text: str, size: float = 7.9, line: float = 4.02) -> None:
        pdf.set_x(18)
        pdf.set_font("DejaVu", "", size)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(176, line, f"• {text}", new_x="LMARGIN", new_y="NEXT")

    def role(
        title: str,
        company: str,
        dates: str,
        location: str,
        bullets: list[str],
        company_context: str | None = None,
    ) -> None:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "B", 8.9)
        pdf.set_text_color(*TEXT)
        pdf.write(4.55, f"{title} | ")
        pdf.set_text_color(*ACCENT)
        pdf.write(4.55, company)
        pdf.ln(4.6)
        pdf.set_font("DejaVu", "", 7.45)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 3.75, f"{dates} | {location}", new_x="LMARGIN", new_y="NEXT")
        if company_context:
            pdf.set_font("DejaVu", "", 7.35)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(178, 3.65, company_context, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.25)
        for item in bullets:
            bullet(item)
        pdf.ln(1.05)

    def earlier(title: str, company: str, dates: str) -> None:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "", 7.65)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(178, 3.88, f"{title} | {company} | {dates}", new_x="LMARGIN", new_y="NEXT")

    # Page 1
    pdf.add_page()
    top_rule()
    pdf.set_y(16.8)
    pdf.set_font("DejaVu", "B", 23)
    pdf.set_text_color(*TEXT)
    pdf.cell(0, 9.5, "Jair Ribeiro", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "B", 10.2)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(
        0,
        4.85,
        "Enterprise AI & Data Leader | Strategy - Operating Models - Governance - Adoption - Business Value",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(0.75)
    pdf.set_font("DejaVu", "", 7.65)
    pdf.set_text_color(*MUTED)
    pdf.cell(
        0,
        4.0,
        "Gothenburg, Sweden | jair.ribeiro@outlook.it | +46 76 761 21 58",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    linkedin_w = pdf.get_string_width(LINKEDIN_DISPLAY)
    sep_w = pdf.get_string_width(" | ")
    pdf.cell(linkedin_w, 4.0, LINKEDIN_DISPLAY, link=LINKEDIN_URL)
    pdf.cell(sep_w, 4.0, " | ")
    pdf.cell(0, 4.0, CV_SITE_DISPLAY, link=CV_SITE_URL, new_x="LMARGIN", new_y="NEXT")

    section("Professional Summary", 3.25)
    body(
        f"Enterprise AI, Data and Analytics leader with {PROFILE_TECH_YEARS} years in enterprise technology, including {PROFILE_AI_LEADERSHIP_YEARS} years in AI, data and analytics leadership across MSX International, Volvo Group, Kimberly-Clark and IBM. Builds the operating structures that turn AI strategy into governed, adopted and repeatable enterprise capability - spanning portfolio decisions, operating models, AI and data governance, Responsible AI, product and portfolio leadership, and business adoption. Experience includes operational AI use across {VOLVO_WORKFLOW_SCOPE}, EMEA value discovery, and enterprise CoE and data-governance foundations.",
        size=8.2,
        line=4.15,
    )

    section("Selected Leadership Impact", 3.0)
    bullet(
        f"Across Volvo AI roles, led business-requirement, product and stakeholder work across {VOLVO_AI_INITIATIVES} AI initiatives, Proofs of Concept (PoCs) and projects spanning multiple regions and functions.",
        7.8,
        3.95,
    )
    bullet(
        f"Supported operational adoption of AI solutions and agents in {VOLVO_WORKFLOW_SCOPE} workflows, moving AI beyond awareness into day-to-day business processes.",
        7.8,
        3.95,
    )
    bullet(
        f"At MSX, established AI & Data CoE foundations, portfolio and lifecycle governance, scale-readiness criteria, a {MSX_ROADMAP} maturity roadmap and initial data-governance foundations.",
        7.8,
        3.95,
    )
    bullet(
        f"At Kimberly-Clark, led EMEA AI value discovery and realization, reporting directly to the CDAO across {KIMBERLY_SCOPE}.",
        7.8,
        3.95,
    )

    section("Core Leadership Areas", 2.8)
    body(
        "Enterprise AI Strategy | AI & Data Operating Models / CoEs | AI Governance & Responsible AI | Data Governance & Trusted Data | AI Portfolio & Value Realization",
        size=7.7,
        line=3.9,
    )
    pdf.ln(0.3)
    body(
        "AI Adoption & Change | Data & Analytics Leadership | Generative AI & Agentic AI | Product & Portfolio Leadership | Executive Stakeholder Management",
        size=7.7,
        line=3.9,
    )

    section("Professional Experience", 2.8)
    role(
        MSX_TITLE,
        MSX_COMPANY,
        MSX_PUBLIC_DATES,
        "Gothenburg, Sweden",
        [
            "Established and led the foundations of MSXi's AI & Data Center of Excellence, connecting AI and data strategy, governance, adoption and business value across strategy, operations and technology.",
            "Introduced portfolio and lifecycle governance with clearer stages, decision rights, ownership and scale-readiness criteria.",
            f"Connected maturity assessment to a pragmatic {MSX_ROADMAP} roadmap and advanced data-governance foundations covering ownership, stewardship, data quality and trusted-data practices.",
            "Worked with business and technology leaders to move AI opportunities from isolated experimentation toward managed enterprise capability.",
        ],
        company_context=MSX_CONTEXT,
    )

    role(
        VOLVO_CURRENT_TITLE,
        "Volvo Group",
        VOLVO_CURRENT_DATES,
        "Greater Gothenburg Metropolitan Area, Sweden",
        [
            f"Led AI and analytics adoption across commercial operations, with AI solutions and agents introduced into {VOLVO_WORKFLOW_SCOPE} workflows and business teams engaged in day-to-day use.",
            "Applied Generative AI to translation, summarization, structured analysis, communications and commercial operations, with human review and responsible-use practices.",
            "Led cross-functional AI use-case and PoC work across warranty, sales, aftermarket, legal, compliance and sustainability, connecting business problems with practical AI solutions.",
            "Designed AI innovation and literacy programs reaching thousands of employees worldwide, strengthening responsible use and the quality of business demand.",
        ],
    )

    role(
        KIMBERLY_TITLE,
        "Kimberly-Clark",
        KIMBERLY_DATES,
        "Krakow Metropolitan Area, Poland",
        [
            "Led value discovery and realization for AI and Data Science opportunities across EMEA in a global role reporting directly to the Chief Data & Analytics Officer.",
            f"Partnered with {KIMBERLY_SCOPE} to frame business problems, value hypotheses, feasibility and readiness before technical solutioning.",
        ],
    )

    # Page 2
    pdf.add_page()
    top_rule()
    pdf.set_y(16.1)
    pdf.set_font("DejaVu", "B", 11.8)
    pdf.set_text_color(*TEXT)
    pdf.cell(0, 5.2, "Jair Ribeiro", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "B", 8.4)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 3.9, "Enterprise AI & Data Leader", new_x="LMARGIN", new_y="NEXT")

    section("Professional Experience", 3.0)
    role(
        VOLVO_SENIOR_AI_TITLE,
        "Volvo Group",
        VOLVO_SENIOR_AI_DATES,
        "Wroclaw, Poland",
        [
            f"Led business requirements, product management and stakeholder engagement across {VOLVO_AI_INITIATIVES} AI initiatives, PoCs and projects in multiple regions.",
            f"Delivered {VOLVO_AI_LEARNING_SESSIONS} AI learning sessions and training opportunities across the global Volvo Group, strengthening AI literacy and the quality of business demand.",
        ],
    )
    role(
        IBM_TITLE,
        "IBM",
        IBM_DATES,
        "Wroclaw, Poland",
        [
            "Worked as an IBM Watson Solution Designer, providing technical advice to sales teams and supporting the development and positioning of cognitive and AI solutions.",
            "Applied IBM Design Thinking to frame customer problems and shape technology-led solutions around user and business needs.",
        ],
    )

    section("Earlier Career", 2.5)
    earlier("Founder, ICT Manager", "Imprendo Consulting", "Mar 2012 - Apr 2013")
    earlier("Information Technology System Administrator", "CityLife S.p.A", "Jun 2009 - Mar 2012")
    earlier("Application Testing & Documentation", "AXA Assicurazioni", "Mar 2009 - May 2009")
    earlier("IT System Administrator", "PeopleLab Srl", "May 2007 - Apr 2009")

    section("Education", 2.45)
    body(
        "Selinus University of Sciences and Literature | Master of Science (MSc), Artificial Intelligence | Oct 2025 - Jun 2026",
        size=7.7,
        line=3.85,
    )
    body(
        "Research focus: Responsible AI Adoption in Global Enterprises",
        size=7.55,
        line=3.8,
        color=MUTED,
    )
    pdf.ln(0.35)
    body(
        "Massachusetts Institute of Technology - edX | MicroMasters program, Statistics and Data Science",
        size=7.7,
        line=3.85,
    )
    body(
        "Massachusetts Institute of Technology | Minds and Machines - Philosophy & Ethics",
        size=7.7,
        line=3.85,
    )
    pdf.ln(0.4)
    selected_credentials = (
        f"{SELECTED_CREDENTIALS[0]} | {SELECTED_CREDENTIALS[1]} - IBM | "
        f"{SELECTED_CREDENTIALS[2]} - University of Michigan"
    )
    body(
        f"Selected credentials: {selected_credentials}",
        size=7.25,
        line=3.65,
        color=MUTED,
    )
    pdf.ln(0.45)
    pdf.set_x(16)
    pdf.set_font("DejaVu", "", 7.55)
    pdf.set_text_color(*ACCENT)
    pdf.cell(
        pdf.get_string_width(CERTIFICATIONS_DISPLAY),
        3.85,
        CERTIFICATIONS_DISPLAY,
        link=CERTIFICATIONS_URL,
        new_x="LMARGIN",
        new_y="NEXT",
    )

    section("Languages", 2.45)
    body(
        "English C2 | Italian Native | Portuguese Native | Spanish B2 | Polish B1 | Swedish A2 | French A2",
        size=7.65,
        line=3.8,
    )

    section("Publications & Recognition", 2.45)
    body(
        "Thinkers360 Top 50 Global Thought Leaders on Emerging Technology | 2023",
        size=7.5,
        line=3.8,
    )
    body(
        "Leading in the AI Enterprise | Article series on AI strategy, ROI, operating models, governance, data readiness, workforce redesign, talent and adoption.",
        size=7.5,
        line=3.8,
    )
    body(
        "AI Governance Is Not About Control. It Is About Scale. | Digital First Magazine, 2026",
        size=7.5,
        line=3.8,
    )
    body(
        "How to Implement an Effective AI Strategy in Your Business | Publication on practical enterprise AI strategy.",
        size=7.5,
        line=3.8,
    )
    pdf.ln(0.45)
    pdf.set_x(16)
    pdf.set_font("DejaVu", "", 7.55)
    pdf.set_text_color(*ACCENT)
    pdf.cell(
        pdf.get_string_width(PRESENCE_DISPLAY),
        3.85,
        PRESENCE_DISPLAY,
        link=PRESENCE_URL,
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_title("Jair Ribeiro - Enterprise AI & Data Leader")
    pdf.set_author("Jair Ribeiro")
    pdf.set_subject("Curriculum Vitae")
    return bytes(pdf.output())


CV_BYTES = build_public_cv()
ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / CV_FILENAME).write_bytes(CV_BYTES)

site_assets.CV_BYTES = CV_BYTES
site_assets.CV_URI = f"app/static/{CV_FILENAME}"
