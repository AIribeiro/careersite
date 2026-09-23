from __future__ import annotations

from io import BytesIO

from PIL import Image

from cms_header_generator import (
    DEFAULT_OPENROUTER_IMAGE_MODEL,
    OPENROUTER_IMAGES_URL,
    background_palette_for,
    build_header_prompt,
    compose_templated_header,
)


def _transparent_motif() -> bytes:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for x in range(70, 190):
        for y in range(70, 190):
            image.putpixel((x, y), (115, 239, 255, 220))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_header_prompt_is_branded_and_text_free():
    prompt = build_header_prompt(
        "AI Governance at Scale",
        "Governance should enable responsible speed.",
        "AI Governance",
        "A practical operating model for enterprise AI.",
    )
    assert "AI Governance at Scale" in prompt
    assert "transparent background" in prompt.lower()
    assert "absolutely no text" in prompt.lower()
    assert "robots" in prompt.lower()


def test_compose_templated_header_returns_16_9_webp():
    rendered = compose_templated_header(
        _transparent_motif(),
        title="Why Enterprise AI Often Stalls Between Pilot and Scale",
        subtitle="AI pilots are rarely the hardest part. Building the operating capability to scale them is.",
    )
    assert rendered[:4] == b"RIFF"
    image = Image.open(BytesIO(rendered))
    assert image.format == "WEBP"
    assert image.size == (1600, 900)


def test_palette_is_deterministic_but_varies_by_article_identity():
    first = background_palette_for("ai-governance-at-scale")
    again = background_palette_for("ai-governance-at-scale")
    second = background_palette_for("why-enterprise-ai-stalls")
    assert first == again
    assert first != second
    assert first["name"]
    assert len(first["left"]) == 3
    assert len(first["right"]) == 3


def test_different_palette_seeds_produce_different_headers():
    kwargs = {
        "motif_png": _transparent_motif(),
        "title": "AI Governance at Scale",
        "subtitle": "Governance should enable responsible speed.",
    }
    first = compose_templated_header(**kwargs, palette_seed="governance")
    second = compose_templated_header(**kwargs, palette_seed="portfolio")
    assert first != second


def test_image_generation_uses_openrouter_not_direct_openai():
    assert OPENROUTER_IMAGES_URL == "https://openrouter.ai/api/v1/images"
    assert DEFAULT_OPENROUTER_IMAGE_MODEL == "sourceful/riverflow-v2.5-pro"
    assert not DEFAULT_OPENROUTER_IMAGE_MODEL.startswith("openai/")
