"""Regression checks for the private, uncalibrated hiring predictor."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hiring_predictor import forecast_hiring
from page_analytics_overview import _evidence_signature, _changes_since_last_check


TODAY = date(2026, 10, 9)


def event(n: int, days_ago: int, *, employer: str | None = None,
          activity: str = "Application submitted", **flags) -> dict:
    r = {
        "id": n, "record_type": "evidence_event",
        "is_primary_analytics_record": True, "logical_event_key": str(n),
        "event_date": (TODAY - timedelta(days=days_ago)).isoformat(),
        "employer": employer or f"Employer {n}",
        "role": "Head of AI", "activity": activity,
        "is_application": True, "is_active": True,
        "is_closed_or_paused": False, "is_negative_decision": False,
        "is_human_interaction": False, "is_interview": False,
        "event_type": None, "stage_outcome": None,
    }
    r.update(flags)
    return r


class HiringPredictorTests(unittest.TestCase):
    def test_hiring_overview_renders_reliability_breakdown_with_portfolio_drivers(self):
        """Regression: nonzero portfolio driver descriptions must not overwrite
        the dictionary used by the reliability score and detailed breakdown.
        Previous implementation crashed after the two expanders were drawn.
        """
        from page_hiring_predictor import render_hiring_predictor

        jobs = [event(n, days_ago=(n * 3) % 52 + 1)
                for n in range(1, 37)]
        actions = {
            "quality_checked": True,
            "includes_partial_today": True,
            "recent_from": (TODAY - timedelta(days=27)).isoformat(),
            "previous_from": (TODAY - timedelta(days=55)).isoformat(),
            "through": TODAY.isoformat(),
            "cv_download_sessions": {"recent": 3, "previous": 0},
            "contact_click_sessions": {"recent": 2, "previous": 0},
            "cv_attribution": {
                "classification": "exclusive_highest_quality_tier",
                "tracking": "qualified_engaged_sessions",
                "parent_recent": 12, "parent_previous": 0,
                "base_only": 12, "variants": 0, "roles": 0,
                "tags": 0, "actions": 0,
            },
        }
        ui = MagicMock()
        ui.session_state = {}
        ui.columns.side_effect = lambda size: [MagicMock() for _ in range(size)]
        with patch("page_hiring_predictor.st", ui):
            render_hiring_predictor(
                jobs, market_model=None, site_correlation=None,
                hiring=None, today=TODAY, portfolio_actions=actions,
            )
        captions = [str(call.args[0]) for call in ui.caption.call_args_list
                    if call.args]
        self.assertTrue(
            any("evidence points" in value for value in captions),
            "Reliability details must render after the portfolio driver breakdown",
        )
        self.assertTrue(
            any("planning adjustment" in value for value in captions),
            "The scenario needs a nonzero portfolio driver to exercise the bug",
        )

    def test_no_evidence_never_fabricates_date(self):
        result = forecast_hiring([], TODAY)
        self.assertEqual(result["status"], "insufficient")
        self.assertEqual(result["curve"], [])

    def test_recent_pipeline_yields_ordered_scenarios(self):
        jobs = [event(n, days_ago=(n * 3) % 52 + 1) for n in range(1, 37)]
        jobs.append(event(80, 12, employer="Interview employer",
                          activity="Interview held", is_application=False,
                          is_interview=True))
        result = forecast_hiring(jobs, TODAY)
        self.assertEqual(result["status"], "scenario")
        self.assertEqual(result["confidence"], "Early estimate")
        for row in result["curve"]:
            self.assertLessEqual(row["Conservative"], row["Current pace"])
            self.assertLessEqual(row["Current pace"], row["Faster conversion"])
            self.assertGreaterEqual(row["Conservative"], 0)
            self.assertLessEqual(row["Faster conversion"], 1)
        self.assertTrue(result["crossings"]["Current pace"])

    def test_contextual_market_and_site_data_cannot_inflate_probabilities(self):
        jobs = [event(n, days_ago=n % 42 + 1) for n in range(1, 26)]
        baseline = forecast_hiring(jobs, TODAY)
        enriched = forecast_hiring(
            jobs, TODAY,
            market_model={"coverage":{"indicators":8,"observations":32},
                          "findings":[{"status":"Repeated association",
                                       "outcome":"interviews"}]},
            portfolio_correlation={"ranked":[{"status":"Repeated association",
                                               "outcome":"responses"}]},
            hiring_quality={"quality_summary":{"analysis_eligible_sessions":123,
                                               "hiring_intent_sessions":4}},
        )
        self.assertEqual(baseline["curve"], enriched["curve"])
        self.assertEqual(enriched["sources"]["market_indicator_series"], 8)
        self.assertEqual(enriched["sources"]["qualified_portfolio_sessions_30d"], 123)

    def test_portfolio_growth_and_cv_contact_actions_are_positive_bounded(self):
        from hiring_forecast_signals import portfolio_adjustment, PORTFOLIO_CAP
        series = []
        for elapsed in range(56, 0, -1):
            first_period = elapsed > 28
            series.append({
                "Date": (TODAY - timedelta(days=elapsed)).isoformat(),
                "sessions": 2 if first_period else 6,
                "engaged_10s": 1 if first_period else 5,
                "article_readers": 1 if first_period else 4,
                "multi_page_visitors": 0 if first_period else 2,
                "impact_visitors": 0 if first_period else 2,
                "governance_visitors": 0 if first_period else 2,
            })
        action_payload = {
            "quality_checked": True,
            "recent_from": (TODAY - timedelta(days=28)).isoformat(),
            "previous_from": (TODAY - timedelta(days=56)).isoformat(),
            "through": (TODAY - timedelta(days=1)).isoformat(),
            "cv_download_sessions": {"recent": 4, "previous": 1},
            "contact_click_sessions": {"recent": 5, "previous": 0},
        }
        p = portfolio_adjustment({"site_daily": series}, action_payload, TODAY)
        self.assertGreater(p["effect"], 0)
        self.assertLessEqual(p["effect"], PORTFOLIO_CAP)
        self.assertEqual(len(p["drivers"]), 5)
        self.assertTrue(p["qualified_actions_available"])
        neutral = portfolio_adjustment({"site_daily": series},
                                       {**action_payload, "quality_checked": False}, TODAY)
        self.assertLess(neutral["effect"], p["effect"])

    def test_live_cv_action_updates_on_current_day(self):
        from hiring_forecast_signals import portfolio_adjustment
        actions = {
            "quality_checked": True,
            "includes_partial_today": True,
            "recent_from": (TODAY - timedelta(days=27)).isoformat(),
            "previous_from": (TODAY - timedelta(days=55)).isoformat(),
            "through": TODAY.isoformat(),
            "cv_download_sessions": {"recent": 2, "previous": 0},
            "contact_click_sessions": {"recent": 1, "previous": 0},
        }
        first = portfolio_adjustment(None, actions, TODAY)
        self.assertTrue(first["qualified_actions_available"])
        self.assertGreater(first["effect"], 0)
        changed = portfolio_adjustment(
            None, {**actions, "cv_download_sessions":{"recent":3,"previous":0}}, TODAY
        )
        self.assertGreater(changed["effect"], first["effect"])

    def test_short_complete_periods_get_less_weight(self):
        from hiring_forecast_signals import portfolio_adjustment
        def data(num_days):
            return {"site_daily": [{
                "Date": (TODAY-timedelta(days=i)).isoformat(),
                "sessions": 8 if i <= num_days // 2 else 4,
                "engaged_10s": 5 if i <= num_days // 2 else 3,
                "article_readers": 6 if i <= num_days // 2 else 3,
            } for i in range(1,num_days+1)]}
        short = portfolio_adjustment(data(12),None,TODAY)
        long = portfolio_adjustment(data(56),None,TODAY)
        self.assertEqual(short["comparison_days"],6)
        self.assertEqual(long["comparison_days"],28)
        self.assertGreater(short["effect"],0)
        self.assertGreater(long["effect"],short["effect"])

    def test_cv_parent_and_explicit_tiers_are_weighted_and_not_stacked(self):
        from hiring_forecast_signals import portfolio_adjustment, PORTFOLIO_CAP, CV_ATTRIBUTION_CAP

        common = {
            "quality_checked": True,
            "includes_partial_today": True,
            "recent_from": (TODAY - timedelta(days=27)).isoformat(),
            "previous_from": (TODAY - timedelta(days=55)).isoformat(),
            "through": TODAY.isoformat(),
            "cv_download_sessions": {"recent":0,"previous":0},
            "contact_click_sessions": {"recent":0,"previous":0},
        }
        raw = {
            "classification":"exclusive_highest_quality_tier",
            "tracking":"qualified_engaged_sessions",
            "parent_recent":15,"parent_previous":0,
            "base_only":15,"variants":0,"roles":0,"tags":0,"actions":0,
        }
        parent = portfolio_adjustment(None,{**common,"cv_attribution":raw},TODAY)
        self.assertTrue(parent["cv_attribution_available"])
        self.assertGreater(parent["cv_attribution_effect"],0)
        self.assertEqual(parent["cv_attribution_tiers"]["roles"],0)
        self.assertEqual(parent["cv_attribution_tiers"]["tags"],0)
        self.assertEqual(parent["general_effect"],0)
        targeted = portfolio_adjustment(None,{**common,"cv_attribution":{
            **raw,"base_only":10,"variants":1,"roles":2,"tags":1,"actions":1
        }},TODAY)
        self.assertGreater(targeted["cv_attribution_effect"],parent["cv_attribution_effect"])
        self.assertLessEqual(targeted["cv_attribution_effect"],CV_ATTRIBUTION_CAP)
        self.assertLessEqual(targeted["effect"],PORTFOLIO_CAP)
        self.assertEqual(targeted["cv_attribution_tiers"]["parent_recent"],15)
        self.assertEqual(sum(targeted["cv_attribution_tiers"][key] for key
                             in ("base_only","variants","roles","tags","actions")),15)
        # Same visitor cannot claim several highest-quality buckets.
        corrupted = portfolio_adjustment(None,{**common,"cv_attribution":{
            **raw,"variants":15,"roles":15,"tags":15
        }},TODAY)
        self.assertFalse(corrupted["cv_attribution_available"])
        self.assertEqual(corrupted["cv_attribution_effect"],0)

    def test_cv_role_or_tag_evidence_influences_future_offer_curve(self):
        core = [event(n,days_ago=(n*3)%52+1) for n in range(1,37)]
        common = {
            "quality_checked": True,
            "includes_partial_today": True,
            "recent_from": (TODAY-timedelta(days=27)).isoformat(),
            "previous_from": (TODAY-timedelta(days=55)).isoformat(),
            "through": TODAY.isoformat(),
            "cv_download_sessions":{"recent":0,"previous":0},
            "contact_click_sessions":{"recent":0,"previous":0},
        }
        origin = {"classification":"exclusive_highest_quality_tier",
                  "tracking":"qualified_engaged_sessions",
                  "parent_recent":15,"parent_previous":0,
                  "base_only":15,"variants":0,"roles":0,"tags":0,"actions":0}
        baseline = forecast_hiring(core,TODAY,portfolio_actions={
            **common,"cv_attribution":origin})
        enriched = forecast_hiring(core,TODAY,portfolio_actions={
            **common,"cv_attribution":{
                **origin,"base_only":11,"variants":1,"roles":2,"tags":1
            }})
        self.assertGreater(enriched["drivers"]["portfolio"]["cv_attribution_effect"],
                           baseline["drivers"]["portfolio"]["cv_attribution_effect"])
        self.assertGreaterEqual(enriched["curve"][-1]["Current pace"],
                                baseline["curve"][-1]["Current pace"])

    def test_attribution_quality_must_be_explicit(self):
        from hiring_forecast_signals import portfolio_adjustment
        common={
            "quality_checked":True,
            "includes_partial_today":True,
            "recent_from":(TODAY-timedelta(days=27)).isoformat(),
            "previous_from":(TODAY-timedelta(days=55)).isoformat(),
            "through":TODAY.isoformat(),
            "cv_download_sessions":{"recent":0,"previous":0},
            "contact_click_sessions":{"recent":0,"previous":0},
        }
        bad={"parent_recent":20,"base_only":20,"variants":0,
             "roles":0,"tags":0,"actions":0}
        r=portfolio_adjustment(None,{**common,"cv_attribution":bad},TODAY)
        self.assertEqual(r["cv_attribution_effect"],0)
        self.assertFalse(r["cv_attribution_available"])
        # Unqualified or stale action summaries cannot grant a CV-source bonus.
        r=portfolio_adjustment(None,{**common,"quality_checked":False,
                                     "cv_attribution":bad},TODAY)
        self.assertEqual(r["cv_attribution_effect"],0)

    def test_offer_and_start_weeks_ranked_by_weekly_likelihood(self):
        jobs = [event(n, days_ago=(n * 3) % 55 + 1) for n in range(1, 45)]
        jobs.append(event(
            80, 5, employer="Interview candidate", is_application=False,
            is_interview=True, activity="Interview held",
            status="Interview completed", is_human_interaction=True,
            interaction_direction="two_way",
        ))
        r = forecast_hiring(jobs, TODAY)
        window = r["windows"]
        self.assertEqual(len(window["offers"]), 3)
        self.assertEqual(len(window["starts"]), 3)
        for label in ("offers","starts"):
            scores = [x["model_week_pct"] for x in window[label]]
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertGreater(scores[0], 0)
            for w in window[label]:
                start = date.fromisoformat(w["from"])
                finish = date.fromisoformat(w["to"])
                self.assertEqual(start.weekday(), 0)
                self.assertEqual((finish-start).days,6)
        # Calendar aggregation conserves the model's cumulative offer mass.
        total_offers = sum(x["model_week_pct"] for x in window["offer_weeks"])/100
        self.assertAlmostEqual(total_offers, r["curve"][-1]["Current pace"], places=2)
        total_starts = sum(x["model_week_pct"] for x in window["start_weeks"])/100
        self.assertAlmostEqual(total_offers,total_starts,places=2)
        earliest_start = min(date.fromisoformat(w["from"]) for w in window["start_weeks"])
        self.assertGreaterEqual(earliest_start,
                                TODAY + timedelta(days=21-6))

    def test_more_documented_evidence_raises_index_but_not_to_certainty(self):
        from hiring_forecast_windows import reliability_index, peak_weeks
        empty = reliability_index({}, [], {})
        self.assertEqual(empty["score_pct"],0)
        full = reliability_index({
            "primary_events":100,"job_history_days":150,
            "event_coverage":1.0,"mature_with_human_contact":20,
            "recorded_offer_events":0,
        },[{"stage":"interview","age":10}]*8,
          {"portfolio":{"qualified_actions_available":True},
           "market":{"indicators_reviewed":10}})
        self.assertGreater(full["score_pct"], empty["score_pct"])
        self.assertLessEqual(full["score_pct"],55)
        self.assertFalse(full["calibrated"])
        self.assertEqual(peak_weeks([],TODAY)["offers"],[])

    def test_model_week_mass_changes_when_market_evidence_changes(self):
        jobs = [event(n, days_ago=n%45 + 1) for n in range(1,40)]
        base = forecast_hiring(jobs,TODAY)
        up = forecast_hiring(jobs,TODAY,market_model={"latest":[{
            "indicator_key":"employment_outlook_it_tech",
            "observation_date":"2026-09-30",
            "published_at":"2026-10-01",
            "signal_score":1,
            "confidence_score":99,"relevance_score":99,
        }]})
        self.assertNotEqual(
            [w["model_week_pct"] for w in up["windows"]["offer_weeks"]],
            [w["model_week_pct"] for w in base["windows"]["offer_weeks"]],
        )

    def test_market_can_help_or_hurt_and_avoids_look_ahead(self):
        from hiring_forecast_signals import market_adjustment, MARKET_CAP
        def indicator(key, score, published="2026-09-30"):
            return {
                "indicator_key": key,
                "indicator_name": key,
                "observation_date": "2026-09-29",
                "published_at": published,
                "signal_score": score,
                "confidence_score": 95,
                "relevance_score": 95,
                "is_current": True,
                "source_organization": "Sample source",
            }
        upbeat = {"latest": [
            indicator("employment_outlook_it_tech", .9),
            indicator("employment_outlook_net_vgr", .8),
        ]}
        adverse = {"latest": [
            indicator("new_vacancies_arbetsformedlingen", -.9),
            indicator("redundancy_notices", -.8),
        ]}
        self.assertGreater(market_adjustment(upbeat, TODAY)["effect"], 0)
        self.assertLess(market_adjustment(adverse, TODAY)["effect"], 0)
        self.assertLessEqual(abs(market_adjustment(upbeat, TODAY)["effect"]), MARKET_CAP)
        future = {"latest": [indicator("employment_outlook_it_tech", 1.0, "2026-10-20")]}
        self.assertEqual(market_adjustment(future, TODAY)["effect"], 0)
        expired = {"latest": [{**indicator("employment_outlook_it_tech", 1.0),
                               "valid_until": "2026-10-01"}]}
        self.assertEqual(market_adjustment(expired, TODAY)["effect"], 0)
        # A repeated/same-source indicator cannot stack the same opportunity signal.
        doubled = {"latest": upbeat["latest"] + [indicator("employment_outlook_it_tech", 1.0)]}
        self.assertAlmostEqual(market_adjustment(doubled, TODAY)["effect"],
                               market_adjustment(upbeat, TODAY)["effect"])

    def test_market_positive_or_negative_moves_curve_in_correct_direction(self):
        jobs = [event(n, days_ago=(n * 3) % 52 + 1) for n in range(1, 37)]
        base = forecast_hiring(jobs, TODAY)
        market = lambda score: {"latest": [{
            "indicator_key":"employment_outlook_it_tech",
            "observation_date":"2026-09-30",
            "published_at":"2026-10-02",
            "signal_score":score,
            "confidence_score":95,"relevance_score":95,
        }]}
        up = forecast_hiring(jobs, TODAY, market_model=market(.9))
        down = forecast_hiring(jobs, TODAY, market_model=market(-.9))
        self.assertGreater(up["drivers"]["market"]["effect"], 0)
        self.assertLess(down["drivers"]["market"]["effect"], 0)
        self.assertGreaterEqual(up["curve"][-1]["Current pace"],
                                base["curve"][-1]["Current pace"])
        self.assertLessEqual(down["curve"][-1]["Current pace"],
                             base["curve"][-1]["Current pace"])
        self.assertEqual(up["comparison"]["base"], base["crossings"]["Current pace"])

    def test_missing_or_incomplete_history_keeps_portfolio_neutral(self):
        from hiring_forecast_signals import portfolio_adjustment
        partial = {"site_daily":[{"Date":(TODAY-timedelta(days=1)).isoformat(),
                                  "sessions":10000}]}
        self.assertEqual(portfolio_adjustment(partial,None,TODAY)["effect"],0)
        self.assertFalse(portfolio_adjustment(partial,None,TODAY)["daily_history_available"])

    def test_source_fingerprint_detects_only_recorded_changes(self):
        previous = {
            "jobs": _evidence_signature([{"id": 1, "status": "applied"}]),
            "market": _evidence_signature([{"id": 1, "score": 15}]),
            "site": _evidence_signature({"sessions": 2}),
        }
        self.assertEqual(_changes_since_last_check(None, previous), [])
        self.assertEqual(_changes_since_last_check(previous, dict(previous)), [])
        changed = dict(previous)
        changed["jobs"] = _evidence_signature([{"id": 1, "status": "interview"}])
        changed["site"] = _evidence_signature({"sessions": 3})
        self.assertEqual(
            _changes_since_last_check(previous, changed),
            ["job search", "portfolio activity"],
        )
        self.assertEqual(
            _changes_since_last_check(previous, {"market": previous["market"]}), [],
        )
        self.assertEqual(
            _evidence_signature({"a": 1, "b": 2}),
            _evidence_signature({"b": 2, "a": 1}),
        )

    def test_outbound_follow_up_does_not_count_as_employer_reply(self):
        jobs = [event(n, 20 + n, employer=f"Employer {n}")
                for n in range(1, 12)]
        outbound = event(
            50, 2, employer="Employer 1", is_application=False,
            is_human_interaction=True, interaction_direction="outbound",
            interaction_type="follow_up", activity="I followed up",
        )
        forecast = forecast_hiring(jobs + [outbound], TODAY)
        first = next(p for p in forecast["active_stages"]
                     if p["stage"] == "application")
        self.assertEqual(first["stage"], "application")
        self.assertFalse(any(p["stage"] == "conversation"
                             for p in forecast["active_stages"]))

    def test_interview_invitation_is_not_treated_as_completed_interview(self):
        jobs = [event(n, 4 + n) for n in range(1, 12)]
        jobs.append(event(
            80, 1, employer="Employer 1", is_application=False,
            is_interview=True, activity="Interview scheduled",
            status="Interview scheduled", is_human_interaction=False,
        ))
        result = forecast_hiring(jobs, TODAY)
        self.assertFalse(any(p["stage"] == "interview"
                             for p in result["active_stages"]))

    def test_completed_interview_status_is_counted_without_guessing_on_invitation(self):
        jobs = [event(n, 4 + n) for n in range(1, 12)]
        jobs.append(event(
            80, 2, employer="Employer 1", is_application=False,
            is_interview=True, activity="Recruiter conversation",
            status="Interview completed / awaiting feedback",
            interaction_direction="two_way", is_human_interaction=True,
        ))
        result = forecast_hiring(jobs, TODAY)
        self.assertTrue(any(p["stage"] == "interview"
                            for p in result["active_stages"]))

    def test_follow_up_does_not_reset_interview_clock(self):
        jobs = [event(n, 30 + n) for n in range(1, 14)]
        jobs.append(event(
            80, 30, employer="Employer 1", is_application=False,
            is_interview=True, activity="Interview held",
            status="Interview completed", interaction_direction="two_way",
            is_human_interaction=True,
        ))
        jobs.append(event(
            81, 1, employer="Employer 1", is_application=False,
            is_human_interaction=True, interaction_direction="outbound",
            activity="Follow-up message sent",
        ))
        r = forecast_hiring(jobs, TODAY)
        self.assertTrue(any(p["stage"] == "interview" and p["age"] == 30
                            for p in r["active_stages"]))

    def test_official_snapshot_is_not_miscounted_as_linked_event(self):
        jobs = [event(n, n + 10) for n in range(1, 12)]
        jobs.append({
            "id": 200, "record_type": "snapshot_metric",
            "snapshot_date": TODAY.isoformat(),
            "metric_name": "Confirmed application submissions",
            "metric_value": 228,
        })
        r = forecast_hiring(jobs, TODAY)
        self.assertEqual(r["sources"]["official_application_total"], 228)
        self.assertEqual(r["sources"]["linked_application_processes"], 11)
        self.assertLess(r["sources"]["event_coverage"], .1)
        self.assertEqual(r["sources"]["applications_last_28d"], 11)

    def test_no_offer_input_never_becomes_observed_conversion(self):
        jobs = [event(n, n % 48 + 1) for n in range(1, 28)]
        result = forecast_hiring(jobs, TODAY)
        self.assertEqual(result["sources"]["recorded_offer_events"], 0)
        self.assertLessEqual(result["sources"]["new_application_offer_assumption"], .035)

    def test_future_events_are_not_used_to_predict_today(self):
        now = [event(n, n % 24 + 1) for n in range(1, 20)]
        future = event(999, -10, event_type="offer_received",
                       stage_outcome="offer_received", is_application=False)
        self.assertEqual(forecast_hiring(now, TODAY)["curve"],
                         forecast_hiring(now + [future], TODAY)["curve"])

    def test_old_closed_offer_does_not_stop_a_new_search(self):
        jobs = [event(n, n % 27 + 1) for n in range(1, 19)]
        jobs.append(event(
            100, 40, employer="Previous employer", is_application=False,
            event_type="offer_received", stage_outcome="offer_received",
            activity="Offer received",
        ))
        jobs.append(event(
            101, 5, employer="Previous employer", is_application=False,
            is_active=False, is_closed_or_paused=True,
            is_negative_decision=True, status="Declined and closed",
            activity="Offer declined",
        ))
        result = forecast_hiring(jobs, TODAY)
        self.assertNotEqual(result["status"], "offer_recorded")
        self.assertEqual(result["sources"]["recorded_offer_events"], 1)

    def test_confirmed_offer_supersedes_a_first_offer_forecast(self):
        jobs = [event(1, 30), event(
            2, 1, employer="Employer 1", is_application=False,
            event_type="offer_received", stage_outcome="offer_received",
            activity="Formal offer received")]
        result = forecast_hiring(jobs, TODAY)
        self.assertEqual(result["status"], "offer_recorded")
        self.assertEqual(result["sources"]["recorded_offer_events"], 1)


if __name__ == "__main__":
    unittest.main()
