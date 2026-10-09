"""Privacy, statistical-screening and adaptability regression tests."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from portfolio_job_correlations import (
    _bh_pvalues, _pearson, _site_features, analyze_portfolio_job_correlations,
)


def job_record(i, when, employer, flag, **kwargs):
    return dict(
        id=i, record_type="evidence_event", event_date=when.isoformat(),
        employer=employer, role="AI Strategy Lead", logical_event_key=str(i),
        is_primary_analytics_record=True, **{flag:True}, **kwargs
    )


def fake_data(days=13, with_page=False):
    start=date(2026,9,26)
    daily=[]
    sources=[]
    pages=[]
    jobs=[]
    for j in range(days):
        d=start+timedelta(days=j)
        cv=4 if j%5==0 else (1 if j%3==0 else 0)
        visits=10+j%4
        daily.append(dict(d=d.isoformat(),sessions=visits,engaged_10s=3+j%4,
                          cv_link_visitors=cv,linkedin_visitors=2,article_readers=3,
                          impact_visitors=1,certification_visitors=2,
                          governance_visitors=1,multi_page_visitors=0,hiring_actions=0,
                          social_visitors=3))
        sources.append(dict(d=d.isoformat(),name="cv",sessions=cv))
        if with_page:
            pages.append(dict(d=d.isoformat(),name="new-portfolio-lens",sessions=5))
        if cv>0:
            jobs.append(job_record(100+j,d,"Employer-"+str(j),"is_application"))
    payload=dict(first_day=(start-timedelta(days=1)).isoformat(),
                 tracking_since="2026-09-25T19:17:18Z",
                 through=(start+timedelta(days=days-1)).isoformat(),
                 daily=daily,pages=pages,sources=sources)
    return payload,jobs


class PortfolioJobCorrelationTests(unittest.TestCase):
    def test_short_sample_never_classified_as_repeatable(self):
        payload,jobs=fake_data()
        out=analyze_portfolio_job_correlations(payload,jobs)
        self.assertEqual(out["coverage"]["coverage"],13)
        self.assertEqual(len(out["anchors"]),2)
        self.assertIsNone(out["top_status"])
        self.assertTrue(all(x["status"]!="Repeated association" for x in out["results"]))
        self.assertEqual(out["tested"],0)

    def test_no_outcomes_never_became_positive_correlation(self):
        payload,_=fake_data(100)
        out=analyze_portfolio_job_correlations(payload,[])
        self.assertFalse(out["ranked"])
        self.assertEqual(out["top_status"],None)

    def test_duplicate_records_snapshot_and_rejection_on_application_not_counted(self):
        payload,rows=fake_data()
        base=rows[0]
        rows.append(dict(base,id=999))
        rows.append(dict(base,id=1000,record_type="snapshot_metric"))
        rows.append(dict(base,id=1001,is_primary_analytics_record=False))
        rows.append(job_record(200,date(2026,9,27),"Z","is_application",is_negative_decision=True))
        out=analyze_portfolio_job_correlations(payload,rows)
        self.assertEqual(out["job_daily"][date(2026,9,26)]["applications"],1)
        self.assertEqual(out["job_daily"][date(2026,9,27)]["rejections"],0)

    def test_new_pages_discovered_only_after_minimum_coverage(self):
        payload,jobs=fake_data(16,with_page=True)
        model=analyze_portfolio_job_correlations(payload,jobs)
        self.assertIn("page:new-portfolio-lens",model["features"])
        payload["pages"]=payload["pages"][:2]
        model=analyze_portfolio_job_correlations(payload,jobs)
        self.assertNotIn("page:new-portfolio-lens",model["features"])

    def test_partial_rollout_day_and_incomplete_future_days_are_excluded(self):
        payload,jobs=fake_data()
        payload["daily"].insert(0,dict(d="2026-09-25",sessions=99999,cv_link_visitors=999))
        payload["daily"].append(dict(d="2026-10-20",sessions=999,cv_link_visitors=999))
        model=analyze_portfolio_job_correlations(payload,jobs)
        self.assertEqual(model["coverage"]["first"],date(2026,9,26))
        self.assertEqual(model["coverage"]["end"],date(2026,10,8))
        self.assertEqual(model["coverage"]["coverage"],13)

    def test_multiple_testing_adjusts_all_eligible_candidates(self):
        tests=[dict(p=.01,q=None),dict(p=.02,q=None),dict(p=.4,q=None)]
        _bh_pvalues(tests)
        self.assertAlmostEqual(tests[0]["q"],.03)
        self.assertAlmostEqual(tests[1]["q"],.03)
        self.assertAlmostEqual(tests[2]["q"],.4)

    def test_constant_sparsity_and_independent_dates(self):
        self.assertIsNone(_pearson([1,1,1],[1,2,3]))
        self.assertIsNone(_pearson([1,2],[2,1]))
        site,jobs=fake_data(100)
        out=analyze_portfolio_job_correlations(site,jobs)
        self.assertTrue(all(result["n"]<=100 for result in out["results"]))
        self.assertTrue(all(result["q"] is None or 0<=result["q"]<=1
                            for result in out["results"]))

    def test_never_infers_visitor_to_company_identity(self):
        site,jobs=fake_data(13)
        report=analyze_portfolio_job_correlations(site,jobs)
        self.assertNotIn("session_id",str(report))
        self.assertNotIn("Employer-",str(report["site_daily"]))


if __name__=="__main__":
    unittest.main()
