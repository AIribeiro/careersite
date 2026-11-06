"""Attribution regression: real editorial tags, privacy and denominators."""
from __future__ import annotations

from portfolio_public_attribution import (
    campaign_tag, role_tag, campaign_cohorts, campaign_channel_cohorts,
    role_cohorts, referrer_origin, referrer_cohorts,
    tag_coverage, meaningful_rate,
)


def test_known_campaigns_are_descriptive_not_raw_tracking_codes():
    assert campaign_tag("weekly_ai_2026_w43_friday") == "Weekly AI · 2026 W43 Friday"
    assert campaign_tag("weekly_ai_2026_w41") == "Weekly AI · 2026 W41"
    assert campaign_tag("linkedin_launch") == "Portfolio launch"
    assert campaign_tag("executive_briefings") == "Executive Briefings"
    assert campaign_tag("thinking") == "Thinking articles"
    assert campaign_tag("untagged") == "No campaign tag"


def test_unknown_or_sensitive_campaign_identifiers_never_appear():
    names = (
        "recruiter_company_foo", "application_secret",
        "https://example.com/personal", "candidate_JaneDoe",
        "random-personal_campaign-tag", "leadership?role=CEO",
        "user@example.com", "custom_source=private",
    )
    for name in names:
        assert campaign_tag(name) == "Other tagged campaigns"
    for name in ("https://linkedin.com/in/private", "unknown-person"):
        assert role_tag(name) == "Other editorial tags"


def test_role_tags_are_link_intents_not_occupations():
    assert role_tag("weeklyai") == "Weekly AI"
    assert role_tag("article") == "Articles"
    assert role_tag("executivebriefings") == "Executive Briefings"
    assert role_tag("ai_leadership") == "AI leadership"
    assert role_tag(None) == "No role tag"
    rows = role_cohorts([
        {"attribution_role": "weeklyai", "sessions": 18, "engaged_sessions": 8},
        {"attribution_role": "weeklyai", "sessions": 12, "engaged_sessions": 3},
        {"attribution_role": "sensitive-person-tag", "sessions": 1},
        {"attribution_role": None, "sessions": 200},
    ])
    assert sum(row["sessions"] for row in rows) == 231
    assert next(row for row in rows if row["Label"] == "Weekly AI")["sessions"] == 30
    assert "sensitive-person-tag" not in str(rows)
    assert tag_coverage(rows, "No role tag") == (31, 231)


def test_campaign_breakdown_uses_only_its_own_collector():
    rows = [
        {"campaign": "thinking", "channel": "LinkedIn", "sessions": 90,
         "reader_sessions": 70, "engaged_sessions": 30},
        {"campaign": "thinking", "channel": "x", "sessions": 30,
         "reader_sessions": 12, "engaged_sessions": 3},
        {"campaign": "untagged", "channel": "direct/unknown", "sessions": 200},
        {"campaign": "secret-client-outreach", "channel": "LinkedIn",
         "sessions": 3},
    ]
    cohorts = campaign_cohorts(rows)
    assert sum(row["sessions"] for row in cohorts) == 323
    assert next(row for row in cohorts if row["Label"] == "Thinking articles")["sessions"] == 120
    assert "secret-client-outreach" not in str(cohorts)
    assert tag_coverage(cohorts, "No campaign tag") == (123, 323)
    assert meaningful_rate({"sessions": 20, "engaged_sessions": 5}, "engaged_sessions") == 25.0
    assert meaningful_rate({"sessions": 4, "engaged_sessions": 4}, "engaged_sessions") is None
    cross = campaign_channel_cohorts(rows)
    assert sum(row["sessions"] for row in cross) == 323
    assert any(row["Channel"] == "LinkedIn"
               and row["Campaign"] == "Thinking articles" for row in cross)


def test_referer_hosts_are_coarse_and_not_people():
    assert referrer_origin("www.linkedin.com") == "LinkedIn"
    assert referrer_origin("m.facebook.com") == "Facebook"
    assert referrer_origin("direct/unknown") == "No referrer recorded"
    assert referrer_origin("https://www.google.com/path?utm_role=private") == "Google Search"
    assert referrer_origin("private.recruiter-crm.example.com") == "Other referrers"
    grouped = referrer_cohorts([
        {"referrer_host": "www.linkedin.com", "sessions": 10},
        {"referrer_host": "m.facebook.com", "sessions": 5},
        {"referrer_host": "direct/unknown", "sessions": 100},
        {"referrer_host": "private.recruiter-crm.example.com", "sessions": 1},
    ])
    assert sum(r["sessions"] for r in grouped) == 116
    assert "recruiter-crm" not in str(grouped)


def test_public_dashboard_sources_only_use_existing_anonymous_reports():
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "src"
    router = (src / "page_public_legacy_insights.py").read_text()
    renderer = (src / "page_public_legacy_intelligence.py").read_text()
    for forbidden in ("careersite_hiring_intelligence_v1",
                      "owner_hiring_headers(", "service_role",
                      "careersite_attribution_integrity_v1"):
        assert forbidden not in router
        assert forbidden not in renderer
    assert "careersite_content_intelligence_v2" in renderer
    assert "public_analytics_rpc_headers()" in renderer
    assert "_attribution_families" in renderer
    assert "visitor's job title" in renderer
