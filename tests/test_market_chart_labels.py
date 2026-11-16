"""Long-label accessibility and responsive chart layout checks."""
from __future__ import annotations

import html
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from market_labelled_bars import labelled_bars_html
from page_advisory_market_observatory import _bars


class MarketChartLabelTests(unittest.TestCase):
    def test_long_names_remain_complete_in_visible_markup(self):
        names=[
            "AI use among large enterprises with at least 250 employees",
            "Lack of relevant expertise in enterprises considering AI but not adopting it",
            "Published consulting assignments across all professional disciplines",
        ]
        rows=[
            {"label":name,"value":value,"display_value":f"{value}%",
             "period":"2026","source":"SCB enterprise survey"}
            for name,value in zip(names,[85,62,10.7])
        ]
        result=labelled_bars_html(rows,unit_label="percentage points")
        for name in names:
            self.assertIn(name,result)
        self.assertIn("white-space:normal!important",result)
        self.assertIn("overflow-wrap:anywhere",result)
        self.assertIn("text-overflow:clip!important",result)
        self.assertNotIn("text-overflow:ellipsis",result)
        self.assertEqual(result.count('class="ms-bar-label"'),3)
        self.assertEqual(result.count('class="ms-bar-track"'),3)

    def test_signed_bars_use_a_zero_baseline_not_misleading_magnitudes(self):
        markup=labelled_bars_html([
            {"label":"ICT output growth","value":4.8,"display_value":"+4.8%"},
            {"label":"ICT employment change","value":-1.5,"display_value":"−1.5%"},
        ])
        self.assertEqual(markup.count('class="ms-bar-zero"'),2)
        self.assertIn("left:50.00%;width:50.00%",markup)
        self.assertIn("left:34.38%;width:15.62%",markup)
        self.assertIn("zero is the centre line",markup)

    def test_untrusted_labels_are_escaped_not_rendered_as_markup(self):
        markup=labelled_bars_html([{
            "label":'<script>alert("x")</script> & AI data',
            "value":2,"display_value":"<2 units>",
            "source":'<img src=x onerror=alert(1)>',
            "period":"Jan < 2026",
        }])
        self.assertNotIn("<script>",markup)
        self.assertNotIn("<img",markup)
        self.assertIn("&lt;script&gt;",markup)
        self.assertIn("&lt;2 units&gt;",markup)
        self.assertIn("&amp; AI data",markup)

    def test_observatory_plot_outputs_complete_indicator_labels(self):
        row={
            "code":"adoption_large","metric_label":"AI use among large enterprises",
            "value":85.0,"metric_unit":"percent",
            "source_title":"SCB", "period_label":"2026",
        }
        with patch("page_advisory_market_observatory.st.html") as render:
            with patch("page_advisory_market_observatory.st.caption"):
                _bars([row],{"adoption_large":"AI adoption among very large enterprises"},
                    title="Adoption by size",unit="share (%)",denominator="250+ employee group")
        output="\n".join(str(c.args[0]) for c in render.call_args_list)
        self.assertIn("AI adoption among very large enterprises",output)
        self.assertIn("85%",output)
        self.assertIn("250+ employee group",output)

    def test_existing_legacy_lenses_have_complete_labels_as_well(self):
        from page_advisory_market_signals import _plot
        sample={
            "code":"scb_large","lens":"adoption","geography":"Sweden",
            "series_code":"ai_large_enterprises","period_end":"2026-12-31",
            "period_label":"2026","metric_label":
                "AI use among large enterprises with at least 250 employees",
            "metric_unit":"percent","value":85,"source_title":"Statistics Sweden",
        }
        with patch("page_advisory_market_signals.st.html") as render:
            with patch("page_advisory_market_signals.st.caption"):
                _plot([sample],"adoption","Sweden")
        markup="\n".join(str(c.args[0]) for c in render.call_args_list)
        self.assertIn(sample["metric_label"],markup)
        self.assertIn("85%",markup)
        self.assertIn("white-space:normal!important",markup)

    def test_reject_invalid_colors_and_nonfinite_values(self):
        with self.assertRaises(ValueError):
            labelled_bars_html([{"label":"test","value":1}],color="red; background:url(x)")
        with self.assertRaises(ValueError):
            labelled_bars_html([{"label":"test","value":float("nan")}])


if __name__=="__main__":
    unittest.main()
