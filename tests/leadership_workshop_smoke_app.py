"""Synthetic UI smoke for the new leadership service; no live user/data writes."""
from __future__ import annotations
import streamlit as st
import page_advisory_leadership_workshop as service

UID = "00000000-0000-4000-8000-000000000001"
WID = "00000000-0000-4000-8000-000000000002"
PID = "00000000-0000-4000-8000-000000000003"

service._workshops = lambda token: [{
    "id": WID, "owner_id": UID, "title": "Synthetic leadership assessment",
    "mode": "individual", "status": "draft", "context": {
        "stage": "Pilots underway", "priority": "Adoption & people",
        "timeframe": "Next quarter", "scope": "Several functions"},
    "decisions": [], "model_version": "leadership-workshop-v1",
    "created_at": "2026-11-15T14:00:00Z", "updated_at": "2026-11-15T14:00:00Z",
}]
service._participants = lambda token, wid: [{
    "id": PID, "workshop_id": WID, "owner_id": UID, "user_id": UID,
    "invited_email": "synthetic@example.org", "status": "accepted",
    "share_answers": True, "completed": False, "invited_at": "2026-11-15T14:00:00Z",
}]
service._responses = lambda token, wid: []
service._pending = lambda token, email: []
session = {"access_token": "synthetic-local-token"}
user = {"id": UID, "email": "synthetic@example.org",
        "email_confirmed_at": "2026-11-15T14:00:00Z"}
st.query_params["workshop_section"] = "workspace"
st.query_params["workshop_id"] = WID
service.render_private_leadership_workshop(session, user)
