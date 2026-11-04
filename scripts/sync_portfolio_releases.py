"""Generate public release events from newly added routes and credentials.

Invoked on a main-branch push by the release-feed workflow. Only additions
qualify: routine edits, CI changes, updated publication copy, and private admin
work never appear as new releases. CMS issues are tracked live on the Home page.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "data" / "portfolio_release_feed.json"
CREDENTIAL_TABLES = {"FLAGSHIP", "CREDLY_BADGES", "ACCREDIBLE_BADGES"}


def git_file(rev: str, path: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "show", f"{rev}:{path}"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL, timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return ""


def constant(source: str, name: str):
    if not source.strip():
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, SyntaxError, TypeError):
                return None
    return None


def credential_rows(source: str) -> dict[str, dict[str, str]]:
    """Use fields only; image variables in credential cards cannot be literal-eval'ed."""
    if not source.strip():
        return {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    result = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        if not any(isinstance(t, ast.Name) and t.id in CREDENTIAL_TABLES for t in node.targets):
            continue
        for item in node.value.elts:
            if not isinstance(item, ast.Dict):
                continue
            entry = {}
            for key, value in zip(item.keys, item.values):
                try:
                    field = ast.literal_eval(key)
                    if field in {"title", "issuer", "date", "credential"}:
                        value_text = ast.literal_eval(value)
                        if isinstance(value_text, str):
                            entry[field] = value_text
                except (ValueError, SyntaxError, TypeError):
                    continue
            if entry.get("title") and entry.get("issuer"):
                slug = (entry.get("credential") or entry["issuer"] + ":" + entry["title"]).casefold()
                result[slug] = entry
    return result


def new_release_items(previous: str, current: str, issued_at: str) -> list[dict[str, str]]:
    date = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    timestamp = date.isoformat()

    old_routes = set(constant(git_file(previous, "main.py"), "PUBLIC_VALID") or ())
    new_routes = set(constant(git_file(current, "main.py"), "PUBLIC_VALID") or ())
    new_titles = constant(git_file(current, "main.py"), "TITLES") or {}
    descriptions = constant(git_file(current, "src/site_meta.py"), "DESCRIPTIONS") or {}
    events = []
    for route in sorted(new_routes - old_routes):
        # Skip aliases, CMS readers and the private admin workspace.
        if route in {"home", "briefing", "analytics", "admin", "certifications",
                     "enterprise", "transformation", "governance", "consulting"}:
            continue
        title = new_titles.get(route) or route.replace("-", " ").title()
        title = title.split(" | ")[0].strip()
        events.append({
            "key": "page:" + route,
            "type": "New page",
            "title": title,
            "description": descriptions.get(route, "Discover the newly published portfolio page.")[:220],
            "date": timestamp,
            "href": "?page=" + route,
            "cta": "Explore the page",
        })

    old_credentials = credential_rows(git_file(previous, "src/page_certifications.py"))
    new_credentials = credential_rows(git_file(current, "src/page_certifications.py"))
    for key in sorted(set(new_credentials) - set(old_credentials)):
        credential = new_credentials[key]
        events.append({
            "key": "credential:" + key,
            "type": "Certification",
            "title": credential["title"],
            "description": credential["issuer"] + " · Newly added to my credentials",
            "date": timestamp,
            "href": "?page=about#credentials-evidence",
            "cta": "Explore the credential",
        })
    return events


def update_feed(previous: str, current: str) -> int:
    commit_date = subprocess.check_output(
        ["git", "show", "-s", "--format=%cI", current],
        cwd=ROOT, text=True, timeout=10,
    ).strip()
    new = new_release_items(previous, current, commit_date)
    if not new:
        return 0
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    old = feed.get("items", [])
    seen = {str(item.get("key")) for item in old}
    additions = [item for item in new if item["key"] not in seen]
    if not additions:
        return 0
    feed["items"] = sorted(old + additions, key=lambda item: item["date"], reverse=True)[:60]
    FEED.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(additions)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: sync_portfolio_releases.py <previous-sha> <current-sha>")
    print(f"New public releases: {update_feed(sys.argv[1], sys.argv[2])}")
