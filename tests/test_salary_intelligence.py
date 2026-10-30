"""Salary Intelligence regression: safe economic bases, evidence, and route behavior."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from page_salary_intelligence import (
    FIELDS, _benchmarked, _direct, _get_rows, _get_sources, _needs_review,
    _pct, _plot, _position, _priority, _process_url, _question, _sek, _summary,
    _get_versions,
)


def role(**extra):
    base = dict(
        opportunity_id=1, process_key="leovegas-ai-strategy-transformation-lead-2026",
        employer="LeoVegas Mobile Gaming Group",
        role_title="AI Strategy and Transformation Lead",
        current_process_outcome="in_progress",
        assessment_id=101, benchmark_id=201, benchmark_source_count=2,
        employment_model="permanent", comparability_group="employee_base_gross",
        comparison_basis="employee_base_gross",
        minimum_sek=85000, expected_sek=95000, ideal_sek=110000,
        market_low_sek=80000, market_central_sek=97000, market_high_sek=115000,
        expected_vs_market_central_pct=-2.1,
        career_floor_gross_monthly_sek=75000,
        negotiation_anchor_gross_monthly_sek=105000,
        benchmark_confidence="low", benchmark_freshness="current",
        next_review_on="2026-11-13",
    )
    base.update(extra)
    return base


class SalaryIntelligenceTests(TestCase):
    today = date(2026, 10, 30)

    def test_contract_and_unknown_employment_cannot_be_ranked_as_employee(self):
        permanent = role()
        contract = role(
            employment_model="contract_umbrella", comparability_group="umbrella_gross_equivalent",
            comparison_basis="employee_salary_proxy_for_contract", expected_sek=73000,
            expected_vs_market_central_pct=None,
        )
        uncertain = role(
            employment_model="unknown", comparability_group="unknown",
            comparison_basis="conditional_employment_unknown",
            expected_vs_market_central_pct=None,
        )
        self.assertTrue(_direct(permanent))
        self.assertFalse(_direct(contract))
        self.assertFalse(_direct(uncertain))
        self.assertEqual(_pct(contract), "N/A")
        self.assertEqual(_pct(uncertain), "N/A")
        self.assertEqual(_position(contract), "Not comparable")
        self.assertEqual(_position(uncertain), "Not comparable")
        self.assertIn("umbrella", _question(contract, self.today))
        self.assertIn("permanent employee", _question(uncertain, self.today))

    def test_market_difference_and_near_center_interpretation(self):
        self.assertIn("-2.1%", _pct(role()))
        self.assertIn("near model center", _pct(role()))
        self.assertEqual(_position(role()), "Inside inferred band")
        self.assertEqual(_position(role(expected_sek=79000)), "Below inferred band")
        self.assertEqual(_position(role(expected_sek=120000)), "Above inferred band")
        self.assertEqual(_position(role(benchmark_id=None)), "Not comparable")

    def test_summary_does_not_reclassify_closed_or_contract(self):
        data = [
            role(), role(opportunity_id=2, employer="KPMG"),
            role(opportunity_id=3, employment_model="contract_umbrella",
                 comparability_group="umbrella_gross_equivalent"),
            role(opportunity_id=4, employment_model="unknown",
                 comparability_group="unknown"),
            role(opportunity_id=5, current_process_outcome="rejected"),
        ]
        self.assertEqual(_summary(data, self.today), (4, 4, 2, 4))

    def test_source_and_freshness_rules(self):
        self.assertTrue(_benchmarked(role()))
        self.assertFalse(_benchmarked(role(benchmark_source_count=0)))
        self.assertTrue(_needs_review(role(benchmark_confidence="medium",
                                          next_review_on="2026-10-30"), self.today))
        self.assertFalse(_needs_review(role(benchmark_confidence="medium",
                                           next_review_on="2026-11-13"), self.today))
        self.assertEqual(_priority(role(employment_model="unknown"), self.today)[0], 0)
        self.assertEqual(_priority(role(next_review_on="2026-10-30"), self.today)[0], 0)

    def test_owner_token_is_required_and_forwarded(self):
        with self.assertRaises(PermissionError):
            _get_rows("", "Active")
        with self.assertRaises(PermissionError):
            _get_sources("", 201)
        with patch("page_salary_intelligence._request_json", return_value=[role()]) as req:
            rows = _get_rows("owner-jwt", "Active")
        self.assertEqual(len(rows), 1)
        self.assertEqual(req.call_args.kwargs["token"], "owner-jwt")
        self.assertIn("current_process_outcome=eq.in_progress", req.call_args.args[1])
        self.assertIn("benchmark_id", FIELDS)

    def test_history_and_unknown_populations_are_disjoint(self):
        with patch("page_salary_intelligence._request_json", return_value=[]) as req:
            _get_rows("owner-jwt", "Historical")
        self.assertIn("not.in.(in_progress,unknown)", req.call_args.args[1])
        with patch("page_salary_intelligence._request_json", return_value=[]) as req:
            _get_rows("owner-jwt", "Unconfirmed")
        self.assertIn("eq.unknown", req.call_args.args[1])


    def test_dated_versions_are_fetched_by_exact_opportunity_with_owner_token(self):
        with self.assertRaises(PermissionError):
            _get_versions("", 1)
        with patch("page_salary_intelligence._request_json", side_effect=[[{"assessment_date": "2026-10-28"}], [{"benchmark_on": "2026-10-30"}]]) as req:
            assessments, benchmarks = _get_versions("owner-jwt", 37)
        self.assertEqual(assessments[0]["assessment_date"], "2026-10-28")
        self.assertEqual(benchmarks[0]["benchmark_on"], "2026-10-30")
        self.assertEqual(req.call_count, 2)
        for call in req.call_args_list:
            self.assertIn("opportunity_id=eq.37", call.args[1])
            self.assertEqual(call.kwargs["token"], "owner-jwt")

    def test_sources_are_tied_to_exact_benchmark_and_owner(self):
        with patch("page_salary_intelligence._request_json", return_value=[]) as req:
            _get_sources("owner-jwt", 201)
        self.assertIn("benchmark_id=eq.201", req.call_args.args[1])
        self.assertEqual(req.call_args.kwargs["token"], "owner-jwt")

    def test_role_link_has_exact_process_key_in_private_workspace(self):
        url = _process_url("betsson-head-artificial-intelligence-2026")
        parts = urlparse(url)
        self.assertEqual(parts.scheme, "https")
        qs = parse_qs(parts.query)
        self.assertEqual(qs["workspace"], ["private"])
        self.assertEqual(qs["view"], ["stages"])
        self.assertEqual(qs["process"], ["betsson-head-artificial-intelligence-2026"])

    def test_interval_chart_encodes_market_and_candidate_with_text_alternative(self):
        html = _plot([role()])
        self.assertIn('role="img"', html)
        self.assertIn("salary-band", html)
        self.assertIn("salary-candidate", html)
        self.assertIn("salary-diamond", html)
        self.assertIn("salary-center", html)
        self.assertIn("salary-anchor", html)
        self.assertIn("95k", html)
        self.assertIn("115k", html)
        self.assertEqual(_plot([role(employment_model="contract_umbrella")]), "")

    def test_chart_escapes_user_controlled_employer_title(self):
        html = _plot([role(employer='<img src=x onerror=alert(1)>')])
        self.assertNotIn('<img src=x', html)
        self.assertIn("&lt;img", html)

    def test_missing_data_does_not_become_zero_salary(self):
        self.assertEqual(_sek(None), "—")
        self.assertFalse(_benchmarked(role(benchmark_id=None)))
        self.assertEqual(_plot([role(market_low_sek=None)]), "")


if __name__ == "__main__":
    import unittest
    unittest.main()
