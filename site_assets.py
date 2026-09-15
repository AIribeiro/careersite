from __future__ import annotations

from pathlib import Path
import base64
import io
import zipfile

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent
LINKEDIN = "https://www.linkedin.com/in/jairribeiro"
MEDIUM = "https://jairribeiro.medium.com"
EMAIL = "jair.ribeiro@outlook.it"


def load_media() -> dict[str, bytes]:
    """Reuse repository media without executing the legacy embedded application."""
    media: dict[str, bytes] = {}
    parts = sorted((ROOT / "payload_parts").glob("part_*.b64"))
    if parts:
        try:
            encoded = "".join(p.read_text(encoding="ascii") for p in parts)
            with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
                for name in bundle.namelist():
                    if name.startswith("assets/") and not name.endswith("/"):
                        media[Path(name).name] = bundle.read(name)
        except (ValueError, zipfile.BadZipFile, OSError):
            pass

    hq = ROOT / "hq_media.zip"
    if hq.exists():
        try:
            with zipfile.ZipFile(hq) as bundle:
                for name in bundle.namelist():
                    if not name.endswith("/"):
                        media[Path(name).name] = bundle.read(name)
        except (zipfile.BadZipFile, OSError):
            pass

    panel_parts = sorted((ROOT / "asset_parts").glob("panel.webp.part*.b64"))
    if panel_parts:
        try:
            panel = "".join(p.read_text(encoding="ascii") for p in panel_parts)
            media["panel.webp"] = base64.b64decode(panel)
        except (ValueError, OSError):
            pass
    return media


def data_uri(blob: bytes, mime: str) -> str:
    if not blob:
        return ""
    return f"data:{mime};base64,{base64.b64encode(blob).decode('ascii')}"


def build_cv_pdf() -> bytes:
    """Create the canonical public CV from the same factual source used by the site."""
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
    pdf.cell(0, 6, "AI, Data & Analytics Director | Governance, Adoption & Business Value", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(70, 76, 84)
    pdf.multi_cell(0, 4.5, "Gothenburg, Sweden | jair.ribeiro@outlook.it | +46 76 761 2158 | linkedin.com/in/jairribeiro", new_x="LMARGIN", new_y="NEXT")

    heading("Executive Profile")
    body("Enterprise AI, data and analytics leader with 15+ years across business strategy, governance, adoption, architecture and technology delivery. Experienced in building capability models, shaping AI and analytics portfolios, improving data trust and translating complex opportunities into governed, practical outcomes. International leadership experience across Sweden, Poland, Italy and Brazil, including automotive, consumer goods and enterprise technology environments.")

    heading("Leadership & Domain Expertise")
    body("AI strategy & enterprise adoption | Responsible AI & AI governance | Data & analytics strategy | Data governance & maturity | GenAI and agentic AI enablement | Portfolio prioritization | Operating models & CoE design | Executive stakeholder management | Change, literacy & capability building | Enterprise architecture | Cloud & technology consulting", size=8.5)

    heading("Selected Leadership Impact")
    bullet("Managed and shaped portfolios covering 100+ AI initiatives and proofs of concept across global markets and business functions.")
    bullet("Designed AI literacy and adoption programs reaching 1,000+ employees and supported communities involving 1,500+ practitioners.")
    bullet("Connected business, data, governance and technology stakeholders to move opportunities from ambiguity toward feasible, governed and adopted solutions.")
    bullet("Led AI value discovery across commercial operations, manufacturing, supply chain, logistics, sales and marketing contexts.")

    heading("Professional Experience")
    body("AI & Data Center of Excellence Director | MSX International", True)
    body("Dec 2025 - Jun 2026 | Gothenburg, Sweden", size=8)
    bullet("Established the foundations of a business-facing AI & Data CoE connecting strategy, governance, adoption and responsible enablement.")
    bullet("Structured the enterprise AI opportunity portfolio, improving visibility, prioritization, decision quality and readiness to scale.")
    bullet("Advanced data governance foundations covering ownership, stewardship, data quality and trusted data practices.")
    bullet("Introduced clearer lifecycle stages, ownership and scale-readiness criteria for AI initiatives.")

    body("Data Analytics and AI Leader | Volvo Group / Volvo Trucks", True)
    body("Aug 2022 - Dec 2025 | Gothenburg, Sweden", size=8)
    bullet("Led AI and analytics adoption across commercial operations, including warranty, sales and aftermarket, translating business needs into practical use cases.")
    bullet("Designed AI literacy and adoption programs reaching 1,000+ employees and promoting responsible, practical GenAI use.")
    bullet("Managed a portfolio of 100+ AI initiatives and proofs of concept across global markets and business functions.")
    bullet("Built cross-functional collaboration among business teams, Digital & IT, analytics specialists and external technology partners.")

    body("AI Strategist - EMEA | Kimberly-Clark", True)
    body("Jul 2021 - Sep 2022 | Krakow, Poland", size=8)
    bullet("Led AI value discovery and realization across EMEA business units, connecting data-science opportunities with business priorities.")
    bullet("Partnered with supply chain, manufacturing, sales, marketing and logistics teams to shape practical AI initiatives.")

    body("Senior AI Business Expert | Volvo Group", True)
    body("Jun 2018 - Jul 2021 | Wroclaw, Poland", size=8)
    bullet("Co-led AI/ML Center of Excellence activities supporting enterprise adoption, use-case development and community growth.")
    bullet("Engaged 1,500+ practitioners, delivered 100+ learning sessions and supported 100+ AI initiatives across regions.")

    body("AI, Cloud, IT Consulting & Infrastructure Roles | IBM, Hewlett Packard Enterprise and earlier employers", True)
    body("2004 - 2018 | Italy, Brazil and Poland", size=8)
    bullet("Built a broad technology foundation spanning AI and cloud projects, IBM Watson solution design, virtualization, data centers, enterprise systems and IT delivery.")
    bullet("Worked across consulting, architecture, infrastructure, client engagement and project delivery in multicultural environments.")

    heading("Education & Credentials")
    bullet("MSc, Artificial Intelligence - research focus: Responsible AI adoption in global enterprises.")
    bullet("MIT MicroMasters coursework - Statistics and Data Science.")
    bullet("MIT - Minds and Machines: Philosophy and Ethics.")

    heading("Languages")
    body("Portuguese and Italian - native/bilingual | English - full professional | Spanish - professional | Polish - limited working | Swedish - elementary", size=8.5)

    heading("Professional Recognition & Thought Leadership")
    bullet("Thinkers360 Top 50 Global Thought Leaders & Influencers on Emerging Technology (2023).")
    bullet("Keynote speaker, Generative AI Summit 2023, London: Strategies for Scaling Adoption across the Enterprise.")
    bullet("Author on enterprise AI leadership, responsible AI, data readiness, governance, operating models and adoption.")

    return bytes(pdf.output())


MEDIA = load_media()
PROFILE_BYTES = MEDIA.get("site-icon.png", b"")
SPEAKING_BYTES = MEDIA.get("panel.webp", MEDIA.get("impact19-header.png", b""))
PROFILE_URI = data_uri(PROFILE_BYTES, "image/png")
SPEAKING_URI = data_uri(SPEAKING_BYTES, "image/webp" if "panel.webp" in MEDIA else "image/png")
CV_BYTES = build_cv_pdf()
CV_URI = data_uri(CV_BYTES, "application/pdf")
