"""Streamlit smoke harness for the owner-only reader workspace.

Uses mock owner data only; never accesses live Supabase or reader identities.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import page_owner_reader_management as manager
import page_reader_campaign_drafts as drafts

profile = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "email": "test-reader@example.invalid",
    "first_name": "Test",
    "newsletter_opt_in": True,
    "newsletter_consent_at": "2026-11-12T12:00:00Z",
    "consent_notice_version": "2026-11-reader-v1",
    "created_at": "2026-11-12T12:00:00Z",
    "acquisition_source": "briefing_pdf",
}
sample = {
    "portfolio_reader_profiles": [profile],
    "portfolio_reader_downloads": [],
    "portfolio_reader_saved_briefings": [],
    "portfolio_reader_consent_events": [],
    "portfolio_reader_admin_controls": [],
    "portfolio_reader_admin_audit": [],
}
manager._verify_owner = lambda session: "smoke-test-only"
manager._read_table = lambda token, table: sample[table]
drafts._verified_owner = lambda token: "00000000-0000-0000-0000-000000000002"
drafts._fetch_drafts = lambda token: []

st.set_page_config(page_title="Private Reader Management Smoke", layout="wide")
manager.render_owner_reader_management({"access_token": "smoke-test-only"})
