"""Detect changed public discovery pages and optionally notify IndexNow.

IndexNow notifies participating search engines, NOT ChatGPT directly.
Every URL is on the final Pages host and points to a public summary page.
Never submit Reader URLs or full editions. A verified IndexNow key provided
via GitHub Actions secret INDEXNOW_KEY is required for network submissions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://airibeiro.github.io/careersite"
STATE_PATH = BASE + "/agent/publication-state.json"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
_KEY = re.compile(r"^[a-zA-Z0-9-]{8,128}$")
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,148}[a-z0-9])?$")


def _read(url: str, *, timeout: int = 15) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "JairPortfolioDiscoveryPublisher/1.0"}), timeout=timeout) as res:
        if res.status != 200:
            raise RuntimeError("Unexpected remote status " + str(res.status))
        return res.read(1_000_000)


def snapshot() -> dict:
    try:
        data = json.loads(_read(STATE_PATH))
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unknown previous state format")
        if data.get("canonical_discovery_base") != BASE:
            raise ValueError("Mismatching discovery host")
        if not isinstance(data.get("records"), dict):
            raise ValueError("Invalid previous record manifest")
        return {"status": "complete", "records": data["records"]}
    except HTTPError as exc:
        if exc.code == 404:
            print("PREVIOUS_STATE absent — first publication of change tracking")
            return {"status": "bootstrap", "records": {}}
        print("PREVIOUS_STATE unavailable: HTTP", exc.code)
    except (URLError, OSError, ValueError, TimeoutError) as exc:
        print("PREVIOUS_STATE unavailable:", type(exc).__name__)
    return {"status": "unavailable", "records": {}}


def diff(previous: dict, current: dict) -> dict:
    state = previous.get("status")
    if state not in ("complete", "bootstrap"):
        return {"version": 1, "status": "unavailable", "added": 0, "updated": 0,
                "removed": 0, "changed_urls": []}
    if current.get("version") != 1 or current.get("canonical_discovery_base") != BASE:
        raise ValueError("Unexpected generated publication state")
    old = previous.get("records", {})
    new = current.get("records", {})
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise ValueError("Invalid manifest structure")
    if not all(_SLUG.fullmatch(str(k)) for k in (list(old) + list(new))):
        raise ValueError("Unexpected slug in tracked state")
    added = sorted(set(new) - set(old))
    updated = sorted(k for k in (set(new) & set(old)) if old[k] != new[k])
    removed = sorted(set(old) - set(new))
    urls = [BASE + "/discover/" + slug + "/" for slug in sorted(set(added + updated + removed))]
    return {
        "version": 1, "status": state, "added": len(added), "updated": len(updated),
        "removed": len(removed), "changed_urls": urls,
    }


def _validate_changed_urls(report: dict) -> list[str]:
    if report.get("version") != 1 or report.get("status") not in ("complete", "bootstrap"):
        return []
    urls = report.get("changed_urls", [])
    if not isinstance(urls, list) or len(urls) > 2000:
        raise ValueError("Unexpected changed URL list")
    if any(not isinstance(url, str) or not url.startswith(BASE + "/discover/") for url in urls):
        raise ValueError("Notification URL outside public discovery page prefix")
    return urls


def create_key_file(output: Path, key: str) -> None:
    if not key:
        print("INDEXNOW_SETUP_REQUIRED: GitHub Actions INDEXNOW_KEY secret is not configured")
        return
    if not _KEY.fullmatch(key):
        raise ValueError("Invalid IndexNow key format")
    output.mkdir(parents=True, exist_ok=True)
    (output / (key + ".txt")).write_text(key + "\n", encoding="utf-8")
    print("INDEXNOW_VERIFICATION_FILE prepared in Pages artifact")


def notify(report: dict, key: str) -> int:
    urls = _validate_changed_urls(report)
    if not key:
        print("INDEXNOW_PENDING_SETUP — no INDEXNOW_KEY secret; no notifications sent")
        return 0
    if not _KEY.fullmatch(key):
        raise ValueError("Invalid configured IndexNow key format")
    if not urls:
        print("INDEXNOW_NO_CHANGES — nothing to notify")
        return 0
    location = BASE + "/" + key + ".txt"
    if _read(location).decode("utf-8").strip() != key:
        raise ValueError("Key not verified at final public Pages host")
    payload = {
        "host": "airibeiro.github.io",
        "key": key,
        "keyLocation": location,
        "urlList": urls,
    }
    request = Request(
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "User-Agent": "JairPortfolioDiscoveryPublisher/1.0"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as res:
            response = res.status
    except HTTPError as exc:
        response = exc.code
    if response not in (200, 202):
        raise RuntimeError("IndexNow refused notification with HTTP " + str(response))
    print("INDEXNOW_ACCEPTED", response, "published summary URL notifications:", len(urls))
    print("Search indexing and ChatGPT discovery are not guaranteed.")
    return len(urls)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("snapshot", "diff", "write-key", "notify"))
    p.add_argument("--output", default="")
    p.add_argument("--previous", default="")
    p.add_argument("--current", default="")
    p.add_argument("--report", default="")
    p.add_argument("--key", default="")
    args = p.parse_args()
    if args.mode == "snapshot":
        Path(args.output).write_text(json.dumps(snapshot()) + "\n", encoding="utf-8")
    elif args.mode == "diff":
        previous = json.loads(Path(args.previous).read_text(encoding="utf-8"))
        current = json.loads(Path(args.current).read_text(encoding="utf-8"))
        report = diff(previous, current)
        Path(args.output).write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
        print("DISCOVERY_CHANGE_REPORT:", {k: report[k] for k in ("status", "added", "updated", "removed")})
    elif args.mode == "write-key":
        create_key_file(Path(args.output), args.key)
    elif args.mode == "notify":
        report = json.loads(_read(args.report))
        notify(report, args.key)


if __name__ == "__main__":
    main()
