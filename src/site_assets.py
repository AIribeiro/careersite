from __future__ import annotations

from pathlib import Path
import base64

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "images"
LINKEDIN = "https://www.linkedin.com/in/jairribeiro"
MEDIUM = "https://jairribeiro.medium.com"
EMAIL = "jair.ribeiro@outlook.it"


def image_bytes(name: str) -> bytes:
    """Read canonical website photography directly from /images."""
    try:
        return (IMAGE_DIR / name).read_bytes()
    except OSError:
        return b""


def data_uri(blob: bytes, mime: str) -> str:
    if not blob:
        return ""
    return f"data:{mime};base64,{base64.b64encode(blob).decode('ascii')}"


def image_uri(name: str) -> str:
    return data_uri(image_bytes(name), "image/webp")


def build_cv_pdf() -> bytes:
    """Create a factual fallback CV; production delivery is bound by site_cv_runtime."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(16, 14, 16)
    pdf.add_page()

    def heading(text: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(184, 97, 52)
        pdf.cell(0, 6, text.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(17, 21, 27)

    def body(text: str, bold: bool = False, size: float = 9) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.multi_cell(0, 4.5, text, new_x="LMARGIN", new_y="NEXT")

    def bullet(text: str) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(0, 4.2, f"- {text}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(11, 18, 32)
    pdf.cell(0, 9, "JAIR RIBEIRO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(184, 97, 52)
    pdf.cell(0, 6, "Enterprise AI & Data Leader | Strategy, Governance, Adoption & Business Value", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(70, 76, 84)
    pdf.multi_cell(0, 4.5, "Gothenburg, Sweden | jair.ribeiro@outlook.it | +46 76 761 2158 | linkedin.com/in/jairribeiro", new_x="LMARGIN", new_y="NEXT")

    heading("Executive Profile")
    body("Enterprise AI, data and analytics leader with 20+ years in enterprise technology, including 8+ years in AI, data and analytics leadership. Experience spans AI strategy, operating models, portfolio decisions, governance, analytics, adoption and business translation across automotive, consumer goods and enterprise technology environments.")

    heading("Leadership & Domain Expertise")
    body("AI strategy & enterprise adoption | Responsible AI & AI governance | Data & analytics strategy | Data governance & maturity | GenAI enablement | Portfolio prioritization | Operating models & CoE design | Executive stakeholder management | Change, literacy & capability building | Enterprise architecture | Cloud & technology consulting", size=8.5)

    heading("Selected Leadership Impact")
    bullet("Across Volvo AI roles, shaped and supported 100+ AI initiatives, proofs of concept and projects across global markets and business functions.")
    bullet("Designed AI literacy and adoption activity reaching 1,000+ employees and supported broader communities engaging 1,500+ practitioners.")
    bullet("Connected business, data, governance and technology stakeholders to move opportunities from ambiguity toward feasible, governed and adopted solutions.")
    bullet("Led AI value discovery across commercial operations, manufacturing, supply chain, logistics, sales and marketing contexts.")

    heading("Professional Experience")
    body("AI & Data Center of Excellence Director | MSX International", True)
    body("Dec 2025 - 2026 | Gothenburg, Sweden", size=8)
    bullet("Built foundations for a business-facing AI & Data CoE connecting strategy, governance, adoption and responsible enablement.")
    bullet("Structured the enterprise AI opportunity portfolio, improving visibility, prioritization, decision quality and readiness to scale.")
    bullet("Advanced data governance foundations covering ownership, stewardship, data quality and trusted data practices.")
    bullet("Introduced clearer lifecycle stages, ownership and scale-readiness criteria for AI initiatives.")

    body("Data Analytics and AI Leader | Volvo Group / Volvo Trucks", True)
    body("Aug 2022 - Dec 2025 | Gothenburg, Sweden", size=8)
    bullet("Led AI and analytics adoption across commercial operations, including warranty, sales and aftermarket, translating business needs into practical use cases.")
    bullet("Designed AI literacy and adoption activity reaching 1,000+ employees and promoting responsible, practical GenAI use.")
    bullet("Led cross-functional use-case and proof-of-concept work with business teams, Digital & IT, analytics specialists and technology partners.")
    bullet("Connected use-case discovery, adoption, governance and enterprise delivery realities rather than treating pilot or training volume as the outcome.")

    body("AI Strategist - EMEA | Kimberly-Clark", True)
    body("Jul 2021 - Sep 2022 | Krakow, Poland", size=8)
    bullet("Led AI value discovery and realization across EMEA business units, connecting data-science opportunities with business priorities.")
    bullet("Partnered with supply chain, manufacturing, sales, marketing and logistics teams to shape practical AI initiatives.")

    body("Senior AI Business Expert | Volvo Group", True)
    body("Jun 2018 - Jul 2021 | Wroclaw, Poland", size=8)
    bullet("Co-led AI/ML Center of Excellence activities supporting enterprise adoption, use-case development and community growth.")
    bullet("Engaged 1,500+ practitioners, delivered 100+ learning sessions and shaped or supported 100+ AI initiatives across regions.")

    body("AI, Cloud, IT Consulting & Infrastructure Roles | IBM, Hewlett Packard Enterprise and earlier employers", True)
    body("2004 - 2018 | Italy, Brazil and Poland", size=8)
    bullet("Built a broad technology foundation spanning AI and cloud projects, IBM Watson solution design, virtualization, data centers, enterprise systems and IT delivery.")
    bullet("Worked across consulting, architecture, infrastructure, client engagement and project delivery in multicultural environments.")

    heading("Education & Credentials")
    bullet("MSc, Artificial Intelligence - research focus: Responsible AI adoption in global enterprises.")

    heading("Languages")
    body("Portuguese and Italian - native/bilingual | English - full professional | Spanish - professional | Polish - limited working | Swedish - elementary", size=8.5)

    heading("Recognition & Writing")
    bullet("Thinkers360 Top 50 Global Thought Leaders & Influencers on Emerging Technology (2023).")
    bullet("Keynote speaker, Generative AI Summit 2023, London: Strategies for Scaling Adoption across the Enterprise.")
    bullet("Author on enterprise AI leadership, responsible AI, data readiness, governance, operating models and adoption.")

    return bytes(pdf.output())


HERO_URI = image_uri("jair-hero-executive.webp")
WORKSHOP_URI = image_uri("jair-leadership-workshop.webp")
PANEL_DIALOGUE_URI = image_uri("jair-panel-dialogue.webp")
THINKING_PANEL_URI = image_uri("jair-thinking-panel.webp")
ABOUT_BW_URI = image_uri("jair-about-bw.webp")

# Stable fallback: the optional delivery layer may replace this with a dedicated
# AI-panel image, but importers must always be able to rely on the symbol.
AI_PANEL_URI = WORKSHOP_URI

# Compatibility aliases used by shared components.
PROFILE_URI = HERO_URI
SPEAKING_URI = PANEL_DIALOGUE_URI

CV_BYTES = build_cv_pdf()
CV_URI = data_uri(CV_BYTES, "application/pdf")
