from pathlib import Path
import sys
import unittest
from datetime import date
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from job_search_metrics import analyze,canonical_events

START, END = date(2026,9,1),date(2026,10,9)
def event(i,day='2026-09-01',**kwargs):
    return dict(id=i,record_type='evidence_event',is_primary_analytics_record=True,event_date=day,
                employer='Example',role='Director AI',logical_event_key=str(i),snapshot_date='2026-10-07',**kwargs)

class JobAnalyticsTests(unittest.TestCase):
    def test_snapshot_secondary_and_duplicate_not_events(self):
        a=event(1,is_application=True)
        rows=[a,dict(a,id=2),dict(a,id=3,record_type='snapshot_metric'),dict(a,id=4,is_primary_analytics_record=False)]
        self.assertEqual(len(canonical_events(rows)),1)
        self.assertEqual(analyze(rows,START,END)['counts']['Applications'],1)

    def test_ordered_cohort_not_event_ratio(self):
        rows=[event(1,is_application=True),event(2,'2026-09-02',is_human_interaction=True),
              event(3,'2026-09-03',is_human_interaction=True),
              event(4,'2026-09-04',is_interview=True,activity='Interview invitation'),
              event(5,'2026-09-06',is_interview=True,activity='Interview completed'),
              event(6,'2026-09-07',interaction_type='reference_check'),
              event(7,'2026-09-08',stage_outcome='offer_received')]
        r=analyze(rows,START,END)
        self.assertEqual([x['Processes'] for x in r['funnel']],[1,1,1,1,1])
        self.assertEqual(r['counts']['Human interactions'],2)
        self.assertEqual(r['contact_latency']['median'],1)

    def test_invitation_is_not_completion_and_status_is_not_rejection_date(self):
        r=analyze([event(1,is_application=True,is_negative_decision=True,activity='Application submitted',status='Rejected'),
                   event(2,'2026-09-03',is_human_interaction=True,is_interview=True,activity='Interview invitation',status='Interview completed')],START,END)
        self.assertEqual(r['rejection_latency']['n'],0)
        self.assertEqual(r['funnel'][2]['Processes'],0)

    def test_undated_application_does_not_enter_dated_cohort(self):
        r=analyze([event(1,None,is_application=True)],START,END)
        self.assertEqual(r['counts']['Applications'],1)
        self.assertEqual(len(r['cohort']),0)
        self.assertEqual(analyze([event(1,None,is_application=True)],START,END,False)['counts']['Applications'],0)

    def test_response_to_older_followup_does_not_resolve_new_followup(self):
        r=analyze([event(1,'2026-09-01',follow_up_sent=True,response_received=True),
                   event(2,'2026-09-04',follow_up_sent=True,response_received=False)],START,END)
        self.assertTrue(r['processes'][0]['Waiting'])
        r=analyze([event(1,'2026-09-01',follow_up_sent=True),event(2,'2026-09-04',response_received=True)],START,END)
        self.assertFalse(r['processes'][0]['Waiting'])

    def test_latest_closed_state_overrides_old_active_flag(self):
        r=analyze([event(1,is_active=True,status='Active'),event(2,'2026-09-10',is_closed_or_paused=True,status='Closed')],START,END)
        self.assertEqual(r['processes'][0]['State'],'Closed / paused')

    def test_signed_out_route_never_fetches_private_data(self):
        from streamlit.testing.v1 import AppTest
        with patch('page_job_search_analytics.fetch_job_records') as fetch:
            at=AppTest.from_string('from page_analytics_v2 import render_analytics_dashboard\nrender_analytics_dashboard()')
            at.query_params['view']='jobs'
            at.run(timeout=15)
            self.assertFalse(at.exception)
            fetch.assert_not_called()
            self.assertEqual(at.title[0].value,'Portfolio Analytics')
            self.assertEqual(len(at.text_input),1)
            self.assertEqual(len(at.metric),0)

    def test_private_report_renders_graphs_and_empty_metrics(self):
        from streamlit.testing.v1 import AppTest
        code="from page_job_search_analytics import render_job_report\nrender_job_report([dict(id=1,record_type='evidence_event',is_primary_analytics_record=True,event_date='2026-09-01',employer='Example',role='Director AI',is_application=True)])"
        at=AppTest.from_string(code).run(timeout=15)
        self.assertFalse(at.exception)
        self.assertGreaterEqual(len(at.get('vega_lite_chart')),1)
        # The redesigned decision dashboard progressively loads details
        # rather than creating eight nested, fully-rendered tab trees.
        self.assertEqual(len(at.tabs),0)
        self.assertGreaterEqual(len(at.metric),4)
        self.assertIn('Next recruitment actions',[h.value for h in at.subheader])
