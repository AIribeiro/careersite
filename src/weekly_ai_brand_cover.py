"""Deterministic, portrait-based WEEKLY AI Friday social cover (1200 x 627).

Source artwork is the user-approved Week 43 design's exact portrait crop,
committed as a small base64-encoded WebP so GitHub Actions can reproduce it.
The image changes only in edition metadata, not in the person's likeness.
"""
from __future__ import annotations

from base64 import b64decode
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from random import Random
import math
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PORTRAIT_SOURCE = ROOT / "data" / "weekly_ai_visual" / "approved_portrait.webp.b64"
PORTRAIT_SHA256 = "afd5f9949851e3dc0ed556941b7d8528f5aa4d90c055bf3105998625c215fb94"
APPROVED_WEEK43_SOURCE = ROOT / "data" / "weekly_ai_visual" / "week43_approved_original.webp.b64"
APPROVED_WEEK43_SHA256 = "109fe0accb9a208b666bc2898821d9fd618dc6d402d47fa3e830d21b7203ca94"
SIZE = (1200, 627)
NAVY = (8, 21, 37)
COPPER = (224, 149, 106)
IVORY = (249, 249, 247)
PALE = (215, 225, 229)
FONT_ROOTS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation2",
    "/usr/local/share/fonts",
)


def _font(size: int, *, serif: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"] if bold and serif else
             ["DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"] if serif else
             ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"] if bold else
             ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"])
    for root in FONT_ROOTS:
        for name in names:
            path = Path(root) / name
            if path.is_file():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _load_portrait(source: Path = PORTRAIT_SOURCE) -> Image.Image:
    raw = b64decode("".join(source.read_text(encoding="ascii").split()), validate=True)
    if sha256(raw).hexdigest() != PORTRAIT_SHA256:
        raise ValueError("Approved WEEKLY AI photo digest mismatch; no replacement allowed")
    with Image.open(BytesIO(raw)) as im:
        return im.convert("RGB")


def approved_week43_image() -> Image.Image:
    """Preserve the exact visually approved edition instead of approximating it."""
    raw = b64decode("".join(APPROVED_WEEK43_SOURCE.read_text(encoding="ascii").split()), validate=True)
    if sha256(raw).hexdigest() != APPROVED_WEEK43_SHA256:
        raise ValueError("The author-approved Week 43 visual has changed unexpectedly")
    with Image.open(BytesIO(raw)) as image:
        if image.size != SIZE:
            raise ValueError("Wrong approved Week 43 LinkedIn cover dimensions")
        return image.convert("RGB")


def _background() -> Image.Image:
    im = Image.new("RGB", SIZE, NAVY)
    px = im.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            glow = 9 * (x / SIZE[0]) + 6 * (1 - y / SIZE[1])
            px[x, y] = (int(8 + glow * .35), int(21 + glow * .55), int(37 + glow))
    return im


def _constellation(canvas: Image.Image) -> None:
    overlay = Image.new("RGBA", SIZE)
    d = ImageDraw.Draw(overlay, "RGBA")
    # Subtle half-globe constellation sits behind the far right of the copy.
    cx, cy, radius = 1175, 275, 290
    for a in range(-65, 110, 12):
        theta = math.radians(a)
        for r in range(110, radius, 31):
            x = cx + int(math.cos(theta) * r)
            y = cy + int(math.sin(theta) * r)
            if 960 <= x < 1195 and 15 <= y < 610:
                d.ellipse((x-1.6,y-1.6,x+1.6,y+1.6),fill=(226,164,111,90))
    for radius2 in (170, 250, 335):
        d.arc((cx-radius2,cy-radius2,cx+radius2,cy+radius2), 100, 280, fill=(216,148,109,52),width=2)
    rng=Random(43)
    for _ in range(40):
        x=rng.randint(930,1190); y=rng.randint(25,610)
        size=rng.choice((1,1,2))
        d.ellipse((x,y,x+size,y+size),fill=(235,174,116,75))
    canvas.paste(overlay,(0,0),overlay)


def _split_lines(draw: ImageDraw.ImageDraw, words: list[str], font: ImageFont.ImageFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2] <= width:
            current=candidate
        else:
            if current:
                lines.append(current)
            current=word
    if current:
        lines.append(current)
    return lines


def render_friday_cover(*, iso_year: int, iso_week: int, title: str,
                        subtitle: str = "Friday perspective · one minute",
                        photo_source: Path = PORTRAIT_SOURCE) -> Image.Image:
    """Return one copy-safe LinkedIn 1200x627 image with distinct edition metadata."""
    date.fromisocalendar(int(iso_year), int(iso_week), 5)  # reject impossible ISO weeks
    title = re.sub(r"\s+", " ", title).strip()
    subtitle = re.sub(r"\s+", " ", subtitle).strip()
    if not (8 <= len(title) <= 95 and 8 <= len(subtitle) <= 70):
        raise ValueError("Unsafe or missing Weekly AI headline/subtitle")
    if (int(iso_year), int(iso_week), title, subtitle) == (
        2026, 43, "Faster Tools, Harder Decisions", "Friday perspective · one minute"
    ):
        return approved_week43_image()
    canvas=_background()
    _constellation(canvas)
    portrait=ImageOps.fit(_load_portrait(photo_source),(485,627),method=Image.Resampling.LANCZOS,centering=(.48,.5))
    canvas.paste(portrait,(0,0))
    # Natural fade into navy; avoid a hard rectangular portrait edge.
    px=canvas.load()
    for x in range(380,525):
        t=max(0,min(1,(x-380)/145))
        a=t*t*(3-2*t)
        for y in range(627):
            r,g,b=px[x,y]
            v=(int(8+4*x/1200), int(21+8*x/1200), int(37+10*x/1200))
            px[x,y]=(int(r*(1-a)+v[0]*a),int(g*(1-a)+v[1]*a),int(b*(1-a)+v[2]*a))
    d=ImageDraw.Draw(canvas)
    left=540
    d.text((left,59),"T H I N K I N G",font=_font(14,bold=True),fill=PALE)
    d.line([(left+160,73),(left+295,73)],fill=COPPER,width=3)
    main=_font(73,serif=True,bold=True)
    d.text((left,98),"WEEKLY",font=main,fill=IVORY,stroke_width=0)
    width=d.textbbox((0,0),"WEEKLY",font=main)[2]
    d.text((left+width+12,98),"AI",font=main,fill=COPPER)
    d.text((left+5,206),f"Week {iso_week} · {iso_year}",font=_font(34),fill=IVORY)
    d.line([(left+8,270),(left+220,270)],fill=COPPER,width=3)

    words=title.split(" ")
    selected=None
    for fontsize in range(43,27,-1):
        f=_font(fontsize,serif=True,bold=True)
        lines=_split_lines(d,words,f,635)
        if len(lines)<=3 and all(d.textbbox((0,0),line,font=f)[2]<=635 for line in lines):
            selected=(f,lines,fontsize)
            break
    if selected is None:
        raise ValueError("Headline cannot fit LinkedIn cover without clipping")
    font,lines,fontsize=selected
    lineheight=fontsize+11
    ypos=305
    for line in lines:
        d.text((left+5,ypos),line,font=font,fill=COPPER)
        ypos+=lineheight
    # Keep subtitle after the actual headline and before the brand signature.
    subtitle_y=max(475,ypos+4)
    subtitle_font=_font(23)
    while d.textbbox((0,0),subtitle,font=subtitle_font)[2]>625:
        subtitle_font=_font(max(13,getattr(subtitle_font,'size',23)-1))
        if getattr(subtitle_font,'size',13)<=13:
            break
    if subtitle_y>532:
        raise ValueError("Friday cover headline collides with subtitle")
    d.text((left+8,subtitle_y),subtitle,font=subtitle_font,fill=PALE)
    d.line([(left+8,578),(left+83,578)],fill=COPPER,width=3)
    d.text((left+97,559),"Jair Ribeiro · Enterprise AI & Data Leader",font=_font(17,bold=True),fill=IVORY)
    return canvas


def save_friday_cover(iso_year: int, iso_week: int, title: str, subtitle: str,
                       output: Path) -> Path:
    image=render_friday_cover(iso_year=iso_year,iso_week=iso_week,title=title,subtitle=subtitle)
    output.parent.mkdir(parents=True,exist_ok=True)
    image.save(output,format="PNG",optimize=True)
    with Image.open(output) as check:
        if check.size!=SIZE or check.format!="PNG":
            raise RuntimeError("Friday cover verification failed")
    return output