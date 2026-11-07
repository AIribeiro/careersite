#!/usr/bin/env python3
"""Release the owner's exact approved 15-outcome image as a one-page A4 PDF.

The approved master PNG is source art, not a design reference to recreate.
Desktop, mobile and PDF are generated from the SAME reviewed raster.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from shutil import copyfile

from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
APPROVED_SOURCE = ROOT / "assets" / "approved_infographics" / "15-ways-ai-can-change-your-business.png"
EXPECTED_SOURCE_SHA256 = "9feafc146e2b54d4dd4bef9bc87672ee50cf503ca5af20d7ddf0aaf62e4d7ec1"
EXPECTED_SIZE = (1055, 1491)


def build(out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = APPROVED_SOURCE.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Approved PNG source changed: {actual_sha}")
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Approved source is not a PNG image")

    with Image.open(APPROVED_SOURCE) as opened:
        if opened.size != EXPECTED_SIZE or opened.format != "PNG":
            raise ValueError(f"Wrong approved image geometry/type: {opened.size}, {opened.format}")
        opened.verify()

    # Identical source composition for both responsive variants. The shared
    # asset packager converts these into bounded WebP files for embedded HTML.
    for name in ("desktop.png", "mobile.png"):
        copyfile(APPROVED_SOURCE, out / name)
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA256

    with Image.open(APPROVED_SOURCE) as opened:
        original = ImageOps.exif_transpose(opened).convert("RGB")
        page_w, page_h = A4
        scale = min(page_w / original.width, page_h / original.height)
        draw_w = original.width * scale
        draw_h = original.height * scale
        pdf_path = out / "infographic.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=A4, pageCompression=1)
        c.setTitle("15 Ways AI Can Change Your Business | Executive AI Briefing")
        c.setAuthor("Jair Ribeiro")
        c.setSubject("Original approved infographic; single A4 page")
        c.drawImage(ImageReader(original),
                    (page_w - draw_w) / 2, (page_h - draw_h) / 2,
                    draw_w, draw_h)
        c.showPage()
        c.save()

    reader = PdfReader(str(pdf_path), strict=True)
    if len(reader.pages) != 1:
        raise ValueError(f"Must be exactly one A4 page, got {len(reader.pages)}")
    page = reader.pages[0]
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    if not (594 < w < 596 and 841 < h < 843):
        raise ValueError("Expected portrait A4 page geometry")
    xobjects = page.get("/Resources").get_object().get("/XObject")
    if not xobjects or len(xobjects.get_object()) != 1:
        raise ValueError("Expected precisely one full-page approved image")
    return {
        "approved_png_sha256": actual_sha,
        "page_count": len(reader.pages),
        "a4_points": [w, h],
        "source_dimensions": list(EXPECTED_SIZE),
        "pdf_bytes": pdf_path.stat().st_size,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    import json
    print(json.dumps(build(args.output), indent=2))
