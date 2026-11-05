from __future__ import annotations

"""Original twenty-decision operating-mandate infographic for Executive AI Briefings.

Four parallel obligations, each with five executive decisions. All content lives
in GROUPS, shared by desktop SVG, mobile SVG and the two-page vector PDF.
No external image or network dependency is required to render an edition.
"""
import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from textwrap import wrap

ROOT = Path(__file__).resolve().parent.parent
PORTRAIT = ROOT / "static" / "briefing-roi-portrait.webp"
SLUG = "ai-was-approved-who-can-stop-it"

# Source-locked, original operating-mandate taxonomy: four simultaneous duties.
GROUPS = (
    ("01", "BUSINESS MANDATE", "Permission has an owner and a purpose", (
        ("Outcome to change", "Name the business result and why AI belongs in the work."),
        ("Accountable decision-maker", "Keep responsibility for the outcome after the pilot."),
        ("Authorised operating scope", "Define allowed users, data, actions and exceptions."),
        ("Workflow consequence", "Locate where AI changes human work or customer outcomes."),
        ("Supplier and handover duty", "Assign vendor obligations and successor ownership."),
    )),
    ("02", "HUMAN CONTROL", "Authority remains exercisable", (
        ("Action permission", "Separate advice, preparation and autonomous execution."),
        ("Immediate pause right", "Name who can stop operation without waiting for approval."),
        ("Protected challenge", "Let people reject, correct or contest outputs safely."),
        ("Exception response", "Set triggers, responders and decision deadlines."),
        ("Recovery and remedy", "Define containment, rollback and correction after error."),
    )),
    ("03", "OPERATING EVIDENCE", "Assurance comes from what happens in work", (
        ("Real AI footprint", "Find authorised, embedded and unofficial uses."),
        ("Reconstructable decision", "Keep input, output, version, approval and action."),
        ("Human correction signal", "Review override patterns instead of hiding them."),
        ("Incident and near-miss learning", "Capture weak signals and assign remediation."),
        ("Shared-dependency exposure", "Know where one failure affects several workflows."),
    )),
    ("04", "RENEWAL AND EXIT", "Permission is conditional, not permanent", (
        ("Business and quality fitness", "Check outcomes and side effects in real operations."),
        ("Material-change gate", "Reapprove changed model, data, vendor, scope or permissions."),
        ("Drift response", "Detect deviations and determine when to intervene."),
        ("Periodic authorisation", "Renew ownership, evidence and controls at agreed gates."),
        ("Withdrawal and retirement", "Name who removes permission and protects continuity."),
    )),
)

NAVY = "#0c263e"
INK = "#1c3449"
WARM = "#fcfaf6"
SLATE = "#5b6c7a"
BORDER = "#d7e2e4"
CYAN = "#08b9d3"
COPPER = "#b98762"
PALETTE = ("#10b4c4", "#bf8865", "#528897", "#748aa7")


def _text(x, y, s, *, size=24, color=INK, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" fill="{color}" text-anchor="{anchor}" '
            'font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" font-weight="{weight}">{escape(str(s))}</text>')


def _portrait_svg(cx, cy, radius):
    if not PORTRAIT.is_file():
        return ""
    encoded = base64.b64encode(PORTRAIT.read_bytes()).decode("ascii")
    x = cx - radius
    y = cy - radius
    return (
        f'<defs><clipPath id="author-portrait"><circle cx="{cx}" cy="{cy}" r="{radius}"/></clipPath></defs>'
        f'<circle cx="{cx}" cy="{cy}" r="{radius+5}" fill="#ffffff"/>'
        f'<image x="{x}" y="{y}" width="{radius*2}" height="{radius*2}" '
        f'href="data:image/webp;base64,{encoded}" '
        'preserveAspectRatio="xMidYMid slice" clip-path="url(#author-portrait)"/>'
    )


def _start_svg(width, height, title):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
        f'<rect width="{width}" height="{height}" fill="{WARM}"/>',
    ]


@lru_cache(maxsize=1)
def artwork_svg() -> str:
    """The four obligations converge on an operating permission, not a maturity ladder."""
    width, height = 1600, 2220
    p = _start_svg(width, height, "20 AI operating decisions in four concurrent obligations")
    p += [
        '<rect width="1600" height="308" fill="#0c263e"/>',
        '<rect x="64" y="42" width="74" height="6" rx="3" fill="#08b9d3"/>',
        _text(64, 93, "EXECUTIVE AI BRIEFING  /  OPERATING AUTHORITY", size=23,
              color="#83d6e4", weight=700),
        _text(64, 180, "THE AI IS LIVE.", size=75, color="#ffffff", weight=700),
        _text(64, 261, "WHO HOLDS THE AUTHORITY?", size=69, color="#ffffff", weight=700),
        _text(1532, 91, "20 DECISIONS / 4 DUTIES", size=23,
              color="#eac3a1", weight=700, anchor="end"),
        _text(70, 366, "Authority must remain with the business after go-live.",
              size=37, color=NAVY, weight=700),
        _text(70, 408, "Four concurrent operating commitments, not a maturity ladder.",
              size=24, color=SLATE),
    ]
    count = 0
    for gi, (_, name, subtitle, decisions) in enumerate(GROUPS):
        x = 60 + (gi % 2) * 755
        y = 454 + (gi // 2) * 710
        accent = PALETTE[gi]
        p += [
            f'<rect x="{x}" y="{y}" width="725" height="686" rx="23" fill="#ffffff" '
            f'stroke="{BORDER}" stroke-width="2"/>',
            f'<rect x="{x}" y="{y}" width="725" height="12" rx="6" fill="{accent}"/>',
            _text(x+34, y+69, f"0{gi+1}   {name}", size=32, color=NAVY, weight=700),
            _text(x+34, y+110, subtitle, size=21, color=SLATE),
        ]
        for ri, (label, detail) in enumerate(decisions):
            count += 1
            yy = y+149 + ri*101
            if ri:
                p += [f'<line x1="{x+33}" y1="{yy-16}" x2="{x+693}" y2="{yy-16}" '
                      'stroke="#e7eeee" stroke-width="1"/>']
            p += [
                _text(x+33, yy+18, f"{count:02}", size=24, color=accent, weight=700),
                _text(x+88, yy+17, label, size=28, color=NAVY, weight=700),
                _text(x+88, yy+52, detail, size=19, color=SLATE),
            ]
    p += [
        '<rect x="60" y="1903" width="1480" height="126" rx="17" fill="#e7f0f0"/>',
        _text(95, 1951, "OPERATING PERMISSION IS CONDITIONAL", size=27,
              color=NAVY, weight=700),
        _text(95, 1995, "Proceed when ownership, intervention, evidence and renewal can be demonstrated.",
              size=24, color=INK),
        '<rect x="0" y="2055" width="1600" height="165" fill="#0c263e"/>',
        '<rect x="62" y="2071" width="1470" height="3" fill="#08b9d3"/>',
        _portrait_svg(126, 2140, 49),
        _text(202, 2133, "Jair Ribeiro", size=39, color="#ffffff", weight=700),
        _text(202, 2173, "AI LEADER  /  Enterprise AI Adoption  •  Governance  •  Business Transformation",
              size=21, color="#dce7ec"),
        _text(1530, 2146, "PROCEED  •  HOLD  •  STOP", size=23,
              color="#e7b992", weight=700, anchor="end"),
        '</svg>',
    ]
    return "".join(p)


@lru_cache(maxsize=1)
def artwork_mobile_svg() -> str:
    """Mobile variant retains all twenty decisions with dedicated line wrapping."""
    width, height = 900, 3850
    p = _start_svg(width, height, "20 AI operating decisions, mobile")
    p += [
        '<rect width="900" height="271" fill="#0c263e"/>',
        _text(39, 64, "EXECUTIVE AI BRIEFING / 20 DECISIONS", size=26, color="#83d6e4", weight=700),
        _text(39, 146, "THE AI IS LIVE.", size=61, color="#ffffff", weight=700),
        _text(39, 219, "WHO HOLDS AUTHORITY?", size=54, color="#ffffff", weight=700),
        _text(39, 324, "Four responsibilities keep permission", size=29, color=NAVY, weight=700),
        _text(39, 362, "to operate answerable to people.", size=29, color=NAVY),
    ]
    count = 0
    for gi, (_, name, subtitle, decisions) in enumerate(GROUPS):
        x, y = 26, 411 + gi*820
        accent = PALETTE[gi]
        p += [
            f'<rect x="{x}" y="{y}" width="848" height="789" rx="20" fill="#ffffff" '
            f'stroke="{BORDER}" stroke-width="2"/>',
            f'<rect x="{x}" y="{y}" width="848" height="12" rx="6" fill="{accent}"/>',
            _text(55, y+66, f"0{gi+1}   {name}", size=37, color=NAVY, weight=700),
            _text(55, y+107, subtitle, size=26, color=SLATE),
        ]
        for ri, (label, detail) in enumerate(decisions):
            count += 1
            ry = y+139 + ri*124
            if ri:
                p.append(f'<line x1="55" y1="{ry-13}" x2="840" y2="{ry-13}" '
                         'stroke="#dfe7e8" stroke-width="1"/>')
            p += [
                _text(56, ry+27, f"{count:02}", size=31, color=accent, weight=700),
                _text(122, ry+28, label, size=33, color=NAVY, weight=700),
            ]
            for k, line in enumerate(wrap(detail, width=49, break_long_words=False)[:2]):
                p.append(_text(122, ry+70+k*35, line, size=26, color=SLATE))
    p += [
        '<rect x="26" y="3697" width="848" height="57" rx="9" fill="#e1f0f2"/>',
        _text(53, 3734, "OWNERSHIP  •  INTERVENTION  •  EVIDENCE  •  REVIEW",
              size=23, color=NAVY, weight=700),
        '<rect x="0" y="3773" width="900" height="77" fill="#0c263e"/>',
        _text(35, 3810, "Jair Ribeiro  /  AI LEADER", size=30, color="#ffffff", weight=700),
        _text(35, 3837, "Enterprise AI Adoption  •  Governance  •  Business Transformation",
              size=20, color="#dce7ec"),
        '</svg>',
    ]
    return "".join(p)


@lru_cache(maxsize=1)
def artwork_pdf() -> bytes:
    """A4, two pages, vector typography: no tiny 20-tile photo of a checklist."""
    from fpdf import FPDF
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.set_title("The AI Is Live. Who Holds the Authority? | 20 Decisions")
    pdf.set_author("Jair Ribeiro")
    for page, selected in enumerate((GROUPS[:2], GROUPS[2:])):
        pdf.add_page()
        pdf.set_fill_color(12, 38, 62)
        pdf.rect(0, 0, 210, 42, "F")
        pdf.set_text_color(174, 224, 233)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.text(13, 12, "EXECUTIVE AI BRIEFING  /  OPERATING AUTHORITY")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 18)
        pdf.text(13, 25, "THE AI IS LIVE. WHO HOLDS THE AUTHORITY?")
        pdf.set_font("Helvetica", "", 9)
        pdf.text(13, 34, "20 decisions across four concurrent operating responsibilities.")
        y, count = 53, (0 if page == 0 else 10)
        for gi, (_, name, subtitle, rows) in enumerate(selected):
            pdf.set_fill_color(238, 244, 246)
            pdf.rect(12, y, 186, 12, "F")
            pdf.set_text_color(16, 43, 61)
            pdf.set_font("Helvetica", "B", 12)
            pdf.text(17, y+7.8, f"0{gi+1 + page*2}  {name}")
            y += 18
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(79, 99, 113)
            pdf.text(17, y, subtitle)
            y += 9
            for label, detail in rows:
                count += 1
                pdf.set_text_color(18, 50, 72)
                pdf.set_font("Helvetica", "B", 10.4)
                pdf.text(18, y, f"{count:02d}  {label}")
                pdf.set_text_color(78, 98, 113)
                pdf.set_font("Helvetica", "", 8.7)
                pdf.text(23, y+5.5, detail)
                y += 11.6
            y += 8
        if page == 1:
            pdf.set_fill_color(232, 243, 243)
            pdf.rect(12, 245, 186, 23, "F")
            pdf.set_text_color(13, 55, 75)
            pdf.set_font("Helvetica", "B", 9.8)
            pdf.text(17, 254, "EXECUTIVE GATE: PROCEED / HOLD / RESTRICT / STOP")
            pdf.set_font("Helvetica", "", 8.3)
            pdf.text(17, 261, "Record owner, scope, stop right, proof, review date and withdrawal rule.")
        pdf.set_fill_color(12, 38, 62)
        pdf.rect(0, 279, 210, 18, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.text(13, 286, "Jair Ribeiro  |  AI LEADER")
        pdf.set_font("Helvetica", "", 8)
        pdf.text(13, 292, "Enterprise AI Adoption  /  Governance  /  Business Transformation")
        pdf.set_text_color(210, 227, 232)
        pdf.text(178, 288, f"{page+1} / 2")
    return bytes(pdf.output())


def approved_authority_studio(article, row: dict) -> str:
    """Approved source-fingerprint gated artwork with responsive SVG and A4 PDF."""
    from html import escape as e
    if len(str(row.get("alt_text") or "").strip()) < 40:
        return ""
    return (
        '<style>'
        '.site .auth-infographic{max-width:930px;margin:28px auto 34px;padding:12px;'
        'background:#fffdf8;border:1px solid #d8e2e3;box-shadow:0 14px 38px rgba(14,37,57,.06)}'
        '.site .auth-infographic img{display:block;width:100%;height:auto;max-width:100%;background:#fff}'
        '.site .auth-infographic figcaption{font:13px/1.6 Arial,sans-serif;color:#536573;margin:12px 0}'
        '.site .auth-infographic a{display:inline-flex;justify-content:center;min-height:43px;'
        'align-items:center;padding:11px 18px;border:1px solid #7caabb;border-radius:6px;'
        'color:#0c3452!important;font:700 12px/1.4 Arial,sans-serif;text-decoration:none!important}'
        '.site .auth-infographic a:hover{background:#e9f5f7}'
        '@media(max-width:700px){.site .auth-infographic{padding:6px}.site .auth-infographic a{width:100%}}'
        '</style>'
        '<section data-analytics-section="briefing-infographic" data-hq-content-slug="'
        + e(article.slug,quote=True) + '">'
        '<figure class="auth-infographic"><picture>'
        '<source media="(max-width:700px)" srcset="/briefing-ai-authority/infographic.mobile.svg"/>'
        '<img loading="eager" decoding="async" '
        'src="/briefing-ai-authority/infographic.svg" width="1600" height="2220" '
        'alt="' + e(str(row["alt_text"]),quote=True) + '"/></picture>'
        '<figcaption>' + e(str(row.get("caption") or "")) + '</figcaption>'
        '<a href="/briefing-ai-authority/infographic.pdf" '
        'download="ai-operating-authority-20-decisions.pdf">'
        'Download the 20-decision operating mandate (A4 PDF)</a>'
        '</figure></section>'
    )
