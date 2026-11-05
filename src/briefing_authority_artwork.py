from __future__ import annotations

"""First-party, source-faithful artwork for the AI operating-authority briefing.

Five parallel operating contracts with 25 distinct decisions.
The SVG is rendered on demand as an image route; PDF is a two-page A4 vector
document. Neither is embedded as a data URI into the Streamlit article HTML.
"""

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTRAIT = ROOT / "static" / "briefing-roi-portrait.webp"
SLUG = "ai-was-approved-who-can-stop-it"

GROUPS = (
    ("01", "VISIBILITY", "Know what AI changes",
     (("Live inventory", "Locate deployed models, agents and AI-enabled workflows."),
      ("Supplier entry points", "Track AI introduced through product and model updates."),
      ("Unapproved use", "Find activity outside the reviewed working route."),
      ("Decision touchpoints", "Map where AI affects people, actions or outcomes."),
      ("Concentrated exposure", "Spot failures that could propagate across many workflows."))),
    ("02", "RESPONSIBILITY", "Put names on outcomes",
     (("Executive sponsor", "Name who accepts accountability for material consequences."),
      ("Service steward", "Assign the person who keeps the system within its scope."),
      ("Decision owner", "Keep accountability with the business decision-maker."),
      ("Domain challenge", "Identify the expert who can question a wrong result."),
      ("Supplier boundary", "Separate vendor duties from obligations retained internally."))),
    ("03", "HUMAN AUTHORITY", "Make intervention possible",
     (("Human decision line", "Set where automation ends and human approval begins."),
      ("Immediate stop right", "Name who can pause operations without a committee."),
      ("Protected override", "Let staff contest, correct or refuse an unsafe output."),
      ("Escalation trigger", "Define who responds, when and to which warning signal."),
      ("Reversal path", "Specify rollback, correction or remedy for irreversible harm."))),
    ("04", "EVIDENCE", "Make decisions explainable",
     (("Decision trace", "Retain inputs, output, action, time and responsible actor."),
      ("Approved-use record", "Show which purpose, users and boundaries were agreed."),
      ("Intervention history", "Capture overrides and investigate recurring patterns."),
      ("Near-miss learning", "Log weak signals and incidents, not just confirmed harm."),
      ("Control lineage", "Link outcomes to ownership, rule, review and proof."))),
    ("05", "CONTINUING PERMISSION", "Review, restrict or retire",
     (("Operating outcomes", "Check that performance remains acceptable in real work."),
      ("Change review gate", "Reassess model, vendor, data, permissions or workflow changes."),
      ("Drift detection", "Watch shifts in behavior, inputs and human reliance."),
      ("Scheduled reassessment", "Recheck evidence, control fitness and named ownership."),
      ("Retirement authority", "Document who can restrict, replace or remove the system."))),
)

NAVY = "#10283e"
DARK = "#16283c"
CREAM = "#f8f8f5"
SLATE = "#566779"
CYAN = "#08b9d3"
COPPER = "#bd8864"
BORDER = "#dfe8e8"
PALETTE = (CYAN, COPPER, "#3a8f9c", "#7891ae", COPPER)


def _text(x, y, value, *, size=21, color=DARK, weight=400, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{size}" font-weight="{weight}"{a}>{escape(str(value))}</text>')


@lru_cache(maxsize=1)
def artwork_svg() -> str:
    """A 1,600 x 2,410 original decision register, not the supplied 5x5 tile layout."""
    width, height = 1600, 2410
    p = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
         'role="img" aria-label="Twenty-five AI operating-authority decisions grouped into five domains">']
    p.extend((f'<rect width="{width}" height="{height}" fill="{CREAM}"/>',
              '<rect width="1600" height="295" fill="#0c263e"/>',
              '<rect x="72" y="43" width="78" height="6" rx="3" fill="#08b9d3"/>',
              _text(72, 88, "EXECUTIVE AI BRIEFING  /  OPERATING AUTHORITY", size=22, color="#9ad7e0", weight=700),
              _text(72, 172, "AI WAS APPROVED.", size=78, color="#ffffff", weight=700),
              _text(72, 247, "WHO CAN STOP IT?", size=78, color="#ffffff", weight=700),
              _text(1530, 87, "25 DECISIONS  /  5 CONTRACTS", size=23, color="#e8c8a9", weight=700, anchor="end"),
              _text(73, 337, "Approval to launch is not permanent permission to operate.", size=31, color=NAVY, weight=600),
              _text(73, 374, "Five concurrent controls, each with five decisions leaders should be able to evidence.", size=23, color=SLATE),
              ))
    top, group_h = 414, 357
    counter = 0
    for i, (number, title, headline, rows) in enumerate(GROUPS):
        y = top + i*group_h
        accent = PALETTE[i]
        p.extend((f'<rect x="64" y="{y}" width="1472" height="341" rx="19" fill="#ffffff" stroke="{BORDER}" stroke-width="2"/>',
                  f'<rect x="64" y="{y}" width="14" height="341" rx="7" fill="{accent}"/>',
                  _text(105, y+81, number, size=67, color=accent, weight=700),
                  _text(105, y+119, title, size=25, color=NAVY, weight=700),
                  _text(105, y+164, headline, size=26, color=SLATE, weight=400),
                  f'<line x1="458" y1="{y+25}" x2="458" y2="{y+315}" stroke="{BORDER}" stroke-width="2"/>'))
        for j, (name, detail) in enumerate(rows):
            counter += 1
            ry = y+31+j*60
            if j:
                p.append(f'<line x1="488" y1="{ry-15}" x2="1509" y2="{ry-15}" stroke="#e8eeee" stroke-width="1"/>')
            p.extend((_text(496, ry+16, f"{counter:02}", size=21, color=accent, weight=700),
                      _text(547, ry+16, name, size=25, color=NAVY, weight=700),
                      _text(547, ry+42, detail, size=21, color=SLATE)))
    foot_y = 2211
    p.extend(('<rect x="0" y="2211" width="1600" height="199" fill="#0c263e"/>',
              f'<rect x="64" y="{foot_y+31}" width="1472" height="3" fill="{CYAN}" opacity=".65"/>',
              _text(220, foot_y+91, "Jair Ribeiro", size=38, color="#ffffff", weight=700),
              _text(220, foot_y+130, "AI LEADER", size=23, color="#8de2eb", weight=700),
              _text(220, foot_y+163, "Enterprise AI Adoption  •  Governance  •  Business Transformation",
                    size=21, color="#dbe7eb")))
    if PORTRAIT.is_file():
        img = base64.b64encode(PORTRAIT.read_bytes()).decode("ascii")
        p.append('<defs><clipPath id="portrait-circle"><circle cx="131" cy="2319" r="63"/></clipPath></defs>')
        p.append('<circle cx="131" cy="2319" r="68" fill="#ffffff"/>')
        p.append(f'<image x="68" y="2256" width="126" height="126" '
                 f'href="data:image/webp;base64,{img}" preserveAspectRatio="xMidYMid slice" '
                 'clip-path="url(#portrait-circle)"/>')
    p.append(_text(1530, foot_y+112, "REVIEW  /  HOLD  /  STOP", size=24,
                   color="#e9c4a5", weight=700, anchor="end"))
    p.append('</svg>')
    return "".join(p)


@lru_cache(maxsize=1)
def artwork_mobile_svg() -> str:
    """Tall, legible mobile composition: five sections and all 25 decisions."""
    width, height = 900, 4520
    p = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
         'role="img" aria-label="Twenty-five AI governance decisions for mobile readers">',
         f'<rect width="{width}" height="{height}" fill="{CREAM}"/>',
         '<rect width="900" height="255" fill="#0c263e"/>',
         _text(45, 65, "EXECUTIVE AI BRIEFING  /  25 DECISIONS", size=25, color="#92dce5", weight=700),
         _text(45, 146, "AI WAS APPROVED.", size=57, color="#ffffff", weight=700),
         _text(45, 214, "WHO CAN STOP IT?", size=57, color="#ffffff", weight=700),
         _text(45, 300, "Five controls. One continuing permission to operate.",
               size=28, color=NAVY, weight=600)]
    top, step = 337, 795
    count = 0
    for i, (number, title, headline, rows) in enumerate(GROUPS):
        y = top + i*step
        accent = PALETTE[i]
        p.extend((
            f'<rect x="27" y="{y}" width="846" height="770" rx="23" fill="white" stroke="{BORDER}" stroke-width="2"/>',
            f'<rect x="27" y="{y}" width="846" height="11" rx="6" fill="{accent}"/>',
            _text(57, y+76, f"{number}  {title}", size=42, color=NAVY, weight=700),
            _text(57, y+117, headline, size=30, color=SLATE)))
        for j, (name, detail) in enumerate(rows):
            count += 1
            ry = y+149+j*119
            if j:
                p.append(f'<line x1="58" y1="{ry-11}" x2="842" y2="{ry-11}" stroke="{BORDER}"/>')
            p.extend((_text(59, ry+25, f"{count:02d}", size=29, color=accent, weight=700),
                      _text(119, ry+25, name, size=34, color=NAVY, weight=700)))
            lines = wrap(detail, width=51, break_long_words=False)
            for k, line in enumerate(lines[:2]):
                p.append(_text(119, ry+65+37*k, line, size=29, color=SLATE))
    foot_y = 4320
    p.extend((f'<rect x="0" y="{foot_y}" width="900" height="200" fill="#0c263e"/>',
              _text(170, foot_y+77, "Jair Ribeiro", size=42, color="#ffffff", weight=700),
              _text(170, foot_y+119, "AI LEADER", size=26, color="#8de2eb", weight=700),
              _text(38, foot_y+172, "Enterprise AI Adoption  •  Governance  •  Business Transformation",
                    size=25, color="#dce7eb")))
    if PORTRAIT.is_file():
        img = base64.b64encode(PORTRAIT.read_bytes()).decode("ascii")
        p.append(f'<circle cx="96" cy="{foot_y+86}" r="57" fill="white"/>')
        p.append(f'<defs><clipPath id="mobile-portrait"><circle cx="96" cy="{foot_y+86}" r="53"/></clipPath></defs>')
        p.append(f'<image x="43" y="{foot_y+33}" width="106" height="106" '
                 f'href="data:image/webp;base64,{img}" preserveAspectRatio="xMidYMid slice" '
                 'clip-path="url(#mobile-portrait)"/>')
    p.append('</svg>')
    return "".join(p)


@lru_cache(maxsize=1)
def artwork_pdf() -> bytes:
    """Two-page A4 PDF; vector text and cards remain sharp when magnified."""
    from fpdf import FPDF
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.set_title("AI Was Approved. Who Can Stop It? | 25 Operating Decisions")
    pdf.set_author("Jair Ribeiro")
    pdf.set_subject("Executive AI governance: operating authority, evidence and continual review")
    for page, groups in enumerate((GROUPS[:3], GROUPS[3:])):
        pdf.add_page()
        pdf.set_fill_color(12, 38, 62)
        pdf.rect(0, 0, 210, 35, "F")
        pdf.set_text_color(180, 231, 238)
        pdf.set_font("Helvetica", "B", 8)
        pdf.text(13, 11, "EXECUTIVE AI BRIEFING  /  OPERATING AUTHORITY")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 20)
        pdf.text(13, 24, "AI WAS APPROVED. WHO CAN STOP IT?")
        pdf.set_text_color(42, 67, 81)
        pdf.set_font("Helvetica", "", 10)
        pdf.text(13, 44, "25 operating decisions across five concurrent controls.")
        y = 54
        global_index = 0 if page == 0 else 15
        for i, (_, title, _, rows) in enumerate(groups):
            rgb = [(8, 153, 170), (174, 120, 83), (42, 125, 137), (81, 112, 146), (174, 120, 83)]
            group_index = (i if page == 0 else i+3)
            pdf.set_fill_color(245, 248, 248)
            pdf.rect(12, y, 186, 8, "F")
            pdf.set_fill_color(*rgb[group_index])
            pdf.rect(12, y, 2, 8, "F")
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(20, 44, 62)
            pdf.text(18, y+5.8, f"{group_index+1:02d}  {title}")
            y += 11
            for name, detail in rows:
                global_index += 1
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(21, 48, 67)
                pdf.text(16, y, f"{global_index:02d}  {name}")
                pdf.set_font("Helvetica", "", 8.8)
                pdf.set_text_color(70, 89, 102)
                pdf.text(20, y+5.3, detail)
                y += 10.8
            y += 4
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
    """One original infographic and a first-party PDF CTA for the approved edition."""
    from html import escape as e
    if len(str(row.get("alt_text") or "").strip()) < 40:
        return ""
    caption = str(row.get("caption") or "").strip()
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
        '<section data-analytics-section="briefing-infographic" data-hq-content-slug="' + e(article.slug,quote=True) + '">'
        '<figure class="auth-infographic"><picture>'
        '<source media="(max-width:700px)" srcset="/briefing-ai-authority/infographic-mobile.svg"/>'
        '<img loading="eager" decoding="async" '
        'src="/briefing-ai-authority/infographic.svg" width="1600" height="2410" '
        'alt="' + e(str(row["alt_text"]),quote=True) + '"/></picture>'
        '<figcaption>' + e(caption) + '</figcaption>'
        '<a href="/briefing-ai-authority/infographic.pdf" '
        'download="ai-operating-authority-25-decisions.pdf">'
        'Download the full 25-decision infographic (A4 PDF)</a>'
        '</figure></section>'
    )
