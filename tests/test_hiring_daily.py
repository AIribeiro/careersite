"""Regression tests for autonomous daily and evidence-based hiring refresh."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import math
import sys
import unittest
from unittest.mock import patch

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root / "src"))
from page_hiring_daily import recheck_owner_now, read_daily_history, _days

SQL=(root / "sql" / "20261020_hiring_dual_track_daily.sql").read_text()


def simulate(as_of: date, initial: date, latest: date):
    """The pure date arithmetic used in private.careersite_hiring_core_v3."""
    shifted=7*max(0,math.ceil(max(0,(as_of-initial).days)/7))
    if as_of>latest+timedelta(days=14):
        return None
    return initial+timedelta(days=shifted)


class HiringDailyTests(unittest.TestCase):
    def test_keep_original_centre_until_it_has_elapsed(self):
        mid=date(2026,11,19)
        late=date(2026,12,10)
        for as_of in (date(2026,10,20),date(2026,10,21),
                      date(2026,11,13),mid):
            self.assertEqual(simulate(as_of,mid,late),mid)
        self.assertEqual((mid-date(2026,10,20)).days,30)
        self.assertEqual((mid-date(2026,10,21)).days,29)

    def test_weekly_overdue_steps_and_hard_expiry(self):
        mid=date(2026,11,19)
        late=date(2026,12,10)
        self.assertEqual(simulate(date(2026,11,20),mid,late),
                         date(2026,11,26))
        self.assertEqual(simulate(date(2026,11,26),mid,late),
                         date(2026,11,26))
        self.assertEqual(simulate(date(2026,11,27),mid,late),
                         date(2026,12,3))
        self.assertIsNone(simulate(date(2026,12,25),mid,late))
        self.assertIn("greatest(0,d-base_middle)",SQL)
        self.assertIn("d>base_middle THEN 'overdue_reassessed_weekly'",SQL)
        self.assertIn("d>base_late+14 THEN NULL::date",SQL)
        self.assertNotIn("d-(base_middle-7)",SQL)

    def test_daily_and_hourly_checks_are_independent_from_browser(self):
        self.assertIn("hiring-daily-calendar-0600-utc",SQL)
        self.assertIn("hiring-new-evidence-hourly",SQL)
        self.assertIn("IF reason<>'unchanged' THEN",SQL)
        self.assertIn("context_only_not_scored",SQL)
        self.assertIn("private.careersite_hiring_core_v3()",SQL)
        self.assertIn("Owner sign-in required",SQL)
        self.assertIn("careersite_daily_rechecks_owner_read",SQL)

    def test_owner_token_is_required_for_on_demand_rechecks(self):
        with self.assertRaises(PermissionError):
            recheck_owner_now("")
        with self.assertRaises(PermissionError):
            read_daily_history("")
        with patch("page_hiring_daily._request_json",
                   return_value={"status":"unchanged"}) as api:
            self.assertEqual(recheck_owner_now("owner-jwt")["status"],"unchanged")
            self.assertEqual(api.call_args.kwargs["token"],"owner-jwt")
            self.assertIn("rpc/careersite_hiring_daily_recheck_v1",
                          api.call_args.args[1])
        with patch("page_hiring_daily._request_json",return_value=[]) as api:
            self.assertEqual(read_daily_history("owner-jwt"),[])
            self.assertEqual(api.call_args.kwargs["token"],"owner-jwt")

    def test_invalid_or_expired_dates_are_not_fake_zeroes(self):
        day=date(2026,10,20)
        self.assertEqual(_days("2026-11-19",day),30)
        self.assertIsNone(_days(None,day))
        self.assertIsNone(_days("no-date",day))


if __name__=="__main__":
    unittest.main()
