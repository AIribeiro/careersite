"""Publish meaningful, verified additions to the homepage What's New panel.

Every deployment triggers evaluation. Only new public pages, new public
credentials, and explicitly approved announcements are eligible. Routine edits,
refactoring, styling, CI, data refreshes and deployment churn are never news.
Published CMS content and market editions are checked by the browser feed.
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
                # A dict may contain one dynamic value (HOME_TITLE or
                # HOME_DESCRIPTION). Read the remaining literal entries
                # without importing the site's runtime or evaluating code.
                if not isinstance(node.value, ast.Dict):
                    return None
                values = {}
                for key, value in zip(node.value.keys, node.value.values):
                    try:
                        parsed_key = ast.literal_eval(key)
                        parsed_value = ast.literal_eval(value)
                    except (ValueError, SyntaxError, TypeError):
                        continue
                    if isinstance(parsed_key, str) and isinstance(parsed_value, str):
                        values[parsed_key] = parsed_value
                return values
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
        # A demo/verification route or account utility must not outrank the
        # actual research publication merely because its page was added last.
        if route in {"home", "briefing", "analytics", "admin", "certifications",
                     "enterprise", "transformation", "governance", "consulting",
                     "privacy", "advisory-access", "advisory-market-demo"} or route.endswith("-demo"):
            continue
        description = str(descriptions.get(route) or "").strip()
        # Do not advertise an unexplained route with a machine placeholder.
        # Editorial description is a prerequisite for homepage promotion.
        if len(description) < 60:
            continue
        title = new_titles.get(route) or route.replace("-", " ").title()
        title = title.split(" | ")[0].strip()
        events.append({
            "key": "page:" + route,
            "type": "New page",
            "title": title,
            "description": description[:320],
            "date": timestamp,
            "href": "?page=" + route,
            "cta": (
                "Read the executive review" if route == "advisory-market-signals"
                else "See speaking & publications" if route == "presence"
                else "Explore the page"
            ),
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



# Meaningful updates to an existing page must be explicitly declared. A release
# cannot be inferred from an arbitrary Git diff: changing CSS says nothing about
# the visitor benefit, and guessing produces misleading homepage announcements.
ANNOUNCEMENTS = "data/portfolio_announcements.json"
ANNOUNCEMENT_TYPES = {"New service", "New resource", "Page update", "Executive research"}
DISALLOWED_DESTINATIONS = {
    "home", "admin", "analytics", "privacy", "advisory-access",
    "advisory-market-demo", "briefing",
}
DISALLOWED_COPY = {
    "latest portfolio improvements",
    "explore the portfolio",
    "explore the update",
    "view the update",
    "discover the newly published portfolio page.",
    "updates to the portfolio are available across its pages and services.",
}


def _announcement_rows(revision: str) -> dict[str, dict]:
    try:
        source = json.loads(git_file(revision, ANNOUNCEMENTS))
    except (TypeError, ValueError):
        return {}
    if not isinstance(source, dict) or not isinstance(source.get("items"), list):
        return {}
    rows = {}
    for row in source["items"]:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            rows[row["id"]] = row
    return rows


def declared_release_items(previous: str, current: str, issued_at: str) -> list[dict[str, str]]:
    """Publish only newly approved, specific, visitor-facing release entries."""
    old = _announcement_rows(previous)
    new = _announcement_rows(current)
    routes = set(constant(git_file(current, "main.py"), "PUBLIC_VALID") or ())
    issued = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    result = []
    for release_id, row in new.items():
        if (
            row.get("status") != "published"
            or (release_id in old and old[release_id].get("status") == "published")
        ):
            continue
        route = str(row.get("page") or "").strip()
        title = str(row.get("title") or "").strip()
        description = str(row.get("description") or "").strip()
        cta = str(row.get("cta") or "").strip()
        item_type = str(row.get("type") or "").strip()
        if (
            not release_id or len(release_id) > 80
            or not all(ch.isalnum() or ch in "-_" for ch in release_id)
            or route not in routes or route in DISALLOWED_DESTINATIONS
            or item_type not in ANNOUNCEMENT_TYPES
            or not 12 <= len(title) <= 110
            or not 70 <= len(description) <= 340
            or not 8 <= len(cta) <= 75
            or title.lower() in DISALLOWED_COPY
            or description.lower() in DISALLOWED_COPY
            or cta.lower() in DISALLOWED_COPY
        ):
            continue
        result.append({
            "key": "editorial:" + release_id,
            "type": item_type,
            "title": title,
            "description": description,
            "date": issued.isoformat(),
            "href": "?page=" + route,
            "cta": cta,
        })
    return result


def update_feed(previous: str, current: str) -> int:
    commit_date = subprocess.check_output(
        ["git", "show", "-s", "--format=%cI", current],
        cwd=ROOT, text=True, timeout=10,
    ).strip()
    new = new_release_items(previous, current, commit_date)
    new.extend(declared_release_items(previous, current, commit_date))
    # All changes are checked, but maintenance cannot generate an announcement.
    if not new:
        return 0
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    old = feed.get("items", [])
    seen = {str(item.get("key")) for item in old}
    additions = [item for item in new if item["key"] not in seen]
    if not additions:
        return 0
    feed["items"] = sorted(old + additions, key=lambda item: item["date"], reverse=True)[:80]
    FEED.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(additions)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: sync_portfolio_releases.py <previous-sha> <current-sha>")
    print(f"New public releases: {update_feed(sys.argv[1], sys.argv[2])}")
