"""Shadow market invariants: vintage integrity, zero production effect, geo and RLS."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hiring_market_shadow import evaluate_market_shadow
from page_market_shadow import fetch_market_registry, record_shadow, _change_message


SOURCES = ["trr_professional_transitions", "brg_gothenburg_business_cycle",
           "scb_enterprise_ai_adoption", "unionen_branschbarometern",
           "almega_services_indicator", "af_jobtech_target_demand"]


def row(source, key, value, observed="2026-09-30", *,
        first="2026-10-19", published="2026-10-01", sector=None,
        frequency="quarterly", metric_text=None, current=True):
    return {"id": len(source+key), "source_registry_key": source, "source_key": key,
            "indicator_key": key, "sector": sector, "metric_value": value,
            "metric_value_text": metric_text, "period_start": observed[:8]+"01",
            "period_end": observed, "observation_date": observed,
            "first_seen_at": first+"T07:30:00+00:00",
            "published_at": published, "updated_at": first+"T09:00:00+00:00",
            "frequency": frequency, "is_current": current,
            "raw_data": {"methodology_version": "v1"},
            "source_url": "https://example.org/source"}


def evidence():
    items = [
        row(SOURCES[0],"trr_average_transition_days",227,"2026-06-30",current=False),
        row(SOURCES[0],"trr_average_transition_days",243),
        row(SOURCES[1],"gothenburg_business_confidence_index",102.2,"2026-06-30",
            sector="services",current=False),
        row(SOURCES[1],"gothenburg_business_confidence_index",99.5,
            sector="services"),
        row(SOURCES[1],"gothenburg_business_confidence_index",92.8,"2026-06-30",
            sector="manufacturing",current=False),
        row(SOURCES[1],"gothenburg_business_confidence_index",103.6,
            sector="manufacturing"),
        row(SOURCES[2],"ai_using_enterprises_10plus_share",35,"2025-12-31"),
        row(SOURCES[2],"ai_using_large_enterprises_250plus_share",71.9,"2025-12-31"),
        row(SOURCES[3],"unionen_private_sector_workplace_outlook",None,
            "2026-05-11",metric_text="Cautiously positive; uneven by sector"),
        row(SOURCES[4],"ict_output_growth_yoy",4.8,"2026-06-30"),
        row(SOURCES[4],"ict_employment_growth_yoy",-1.5,"2026-06-30"),
    ]
    for indicator, value in (("jobtech_high_signal_target_ads_v1",19),
                             ("jobtech_high_signal_target_ads_stockholm_v1",12),
                             ("jobtech_high_signal_target_ads_vgr_v1",3)):
        items.append(row(SOURCES[5],indicator,value,"2026-09-30",published=None,
                         frequency="monthly",first="2026-10-11"))
    items.append(row(SOURCES[5],"jobtech_high_signal_target_ads_vgr_v1",300,
                     "2026-10-14",published=None,first="2026-10-14",
                     frequency="monthly"))
    return items


def baseline():
    return {"model_version": "hiring-v2-stage-evidence-provisional",
            "stage_breakdown": {"subsequent_interview_scheduled": 1},
            "portfolio_credibility_index": 46,
            "leading_stage_scenario": {
                "offer_earliest": "2026-11-05",
                "offer_central": "2026-11-19",
                "offer_latest": "2026-12-10",
                "start_earliest": "2026-11-19",
                "start_central": "2026-12-17",
                "start_latest": "2027-01-21"}}


def registry():
    return [{"source_key": s, "active": True} for s in SOURCES]


class MarketShadowTests(unittest.TestCase):
    def test_shadow_keeps_offer_and_start_scenario_without_scores(self):
        model = evaluate_market_shadow(evidence(),registry(),baseline(),date(2026,10,20))
        self.assertEqual(model["baseline_timing"],model["shadow_timing"])
        self.assertEqual(model["offer_date_delta_days"],0)
        self.assertEqual(model["start_date_delta_days"],0)
        self.assertEqual(model["external_contribution"],"Unchanged (not scored)")
        self.assertFalse(model["promotion_allowed"])
        self.assertEqual(model["validation"],"not_backtested")
        self.assertNotIn("offer_probability",model)
        self.assertNotIn("probability_working_90d",model)

    def test_region_definitions_and_partial_month_guard(self):
        model = evaluate_market_shadow(evidence(),registry(),baseline(),"2026-10-20")
        self.assertEqual(model["jobtech"]["Sweden"]["value"],19)
        self.assertEqual(model["jobtech"]["Stockholm"]["value"],12)
        self.assertEqual(model["jobtech"]["Västra Götaland"]["value"],3)
        self.assertTrue(model["jobtech"]["Västra Götaland"]["sample_small"])
        self.assertIn("municipalities",model["geography"]["Göteborgsregionen"]["geography_note"])
        self.assertTrue(model["contradictory_output_employment"])
        self.assertEqual(model["groups"]["Professional transitions"][0]["metric"]["change"],16.0)
        self.assertEqual(model["geography"]["Göteborgsregionen"]["services"]["change"],-2.7)

    def test_no_hindsight_before_first_seen_even_if_period_and_release_old(self):
        model = evaluate_market_shadow(evidence(),registry(),baseline(),"2026-10-18")
        self.assertTrue(all(n == 0 for n in model["source_counts"].values()))
        self.assertEqual(set(model["missing_sources"]),set(SOURCES[:5]))
        # Previously discovered JobTech v1 remains a proxy, not a newly scored indicator.
        self.assertEqual(model["jobtech"]["Västra Götaland"]["value"],3)

    def test_missing_source_is_not_fabricated_zero_or_independent_vote(self):
        disabled = [dict(r) for r in registry()]
        disabled[4]["active"]=False
        model = evaluate_market_shadow(evidence(),disabled,baseline(),"2026-10-20")
        self.assertEqual(model["source_counts"]["almega_services_indicator"],0)
        self.assertIn("almega_services_indicator",model["missing_sources"])
        self.assertNotIn("ict_output_growth_yoy",str(model["groups"]))
        self.assertEqual(model["offer_date_delta_days"],0)

    def test_backfilled_data_cannot_revise_earlier_forecast(self):
        before = evaluate_market_shadow(evidence(),registry(),baseline(),"2026-10-18")
        after = evaluate_market_shadow(evidence(),registry(),baseline(),"2026-10-20")
        self.assertNotEqual(before["evidence_signature"],after["evidence_signature"])
        self.assertEqual(before["baseline_timing"],after["baseline_timing"])

    def test_private_audit_insert_only_and_failed_owner_token(self):
        report = evaluate_market_shadow(evidence(),registry(),baseline(),"2026-10-20")
        with patch("page_market_shadow._request_json") as req:
            record_shadow("owner-token",report)
            args = req.call_args
            self.assertEqual(args.args[0],"POST")
            self.assertIn("careersite_hiring_market_shadow_history",args.args[1])
            self.assertNotIn("careersite_hiring_forecast_history",args.args[1])
            self.assertEqual(args.kwargs["token"],"owner-token")
            self.assertEqual(args.kwargs["payload"]["scoring_status"],"context_only")
            self.assertNotIn("owner_user_id",args.kwargs["payload"])
        with self.assertRaises(ValueError):
            record_shadow("",report)
        with patch("page_market_shadow._request_json",return_value=[{"active":True}]) as req:
            self.assertEqual(fetch_market_registry("owner-token"),[{"active":True}])
            self.assertEqual(req.call_args.kwargs["token"],"owner-token")

    def test_first_shadow_report_is_not_claimed_as_validation(self):
        report = evaluate_market_shadow(evidence(),registry(),baseline(),"2026-10-20")
        self.assertIn("First observed",_change_message(report,[]))


if __name__ == "__main__":
    unittest.main()
