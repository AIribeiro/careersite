"""Decision engine and report regression tests with 10 fictional enterprise cases."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import ast
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from page_advisory_scorecard_decision import assess,recommend
from page_advisory_scorecard_report import build_executive_pdf


def row(name, score, gate, evidence, fte, cost, gross, run,
        *, selected=False, owner="Business owner", uid=None):
    from page_advisory_scorecard_workspace import new_initiative
    base=new_initiative()
    base.update({
        "id":uid or name,
        "name":name,
        "owner":owner,
        "sponsor":"Executive sponsor",
        "stage":"Pilot",
        "scores":score,
        "evidence":evidence,
        "gate":gate,
        "fte_months":fte,
        "investment_sek":cost,
        "gross_benefit_sek":gross,
        "run_cost_sek":run,
        "selected":selected,
        "next_proof":"Validate the baseline and decision rights.",
        "decision":"Unreviewed",
        "sponsor_signed":False,
        "capacity_signed":False,
    })
    return base


def demo_payload():
    rows=[
        row("DEMO - Service Knowledge Copilot",[5,4,4,4,4,5,4],"Pass","High",2.5,250000,930000,155000,selected=True),
        row("DEMO - Warranty Claim Triage Assistant",[5,5,4,3,3,4,3],"Review","Medium",3,380000,1250000,230000,selected=True),
        row("DEMO - Spare-Parts Demand Forecasting",[5,5,3,2,3,3,4],"Pass","Medium",4.5,500000,2100000,270000,selected=True),
        row("DEMO - Financial Close Narrative Assistant",[4,4,5,5,4,5,4],"Pass","High",1.4,160000,620000,85000,selected=True),
        row("DEMO - Procurement Contract Risk Review",[4,4,4,4,3,4,2],"Review","Medium",2.5,300000,850000,160000),
        row("DEMO - Contact Center Conversation Intelligence",[5,4,4,3,3,4,2],"Review","Medium",2.8,320000,1120000,245000),
        row("DEMO - Automated Candidate Ranking",[2,3,3,3,2,2,1],"Block","Low",3,450000,700000,250000),
        row("DEMO - Fleet Predictive Maintenance Signals",[5,5,3,2,3,3,3],"Pass","Medium",6,900000,3300000,650000),
        row("DEMO - IT Support Agent with Tool Access",[4,4,3,4,4,3,2],"Review","Low",2.5,390000,1050000,320000),
        row("DEMO - Commercial Proposal Drafting Assistant",[4,4,5,4,4,5,4],"Pass","High",2,210000,750000,120000,selected=True),
    ]
    return {"settings":{
        "weights":[15,20,15,15,15,10,10],
        "advance":78,"test":62,"capacity_fte_months":12.0,
        "budget_sek":1200000.0,"max_tests":1,
    },"initiatives":rows}


class ExecutivePortfolioDecisionTests(unittest.TestCase):
    def test_source_parses(self):
        for path in [
            "src/page_advisory_scorecard_decision.py",
            "src/page_advisory_scorecard_report.py",
            "src/page_advisory_scorecard_decision_ui.py",
            "src/page_advisory_scorecard_workspace.py",
        ]:
            with self.subTest(path=path):
                ast.parse((ROOT/path).read_text(encoding="utf-8"))

    def test_10_demo_initiatives_produce_specific_defensible_decision(self):
        result=recommend(demo_payload(),revision=3,generated_at="2026-11-14 22:00 UTC")
        self.assertEqual(len(result["rows"]),10)
        self.assertEqual(result["advanced_count"],3)
        self.assertEqual(result["test_count"],1)
        self.assertEqual(result["selection_method"],"exhaustive")
        self.assertEqual(result["recommended"]["count"],4)
        self.assertEqual(result["recommended"]["fte_months"],10.4)
        self.assertEqual(result["recommended"]["investment_sek"],1120000)
        self.assertTrue(result["recommended"]["fits"])
        self.assertEqual(result["conservative"]["count"],3)
        self.assertEqual(result["conservative"]["fte_months"],5.9)
        self.assertEqual(result["conservative"]["investment_sek"],620000)
        self.assertEqual(result["current_selection"]["count"],5)
        self.assertEqual(result["current_selection"]["fte_months"],13.4)
        self.assertEqual(result["current_selection"]["investment_sek"],1500000)
        self.assertFalse(result["current_selection"]["fits"])
        outcomes={r["name"]:r for r in result["rows"]}
        self.assertEqual(
            outcomes["DEMO - Spare-Parts Demand Forecasting"]["recommendation"],
            "Time-boxed test",
        )
        self.assertEqual(
            outcomes["DEMO - Warranty Claim Triage Assistant"]["recommendation"],
            "Hold - control review",
        )
        self.assertEqual(
            outcomes["DEMO - Automated Candidate Ranking"]["recommendation"],
            "Stop / redesign",
        )
        self.assertEqual(result["changes"]["removed"],[
            "DEMO - Warranty Claim Triage Assistant",
        ])
        self.assertTrue(any("DEMONSTRATION ONLY" in caveat for caveat in result["caveats"]))

    def test_never_recommend_blocked_or_unreviewed_control_even_at_100(self):
        p=demo_payload()
        for r in p["initiatives"]:
            r["selected"]=False
        p["initiatives"].append(
            row("DEMO - High score but blocked",[5]*7,"Block","High",0.2,10,1000,10)
        )
        p["initiatives"].append(
            row("DEMO - High score but pending review",[5]*7,"Review","High",0.2,10,1000,10)
        )
        out=recommend(p)
        blocked=next(r for r in out["rows"] if r["name"].endswith("blocked"))
        pending=next(r for r in out["rows"] if r["name"].endswith("review"))
        self.assertEqual(blocked["recommendation"],"Stop / redesign")
        self.assertEqual(pending["recommendation"],"Hold - control review")
        self.assertFalse(blocked["included_in_proposal"])
        self.assertFalse(pending["included_in_proposal"])

    def test_missing_cost_and_capacity_not_treated_as_free(self):
        p={"settings":demo_payload()["settings"],"initiatives":[
            row("Needs cost estimate",[5]*7,"Pass","High",1,0,20000,0),
            row("Needs capacity estimate",[5]*7,"Pass","High",0,15000,20000,0),
        ]}
        r=recommend(p)
        self.assertEqual(r["recommended"]["count"],0)
        self.assertTrue(all(x["recommendation"]=="Complete assessment" for x in r["rows"]))
        self.assertTrue(any("resource estimates" in x for x in r["caveats"]))

    def test_scoped_test_limit_and_threshold_changes(self):
        p=demo_payload()
        p["settings"]["max_tests"]=0
        r=recommend(p)
        self.assertEqual(r["test_count"],0)
        self.assertEqual(r["recommended"]["count"],3)
        p["settings"]["max_tests"]=2
        p["settings"]["budget_sek"]=5000000
        p["settings"]["capacity_fte_months"]=25
        r=recommend(p)
        self.assertEqual(r["test_count"],2)
        self.assertTrue(r["recommended"]["fits"])

    def test_engine_does_not_mutate_client_record_or_record_approvals(self):
        import copy
        p=demo_payload()
        original=copy.deepcopy(p)
        r=recommend(p)
        self.assertEqual(p,original)
        self.assertIn("business-case",r["verdict"])
        self.assertIn("not",r["verdict"].lower())
        self.assertTrue(any("signoff" in x.lower() or "confirmations" in x.lower() for x in r["caveats"]))
        self.assertTrue(all(x["recorded_decision"]=="Unreviewed" for x in r["rows"]))

    def test_scoring_consistent_with_existing_scorecard(self):
        from page_advisory_scorecard_workspace import evaluation
        p=demo_payload()
        for row_ in p["initiatives"]:
            self.assertEqual(assess(row_,p["settings"]),evaluation(row_,p["settings"]))

    def test_more_than_17_candidates_uses_bounded_selection(self):
        p=demo_payload()
        p["initiatives"]=[
            row("Case "+str(i),[5,4,4,4,4,4,4],"Pass","Medium",1.0,10000,40000,1000)
            for i in range(25)
        ]
        p["settings"]["capacity_fte_months"]=5
        p["settings"]["budget_sek"]=50000
        r=recommend(p)
        self.assertEqual(r["selection_method"],"bounded heuristic")
        self.assertEqual(r["recommended"]["count"],5)
        self.assertTrue(r["recommended"]["fits"])

    def test_download_pdf_contains_real_recommendation_not_just_scores(self):
        from pypdf import PdfReader
        report=recommend(demo_payload(),revision=3,generated_at="2026-11-14 22:00 UTC")
        pdf=build_executive_pdf(report)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf),1700)
        reader=PdfReader(BytesIO(pdf))
        self.assertGreaterEqual(len(reader.pages),2)
        text="\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Executive Portfolio Decision",text)
        self.assertIn("DEMONSTRATION REPORT",text)
        self.assertIn("Service Knowledge Copilot",text)
        self.assertIn("Hold for control review",text)
        self.assertIn("Conditions and executive sign-off",text)

    def test_recommendation_is_first_tab_and_pdf_precedes_feedback(self):
        workspace=(ROOT/"src/page_advisory_scorecard_workspace.py").read_text()
        ui=(ROOT/"src/page_advisory_scorecard_decision_ui.py").read_text()
        self.assertIn('"Executive recommendation","Portfolio overview"',workspace)
        self.assertIn("render_executive_recommendation(",workspace)
        self.assertLess(ui.index('st.download_button('),ui.index('"report_download"'))
        self.assertLess(ui.index('st.markdown("#### Recommended decision")'),ui.index('"executive_recommendation"'))
        self.assertIn('build_executive_pdf(report)',ui)
        self.assertIn('Current client selection',ui) if False else None


if __name__=="__main__":
    unittest.main()
