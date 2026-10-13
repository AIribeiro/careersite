import unittest
from datetime import date
from job_search_outlook import outlook

TODAY = date(2026, 10, 13)

class OutlookTests(unittest.TestCase):
    def test_panel_renders_missing_and_recent_evidence(self):
        from streamlit.testing.v1 import AppTest
        for jobs in (None, {'daily':[{'d':'2026-10-07','interviews':1}]}):
            code = ('from datetime import date\nfrom job_search_outlook import render_search_outlook\n'
                    f'render_search_outlook({jobs!r},None,date(2026,10,13))')
            app=AppTest.from_string(code).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.metric),3)
            self.assertEqual(app.metric[2].value,'Unavailable')

    def test_interview_evidence_not_promise(self):
        result = outlook({'daily':[{'d':'2026-10-07','interviews':1,'responses':1}]},None,TODAY)
        self.assertTrue(result['verdict'].startswith('Yes'))
        self.assertIn('does not prove',result['caution'])
        self.assertEqual(result['recent']['interviews'],1)

    def test_missing_is_not_zero(self):
        result=outlook(None,None,TODAY)
        self.assertFalse(result['jobs_available'])
        self.assertIn('Not enough',result['verdict'])

    def test_future_and_stale_events_do_not_establish_momentum(self):
        result=outlook({'daily':[{'d':'2026-12-01','interviews':3},{'d':'2026-08-01','responses':1}]},None,TODAY)
        self.assertIn('does not establish',result['verdict'])
        self.assertEqual(result['recent']['interviews'],0)

    def test_provisional_and_old_pipeline_not_fresh(self):
        stages={'as_of':'2026-10-13','stage_buckets':[
            {'stage':'interview','stage_weight':.35,'age_month_index':0,'n':2},
            {'stage':'conversation','stage_weight':1,'age_month_index':1,'n':4},
            {'stage':'application','stage_weight':1,'age_month_index':0,'n':20}]}
        result=outlook({'daily':[]},stages,TODAY)
        self.assertEqual(result['fresh_stages'],0)
        self.assertEqual(result['stale_stages'],6)

    def test_stale_payload_not_current_pipeline(self):
        result=outlook({'daily':[]},{'as_of':'2026-09-01','stage_buckets':[
            {'stage':'interview','stage_weight':1,'age_month_index':0,'n':2}]},TODAY)
        self.assertFalse(result['stages_available'])

    def test_adjacent_windows(self):
        result=outlook({'daily':[{'d':'2026-09-16','responses':2},{'d':'2026-09-15','responses':3}]},None,TODAY)
        self.assertEqual(result['recent']['responses'],2)
        self.assertEqual(result['prior']['responses'],3)
