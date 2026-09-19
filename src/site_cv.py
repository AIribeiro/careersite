from __future__ import annotations

"""Build and expose the reviewed canonical public CV used by every website download CTA."""

from pathlib import Path
from fpdf import FPDF
import site_assets

ACCENT = (24, 91, 117)
TEXT = (31, 41, 51)
MUTED = (93, 111, 123)
RULE = (214, 224, 229)

LINKEDIN_DISPLAY = "LinkedIn Profile"
LINKEDIN_URL = "https://www.linkedin.com/in/jairribeiro"
CV_SITE_DISPLAY = "AI Leadership Portfolio"
CV_SITE_URL = "https://jairribeiro-ai.streamlit.app/?source=cv"
CERTIFICATIONS_DISPLAY = "View additional certifications and credentials"
CERTIFICATIONS_URL = "https://jairribeiro-ai.streamlit.app/?page=certifications&utm_source=cv"
CV_FILENAME = "Jair_Ribeiro_CV.pdf"


class _CVPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("DejaVu", "", 6.8)
        self.set_text_color(136, 151, 162)
        self.cell(0, 4, "Jair Ribeiro - Portfolio CV")
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

    def section(title: str, before: float = 3.5) -> None:
        pdf.ln(before)
        pdf.set_font("DejaVu", "B", 8.2)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 4.4, title.upper(), new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y() + 0.25
        pdf.set_draw_color(*RULE)
        pdf.set_line_width(0.2)
        pdf.line(16, y, 194, y)
        pdf.set_y(y + 2.3)

    def body(text: str, size: float = 8.45, line: float = 4.45, color=TEXT, bold: bool = False) -> None:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "B" if bold else "", size)
        pdf.set_text_color(*color)
        pdf.multi_cell(178, line, text, new_x="LMARGIN", new_y="NEXT")

    def role(title: str, company: str, dates: str, location: str, bullets: list[str]) -> None:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "B", 9.0)
        pdf.set_text_color(*TEXT)
        pdf.write(4.7, f"{title} | ")
        pdf.set_text_color(*ACCENT)
        pdf.write(4.7, company)
        pdf.ln(4.8)
        pdf.set_font("DejaVu", "", 7.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 3.8, f"{dates} | {location}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.3)
        for item in bullets:
            x, y = 18, pdf.get_y()
            pdf.set_xy(x, y)
            pdf.set_font("DejaVu", "", 8.0)
            pdf.set_text_color(*TEXT)
            pdf.multi_cell(176, 4.1, f"• {item}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.2)

    def earlier(title: str, company: str, dates: str) -> None:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "", 7.8)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(178, 4.0, f"{title} | {company} | {dates}", new_x="LMARGIN", new_y="NEXT")

    pdf.add_page()
    top_rule()
    pdf.set_y(17.5)
    pdf.set_font("DejaVu", "B", 23.5)
    pdf.set_text_color(*TEXT)
    pdf.cell(0, 10, "Jair Ribeiro", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "B", 10.4)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(
        0,
        5.0,
        "Enterprise AI & Data Leader | Strategy - Operating Models - Governance - Adoption - Business Value",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(1.0)
    pdf.set_font("DejaVu", "", 7.7)
    pdf.set_text_color(*MUTED)
    pdf.cell(
        0,
        4.1,
        "Gothenburg, Sweden | jair.ribeiro@outlook.it | +46 76 761 21 58",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    linkedin_w = pdf.get_string_width(LINKEDIN_DISPLAY)
    sep_w = pdf.get_string_width(" | ")
    pdf.cell(linkedin_w, 4.1, LINKEDIN_DISPLAY, link=LINKEDIN_URL)
    pdf.cell(sep_w, 4.1, " | ")
    pdf.cell(0, 4.1, CV_SITE_DISPLAY, link=CV_SITE_URL, new_x="LMARGIN", new_y="NEXT")

    section("Professional Summary", 3.6)
    body(
        "Artificial Intelligence (AI) and Data leader with enterprise experience across MSX International, Volvo Group, Kimberly-Clark and IBM. Builds the structures that move AI from experimentation into repeatable business capability, including portfolio governance, operating models, responsible AI, adoption and value realization. Experience includes supporting operational use of AI in warranty, sales and aftermarket workflows, alongside enterprise AI strategy, product and portfolio leadership, cross-functional delivery and responsible adoption across global and Europe, Middle East and Africa (EMEA) environments."
    )

    section("Selected Impact")
    body(
        "Supported operational adoption of AI solutions and agents in warranty, sales and aftermarket workflows, moving AI beyond awareness into everyday business processes.",
        size=8.1,
        line=4.2,
    )
    body(
        "Applied Generative AI to translation, summarization, structured analysis, communications and commercial operations, with human review and responsible-use practices.",
        size=8.1,
        line=4.2,
    )
    body(
        "100+ AI initiatives, Proofs of Concept (PoCs) and projects supported across multiple regions at Volvo Group, complemented by 100+ AI literacy sessions as adoption enablement.",
        size=8.1,
        line=4.2,
    )

    section("Core Competencies")
    body(
        "Enterprise AI Strategy | AI & Data Center of Excellence (CoE) | AI Operating Models | Responsible AI & AI Governance | Data Governance | AI Portfolio Management | Value Management",
        size=7.95,
        line=4.1,
    )
    pdf.ln(0.5)
    body(
        "AI Adoption & Change | Data & Analytics Leadership | AI Product Management | Product Management | Executive Stakeholder Management | Generative AI & Large Language Models (LLMs)",
        size=7.95,
        line=4.1,
    )

    section("Professional Experience")
    role(
        "AI & Data Center of Excellence Director",
        "MSX International",
        "2025 - 2026",
        "Gothenburg, Sweden",
        [
            "Established and led MSXi's AI & Data Center of Excellence, connecting AI and data strategy, governance, adoption and business value across strategy, operations and technology.",
            "Introduced lifecycle discipline for AI initiatives, with clearer stages, roles, ownership and scale-readiness criteria.",
            "Worked with business and technology leaders to move AI opportunities from isolated experimentation toward managed enterprise capability and responsible adoption.",
        ],
    )
    role(
        "Data Analytics and AI Leader",
        "Volvo Group",
        "Aug 2022 - Dec 2025",
        "Greater Gothenburg Metropolitan Area, Sweden",
        [
            "Supported operational adoption of AI solutions and agents in warranty, sales and aftermarket workflows, working with business teams to move use cases into everyday processes.",
            "Applied Generative AI in translation, summarization, structured analysis, communications and commercial operations, with human review and responsible-use practices.",
            "Designed and launched AI innovation and literacy programs reaching thousands of employees worldwide, building the knowledge and confidence required to use AI responsibly.",
            "Led cross-functional AI Proofs of Concept across warranty, sales, aftermarket, legal, compliance and sustainability, connecting business problems with practical AI use cases.",
        ],
    )
    role(
        "Artificial Intelligence Strategist - EMEA",
        "Kimberly-Clark",
        "Jul 2021 - Sep 2022",
        "Krakow Metropolitan Area, Poland",
        [
            "Managed value discovery and realization for AI and Data Science initiatives supporting the company's AI agenda across EMEA.",
            "Worked in a global role reporting directly to the Chief Data & Analytics Officer, connecting AI ambition with business opportunities and investment choices.",
        ],
    )

    pdf.add_page()
    top_rule()
    pdf.set_y(16.5)
    pdf.set_font("DejaVu", "B", 12.0)
    pdf.set_text_color(*TEXT)
    pdf.cell(0, 5.4, "Jair Ribeiro", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "B", 8.5)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 4.0, "Enterprise AI & Data Leader", new_x="LMARGIN", new_y="NEXT")

    section("Professional Experience", 3.2)
    role(
        "Senior Artificial Intelligence Business Expert",
        "Volvo Group",
        "Jun 2018 - Jul 2021",
        "Wroclaw, Poland",
        [
            "Led business requirements, product management and stakeholder engagement for 100+ AI initiatives, Proofs of Concept and projects across multiple regions.",
            "Delivered 100+ AI literacy sessions and training opportunities across the global Volvo Group, supporting broader enterprise capability and adoption.",
        ],
    )
    role(
        "Cloud and AI Project Manager | IBM Watson Solution Designer",
        "IBM",
        "Jul 2017 - Jun 2018",
        "Wroclaw, Poland",
        [
            "Worked as an IBM Watson Solution Designer, providing technical advice to sales teams and supporting the development and sale of cognitive solutions.",
            "Applied IBM Design Thinking to frame customer problems and shape technology-led solutions around user and business needs.",
        ],
    )

    section("Earlier Career", 2.8)
    earlier("Founder, ICT Manager", "Imprendo Consulting", "Mar 2012 - Apr 2013")
    earlier("Information Technology System Administrator", "CityLife S.p.A", "Jun 2009 - Mar 2012")
    earlier("Application Testing & Documentation", "AXA Assicurazioni", "Mar 2009 - May 2009")
    earlier("IT System Administrator", "PeopleLab Srl", "May 2007 - Apr 2009")

    section("Education", 2.8)
    body(
        "Selinus University of Sciences and Literature | Master of Science (MSc), Artificial Intelligence | Oct 2025 - Jun 2026",
        size=7.85,
        line=4.0,
    )
    body(
        "Research focus: Responsible AI Adoption in Global Enterprises",
        size=7.75,
        line=3.9,
        color=MUTED,
    )
    pdf.ln(0.5)
    body(
        "Massachusetts Institute of Technology - edX | MicroMasters program, Statistics and Data Science",
        size=7.85,
        line=4.0,
    )
    body(
        "Massachusetts Institute of Technology | Minds and Machines - Philosophy & Ethics",
        size=7.85,
        line=4.0,
    )
    pdf.ln(0.6)
    pdf.set_x(16)
    pdf.set_font("DejaVu", "", 7.7)
    pdf.set_text_color(*ACCENT)
    pdf.cell(
        pdf.get_string_width(CERTIFICATIONS_DISPLAY),
        4.0,
        CERTIFICATIONS_DISPLAY,
        link=CERTIFICATIONS_URL,
        new_x="LMARGIN",
        new_y="NEXT",
    )

    section("Languages", 2.8)
    body(
        "English C2 | Italian Native | Portuguese Native | Spanish B2 | Polish B1 | Swedish A2 | French A2",
        size=7.85,
        line=4.0,
    )

    section("Publications & Recognition", 2.8)
    body(
        "Thinkers360 Top 50 Global Thought Leaders on Emerging Technology | 2023",
        size=7.75,
        line=3.95,
    )
    body(
        "Leading in the AI Enterprise | Article series on AI strategy, ROI, operating models, governance, data readiness, workforce redesign, talent and adoption.",
        size=7.75,
        line=3.95,
    )
    body(
        "AI Governance Is Not About Control. It Is About Scale. | Digital First Magazine, 2026",
        size=7.75,
        line=3.95,
    )
    body(
        "How to Implement an Effective AI Strategy in Your Business | Publication on practical enterprise AI strategy.",
        size=7.75,
        line=3.95,
    )

    return bytes(pdf.output())


CV_BYTES = build_public_cv()
ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / CV_FILENAME).write_bytes(CV_BYTES)

site_assets.CV_BYTES = CV_BYTES
site_assets.CV_URI = f"app/static/{CV_FILENAME}"
