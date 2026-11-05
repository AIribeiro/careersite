from __future__ import annotations

"""Lazy, self-contained reproduction of the approved AI ROI executive artwork.

The 1800 x 2400 poster is rendered with Pillow only when its briefing is viewed.
This avoids the static-URL failures observed in the Streamlit HTML reader.
"""

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import base64

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
NAVY = (8, 33, 58)
CYAN = (2, 188, 222)
COPPER = (195, 139, 87)
INK = (23, 42, 58)
SLATE = (85, 103, 119)
PALE = (232, 242, 247)
LINE = (210, 221, 227)


def font(size: int, bold: bool = False):
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for location in ("/usr/share/fonts/truetype/dejavu/" + filename, filename):
        try:
            return ImageFont.truetype(location, size)
        except OSError:
            pass
    raise OSError("DejaVu Sans fonts are required for the AI ROI poster")


def render() -> Image.Image:
    image = Image.new("RGB", (1800, 2400), (250, 249, 246))
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size, color=INK, bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=color)

    def box(xy, fill, radius=24, outline=None, width=2):
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

    def wrap(s, max_width, size, bold=False):
        result, current = [], ""
        for word in s.split():
            trial = (current + " " + word).strip()
            if draw.textbbox((0, 0), trial, font=font(size, bold))[2] <= max_width:
                current = trial
            else:
                if current:
                    result.append(current)
                current = word
        if current:
            result.append(current)
        return result

    def para(x, y, s, width, size=32, color=SLATE, spacing=13, max_lines=None, bold=False):
        lines = wrap(s, width, size, bold)
        if max_lines and len(lines) > max_lines:
            raise ValueError("Poster card overflow: " + s)
        for line in lines:
            text(x, y, line, size, color, bold)
            y += size + spacing

    draw.rectangle((0, 0, 1800, 310), fill=NAVY)
    draw.rectangle((0, 310, 1800, 320), fill=CYAN)
    text(90, 46, "EXECUTIVE AI BRIEFING  /  INVESTMENT DECISIONS", 33, (161, 218, 233), True)
    text(90, 107, "AI ROI: PROOF BEFORE SCALE", 75, (255, 255, 255), True)
    text(92, 222, "Seven measurement lenses. One disciplined financial decision.", 34, (215, 224, 234))

    text(91, 365, "01  |  THE FULL INVESTMENT", 29, (143, 88, 51), True)
    box((88, 419, 1710, 593), (242, 231, 215), 20, (219, 192, 159))
    text(126, 454, "COST", 45, NAVY, True)
    para(364, 449, "API and tokens • infrastructure • licences • build and maintenance • people • controls • change and training", 1300, 32, INK, 12, 2)
    text(126, 540, "Include the complete cost across the same measurement period.", 26, (118, 84, 53), True)

    text(90, 655, "02  |  MEASURABLE BUSINESS EFFECTS", 31, NAVY, True)
    text(90, 702, "Only verified financial effects enter the ROI numerator.", 27, SLATE)
    cards = [
        ("PRODUCTIVITY", "Hours saved • cases per employee • cycle time",
         "Count savings only when cost falls, hiring is avoided or capacity has evidenced economic use."),
        ("QUALITY", "Accuracy • rework • error rate • customer outcomes",
         "Value lower repair cost, fewer claims or measurable margin effects; do not count the same saving twice."),
        ("REVENUE", "Conversion • retention • upsell • new AI offerings",
         "Use incremental contribution margin, not gross revenue or pipeline estimates."),
        ("RISK REDUCTION", "Compliance events • fraud • errors • security",
         "Use defensible expected-loss reduction, adjusted for likelihood, impact and control cost."),
    ]
    for index, (name, metric, rule) in enumerate(cards):
        x, y = (88, 913)[index % 2], 755 + (index // 2) * 328
        box((x, y, x + 797, y + 292), (255, 255, 255), 22, LINE, 3)
        draw.rounded_rectangle((x, y, x + 12, y + 292), radius=6, fill=CYAN if index < 3 else COPPER)
        text(x + 42, y + 29, name, 39, NAVY, True)
        para(x + 42, y + 91, metric, 715, 28, (31, 88, 117), 12, 2, True)
        draw.line((x + 42, y + 171, x + 749, y + 171), fill=LINE, width=2)
        para(x + 42, y + 191, rule, 713, 25, SLATE, 10, 3)

    text(90, 1452, "03  |  SIGNALS THAT SUPPORT THE DECISION", 31, NAVY, True)
    text(90, 1498, "Track them carefully. Do not price them as cash without evidence.", 27, SLATE)
    for index, (name, metric, rule) in enumerate([
        ("ADOPTION", "Active users • usage depth • workflow coverage",
         "A leading signal of reach and use, not a financial return."),
        ("STRATEGIC VALUE", "Time-to-market • decision speed • growth capacity",
         "Record options and milestones; monetize only realized effects."),
    ]):
        x, y = (88, 913)[index], 1550
        box((x, y, x + 797, y + 247), PALE, 20, (173, 201, 214))
        text(x + 40, y + 22, name, 37, NAVY, True)
        para(x + 40, y + 87, metric, 730, 27, (37, 91, 115), 9, 2, True)
        para(x + 40, y + 159, rule, 723, 26, SLATE, 9, 2)

    box((87, 1840, 1711, 1989), (14, 53, 83), 20)
    text(122, 1865, "THE EVIDENCE CHAIN", 27, (144, 218, 235), True)
    for index, (step, explanation) in enumerate([
        ("BASELINE", "Before vs. after"),
        ("ATTRIBUTION", "Against a credible alternative"),
        ("REALIZATION", "Verified financial effect"),
        ("TOTAL COST", "Same period and scope"),
    ]):
        x = 124 + index * 395
        text(x, 1912, step, 26, (255, 255, 255), True)
        text(x, 1951, explanation, 19, (205, 223, 234))
        if index < 3:
            text(x + 346, 1913, "›", 42, CYAN, True)

    text(90, 2029, "NET ROI  =", 31, NAVY, True)
    text(370, 2025, "(Attributable financial benefit − full AI cost) ÷ full AI cost × 100", 29, NAVY, True)
    text(90, 2084, "Decision: SCALE with verified evidence  /  REDESIGN uncertain value  /  STOP persistent underperformance", 24, (78, 100, 117), True)

    draw.rectangle((0, 2167, 1800, 2400), fill=NAVY)
    draw.rectangle((0, 2167, 1800, 2175), fill=CYAN)
    for photo in (
        ROOT / "static" / "briefing-roi-portrait.webp",
        ROOT / "static" / "governance-avatar.webp",
        ROOT / "images" / "optimized" / "profile_red_bg.jpg.jpg.160.webp",
    ):
        try:
            portrait = ImageOps.fit(Image.open(photo).convert("RGB"), (155, 155), centering=(0.5, 0.4))
            mask = Image.new("L", (155, 155), 0)
            ImageDraw.Draw(mask).ellipse((2, 2, 152, 152), fill=255)
            image.paste(portrait, (91, 2205), mask)
            break
        except (OSError, ValueError):
            continue
    draw.ellipse((91, 2205, 245, 2359), outline=(246, 247, 246), width=6)
    text(276, 2216, "JAIR RIBEIRO", 41, (255, 255, 255), True)
    text(278, 2275, "AI LEADER", 29, CYAN, True)
    text(278, 2320, "Enterprise AI Adoption • Governance • Business Transformation", 27, (196, 214, 224))
    return image


@lru_cache(maxsize=2)
def artwork_bytes(variant: str) -> bytes:
    """Bounded, on-demand display or full-resolution PNG bytes."""
    if variant not in ("display", "download"):
        return b""
    data = BytesIO()
    image = render()
    if variant == "display":
        image.save(data, format="WEBP", quality=78, method=5)
    else:
        image.save(data, format="PNG", optimize=True)
    return data.getvalue()


@lru_cache(maxsize=2)
def artwork_data_uri(variant: str) -> str:
    data = artwork_bytes(variant)
    if not data:
        return ""
    mime = "image/webp" if variant == "display" else "image/png"
    return "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
