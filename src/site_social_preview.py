from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "profile_red_bg.jpg.jpg"
TARGET = ROOT / "static" / "jair-ribeiro-social-preview.png"
PUBLIC_URL = "https://jairribeiro-ai.streamlit.app/app/static/jair-ribeiro-social-preview.png"
SIZE = (1200, 630)

NAVY = "#0b1220"
WHITE = "#fffdf8"
COPPER = "#b86134"
COPPER_LIGHT = "#f0c09d"
EYEBROW = "#e6aa7d"
MUTED = "#c4ceda"
MUTED_DARK = "#95a2b4"
DIVIDER = "#364052"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    suffix = "-Bold" if bold else ""
    candidates = [
        Path(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf"),
        Path(
            "/usr/share/fonts/truetype/liberation2/"
            + ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")
        ),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def ensure_social_preview() -> Path:
    """Create the canonical 1200x630 social card from authentic site photography."""
    if not SOURCE.exists():
        return TARGET

    try:
        if TARGET.exists() and TARGET.stat().st_mtime >= SOURCE.stat().st_mtime:
            with Image.open(TARGET) as existing:
                if existing.size == SIZE and existing.format == "PNG":
                    return TARGET
    except OSError:
        pass

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", SIZE, NAVY)

    with Image.open(SOURCE) as source:
        photo = ImageOps.fit(
            source.convert("RGB"),
            (500, SIZE[1]),
            method=Image.Resampling.LANCZOS,
            centering=(0.52, 0.38),
        )

    canvas.paste(photo, (700, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((680, 0, 700, SIZE[1]), fill=COPPER)

    draw.text((70, 72), "ENTERPRISE AI · DATA · ANALYTICS", font=_font(22, bold=True), fill=EYEBROW)
    draw.text((70, 145), "Jair Ribeiro", font=_font(70, bold=True), fill=WHITE)
    draw.text((70, 245), "Enterprise AI &", font=_font(42), fill=COPPER_LIGHT)
    draw.text((70, 302), "Data Leader", font=_font(42), fill=COPPER_LIGHT)
    draw.line((70, 385, 585, 385), fill=DIVIDER, width=2)
    draw.text((70, 420), "Strategy · Operating capability", font=_font(23), fill=MUTED)
    draw.text((70, 458), "Adoption · Governance · Value", font=_font(23), fill=MUTED)
    draw.text((70, 560), "jairribeiro-ai.streamlit.app", font=_font(20, bold=True), fill=MUTED_DARK)

    canvas.save(TARGET, format="PNG", optimize=True)
    return TARGET
