"""Scorecard member request tests: one-open-request rule and owner handoff."""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))


class ScorecardAccessRequestTests(TestCase):
    def test_modules_compile_and_client_action_is_present(self):
        for path in (
            "src/page_advisory_scorecard_requests.py",
            "src/page_advisory_scorecard_workspace.py",
            "src/page_owner_advisory_requests.py",
        ):
            ast.parse((ROOT/path).read_text(encoding="utf-8"),filename=str(path))
        workspace=(ROOT/"src/page_advisory_scorecard_workspace.py").read_text()
        self.assertIn("render_scorecard_access_request(token, uid)",workspace)
        client=(ROOT/"src/page_advisory_scorecard_requests.py").read_text()
        self.assertIn('"Request Access"',client)
        self.assertIn('"Submit access request"',client)
        self.assertNotIn("portfolio_advisory_scorecard_owner_action_v1",client)

    def test_member_sees_service_details_and_page_link_before_request(self):
        source=(ROOT/"src/page_advisory_scorecard_workspace.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("which initiatives to advance, test, hold ",source)
        self.assertIn("Compare opportunities:",source)
        self.assertIn("Test portfolio constraints:",source)
        self.assertIn("Record executive decisions:",source)
        self.assertIn("https://jairribeiro.com/?page=advisory-scorecard",source)
        self.assertIn("Explore the full Scorecard service",source)
        self.assertLess(
            source.index("Explore the full Scorecard service"),
            source.index("render_scorecard_access_request(token, uid)")
        )

    def test_existing_engagement_receives_a_message_not_duplicate_request(self):
        from page_advisory_scorecard_requests import submit_scorecard_access
        current={"id":"engagement-one","status":"active","title":"Existing advisory discussion"}
        with (
            patch("page_advisory_scorecard_requests._find_request_context",return_value=(current,False)),
            patch("page_advisory_scorecard_requests._reply") as reply,
            patch("page_advisory_scorecard_requests._create_request") as create,
        ):
            result=submit_scorecard_access("member-token","user-one",
                                          "We need to decide which AI pilots to scale.",
                                          "A defensible capacity-constrained priority list.",
                                          "This month")
            self.assertEqual(result,"added_to_engagement")
            self.assertEqual(reply.call_args.args[:3],("member-token","user-one","engagement-one"))
            self.assertIn("AI PORTFOLIO SCORECARD ACCESS REQUEST",reply.call_args.args[3])
            create.assert_not_called()

    def test_no_existing_engagement_opens_formal_advisory_request(self):
        from page_advisory_scorecard_requests import submit_scorecard_access,SCORECARD_REQUEST_TITLE
        with (
            patch("page_advisory_scorecard_requests._find_request_context",return_value=(None,False)),
            patch("page_advisory_scorecard_requests._create_request") as create,
            patch("page_advisory_scorecard_requests._reply") as reply,
        ):
            status=submit_scorecard_access("token","user",
                                           "Our AI demand pipeline exceeds delivery capacity.",
                                           "Prioritize a viable portfolio with executive owners.",
                                           "1–3 months")
            self.assertEqual(status,"new_request")
            self.assertEqual(create.call_args.args[2]["title"],SCORECARD_REQUEST_TITLE)
            reply.assert_not_called()

    def test_duplicate_request_is_idempotent(self):
        from page_advisory_scorecard_requests import submit_scorecard_access
        with (
            patch("page_advisory_scorecard_requests._find_request_context",return_value=({"id":"already"},True)),
            patch("page_advisory_scorecard_requests._reply") as reply,
            patch("page_advisory_scorecard_requests._create_request") as create,
        ):
            self.assertEqual(submit_scorecard_access(
                "token","user","Business decision to rank our most important AI investments.",
                "A repeatable, justified allocation decision.","Exploratory"),
                "already_requested")
            reply.assert_not_called()
            create.assert_not_called()

    def test_detects_scorecard_request_in_existing_conversation(self):
        from page_advisory_scorecard_requests import _find_request_context
        requests=[{"id":"case-a","status":"active","title":"AI business case review"}]
        messages=[{"sender":"client","body":"AI PORTFOLIO SCORECARD ACCESS REQUEST\\nPortfolio decision: priorities"}]
        with (
            patch("page_advisory_scorecard_requests._client_requests",return_value=requests),
            patch("page_advisory_scorecard_requests._request_messages",return_value=messages),
        ):
            self.assertEqual(_find_request_context("token","member"),(requests[0],True))

    def test_incomplete_request_does_not_write(self):
        from page_advisory_scorecard_requests import submit_scorecard_access
        with patch("page_advisory_scorecard_requests._reply") as reply:
            with self.assertRaises(ValueError):
                submit_scorecard_access("token","user","Too vague",
                                        "Too short","Exploratory")
            reply.assert_not_called()

    def test_owner_sees_a_specific_scorecard_signal(self):
        owner=(ROOT/"src/page_owner_advisory_requests.py").read_text()
        self.assertIn("AI PORTFOLIO SCORECARD ACCESS REQUEST",owner)
        self.assertIn("Scorecard access requested",owner)
        self.assertIn("enable the workspace below",owner)
