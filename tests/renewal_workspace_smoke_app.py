"""Offline Streamlit smoke: real Renewal Advisor UI with a synthetic owned case."""
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))

import streamlit as st
from page_advisory_renewal import render_private_renewal
from page_advisory_renewal_logic import assess
from test_ai_portfolio_renewal import make_case

CASE_ID="11111111-2222-4333-8444-555555555555"
INPUTS=make_case()
OUT=assess(INPUTS)
RECORD={
    "id":CASE_ID,"initiative":"Synthetic enterprise service renewal",
    "status":"analyzed","inputs":INPUTS,"analysis":OUT,
    "model_version":OUT["version"],"revision":1,"synthetic":True,
    "next_review":"2027-02-15","created_at":"2026-11-16T12:00:00Z",
    "updated_at":"2026-11-16T12:00:00Z",
}
USER={"id":"11111111-1111-4111-8111-111111111111","email_confirmed_at":"2026-01-01T10:00:00Z"}
SESSION={"access_token":"synthetic-not-a-real-access-token"}

with (
    patch("page_advisory_renewal.advisory_role",return_value="admin"),
    patch("page_advisory_renewal.service_enabled",return_value=True),
    patch("page_advisory_renewal._cases",return_value=[RECORD]),
    patch("page_advisory_renewal._children",return_value=[]),
    patch("page_advisory_renewal._event",return_value=None),
):
    render_private_renewal(SESSION,USER)
