from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

VISUAL_VERSION = "thinking-vector-v1-2026-09-18"


@dataclass(frozen=True)
class VisualSpec:
    title_lines: tuple[str, ...]
    subtitle_lines: tuple[str, ...]
    motif: str


VISUALS: dict[str, VisualSpec] = {
    "pilot_to_scale": VisualSpec(
        ("Why Enterprise AI Often Stalls", "Between Pilot and Scale"),
        ("AI pilots are rarely the hardest part.", "Building the operating capability to scale them is."),
        "scale",
    ),
    "governance_accountability": VisualSpec(
        ("The AI Governance Gate", "I Would Never Remove"),
        ("Good AI governance should help organizations move with confidence,", "not simply add control."),
        "gate",
    ),
    "investable_portfolio": VisualSpec(
        ("From AI Use-Case List", "to Investable Portfolio"),
        ("A list of AI ideas is not a portfolio.", "The real work is deciding where investment can create measurable value."),
        "portfolio",
    ),
    "adoption_metric": VisualSpec(
        ("One AI Adoption Metric", "I Don’t Trust"),
        ("Usage tells us something about AI adoption.", "It does not tell us whether work has actually changed."),
        "adoption",
    ),
    "coe_not_ai_department": VisualSpec(
        ("The AI CoE Should Not Become", "the Company’s AI Department"),
        ("An AI CoE should build organizational capability—", "not become the permanent owner of everything AI."),
        "coe",
    ),
    "strategy_to_value_framework": VisualSpec(
        ("Strategy → Portfolio → Governance", "→ Adoption → Value"),
        ("AI value depends on the whole chain working—", "not on strategy, governance or technology in isolation."),
        "chain",
    ),
    "stop_ai_use_case": VisualSpec(
        ("When an AI Use Case", "Should Be Stopped"),
        ("Stopping weak AI work is not failure.", "Continuing after the evidence changes often is."),
        "stop",
    ),
    "roi_diagnosed_too_late": VisualSpec(
        ("AI ROI Is Often", "Diagnosed Too Late"),
        ("If ROI becomes a serious question only after deployment,", "the value problem probably started much earlier."),
        "roi",
    ),
}


def visual_spec(article_key: str) -> VisualSpec:
    return VISUALS[article_key]


def _svg_motif(kind: str) -> str:
    common = 'fill="none" stroke-linecap="round" stroke-linejoin="round"'
    cyan = '#73efff'
    amber = '#ffb25f'
    white = '#f6fbff'
    dim = '#82bfd3'
    if kind == "scale":
        return f'''<g {common} stroke-width="6"><rect x="1040" y="510" width="92" height="92" rx="14" stroke="{cyan}"/><path d="M1145 556H1220" stroke="{white}"/><path d="M1200 536l20 20-20 20" stroke="{white}"/><rect x="1240" y="455" width="120" height="120" rx="16" stroke="{amber}"/><path d="M1368 515H1435" stroke="{white}"/><path d="M1415 495l20 20-20 20" stroke="{white}"/><rect x="1450" y="402" width="142" height="142" rx="18" stroke="{cyan}"/></g><g fill="{cyan}"><circle cx="1086" cy="556" r="9"/><circle cx="1300" cy="515" r="11"/><circle cx="1521" cy="473" r="13"/></g>'''
    if kind == "gate":
        return f'''<g {common} stroke-width="6"><path d="M1010 520H1180" stroke="{dim}"/><path d="M1330 520H1535" stroke="{dim}"/><rect x="1192" y="390" width="126" height="260" rx="18" stroke="{amber}"/><circle cx="1255" cy="492" r="34" stroke="{white}"/><path d="M1208 585c18-45 77-45 95 0" stroke="{white}"/><path d="M1535 520l-24-24m24 24-24 24" stroke="{cyan}"/></g><circle cx="1255" cy="520" r="110" fill="none" stroke="{amber}" stroke-width="2" stroke-dasharray="10 12"/>'''
    if kind == "portfolio":
        cards = ''.join(f'<rect x="{1015+(i%3)*92}" y="{390+(i//3)*82}" width="68" height="52" rx="8" fill="none" stroke="{dim}" stroke-width="4"/>' for i in range(6))
        return f'''<g>{cards}</g><path d="M1280 428L1370 500 1280 572" fill="none" stroke="{amber}" stroke-width="6"/><g fill="none" stroke-width="6"><rect x="1400" y="425" width="92" height="70" rx="10" stroke="{cyan}"/><rect x="1400" y="520" width="92" height="70" rx="10" stroke="{white}"/><rect x="1515" y="472" width="92" height="70" rx="10" stroke="{amber}"/></g>'''
    if kind == "adoption":
        return f'''<g fill="none" stroke-width="5"><path d="M1020 590V510M1080 590V470M1140 590V535" stroke="{dim}"/><path d="M1210 548H1300L1375 475H1475L1550 425" stroke="{cyan}"/><circle cx="1210" cy="548" r="15" stroke="{white}"/><circle cx="1375" cy="475" r="15" stroke="{amber}"/><circle cx="1550" cy="425" r="18" stroke="{white}"/><path d="M1515 425l20 20 40-48" stroke="{amber}"/></g>'''
    if kind == "coe":
        nodes = [(1055,420),(1055,620),(1475,420),(1475,620)]
        links = ''.join(f'<path d="M1265 520L{x} {y}" stroke="{dim}" stroke-width="4"/>' for x,y in nodes)
        boxes = ''.join(f'<rect x="{x-42}" y="{y-30}" width="84" height="60" rx="10" fill="none" stroke="{cyan if i%2==0 else white}" stroke-width="5"/>' for i,(x,y) in enumerate(nodes))
        return f'''{links}<circle cx="1265" cy="520" r="84" fill="none" stroke="{amber}" stroke-width="7"/><circle cx="1265" cy="520" r="24" fill="{amber}"/>{boxes}'''
    if kind == "chain":
        xs = [1015,1145,1275,1405,1535]
        labels = ['S','P','G','A','V']
        parts=[]
        for i,(x,label) in enumerate(zip(xs,labels)):
            col = amber if i in (0,4) else cyan
            parts.append(f'<circle cx="{x}" cy="520" r="42" fill="none" stroke="{col}" stroke-width="6"/><text x="{x}" y="533" text-anchor="middle" fill="{white}" font-family="Arial,sans-serif" font-size="34" font-weight="700">{label}</text>')
            if i < 4:
                parts.append(f'<path d="M{x+48} 520H{xs[i+1]-48}" stroke="{dim}" stroke-width="5"/><path d="M{xs[i+1]-62} 506l14 14-14 14" fill="none" stroke="{dim}" stroke-width="5"/>')
        return ''.join(parts)
    if kind == "stop":
        return f'''<g fill="none" stroke-width="6" {common}><path d="M1020 540H1220" stroke="{cyan}"/><path d="M1220 540C1320 540 1330 440 1410 440H1530" stroke="{amber}"/><path d="M1220 540C1320 540 1330 650 1410 650H1530" stroke="{cyan}"/><circle cx="1220" cy="540" r="22" stroke="{white}"/><rect x="1530" y="395" width="84" height="84" rx="12" stroke="{amber}"/><path d="M1550 415l44 44m0-44-44 44" stroke="{amber}"/><rect x="1530" y="608" width="84" height="84" rx="12" stroke="{cyan}"/><path d="M1549 650l18 18 31-39" stroke="{white}"/></g>'''
    return f'''<g fill="none" stroke-width="6" {common}><circle cx="1025" cy="590" r="18" stroke="{dim}"/><circle cx="1180" cy="540" r="18" stroke="{cyan}"/><circle cx="1340" cy="480" r="18" stroke="{amber}"/><circle cx="1515" cy="400" r="22" stroke="{white}"/><path d="M1043 584L1162 546 1322 488 1495 410" stroke="{cyan}"/><path d="M1470 395h45v45" stroke="{amber}"/></g><path d="M1000 650H1570" stroke="{dim}" stroke-width="2" opacity=".6"/>'''


@lru_cache(maxsize=None)
def visual_svg(article_key: str) -> str:
    spec = visual_spec(article_key)
    title_size = 70 if article_key == "coe_not_ai_department" else 78
    title = ''.join(
        f'<text x="92" y="{170 + i*86}" fill="#ffffff" font-family="Inter,Arial,sans-serif" font-size="{title_size}" font-weight="750" letter-spacing="-2">{html.escape(line)}</text>'
        for i, line in enumerate(spec.title_lines)
    )
    subtitle_y = 170 + len(spec.title_lines)*86 + 42
    subtitle = ''.join(
        f'<text x="96" y="{subtitle_y + i*40}" fill="#d7edf5" font-family="Inter,Arial,sans-serif" font-size="31" font-weight="400">{html.escape(line)}</text>'
        for i, line in enumerate(spec.subtitle_lines)
    )
    motif = _svg_motif(spec.motif)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-label="{html.escape(' '.join(spec.title_lines))}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#063b68"/><stop offset=".52" stop-color="#087ca7"/><stop offset="1" stop-color="#17b8cf"/></linearGradient>
  <pattern id="grid" width="70" height="70" patternUnits="userSpaceOnUse"><path d="M70 0H0V70" fill="none" stroke="#9ce8f2" stroke-width="1" opacity=".12"/></pattern>
  <filter id="glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/><rect width="1600" height="900" fill="url(#grid)"/>
<circle cx="150" cy="80" r="300" fill="none" stroke="#7be8f4" stroke-width="2" opacity=".22"/><circle cx="1460" cy="840" r="350" fill="none" stroke="#7be8f4" stroke-width="2" opacity=".18"/>
<text x="94" y="75" fill="#ffc089" font-family="Inter,Arial,sans-serif" font-size="20" font-weight="800" letter-spacing="4">LEADING IN THE AI ENTERPRISE</text>
{title}{subtitle}
<g filter="url(#glow)" opacity=".96">{motif}</g>
<path d="M1350 826h54" stroke="#ffffff" stroke-width="3" opacity=".85"/><text x="1420" y="835" fill="#ffffff" font-family="Inter,Arial,sans-serif" font-size="24">Jair Ribeiro</text>
</svg>'''


@lru_cache(maxsize=None)
def visual_data_uri(article_key: str) -> str:
    payload = base64.b64encode(visual_svg(article_key).encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{payload}"


def _font(size: int, *, bold: bool = False):
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(size: tuple[int, int]) -> Image.Image:
    w, h = size
    image = Image.new("RGB", size)
    px = image.load()
    left = (6, 59, 104)
    right = (23, 184, 207)
    for x in range(w):
        t = x / max(1, w - 1)
        col = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(3))
        for y in range(h):
            v = min(1.0, 0.88 + 0.12 * (y / max(1, h - 1)))
            px[x, y] = tuple(round(c * v) for c in col)
    return image


def _draw_motif(draw: ImageDraw.ImageDraw, kind: str, w: int, h: int) -> None:
    cyan = (115, 239, 255)
    amber = (255, 178, 95)
    white = (246, 251, 255)
    dim = (130, 191, 211)
    x0 = int(w * .67)
    cy = int(h * .68)
    if kind == "scale":
        for i, s in enumerate((54, 70, 88)):
            x = x0 + i * 115
            y = cy - s // 2 - i * 20
            draw.rounded_rectangle((x, y, x+s, y+s), radius=9, outline=cyan if i != 1 else amber, width=4)
            if i < 2:
                draw.line((x+s+12, y+s//2, x+105, y+s//2), fill=white, width=4)
    elif kind == "gate":
        draw.line((x0, cy, w-90, cy), fill=dim, width=4)
        gx = x0 + 150
        draw.rounded_rectangle((gx, cy-100, gx+88, cy+100), radius=12, outline=amber, width=5)
        draw.ellipse((gx+24, cy-55, gx+64, cy-15), outline=white, width=4)
        draw.arc((gx+15, cy-10, gx+73, cy+58), 200, 340, fill=white, width=4)
    elif kind == "portfolio":
        for r in range(2):
            for c in range(3):
                x=x0+c*60; y=cy-120+r*58
                draw.rounded_rectangle((x,y,x+44,y+34),radius=5,outline=dim,width=3)
        draw.polygon([(x0+205,cy-100),(x0+260,cy),(x0+205,cy+100)], outline=amber)
        for i,col in enumerate((cyan,white,amber)):
            x=x0+285+(i%2)*75; y=cy-70+(i//2)*82
            draw.rounded_rectangle((x,y,x+60,y+44),radius=6,outline=col,width=4)
    elif kind == "adoption":
        for i,bar in enumerate((58,90,42)):
            x=x0+i*48
            draw.line((x,cy+75,x,cy+75-bar),fill=dim,width=8)
        pts=[(x0+180,cy+35),(x0+245,cy+35),(x0+310,cy-28),(x0+390,cy-28),(x0+455,cy-82)]
        draw.line(pts,fill=cyan,width=5,joint="curve")
        for p in pts[::2]: draw.ellipse((p[0]-8,p[1]-8,p[0]+8,p[1]+8),outline=amber,width=4)
    elif kind == "coe":
        cx=x0+230
        draw.ellipse((cx-52,cy-52,cx+52,cy+52),outline=amber,width=6)
        nodes=[(x0+30,cy-85),(x0+30,cy+85),(x0+430,cy-85),(x0+430,cy+85)]
        for i,(x,y) in enumerate(nodes):
            draw.line((cx,cy,x,y),fill=dim,width=3)
            draw.rounded_rectangle((x-34,y-24,x+34,y+24),radius=6,outline=cyan if i%2==0 else white,width=4)
    elif kind == "chain":
        xs=[x0+i*88 for i in range(5)]
        for i,x in enumerate(xs):
            draw.ellipse((x-26,cy-26,x+26,cy+26),outline=amber if i in (0,4) else cyan,width=5)
            if i<4: draw.line((x+28,cy,xs[i+1]-28,cy),fill=dim,width=4)
    elif kind == "stop":
        bx=x0+145
        draw.line((x0,cy,bx,cy),fill=cyan,width=5)
        draw.line((bx,cy,bx+130,cy-85,w-95,cy-85),fill=amber,width=5)
        draw.line((bx,cy,bx+130,cy+85,w-95,cy+85),fill=cyan,width=5)
        draw.rectangle((w-145,cy-125,w-90,cy-70),outline=amber,width=4)
        draw.line((w-135,cy-115,w-100,cy-80),fill=amber,width=4); draw.line((w-100,cy-115,w-135,cy-80),fill=amber,width=4)
        draw.rectangle((w-145,cy+58,w-90,cy+113),outline=cyan,width=4)
        draw.line((w-135,cy+85,w-120,cy+100,w-98,cy+72),fill=white,width=4)
    else:
        pts=[(x0,cy+70),(x0+110,cy+35),(x0+220,cy-15),(x0+350,cy-90)]
        draw.line(pts,fill=cyan,width=5,joint="curve")
        for i,p in enumerate(pts): draw.ellipse((p[0]-9,p[1]-9,p[0]+9,p[1]+9),outline=amber if i==2 else white,width=4)


def render_social_image(article_key: str, size: tuple[int, int] = (1200, 627)) -> Image.Image:
    spec = visual_spec(article_key)
    image = _gradient(size)
    draw = ImageDraw.Draw(image)
    w, h = size
    grid = (56, 143, 170)
    for x in range(0, w, 60):
        draw.line((x, 0, x, h), fill=grid, width=1)
    for y in range(0, h, 60):
        draw.line((0, y, w, y), fill=grid, width=1)
    draw.text((66, 38), "LEADING IN THE AI ENTERPRISE", font=_font(17, bold=True), fill=(255, 192, 137))
    title_size = 53 if article_key == "coe_not_ai_department" else 60
    y = 92
    for line in spec.title_lines:
        draw.text((64, y), line, font=_font(title_size, bold=True), fill=(255, 255, 255))
        y += title_size + 10
    y += 12
    for line in spec.subtitle_lines:
        draw.text((68, y), line, font=_font(23), fill=(216, 237, 245))
        y += 32
    _draw_motif(draw, spec.motif, w, h)
    draw.line((965, h-52, 1005, h-52), fill=(255,255,255), width=2)
    draw.text((1020, h-67), "Jair Ribeiro", font=_font(21), fill=(255,255,255))
    return image
