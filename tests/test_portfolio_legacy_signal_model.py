"""Evidence, small-sample, reporting-window and privacy regression tests."""
from __future__ import annotations

from datetime import date, timedelta

from portfolio_legacy_signal_model import (
    n, percentage, channel_label, channel_rollup, device_comparison,
    seven_day_comparison, traffic_findings,
)


def test_channel_names_are_broad_and_cohorts_reconcile():
    private = "sensitive-employer-role&utm_campaign=private"
    rows = [
        {"attribution_source": "LinkedIn?role=" + private,
         "sessions": 50, "engaged_sessions": 25, "article_sessions": 10},
        {"attribution_source": "linkedin?role=another-role",
         "sessions": 20, "engaged_sessions": 5, "article_sessions": 4},
        {"attribution_source": "cv",
         "sessions": 12, "engaged_sessions": 6},
        {"attribution_source": "direct/unknown",
         "sessions": 18, "engaged_sessions": 2},
    ]
    grouped = channel_rollup(rows)
    assert sum(row["sessions"] for row in grouped) == 100
    linkedin = next(row for row in grouped if row["Channel"] == "LinkedIn")
    assert linkedin["sessions"] == 70
    assert linkedin["engaged_sessions"] == 30
    assert linkedin["Engagement rate"] == 42.9
    assert "CV distribution" in [row["Channel"] for row in grouped]
    assert private not in str(grouped)
    assert all("role=" not in str(item) for item in grouped)


def test_missing_denominators_are_not_zero_percent():
    assert percentage(0, 0) is None
    assert percentage(8, 5) is None
    assert percentage(0, 10) == 0
    assert percentage(3, 20) == 15
    assert n("nan") == 0


def test_two_seven_day_periods_exclude_current_day():
    today = date(2026, 11, 6)
    days = [
        {"day": (today - timedelta(days=days_ago)).isoformat(),
         "sessions": 12 if days_ago <= 7 else 8}
        for days_ago in range(15)
    ]
    report = seven_day_comparison(days, today=today, window="all",
                                  period_since="2026-09-16T00:00:00Z")
    assert report is not None
    assert report["recent"] == 84
    assert report["previous"] == 56
    assert report["change_pct"] == 50.0
    assert seven_day_comparison(days, today=today, window="today",
                                period_since="2026-09-16T00:00:00Z") is None
    assert seven_day_comparison(days, today=today, window="all",
                                period_since="2026-11-03T00:00:00Z") is None


def test_no_inference_from_tiny_source_and_device_samples():
    report = {
        "totals": {"sessions": 18, "single_page_sessions": 18,
                   "unconfirmed_duration_sessions": 10},
        "attribution": [{"attribution_source": "direct/unknown", "sessions": 18}],
        "devices": [{"device_type": "desktop", "sessions": 12,
                     "engaged_sessions": 10},
                    {"device_type": "mobile", "sessions": 6,
                     "engaged_sessions": 0}],
        "daily": [],
    }
    findings = traffic_findings(report, today=date(2026, 11, 6), window="today")
    assert not any("uncertain" in item["title"] for item in findings)
    assert not any("differs by device" in item["title"] for item in findings)
    assert not any("Most recorded sessions" in item["title"] for item in findings)


def test_device_rates_not_unweighted_average():
    result = device_comparison([
        {"device_type": "desktop", "sessions": 100, "engaged_sessions": 20,
         "avg_pages": 1.4},
        {"device_type": "mobile", "sessions": 20, "engaged_sessions": 10,
         "avg_pages": 2.1},
    ])
    assert result[0]["Device"] == "Desktop"
    assert result[0]["Engagement rate"] == 20.0
    assert result[1]["Engagement rate"] == 50.0
    assert result[1]["Avg recorded pages"] == 2.1
