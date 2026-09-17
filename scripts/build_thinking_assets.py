from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thinking_articles import ARTICLES  # noqa: E402
from thinking_social import build_article_asset_manifest  # noqa: E402

MANIFEST_PATH = ROOT / "static" / "thinking" / "article-assets.json"
EXPECTED_SIZE = (1200, 627)


def build(*, check: bool = False) -> dict[str, object]:
    manifest = build_article_asset_manifest()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if check:
        articles = manifest.get("articles", [])
        if manifest.get("count") != len(ARTICLES) or len(articles) != len(ARTICLES):
            raise SystemExit("Article asset count does not match the publishing registry")

        slugs: set[str] = set()
        signatures: set[str] = set()
        for row in articles:
            slug = str(row["slug"])
            if slug in slugs:
                raise SystemExit(f"Duplicate article asset slug: {slug}")
            slugs.add(slug)

            signature = str(row["signature"])
            if not signature or signature in signatures:
                raise SystemExit(f"Invalid/non-unique article image signature: {slug}")
            signatures.add(signature)

            image_path = ROOT / str(row["image"])
            share_path = ROOT / str(row["share_page"])
            signature_path = image_path.with_suffix(".sha256")
            for path in (image_path, share_path, signature_path):
                if not path.is_file():
                    raise SystemExit(f"Missing generated article asset: {path}")

            with Image.open(image_path) as image:
                if image.format != "PNG":
                    raise SystemExit(f"{slug}: expected PNG, got {image.format}")
                if image.size != EXPECTED_SIZE:
                    raise SystemExit(f"{slug}: expected {EXPECTED_SIZE}, got {image.size}")

            html = share_path.read_text(encoding="utf-8")
            if f"/social/{slug}.png" not in html:
                raise SystemExit(f"{slug}: crawler page does not reference its generated image")
            if 'property="og:image"' not in html:
                raise SystemExit(f"{slug}: crawler page is missing og:image")

        print(
            f"Built and validated {len(articles)} article social cards "
            f"at {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}."
        )

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate social/share assets for every published Thinking article."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if any registry article is missing a valid generated asset.",
    )
    args = parser.parse_args()
    build(check=args.check)


if __name__ == "__main__":
    main()
