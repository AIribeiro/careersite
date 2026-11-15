"""Executive-grade, evidence-traceable PDF for AI Investment Decision Advisor.

Page 1 is the decision brief (verdict, executive summary, owners and
completion tests). Page 2 retains the exact user selections and a clearly
labelled, self-reported context note. No LLM or inferred facts are added.
"""
from __future__ import annotations

import re
import unicodedata

from fpdf import FPDF

from page_advisory_investment_logic import MODEL_VERSION, validate


NAVY = (14, 34, 52)
NAVY_2 = (25, 52, 72)
INK = (35, 53, 68)
MUTED = (89, 107, 119)
GOLD = (190, 135, 91)
PAPER = (250, 249, 246)
WHITE = (255, 255, 255)
LINE = (220, 225, 228)
PALE = (241, 245, 247)
LIGHT_GOLD = (249, 241, 232)


def _ascii(value: object) -> str:
    original = " ".join(str(value if value is not None else "").split())
    original = original.replace("\u2014", " - ").replace("\u2013", "-")
    original = original.replace("\u2018", "'").replace("\u2019", "'")
    original = original.replace("\u201c", '"').replace("\u201d", '"')
    return unicodedata.normalize("NFKD", original).encode("ascii", "replace").decode("ascii")


def _wrap(pdf: FPDF, text: str, width: float, size: float, style: str = "",
          max_lines: int | None = None) -> list[str]:
    pdf.set_font("Helvetica", style, size)
    words = _ascii(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if current and pdf.get_string_width(trial) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    if not lines:
        lines = [""]
    if max_lines is not None and len(lines) > max_lines:
        limited = lines[:max_lines]
        last = limited[-1]
        while last and pdf.get_string_width(last + "...") > width:
            last = last[:-1].rstrip()
        limited[-1] = last + "..."
        return limited
    return lines


def _txt(pdf: FPDF, x: float, baseline: float, text: str,
         size: float = 9, color: tuple = INK, style: str = "") -> None:
    pdf.set_font("Helvetica", style, size)
    pdf.set_text_color(*color)
    pdf.text(x, baseline, _ascii(text))


def _lines(pdf: FPDF, x: float, baseline: float, text: str, width: float,
           size: float = 9, color: tuple = INK, style: str = "",
           leading: float = 5, max_lines: int | None = None) -> int:
    rows = _wrap(pdf, text, width, size, style, max_lines)
    for i, row in enumerate(rows):
        _txt(pdf, x, baseline + leading * i, row, size, color, style)
    return len(rows)


def _band(pdf: FPDF, x: float, y: float, w: float, h: float,
          fill: tuple, radius: float = 0) -> None:
    pdf.set_fill_color(*fill)
    if radius:
        pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=radius)
    else:
        pdf.rect(x, y, w, h, style="F")


def _heading(pdf: FPDF, label: str, page: int) -> None:
    _band(pdf, 0, 0, 210, 51, NAVY)
    _band(pdf, 18, 14, 1, 23, GOLD)
    _txt(pdf, 24, 19, "JAIR RIBEIRO  /  EXECUTIVE AI ADVISORY", 9, (224, 195, 168), "B")
    _txt(pdf, 24, 31, label, 22, WHITE, "B")
    _txt(pdf, 24, 41, "INDEPENDENT DECISION SUPPORT  |  SINGLE AI OPPORTUNITY",
         8, (199, 212, 221))
    _footer(pdf, page)


def _footer(pdf: FPDF, page: int) -> None:
    pdf.set_draw_color(*LINE)
    pdf.line(18, 282, 192, 282)
    _txt(pdf, 18, 287, "Jair Ribeiro  /  Executive AI Advisory", 7.3, MUTED)
    _txt(pdf, 125, 287, "Self-reported assessment  |  " + str(page) + " / 2",
         7.3, MUTED)


def _executive_summary(data: dict, result: dict) -> str:
    """One accountable position, supporting evidence and reasons not to scale."""
    a = data["choices"]
    direction = {
        "INVEST": "Advance to formal investment review, not automatic deployment.",
        "EXPERIMENT": "Continue a bounded, monitored experiment; withhold wider rollout.",
        "HOLD": "Defer new commitment until the missing prerequisites are resolved.",
        "STOP": "Reject this design; reconsider only if the underlying case changes.",
    }[result["verdict"]]

    proof: list[str] = []
    if a["non_ai"] == "Compared; AI has a documented advantage":
        proof.append("a reported advantage against the non-AI alternative")
    if a["feasibility"] == "Demonstrated in relevant setting":
        proof.append("demonstrated feasibility in a relevant setting")
    if a["owner"] == "Named accountable business owner":
        proof.append("identified business accountability")
    if proof:
        positive = "The submitted case cites " + " and ".join(proof[:2]) + ". "
    else:
        positive = "The current evidence does not yet establish a defensible investment case. "

    gaps: list[str] = []
    if a["value"] != "Measured against a baseline" or a["baseline"] != "Verified baseline":
        gaps.append("verified financial or operational benefit")
    if a["data"] != "Access, ownership and quality verified":
        gaps.append("data readiness")
    if a["control"] != "Controls tested and recorded":
        gaps.append("control sign-off")
    if a["capacity"] != "People and budget explicitly available":
        gaps.append("committed capacity")
    if a["legal"] != "Applicable obligations reviewed":
        gaps.append("specialist legal review")
    if a["owner"] != "Named accountable business owner":
        gaps.append("decision ownership")
    if gaps:
        constraints = "Outstanding: " + ", ".join(gaps[:3]) + ". "
    else:
        constraints = "No unresolved condition was reported in these selections. "
    return direction + " " + positive + constraints + "Complete the action gates below."


def _compact_state(choices: dict) -> tuple[str, str, str]:
    value = {
        "Measured against a baseline": "Measured benefit",
        "Quantified estimate only": "Benefit estimated",
        "Unquantified expectation": "Value unquantified",
        "No credible benefit": "Value not established",
    }[choices["value"]]
    controls = {
        "Controls tested and recorded": "Controls tested",
        "Control review pending": "Review pending",
        "Controls absent or ineffective": "Controls missing",
    }[choices["control"]]
    return value, controls, choices["stage"]


def _priority_card(pdf: FPDF, y: float, number: int, action: dict) -> None:
    _band(pdf, 18, y, 174, 29, PALE, 2)
    _band(pdf, 18, y, 1.2, 29, GOLD)
    _txt(pdf, 23, y + 9, f"{number:02d}", 14, NAVY, "B")
    _lines(pdf, 39, y + 8, action["text"], 146, 9.1, INK, "B",
           leading=4.7, max_lines=2)
    _txt(pdf, 39, y + 19, "OWNER", 7.1, GOLD, "B")
    _lines(pdf, 56, y + 19, action["owner"], 129, 7.7, MUTED,
           max_lines=1)
    _txt(pdf, 39, y + 25, "PROOF", 7.1, GOLD, "B")
    _lines(pdf, 56, y + 25, action["trigger"], 129, 7.7, MUTED,
           max_lines=1)


def _group(pdf: FPDF, y: float, heading: str,
           rows: list[tuple[str, str]]) -> float:
    _band(pdf, 18, y, 174, 8, NAVY_2)
    _txt(pdf, 22, y + 5.7, heading.upper(), 8.3, WHITE, "B")
    y += 8
    for i, (label, value) in enumerate(rows):
        _band(pdf, 18, y, 174, 7.3, PALE if i % 2 == 0 else WHITE)
        _txt(pdf, 22, y + 5.0, label, 8.0, INK, "B")
        _lines(pdf, 89, y + 5.0, value, 98, 7.8, MUTED, max_lines=1)
        y += 7.3
    return y + 3


def _page_two(pdf: FPDF, data: dict, result: dict, created_at: str) -> None:
    pdf.add_page()
    _heading(pdf, "Evidence & decision conditions", 2)
    _txt(pdf, 18, 62, "ASSESSMENT RECORD", 8, GOLD, "B")
    _lines(pdf, 18, 70, data["name"], 174, 14, NAVY, "B", max_lines=2, leading=6)
    _txt(pdf, 18, 84, "Completed " + _ascii(created_at[:10]) +
         "   |   Model " + MODEL_VERSION + "   |   Confidence: " +
         result["confidence"], 8, MUTED)
    a = data["choices"]
    y = 91
    y = _group(pdf, y, "01  Business case", [
        ("Intended outcome", a["objective"]),
        ("Opportunity stage", a["stage"]),
        ("AI authority", a["autonomy"]),
        ("Non-AI alternative", a["non_ai"]),
        ("Business benefit", a["value"]),
        ("Current baseline", a["baseline"]),
    ])
    y = _group(pdf, y, "02  Delivery readiness", [
        ("Data readiness", a["data"]),
        ("Feasibility", a["feasibility"]),
        ("Capacity", a["capacity"]),
        ("Business ownership", a["owner"]),
        ("Adoption approach", a["adoption"]),
    ])
    y = _group(pdf, y, "03  Governance and authority", [
        ("Control status", a["control"]),
        ("Business consequence", a["exposure"]),
        ("Regulatory review", a["legal"]),
    ])
    # The original free-text note is retained as declared context, never
    # treated as independently verified evidence or used to change the verdict.
    note = data.get("context") or ""
    if note:
        _band(pdf, 18, y + 2, 174, max(21, 269 - y), LIGHT_GOLD, 2)
        _txt(pdf, 22, y + 9, "CONTEXT SUPPLIED BY THE RESPONDENT", 8.1, GOLD, "B")
        _lines(pdf, 22, y + 16, note, 164, 8.0, INK, leading=4.2,
               max_lines=max(1, min(8, int((269 - y - 17) // 4.2))))
    else:
        _band(pdf, 18, y + 2, 174, 19, LIGHT_GOLD, 2)
        _txt(pdf, 22, y + 10, "No additional context was supplied.", 8.4, MUTED)
    _txt(pdf, 18, 278, "Inputs and context are self-reported. The verdict uses selections only.",
         7.1, MUTED)


def generate_decision_pdf(data: dict, result: dict, created_at: str) -> bytes:
    """Return a two-page decision brief with stable page geometry."""
    data = validate(data)
    if result.get("verdict") not in {"INVEST", "EXPERIMENT", "HOLD", "STOP"}:
        raise ValueError("Invalid executive decision.")
    actions = result.get("actions") or []
    if len(actions) != 3 or any(not all(k in a for k in ("text", "owner", "trigger")) for a in actions):
        raise ValueError("An executive report requires three accountable priority actions.")
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.set_margins(18, 16, 18)
    pdf.set_title("Executive AI Investment Decision - " + _ascii(data["name"]))
    pdf.set_author("Jair Ribeiro - Executive AI Advisory")
    pdf.add_page()
    _heading(pdf, "AI Investment Decision", 1)
    _txt(pdf, 18, 61, "DECISION BRIEF", 8, GOLD, "B")
    _lines(pdf, 18, 70, data["name"], 174, 12, INK, "B", max_lines=1, leading=6)

    # Decision verdict is the focal element, followed by its limits.
    _band(pdf, 18, 78, 174, 46, NAVY_2, 2)
    _band(pdf, 18, 78, 1.4, 46, GOLD)
    _txt(pdf, 24, 88, "RECOMMENDED POSITION", 8.3, (229, 192, 157), "B")
    _txt(pdf, 24, 106, result["verdict"], 28, WHITE, "B")
    _lines(pdf, 24, 116, result["headline"], 162, 10, (222, 232, 238),
           max_lines=1)
    value, control, stage = _compact_state(data["choices"])
    _txt(pdf, 18, 133, "EXECUTIVE SUMMARY", 9.0, GOLD, "B")
    _txt(pdf, 116, 133, "CONFIDENCE: " + result["confidence"].upper(),
         7.1, MUTED, "B")
    _lines(pdf, 18, 142, _executive_summary(data, result), 174, 9.3,
           INK, leading=5.4, max_lines=4)
    _band(pdf, 18, 162, 174, 11.5, LIGHT_GOLD, 1)
    _txt(pdf, 22, 169, "STAGE  " + stage.upper(), 7.5, INK, "B")
    _txt(pdf, 74, 169, "VALUE  " + value.upper(), 7.5, INK, "B")
    _txt(pdf, 139, 169, "CONTROLS  " + control.upper(), 7.1, INK, "B")

    _txt(pdf, 18, 180, "THREE PRIORITY ACTIONS", 9, GOLD, "B")
    for i, action in enumerate(actions, 1):
        _priority_card(pdf, 184 + (i - 1) * 30.5, i, action)

    # Page two provides traceability rather than diluting the first page.
    _page_two(pdf, data, result, created_at)
    return bytes(pdf.output())
