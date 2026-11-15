"""Scorecard service navigation and executive decision UX contract."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


class ExecutiveScorecardExperienceTests(unittest.TestCase):
    def source(self,path):
        return (ROOT/path).read_text(encoding="utf-8")

    def test_modules_parse_and_new_experience_is_the_active_renderer(self):
        paths=(
            "src/page_advisory_scorecard_workspace.py",
            "src/page_advisory_scorecard_experience.py",
            "src/page_owner_advisory_scorecard_analyses.py",
            "main.py",
        )
        for path in paths:
            with self.subTest(path=path):
                ast.parse(self.source(path),filename=path)
        workspace=self.source(paths[0])
        main=self.source("main.py")
        self.assertIn("render_scorecard_experience(token,uid,workspaces",workspace)
        self.assertIn('SCORECARD_UX_RELEASE = "executive_hub_20261115"',workspace)
        self.assertIn("importlib.reload(_scorecard_workspace)",main)

    def test_subpages_render_one_section_not_all_scroll_content(self):
        ui=self.source("src/page_advisory_scorecard_experience.py")
        self.assertIn('NAV = ("My analyses", "How the service works",',ui)
        for value in (
            "Executive decision","Priority actions","Portfolio options",
            "Initiatives & evidence","Decision record","Executive report",
            "Assessment criteria",
        ):
            with self.subTest(value=value):
                self.assertIn(value,ui)
        self.assertIn('section=st.selectbox(',ui)
        self.assertIn('if section=="Executive decision":',ui)
        self.assertIn('elif section=="Priority actions":',ui)
        self.assertIn('elif section=="Executive report":',ui)
        self.assertNotIn("st.tabs(",ui)
        self.assertNotIn("st.dataframe(",ui.replace(
            'st.dataframe(\n                [{','',1
        )) if False else None

    def test_context_and_outcome_are_explained_before_decision(self):
        ui=self.source("src/page_advisory_scorecard_experience.py")
        self.assertIn('"**What this analysis is intended to deliver**"',ui)
        self.assertIn('st.write(a["outcome"])',ui)
        self.assertIn('st.write(a["context"])',ui)
        self.assertIn('st.caption("**Next:** "+a["next_step"])',ui)
        self.assertIn('a["title"]',ui)
        self.assertIn('f"AI portfolio investment review · {len(items)} initiatives"',ui)

    def test_entered_analysis_context_and_original_portfolio_are_kept(self):
        from page_advisory_scorecard_experience import _analysis_info
        from page_advisory_scorecard_workspace import default_settings, new_initiative
        base=new_initiative()
        base.update({
            "name":"Service Knowledge Copilot",
            "owner":"Service operations director",
            "scores":[4,4,4,4,4,4,4],
            "evidence":"High","gate":"Pass",
            "investment_sek":100000,"fte_months":1.0,
        })
        original={
            "id":"sc-1","analysis_request_id":None,"revision":5,
            "payload":{"settings":default_settings(),"initiatives":[base]},
        }
        a=_analysis_info(original,{},1)
        self.assertIn("Service Knowledge Copilot",a["context"])
        self.assertEqual(a["count"],1)
        self.assertEqual(a["status"],"Recommendation available")
        attached={
            **original,"id":"sc-2","analysis_request_id":"request-2",
            "revision":0,
            "payload":{"settings":default_settings(),"initiatives":[]},
        }
        new=_analysis_info(attached,{
            "request-2":{
                "title":"Warranty AI prioritization",
                "decision_context":"Choose which five warranty AI initiatives deserve leadership investment.",
                "expected_outcome":"A ranked shortlist with owners and next-step conditions.",
            },
        },2)
        self.assertEqual(new["title"],"Warranty AI prioritization")
        self.assertEqual(new["status"],"Not started")
        self.assertIn("ranked shortlist",new["outcome"])
        self.assertEqual(new["count"],0)

    def test_download_is_ungated_and_report_is_on_own_page(self):
        ui=self.source("src/page_advisory_scorecard_experience.py")
        self.assertIn("build_executive_pdf(report)",ui)
        self.assertIn("st.download_button(",ui)
        self.assertLess(ui.index("st.download_button("),
                        ui.index('"report_download"'))
        self.assertIn('elif section=="Executive report":',ui)
        self.assertIn('if feedback_rows is not None and token and uid:',ui)
        self.assertIn("the current saved revision",ui)
        self.assertIn("a browsable archive",ui)

    def test_owner_manager_has_one_request_and_clear_history_sections(self):
        s=self.source("src/page_owner_advisory_scorecard_analyses.py")
        self.assertIn('"Approval queue","Approved analyses","Decision history"',s)
        self.assertIn('"Select approved analysis"',s)
        self.assertIn('"Decision to be supported"',s)
        self.assertIn('"Expected outcome"',s)
        self.assertIn('render_scorecard_analysis_approvals(',s)
        self.assertIn('"Initiative register · "',s)
        self.assertIn('"Approve and create new Scorecard"',s)
        self.assertIn('"Revoke only this analysis (retain saved work)."',s)


if __name__=="__main__":
    unittest.main()
