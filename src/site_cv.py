from __future__ import annotations

"""Build and expose the canonical public CV used by every website download CTA."""

from pathlib import Path

from fpdf import FPDF

import site_assets

NAVY = (11, 18, 32)
INK = (17, 21, 27)
MUTED = (82, 92, 103)
COPPER = (184, 97, 52)
LINE = (215, 209, 199)
WHITE = (255, 253, 248)

LINKEDIN_DISPLAY = "linkedin.com/in/jairribeiro"
LINKEDIN_URL = "https://www.linkedin.com/in/jairribeiro"
CV_SITE_DISPLAY = "jairribeiro-ai.streamlit.app"
CV_SITE_URL = "https://jairribeiro-ai.streamlit.app/?source=cv"


class _CVPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-9)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 4, f"Jair Ribeiro | Senior AI & Data Leader | Page {self.page_no()}", align="R")


def build_public_cv() -> bytes:
    pdf = _CVPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=13)
    pdf.set_margins(16, 14, 16)
    pdf.add_page()

    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_xy(16, 10)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, "JAIR RIBEIRO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10.2)
    pdf.set_text_color(240, 192, 157)
    pdf.cell(
        0,
        5.5,
        "Senior AI & Data Leader | Enterprise AI Strategy, Governance, Adoption & Business Value",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(215, 223, 232)
    pdf.cell(
        0,
        4.2,
        "Gothenburg, Sweden | jair.ribeiro@outlook.it | +46 76 761 21 58",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(215, 223, 232)
    linkedin_width = pdf.get_string_width(LINKEDIN_DISPLAY)
    separator_width = pdf.get_string_width(" | ")
    pdf.cell(linkedin_width, 4.2, LINKEDIN_DISPLAY, link=LINKEDIN_URL)
    pdf.cell(separator_width, 4.2, " | ")
    pdf.cell(0, 4.2, CV_SITE_DISPLAY, link=CV_SITE_URL, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(48)

    def section(title: str) -> None:
        pdf.ln(1.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*COPPER)
        pdf.cell(0, 5.2, title.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*LINE)
        y = pdf.get_y()
        pdf.line(16, y, 194, y)
        pdf.ln(2.2)
        pdf.set_text_color(*INK)

    def paragraph(
        text: str,
        size: float = 8.8,
        color: tuple[int, int, int] = INK,
        line: float = 4.35,
        bold: bool = False,
    ) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, line, text, new_x="LMARGIN", new_y="NEXT")

    def bullet(text: str, size: float = 8.5, line: float = 4.15) -> None:
        x = pdf.l_margin
        y = pdf.get_y()
        pdf.set_x(x)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*COPPER)
        pdf.cell(4, line, "-")
        pdf.set_xy(x + 5, y)
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(*INK)
        pdf.multi_cell(0, line, text, new_x="LMARGIN", new_y="NEXT")

    def role(
        title: str,
        company: str,
        dates: str,
        location: str,
        bullets: list[str],
    ) -> None:
        if pdf.get_y() > 254:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 9.2)
        pdf.set_text_color(*INK)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 4.7, f"{title} | {company}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 7.9)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(0, 4.0, f"{dates} | {location}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.4)
        for item in bullets:
            bullet(item)
        pdf.ln(1.5)

    section("Executive Profile")
    paragraph(
        "Enterprise AI, data and analytics leader with 20+ years in enterprise technology, including 8+ years in AI, data and analytics leadership. I turn AI ambition into operating capability by connecting business priorities, opportunity portfolios, data and architecture, governance, adoption and measurable value. Experience includes AI & Data Center of Excellence leadership, regional AI strategy, global analytics and AI adoption, product and portfolio work, and executive stakeholder engagement across automotive, consumer goods and enterprise technology environments.",
        size=8.8,
        line=4.45,
    )

    section("Core Leadership & Domain Expertise")
    paragraph(
        "Enterprise AI strategy | AI & Data operating models | AI & Data CoE design | AI governance & Responsible AI | AI portfolio prioritization | Data strategy, governance & trust | GenAI & agentic AI enablement | Analytics strategy | Product & portfolio leadership | Value discovery & business cases | Enterprise architecture | Cloud & AI solutions | Adoption, literacy & change | Executive stakeholder management | Management consulting",
        size=8.35,
        line=4.25,
    )

    section("Selected Leadership Impact")
    bullet("Shaped and supported 100+ AI initiatives, proofs of concept and projects across multiple regions and business functions.")
    bullet("Designed and delivered AI literacy and adoption activity reaching 1,000+ employees, with 100+ learning sessions delivered across Volvo Group roles.")
    bullet("Worked across business, data, technology, governance and risk stakeholders to move AI opportunities from early discovery toward governed, usable enterprise capability.")
    bullet("Built practical experience across AI strategy, portfolio governance, operating-model design, data foundations, responsible adoption and scale-readiness.")

    section("Professional Experience")
    role(
        "AI & Data Center of Excellence Director",
        "MSX International",
        "Dec 2025 - Jun 2026",
        "Gothenburg, Sweden",
        [
            "Led the foundations of a business-facing AI & Data Center of Excellence, connecting AI strategy, data governance, responsible AI, adoption and enterprise scale-readiness.",
            "Structured AI opportunity and lifecycle governance with clearer stages, ownership, decision points and criteria for moving initiatives toward investment and scale.",
            "Advanced data-governance foundations covering ownership, stewardship, data quality and trusted-data practices.",
            "Partnered with strategy, operations, technology and business leaders to make AI priorities, dependencies and next decisions clearer.",
        ],
    )
    role(
        "Data Analytics and AI Leader",
        "Volvo Group / Volvo Trucks",
        "Aug 2022 - Dec 2025",
        "Gothenburg, Sweden",
        [
            "Led AI and analytics adoption across commercial operations, including warranty, sales and aftermarket, translating business needs into practical AI use cases and workflow improvements.",
            "Designed and launched AI literacy and adoption programs reaching thousands of employees worldwide and supporting responsible use of generative AI.",
            "Led cross-functional proofs of concept across warranty, sales, aftermarket, legal, compliance and sustainability, coordinating business, Digital & IT and specialist stakeholders.",
            "Worked on AI solutions and agents intended to reduce cycle time and cost while improving adoption in everyday operations.",
        ],
    )
    role(
        "Artificial Intelligence Strategist - EMEA",
        "Kimberly-Clark",
        "Jul 2021 - Sep 2022",
        "Krakow, Poland / EMEA",
        [
            "Managed value discovery and realization for AI and Data Science initiatives across EMEA, connecting business priorities with feasible AI opportunities.",
            "Worked in a global role reporting to the Chief Data & Analytics Officer and supporting the company ambition to become more AI-driven.",
            "Partnered with functions including supply chain, manufacturing, sales, marketing and logistics to shape use cases around business value and readiness.",
        ],
    )

    if pdf.get_y() > 230:
        pdf.add_page()

    role(
        "Senior Artificial Intelligence Business Expert",
        "Volvo Group",
        "Jun 2018 - Jul 2021",
        "Wroclaw, Poland",
        [
            "Led business requirements, product management and stakeholder management for 100+ AI initiatives, proofs of concept and projects across multiple regions.",
            "Delivered 100+ sessions and training opportunities to strengthen AI literacy across the global Volvo Group.",
            "Contributed to enterprise AI community and Center of Excellence activity, helping connect use-case demand, technical teams and practical adoption.",
        ],
    )
    role(
        "Cloud and AI Project Manager | IBM Watson Solution Designer",
        "IBM",
        "Jul 2017 - Jun 2018",
        "Wroclaw, Poland",
        [
            "Applied IBM Design Thinking to frame customer problems and shape technology solutions around user and business needs.",
            "Worked as an IBM Watson Solutions Designer, advising sales teams and supporting the development and positioning of cognitive and AI solutions.",
        ],
    )

    section("Earlier Career")
    paragraph(
        "AI, Cloud, IT Consulting & Infrastructure Roles | IBM, Hewlett Packard Enterprise and earlier employers",
        size=8.5,
        bold=True,
    )
    paragraph("2004 - 2018 | Italy, Brazil and Poland", size=8.2, color=MUTED)
    bullet("Built a broad technology foundation spanning AI and cloud projects, IBM Watson solution design, virtualization, data centers, enterprise systems and IT delivery.")
    bullet("Worked across consulting, architecture, infrastructure, client engagement and project delivery in multicultural environments.")

    section("Technical & Enterprise Fluency")
    paragraph(
        "GenAI | Large Language Models (LLM) | Agentic AI | Enterprise AI architecture | Analytics | Data platforms | Data quality | Stewardship | Cloud | MLOps principles | Security | AI risk | Governance | Scalability | Vendor evaluation | Cost / accuracy trade-offs | Operational readiness",
        size=8.35,
        line=4.25,
    )

    section("Education")
    paragraph("Selinus University of Sciences and Literature - MSc, Artificial Intelligence", size=8.5, bold=True)
    paragraph("Research focus: Responsible AI Adoption in Global Enterprises | Oct 2025 - Jun 2026", size=8.2, color=MUTED)

    section("Languages")
    paragraph(
        "Portuguese - native/bilingual | Italian - native/bilingual | English - full professional | Spanish - professional | Polish - limited working | Swedish - elementary",
        size=8.35,
    )

    section("Recognition & Thought Leadership")
    bullet("Thinkers360 Top 50 Global Thought Leaders & Influencers on Emerging Technology (2023).")
    bullet("Speaker on enterprise AI adoption, including strategies for scaling AI across the enterprise.")
    bullet("Published writing on AI strategy, governance, operating models, data readiness, Responsible AI and enterprise adoption.")
    bullet("Selected publication: How to Implement an effective AI strategy in your business.")

    return bytes(pdf.output())


CV_BYTES = build_public_cv()
ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)
CV_FILENAME = "Jair_Ribeiro_Senior_AI_Data_Leader_CV_2026.pdf"
(STATIC_DIR / CV_FILENAME).write_bytes(CV_BYTES)

site_assets.CV_BYTES = CV_BYTES
site_assets.CV_URI = f"/app/static/{CV_FILENAME}"
