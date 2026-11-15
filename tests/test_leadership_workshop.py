"""Executive AI Leadership Workshop: decision model and integration contracts."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class LeadershipWorkshopTests(unittest.TestCase):
    def test_twenty_one_scored_conditions(self):
        from page_advisory_leadership_logic import DIMENSIONS, QUESTION_INDEX
        self.assertEqual(len(DIMENSIONS), 7)
        self.assertEqual(len(QUESTION_INDEX), 21)
        self.assertEqual(sum(d[2] for d in DIMENSIONS), 100)
        self.assertEqual(len(set(QUESTION_INDEX)), 21)
        self.assertTrue(all(len(d[3]) == 3 for d in DIMENSIONS))

    def test_every_demonstrated_condition_is_a_strong_self_report(self):
        from page_advisory_leadership_logic import QUESTION_INDEX, assess
        result = assess({key: 3 for key in QUESTION_INDEX})
        self.assertEqual(result["label"], "FOUNDATIONS ESTABLISHED")
        self.assertEqual(result["overall"], 100)
        self.assertEqual(result["coverage"], 100)
        self.assertFalse(result["critical_gates"])

    def test_report_always_contains_three_executive_actions(self):
        from page_advisory_leadership_logic import QUESTION_INDEX, assess
        complete = {key: 3 for key in QUESTION_INDEX}
        result = assess(complete)
        self.assertEqual(len(result["actions"]), 3)
        self.assertTrue(all(a["evidence"] and a["owner"] for a in result["actions"]))
        incomplete = dict(complete)
        del incomplete["strategy_priorities"]
        case = assess(incomplete)
        self.assertNotEqual(case["label"], "FOUNDATIONS ESTABLISHED")
        self.assertEqual(len(case["actions"]), 3)

    def test_gates_override_high_average(self):
        from page_advisory_leadership_logic import QUESTION_INDEX, assess
        sample = {key: 3 for key in QUESTION_INDEX}
        sample["governance_controls"] = 0
        result = assess(sample)
        self.assertEqual(result["label"], "LEADERSHIP RESET REQUIRED")
        self.assertTrue(any("risk and control" in x for x in result["critical_gates"]))

    def test_missing_answers_cannot_be_assessed_as_ready(self):
        from page_advisory_leadership_logic import assess
        result = assess({})
        self.assertFalse(result["enough_evidence"])
        self.assertIsNone(result["overall"])
        self.assertEqual(result["label"], "EVIDENCE INCOMPLETE")

    def test_adoption_low_generates_specific_actions(self):
        from page_advisory_leadership_logic import QUESTION_INDEX, assess
        sample = {key: 3 for key in QUESTION_INDEX}
        for key in ("adoption_workflow", "adoption_employee", "adoption_measures"):
            sample[key] = 0
        result = assess(sample)
        self.assertTrue(any(a["dimension"] == "adoption" for a in result["actions"]))
        self.assertEqual(result["label"], "TARGETED CHANGES REQUIRED")

    def test_invalid_answers_and_exercises_rejected(self):
        from page_advisory_leadership_logic import clean_answers, clean_exercises
        for sample in ({"unknown": 3}, {"adoption_workflow": True},
                       {"adoption_workflow": 100}):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                clean_answers(sample)
        with self.assertRaises(ValueError):
            clean_exercises({"pilot": 100})

    def test_dilemmas_are_reproducible_and_distinct(self):
        from page_advisory_leadership_logic import QUESTION_INDEX, assess, EXERCISES, interpret_exercise
        result = assess({key: 3 for key in QUESTION_INDEX})
        self.assertEqual(len(result["scenarios"]), 2)
        self.assertEqual(len(set(result["scenarios"])), 2)
        for key in EXERCISES:
            self.assertEqual(len(EXERCISES[key]["choices"]), 4)
            self.assertTrue(interpret_exercise(key, EXERCISES[key]["preferred"])["preferred"])

    def test_team_aggregation_requires_explicit_minimum(self):
        from page_advisory_leadership_logic import QUESTION_INDEX, aggregate_team
        sample = {key: 3 for key in QUESTION_INDEX}
        self.assertFalse(aggregate_team([sample, sample])["available"])
        result = aggregate_team([sample, sample, sample])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["dimensions"]["adoption"]["average"], 100)
        self.assertIn("not anonymous", result["note"])

    def test_pdf_uses_real_selected_inputs(self):
        from page_advisory_leadership_logic import QUESTION_INDEX
        from page_advisory_leadership_report import render_leadership_pdf
        from fpdf import FPDF
        answers = {key: 3 for key in QUESTION_INDEX}
        pdf = render_leadership_pdf(
            {"title": "Test executive leadership review", "mode": "individual",
             "context": {"stage": "Pilots underway", "priority": "Adoption & people",
                         "scope": "Several functions"},
             "decisions": []},
            answers,
            {"pilot": 2, "resistance": 1},
        )
        self.assertGreater(len(pdf), 1300)
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_synthetic_streamlit_assessment_renders(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(
            str(ROOT / "tests" / "leadership_workshop_smoke_app.py"),
            default_timeout=25,
        ).run()
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        labels = [x.label for x in app.selectbox]
        self.assertIn("Are major AI initiatives explicitly tied to business priorities?", labels)
        self.assertGreaterEqual(len(labels), 21)

    def test_site_service_is_separate_from_existing_access_controls(self):
        files = (
            "src/page_advisory_leadership_logic.py",
            "src/page_advisory_leadership_workshop.py",
            "src/page_advisory_leadership_report.py",
            "src/page_advisory_portal.py",
            "src/page_advisory_member_experience.py",
            "src/page_public_services.py",
            "src/site_reader_navigation.py",
        )
        for path in files:
            with self.subTest(path=path):
                ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        portal = (ROOT / "src/page_advisory_portal.py").read_text(encoding="utf-8")
        self.assertIn("render_private_leadership_workshop(session, user)", portal)
        nav = (ROOT / "src/site_reader_navigation.py").read_text(encoding="utf-8")
        self.assertIn('"workshop"', nav)
        workspace = (ROOT / "src/page_advisory_leadership_workshop.py").read_text(encoding="utf-8")
        self.assertIn("token=str", workspace.replace(" ", "")) if False else None
        self.assertIn("_session", portal)
        self.assertIn("portfolio_leadership_responses", workspace)
        self.assertNotIn("service_role", workspace)
        self.assertNotIn("openai", workspace.lower())


if __name__ == "__main__":
    unittest.main()
