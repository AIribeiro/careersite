"""Regression tests for the selectively approved online AI Portfolio Scorecard."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class ScorecardTests(unittest.TestCase):
    def source(self, p: str) -> str:
        return (ROOT / p).read_text(encoding="utf-8")

    def test_new_modules_parse(self):
        for path in (
            "src/page_advisory_scorecard.py",
            "src/page_advisory_scorecard_workspace.py",
            "src/page_owner_advisory_scorecard.py",
        ):
            with self.subTest(path=path):
                ast.parse(self.source(path), filename=path)

    def test_public_and_private_routes_are_separate(self):
        main = self.source("main.py")
        self.assertIn('PAGE == "advisory-scorecard"', main)
        self.assertIn('PAGE == "advisory-access"', main)
        self.assertIn('render_private_scorecard(session, user)', self.source(
            "src/page_advisory_portal.py"))
        page = self.source("src/page_advisory_scorecard.py")
        self.assertIn("Registration alone does not provide access", self.source(
            "src/page_public_services.py"))
        self.assertIn("enable the private Scorecard individually", page)
        self.assertNotIn("portfolio_advisory_scorecards?select=", page)

    def test_public_page_explains_value_method_experience_and_approval(self):
        page = self.source("src/page_advisory_scorecard.py")
        self.assertIn("The experience behind the method", page)
        self.assertIn("years working across enterprise AI", page)
        self.assertIn("I have been involved in reviewing competing AI initiatives", page)
        self.assertIn("Fictional examples for explanation only", page)
        for phrase in (
            "Service knowledge assistant",
            "Warranty claim triage",
            "Demand forecasting",
            "Management reporting assistant",
            "Strategic fit",
            "Business value",
            "Data readiness",
            "Adoption",
            "Risk and controls",
            "A portfolio recommendation leaders can review and act on.",
            "Not every request is accepted",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, page)
        self.assertIn('href="?page=advisory-access"', page)
        self.assertIn('href="?page=advisory"', page)
        self.assertIn("Registration alone does not provide access", page)
        self.assertNotIn("portfolio_advisory_scorecards?select=", page)

    def test_scorecard_service_has_tablet_and_phone_layouts(self):
        page = self.source("src/page_advisory_scorecard.py")
        self.assertIn("@media(max-width:980px)", page)
        self.assertIn("@media(max-width:760px)", page)
        self.assertIn("minmax(0,1fr)", page)
        self.assertIn("overflow-x:auto", page)
        self.assertIn("width:calc(100% - 36px)", page)

    def test_scoring_and_control_override(self):
        from page_advisory_scorecard_workspace import (
            default_settings, evaluation, new_initiative,
        )
        r = new_initiative()
        r.update({"name": "AI service assistant", "owner": "Service director",
                  "scores": [5]*7, "evidence": "Medium", "gate": "Pass"})
        score, action = evaluation(r, default_settings())
        self.assertEqual(score, 100)
        self.assertEqual(action, "ADVANCE TO CASE")
        r["gate"] = "Block"
        self.assertEqual(evaluation(r, default_settings()), (100, "STOP / REDESIGN"))
        r["gate"] = "Review"
        self.assertEqual(evaluation(r, default_settings()), (100, "CONTROL REVIEW"))
        r["gate"] = "Pass"
        r["evidence"] = "Low"
        self.assertEqual(evaluation(r, default_settings()), (100, "VALIDATE EVIDENCE"))
        r["scores"][0] = 0
        self.assertEqual(evaluation(r, default_settings())[1], "NOT SCORED")

    def test_original_weighted_model_and_capacity(self):
        from page_advisory_scorecard_workspace import (
            capacity_summary,default_settings,evaluation,new_initiative,
        )
        settings=default_settings()
        a=new_initiative()
        a.update({"name":"Reporting AI","owner":"Finance leader",
                  "scores":[3,3,5,5,4,5,4],"evidence":"High",
                  "gate":"Pass","selected":True,"fte_months":2,
                  "investment_sek":120000,"gross_benefit_sek":300000,
                  "run_cost_sek":50000})
        self.assertEqual(evaluation(a,settings),(81,"ADVANCE TO CASE"))
        summary=capacity_summary([a],settings)
        self.assertEqual(summary["annual_net"],250000)
        self.assertEqual(summary["fte_headroom"],10)
        self.assertEqual(summary["budget_headroom"],1080000)
        self.assertEqual(summary["unsigned"],2)

    def test_payload_normalization_is_bounded(self):
        from page_advisory_scorecard_workspace import normalize,new_initiative
        rows=[new_initiative() for _ in range(33)]
        result=normalize({"settings":{"weights":[5]*7},"initiatives":rows})
        self.assertEqual(len(result["initiatives"]),30)
        self.assertEqual(sum(result["settings"]["weights"]),100)

    def test_server_token_and_revision_used_on_save(self):
        from page_advisory_scorecard_workspace import _save
        workspace={"id":"workspace-1","revision":4}
        result={"id":"workspace-1","revision":5}
        with patch("page_advisory_scorecard_workspace._request_json",return_value=result) as req:
            self.assertEqual(_save("member-token",workspace,{"initiatives":[]}),5)
            args=req.call_args
            self.assertEqual(args.kwargs["token"],"member-token")
            self.assertEqual(args.kwargs["payload"]["p_expected_revision"],4)

    def test_owner_action_is_audited_rpc(self):
        from page_owner_advisory_scorecard import _action
        result={"status":"active","id":"scorecard-1"}
        with patch("page_owner_advisory_scorecard._request_json",return_value=result) as req:
            self.assertEqual(_action("owner-token","request-1","approve"),result)
            self.assertIn("portfolio_advisory_scorecard_owner_action_v1",
                          req.call_args.args[1])
            self.assertEqual(req.call_args.kwargs["token"],"owner-token")


if __name__=="__main__":
    unittest.main()
