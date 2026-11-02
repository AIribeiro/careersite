"""Release-level source contracts for the security and reliability briefing."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "src" / "page_executive_briefings.py"
NAVIGATION = ROOT / "src" / "briefing_related_navigation.py"
SLUG = "secure-enterprise-ai-ten-failures-to-control"


def _assigned_constant(source: str, variable: str):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == variable for t in node.targets
        ):
            return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == variable:
                return ast.literal_eval(node.value)
    raise AssertionError(f"Missing source contract: {variable}")


class SecureEnterpriseAIBriefingTests(unittest.TestCase):
    def test_specific_executive_judgment_replaces_generic_fallback(self):
        source = READER.read_text(encoding="utf-8")
        self.assertEqual(_assigned_constant(source, "SECURITY_SLUG"), SLUG)
        decision = _assigned_constant(source, "SECURITY_DECISION")
        self.assertIn("authority", decision["call"])
        self.assertEqual(len(decision["checks"]), 4)
        self.assertIn("SECURITY_DECISION if article.slug == SECURITY_SLUG", source)
        self.assertIn("if article.slug == SECURITY_SLUG else", source)

    def test_contextual_next_reads_are_curated_and_distinct(self):
        source = NAVIGATION.read_text(encoding="utf-8")
        paths = _assigned_constant(source, "EDITORIAL_PATHS")
        self.assertIn(SLUG, paths)
        choices = paths[SLUG]
        self.assertEqual(len(choices), 2)
        self.assertEqual(len({destination for destination, _ in choices}), 2)
        self.assertNotIn(SLUG, {destination for destination, _ in choices})
        self.assertTrue(all(len(rationale) > 35 for _, rationale in choices))
        self.assertIn(SLUG, _assigned_constant(source, "EDITORIAL_INTROS"))


if __name__ == "__main__":
    unittest.main()
