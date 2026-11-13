"""Safe standalone widget smoke for the Advisory client request experience."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import streamlit as st
import page_advisory_client_journey as journey

st.set_page_config(page_title="Advisory client journey test",layout="wide")
journey._client_requests=lambda _token,_uid: []
journey.render_advisory_client_journey(
    {"access_token":"fixture-do-not-send"},
    {"id":"00000000-0000-4000-8000-000000000001"},
    {"first_name":"Alex","organization":"Example Corp","account_status":"active"},
)
