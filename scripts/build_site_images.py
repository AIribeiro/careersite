from __future__ import annotations

from pathlib import Path
from io import BytesIO
import base64
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)

# Canonical website assets built from the original project photography already
# stored in the repository bundles. Each output has one communication purpose.
SPECS = {
    "hero-executive.webp": {
        "needles": ["54907620908", "54907647524"],
        "ratio": (4, 3),
        "max_width": 2000,
        "quality": 86,
    },
    "impact-keynote.webp": {
        "needles": ["IMG_0777"],
        "ratio": (16, 10),
        "max_width": 1900,
        "quality": 84,
    },
    "impact-ai-panel.webp": {
        "needles": ["1700157848740"],
        "ratio": (16, 10),
        "max_width": 1900,
        "quality": 86,
    },
    "thinking-panel.webp": {
        "needles": ["IMG_8281"],
        "ratio": (4, 5),
        "max_width": 1200,
        "quality": 86,
    },
    "about-books.webp": {
        "needles": ["IMG_20220718_155712_485"],
        "ratio": (1, 1),
        "max_width": 1600,
        "quality": 86,
    },
    "about-bw.webp": {
        "needles": ["pixelup_1683528862014"],
        "ratio": (4, 5),
        "max_width": 1500,
        "quality": 86,
    },
    "contact-executive.webp": {
        "needles": ["face_profile_studio", "profile_white_bg"],
        "ratio": (1, 1),
        "max_width": 900,
        "quality": 88,
    },
    "consulting-panel.webp": {
        "needles": ["54907647524"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
    "enterprise-stage.webp": {
        "needles": ["profile_red_bg", "f1d957ff"],
        "ratio": (16, 10),
        "max_width": 1800,
        "quality": 86,
    },
}


def collect_sources() -> dict[str, bytes]:
    sources: dict[str, bytes] = {}

    # Any unpacked source photography committed alongside the app.
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        for path in ROOT.rglob(ext):
            if "images" in path.parts and path.parent == OUT:
                continue
            try:
                sources[path.name] = path.read_bytes()
            except OSError:
                pass

    # High-resolution media bundle from the previous site implementation.
    hq = ROOT / "hq_media.zip"
    if hq.exists():
        try:
            with zipfile.ZipFile(hq) as zf:
                for name in zf.namelist():
                    if not name.endswith("/"):
                        sources[Path(name).name] = zf.read(name)
        except zipfile.BadZipFile:
            pass

    # Main embedded repository payload.
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


def find_source(sources: dict[str, bytes], needles: list[str]) -> tuple[str, bytes]:
    for needle in needles:
        needle_l = needle.lower()
        for name, data in sources.items():
            if needle_l in name.lower():
                try:
                    with Image.open(BytesIO(data)) as image:
                        image.verify()
                    return name, data
                except Exception:
                    continue
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
    # Slight top bias keeps faces and stage context in frame on portrait sources.
    top = max(0, int((image.height - height) * 0.35))
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
