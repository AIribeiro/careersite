"""No-network Streamlit smoke harness for the authenticated reader workspace."""
from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

import streamlit as st

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_cms import CmsArticle
import page_reader_native as reader


def sample(slug: str, kind: str, category: str, published: str) -> CmsArticle:
    return CmsArticle(
        id=slug, slug=slug, title=slug.replace("-", " ").title(),
        kind=kind, category=category, status="published",
        published_at=published, subtitle="A practical executive decision perspective.",
        excerpt="Evidence, ownership and the trade-offs behind business outcomes.",
        read_minutes=5,
    )


st.set_page_config(layout="wide")
items = (
    sample("member-briefing-example", "Executive Briefing", "AI Governance",
           "2026-11-07T12:00:00+00:00"),
    sample("member-article-example", "Article", "AI Leadership",
           "2026-11-08T12:00:00+00:00"),
    sample("weekly-ai-2026-11-06", "Weekly Brief", "Weekly AI",
           "2026-11-06T12:00:00+00:00"),
)


def member_rows(session, user, table, *, order: str, limit: int = 200):
    if table == "portfolio_reader_saved_briefings":
        return [{"article_slug": "member-briefing-example", "saved_at": "2026-11-10"}]
    if table == "portfolio_reader_downloads":
        return [{
            "article_slug": "member-briefing-example",
            "downloaded_at": "2026-11-11T09:00:00Z",
        }]
    raise AssertionError("Unexpected member collection")


with patch.object(reader, "_register_profile", return_value={
    "first_name": "Reader",
    "created_at": "2026-11-01T00:00:00Z",
    "newsletter_opt_in": False,
}), patch.object(reader, "fetch_published_articles", return_value=items), \
     patch.object(reader, "_reader_collection", side_effect=member_rows), \
     patch.object(reader, "has_briefing_pdf", return_value=False):
    reader._library(
        {"access_token": "test-only-token"},
        {"id": "test-only-reader-id", "email": "member@example.test"},
    )
