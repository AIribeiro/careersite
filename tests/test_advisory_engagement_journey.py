"""Advisory service journey verification, independent of real client credentials."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


class AdvisoryJourneyTests(unittest.TestCase):
    def test_new_advisory_modules_parse(self):
        for file in ("src/page_advisory_client_journey.py",
                     "src/page_owner_advisory_requests.py",
                     "src/page_owner_advisory_management.py",
                     "src/page_advisory_portal.py"):
            ast.parse((ROOT/file).read_text(encoding="utf-8"),filename=file)

    def test_member_request_post_keeps_membership_and_request_distinct(self):
        from page_advisory_client_journey import _create_request
        uid="00000000-0000-4000-8000-000000000001"
        fields={
            "title":"Prioritize our AI portfolio",
            "desired_outcome":"Decide which AI initiatives warrant the next investment.",
            "business_context":"Three departments have competing initiatives.",
            "decision_timing":"1–3 months","contact_preference":"Video call",
        }
        with patch("page_advisory_client_journey._request_json",
                   return_value=[{"id":"request-1"}]) as call:
            _create_request("member-token",uid,fields)
            self.assertIn("portfolio_advisory_requests",call.call_args.args[1])
            self.assertEqual(call.call_args.kwargs["token"],"member-token")
            payload=call.call_args.kwargs["payload"]
            self.assertEqual(payload["user_id"],uid)
            self.assertNotIn("status",payload)
            self.assertNotIn("account_status",payload)
            self.assertNotIn("engagement_status",payload)
        with self.assertRaises(ValueError):
            _create_request("member-token",uid,{**fields,"desired_outcome":"brief"})

    def test_client_reply_cannot_impersonate_advisor(self):
        from page_advisory_client_journey import _reply
        uid="00000000-0000-4000-8000-000000000001"
        with patch("page_advisory_client_journey._request_json",
                   return_value=[{"id":1}]) as call:
            _reply("member-token",uid,"req-1","Here is the missing evidence.")
            payload=call.call_args.kwargs["payload"]
            self.assertEqual(payload["sender"],"client")
            self.assertEqual(payload["user_id"],uid)
            self.assertNotIn("status",payload)

    def test_owner_action_goes_through_authorized_audited_rpc(self):
        from page_owner_advisory_requests import _send_owner_action
        with patch("page_owner_advisory_requests._request_json",
                   return_value={"id":"req-1","status":"awaiting_client"}) as call:
            result=_send_owner_action("owner-token","req-1","ask_client",
                                      message="What is your decision horizon?")
            self.assertEqual(result["status"],"awaiting_client")
            self.assertIn("rpc/portfolio_advisory_request_owner_action_v1",
                          call.call_args.args[1])
            self.assertEqual(call.call_args.kwargs["token"],"owner-token")
        with self.assertRaises(ValueError):
            _send_owner_action("owner-token","req-1","mark_paid")

    def test_owner_inbox_prioritizes_client_submissions(self):
        from page_owner_advisory_requests import _client_waiting,_overdue,_priority
        new={"status":"submitted","last_client_at":"2026-11-13T10:00:00Z",
             "last_owner_at":None,"created_at":"2026-11-13T10:00:00Z"}
        responded={**new,"last_owner_at":"2026-11-13T12:00:00Z"}
        self.assertTrue(_client_waiting(new))
        self.assertFalse(_client_waiting(responded))
        self.assertLess(_priority(new),_priority(responded))
        self.assertFalse(_client_waiting({**new,"status":"awaiting_client"}))
        self.assertFalse(_client_waiting({**new,"status":"closed"}))
        self.assertFalse(_overdue({**new,"follow_up_on":None}))

    def test_analytics_pipeline_is_driven_by_request_not_registration(self):
        from page_owner_advisory_management import _reflect_request_journey
        person={"user_id":"u1","email":"example@example.org",
                "relationship_stage":"engaged","onboarding":"Profile completed"}
        empty=_reflect_request_journey([person],[])
        self.assertEqual(empty[0]["relationship_stage"],"not_requested")
        self.assertEqual(empty[0]["request_count"],0)
        active=_reflect_request_journey([person],[{
            "user_id":"u1","status":"active","created_at":"2026-11-13T14:00:00Z"
        }])
        self.assertEqual(active[0]["relationship_stage"],"engaged")
        self.assertEqual(active[0]["request_count"],1)

    def test_profile_editor_is_secondary_to_business_request(self):
        source=(ROOT/"src/page_advisory_portal.py").read_text(encoding="utf-8")
        account=source.split("def _advisory_account(",1)[1].split(
            "\ndef render_advisory_portal",1)[0]
        self.assertLess(account.index("render_advisory_client_journey("),
                        account.index('st.expander("Your professional profile'))
        client=(ROOT/"src/page_advisory_client_journey.py").read_text(encoding="utf-8")
        self.assertIn("What decision do you need help with?",client)
        self.assertIn("Send my advisory request",client)
        self.assertIn("Your conversation",client)
        self.assertIn("Registration",source)

    def test_owner_has_prominent_action_inbox(self):
        admin=(ROOT/"src/page_owner_advisory_management.py").read_text(encoding="utf-8")
        self.assertIn('"Action inbox"',admin)
        self.assertIn("render_advisory_action_inbox(token, people, requests)",admin)
        owner=(ROOT/"src/page_owner_advisory_requests.py").read_text(encoding="utf-8")
        self.assertIn("Needs your response",owner)
        self.assertIn("Follow-ups due",owner)
        self.assertIn("Start agreed engagement",owner)
        self.assertIn("Mark work completed",owner)


if __name__=="__main__":
    unittest.main()
