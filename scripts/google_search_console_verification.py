"""Prepare verifiable Google Search Console ownership for a Pages URL-prefix.

Only first-party GitHub Pages assets are changed. Ownership verification is
not Google sitemap submission; that requires authenticated Search Console.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re

_GOOGLE_FILE = re.compile(r"^google[a-zA-Z0-9]{10,80}\.html$")
_GOOGLE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{10,256}$")


def prepare(directory: Path, *, file_name: str = "", meta_token: str = "") -> dict:
    """Place Google's exact proof file or meta tag on the Pages project root.

    Neither verification method changes URLs, Premium reader permissions, nor
    site content. Invalid input fails the deployment instead of writing HTML.
    """
    if file_name and not _GOOGLE_FILE.fullmatch(file_name):
        raise ValueError("Google HTML verification filename must look like google<token>.html")
    if meta_token and not _GOOGLE_TOKEN.fullmatch(meta_token):
        raise ValueError("Invalid Google HTML meta verification token")
    if not file_name and not meta_token:
        print("GOOGLE_SEARCH_CONSOLE_SETUP_REQUIRED: No ownership verification token configured.")
        return {"configured": False, "proof_file": None, "meta": False}
    if not directory.is_dir() or not (directory / "index.html").is_file():
        raise FileNotFoundError("Pages artifact must exist before adding verification")

    if file_name:
        (directory / file_name).write_text(
            "google-site-verification: " + file_name + "\n", encoding="utf-8"
        )
        print("GOOGLE_SEARCH_CONSOLE_PROOF_READY: " + file_name)

    if meta_token:
        name = '<meta name="google-site-verification" content="' + escape(meta_token, quote=True) + '">'
        for page in (directory / "index.html", directory / "discover/index.html"):
            if not page.is_file():
                continue
            html = page.read_text(encoding="utf-8")
            if name in html:
                continue
            if "</head>" not in html:
                raise ValueError("Cannot add Google verification tag outside <head>: " + str(page))
            page.write_text(html.replace("</head>", name + "\n</head>", 1), encoding="utf-8")
        print("GOOGLE_SEARCH_CONSOLE_META_READY: Pages HTML head.")

    return {"configured": True, "proof_file": file_name or None, "meta": bool(meta_token)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--file-name", default="")
    parser.add_argument("--meta-token", default="")
    args = parser.parse_args()
    prepare(Path(args.output), file_name=args.file_name, meta_token=args.meta_token)


if __name__ == "__main__":
    main()
