"""Guard the premium editorial release contract for future executive briefings."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / "src" / "page_admin.py"
STANDARD = ROOT / "docs" / "executive_briefings_editorial_standard.md"
CHANNEL_SELECTION = ROOT / "docs" / "editorial_channel_selection.md"


class ExecutiveBriefingEditorialStandardTests(unittest.TestCase):
    def test_standard_is_linked_from_channel_selection(self):
        standard = STANDARD.read_text(encoding="utf-8")
        editorial = CHANNEL_SELECTION.read_text(encoding="utf-8")
        self.assertIn("executive_briefings_editorial_standard.md", editorial)
        for heading in (
            "The editorial promise",
            "Content architecture: one issue, two speeds",
            "Evidence, accuracy and originality are release blockers",
            "Visual language: premium, restrained and readable",
            "Editorial pre-publication gate",
        ):
            self.assertIn(heading, standard)
        self.assertIn("EU AI Act: What Executives Must Decide Now", standard)
        self.assertIn("hold / revise", standard)
        self.assertIn("live", standard)

    def test_six_human_review_criteria_are_present(self):
        tree = ast.parse(EDITOR.read_text(encoding="utf-8"), filename=str(EDITOR))
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "BRIEFING_REVIEW_CRITERIA"
                    for target in node.targets)
        )
        checks = ast.literal_eval(assignment.value)
        self.assertEqual(len(checks), 6)
        self.assertTrue(all(len(check) > 25 for check in checks))
        self.assertTrue(any("Sources" in check for check in checks))
        self.assertTrue(any("Visual" in check for check in checks))
        self.assertTrue(any("Decision" in check for check in checks))

    def test_publish_gate_is_specific_to_executive_briefings(self):
        tree = ast.parse(EDITOR.read_text(encoding="utf-8"), filename=str(EDITOR))
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "briefing_release_ready"
        )
        module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
        namespace: dict[str, object] = {}
        exec(compile(module, str(EDITOR), "exec"), namespace)
        ready = namespace["briefing_release_ready"]
        self.assertFalse(ready("Executive Briefing", False))
        self.assertFalse(ready(" executive briefing ", False))
        self.assertTrue(ready("Executive Briefing", True))
        self.assertTrue(ready("Article", False))
        self.assertTrue(ready("Weekly Brief", False))

    def test_list_shortcut_does_not_directly_publish_unreviewed_briefing(self):
        source = EDITOR.read_text(encoding="utf-8")
        self.assertIn('"Review to publish"', source)
        self.assertIn("cms_edit_id", source)
        self.assertIn("disabled=not briefing_release_ready(draft.kind, review_acknowledged)", source)
        self.assertIn('if article.kind.strip().casefold() == "executive briefing":', source)


if __name__ == "__main__":
    unittest.main()
