"""Private, authenticated-reader A4 AI Portfolio Renewal Decision Record.

PDF bytes are generated only when the native Streamlit reader dialog has
verified an active member session. No public PDF asset or unauthenticated
download route is created for this worksheet.
"""
from __future__ import annotations

from io import BytesIO
from functools import lru_cache

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SLUG = "would-you-fund-the-same-ai-initiatives-today"
NAVY = colors.HexColor("#071E34")
TEAL = colors.HexColor("#117D94")
COPPER = colors.HexColor("#B4805A")
INK = colors.HexColor("#183248")
MUTED = colors.HexColor("#526B7B")
LINE = colors.HexColor("#D8E2E5")
CREAM = colors.HexColor("#F6F9F9")


@lru_cache(maxsize=1)
def build_decision_record_pdf() -> bytes:
    """Create a single-page, printable A4 PDF with eight AcroForm text fields."""
    out = BytesIO()
    pdf = canvas.Canvas(out, pagesize=A4, pageCompression=1)
    width, height = A4
    pdf.setTitle("AI Portfolio Renewal Decision Record (Fillable)")
    pdf.setAuthor("Jair Ribeiro")

    pdf.setFillColor(NAVY)
    pdf.rect(0, height - 119, width, 119, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#62D3E1"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(35, height - 31, "EXECUTIVE AI PORTFOLIO / DECISION RECORD")
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(35, height - 65, "Would you fund it again?")
    pdf.setFont("Helvetica", 10.5)
    pdf.setFillColor(colors.HexColor("#DFEBF1"))
    pdf.drawString(35, height - 88, "Assess the next commitment, not the effort already spent.")

    form = pdf.acroForm

    def section(y: float, label: str) -> None:
        pdf.setFillColor(COPPER)
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(36, y, label.upper())
        pdf.setStrokeColor(LINE)
        pdf.line(36, y - 7, width - 36, y - 7)

    def field(y: float, label: str, name: str, helper: str = "",
              field_height: int = 28) -> float:
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 8.4)
        pdf.drawString(37, y, label)
        if helper:
            pdf.setFillColor(MUTED)
            pdf.setFont("Helvetica", 7.3)
            pdf.drawRightString(width - 37, y, helper)
        bottom = y - field_height - 7
        form.textfield(
            name=name, tooltip=label, x=37, y=bottom,
            width=width - 74, height=field_height,
            borderStyle="solid", borderColor=colors.HexColor("#CAD9DF"),
            fillColor=CREAM, textColor=INK, forceBorder=True,
            fontName="Helvetica", fontSize=10,
            fieldFlags="multiline" if field_height >= 42 else "",
        )
        return bottom - 15

    y = height - 146
    section(y, "Mandate and options")
    y -= 25
    y = field(y, "Business outcome to improve", "outcome",
              "One outcome / baseline / owner", 29)
    y = field(y, "Incumbent AI initiative and its next requested commitment",
              "incumbent", "Future spend + capacity", 28)
    y = field(y, "Best credible alternative (include process-only option)",
              "alternative", "Same outcome and timeframe", 28)
    section(y + 1, "Pass one / clean-sheet judgment")
    y -= 22
    y = field(y, "What wins on future value, evidence and capacity?",
              "clean_sheet", "Ignore sunk costs and sponsor seniority", 43)
    section(y + 1, "Pass two / restore the real world")
    y -= 22
    y = field(y, "What changes after switching cost, obligations and risk?",
              "real_world", "Include safeguards and continuity", 43)
    section(y + 1, "Executive decision and next gate")
    y -= 22
    y = field(y, "Decision: RENEW / REPLACE / TEST / STOP",
              "decision", "State one choice and why", 30)
    y = field(y, "Business decision owner and Finance / risk input",
              "owner", "Who can release or withdraw capacity?", 30)
    y = field(y, "Proof required and review date",
              "next_gate", "What would reverse the decision?", 43)

    pdf.setStrokeColor(LINE)
    pdf.line(36, 46, width - 36, 46)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(36, 31, "Jair Ribeiro | AI Leader | jairribeiro.com")
    pdf.drawRightString(width - 36, 31, "Fillable executive decision tool")
    pdf.showPage()
    pdf.save()
    data = out.getvalue()
    if not data.startswith(b"%PDF-") or len(data) < 2000:
        raise ValueError("Decision record PDF generation failed.")
    return data


def decision_record_cta_html() -> str:
    """Display only inside the authenticated full Executive Briefing reader."""
    return (
        '<section class="renewal-worksheet-cta" data-analytics-section="briefing-decision-record">'
        '<style>.site .renewal-worksheet-cta{margin:34px 0 38px;padding:25px 28px;'
        'background:#edf3f2;border:1px solid #c8d8dc;border-left:4px solid #b4805a}'
        '.site .renewal-worksheet-cta h3{font:500 28px/1.2 Georgia,serif;'
        'margin:7px 0 10px;color:#102b40}.site .renewal-worksheet-cta p{'
        'font:14px/1.75 Arial,sans-serif;color:#354b5b;max-width:730px}'
        '.site .renewal-worksheet-cta a{display:inline-flex;align-items:center;'
        'justify-content:center;min-height:46px;background:#13354b;'
        'color:#fff!important;text-decoration:none!important;padding:13px 19px;'
        'font:750 12px/1.4 Arial,sans-serif;margin-top:9px}'
        '@media(max-width:650px){.site .renewal-worksheet-cta{padding:19px}'
        '.site .renewal-worksheet-cta a{width:100%}}</style>'
        '<span class="eyebrow">EXECUTIVE DECISION RECORD · MEMBER RESOURCE</span>'
        '<h3>Take the Renewal Challenge into your next meeting.</h3>'
        '<p>A one-page, fillable A4 record for your business outcome, the '
        'incumbent and alternative, the two decision passes, the authorized '
        'choice and the evidence for the next review. Included with your '
        'complimentary verified reader access.</p>'
        '<a href="?page=briefing&amp;article=' + SLUG
        + '&amp;worksheet=1" target="_self" '
        'data-hq-event="briefing_decision_record_open">'
        'Download the fillable A4 decision record</a></section>'
    )
