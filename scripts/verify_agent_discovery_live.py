"""Verify deployed GitHub Pages AI discovery files and report branded readiness.

Read-only HTTP checks. An inaccessible branded root is a tracked infrastructure
requirement, not a reason to undo the live public Pages mirror.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PAGES = "https://airibeiro.github.io/careersite"
BRANDED = "https://jairribeiro.com"


def get(url: str, *, tries: int = 5, delay: int = 10):
    last_error = None
    for attempt in range(tries):
        try:
            with urlopen(Request(url, headers={"User-Agent": "JairPortfolioDiscoveryVerifier/1.0"}), timeout=30) as res:
                return res.status, res.headers.get("Content-Type", ""), res.read(2_000_000)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 < tries:
                time.sleep(delay)
    raise RuntimeError(f"Could not read {url}: {last_error}")


def verify_pages() -> None:
    paths = [
        ("/llms.txt", "text/plain"),
        ("/agents.md", "text/"),
        ("/agent/catalog.json", "application/json"),
    ]
    docs = {}
    for path, expected_type in paths:
        status, content_type, data = get(PAGES + path)
        if status != 200 or not content_type.lower().startswith(expected_type):
            raise AssertionError(f"{path}: expected HTTP 200 {expected_type}, got {status} {content_type}")
        decoded = data.decode("utf-8")
        if not decoded or "<iframe" in decoded.lower() or "<html" in decoded.lower():
            raise AssertionError("Unexpected page wrapper at " + path)
        docs[path] = decoded
        print("PASS", path, status, content_type, len(data), "bytes")

    if "Jair Ribeiro" not in docs["/llms.txt"]:
        raise AssertionError("llms.txt does not name the publisher")
    if PAGES + "/agent/catalog.json" not in docs["/llms.txt"]:
        raise AssertionError("llms.txt does not link to reachable static index")
    catalogue = json.loads(docs["/agent/catalog.json"])
    if catalogue.get("catalogue_status") != "complete":
        raise AssertionError("Static public discovery index must have complete publication state")
    if catalogue.get("content_policy") != "summary_only":
        raise AssertionError("Static mirror must never contain full CMS HTML")
    if catalogue.get("site") != BRANDED or catalogue.get("count", 0) < 10:
        raise AssertionError("Unexpected canonical site or truncated catalogue")
    items = catalogue.get("content") or []
    if len(items) != catalogue["count"]:
        raise AssertionError("Catalogue count disagrees with item array")
    if not all(item["url"].startswith(BRANDED + "/") for item in items):
        raise AssertionError("Canonical destination escaped the branded domain")
    if not all(item["markdown_url"].startswith(PAGES + "/agent/content/") for item in items):
        raise AssertionError("Markdown resource escaped public Pages mirror")
    if not any(item["access"] == "premium" for item in items):
        raise AssertionError("Published CMS premium access state missing")
    if any(item["type"] == "executive_briefing" and item["access"] != "premium" for item in items):
        raise AssertionError("Premium briefing incorrectly marked open")

    timestamp = datetime.fromisoformat(catalogue["generated_at"].replace("Z", "+00:00"))
    if abs((datetime.now(timezone.utc) - timestamp).total_seconds()) > 4 * 3600:
        raise AssertionError("Discovery snapshot is too stale for this deployment")

    sample = items[0]
    status, content_type, content = get(sample["markdown_url"])
    text = content.decode("utf-8")
    if status != 200 or not content_type.lower().startswith(("text/plain", "text/markdown")):
        raise AssertionError("Published Markdown is missing or wrongly served: " + content_type)
    if "# " + sample["title"] not in text or "## Public executive summary" not in text:
        raise AssertionError("Markdown public summary is incomplete")
    if "## Full public edition" in text:
        raise AssertionError("Static Pages export unexpectedly contained complete content")
    print("PASS", "/agent/content/" + sample["slug"] + ".md", content_type)
    print("Verified static agent catalogue for", len(items), "published items.")


def probe_branded() -> bool:
    try:
        status, ctype, body = get(BRANDED + "/llms.txt", tries=1)
        correct = status == 200 and ctype.lower().startswith("text/plain") and body.startswith(b"# Jair Ribeiro")
        print("Branded root:", status, ctype,
              "AGENT DISCOVERY READY" if correct else "NOT READY: requires path-aware HTTP routing")
        return correct
    except Exception as exc:
        print("Branded root: UNVERIFIED", type(exc).__name__,
              "— path-aware DNS/hosting action remains outstanding")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-branded", action="store_true")
    args = parser.parse_args()
    verify_pages()
    if args.require_branded and not probe_branded():
        raise SystemExit("Branded root is not yet serving raw llms.txt")
    if not args.require_branded:
        probe_branded()


if __name__ == "__main__":
    main()
