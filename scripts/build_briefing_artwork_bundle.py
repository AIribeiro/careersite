#!/usr/bin/env python3
"""Package source-approved infographic files for the shared briefing reader.

Example:
python scripts/build_briefing_artwork_bundle.py \
 --slug example-ai-decision --article-fingerprint <64-sha256> \
 --revision 2026-11-06-r1 --desktop approved-desktop.png \
 --mobile approved-mobile.png --pdf approved-a4.pdf \
 --heading "The executive decision" --deck "The source-verified takeaway"

Store the generated static/briefing-artwork/<slug>/ directory in the repo,
complete CMS approval, and verify the deployed reader before claiming success.
The tool does not mutate CMS or approve artwork.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import sys

from PIL import Image, ImageOps
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from briefing_approved_asset_renderer import (
    MAX_INLINE_BYTES, ArtworkError, _slug, validate_bundle, load_bundle
)


def _webp_image(source: Path, dest: Path) -> dict:
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        if image.width < 600 or image.height < 450:
            raise ValueError(f"Artwork too small for a premium executive briefing: {source}")
        with BytesIO() as output:
            image.save(output, format="WEBP", quality=85, method=5)
            data = output.getvalue()
    if not (1000 < len(data) < MAX_INLINE_BYTES):
        raise ValueError(f"Artwork exceeds the iPad-safe inline image budget: {source} ({len(data)} bytes)")
    dest.write_bytes(data)
    return {
        "file": dest.name, "sha256": hashlib.sha256(data).hexdigest(),
        "width": image.width, "height": image.height,
        "bytes": len(data),
    }


def _pdf(source: Path, dest: Path) -> dict:
    data = source.read_bytes()
    reader = PdfReader(BytesIO(data), strict=True)
    if not reader.pages:
        raise ValueError("Infographic PDF has no pages")
    for number, page in enumerate(reader.pages, start=1):
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        # ISO A4: 595.3 × 841.9pt; allow modest print box tolerances.
        if not (589 < min(w, h) < 601 and 836 < max(w, h) < 848):
            raise ValueError(f"PDF page {number} is not A4 ({w:.1f} × {h:.1f})")
    dest.write_bytes(data)
    return {
        "file": dest.name, "sha256": hashlib.sha256(data).hexdigest(),
        "pages": len(reader.pages), "bytes": len(data),
    }


def bundle(*, slug: str, article_fingerprint: str, revision: str, desktop: Path,
           mobile: Path, pdf: Path, heading: str, deck: str,
           out_root: Path | None = None) -> dict:
    slug = _slug(slug)
    if not re.fullmatch("[0-9a-f]{64}", article_fingerprint):
        raise ValueError("Expected SHA-256 article fingerprint (64 hex chars)")
    if not re.fullmatch("[A-Za-z0-9][A-Za-z0-9._-]{0,79}", revision):
        raise ValueError("Invalid immutable artwork revision")
    if not heading.strip() or not deck.strip():
        raise ValueError("Artwork heading and deck are required")
    out_root = (out_root or ROOT / "static" / "briefing-artwork").resolve()
    target = out_root / slug
    # Each revision is a guarded release; don't overwrite approved artifacts.
    if target.exists():
        raise FileExistsError(f"Existing bundle must be reviewed/revisioned: {target}")
    target.mkdir(parents=True)
    try:
        d = _webp_image(desktop, target / "desktop.webp")
        m = _webp_image(mobile, target / "mobile.webp")
        p = _pdf(pdf, target / "infographic.pdf")
        manifest = {
            "schema_version": 1, "slug": slug,
            "article_fingerprint": article_fingerprint,
            "revision": revision, "heading": heading.strip(), "deck": deck.strip(),
            "desktop": d, "mobile": m, "pdf": p,
            "release_note": "Exact source content and premium design require editorial approval in CMS.",
        }
        (target / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        verified = load_bundle(slug, asset_root=out_root)
        if verified is None:
            raise ArtworkError("Generated manifest cannot be loaded")
        validate_bundle(verified)
        return manifest
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--article-fingerprint", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--desktop", type=Path, required=True)
    parser.add_argument("--mobile", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--heading", required=True)
    parser.add_argument("--deck", required=True)
    parser.add_argument("--out-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(bundle(
        slug=args.slug, article_fingerprint=args.article_fingerprint,
        revision=args.revision, desktop=args.desktop, mobile=args.mobile,
        pdf=args.pdf, heading=args.heading, deck=args.deck,
        out_root=args.out_root,
    ), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
