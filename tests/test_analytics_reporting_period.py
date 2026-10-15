import unittest
from unittest.mock import Mock

from analytics_reporting_period import (
    WINDOW_KEY, PREFERENCE_KEY, initialize_reporting_period, remember_reporting_period,
)


class ReportingPeriodTests(unittest.TestCase):
    def test_zero_uses_today(self):
        for value in (0, "0"):
            state = {}
            fetch = Mock(return_value={"totals": {"sessions": value}})
            initialize_reporting_period(state, fetch)
            self.assertEqual(state[WINDOW_KEY], "today")
            fetch.assert_called_once_with("last_hour")

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
        state[WINDOW_KEY] = "30d"
        remember_reporting_period(state)
        self.assertEqual(state[PREFERENCE_KEY], "30d")
