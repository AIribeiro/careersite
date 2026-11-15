"""Premium Requests workspace contracts: accurate statuses and shared visual language."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class PremiumRequestsTests(unittest.TestCase):
    def test_page_parses_and_uses_rollout_ui(self):
        body = (ROOT / "src/page_advisory_member_experience.py").read_text(encoding="utf-8")
        ast.parse(body)
        self.assertIn("from page_rollout_workspace_ui import WORKSPACE_CSS", body)
        self.assertIn("WORKSPACE_CSS + REQUEST_CSS", body)
        for item in ("About requests", "Current request", "My history", "New request",
                     "One business question. A clear path to the next decision.",
                     "What happens next", "What this request contains"):
            self.assertIn(item, body)
        self.assertIn('st.query_params["requests_section"]', body)
        self.assertIn("_request_form(token, uid, profile)", body)

    def test_status_guidance_reuses_conversation_logic(self):
        from page_advisory_member_experience import _request_guidance
        from page_advisory_conversation_workspace import STATE_GUIDANCE
        for status in ("submitted", "reviewing", "awaiting_client", "proposal",
                       "completed", "closed", "declined"):
            with self.subTest(status=status):
                self.assertEqual(_request_guidance({"status": status}),
                                 STATE_GUIDANCE[status])
        self.assertIn("no response is required", _request_guidance({"status": "reviewing"}))

    def test_request_title_and_client_details_are_escaped(self):
        from page_advisory_member_experience import _request_case, _request_context
        sample = {
            "id": "sample",
            "title": "<script>bad()</script>",
            "created_at": "2026-11-15T09:00:00Z",
            "status": "reviewing",
            "desired_outcome": "<img src=x onerror=bad()>",
            "business_context": "<not-trusted>",
            "decision_timing": "Within 30 days",
            "contact_preference": "Email",
        }
        with patch("page_advisory_member_experience.st.html") as html:
            _request_case(sample)
            _request_context(sample)
        rendered = "".join(str(c.args[0]) for c in html.call_args_list)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;img src=x onerror=bad()&gt;", rendered)
        self.assertIn("&lt;not-trusted&gt;", rendered)
        self.assertNotIn("<script>bad()", rendered)

    def test_review_is_not_approval_and_next_step_is_labelled_as_recorded(self):
        from page_advisory_member_experience import _request_next_step
        with patch("page_advisory_member_experience.st.html") as html:
            _request_next_step({"status": "reviewing", "next_step": "Access the services"})
        rendered = " ".join(str(c.args[0]) for c in html.call_args_list)
        self.assertIn("no response is required", rendered)
        self.assertIn("Next step recorded in your advisory request", rendered)
        self.assertIn("Access the services", rendered)
        self.assertIn("not a promised date or approval", rendered)

    def test_mobile_rules_and_one_open_request_are_preserved(self):
        body = (ROOT / "src/page_advisory_member_experience.py").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:760px),(max-device-width:760px)", body)
        self.assertIn("One open advisory request at a time", body)
        self.assertIn("if current:", body)
        self.assertIn("navigate(\"messages\", str(current[\"id\"]))", body)
        self.assertIn("Service access is", body)


if __name__ == "__main__":
    unittest.main()
