from __future__ import annotations

from io import BytesIO
from pathlib import Path
import base64
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)

# These are the exact original photographs selected for the public site.
# They already exist in the repository's preserved source-media bundles.
# Public derivatives keep the source pixel dimensions; CSS handles display crops.
SPECS = {
    "jair-hero-executive.webp": "1700157848740",
    "jair-ai-panel.webp": "1700157848740",
    "jair-leadership-workshop.webp": "54907620908",
    "jair-panel-dialogue.webp": "54907620908",
    "jair-thinking-panel.webp": "profile_red_bg",
    "jair-about-bw.webp": "IMG_8281",
}

QUALITY = 92


def collect_sources() -> dict[str, bytes]:
    sources: dict[str, bytes] = {}

    # Unpacked original photography, when present.
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        for path in ROOT.rglob(ext):
            if path.parent == OUT:
                continue
            try:
                sources[path.name] = path.read_bytes()
            except OSError:
                pass

    # Preserved high-resolution media from the earlier site.
    hq = ROOT / "hq_media.zip"
    if hq.exists():
        try:
            with zipfile.ZipFile(hq) as zf:
                for name in zf.namelist():
                    if not name.endswith("/"):
                        sources[Path(name).name] = zf.read(name)
        except zipfile.BadZipFile:
            pass

    # Original embedded project payload.
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


def find_source(sources: dict[str, bytes], needle: str) -> tuple[str, bytes]:
    needle_l = needle.lower()
    matches: list[tuple[int, str, bytes]] = []
    for name, data in sources.items():
        if needle_l not in name.lower():
            continue
        try:
            with Image.open(BytesIO(data)) as image:
                image.verify()
            with Image.open(BytesIO(data)) as image:
                pixels = image.width * image.height
            matches.append((pixels, name, data))
        except Exception:
            continue

    if not matches:
        raise RuntimeError(f"Could not find valid original photography matching {needle!r}")

    matches.sort(reverse=True, key=lambda item: item[0])
    _, name, data = matches[0]
    return name, data


def build() -> None:
    sources = collect_sources()
    if not sources:
        raise RuntimeError("No project source photography was found.")

    for output_name, needle in SPECS.items():
        source_name, raw = find_source(sources, needle)
        with Image.open(BytesIO(raw)) as source:
            # Preserve the original pixel dimensions. No upscaling, resizing or
            # destructive baked-in crop; page CSS controls framing responsively.
            image = source.convert("RGB")
            output = OUT / output_name
            image.save(output, "WEBP", quality=QUALITY, method=6)
            width, height = image.size
            if width * height < 1_000_000:
                raise RuntimeError(
                    f"{output_name} is below the leadership-photo resolution floor: {width}x{height}"
                )
            print(f"{output_name}: {width}x{height} <- {source_name}")


if __name__ == "__main__":
    build()
