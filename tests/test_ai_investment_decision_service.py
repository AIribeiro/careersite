"""Regression coverage: a single AI opportunity, not portfolio ranking or rollout."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from page_advisory_investment_logic import FIELDS, MODEL_VERSION, assess, validate


def case(**overrides):
    selections = {
        "objective": FIELDS["objective"][0],
        "stage": FIELDS["stage"][2],
        "autonomy": FIELDS["autonomy"][0],
        "non_ai": FIELDS["non_ai"][0],
        "value": FIELDS["value"][0],
        "baseline": FIELDS["baseline"][0],
        "data": FIELDS["data"][0],
        "feasibility": FIELDS["feasibility"][0],
        "capacity": FIELDS["capacity"][0],
        "owner": FIELDS["owner"][0],
        "adoption": FIELDS["adoption"][0],
        "control": FIELDS["control"][0],
        "exposure": FIELDS["exposure"][0],
        "legal": FIELDS["legal"][0],
    }
    selections.update(overrides)
    return {"name": "AI customer case routing", "context": "", "choices": selections}


class ExecutiveDecisionAdvisorTests(unittest.TestCase):
    def test_modules_parse(self):
        for path in ("src/page_advisory_investment_logic.py",
                     "src/page_advisory_investment.py",
                     "src/page_advisory_portal.py", "main.py"):
            ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)

    def test_four_decision_outcomes(self):
        self.assertEqual(assess(case())["verdict"], "INVEST")
        self.assertEqual(
            assess(case(value=FIELDS["value"][1], baseline=FIELDS["baseline"][1]))["verdict"],
            "EXPERIMENT")
        self.assertEqual(assess(case(owner=FIELDS["owner"][2]))["verdict"], "HOLD")
        self.assertEqual(assess(case(legal=FIELDS["legal"][2]))["verdict"], "STOP")

    def test_business_objective_and_maturity_affect_advice(self):
        early = assess(case(stage=FIELDS["stage"][0]))
        self.assertEqual(early["verdict"], "EXPERIMENT")
        self.assertTrue(any("limited evidence-gathering test" in a["text"]
                            for a in early["actions"]))
        outcome = assess(case(objective=FIELDS["objective"][2],
                              value=FIELDS["value"][1]))
        self.assertIn("revenue", outcome["decision_lens"])

    def test_gates_override_business_case(self):
        self.assertEqual(assess(case(exposure=FIELDS["exposure"][2],
                                     legal=FIELDS["legal"][1]))["verdict"], "HOLD")
        self.assertEqual(assess(case(autonomy=FIELDS["autonomy"][3],
                                     control=FIELDS["control"][1]))["verdict"], "HOLD")
        self.assertEqual(assess(case(non_ai=FIELDS["non_ai"][1]))["verdict"], "STOP")
        self.assertEqual(assess(case(data=FIELDS["data"][3]))["verdict"], "STOP")

    def test_evidence_does_not_invent_business_results(self):
        report = assess(case(value=FIELDS["value"][2], baseline=FIELDS["baseline"][2]))
        self.assertEqual(report["verdict"], "EXPERIMENT")
        self.assertNotEqual(report["confidence"], "Higher (self-reported)")
        self.assertEqual(len(report["actions"]), 3)
        for action in report["actions"]:
            self.assertTrue(action["owner"])
            self.assertTrue(action["trigger"])
        self.assertEqual(report["model_version"], MODEL_VERSION)

    def test_rejects_invalid_or_missing_evidence(self):
        for invalid in (
            {"name": "Short", "choices": {}},
            {**case(), "name": "<"},
            {**case(), "choices": {**case()["choices"], "legal": "I approve this"}},
            {**case(), "context": "X" * 501},
        ):
            with self.subTest(invalid=str(invalid)[:100]):
                with self.assertRaises(ValueError):
                    validate(invalid)

    def test_public_and_private_routes_reuse_auth(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        portal = (ROOT / "src/page_advisory_portal.py").read_text(encoding="utf-8")
        nav = (ROOT / "src/site_reader_navigation.py").read_text(encoding="utf-8")
        page = (ROOT / "src/page_advisory_investment.py").read_text(encoding="utf-8")
        self.assertIn('"advisory-decision"', main)
        self.assertIn('elif view == "decision"', portal)
        self.assertIn('"decision": "Investment Advisor"', (
            ROOT / "src/page_advisory_member_experience.py").read_text(encoding="utf-8"))
        self.assertIn('"advisory-decision"', nav)
        self.assertIn("view=decision", page)
        self.assertIn("render_private_investment", page)
        self.assertIn("feedback_rating", page)
        self.assertIn("st.download_button", page)

    def test_short_guided_form_renders_without_database_access(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "advisory_investment_smoke_app.py"),
            default_timeout=30,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertEqual(len(app.selectbox), len(FIELDS))
        self.assertTrue(any("AI opportunity" in x.label for x in app.text_input))
        self.assertTrue(any("Generate my executive decision brief" in x.label
                            for x in app.button))

    def test_advisory_cards_are_present_in_expected_order(self):
        page = (ROOT / "src/page_public_services.py").read_text(encoding="utf-8")
        a = page.index('data-analytics-section="advisory-scorecard"')
        b = page.index('data-analytics-section="advisory-rollout"')
        c = page.index('data-analytics-section="advisory-decision"')
        self.assertLess(a, b)
        self.assertLess(b, c)
        self.assertIn('href="?page=advisory-decision"', page)
        self.assertIn("no individual service approval required", page.lower())

    def test_pdf_is_premium_two_page_executive_brief(self):
        from io import BytesIO
        from pypdf import PdfReader
        from page_advisory_investment import _pdf_report

        raw = case(
            value=FIELDS["value"][1], baseline=FIELDS["baseline"][1],
            data=FIELDS["data"][1], control=FIELDS["control"][1],
            capacity=FIELDS["capacity"][1],
        )
        raw["name"] = "AI-assisted warranty case routing - European aftersales"
        raw["context"] = (
            "Two-market shadow pilot against historical service routing cases. "
            "Measured live benefit has not yet been established and controls are pending."
        )
        result = assess(raw)
        result_pdf = _pdf_report(raw, result, "2026-11-15")
        self.assertTrue(result_pdf.startswith(b"%PDF"))
        self.assertGreater(len(result_pdf), 3500)

        reader = PdfReader(BytesIO(result_pdf))
        self.assertEqual(len(reader.pages), 2)
        page_one = reader.pages[0].extract_text()
        page_two = reader.pages[1].extract_text()
        self.assertIn("EXECUTIVE SUMMARY", page_one)
        self.assertIn("THREE PRIORITY ACTIONS", page_one)
        self.assertIn("EXPERIMENT", page_one)
        self.assertIn("OWNER", page_one)
        self.assertIn("PROOF", page_one)
        self.assertIn("EVIDENCE", page_two.upper())
        self.assertIn("DATA READINESS", page_two.upper())
        self.assertIn("CONTEXT SUPPLIED BY THE RESPONDENT", page_two.upper())
        self.assertNotIn("Self-reported. Self-reported", page_one + page_two)

    def test_pdf_renders_for_all_verdicts_and_long_notes(self):
        from io import BytesIO
        from pypdf import PdfReader
        from page_advisory_investment import _pdf_report

        raw_cases = [
            case(), case(value=FIELDS["value"][1]), 
            case(owner=FIELDS["owner"][2]),
            case(legal=FIELDS["legal"][2]),
        ]
        for raw in raw_cases:
            raw["context"] = "Non-confidential working context. " * 15
            raw["context"] = raw["context"][:500]
            with self.subTest(verdict=assess(raw)["verdict"]):
                pdf_bytes = _pdf_report(raw, assess(raw), "2026-11-15")
                pages = PdfReader(BytesIO(pdf_bytes)).pages
                self.assertEqual(len(pages), 2)
                self.assertIn(assess(raw)["verdict"], pages[0].extract_text())
                self.assertIn("PRIORITY", pages[0].extract_text())


if __name__ == "__main__":
    unittest.main()
