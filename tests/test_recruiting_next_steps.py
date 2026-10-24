"""Next-step timing planner: promise precedence, absence of calibrated certainty."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recruiting_next_steps import (
    make_plan, timing_sample, working_day_on_or_after, working_days_after,
)


TODAY = date(2026, 10, 24)


def opp(id, employer, name, *, outcome="in_progress", applied="2026-09-20",
        decision=None):
    return {"id": id, "employer": employer, "role_title": name, "outcome": outcome,
            "application_date": applied, "decision_date": decision}


def meet(id, opp_id, day, stage, status, meeting_type="interview"):
    return {"id": id, "opportunity_id": opp_id, "stage": stage,
            "scheduled_date": day, "attendance": status,
            "meeting_type": meeting_type,
            "evidence_note": "Calendar event verified"}


def signal(id, opp_id, kind, anchor, begin=None, end=None):
    return {"id": id, "opportunity_id": opp_id, "kind": kind,
            "event_label": "Recruiter reply" if kind=="employer_response_window" else
            "Referral discussion" if kind=="referral_intent" else "Stage 2 invitation",
            "anchor_date": anchor, "window_start": begin, "window_end": end,
            "source_reference": "interview review: confirmed first-party correspondence"}


class NextStepPlanningTests(unittest.TestCase):
    def setUp(self):
        self.ops = [
            opp(2,"Betsson Group","Head of SB Product"),
            opp(7,"KPMG","AI Lead"),
            opp(8,"LeoVegas","AI Strategy Lead"),
            opp(16,"Betsson Group","Head of Artificial Intelligence",
                applied="2026-10-12"),
            opp(1,"Adven","Director",outcome="rejected",applied="2026-08-27",
                decision="2026-10-08"),
            opp(3,"Old employer","Old role",outcome="unknown"),
        ]
        self.meetings = [
            meet(15,2,"2026-10-23",1,"attended","recruiter_screening"),
            meet(23,2,"2026-10-20",1,"cancelled","recruiter_screening"),
            meet(16,7,"2026-10-22",2,"attended"),
            meet(14,7,"2026-10-07",1,"attended"),
            meet(18,8,"2026-10-28",2,"unverified"),
            meet(13,8,"2026-10-02",1,"attended"),
            meet(17,1,"2026-09-21",1,"attended"),
        ]
        self.signals = [
            signal(1,2,"employer_response_window","2026-10-23",
                   "2026-10-26","2026-10-27"),
            signal(2,16,"referral_intent","2026-10-23"),
            signal(3,7,"stage_progression","2026-10-13",
                   "2026-10-13","2026-10-13"),
            signal(4,8,"stage_progression","2026-10-19",
                   "2026-10-19","2026-10-19"),
        ]

    def test_weekend_not_treated_as_recruiter_business_day(self):
        self.assertEqual(working_day_on_or_after(TODAY), date(2026,10,26))
        self.assertEqual(working_days_after(date(2026,10,23),5), date(2026,10,30))
        self.assertEqual(working_days_after(date(2026,10,22),5), date(2026,10,29))

    def test_promise_overrides_generic_betsson_guess(self):
        result = make_plan(self.ops,self.meetings,self.signals,TODAY)
        events = [i for i in result["items"] if i["opportunity_id"]==2]
        indicated = [i for i in events if i["kind"]=="indicated"]
        self.assertEqual(len(indicated),1)
        self.assertEqual((indicated[0]["start"],indicated[0]["end"]),
                         (date(2026,10,26),date(2026,10,27)))
        self.assertFalse(any(i["kind"]=="estimated" for i in events))
        self.assertEqual([i["start"] for i in events if i["kind"]=="action"],
                         [date(2026,10,28)])

    def test_booked_leovegas_remains_confirmed_not_completed(self):
        result=make_plan(self.ops,self.meetings,self.signals,TODAY)
        events=[i for i in result["items"] if i["opportunity_id"]==8]
        booked=[i for i in events if i["kind"]=="confirmed"]
        self.assertEqual([e["start"] for e in booked],[date(2026,10,28)])
        self.assertIn("not yet occurred",booked[0]["conditional"])
        self.assertEqual(len([e for e in events if e["kind"]=="estimated"]),1)

    def test_kpmg_post_second_round_planned_not_booked(self):
        result=make_plan(self.ops,self.meetings,self.signals,TODAY)
        events=[i for i in result["items"] if i["opportunity_id"]==7]
        self.assertFalse(any(i["kind"]=="confirmed" for i in events))
        forecast=next(i for i in events if i["kind"]=="estimated")
        self.assertGreaterEqual(forecast["start"],date(2026,10,26))
        self.assertGreater(forecast["end"],forecast["start"])
        self.assertEqual(next(i for i in events if i["kind"]=="action")["start"],
                         date(2026,10,29))

    def test_other_betsson_role_is_not_mislinked(self):
        result=make_plan(self.ops,self.meetings,self.signals,TODAY)
        events=[i for i in result["items"] if i["opportunity_id"]==16]
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["kind"],"action")
        self.assertEqual(events[0]["start"],date(2026,10,30))
        self.assertEqual(events[0]["end"],date(2026,11,6))
        self.assertNotIn("interview",events[0]["label"].lower())

    def test_rejected_and_unknown_processes_not_forecast_as_live(self):
        result=make_plan(self.ops,self.meetings,self.signals,TODAY)
        self.assertEqual({o["id"] for o in result["active"]},{2,7,8,16})
        self.assertEqual({o["id"] for o in result["watch"]},{3})
        self.assertFalse(any(i["opportunity_id"] in (1,3) for i in result["items"]))

    def test_empirical_dates_are_data_driven_and_small_sample(self):
        data=timing_sample(self.ops,self.meetings,self.signals)
        self.assertEqual(data["decision_n"],1)
        self.assertEqual(data["progression_n"],2)
        self.assertEqual(data["n"],3)
        self.assertEqual(data["typical"],17)
        self.assertEqual(data["minimum"],6)

    def test_missing_history_falls_back_to_broad_uncalibrated_window(self):
        res=make_plan(self.ops[:3],self.meetings[:1],[],TODAY)
        # User gets planning ranges, not fabricated confidence probabilities.
        self.assertEqual(res["historical"]["n"],0)
        self.assertTrue(all("probability" not in i for i in res["items"]))
        self.assertTrue(all(i["kind"] in ("estimated","action")
                            for i in res["items"]))


if __name__ == "__main__":
    unittest.main()
