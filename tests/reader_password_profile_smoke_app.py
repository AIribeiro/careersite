"""Exercise real profile/password widgets without accessing live Supabase."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import streamlit as st
from page_reader_native import _render_preferences, _render_password_settings

st.set_page_config(page_title="Reader profile smoke", layout="wide")
st.title("Verified reader profile")
session = {"access_token": "test-only-not-real"}
user = {"id": "00000000-0000-0000-0000-000000000001", "email": "reader@example.invalid"}
profile = {
    "first_name": "Test", "last_name": "Reader",
    "job_title": "AI Director", "organization": "Example Organization",
    "country": "Sweden", "interests": ["AI governance"],
    "newsletter_opt_in": False,
}
_render_preferences(session, profile, user)
_render_password_settings(session)
