"""Isolated Advisory password-creation page for Streamlit widget smoke tests."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "src"))
import streamlit as st
from page_advisory_portal import ADVISORY_CSS, _first_password_form
st.set_page_config(page_title="Advisory password setup smoke",layout="wide")
st.html(ADVISORY_CSS)
_first_password_form(
    {"access_token": "fixture-do-not-send", "refresh_token": "fixture"},
    {"id": "test-member", "email": "test@example.invalid", "email_confirmed_at": "fixture"},
)
