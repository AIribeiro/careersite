"""Decision, security-contract and export regression for the AI Portfolio Renewal Advisor."""
from __future__ import annotations

import ast
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile, BadZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from page_advisory_renewal_logic import assess, scenario, validate, MODEL_VERSION

def make_case():
    return {
      "context":{"name":"Enterprise service AI assistant","function":"Customer service",
        "outcome":"Reduce unresolved cases per month","baseline":"42 per 1000 cases, verified Q3",
        "stage":"pilot","owner":"Head of service","authority":"Service investment board",
        "currency":"SEK","horizon_months":12,"next_commitment":150000,
        "opportunity_cost_day":1000,"materiality":0.10,"mandatory_obligation":False,
        "material_nonfinancial":False,"nonfinancial_reviewed":False,
        "review_date":"2027-02-15"},
      "incumbent":{"name":"Existing AI assistant","benefit":600000,"remaining_cost":200000,
        "specialist_days":30,"transition_cost":0,"evidence":"operational",
        "adoption":"ready","operations":"ready","data":"ready","controls":"clear",
        "operating_owner":True,"mandatory_meets":True},
      "alternative":{"name":"Process simplification","route":"process_redesign",
        "benefit":400000,"remaining_cost":250000,"specialist_days":20,
        "transition_cost":10000,"evidence":"operational",
        "adoption":"ready","operations":"ready","data":"ready","controls":"clear",
        "operating_owner":True,"mandatory_meets":True}
    }

class RenewalEngineTests(unittest.TestCase):
    def test_model_version_and_threshold(self):
        case=make_case()
        out=assess(case)
        self.assertEqual(out["version"],MODEL_VERSION)
        self.assertAlmostEqual(out["materiality"],.1)

    def test_renew(self):
        self.assertEqual(assess(make_case())["recommendation"],"RENEW")

    def test_replace(self):
        case=make_case()
        case["alternative"]["benefit"]=800000
        self.assertEqual(assess(case)["recommendation"],"REPLACE")

    def test_test_close_alternatives(self):
        case=make_case()
        case["alternative"]["benefit"]=640000
        self.assertEqual(assess(case)["recommendation"],"TEST")

    def test_test_hypothesis_candidate(self):
        case=make_case()
        case["alternative"]["benefit"]=950000
        case["alternative"]["evidence"]="hypothesis"
        self.assertEqual(assess(case)["recommendation"],"TEST")

    def test_test_unready_candidate(self):
        case=make_case()
        case["alternative"]["benefit"]=900000
        case["alternative"]["adoption"]="partial"
        self.assertEqual(assess(case)["recommendation"],"TEST")

    def test_stop_when_both_nonpositive(self):
        case=make_case()
        case["incumbent"]["benefit"]=15000
        case["alternative"]["benefit"]=15000
        self.assertEqual(assess(case)["recommendation"],"STOP")

    def test_mandatory_duty_prevents_stop(self):
        case=make_case()
        case["incumbent"]["benefit"]=15000
        case["alternative"]["benefit"]=15000
        case["context"]["mandatory_obligation"]=True
        self.assertEqual(assess(case)["recommendation"],"HOLD")

    def test_mandatory_duty_prevents_noncompliant_replace(self):
        case=make_case()
        case["context"]["mandatory_obligation"]=True
        case["alternative"]["benefit"]=950000
        case["alternative"]["mandatory_meets"]=False
        self.assertEqual(assess(case)["recommendation"],"HOLD")

    def test_unpriced_nonfinancial_value_requires_human_review(self):
        case=make_case()
        case["context"]["material_nonfinancial"]=True
        self.assertEqual(assess(case)["recommendation"],"HOLD")

    def test_unpriced_nonfinancial_review_does_not_invent_cash(self):
        case=make_case()
        original=assess(case)
        case["context"]["material_nonfinancial"]=True
        case["context"]["nonfinancial_reviewed"]=True
        out=assess(case)
        self.assertEqual(out["recommendation"],"RENEW")
        self.assertEqual(out["pass_two"],original["pass_two"])

    def test_control_blocker(self):
        case=make_case()
        case["incumbent"]["controls"]="blocked"
        self.assertEqual(assess(case)["recommendation"],"HOLD")

    def test_missing_operating_owner(self):
        case=make_case()
        case["incumbent"]["operating_owner"]=False
        self.assertEqual(assess(case)["recommendation"],"HOLD")

    def test_missing_inputs(self):
        case=make_case()
        del case["context"]["owner"]
        self.assertEqual(assess(case)["recommendation"],"COMPLETE INPUTS")

    def test_negative_money(self):
        case=make_case()
        case["incumbent"]["benefit"]=-1
        self.assertEqual(assess(case)["recommendation"],"COMPLETE INPUTS")

    def test_nan_and_overflow(self):
        for invalid in (float("nan"),float("inf"),1e20):
            with self.subTest(value=invalid):
                case=make_case()
                case["alternative"]["benefit"]=invalid
                self.assertEqual(assess(case)["recommendation"],"COMPLETE INPUTS")

    def test_invalid_horizon(self):
        case=make_case()
        case["context"]["horizon_months"]=0
        self.assertEqual(assess(case)["recommendation"],"COMPLETE INPUTS")

    def test_invalid_materiality(self):
        case=make_case()
        case["context"]["materiality"]=2
        self.assertEqual(assess(case)["recommendation"],"COMPLETE INPUTS")

    def test_switching_cost_flips_recommendation(self):
        case=make_case()
        case["alternative"]["benefit"]=850000
        case["alternative"]["transition_cost"]=0
        self.assertEqual(assess(case)["recommendation"],"REPLACE")
        after,out=scenario(case,{"alternative.transition_cost":750000})
        self.assertEqual(out["recommendation"],"RENEW")
        self.assertEqual(assess(case)["recommendation"],"REPLACE")
        self.assertEqual(after["alternative"]["transition_cost"],750000)

    def test_scarce_capacity_changes_direction(self):
        case=make_case()
        case["alternative"]["benefit"]=860000
        case["alternative"]["specialist_days"]=100
        _,out=scenario(case,{"context.opportunity_cost_day":10000})
        self.assertEqual(out["recommendation"],"RENEW")

    def test_clean_sheet_and_real_world_consequences_can_differ(self):
        case=make_case()
        case["alternative"]["benefit"]=880000
        case["alternative"]["transition_cost"]=600000
        out=assess(case)
        self.assertEqual(out["pass_one"]["direction"],"ALTERNATIVE")
        self.assertEqual(out["pass_two"]["direction"],"INCUMBENT")
        self.assertEqual(out["recommendation"],"RENEW")

    def test_mandatory_duty_sensitivity(self):
        case=make_case()
        case["alternative"]["benefit"]=850000
        _,result=scenario(case,{"context.mandatory_obligation":True,
                                 "alternative.mandatory_meets":False})
        self.assertEqual(result["recommendation"],"HOLD")

    def test_unknown_scenario_rejected(self):
        for change in ({"context.owner":"hacker"},{"unrecognized.secret":1},{}):
            with self.assertRaises(ValueError):scenario(make_case(),change)

    def test_no_sunk_cost_or_hidden_multiplier(self):
        raw=(ROOT/"src/page_advisory_renewal_logic.py").read_text()
        self.assertNotIn('["sunk_cost"]',raw)
        self.assertIn('prospective',raw.lower())
        self.assertIn('opportunity',raw.lower())

class RenewalUIContractTests(unittest.TestCase):
    def test_new_sources_compile(self):
        for name in ("page_advisory_renewal.py","page_advisory_renewal_logic.py",
                     "page_advisory_renewal_reports.py"):
            with self.subTest(name=name):
                ast.parse((ROOT/"src"/name).read_text(encoding="utf-8"))

    def test_routes_and_catalogue(self):
        from advisory_service_visibility import SERVICE_LABELS,PAGE_SERVICES
        self.assertEqual(SERVICE_LABELS["renewal"],"AI Portfolio Renewal Advisor")
        self.assertEqual(PAGE_SERVICES["advisory-renewal"],"renewal")
        source=(ROOT/"main.py").read_text(encoding="utf-8")
        self.assertIn('"advisory-renewal"',source)
        self.assertIn('render_private_renewal(session, user)',
                     (ROOT/"src/page_advisory_portal.py").read_text())

    def test_private_data_is_not_exported_as_static(self):
        source=(ROOT/"src/page_advisory_renewal.py").read_text(encoding="utf-8")
        self.assertIn('"token":token',source)
        self.assertIn('owner_id=eq.',source)
        self.assertIn('.download_button',source)
        self.assertNotIn('openai.',source.lower())
        self.assertNotIn('upload_from_data',source)

    def test_disabled_services_hide_from_regular_members(self):
        from advisory_service_visibility import service_enabled
        with patch("advisory_service_visibility.service_visibility",
                                 return_value={"renewal":False}):
            self.assertFalse(service_enabled("renewal"))
            self.assertTrue(service_enabled("renewal",admin=True))

    def test_owner_scope_and_rls_contract(self):
        source=(ROOT/"supabase/migrations/20261116190000_ai_portfolio_renewal_advisor.sql").read_text()
        for term in ("enable row level security","owner_id=(select auth.uid())",
                     "with check(owner_id=(select auth.uid())",
                     "portfolio_advisory_renewal_versions",
                     "portfolio_advisory_renewal_decisions",
                     "portfolio_renewal_service_allowed",
                     "portfolio_advisory_user_roles"):
            self.assertIn(term,source)
        self.assertNotIn("service_role",source)
        self.assertIn("values ('renewal'",source)

    def test_authenticated_workspace_renders_navigation_and_private_case(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/"tests/renewal_workspace_smoke_app.py"),
                              default_timeout=30).run()
        self.assertFalse(app.exception,[str(e.message) for e in app.exception])
        self.assertTrue(any("Start new assessment" in b.label for b in app.button))
        # Streamlit can rerun a case without a new identity system or redirect.
        app.session_state["renewal_selected"]="11111111-2222-4333-8444-555555555555"
        app.session_state["renewal_section"]="recommendation"
        app.session_state["rn_nav_pills"]="recommendation"
        app.run()
        self.assertFalse(app.exception,[str(e.message) for e in app.exception])
        self.assertTrue(any("Record executive authorization" in b.label
                            for b in app.button))
        self.assertTrue(any("Download executive PDF" in b.label
                            for b in app.button))

    def test_export_case_specific_financial_formulas_and_pdf(self):
        from page_advisory_renewal_reports import report_pdf,report_xlsx
        case=make_case()
        out=assess(case)
        pdf=report_pdf(case,out)
        self.assertTrue(pdf.startswith(b"%PDF"),pdf[:8])
        self.assertGreater(len(pdf),3000)
        book=report_xlsx(case,out)
        with ZipFile(BytesIO(book)) as z:
            names=z.namelist()
            self.assertIn("xl/worksheets/sheet3.xml",names)
            formulas=z.read("xl/worksheets/sheet3.xml").decode()
            self.assertIn("INPUTS!D22",formulas)
            self.assertIn("INPUTS!F25",formulas)
            self.assertIn("<f>",formulas)
            context=z.read("xl/worksheets/sheet2.xml").decode()
            self.assertIn("Enterprise service AI assistant",context)
            self.assertIn("Process simplification",context)
        self.assertNotIn(b"not a blank",book)

if __name__=="__main__":
    unittest.main()
