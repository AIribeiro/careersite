"""Focused release guard: bounded employer-neutral evidence and in-page navigation."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio_operating_evidence import home_evidence, impact_evidence


class CaseParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.articles = set()
        self.links = {}
        self.details = []
        self.summaries = []
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag == "article" and props.get("id"):
            self.articles.add(props["id"])
        if tag == "a" and props.get("data-hq-event", "").startswith("impact_evidence_nav_"):
            self.links[props["data-hq-event"]] = props["href"]
        if tag == "details":
            self.details.append(props.get("data-evidence-case"))
            self.stack.append("details")
        if tag == "summary":
            self.summaries.append(props.get("data-hq-event", ""))
            if not self.stack:
                self.errors.append("summary without details")
        if tag in ("details", "summary"):
            if tag == "summary":
                self.stack.append("summary")

    def handle_endtag(self, tag):
        if tag in ("summary", "details"):
            if not self.stack or self.stack[-1] != tag:
                self.errors.append(f"mismatched {tag}")
            else:
                self.stack.pop()


def test_home_keeps_four_bounded_evidence_cards_and_no_new_section():
    home = home_evidence()
    assert home.count('class="card"') == 4
    assert home.count('id="leadership-in-practice"') == 1
    assert home.count("<details") == 0
    assert "working multilingual GenAI prototype" in home
    assert 'href="?page=impact#customer-interview-analyzer"' in home


def test_four_cases_have_direct_accessible_deep_dives_and_stable_anchors():
    page = impact_evidence()
    parser = CaseParser()
    parser.feed(page)
    assert not parser.errors
    assert not parser.stack
    ids = {
        "customer-interview-analyzer", "ai-portfolio-decisions",
        "ai-adoption-learning", "operational-governance",
    }
    assert parser.articles == ids
    assert set(parser.details) == ids
    assert len(parser.summaries) == len(set(parser.summaries)) == 4
    assert all(name.startswith("impact_case_") for name in parser.summaries)
    assert len(parser.links) == 3
    assert {dest.removeprefix("#") for dest in parser.links.values()} <= ids
    assert page.index('id="customer-interview-analyzer"') < page.index('id="ai-portfolio-decisions"')
    assert page.count('class="grid3 evidence-cards-grid"') == 1
    assert page.count('<script') == 0
    assert page.count('<form') == 0


def test_recruiter_evidence_has_auditable_maturity_and_anonymization():
    page = impact_evidence()
    assert "working GenAI prototype" in page
    assert "transcribed and translated" in page
    assert "did not proceed to a production rollout" in page
    assert "80+ AI opportunities" in page
    assert "100+ AI learning sessions" in page
    assert "Power BI Premium capacity" in page
    assert "<strong>My decision.</strong>" in page
    assert "Illustrative request example:" in page
    assert "The organization did not proceed to a production rollout" in page
    assert "Funding and execution decisions remained with the respective business owners." in page
    assert "longer-term behavior change would require separate measurement" in page
    for employer in ("Volvo Group", "Volvo Trucks", "MSX International", "Kimberly-Clark"):
        assert employer not in page
    for unverified in ("ROI of", "saved millions", "reduced costs by", "rolled out to all"):
        assert unverified not in page


def test_details_styles_are_scoped_responsive_and_keyboard_accessible():
    css = (ROOT / "src/site_styles.py").read_text(encoding="utf-8")
    assert ".site #operating-evidence .evidence-deep-dive>summary" in css
    assert ".site #operating-evidence .evidence-deep-dive>summary:focus-visible" in css
    assert ".site #operating-evidence .evidence-context-links" in css
    assert ".site #operating-evidence .evidence-deep-dive[open]>summary::after" in css
    assert ".site #operating-evidence .evidence-deep-dive-body p" in css
    assert "@media(max-width:700px)" in css
    assert "min-height:44px" in css


def test_case_interactions_use_existing_private_first_party_cta_measurement():
    analytics = (ROOT / "src/site_analytics.py").read_text(encoding="utf-8")
    assert "const raw = String(el.dataset.hqEvent || '').toLowerCase();" in analytics
    # CTA telemetry records a toggle click; it is not claimed as a verified open.
    assert "win.__jairAnalyticsSend('cta_click', ctaDescriptor)" in analytics
    assert "cta_click" in analytics
    assert "raw.startsWith('impact_case_')" in analytics
    assert "el.parentElement.open) return;" in analytics
    assert "data-hq-event" in impact_evidence()
