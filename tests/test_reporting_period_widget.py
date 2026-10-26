"""Exercise Streamlit reruns, including automatic and manual selection."""
import unittest
from streamlit.testing.v1 import AppTest


class ReportingPeriodWidgetTests(unittest.TestCase):
    def test_automatic_and_manual_selection(self):
        app = AppTest.from_string("""
import streamlit as st
from analytics_reporting_period import *
def fetch(window):
    return {"totals": {"recorded_views": 4 if window == "last_week" else 0}}
initialize_reporting_period(st.session_state, fetch)
st.selectbox("Reporting period", DEFAULT_WINDOWS, key=WINDOW_KEY,
             on_change=remember_reporting_period, args=(st.session_state,))
""").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox[0].value, "last_week")
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox[0].value, "last_week")
        app.selectbox[0].set_value("today").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox[0].value, "today")
