"""Safe standalone widget smoke for owner Advisory action inbox."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import streamlit as st
import page_owner_advisory_requests as owner

st.set_page_config(page_title="Advisory owner inbox test",layout="wide")
owner._read_thread=lambda _token,_rid: []
owner.render_advisory_action_inbox(
 "fixture-do-not-send",
 [{"user_id":"00000000-0000-4000-8000-000000000001",
   "email":"executive@example.org","first_name":"Alex"}],
 [{"id":"00000000-0000-4000-8000-000000000002",
   "user_id":"00000000-0000-4000-8000-000000000001",
   "title":"Prioritize enterprise AI opportunities",
   "desired_outcome":"Decide which initiatives deserve investment.",
   "status":"submitted","created_at":"2026-11-13T13:00:00+00:00",
   "updated_at":"2026-11-13T13:00:00+00:00",
   "last_client_at":"2026-11-13T13:00:00+00:00",
   "last_owner_at":None,"contact_preference":"Email",
   "decision_timing":"1–3 months"}],
)
