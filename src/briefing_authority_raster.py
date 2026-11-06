from __future__ import annotations

"""Safari-safe, Pillow-rendered WebP assets for the 20-decision operating mandate.

SVG remains an editable source only. Public <img> URLs deliver ordinary
image/webp bytes, cached once per running application process.
"""

from functools import lru_cache
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


def _desktop():
    W,H = 1600,2220
    image=Image.new("RGB",(W,H),WARM)
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,W,308),fill=NAVY)
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
        d.rounded_rectangle((x,y,x+725,y+686),radius=22,fill=(255,255,255),outline=BORDER,width=2)
        d.rounded_rectangle((x,y,x+725,y+12),radius=5,fill=accent)
        _text(d,x+34,y+43,f"0{i+1}  {title}",30,NAVY,True)
        _text(d,x+34,y+91,sub,20,SLATE,max_width=650,max_lines=2)
        for j,(label,detail) in enumerate(decisions):
            n+=1
            yy=y+149+j*101
            if j:
                d.line((x+33,yy-17,x+693,yy-17),fill=BORDER,width=2)
            _text(d,x+34,yy,f"{n:02d}",23,accent,True)
            _text(d,x+89,yy,label,25,NAVY,True,max_width=600)
            _text(d,x+89,yy+40,detail,18,SLATE,max_width=598,max_lines=2,leading=27)
    d.rounded_rectangle((60,1903,1540,2029),radius=18,fill=(231,240,240))
    _text(d,95,1924,"OPERATING PERMISSION IS CONDITIONAL",27,NAVY,True)
    _text(d,95,1978,"Proceed only while the business can own, intervene, explain and withdraw permission.",23,INK)
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
        d.rounded_rectangle((26,y,874,y+789),radius=21,fill=(255,255,255),outline=BORDER,width=2)
        d.rounded_rectangle((26,y,874,y+12),radius=5,fill=accent)
        _text(d,55,y+37,f"0{i+1}  {title}",36,NAVY,True)
        _text(d,55,y+89,sub,24,SLATE,max_width=760,max_lines=2)
        for j,(label,detail) in enumerate(decisions):
            n+=1
            yy=y+139+j*124
            if j:
                d.line((55,yy-14,840,yy-14),fill=BORDER,width=2)
            _text(d,56,yy,f"{n:02d}",29,accent,True)
            _text(d,122,yy,label,30,NAVY,True,max_width=713)
            _text(d,122,yy+44,detail,24,SLATE,max_width=702,max_lines=2,leading=35)
    d.rounded_rectangle((26,3697,874,3754),radius=9,fill=(225,240,242))
    _text(d,54,3714,"OWNERSHIP / INTERVENTION / EVIDENCE / REVIEW",21,NAVY,True)
    d.rectangle((0,3773,900,3850),fill=NAVY)
    _text(d,35,3786,"Jair Ribeiro  /  AI LEADER",28,(255,255,255),True)
    _text(d,35,3820,"Enterprise AI Adoption  •  Governance  •  Business Transformation",18,(220,231,236))
    return image


@lru_cache(maxsize=2)
def artwork_webp(mode: str = "desktop") -> bytes:
    """Pre-rasterised WebP encoded once per process, never inside Streamlit HTML."""
    if mode not in ("desktop", "mobile"):
        raise ValueError("Unknown infographic size")
    img = _mobile() if mode == "mobile" else _desktop()
    stream=BytesIO()
    img.save(stream,format="WEBP",quality=89,method=4)
    return stream.getvalue()
