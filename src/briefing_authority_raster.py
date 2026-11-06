from __future__ import annotations

"""Safari-safe, Pillow-rendered WebP assets for the 20-decision operating mandate.

SVG remains an editable source only. Public <img> URLs deliver ordinary
image/webp bytes, cached once per running application process.
"""

from functools import lru_cache
import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from briefing_authority_artwork import GROUPS

ROOT = Path(__file__).resolve().parents[1]
NAVY = (12, 38, 62)
INK = (27, 51, 72)
WARM = (252, 250, 247)
SLATE = (85, 104, 118)
BORDER = (214, 226, 228)
CYAN = (8, 184, 205)
COPPER = (194, 135, 97)
ACCENTS = ((16, 179, 193), (191, 137, 101), (82, 139, 150), (121, 141, 172))


@lru_cache(maxsize=30)
def _font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for file in ("/usr/share/fonts/truetype/dejavu/" + name, name):
        try:
            return ImageFont.truetype(file, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def _wrap(draw, value: str, width: int, size: int, bold=False) -> list[str]:
    font = _font(size, bold)
    lines, current = [], ""
    for word in value.split():
        test = (current + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _text(draw, x: int, y: int, value: str, size: int, color=INK, bold=False,
          *, max_width: int | None = None, max_lines: int = 1, leading: int | None = None):
    lines = _wrap(draw, value, max_width, size, bold) if max_width else [value]
    if len(lines) > max_lines:
        raise ValueError(f"Infographic text overflow: {value!r}: {len(lines)} lines")
    for i, line in enumerate(lines):
        draw.text((x, y+i*(leading or size+8)), line, font=_font(size, bold), fill=color)


def _avatar(image, x, y, size):
    for path in (
        ROOT / "static" / "briefing-roi-portrait.webp",
        ROOT / "static" / "governance-avatar.webp",
        ROOT / "images" / "optimized" / "profile_red_bg.jpg.jpg.160.webp",
    ):
        try:
            avatar = ImageOps.fit(Image.open(path).convert("RGB"), (size, size),
                                  method=Image.Resampling.LANCZOS, centering=(.5,.42))
            mask = Image.new("L", (size,size))
            ImageDraw.Draw(mask).ellipse((0,0,size-1,size-1),fill=255)
            image.paste(avatar, (x,y), mask)
            ImageDraw.Draw(image).ellipse((x-3,y-3,x+size+3,y+size+3), outline=(255,255,255), width=5)
            break
        except (OSError, ValueError):
            continue



# Premium iconography: geometric line symbols, drawn by Pillow at source
# resolution so the published inline image does not depend on icon fonts,
# SVG endpoints, external libraries or separate browser network requests.
HEADER_GRADIENTS = (
    ((0, 169, 177), (0, 93, 117)),      # business mandate: teal
    ((206, 140, 80), (144, 75, 48)),    # human control: copper
    ((14, 145, 155), (21, 88, 115)),    # operating evidence: deep teal
    ((109, 147, 190), (53, 87, 130)),   # renewal: slate
)


def _rounded_gradient(image, xy, top, bottom, radius=18):
    x0, y0, x1, y1 = map(int, xy)
    w, h = x1 - x0, y1 - y0
    fill = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(fill)
    for y in range(h):
        t = y / max(h-1, 1)
        c = tuple(round(a*(1-t) + b*t) for a, b in zip(top, bottom))
        draw.line((0, y, w, y), fill=c)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w-1, h-1), radius=radius, fill=255)
    image.paste(fill, (x0, y0), mask)


def _symbol(d, kind: int, cx: int, cy: int, scale: float=1.0, color=(248,250,251)):
    """Five quiet line icons, intentionally one per governance obligation."""
    def pt(dx, dy):
        return (round(cx+dx*scale), round(cy+dy*scale))
    sw = max(3, round(4*scale))
    def line(points, width=None):
        d.line([pt(x,y) for x,y in points], fill=color,
               width=width or sw, joint="curve")
    if kind == 0:  # Business: briefcase and accountable work
        d.rounded_rectangle((*pt(-23,-15),*pt(23,19)), radius=round(5*scale),
                            outline=color, width=sw)
        d.rounded_rectangle((*pt(-10,-25),*pt(10,-14)), radius=round(4*scale),
                            outline=color, width=sw)
        line([(-23,0),(-5,0),(-5,6),(5,6),(5,0),(23,0)])
    elif kind == 1:  # Human authority: shield with positive check
        line([(0,-27),(23,-16),(20,5),(11,21),(0,28),
              (-11,21),(-20,5),(-23,-16),(0,-27)])
        line([(-12,0),(-2,10),(13,-8)],width=round(5*scale))
    elif kind == 2:  # Evidence: source record and audit lens
        line([(-24,22),(-24,-23),(7,-23),(16,-14),(16,1)])
        line([(7,-23),(7,-14),(16,-14)])
        line([(-16,-9),(3,-9)])
        line([(-16,0),(-3,0)])
        r=round(13*scale)
        q=pt(9,10)
        d.ellipse((q[0]-r,q[1]-r,q[0]+r,q[1]+r),outline=color,width=sw)
        line([(18,19),(29,30)])
    elif kind == 3:  # Renewal: circular authority and deliberate exit
        xy=(*pt(-23,-23),*pt(23,23))
        d.arc(xy, start=208, end=350, fill=color,width=sw)
        d.arc(xy, start=30, end=175, fill=color,width=sw)
        line([(18,-18),(23,-8),(30,-17)])
        line([(-18,18),(-23,8),(-30,17)])
    else:  # Conditional permission: stacked decision layers
        line([(-29,-13),(0,-27),(29,-13),(0,1),(-29,-13)])
        line([(-29,-1),(0,13),(29,-1)])
        line([(-29,12),(0,26),(29,12)])


def _premium_card_header(image, d, x, y, width, i, mobile=False):
    h=123 if mobile else 121
    top,bottom=HEADER_GRADIENTS[i]
    _rounded_gradient(image,(x,y,x+width,y+h),top,bottom,radius=18)
    icon_x=x+(70 if mobile else 72)
    _symbol(d,i,icon_x,y+62,scale=1.04 if mobile else 1.10)
    divider=x+(126 if mobile else 128)
    d.line((divider,y+26,divider,y+96),fill=(217,229,234),width=2)
    _,title,subtitle,_=GROUPS[i]
    tx=x+(150 if mobile else 153)
    _text(d,tx,y+29,f"0{i+1}  {title}",34 if mobile else 30,(255,255,255),True,
          max_width=width-(tx-x)-24)
    _text(d,tx,y+81,subtitle,22 if mobile else 19,(238,245,247),
          max_width=width-(tx-x)-24)

def _desktop():
    W,H = 1600,2220
    image=Image.new("RGB",(W,H),WARM)
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,W,308),fill=NAVY)
    for k in range(4):
        d.arc((930+k*35,-320,1850+k*35,610),start=10,end=150,fill=(15+k*5,63+k*7,94+k*8),width=4)
    d.rounded_rectangle((64,42,138,48),radius=3,fill=CYAN)
    _text(d,64,69,"EXECUTIVE AI BRIEFING  /  OPERATING AUTHORITY",23,(131,214,228),True)
    _text(d,64,138,"THE AI IS LIVE.",76,(255,255,255),True)
    _text(d,64,222,"WHO HOLDS THE AUTHORITY?",67,(255,255,255),True)
    _text(d,1160,74,"20 DECISIONS / 4 DUTIES",23,(231,192,162),True)
    _text(d,70,326,"Authority must remain with the business after go-live.",36,NAVY,True)
    _text(d,70,384,"Four concurrent operating commitments, not a maturity ladder.",24,SLATE)
    n=0
    for i, (_, title, sub, decisions) in enumerate(GROUPS):
        x=60+(i%2)*755
        y=454+(i//2)*710
        accent=ACCENTS[i]
        d.rounded_rectangle((x+4,y+7,x+729,y+693),radius=22,fill=(226,232,232))
        d.rounded_rectangle((x,y,x+725,y+686),radius=22,fill=(255,255,255),outline=BORDER,width=2)
        _premium_card_header(image,d,x,y,725,i)
        for j,(label,detail) in enumerate(decisions):
            n+=1
            yy=y+149+j*101
            if j:
                d.line((x+33,yy-17,x+693,yy-17),fill=BORDER,width=2)
            _text(d,x+34,yy,f"{n:02d}",23,accent,True)
            _text(d,x+89,yy,label,25,NAVY,True,max_width=600)
            _text(d,x+89,yy+40,detail,18,SLATE,max_width=598,max_lines=2,leading=27)
    d.rounded_rectangle((60,1903,1540,2029),radius=20,fill=(226,241,245))
    _symbol(d,4,126,1966,scale=1.2,color=(21,103,123))
    d.line((194,1925,194,2007),fill=(36,127,148),width=2)
    _text(d,231,1924,"OPERATING PERMISSION IS CONDITIONAL",29,NAVY,True)
    _text(d,231,1978,"Proceed only while the business can own, intervene, explain and withdraw permission.",23,INK)
    d.rectangle((0,2055,1600,2220),fill=NAVY)
    d.rectangle((62,2071,1532,2075),fill=CYAN)
    _avatar(image,77,2093,100)
    _text(d,205,2102,"Jair Ribeiro",38,(255,255,255),True)
    _text(d,205,2157,"AI LEADER  /  Enterprise AI Adoption  •  Governance  •  Business Transformation",
          19,(220,231,236))
    _text(d,1200,2118,"PROCEED  /  HOLD  /  STOP",21,(233,185,148),True)
    return image


def _mobile():
    W,H=900,3850
    image=Image.new("RGB",(W,H),WARM)
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,900,271),fill=NAVY)
    _text(d,39,37,"EXECUTIVE AI BRIEFING / 20 DECISIONS",25,(131,214,228),True)
    _text(d,39,98,"THE AI IS LIVE.",59,(255,255,255),True)
    _text(d,39,171,"WHO HOLDS AUTHORITY?",52,(255,255,255),True)
    _text(d,39,298,"Four responsibilities keep permission",28,NAVY,True)
    _text(d,39,336,"to operate answerable to people.",28,NAVY)
    n=0
    for i, (_,title,sub,decisions) in enumerate(GROUPS):
        y=411+i*820
        accent=ACCENTS[i]
        d.rounded_rectangle((30,y+5,878,y+794),radius=21,fill=(226,232,232))
        d.rounded_rectangle((26,y,874,y+789),radius=21,fill=(255,255,255),outline=BORDER,width=2)
        _premium_card_header(image,d,26,y,848,i,mobile=True)
        for j,(label,detail) in enumerate(decisions):
            n+=1
            yy=y+139+j*124
            if j:
                d.line((55,yy-14,840,yy-14),fill=BORDER,width=2)
            _text(d,56,yy,f"{n:02d}",29,accent,True)
            _text(d,122,yy,label,30,NAVY,True,max_width=713)
            _text(d,122,yy+44,detail,24,SLATE,max_width=702,max_lines=2,leading=35)
    d.rounded_rectangle((26,3686,874,3761),radius=14,fill=(225,240,242))
    _symbol(d,4,68,3723,scale=.66,color=(21,103,123))
    d.line((112,3704,112,3745),fill=(36,127,148),width=2)
    _text(d,132,3710,"OPERATING PERMISSION IS CONDITIONAL",22,NAVY,True)
    _text(d,132,3739,"Own, intervene, explain and withdraw permission.",17,INK)
    d.rectangle((0,3773,900,3850),fill=NAVY)
    _text(d,35,3786,"Jair Ribeiro  /  AI LEADER",28,(255,255,255),True)
    _text(d,35,3820,"Enterprise AI Adoption  •  Governance  •  Business Transformation",18,(220,231,236))
    return image


@lru_cache(maxsize=2)
def artwork_webp(mode: str = "desktop") -> bytes:
    """WebP image encoded once per process; source for the HTTP and inline modes."""
    if mode not in ("desktop", "mobile"):
        raise ValueError("Unknown infographic size")
    img = _mobile() if mode == "mobile" else _desktop()
    stream=BytesIO()
    img.save(stream,format="WEBP",quality=89,method=4)
    return stream.getvalue()



@lru_cache(maxsize=2)
def artwork_data_uri(mode: str = "desktop") -> str:
    """Embed validated WebP bytes directly into Streamlit's HTML.

    In iPad Safari, the infographic's separate /briefing-ai-authority image
    request repeatedly failed even though the same route passed HTTP tests.
    A bounded data URI avoids that extra request, matching the working AI
    adoption infographic reader. The rendered image and PDF remain independent.
    """
    data = artwork_webp(mode)
    if not (15_000 < len(data) < 2_000_000):
        raise ValueError("AI authority infographic is missing or unexpectedly large")
    if not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        raise ValueError("AI authority infographic has invalid WebP signature")
    return "data:image/webp;base64," + base64.b64encode(data).decode("ascii")
