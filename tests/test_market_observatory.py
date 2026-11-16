"""AI & Data Market Observatory regression contracts.

The public service can only use approved curated evidence. All trend and scope
checks are deterministic and independent of the owner's private analytics.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from io import BytesIO
import csv
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from page_advisory_market_observatory import (
    DASHBOARDS,leadership_timeline,comparable_series,interpretation_pairs,
    _evidence_csv,_freshness,_number,_point_map
)


def point(code, val, *, when="2026-10-01", end="2026-10-31",
          geo="Sweden", complete=True, series="jobtech_ai_data_leadership_v1",
          unit="advertisements", family="af_jobtech_target_demand",
          checked="2026-11-16"):
    return {
        "code":code,"value":val,"period_start":when,"period_end":end,
        "geography":geo,"period_complete":complete,"series_code":series,
        "metric_unit":unit,"source_family":family,"verified_on":checked,
        "period_label":when[:7],"source_url":"https://historical.api.jobtechdev.se/search",
        "source_title":"JobTech v1 basket","metric_label":"High signal AI/Data leadership adverts",
        "lens":"leadership","population_note":"Published headline-only title-basket",
        "methodology":"Frozen v1 classifier; deduped ads",
        "caveat":"Only observed titles, not all opportunities",
        "published_on":checked,"evidence_grade":"derived",
    }


class ObservatoryTests(unittest.TestCase):
    def test_eight_decision_oriented_dashboards_are_available(self):
        self.assertEqual(len(DASHBOARDS),8)
        self.assertEqual(set(DASHBOARDS),{
            "pulse","demand","adoption","talent","commercial","signals","trends","ledger"
        })

    def test_original_title_basket_excludes_incomplete_month(self):
        rows=[
            point("jun",12,when="2026-06-01",end="2026-06-30"),
            point("oct",29),
            point("nov_mtd",12,when="2026-11-01",end="2026-11-15",complete=False),
        ]
        full=leadership_timeline(rows)
        self.assertEqual([p["code"] for p in full],["jun","oct"])
        all_periods=leadership_timeline(rows,include_partial=True)
        self.assertEqual(len(all_periods),3)

    def test_regional_series_are_kept_separate_not_summed(self):
        rows=[
            point("oct_se",29),
            point("oct_vgr",5,geo="Västra Götaland"),
            point("oct_sto",13,geo="Stockholm"),
        ]
        result=leadership_timeline(rows)
        self.assertEqual(len(result),3)
        self.assertEqual([p["value"] for p in result if p["geography"]=="Sweden"],[29])
        self.assertNotIn(47,[p["value"] for p in result])

    def test_revised_identical_period_uses_latest_verified_vintage(self):
        rows=[
            point("older",19,checked="2026-10-11"),
            point("revision",20,checked="2026-10-22"),
        ]
        result=leadership_timeline(rows)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["value"],20)

    def test_histories_never_join_incompatible_units(self):
        rows=[
            point("p1",12,unit="advertisements"),
            point("p2",2.5,unit="percent"),
        ]
        with self.assertRaisesRegex(ValueError,"Incompatible"):
            comparable_series(rows,"jobtech_ai_data_leadership_v1","Sweden")
        self.assertEqual(comparable_series([rows[0]],
            "jobtech_ai_data_leadership_v1","Sweden")[0][0]["value"],12)

    def test_one_period_stays_one_period(self):
        complete,partial=comparable_series([point("oct",29)],
            "jobtech_ai_data_leadership_v1","Sweden")
        self.assertEqual(len(complete),1)
        self.assertEqual(partial,[])

    def test_cross_source_interpretations_restrict_to_available_observations(self):
        first=point("brainville_202610_assignments_yoy",10.7,
            family="brainville_consulting_market",series="consulting_assignments_yoy",unit="percent")
        pairs=interpretation_pairs([first])
        self.assertEqual(pairs,[])
        second=point("brainville_202610_consultants_yoy",18.5,
            family="brainville_consulting_market",series="consulting_consultants_yoy",unit="percent")
        matched=interpretation_pairs([first,second])
        self.assertEqual([x["key"] for x in matched],["consulting_supply"])
        self.assertEqual([x["evidence"][0]["value"] for x in matched],[10.7])

    def test_source_ledger_export_preserves_publication_scope_and_escapes_formulas(self):
        x=point("oct",29)
        x["metric_label"]="=HYPERLINK(1)"
        raw=_evidence_csv([x]).decode("utf-8-sig")
        rows=list(csv.reader(raw.splitlines()))
        self.assertTrue(rows[1][8].startswith("'="))
        self.assertIn("source_url",rows[0])
        self.assertIn("period_complete",rows[0])
        self.assertNotIn("user_id",rows[0])

    def test_source_review_clock_not_confused_with_observation_month(self):
        p=point("old",12,checked="2026-11-16")
        self.assertEqual(_freshness(p,date(2026,11,20)),"Within review interval")
        self.assertEqual(_freshness(p,date(2026,12,4)),"Overdue for recheck")
        self.assertEqual(_freshness(p,date(2026,11,10)),"Future verification — investigate")

    def test_market_review_pdf_supplement_is_derived_only_from_released_context(self):
        from page_advisory_market_review import _additional_market_lenses,_styles
        from reportlab.platypus import Paragraph,PageBreak
        optional=point("market_context_20261116_03",41,series="employment_outlook_q4_it_tech",
            unit="percentage points",family="manpower_employment_outlook")
        optional.update({
            "metric_label":"IT & Tech net hiring intentions · Q4 2026",
            "period_label":"Q4 2026","population_note":"Manpower employer survey"
        })
        flowables=_additional_market_lenses([optional],_styles())
        self.assertTrue(any(isinstance(x,PageBreak) for x in flowables))
        rendered=" ".join(x.text for x in flowables if isinstance(x,Paragraph))
        self.assertIn("41 percentage points",rendered)
        self.assertIn("Manpower",rendered)
        self.assertEqual(_additional_market_lenses([],_styles()),[])

    def test_public_observatory_has_no_private_db_access(self):
        code=(ROOT/"src/page_advisory_market_observatory.py").read_text()
        self.assertNotIn("fetch_market_records(",code)
        self.assertNotIn('"_request_json"',code)
        self.assertNotIn("portfolio_advisory_renewal_events",code)
        self.assertNotIn("job_market_correlations import",code)
        self.assertNotIn("fetch_job_records",code)

    def test_public_render_path_passes_curated_edition_snapshot(self):
        code=(ROOT/"src/page_advisory_market_signals.py").read_text()
        self.assertIn("points, briefs, release = _release_snapshot(token,points,briefs)",code)
        self.assertIn("render_market_observatory(points)",code)
        self.assertNotIn("render_swedish_job_market(",code)


if __name__=="__main__":
    unittest.main()
