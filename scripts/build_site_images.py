from __future__ import annotations

from pathlib import Path
from io import BytesIO
import base64
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)

# Build purpose-specific crops only from preserved source assets that meet the
# native-resolution floor. Never upscale a small source to satisfy the website.
SPECS = {
    "hero-executive.webp": {"needles": ["hero.webp", "portrait-casual.webp"], "ratio": (4, 3), "max_width": 1800, "quality": 88},
    "home-panel.webp": {"needles": ["panel-live.webp", "hero.webp"], "ratio": (16, 10), "max_width": 1800, "quality": 86},
    "impact-keynote.webp": {"needles": ["panel-live.webp", "hero.webp"], "ratio": (16, 10), "max_width": 1800, "quality": 86},
    "impact-ai-panel.webp": {"needles": ["panel-live.webp", "hero.webp"], "ratio": (16, 10), "max_width": 1800, "quality": 86},
    "thinking-panel.webp": {"needles": ["portrait-casual.webp", "hero.webp"], "ratio": (4, 5), "max_width": 1200, "quality": 88},
    "about-human.webp": {"needles": ["portrait-casual.webp", "hero.webp"], "ratio": (1, 1), "max_width": 1400, "quality": 88},
    "about-editorial.webp": {"needles": ["hero.webp", "portrait-casual.webp"], "ratio": (4, 5), "max_width": 1200, "quality": 88},
    "contact-executive.webp": {"needles": ["hero.webp", "portrait-casual.webp"], "ratio": (1, 1), "max_width": 900, "quality": 90},
    "consulting-panel.webp": {"needles": ["panel-live.webp", "hero.webp"], "ratio": (16, 10), "max_width": 1800, "quality": 86},
    "enterprise-stage.webp": {"needles": ["panel-live.webp", "hero.webp"], "ratio": (16, 10), "max_width": 1800, "quality": 86},
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


def image_info(data: bytes) -> tuple[int, int] | None:
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            return image.size
    except Exception:
        return None


def find_source(sources: dict[str, bytes], needles: list[str]) -> tuple[str, bytes]:
    # Honor semantic priority, but skip any source that is too small to display
    # crisply. This keeps resolution policy in the build rather than runtime.
    for needle in needles:
        needle_l = needle.lower()
        matches = []
        for name, data in sources.items():
            if name.lower() == needle_l or needle_l in name.lower():
                size = image_info(data)
                if size:
                    matches.append((size[0] * size[1], name, data, size))
        if matches:
            matches.sort(reverse=True, key=lambda x: x[0])
            pixels, name, data, size = matches[0]
            print(f"Source candidate {name}: {size[0]}x{size[1]}")
            if pixels >= 500_000:
                return name, data
    raise RuntimeError(f"No native high-resolution source found for {needles}")


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
            image = crop_to_ratio(source.convert("RGB"), spec["ratio"])
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
