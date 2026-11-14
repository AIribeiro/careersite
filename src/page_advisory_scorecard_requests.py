"""Member-initiated access requests for the on-demand Advisory Scorecard.

Reuses the established Advisory request and conversation lifecycle. The
database allows only one open Advisory engagement per member; never create a
parallel request when an open engagement already exists.
"""
from __future__ import annotations

import streamlit as st

from page_advisory_client_journey import (
    _client_requests, _request_messages, _create_request, _reply, CLOSED,
)

SCORECARD_REQUEST_TITLE = "AI Portfolio Prioritization Scorecard — access request"
SCORECARD_MESSAGE_MARKER = "AI PORTFOLIO SCORECARD ACCESS REQUEST"
SCORECARD_OPEN_FORM_KEY = "advisory_scorecard_request_form_open"


def _find_request_context(token: str, uid: str) -> tuple[dict | None, bool]:
    """Return current request and whether the scorecard has already been requested."""
    requests = _client_requests(token, uid)
    current = next((r for r in requests if str(r.get("status")) not in CLOSED), None)
    if current is None:
        return None, False
    if str(current.get("title") or "").casefold() == SCORECARD_REQUEST_TITLE.casefold():
        return current, True
    messages = _request_messages(token, uid, str(current["id"]))
    prior = any(
        str(m.get("sender") or "") == "client"
        and SCORECARD_MESSAGE_MARKER in str(m.get("body") or "")
        for m in messages
    )
    return current, prior


def submit_scorecard_access(
    token: str, uid: str, challenge: str, outcome: str, timing: str
) -> str:
    """Submit once into the real Advisory inbox; never grant entitlement here."""
    challenge = str(challenge or "").strip()
    outcome = str(outcome or "").strip()
    if len(challenge) < 25 or len(challenge) > 1400:
        raise ValueError("Describe the AI portfolio decision in 25–1,400 characters.")
    if len(outcome) < 20 or len(outcome) > 800:
        raise ValueError("Describe the decision outcome in 20–800 characters.")
    if timing not in ("This month", "1–3 months", "Exploratory"):
        raise ValueError("Choose a decision timeframe.")
    current, existing = _find_request_context(token, uid)
    if existing:
        return "already_requested"
    if current is not None:
        # Existing Advisory request — the message-stamp trigger updates
        # last_client_at so the owner sees a new actionable reply.
        note = (
            SCORECARD_MESSAGE_MARKER + "\n\n"
            + "Portfolio decision: " + challenge + "\n"
            + "Desired outcome: " + outcome + "\n"
            + "Timeframe: " + timing + "\n\n"
            + "Please consider individual pro-bono Scorecard access "
              "within this Advisory engagement."
        )
        _reply(token, uid, str(current["id"]), note)
        return "added_to_engagement"
    _create_request(token, uid, {
        "title": SCORECARD_REQUEST_TITLE,
        "desired_outcome": outcome,
        "business_context": "AI portfolio decision: " + challenge,
        "decision_timing": timing,
        "contact_preference": "Email",
    })
    return "new_request"


def render_scorecard_access_request(token: str, uid: str) -> None:
    """Render the Request Access action when a verified member lacks entitlement."""
    try:
        current, already_requested = _find_request_context(token, uid)
    except (RuntimeError, TimeoutError, ValueError, KeyError):
        st.error("Your Advisory request status could not be checked. Please retry.")
        return

    if already_requested:
        st.info(
            "Scorecard access requested — under individual review. "
            "Approval is not automatic."
        )
        if st.button("Follow this request in conversations",
                     key="scorecard_pending_conversation"):
            from page_advisory_member_experience import navigate
            navigate("messages")
        return

    if st.button(
        "Request Access", type="primary",
        key="scorecard_request_access_button",
    ):
        st.session_state[SCORECARD_OPEN_FORM_KEY] = True

    if not st.session_state.get(SCORECARD_OPEN_FORM_KEY):
        st.caption(
            "Available at no charge to selected pro-bono Advisory clients. "
            "Submitting a request does not activate the workspace."
        )
        return

    st.markdown("#### Request individual access")
    st.caption(
        "A short description is enough. Do not submit confidential company "
        "data or personal records. Your request will appear in the existing "
        "Advisory conversation for individual review."
    )
    with st.form("scorecard_request_access_form"):
        challenge = st.text_area(
            "Which AI portfolio decision do you need to make? *",
            max_chars=1400, height=110,
            placeholder="For example: deciding which initiatives to fund, pause "
                        "or stop when resources are constrained.",
        )
        outcome = st.text_area(
            "What would a useful outcome look like? *",
            max_chars=800, height=92,
            placeholder="For example: an evidence-based prioritization to review "
                        "with accountable executives.",
        )
        timing = st.selectbox(
            "Decision timeframe",
            ("This month", "1–3 months", "Exploratory"),
        )
        submitted = st.form_submit_button("Submit access request", type="primary")
    if submitted:
        try:
            status = submit_scorecard_access(token, uid, challenge, outcome, timing)
            st.session_state[SCORECARD_OPEN_FORM_KEY] = False
            if status == "already_requested":
                st.info("Your Scorecard access request is already under review.")
            else:
                st.success(
                    "Scorecard access request submitted for individual review. "
                    "No access has been granted yet."
                )
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except (RuntimeError, TimeoutError, KeyError):
            st.error(
                "The request could not be confirmed. Review your Advisory "
                "conversation before submitting again."
            )
