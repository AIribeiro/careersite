import unittest

from market_trend_dashboard import trend_cards, default_indicator_keys, is_ai_indicator


def row(date, value, unit="people"):
    return {"observation_date": date, "metric_value": value, "metric_unit": unit,
            "indicator_name": "Employment", "source_organization": "Evidence source"}


class MarketTrendCardsTests(unittest.TestCase):
    def test_ai_series_after_first_six_are_selected(self):
        groups = {str(i): [row("2026-08-01", 1), row("2026-09-01", 2)] for i in range(8)}
        groups["ai"] = [dict(row("2026-08-01", 3), indicator_name="AI/Data leadership ads"),
                        dict(row("2026-09-01", 4), indicator_name="AI/Data leadership ads")]
        selected = default_indicator_keys(trend_cards(groups))
        self.assertEqual(selected, ["ai", "0", "1", "2", "3", "4", "5", "6", "7"])

    def test_audience_role_does_not_make_every_indicator_ai(self):
        self.assertFalse(is_ai_indicator({"indicator_name": "Business confidence", "role_family": "enterprise_ai_data_leadership"}))
        self.assertFalse(is_ai_indicator({"indicator_name": "Retail vacancies"}))
        self.assertTrue(is_ai_indicator({"indicator_key": "ai_occupational_groups"}))

    def test_ai_snapshot_does_not_fabricate_change(self):
        cards = trend_cards({"ai": [dict(row("2026-09-01", 278), indicator_name="AI mentions growth")]}, include_ai_snapshots=True)
        self.assertEqual(len(cards), 1)
        self.assertIsNone(cards[0]["change"])
        self.assertEqual(len(cards[0]["points"]), 1)

    def test_partial_month_never_compared_as_complete_month(self):
        cards = trend_cards({"ai": [dict(row(d, n), indicator_name="AI job ads MTD")
                                   for d, n in (("2026-09-01", 4), ("2026-10-01", 2))]})
        self.assertEqual(cards[0]["direction"], "Month to date")
        self.assertIsNone(cards[0]["change"])

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
        self.assertEqual(app.multiselect[0].value, [None])
        self.assertEqual(app.metric[0].label, "Higher")
        self.assertFalse(app.expander[0].proto.expanded)
        app.multiselect[0].set_value([]).run()
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
