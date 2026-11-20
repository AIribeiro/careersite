"""Registration invitation contracts across Reader previews and Advisory."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reader_access_invitation import READER_INVITATIONS, reader_access_invitation


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "a":
            self.links.append(dict(attrs))


def test_reader_banners_share_one_registration_component_and_keep_routes():
    params = {
        "briefing": ("?page=briefing&amp;article=test-case&amp;access=1",
                     "briefing-reader-free-access", "briefing_unlock_register", "briefing_unlock_signin"),
        "article": ("?page=thinking&amp;article=test-case&amp;access=1",
                    "article-reader-free-access", "article_unlock_register", "article_unlock_signin"),
        "weekly_ai": ("?page=thinking&amp;article=weekly-issue&amp;access=1",
                      "weekly-ai-reader-free-access", "weekly_ai_premium_access", "weekly_ai_premium_signin"),
    }
    assert set(READER_INVITATIONS) == set(params)
    for kind, (target, section, register, signin) in params.items():
        html = reader_access_invitation(
            kind, target, section=section,
            register_event=register, signin_event=signin,
        )
        parser = _Links()
        parser.feed(html)
        assert len(parser.links) == 2
        assert parser.links[0]["href"] == target.replace("&amp;", "&")
        assert parser.links[1]["href"] == target.replace("&amp;", "&") + "&signin=1"
        assert parser.links[0]["data-hq-event"] == register
        assert parser.links[1]["data-hq-event"] == signin
        assert f'data-analytics-section="{section}"' in html
        assert "Register free" in html
        assert "Continue reading" in html
        assert "Email verification" in html
        assert "No payment details" in html
        assert "Already have an account? Sign in" in html
        assert "opt in" in html or "No automatic editorial email subscription" in html
        assert html.count("<h2>") == 1
        assert html.count("<li>") == 3
        assert "<form" not in html

    for source, kind in (
        ("briefing_reader_preview", "briefing"),
        ("article_reader_preview", "article"),
        ("weekly_ai_reader_preview", "weekly_ai"),
    ):
        content = (ROOT / "src" / (source + ".py")).read_text(encoding="utf-8")
        assert f'reader_access_invitation("{kind}"' in content
        assert "from reader_access_invitation import reader_access_invitation" in content


def test_restricted_advisory_services_never_promise_immediate_access():
    advisory = (ROOT / "src" / "page_advisory_portal.py").read_text(encoding="utf-8")
    assert "Register free to request Rollout Readiness Advisor access." in advisory
    assert "registration alone" in advisory.lower()
    assert "does not automatically unlock it" in advisory
    assert "Register free to start your AI Investment Decision Advisor." in advisory
    assert "Register free to use the AI Portfolio Renewal Advisor." in advisory
    assert "Register free to start your AI Leadership Workshop." in advisory
    assert "Register free to submit an Advisory request." in advisory
    assert "Send verification link · Continue registration" in advisory
    assert "No automatic editorial emails" in advisory
