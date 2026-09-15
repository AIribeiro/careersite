from __future__ import annotations

from pathlib import Path
from io import BytesIO
import base64
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)

# The original project photography is preserved in the repository media bundle
# under generic asset names. Build purpose-specific, high-resolution WebP crops
# from those originals so public pages never depend on corrupt placeholders.
SPECS = {
    "hero-executive.webp": {
        "needles": ["panel.webp"],
        "ratio": (4, 3),
        "max_width": 1800,
        "quality": 88,
    },
    "home-panel.webp": {
        "needles": ["panel-live.webp", "panel.webp"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
    "impact-keynote.webp": {
        "needles": ["hero.webp", "panel-live.webp"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
    "impact-ai-panel.webp": {
        "needles": ["panel-live.webp", "panel.webp"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
    "thinking-panel.webp": {
        "needles": ["portrait-casual.webp", "panel.webp"],
        "ratio": (4, 5),
        "max_width": 1200,
        "quality": 88,
    },
    "about-human.webp": {
        "needles": ["portrait-casual.webp", "hero.webp"],
        "ratio": (1, 1),
        "max_width": 1400,
        "quality": 88,
    },
    "about-editorial.webp": {
        "needles": ["hero.webp", "portrait-casual.webp"],
        "ratio": (4, 5),
        "max_width": 1200,
        "quality": 88,
    },
    "contact-executive.webp": {
        "needles": ["hero.webp", "portrait-casual.webp"],
        "ratio": (1, 1),
        "max_width": 900,
        "quality": 90,
    },
    "consulting-panel.webp": {
        "needles": ["panel-live.webp", "panel.webp"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
    "enterprise-stage.webp": {
        "needles": ["panel.webp", "panel-live.webp"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
}


def collect_sources() -> dict[str, bytes]:
    sources: dict[str, bytes] = {}

    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        for path in ROOT.rglob(ext):
            if path.parent == OUT:
                continue
            try:
                sources[path.name] = path.read_bytes()
            except OSError:
                pass

    hq = ROOT / "hq_media.zip"
    if hq.exists():
        try:
            with zipfile.ZipFile(hq) as zf:
                for name in zf.namelist():
                    if not name.endswith("/"):
                        sources[Path(name).name] = zf.read(name)
        except zipfile.BadZipFile:
            pass

    parts = sorted((ROOT / "payload_parts").glob("part_*.b64"))
    if parts:
        try:
            encoded = "".join(p.read_text(encoding="ascii") for p in parts)
            with zipfile.ZipFile(BytesIO(base64.b64decode(encoded))) as zf:
                for name in zf.namelist():
                    if not name.endswith("/"):
                        sources[Path(name).name] = zf.read(name)
        except (ValueError, zipfile.BadZipFile, OSError):
            pass

    return sources


def valid_image(data: bytes) -> bool:
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        return True
    except Exception:
        return False


def find_source(sources: dict[str, bytes], needles: list[str]) -> tuple[str, bytes]:
    for needle in needles:
        needle_l = needle.lower()
        # Prefer an exact basename before substring matching.
        for name, data in sources.items():
            if name.lower() == needle_l and valid_image(data):
                return name, data
        for name, data in sources.items():
            if needle_l in name.lower() and valid_image(data):
                return name, data
    raise RuntimeError(
        f"Could not find a valid source for {needles}. Available image names: "
        + ", ".join(sorted(sources))
    )


def crop_to_ratio(image: Image.Image, ratio: tuple[int, int]) -> Image.Image:
    target = ratio[0] / ratio[1]
    current = image.width / image.height
    if abs(current - target) < 0.002:
        return image
    if current > target:
        width = int(image.height * target)
        left = max(0, (image.width - width) // 2)
        return image.crop((left, 0, left + width, image.height))
    height = int(image.width / target)
    top = max(0, int((image.height - height) * 0.32))
    return image.crop((0, top, image.width, top + height))


def build() -> None:
    sources = collect_sources()
    if not sources:
        raise RuntimeError("No project source photography was found.")

    for output_name, spec in SPECS.items():
        source_name, raw = find_source(sources, spec["needles"])
        with Image.open(BytesIO(raw)) as source:
            image = source.convert("RGB")
            image = crop_to_ratio(image, spec["ratio"])
            if image.width > spec["max_width"]:
                height = round(image.height * spec["max_width"] / image.width)
                image = image.resize((spec["max_width"], height), Image.Resampling.LANCZOS)
            output = OUT / output_name
            image.save(output, "WEBP", quality=spec["quality"], method=6)
            pixels = image.width * image.height
            if pixels < 500_000:
                raise RuntimeError(f"{output_name} is below the website resolution floor: {image.size}")
            print(f"{output_name}: {image.width}x{image.height} <- {source_name}")


if __name__ == "__main__":
    build()
