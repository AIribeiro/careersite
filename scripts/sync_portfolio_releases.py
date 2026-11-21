"""Generate public What's New events from portfolio deployments.

Capture new pages/credentials and subsequent code, media, configuration or
publication changes. Updates never require editing the Home page by hand.
Internal-only commits are safely presented as a generic portfolio update,
without exposing private content or Git commit messages. CMS publications are
tracked independently by the Home page's public metadata refresh.
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
            "cta": "Explore the research" if route == "advisory-market-signals" else "Explore the service",
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



# Paths that are deployed or otherwise change the visitor/member experience.
# Tests, docs and GitHub workflow edits alone are not public announcements.
DEPLOYED_PREFIXES = (
    "src/", "assets/", "images/", "static/", "data/", "sql/",
    "supabase/", ".streamlit/", "deploy/",
)
DEPLOYED_FILES = {"main.py", "app.py", "reader_test.py"}
IGNORE_FILES = {"data/portfolio_release_feed.json"}
ROUTE_FILES = {
    "main.py": "home",
    "src/page_home.py": "home",
    "src/page_home_featured.py": "home",
    "src/home_whats_new.py": "home",
    "src/home_pathways.py": "home",
    "src/home_employer_strip.py": "home",
    "src/page_impact.py": "impact",
    "src/portfolio_operating_evidence.py": "impact",
    "src/page_about.py": "about",
    "src/page_presence.py": "presence",
    "src/page_contact.py": "contact",
    "src/page_certifications.py": "certifications",
    "src/page_thinking.py": "thinking",
    "src/page_executive_briefings.py": "briefings",
    "src/page_reader_native.py": "readers",
    "src/site_reader_shell.py": "readers",
    "src/page_public_services.py": "advisory",
    "src/page_advisory_portal.py": "advisory",
    "src/page_advisory_scorecard.py": "advisory-scorecard",
    "src/page_advisory_rollout.py": "advisory-rollout",
    "src/page_advisory_renewal.py": "advisory-renewal",
    "src/page_advisory_investment.py": "advisory-decision",
    "src/page_advisory_leadership_public.py": "advisory-leadership",
    "src/page_advisory_leadership_workshop.py": "advisory-leadership",
    "src/page_advisory_market_signals.py": "advisory-market-signals",
    "src/page_advisory_market_review.py": "advisory-market-signals",
}
ROUTE_LABELS = {
    "home": "The portfolio",
    "impact": "AI Leadership",
    "about": "About",
    "presence": "Speaking & Publications",
    "contact": "Contact",
    "certifications": "Certifications",
    "thinking": "Thinking",
    "briefings": "Executive AI Briefings",
    "readers": "Reader Library",
    "advisory": "Executive Advisory",
    "advisory-scorecard": "AI Portfolio Scorecard",
    "advisory-rollout": "AI Rollout Readiness",
    "advisory-renewal": "AI Portfolio Renewal Advisor",
    "advisory-decision": "AI Investment Decision Advisor",
    "advisory-leadership": "AI Leadership Workshop",
    "advisory-market-signals": "Swedish AI & Data Market Review",
}


def changed_public_files(previous: str, current: str) -> tuple[str, ...]:
    """Diff all commits in a push; exclude release-feed self-updates."""
    try:
        names = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT",
             previous, current, "--"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL, timeout=15,
        ).splitlines()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        # Never use the whole repository as a fallback: it fabricates updates.
        return ()
    return tuple(sorted({
        name for name in names
        if name not in IGNORE_FILES
        and (name in DEPLOYED_FILES or name.startswith(DEPLOYED_PREFIXES))
    }))


def _public_route(path: str) -> str | None:
    if path in ROUTE_FILES:
        return ROUTE_FILES[path]
    # Group modules under the public service they support. Unknown backend
    # files receive only the general portfolio label, never their private name.
    if path.startswith("src/page_advisory_"):
        if "market" in path:
            return "advisory-market-signals"
        if "scorecard" in path:
            return "advisory-scorecard"
        if "rollout" in path:
            return "advisory-rollout"
        if "renewal" in path:
            return "advisory-renewal"
        if "leadership" in path:
            return "advisory-leadership"
        if "investment" in path:
            return "advisory-decision"
        return "advisory"
    if path.startswith("src/briefing_"):
        return "briefings"
    if path.startswith("src/weekly_ai_") or path.startswith("src/thinking_") or path.startswith("src/article_"):
        return "thinking"
    if path.startswith("src/page_owner_") or path.startswith("src/page_analytics"):
        return None
    if path.startswith("src/reader_"):
        return "readers"
    return None


def changed_update_item(paths: tuple[str, ...], commit_sha: str,
                        issued_at: str) -> dict[str, str] | None:
    """One public, truthful release record per deployed change set."""
    if not paths:
        return None
    if len(commit_sha) < 12 or not all(ch in "0123456789abcdef" for ch in commit_sha.lower()):
        return None
    date = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    routes = {_public_route(path) for path in paths}
    routes.discard(None)
    if len(routes) == 1:
        route = next(iter(routes))
        label = ROUTE_LABELS[route]
        title = label if route != "home" else "Portfolio homepage"
        return {
            "key": "update:" + commit_sha,
            "type": "Page updated",
            "title": title,
            "description": f"The {label} section has been updated. Explore its current content and experience.",
            "date": date.isoformat(),
            "href": "?page=" + route,
            "cta": "View the update",
        }
    return {
        "key": "update:" + commit_sha,
        "type": "Portfolio updated",
        "title": "Latest portfolio improvements",
        "description": (
            "Updates to the portfolio are available across its pages and "
            "services. Explore the current experience."
        ),
        "date": date.isoformat(),
        "href": "?page=home",
        "cta": "Explore the portfolio",
    }



def update_feed(previous: str, current: str) -> int:
    commit_date = subprocess.check_output(
        ["git", "show", "-s", "--format=%cI", current],
        cwd=ROOT, text=True, timeout=10,
    ).strip()
    new = new_release_items(previous, current, commit_date)
    # A newly launched page/credential is already a more useful announcement.
    # Otherwise emit a real update for EVERY deployed code or asset change,
    # even when the route and file existed for years.
    if not new:
        update = changed_update_item(
            changed_public_files(previous, current), current, commit_date
        )
        if update:
            new.append(update)
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
