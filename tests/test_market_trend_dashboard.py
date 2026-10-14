import unittest

from market_trend_dashboard import trend_cards


def row(date, value, unit="people"):
    return {"observation_date": date, "metric_value": value, "metric_unit": unit,
            "indicator_name": "Employment", "source_organization": "Evidence source"}


class MarketTrendCardsTests(unittest.TestCase):
    def test_chronological_change_and_evidence(self):
        cards = trend_cards({"a": [row("2026-09-01", 90), row("2026-08-01", 100)]})
        self.assertEqual(cards[0]["direction"], "Lower")
        self.assertEqual(cards[0]["change"], -10)
        self.assertEqual(cards[0]["previous_period"], "2026-08-01")
        self.assertEqual(cards[0]["source"], "Evidence source")

    def test_sparse_nonfinite_and_mixed_units_not_charted(self):
        self.assertEqual(trend_cards({"a": [row("2026-08-01", 1)]}), [])
        for invalid in (None, "bad", float("nan"), float("inf")):
            self.assertEqual(trend_cards({"a": [row("2026-08-01", 1), row("2026-09-01", invalid)]}), [])
        self.assertEqual(trend_cards({"a": [row("2026-08-01", 1), row("2026-09-01", 2, "percent")]}), [])

    def test_direction_is_not_a_claim_of_improvement(self):
        for value, expected in ((1, "Unchanged"), (2, "Higher"), (0, "Lower")):
            self.assertEqual(trend_cards({"a": [row("2026-08-01", 1), row("2026-09-01", value)]})[0]["direction"], expected)

    def test_render_without_exception(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string('''
from market_trend_dashboard import render_market_trends
render_market_trends({"groups": {"a": [
    {"observation_date": "2026-08-01", "metric_value": 1, "metric_unit": "people"},
    {"observation_date": "2026-09-01", "metric_value": 2, "metric_unit": "people"}
]}, "trends": [{"Latest": 2}]})
''').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].label, "Higher")
        self.assertFalse(app.expander[0].proto.expanded)
        app.multiselect[0].set_value([]).run()
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
