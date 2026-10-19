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
CV_SITE_DISPLAY = "AI & Data Portfolio"
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
        mandate: str | None = None,
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
        if mandate:
            pdf.set_x(16)
            pdf.set_font("DejaVu", "", 7.7)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(178, 3.85, "Mandate: " + mandate, new_x="LMARGIN", new_y="NEXT")
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
    cv_headline = "Enterprise AI & Data Leader | Strategy - Operating Models - Governance - Adoption - Business Value"
    pdf.set_font("DejaVu", "B", 8.6)
    if pdf.get_string_width(cv_headline) > 178:
        raise ValueError("CV headline must fit on one line")
    pdf.set_text_color(*ACCENT)
    pdf.cell(
        0,
        4.85,
        cv_headline,
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
    pdf.cell(
        0,
        4.0,
        "Sweden / Nordic scope | Open to immediate collaboration and relevant mandates",
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
        f"Enterprise AI, Data and Analytics leader with {PROFILE_TECH_YEARS} years in enterprise technology and {PROFILE_AI_LEADERSHIP_YEARS} years focused on AI, data and analytics leadership across MSX International, Volvo Group, Kimberly-Clark and IBM. I work where strategy has to become something the business can actually use - setting priorities, clarifying ownership, putting the right governance in place and helping teams adopt AI in day-to-day work. My experience spans Microsoft 365 Copilot and agent initiatives, AI in {VOLVO_WORKFLOW_SCOPE} workflows, EMEA value discovery, and building the operating and governance foundations needed to scale AI with clearer ownership and business value.",
        size=8.2,
        line=4.15,
    )

    section("Core Leadership Areas", 2.8)
    body(
        "Enterprise AI Strategy | AI & Data Operating Models / CoEs | AI Governance & Responsible AI | Data Governance & Trusted Data | AI Portfolio & Value Realization",
        size=7.7,
        line=3.9,
    )
    pdf.ln(0.3)
    body(
        "Enterprise AI Adoption & Workflow Change | Data & Analytics Leadership | Generative AI & Agentic AI | Product & Portfolio Leadership | Executive Stakeholder Management",
        size=7.7,
        line=3.9,
    )

    section("Professional Experience", 2.8)
    role(
        MSX_TITLE,
        MSX_COMPANY,
        MSX_PUBLIC_DATES,
        "Göteborg, Sweden",
        [
            "Created an AI opportunity portfolio and lifecycle process with named decision owners, stage criteria and readiness-to-scale checks, making prioritization and accountability easier to examine.",
            f"Translated AI and data maturity assessment into a {MSX_ROADMAP} roadmap, identifying capability gaps and priorities for stewardship, data ownership and trusted information.",
            "Established early CoE governance and engagement mechanisms across business and technology stakeholders, giving an emerging enterprise capability a more defined working structure.",
        ],
        company_context=MSX_CONTEXT,
        mandate="Build the foundations of a business-facing AI & Data Center of Excellence, covering portfolio governance, data accountability and adoption.",
    )

    role(
        VOLVO_CURRENT_TITLE,
        "Volvo Group / Volvo Trucks",
        VOLVO_CURRENT_DATES,
        "Göteborg, Sweden",
        [
            f"Led Microsoft 365 Copilot and agent initiatives alongside AI solutions introduced into {VOLVO_WORKFLOW_SCOPE} workflows, connecting adoption with real commercial work and human review.",
            "Connected business teams with Digital & IT, legal, compliance and other stakeholders to frame use cases, clarify dependencies and consider practical responsible-use requirements.",
            "Designed practical AI innovation and literacy programs reaching thousands of employees globally, building understanding of AI use and its limits.",
            f"Across my two Volvo AI roles (2018–2021 and 2022–2025), led business-requirement, product and stakeholder work on {VOLVO_AI_INITIATIVES} AI initiatives, PoCs and projects across regions.",
        ],
        mandate="Lead AI and analytics adoption in commercial operations, with business ownership, operational fit and responsible use at the center.",
    )

    role(
        KIMBERLY_TITLE,
        "Kimberly-Clark",
        KIMBERLY_DATES,
        "Kraków, Poland",
        [
            "Led EMEA AI and Data Science value discovery, reporting directly to the Chief Data & Analytics Officer; made business problems, expected value and feasibility explicit before technical solution selection.",
            f"Worked across {KIMBERLY_SCOPE} to compare opportunities against business readiness, data conditions and delivery considerations.",
        ],
        mandate="Help EMEA functions evaluate AI opportunities against business priorities and readiness, not technology appeal alone.",
    )

    role(
        VOLVO_SENIOR_AI_TITLE,
        "Volvo Group",
        VOLVO_SENIOR_AI_DATES,
        "Wroclaw, Poland",
        [
            "Led business requirements, product and stakeholder coordination in AI and ML CoE work, translating cross-regional business needs into AI use cases and delivery discussions.",
            f"Delivered {VOLVO_AI_LEARNING_SESSIONS} AI learning sessions and supported enterprise practitioner communities, strengthening shared AI understanding across business and technical teams.",
        ],
        mandate="Connect enterprise AI demand, stakeholders and CoE specialists while building practical literacy and business engagement.",
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
    earlier("Infrastructure Services Solution Manager", "IBM", "Jul 2016 - Jul 2017")
    earlier("Project Manager (concurrent IBM assignment)", "IBM", "Apr 2017 - Aug 2017")
    earlier("IT&C Manager / Senior IT Engineer / IT Project Manager", "Hewlett Packard Enterprise", "Jan 2013 - Jul 2016")
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
    # Keep the compact CV selection sourced from the canonical credential list.
    selected_credentials = (
        f"{SELECTED_CREDENTIALS[0]} | {SELECTED_CREDENTIALS[1]} - Microsoft | "
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


# The PDF builder above runs only in CI to refresh the committed static CV.
# At application runtime this module reads the approved PDF; it must not
# regenerate or overwrite the downloadable artifact.
ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
CV_PATH = STATIC_DIR / CV_FILENAME
if not CV_PATH.is_file():
    raise FileNotFoundError(f"Approved public CV is missing: {CV_PATH}")
CV_BYTES = CV_PATH.read_bytes()

site_assets.CV_BYTES = CV_BYTES
site_assets.CV_URI = f"app/static/{CV_FILENAME}"
