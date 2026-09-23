from __future__ import annotations

import base64
from io import BytesIO
import json
import textwrap
from urllib import error, request

from PIL import Image, ImageDraw, ImageFont, ImageOps


OPENAI_IMAGE_MODEL = "gpt-image-2.5-flare"
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"


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
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    left = (6, 59, 104)
    right = (23, 184, 207)
    for x in range(width):
        t = x / max(1, width - 1)
        col = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(3))
        for y in range(height):
            vertical = min(1.0, 0.88 + 0.12 * (y / max(1, height - 1)))
            pixels[x, y] = tuple(round(c * vertical) for c in col)
    return image


def build_header_prompt(title: str, subtitle: str = "", category: str = "", excerpt: str = "") -> str:
    context = " ".join(part.strip() for part in (subtitle, excerpt) if part and part.strip())
    context = context[:900]
    return (
        "Create one abstract editorial vector motif for the right-hand side of a professional "
        "enterprise AI thought-leadership article header. Infer the visual metaphor from the article. "
        "Use elegant geometric line art: nodes, pathways, gates, arrows, decision structures, data "
        "signals, organizational networks, or another simple conceptual symbol appropriate to the topic. "
        "Palette only: luminous cyan, soft white, muted blue, and restrained warm amber/copper. "
        "Transparent background. Flat vector aesthetic, precise lines, restrained complexity, executive "
        "rather than futuristic or sci-fi. No people, no faces, no photographs, no 3D rendering, no "
        "robots, no brains, no glowing orb clichés. Absolutely no text, letters, numbers, logos, "
        "watermarks, labels, UI, charts with readable labels, or signature. Keep the motif centered with "
        "generous transparent space around it so it can be composited into a branded template.\n\n"
        f"ARTICLE TITLE: {title.strip()}\n"
        f"ARTICLE CATEGORY: {category.strip() or 'Enterprise AI'}\n"
        f"ARTICLE CONTEXT: {context or title.strip()}"
    )


def generate_ai_motif(
    api_key: str,
    *,
    title: str,
    subtitle: str = "",
    category: str = "",
    excerpt: str = "",
    timeout: int = 180,
) -> bytes:
    if not api_key.strip():
        raise ValueError("OPENAI_API_KEY is not configured.")
    if not title.strip():
        raise ValueError("Add the article title before generating a header.")

    payload = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": build_header_prompt(title, subtitle, category, excerpt),
        "size": "1024x1024",
        "quality": "medium",
        "background": "transparent",
        "output_format": "png",
        "n": 1,
    }
    req = request.Request(
        OPENAI_IMAGES_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            detail_json = json.loads(detail)
            message = detail_json.get("error", {}).get("message") or detail
        except Exception:
            message = detail
        raise RuntimeError(f"OpenAI image generation failed ({exc.code}): {str(message)[:400]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI image generation could not be reached: {exc.reason}") from exc

    try:
        encoded = data["data"][0]["b64_json"]
        return base64.b64decode(encoded)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("OpenAI image generation returned an unexpected response.") from exc


def _wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    max_lines: int,
    start_size: int,
    min_size: int,
    bold: bool,
) -> tuple[list[str], ImageFont.ImageFont]:
    words = text.strip().split()
    if not words:
        return [], _font(start_size, bold=bold)

    for size in range(start_size, min_size - 1, -2):
        font = _font(size, bold=bold)
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
        if current:
            lines.append(current)
        if len(lines) <= max_lines and all(
            draw.textbbox((0, 0), line, font=font)[2] <= max_width for line in lines
        ):
            return lines, font

    font = _font(min_size, bold=bold)
    approximate_chars = max(12, int(max_width / max(1, min_size * 0.56)))
    lines = textwrap.wrap(text.strip(), width=approximate_chars)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "…"
    return lines, font


def compose_templated_header(
    motif_png: bytes,
    *,
    title: str,
    subtitle: str = "",
    size: tuple[int, int] = (1600, 900),
) -> bytes:
    width, height = size
    canvas = _gradient(size).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    grid = (156, 232, 242, 30)
    for x in range(0, width, 70):
        draw.line((x, 0, x, height), fill=grid, width=1)
    for y in range(0, height, 70):
        draw.line((0, y, width, y), fill=grid, width=1)

    draw.ellipse((-150, -220, 450, 380), outline=(123, 232, 244, 55), width=2)
    draw.ellipse((1260, 560, 1960, 1260), outline=(123, 232, 244, 45), width=2)

    kicker_font = _font(20, bold=True)
    draw.text(
        (94, 58),
        "LEADING IN THE AI ENTERPRISE",
        font=kicker_font,
        fill=(255, 192, 137, 255),
    )

    title_lines, title_font = _wrapped_lines(
        draw,
        title,
        max_width=825,
        max_lines=3,
        start_size=78,
        min_size=54,
        bold=True,
    )
    title_y = 155
    title_bbox = draw.textbbox((0, 0), "Ag", font=title_font)
    line_height = (title_bbox[3] - title_bbox[1]) + 18
    for line in title_lines:
        draw.text((92, title_y), line, font=title_font, fill=(255, 255, 255, 255))
        title_y += line_height

    if subtitle.strip():
        subtitle_lines, subtitle_font = _wrapped_lines(
            draw,
            subtitle,
            max_width=810,
            max_lines=3,
            start_size=31,
            min_size=24,
            bold=False,
        )
        subtitle_y = title_y + 30
        sub_bbox = draw.textbbox((0, 0), "Ag", font=subtitle_font)
        sub_height = (sub_bbox[3] - sub_bbox[1]) + 14
        for line in subtitle_lines:
            draw.text((96, subtitle_y), line, font=subtitle_font, fill=(215, 237, 245, 255))
            subtitle_y += sub_height

    motif = Image.open(BytesIO(motif_png)).convert("RGBA")
    motif = ImageOps.contain(motif, (610, 610), Image.Resampling.LANCZOS)
    alpha = motif.getchannel("A")
    if alpha.getbbox() is None:
        alpha = Image.new("L", motif.size, 235)
        motif.putalpha(alpha)
    motif_x = width - motif.width - 55
    motif_y = max(155, int((height - motif.height) / 2) + 30)
    canvas.alpha_composite(motif, (motif_x, motif_y))

    author_font = _font(24)
    draw.line((1348, 828, 1404, 828), fill=(255, 255, 255, 220), width=3)
    draw.text((1420, 812), "Jair Ribeiro", font=author_font, fill=(255, 255, 255, 255))

    output = BytesIO()
    canvas.convert("RGB").save(output, format="WEBP", quality=92, method=6)
    return output.getvalue()


def generate_templated_ai_header(
    api_key: str,
    *,
    title: str,
    subtitle: str = "",
    category: str = "",
    excerpt: str = "",
) -> bytes:
    motif = generate_ai_motif(
        api_key,
        title=title,
        subtitle=subtitle,
        category=category,
        excerpt=excerpt,
    )
    return compose_templated_header(motif, title=title, subtitle=subtitle)
