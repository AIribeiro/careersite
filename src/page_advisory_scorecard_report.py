"""Executive decision memo exported from a live, approved Scorecard workspace.

PDF content is derived only from the client's current Scorecard inputs and
the deterministic recommendation. No external facts or fake approvals are
introduced. No report is persisted or exposed outside authenticated Advisory.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
import unicodedata

from fpdf import FPDF


NAVY = (15, 34, 54)
TEAL = (18, 106, 116)
WARM = (192, 131, 95)
INK = (37, 54, 72)
MUTED = (95, 111, 127)
PALE = (236, 243, 245)


def _clean(text: Any) -> str:
    value = str(text if text is not None else "")
    for a, b in (
        ("\u2014", " - "), ("\u2013", "-"), ("\u2018", "'"),
        ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'),
        ("\u2022", "-"), ("\u2192", "->"), ("\u00a0", " "),
    ):
        value = value.replace(a, b)
    return unicodedata.normalize("NFKD", value).encode("latin-1", errors="replace").decode("latin-1")


def _money(value: float) -> str:
    return f"{value:,.0f} SEK"


class _DecisionPDF(FPDF):
    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 31, "F")
        self.set_xy(17, 9)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 7, "JAIR RIBEIRO | EXECUTIVE AI ADVISORY")
        self.set_xy(17, 19)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(210, 224, 234)
        self.cell(0, 5, "AI PORTFOLIO PRIORITIZATION SCORECARD  /  DECISION MEMO")
        self.set_y(38)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(220, 227, 230)
        self.line(17, self.y, 193, self.y)
        self.set_y(-12)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 5, "Decision support only  |  Not authorization to spend, deploy or process protected data")
        self.set_x(-27)
        self.cell(10, 5, str(self.page_no()), align="R")


def _heading(pdf: FPDF, title: str):
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 7, _clean(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _text(pdf: FPDF, message: str, *, strong: bool = False, size: float = 9,
          color: tuple[int, int, int] = INK, indent: int = 0):
    pdf.set_font("Helvetica", "B" if strong else "", size)
    pdf.set_text_color(*color)
    pdf.set_x(17 + indent)
    pdf.multi_cell(176 - indent, 5.2, _clean(message),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.7)


def _item(pdf: FPDF, item: dict):
    if pdf.get_y() > 252:
        pdf.add_page()
    name = str(item.get("name") or "")
    score = item.get("score")
    label = f"{name}  /  Score {score if score is not None else 'N/A'}/100"
    _text(pdf, label, strong=True, size=9.5)
    _text(pdf, item.get("rationale") or "", size=8.7, indent=3)
    _text(pdf, "Next: " + str(item.get("next_action") or ""),
          size=8.7, color=TEAL, indent=3)


def build_executive_pdf(decision: dict) -> bytes:
    pdf = _DecisionPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=19)
    pdf.set_margins(17, 38, 17)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 10, "Executive Portfolio Decision", new_x="LMARGIN", new_y="NEXT")
    _text(pdf, "Prepared " + str(decision.get("generated_at") or "") +
          "   |   Source revision " + str(decision.get("revision") if decision.get("revision") is not None else "not supplied"),
          size=8, color=MUTED)
    if any("DEMONSTRATION" in str(x) for x in decision.get("caveats") or []):
        pdf.set_fill_color(252, 242, 229)
        pdf.set_text_color(103, 62, 38)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 7, "DEMONSTRATION REPORT - Fictional input data; not an actual investment recommendation",
                       border=0, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
    _heading(pdf, "Decision in brief")
    _text(pdf, decision.get("verdict") or "No decision available", strong=True, size=10.5)
    rec = decision["recommended"]
    cur = decision["current_selection"]
    low = decision["conservative"]
    _text(pdf, (
        f"Recommended portfolio: {rec['count']} initiatives; "
        f"{rec['fte_months']:.1f} FTE-months of "
        f"{float(decision['settings']['capacity_fte_months']):.1f} available; "
        f"{_money(rec['investment_sek'])} of "
        f"{_money(float(decision['settings']['budget_sek']))} planning budget."
    ))
    _text(pdf, (
        f"Current client selection: {cur['count']} initiatives, "
        f"{cur['fte_months']:.1f} FTE-months, {_money(cur['investment_sek'])}; "
        + ("within limits" if cur["fits"] else "EXCEEDS planning limits") + "."
    ))
    _heading(pdf, "Recommended actions")
    for title, status in (
        ("Advance to business-case review", "Advance to business case"),
        ("Evidence-building tests", "Time-boxed test"),
        ("Hold for control review", "Hold - control review"),
        ("Stop or redesign", "Stop / redesign"),
    ):
        entries = decision["categories"].get(status, [])
        if entries:
            _text(pdf, title + f"  ({len(entries)})", strong=True, color=TEAL)
            for item in entries:
                _item(pdf, item)
    _heading(pdf, "Alternatives and planning trade-offs")
    _text(pdf, (
        f"Recommended: {rec['count']} initiatives, {rec['fte_months']:.1f} FTE-months, "
        f"{_money(rec['investment_sek'])}; "
        f"estimated annual net benefit {_money(rec['annual_net_sek'])}."
    ))
    _text(pdf, (
        f"Lower-commitment option (business cases only): {low['count']} initiatives, "
        f"{low['fte_months']:.1f} FTE-months, {_money(low['investment_sek'])}; "
        f"leaves {low['fte_headroom']:.1f} FTE-months and "
        f"{_money(low['budget_headroom'])} unallocated."
    ))
    _text(pdf, (
        f"Client's current selection: {cur['count']} initiatives, "
        f"{cur['fte_months']:.1f} FTE-months, {_money(cur['investment_sek'])}; "
        + ("fits" if cur["fits"] else "does not fit") + " current limits."
    ))
    changes = decision.get("changes") or {}
    if changes.get("added"):
        _text(pdf, "Include versus current selection: " + "; ".join(changes["added"]), size=8.5)
    if changes.get("removed"):
        _text(pdf, "Remove / defer versus current selection: " + "; ".join(changes["removed"]), size=8.5)

    _heading(pdf, "Items requiring further proof or later consideration")
    for status in ("Defer - constrained", "Queue for a test", "Validate evidence",
                   "Complete assessment", "Defer / stop"):
        rows = decision["categories"].get(status, [])
        if rows:
            _text(pdf, status + f"  ({len(rows)})", strong=True, size=9.3)
            for item in rows:
                _item(pdf, item)

    _heading(pdf, "Conditions and executive sign-off")
    caveats = decision.get("caveats") or []
    for item in caveats:
        _text(pdf, "- " + str(item), size=8.7)
    _text(pdf, (
        "The selected work is a proposal for business-case review or scoped tests, "
        "not an authorization to fund or deploy. Accountable sponsors must "
        "validate source evidence, data rights, risk controls and capacity commitments. "
        "Financial benefits are estimates supplied by the user; no independent audit "
        "or discounted cash-flow analysis has been performed."
    ), size=8.7)
    _text(pdf, (
        "Decision method: seven configurable weighted criteria; control and "
        "evidence gates precede selection; first choose business-case candidates "
        "within both resource limits, then a bounded number of evidence-building "
        "tests with remaining resources. Selection method: "
        + str(decision.get("selection_method") or "not known") + "."
    ), size=8.5, color=MUTED)
    _text(pdf, "Source: private client Scorecard inputs, not external research.", size=8, color=MUTED)
    return bytes(pdf.output())
