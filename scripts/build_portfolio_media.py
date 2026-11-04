"""Build page-sized, cacheable WebP versions of curated portfolio photographs.

The canonical originals remain in /images and are always the fallback.
Only JPEG photographs are converted; text-heavy credential artwork is
not lossily recompressed. No image processing occurs during page rendering.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps
import re

ROOT=Path(__file__).resolve().parents[1]
IMAGES=ROOT/"images"
MEDIA_SOURCE=(ROOT/"src/site_media.py").read_text(encoding="utf-8")
SOURCES=tuple(dict.fromkeys(
    (name,int(width))
    for name,width in re.findall(r'_uri\("([^"]+)",\s*(\d+)\)',MEDIA_SOURCE)
))
def generated_path(name: str,width: int) -> Path:
    return IMAGES/"optimized"/f"{name}.{width}.webp"

def build() -> tuple[int,int,int]:
    made=0;skipped=0;bytes_saved=0
    for name,width in SOURCES:
        source=IMAGES/name
        if not source.is_file() or source.suffix.lower() not in {".jpg",".jpeg"}:
            skipped+=1
            continue
        output=generated_path(name,width)
        output.parent.mkdir(parents=True,exist_ok=True)
        with Image.open(source) as original:
            prepared=ImageOps.exif_transpose(original)
            if prepared.mode not in {"RGB","RGBA"}:
                prepared=prepared.convert("RGB")
            prepared.thumbnail((width,2048),Image.Resampling.LANCZOS)
            prepared.save(output,"WEBP",quality=84,method=6)
        before=source.stat().st_size
        after=output.stat().st_size
        if after>=int(before*.93):
            output.unlink()
            skipped+=1
            continue
        with Image.open(output) as check:
            assert check.format=="WEBP"
            assert check.width<=width
        made+=1
        bytes_saved+=before-after
        print(f"{name} @ {width}px: {before:,} -> {after:,} bytes")
    return made,skipped,bytes_saved

if __name__=="__main__":
    made,skipped,saved=build()
    assert made>=6, f"Expected curated WebP output, only {made} created"
    print(f"Optimized {made} photographs, skipped {skipped}; reduced transferred original bytes by {saved:,}")
