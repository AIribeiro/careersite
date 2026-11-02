from __future__ import annotations

import unittest
from types import SimpleNamespace

from briefing_content_policy import validate_briefing_employer_anonymity


def briefing(**overrides):
    values = {
        "kind": "Executive Briefing",
        "title": "A decision about data ownership",
        "slug": "data-ownership-decision",
        "subtitle": "An anonymized operating example",
        "content_html": "<p>An illustrative service workflow with no company identified.</p>",
        "source_url": "https://csrc.nist.gov/glossary/term/machine_learning",
        "meta_description": "Decision, trade-offs and accountable owner",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ExecutiveBriefingAnonymityTests(unittest.TestCase):
    def test_employer_names_are_blocked_in_public_fields(self):
        cases = (
            ("content_html", "<p>A case from Volvo Group</p>"),
            ("content_html", "<p>Nothing from MSXi is disclosed.</p>"),
            ("content_html", "<p>Example from Kimberly-Clark.</p>"),
            ("source_url", "https://www.ibm.com/think/topics/ai"),
            ("subtitle", "Hewlett Packard Enterprise experience"),
            ("meta_description", "HPE was the starting point"),
            ("title", "MSX International data case"),
            ("content_html", "<p>Kimberly‑Clark operations</p>"),
            ("source_url", "https://example.org/?context=%56olvo"),
            ("keywords", ("AI governance", "IBM programme")),
            ("category", "HPE operating model"),
            ("hashtags", ("#MSXi",)),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(ValueError, "must not identify"):
                    validate_briefing_employer_anonymity(briefing(**{field: value}))

    def test_anonymous_case_and_neutral_source_are_accepted(self):
        validate_briefing_employer_anonymity(briefing())

    def test_other_article_formats_can_attribute_employers(self):
        validate_briefing_employer_anonymity(
            briefing(kind="Article", content_html="<p>Experience at Volvo Trucks</p>")
        )

    def test_partial_words_do_not_trigger_a_false_positive(self):
        validate_briefing_employer_anonymity(
            briefing(content_html="<p>Machine learning and blockchain implications</p>")
        )


if __name__ == "__main__":
    unittest.main()
