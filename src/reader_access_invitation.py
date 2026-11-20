"""One clear registration invitation across editorial preview gates.

Shared copy and markup for Executive AI Briefings, early-access articles and
current Weekly AI. Registration and sign-in destinations are supplied by the
owning page so their route, tracking events and access rules do not change.
"""
from __future__ import annotations

from html import escape


READER_INVITATIONS = {
    "briefing": {
        "headline": "Register free to read the full briefing.",
        "intro": (
            "You have read the public preview. Create a free reader account "
            "to continue with the full decision analysis, evidence and "
            "practical considerations."
        ),
        "benefits": (
            "Read the complete briefing and its decision framework",
            "View the original infographic and PDF, where available",
            "Access other Executive AI Briefings with the same account",
        ),
        "note": (
            "Free registration · Email verification · No payment details · "
            "Editorial emails only if you opt in."
        ),
    },
    "article": {
        "headline": "Register free to finish reading this article.",
        "intro": (
            "The public executive summary is open to everyone. "
            "Create a free reader account to continue with the full argument, "
            "supporting evidence and practical implications."
        ),
        "benefits": (
            "Read the complete article and its references",
            "Access complete Executive AI Briefings with one account",
            "Read the latest Weekly AI edition and revisit the library",
        ),
        "note": (
            "Free registration · Email verification · No payment details · "
            "Editorial emails only if you opt in."
        ),
    },
    "weekly_ai": {
        "headline": "Register free to read this week's complete Weekly AI.",
        "intro": (
            "Continue beyond the public summary to the full selection of "
            "developments, original sources and implications for business "
            "leaders. One free reader account also opens Executive AI Briefings."
        ),
        "benefits": (
            "Read every item in the latest Weekly AI edition",
            "Listen to the narrated edition, when available",
            "Previous editions become public after the next release",
        ),
        "note": (
            "Free registration · Email verification · No payment details · "
            "No automatic editorial email subscription."
        ),
    },
}


def reader_access_invitation(kind: str, target: str, *,
                             section: str, register_event: str,
                             signin_event: str) -> str:
    """Return a consistent gate without modifying the content's own route."""
    copy = READER_INVITATIONS[kind]
    if not target.startswith("?page="):
        raise ValueError("Reader access target must be a relative portfolio route")
    for event in (section, register_event, signin_event):
        if not event.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid analytics event")
    # target is already HTML attribute encoded by its caller (ampersands
    # represented as &amp;). Never double-escape its query string.
    if any(char in target for char in ('"', "'", "<", ">")):
        raise ValueError("Invalid reader target")
    bullets = "".join("<li>" + escape(text) + "</li>" for text in copy["benefits"])
    return (
        f'<section class="briefing-unlock" data-analytics-section="{section}">'
        '<div class="briefing-unlock-inner"><div>'
        '<p class="eyebrow">Continue reading · Free reader registration</p>'
        '<h2>' + escape(copy["headline"]) + '</h2>'
        '<p>' + escape(copy["intro"]) + '</p></div>'
        '<ul class="briefing-unlock-benefits">' + bullets + '</ul>'
        '</div><div class="briefing-unlock-actions">'
        f'<a class="briefing-unlock-primary" href="{target}" target="_self" '
        f'data-hq-event="{register_event}">Register free · Continue reading</a>'
        f'<a class="briefing-unlock-secondary" href="{target}&amp;signin=1" '
        f'target="_self" data-hq-event="{signin_event}">'
        'Already have an account? Sign in</a>'
        '</div><p class="briefing-unlock-note">' + escape(copy["note"]) + '</p>'
        '</section>'
    )
