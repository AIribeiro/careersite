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
import page_hiring_daily
from page_hiring_daily import read_daily_history, _days

SQL=(root / "sql" / "20261020_hiring_dual_track_daily.sql").read_text()
DAILY=(root / "sql" / "20261020_hiring_daily_only_antiloop.sql").read_text()


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

    def test_daily_only_schedule_guards_and_no_page_recompute(self):
        self.assertIn("hiring-daily-calendar-0600-utc", DAILY)
        self.assertIn("cron.unschedule('hiring-new-evidence-hourly')", DAILY)
        self.assertNotIn("cron.schedule('hiring-new-evidence-hourly'", DAILY)
        self.assertIn("pg_try_advisory_xact_lock(191000, 24)", DAILY)
        self.assertIn("'status','already_running'", DAILY)
        self.assertIn("'status','already_checked_today'", DAILY)
        self.assertLess(DAILY.index("already_checked_today"),
                        DAILY.index("calc := private.careersite_hiring_core_v3()"))
        self.assertIn("REVOKE EXECUTE ON FUNCTION public.careersite_hiring_daily_recheck_v1()", DAILY)
        self.assertFalse(hasattr(page_hiring_daily, "recheck_owner_now"))
        overview=(root / "src" / "page_analytics_overview.py").read_text()
        market=(root / "src" / "page_job_market_insights.py").read_text()
        self.assertIn('_REFRESH_INTERVAL = "24h"', overview)
        self.assertEqual(market.count('@st.fragment(run_every="24h")'),2)
        for forbidden in ("recheck_owner_now(", "record_v2_daily_first(",
                          "publish_v2_timing(", "record_shadow(",
                          "fetch_hiring_prediction_v2("):
            self.assertNotIn(forbidden,overview)
        self.assertIn("read_daily_history(",overview)
        self.assertIn("read_daily_history(",market)
        self.assertNotIn("fetch_hiring_prediction_v2(",market)

    def test_history_is_read_only_and_requires_owner_token(self):
        with self.assertRaises(PermissionError):
            read_daily_history("")
        with patch("page_hiring_daily._request_json",return_value=[]) as api:
            self.assertEqual(read_daily_history("owner-jwt"),[])
            self.assertEqual(api.call_args.kwargs["token"],"owner-jwt")
            self.assertEqual(api.call_args.args[0],"GET")

    def test_invalid_or_expired_dates_are_not_fake_zeroes(self):
        day=date(2026,10,20)
        self.assertEqual(_days("2026-11-19",day),30)
        self.assertIsNone(_days(None,day))
        self.assertIsNone(_days("no-date",day))


if __name__=="__main__":
    unittest.main()
