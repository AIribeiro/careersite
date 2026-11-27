from __future__ import annotations

"""Build single-column recruitment CVs from the same reviewed career source."""
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from site_cv import build_public_cv, LINKEDIN_URL, CERTIFICATIONS_URL, PRESENCE_URL

ATS_DOCX = "Jair_Ribeiro_CV_ATS.docx"
ATS_PDF = "Jair_Ribeiro_CV_ATS.pdf"

def dates(value):
    return " - ".join(datetime.strptime(x.strip(), "%b %Y").strftime("%B %Y") for x in value.split(" - "))

def paragraphs():
    records = []
    build_public_cv(records)
    result = [
        ("name", "Jair Ribeiro"),
        ("title", "Enterprise AI & Data Leader"),
        ("normal", "Strategy, Operating Models, Governance, Adoption, Business Value"),
        ("normal", "Gothenburg, Sweden | jair@jairribeiro.com | +46 76 761 21 58"),
        ("normal", "Sweden / Nordic scope | Open to immediate collaboration and relevant mandates"),
        ("normal", "LinkedIn: " + LINKEDIN_URL),
        ("normal", "Portfolio: https://jairribeiro.com/"),
    ]
    def add(kind, value):
        result.append((kind, value))
    section = ""
    seen = set()
    for rec in records:
        kind, *v = rec
        if kind == "section":
            section = v[0]
            label = {"Professional Experience": "Work Experience", "Earlier Career": "Work Experience",
                     "Publications & Recognition": "Publications and Recognition"}.get(section, section)
            if label not in seen:
                add("section", label)
                seen.add(label)
        elif kind in ("role", "earlier"):
            title, company, period = v[:3]
            add("role", title.replace(" | ", "; ").replace(" / ", "; "))
            add("meta", company.replace("Volvo Group / Volvo Trucks", "Volvo Group (Volvo Trucks)"))
            add("meta", dates(period))
            if kind == "role":
                location, bullets, context, mandate = v[3:]
                add("meta", location.replace("Göteborg", "Gothenburg"))
                if context or mandate:
                    add("normal", " ".join(x for x in (context, "Mandate: " + mandate if mandate else None) if x))
                for bullet in bullets:
                    add("bullet", bullet)
            elif company == "Hewlett Packard Enterprise":
                add("meta", "Milano, Italy")
        elif kind == "body":
            value = v[0]
            if section == "Education":
                if value.startswith("Selinus University"):
                    school, degree, period = value.split(" | ", 2)
                    add("role", degree.replace("), ", ") in "))
                    add("meta", school)
                    add("meta", dates(period))
                elif value.startswith("Massachusetts Institute"):
                    if "Professional Development and Certifications" not in seen:
                        add("section", "Professional Development and Certifications")
                        seen.add("Professional Development and Certifications")
                    school, course = value.split(" | ", 1)
                    add("role", course)
                    add("meta", school)
                elif value.startswith("Selected credentials: "):
                    for item in value.removeprefix("Selected credentials: ").split(" | "):
                        add("normal", item)
                    add("normal", "Additional credentials: " + CERTIFICATIONS_URL)
                else:
                    add("normal", value)
            elif section == "Languages":
                levels = {"Native": "Native", "C2": "Proficient (CEFR C2)", "B2": "Upper intermediate (CEFR B2)",
                          "B1": "Intermediate (CEFR B1)", "A2": "Elementary (CEFR A2)"}
                for item in value.split(" | "):
                    language, level = item.rsplit(" ", 1)
                    add("normal", language + " - " + levels.get(level, level))
            else:
                add("normal", value.replace(" | ", "; " if section == "Core Competencies" else " - "))
    add("normal", "Speaking and thought leadership: " + PRESENCE_URL)
    return result

def build_ats_docx(path):
    doc = Document()
    doc.core_properties.title = "Jair Ribeiro - Enterprise AI & Data Leader"
    doc.core_properties.author = "Jair Ribeiro"
    sec = doc.sections[0]
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    sec.top_margin = sec.bottom_margin = Inches(.65)
    sec.left_margin = sec.right_margin = Inches(.72)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor.from_string("20262E")
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.line_spacing = 1.06
    heading = doc.styles["Heading 1"]
    heading.font.name = "Arial"
    heading.font.size = Pt(12)
    heading.font.bold = True
    heading.font.color.rgb = RGBColor.from_string("183B50")
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(4)
    for kind, value in paragraphs():
        if kind == "section":
            doc.add_heading(value, level=1)
            continue
        p = doc.add_paragraph(style="List Bullet" if kind == "bullet" else "Normal")
        run = p.add_run(value)
        if kind in ("name", "title", "role"):
            run.bold = True
            run.font.size = Pt({"name": 21, "title": 13, "role": 10.5}[kind])
            p.paragraph_format.keep_with_next = True
            if kind == "role":
                p.paragraph_format.space_before = Pt(6)
        if kind == "meta":
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.keep_with_next = True
    doc.save(path)
    return path

if __name__ == "__main__":
    build_ats_docx(Path("static") / ATS_DOCX)
