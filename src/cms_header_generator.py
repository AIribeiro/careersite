from __future__ import annotations

import base64
import hashlib
from io import BytesIO
import json
import textwrap
from urllib import error, request

from PIL import Image, ImageDraw, ImageFont, ImageOps


OPENAI_IMAGE_MODEL = "gpt-image-2.5-flare"
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"

# Dark-to-vivid pairs chosen to preserve white-title legibility while giving each
# article a distinct identity. Selection is pseudo-random but deterministic from
# the article slug/title, so regenerating the same article keeps its color family.
BACKGROUND_PALETTES = (
    ("Arctic", (6, 59, 104), (23, 184, 207)),
    ("Forest", (24, 61, 53), (63, 156, 122)),
    ("Indigo", (43, 49, 94), (112, 106, 203)),
    ("Plum", (73, 42, 79), (163, 91, 140)),
    ("Ember", (97, 47, 41), (200, 109, 74)),
    ("Slate", (38, 60, 74), (93, 141, 158)),
    ("Teal", (6, 74, 82), (44, 166, 164)),
    ("Bronze", (85, 58, 40), (184, 138, 85)),
    ("Ink", (23, 37, 63), (74, 120, 168)),
    ("Olive", (57, 69, 45), (131, 154, 83)),
    ("Wine", (81, 43, 63), (167, 96, 114)),
    ("Ocean", (10, 61, 86), (44, 142, 175)),
)


def background_palette_for(seed: str) -> dict[str, object]:
    normalized = (seed or "untitled").strip().lower().encode("utf-8")
    digest = hashlib.sha256(normalized).digest()
    index = int.from_bytes(digest[:2], "big") % len(BACKGROUND_PALETTES)
    name, left, right = BACKGROUND_PALETTES[index]

    # Blend a small amount of a second approved palette into the right edge.
    # This yields many stable variants while staying inside the designated family.
    offset = 1 + digest[2] % (len(BACKGROUND_PALETTES) - 1)
    _, _, neighbor_right = BACKGROUND_PALETTES[(index + offset) % len(BACKGROUND_PALETTES)]
    mix = 0.04 + (digest[3] / 255.0) * 0.14
    varied_right = tuple(
        round(right[i] * (1.0 - mix) + neighbor_right[i] * mix)
        for i in range(3)
    )
    tilt = (digest[4] / 255.0) * 2.0 - 1.0
    return {
        "name": name,
        "left": left,
        "right": varied_right,
        "tilt": tilt,
        "digest": digest,
    }


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


def _gradient(size: tuple[int, int], *, seed: str) -> tuple[Image.Image, dict[str, object]]:
    width, height = size
    palette = background_palette_for(seed)
    left = palette["left"]
    right = palette["right"]
    tilt = float(palette["tilt"])

    image = Image.new("RGB", size)
    pixels = image.load()
    for x in range(width):
        x_t = x / max(1, width - 1)
        for y in range(height):
            y_t = (y / max(1, height - 1)) - 0.5
            t = max(0.0, min(1.0, x_t + y_t * tilt * 0.16))
            col = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(3))
            vertical = min(1.0, 0.88 + 0.12 * (y / max(1, height - 1)))
            pixels[x, y] = tuple(round(c * vertical) for c in col)
    return image, palette


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
    palette_seed: str = "",
    size: tuple[int, int] = (1600, 900),
) -> bytes:
    width, height = size
    seed = palette_seed.strip() or title.strip() or "untitled"
    background, palette = _gradient(size, seed=seed)
    canvas = background.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    grid = (156, 232, 242, 30)
    for x in range(0, width, 70):
        draw.line((x, 0, x, height), fill=grid, width=1)
    for y in range(0, height, 70):
        draw.line((0, y, width, y), fill=grid, width=1)

    digest = palette["digest"]
    ring_dx = int(digest[5]) - 128
    ring_dy = int(digest[6]) - 128
    ring_color = tuple(palette["right"]) + (55,)
    draw.ellipse(
        (-150 + ring_dx, -220 + ring_dy // 2, 450 + ring_dx, 380 + ring_dy // 2),
        outline=ring_color,
        width=2,
    )
    draw.ellipse(
        (1260 - ring_dx // 2, 560 - ring_dy // 2, 1960 - ring_dx // 2, 1260 - ring_dy // 2),
        outline=tuple(palette["right"]) + (45,),
        width=2,
    )

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
    palette_seed: str = "",
) -> bytes:
    motif = generate_ai_motif(
        api_key,
        title=title,
        subtitle=subtitle,
        category=category,
        excerpt=excerpt,
    )
    return compose_templated_header(
        motif,
        title=title,
        subtitle=subtitle,
        palette_seed=palette_seed or title,
    )
