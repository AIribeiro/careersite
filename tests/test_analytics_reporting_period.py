import unittest
from unittest.mock import Mock

from analytics_reporting_period import (
    WINDOW_KEY, PREFERENCE_KEY, DEFAULT_WINDOWS, initialize_reporting_period, remember_reporting_period,
)


class ReportingPeriodTests(unittest.TestCase):
    def test_zero_uses_today(self):
        for value in (0, "0"):
            state = {}
            fetch = Mock(side_effect=[{"totals": {"sessions": value}}, {"totals": {"sessions": 2}}])
            initialize_reporting_period(state, fetch)
            self.assertEqual(state[WINDOW_KEY], "today")
            self.assertEqual([c.args[0] for c in fetch.call_args_list], ["last_hour", "today"])

    def test_each_period_is_selected_when_first_nonempty(self):
        for index, expected in enumerate(DEFAULT_WINDOWS):
            state = {}
            fetch = Mock(side_effect=[{"totals": {"sessions": 0}}] * index
                         + [{"totals": {"sessions": 1}}])
            initialize_reporting_period(state, fetch)
            self.assertEqual(state[WINDOW_KEY], expected)
            self.assertEqual([c.args[0] for c in fetch.call_args_list], list(DEFAULT_WINDOWS[:index+1]))

    def test_all_empty_stops_at_all(self):
        state = {}
        fetch = Mock(return_value={"totals": {"sessions": 0}})
        initialize_reporting_period(state, fetch)
        self.assertEqual(state[WINDOW_KEY], "all")
        self.assertEqual(fetch.call_count, len(DEFAULT_WINDOWS))

    def test_error_after_zero_stops_without_widening_again(self):
        state = {}
        fetch = Mock(side_effect=[{"totals": {"sessions": 0}}, RuntimeError("offline")])
        initialize_reporting_period(state, fetch)
        self.assertEqual(state[WINDOW_KEY], "today")
        self.assertEqual(fetch.call_count, 2)

    def test_activity_keeps_last_hour(self):
        state = {}
        initialize_reporting_period(state, Mock(return_value={"totals": {"sessions": 1}}))
        self.assertEqual(state[WINDOW_KEY], "last_hour")

    def test_unknown_is_not_zero(self):
        for data in ({}, {"totals": None}, {"totals": {"sessions": "bad"}}):
            state = {}
            initialize_reporting_period(state, Mock(return_value=data))
            self.assertEqual(state[WINDOW_KEY], "last_hour")
        state = {}
        initialize_reporting_period(state, Mock(side_effect=RuntimeError("offline")))
        self.assertEqual(state[WINDOW_KEY], "last_hour")

    def test_manual_choice_survives_rerun_and_navigation(self):
        state = {WINDOW_KEY: "last_hour"}
        remember_reporting_period(state)
        fetch = Mock()
        initialize_reporting_period(state, fetch)
        del state[WINDOW_KEY]  # Streamlit removes widgets when changing views.
        initialize_reporting_period(state, fetch)
        self.assertEqual(state[WINDOW_KEY], "last_hour")
        fetch.assert_not_called()
        state[WINDOW_KEY] = "this_month"
        remember_reporting_period(state)
        self.assertEqual(state[PREFERENCE_KEY], "this_month")

    def test_automatic_choice_rechecks_and_ignores_old_preferences(self):
        state = {WINDOW_KEY: "today", PREFERENCE_KEY: "365d"}
        initialize_reporting_period(state, Mock(return_value={"totals": {"recorded_views": 1}}))
        self.assertEqual(state[WINDOW_KEY], "last_hour")
        initialize_reporting_period(state, Mock(side_effect=[
            {"totals": {"recorded_views": 0}}, {"totals": {"recorded_views": 3}}]))
        self.assertEqual(state[WINDOW_KEY], "today")

    def test_telemetry_without_visits_does_not_select_period(self):
        state = {}
        initialize_reporting_period(state, Mock(side_effect=[
            {"totals": {"sessions": 10, "recorded_views": 0}},
            {"totals": {"sessions": 12, "recorded_views": 2}}]))
        self.assertEqual(state[WINDOW_KEY], "today")
