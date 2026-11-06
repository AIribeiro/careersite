from __future__ import annotations

"""Source-locked, original six-decision graphic for the AI scaling briefing.

Responsive first-party SVG. Labels and artwork are deterministic, safe to embed
as data URIs, and do not fetch any external resource.
"""

import base64
import html
import textwrap
from functools import lru_cache
from io import BytesIO
from pathlib import Path

NAVY = "#092d4e"
DEEP = "#061d36"
CYAN = "#09b7dc"
COPPER = "#c69067"
INK = "#18334c"
MUTED = "#4b6475"
CREAM = "#faf9f6"
WHITE = "#ffffff"

ICONS = {
    "target": '<circle cx="20" cy="20" r="14"/><circle cx="20" cy="20" r="5"/><path d="M20 1v9M20 30v9M1 20h9M30 20h9"/>',
    "workflow": '<rect x="3" y="4" width="12" height="12" rx="3"/><rect x="25" y="24" width="12" height="12" rx="3"/><path d="M15 10h8v8M23 18l-4-4M23 18h-8v12h10"/>',
    "people": '<circle cx="20" cy="12" r="7"/><path d="M6 36v-4a14 14 0 0 1 28 0v4M2 17h5M33 17h5"/>',
    "shield": '<path d="M20 2 35 8v11c0 11-6 17-15 20C11 36 5 30 5 19V8z"/><path d="m13 20 5 5 10-12"/>',
    "network": '<rect x="15" y="2" width="11" height="11" rx="2"/><rect x="1" y="27" width="11" height="11" rx="2"/><rect x="29" y="27" width="11" height="11" rx="2"/><path d="M20 13v9M20 22H7v5M20 22h14v5"/>',
    "trend": '<path d="M3 4v31h35M8 27l8-9 7 5 12-15M29 8h6v6"/>',
}
DEFAULT_ICONS = ("target", "workflow", "people", "shield", "network", "trend")


def _esc(value):
    return html.escape(str(value or ""), quote=True)


def _rect(x, y, w, h, fill, r=0, stroke="none"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


def _text(x, y, value, size, color=INK, weight=500, chars=50, lines=2, leading=1.30, *, anchor=None):
    words = textwrap.wrap(str(value), width=chars, break_long_words=False, break_on_hyphens=False)
    attr = ' text-anchor="middle"' if anchor == "middle" else ""
    pieces = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else int(size*leading)}">{_esc(line)}</tspan>'
        for i, line in enumerate(words[:lines])
    )
    return (f'<text x="{x}" y="{y}" font-family="Inter,Segoe UI,Arial,sans-serif" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}"{attr}>{pieces}</text>')


@lru_cache(maxsize=1)
def _portrait():
    """Use the real creator-supplied photograph already bundled with the portfolio."""
    try:
        from PIL import Image
        path = Path(__file__).resolve().parent.parent / "images" / "profile_red_bg.jpg.jpg"
        with Image.open(path) as pic:
            w, h = pic.size
            crop = pic.crop((int(w*.2875),int(h*.101),int(w*.545),int(h*.488)))
            crop = crop.resize((110,110), Image.Resampling.LANCZOS).convert("RGB")
            out = BytesIO()
            crop.save(out,format="JPEG",quality=72,optimize=True)
            return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")
    except (OSError, ValueError, ImportError):
        return ""


def _defs():
    return """<defs>
    <linearGradient id="nav" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#061d36"/><stop offset="1" stop-color="#0b4266"/></linearGradient>
    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffffff"/><stop offset="1" stop-color="#f4f9fb"/></linearGradient>
    <clipPath id="avatar"><circle cx="0" cy="0" r="43"/></clipPath>
    </defs>"""


def _icon(name, x, y, scale=1):
    paths = ICONS.get(name, ICONS["target"])
    return (f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{NAVY}" '
            'stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round">' + paths + '</g>')


def _card(item, i, x, y, w, *, mobile=False):
    h = 234 if mobile else 222
    title_size = 23 if mobile else 24
    detail_size = 16 if mobile else 17
    tx = x + 25
    icon_x = x + w - 89
    icon_y = y + 20
    label = item.get("label") or f"{i+1:02d}"
    p = [_rect(x, y, w, h, "url(#card)", 16, "#d7e4eb"),
         _rect(x, y, 5, h, CYAN if i % 2 == 0 else COPPER, 2),
         _rect(icon_x,icon_y,62,62,"#e7f5fa",13),
         _icon(item.get("icon") or DEFAULT_ICONS[i % len(DEFAULT_ICONS)],icon_x+10,icon_y+10,1.03),
         _text(tx, y+38, label, 16, "#39768b", 800, 32, 1),
         _text(tx,y+88,item.get("title"),title_size,NAVY,750,24 if mobile else 32,2),
         _rect(tx,y+136,w-50,2,"#e5eef2",1),
         _text(tx,y+164,item.get("detail"),detail_size,MUTED,480,36 if mobile else 48,3)
    ]
    return "".join(p)


def _footer(width, y, *, mobile=False):
    h = 180 if mobile else 145
    portrait = _portrait()
    x = 54 if mobile else 68
    cy = y + (77 if mobile else 68)
    p = [_rect(0,y,width,h,"url(#nav)"),
         _rect(0,y,width,3,CYAN),
         f'<circle cx="{x}" cy="{cy}" r="47" fill="{WHITE}"/>']
    if portrait:
        p.extend([f'<defs><clipPath id="footer-clip"><circle cx="{x}" cy="{cy}" r="43"/></clipPath></defs>',
                  f'<image href="{portrait}" x="{x-43}" y="{cy-43}" width="86" height="86" preserveAspectRatio="xMidYMid slice" clip-path="url(#footer-clip)"/>'])
    else:
        p.append(_text(x,cy+9,"JR",24,NAVY,800,2,1,anchor="middle"))
    tx = x + (64 if mobile else 78)
    p.extend([
        _text(tx, y+58 if mobile else y+55, "Jair Ribeiro", 26 if mobile else 30,WHITE,750,25,1),
        _text(tx, y+88 if mobile else y+84, "AI LEADER", 14 if mobile else 16,CYAN,850,30,1),
        _text(24 if mobile else tx,y+151 if mobile else y+115,
              "Enterprise AI Adoption · Governance · Business Transformation",
              13 if mobile else 16,"#c7dce8",500,51 if mobile else 80,2),
    ])
    return "".join(p)


def scale_svg(spec, mobile=False):
    """One six-part operating contract, not six borrowed vendor diagrams."""
    items = list(spec.get("items") or [])
    if len(items) != 6:
        raise ValueError("This edition requires exactly six distinct operating decisions.")
    width, height = (420, 2360) if mobile else (1200, 1520)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" role="img" aria-label="Six operating decisions that make enterprise AI scalable">',
         _defs(),_rect(0,0,width,height,CREAM),
         _rect(0,0,width,326 if mobile else 306,"url(#nav)"),
         _rect(0,0,width,8,CYAN)]
    if mobile:
        p.extend([
            _text(26,44,"EXECUTIVE AI BRIEFING  /  DECISION MAP",12,CYAN,850,46,1),
            _text(26,102,"BEYOND THE",35,WHITE,800,23,1),
            _text(26,146,"AI PILOT",40,WHITE,800,23,1),
            _text(26,193,"The operating contract",24,"#dbeaf2",650,28,1),
            _text(26,237,"Six decisions that move AI into",17,"#bdd4df",500,38,2),
            _text(26,261,"accountable enterprise work.",17,"#bdd4df",500,38,1),
            _rect(20,347,380,116,"#e6f3f7",14),
            _text(40,382,"PILOT PROOF",15,"#285e76",850,22,1),
            _text(40,413,"Capability tested",18,NAVY,650,27,1),
            _text(40,443,"SCALE NEEDS BUSINESS PERMISSION",14,NAVY,800,37,1),
        ])
        start=484
        for i,item in enumerate(items):
            p.append(_card(item,i,20,start+i*247,380,mobile=True))
        decision_y=1996
        p.extend([
            _rect(20,decision_y,380,160,NAVY,15),
            _text(40,decision_y+36,"THE SCALE DECISION",15,CYAN,850,35,1),
            _text(40,decision_y+73,"PROCEED  /  HOLD",24,WHITE,780,30,1),
            _text(40,decision_y+105,"/  REDESIGN",24,WHITE,780,30,1),
            _text(40,decision_y+137,"Based on evidence and accountable ownership",14,"#d5e8f1",450,43,1),
            _footer(width,2180,mobile=True)
        ])
    else:
        p.extend([
            _text(63,48,"EXECUTIVE AI BRIEFING   /   OPERATING DECISIONS",16,CYAN,850,65,1),
            _text(63,128,"BEYOND THE AI PILOT",61,WHITE,800,30,1),
            _text(63,182,"THE OPERATING CONTRACT",41,"#d9edf5",690,48,1),
            _text(63,237,"Six decisions that move AI from a successful test to accountable business work.",
                  22,"#c9deea",480,78,1),
            _rect(60,335,1080,87,"#e6f3f7",15),
            _text(83,370,"PILOT PROOF",16,"#316479",850,28,1),
            _text(83,398,"Technical capability tested",18,NAVY,630,40,1),
            _text(543,386,"→",38,COPPER,800,3,1),
            _text(632,370,"SCALE PERMISSION",16,"#316479",850,30,1),
            _text(632,398,"Owned work · authority · controls · measured value",18,NAVY,630,55,1)
        ])
        for i,item in enumerate(items):
            col=i%2
            row=i//2
            p.append(_card(item,i,60+col*552,452+row*244,528))
        p.extend([
            _rect(60,1208,1080,108,NAVY,16),
            _text(85,1242,"EXECUTIVE RELEASE DECISION",16,CYAN,850,50,1),
            _text(85,1286,"PROCEED     /     HOLD     /     REDESIGN",29,WHITE,780,57,1),
            _text(735,1283,"Based on evidence, not the demo.",18,"#d2e5ed",530,37,1),
            _footer(width,1375)
        ])
    p.append("</svg>")
    return "".join(p)
