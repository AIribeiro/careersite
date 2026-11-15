"""Isolated Streamlit smoke harness for Investment Advisor's authenticated UX.

Substitutes a single local assessment. Does not connect to Supabase or write
customer data; used to verify layout and navigation logic in CI.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import page_advisory_investment as module
from page_advisory_investment_logic import FIELDS

st.set_page_config(page_title="Investment Advisor UX smoke", layout="wide")

record = {
    "id": "11111111-1111-4111-8111-111111111111",
    "created_at": "2026-11-15T09:00:00+01:00",
    "feedback_rating": None,
    "feedback_usefulness": None,
    "answers": {
        "name": "AI-assisted warranty case routing - European aftersales",
        "context": "Historical shadow pilot, partial evidence; control review pending.",
        "choices": {
            "objective": FIELDS["objective"][1],
            "stage": FIELDS["stage"][2],
            "autonomy": FIELDS["autonomy"][1],
            "non_ai": FIELDS["non_ai"][0],
            "value": FIELDS["value"][1],
            "baseline": FIELDS["baseline"][1],
            "data": FIELDS["data"][1],
            "feasibility": FIELDS["feasibility"][0],
            "capacity": FIELDS["capacity"][1],
            "owner": FIELDS["owner"][0],
            "adoption": FIELDS["adoption"][1],
            "control": FIELDS["control"][1],
            "exposure": FIELDS["exposure"][1],
            "legal": FIELDS["legal"][0],
        },
    },
}

module._history = lambda token, uid: [record]
module.render_private_investment(
    {"access_token": "local-test-only"},
    {"id": "22222222-2222-4222-8222-222222222222",
     "email_confirmed_at": "2026-11-15T08:00:00+00:00"},
)
