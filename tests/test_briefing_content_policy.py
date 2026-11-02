from __future__ import annotations

from types import SimpleNamespace

import pytest

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


@pytest.mark.parametrize(
    "field,value",
    [
        ("content_html", "<p>A case from Volvo Group</p>"),
        ("content_html", "<p>Nothing from MSXi is disclosed.</p>"),
        ("content_html", "<p>Example from Kimberly-Clark.</p>"),
        ("source_url", "https://www.ibm.com/think/topics/ai"),
        ("subtitle", "Hewlett Packard Enterprise experience"),
        ("meta_description", "HPE was the starting point"),
        ("title", "MSX International data case"),
    ],
)
def test_employer_names_cannot_be_saved_in_briefing(field, value):
    with pytest.raises(ValueError, match="must not identify"):
        validate_briefing_employer_anonymity(briefing(**{field: value}))


def test_anonymous_field_informed_case_and_independent_sources_allowed():
    validate_briefing_employer_anonymity(briefing())


def test_other_article_formats_may_retain_attributed_employers():
    validate_briefing_employer_anonymity(
        briefing(kind="Article", content_html="<p>Experience at Volvo Trucks</p>")
    )


def test_partial_word_does_not_trigger_name_guard():
    validate_briefing_employer_anonymity(
        briefing(content_html="<p>Machine learning and blockchain implications</p>")
    )
