"""Two-page executive leadership workshop PDF; all data from user-selected inputs."""
from __future__ import annotations

from datetime import datetime
from fpdf import FPDF

from page_advisory_leadership_logic import DIMENSIONS, assess, clean_exercises, EXERCISES

NAVY = (15, 35, 55)
INK = (36, 52, 69)
MUTED = (92, 107, 122)
COPPER = (176, 116, 77)
PALE = (246, 244, 239)
RULE = (215, 221, 226)


def _ascii(value: object, limit: int = 500) -> str:
    return str(value or "")[:limit].replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'").replace("\u2022", "-").encode("latin-1", errors="replace").decode("latin-1")


def _write(pdf: FPDF, text: object, *, size: int = 9, bold: bool = False,
           color=INK, line: float = 5, width: float = 176) -> None:
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.set_text_color(*color)
    pdf.multi_cell(width, line, _ascii(text), border=0, align="L")


def _section(pdf: FPDF, heading: str) -> None:
    pdf.ln(3)
    _write(pdf, heading.upper(), size=9, bold=True, color=COPPER, line=7)


def _header(pdf: FPDF, page: int) -> None:
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 31, style="F")
    pdf.set_xy(17, 10)
    _write(pdf, "EXECUTIVE AI LEADERSHIP WORKSHOP", size=12, bold=True,
           color=(255, 255, 255), line=6)
    pdf.set_xy(17, 22)
    _write(pdf, "JAIR RIBEIRO  /  EXECUTIVE DECISION BRIEF", size=7,
           color=(222, 230, 237), line=4)
    pdf.set_xy(17, 275)
    pdf.set_draw_color(*RULE)
    pdf.line(17, 273, 193, 273)
    _write(pdf, f"Self-reported evidence | No independent audit or authorization | Page {page} of 2",
           size=7, color=MUTED, line=4)
    pdf.set_xy(17, 37)


def render_leadership_pdf(workshop: dict, raw: dict,
                          exercises: dict | None = None,
                          team: dict | None = None) -> bytes:
    report = assess(raw)
    exercises = clean_exercises(exercises or {})
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_margins(17, 17, 17)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    _header(pdf, 1)
    _write(pdf, workshop.get("title", "Leadership workshop"), size=17, bold=True,
           color=NAVY, line=8)
    context = workshop.get("context") or {}
    _write(pdf, " / ".join(_ascii(context.get(k), 50) for k in ("stage", "scope", "priority")
                            if context.get(k)), size=8, color=MUTED, line=5)
    pdf.ln(5)
    pdf.set_fill_color(*PALE)
    pdf.rect(17, pdf.get_y(), 176, 37, style="F")
    pdf.set_x(22)
    _write(pdf, "LEADERSHIP ASSESSMENT", size=8, bold=True, color=COPPER)
    pdf.set_x(22)
    _write(pdf, report["label"], size=14, bold=True, color=NAVY, line=7, width=163)
    pdf.set_x(22)
    _write(pdf, report["reason"], size=8, width=163, line=4.5)
    pdf.set_y(max(113, pdf.get_y() + 7))
    _section(pdf, "Evidence and decision boundary")
    summary = (f"{report['answered']} of 21 questions answered; {report['coverage']}% coverage. "
               f"Weighted index: {report['overall'] if report['overall'] is not None else 'not issued'}."
               " Neither the index nor the recommendations approve deployment or spending.")
    _write(pdf, summary, size=8, line=4.7)
    if report["critical_gates"]:
        _write(pdf, "Critical conditions: " + "; ".join(report["critical_gates"]),
               size=8, bold=True, line=4.7)
    _section(pdf, "Seven-dimension leadership profile")
    for key, title, weight, questions in DIMENSIONS:
        score = report["scores"].get(key)
        line = f"{title:<31}  {str(score) + '%' if score is not None else 'Not assessed':>10}"
        _write(pdf, line, size=9, line=7, width=176)
    _section(pdf, "Interpretation")
    _write(pdf, report["confidence"] + ". Ratings describe reported practice, not verified maturity.",
           size=8, color=MUTED, line=4.7)

    pdf.add_page()
    _header(pdf, 2)
    _write(pdf, "Leadership decisions and actions", size=17, bold=True, color=NAVY, line=9)
    _write(pdf, "Proposed accountable functions and review conditions are not commitments until accepted.",
           size=8, color=MUTED, line=5)
    for i, action in enumerate(report["actions"], 1):
        _section(pdf, f"Priority {i:02d} / {action['dimension'].replace('_',' ')}")
        _write(pdf, action["action"], size=10, bold=True, color=NAVY, line=5.5)
        _write(pdf, "Proposed owner: " + action["owner"], size=8, line=5)
        _write(pdf, "Evidence to require: " + action["evidence"], size=8, line=5)
        _write(pdf, "Review: " + action["review"], size=8, color=MUTED, line=5)
    _section(pdf, "Leadership discussion exercise")
    for code in list(exercises)[:2]:
        item = EXERCISES[code]
        chosen = item["choices"][exercises[code]]
        _write(pdf, item["title"], size=9, bold=True, line=5)
        _write(pdf, "Selected: " + chosen, size=8, line=5)
        _write(pdf, "Trade-off: " + item["tradeoff"], size=8, color=MUTED, line=5)
    decisions = workshop.get("decisions") or []
    if decisions:
        _section(pdf, "Recorded leadership decisions")
        for d in decisions[:3]:
            if not isinstance(d, dict):
                continue
            _write(pdf, "- " + str(d.get("decision") or "")[:140], size=8, line=5)
            _write(pdf, "Owner: " + str(d.get("owner") or "Not assigned") +
                   " | Review: " + str(d.get("review") or "Not agreed"),
                   size=7, color=MUTED, line=4)
    if team and team.get("available"):
        _section(pdf, "Team participation")
        _write(pdf, f"{team['count']} explicitly shared participant responses were considered. "
               "Differences in a small leadership group may remain identifiable.",
               size=8, line=5)
    pdf.set_y(253)
    pdf.set_draw_color(*RULE)
    pdf.line(17, 252, 193, 252)
    _write(pdf, "Next gate: Verify evidence, confirm responsible owners and obtain the relevant "
           "business, risk and legal approvals. Model: " + report["model_version"],
           size=7, color=MUTED, line=4)
    if len(pdf.pages) != 2:
        raise RuntimeError("The leadership report must have two pages.")
    return bytes(pdf.output())
