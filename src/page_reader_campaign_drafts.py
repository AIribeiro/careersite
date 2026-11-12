"""Private editorial campaign drafts. No automatic or manual send endpoint.

A saved draft records subject, plain-text content and a reader tag segment.
Recipients are resolved from current affirmative consent at export time; no
email addresses are persisted into drafts.
"""
from __future__ import annotations

from urllib.parse import urlencode
import streamlit as st

from site_cms import _request_json, _rest_url, OWNER_EMAIL
from site_analytics import ANALYTICS_URL


def _verified_owner(token: str) -> str:
    identity = _request_json(
        "GET", ANALYTICS_URL.rstrip("/") + "/auth/v1/user",
        token=token, timeout=12,
    )
    if not isinstance(identity, dict) or (
        str(identity.get("email") or "").strip().lower() != OWNER_EMAIL
    ) or not identity.get("id"):
        raise PermissionError("Verified owner access required.")
    return str(identity["id"])


def _fetch_drafts(token: str) -> list[dict]:
    query = urlencode({
        "select": "id,subject,body,segment_tag,status,created_at,updated_at",
        "order": "updated_at.desc", "limit": 200,
    })
    result = _request_json(
        "GET", _rest_url("portfolio_reader_mail_drafts?" + query),
        token=token, timeout=15,
    )
    if not isinstance(result, list):
        raise RuntimeError("Campaign drafts are temporarily unavailable.")
    return [r for r in result if isinstance(r, dict)]


def render_reader_campaign_drafts(token: str, eligible: list[dict],
                                  controls: dict[str, dict]) -> None:
    """Owner-only draft management; never schedules or sends a campaign."""
    try:
        owner_id = _verified_owner(token)
        drafts = _fetch_drafts(token)
    except (PermissionError, RuntimeError, ValueError, TimeoutError):
        st.error("Private editorial drafts could not be loaded.")
        return

    st.subheader("Editorial campaign drafts")
    st.caption(
        "Prepare email copy and a segment for future reviewed campaigns. "
        "Drafts contain no recipient addresses and cannot send messages."
    )
    choices = {str(d["id"]): d for d in drafts if d.get("id")}
    choice = st.selectbox(
        "Draft", ["new"] + list(choices),
        format_func=lambda value: (
            "Create a new draft" if value == "new" else
            str(choices[value].get("subject") or "Untitled") + " · "
            + str(choices[value].get("status") or "draft")
        ), key="reader_campaign_draft_choice",
    )
    draft = choices.get(choice, {})
    all_tags = sorted({
        str(tag) for row in eligible
        for tag in (controls.get(str(row.get("user_id")), {}).get("tags") or [])
    })
    current_tag = str(draft.get("segment_tag") or "")
    tag_options = [""] + all_tags
    if current_tag and current_tag not in tag_options:
        tag_options.append(current_tag)
    with st.form("reader_campaign_form_" + choice):
        subject = st.text_input(
            "Email subject", value=str(draft.get("subject") or ""),
            max_chars=180,
        )
        tag = st.selectbox(
            "Current recipient segment", tag_options,
            index=tag_options.index(current_tag),
            format_func=lambda v: "All consent-qualified readers" if not v else v,
        )
        body = st.text_area(
            "Email body (plain text)", value=str(draft.get("body") or ""),
            max_chars=20000, height=240,
        )
        status = st.selectbox(
            "Status", ["draft", "archived"],
            index=1 if draft.get("status") == "archived" else 0,
        )
        save = st.form_submit_button("Save draft")
    if save:
        if not subject.strip():
            st.error("Provide an email subject.")
        else:
            payload = {
                "subject": subject.strip(), "body": body,
                "segment_tag": tag, "status": status,
                "updated_by": owner_id,
            }
            try:
                if choice == "new":
                    payload["created_by"] = owner_id
                    _request_json(
                        "POST", _rest_url("portfolio_reader_mail_drafts"),
                        token=token, payload=payload, timeout=15,
                    )
                else:
                    _request_json(
                        "PATCH", _rest_url(
                            "portfolio_reader_mail_drafts?id=eq." + choice
                        ), token=token, payload=payload, timeout=15,
                    )
                st.success("Draft saved. No email was sent.")
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Could not save the draft.")

    current = [
        r for r in eligible if not tag or tag in (
            controls.get(str(r.get("user_id")), {}).get("tags") or []
        )
    ]
    st.caption(
        f"{len(current):,} currently eligible recipients in the selected segment. "
        "This count is recalculated from live consent and suppression, "
        "not stored as a permanent campaign recipient list."
    )
    if subject or body:
        with st.expander("Preview draft", expanded=False):
            st.markdown("**Subject:** " + subject.strip())
            st.text(body)
    st.info(
        "Email sending is deliberately disabled. Before enabling it, verify "
        "the sender domain and configure unsubscribe links, bounce/complaint "
        "handling, rate limits and a reviewed send-confirmation workflow."
    )
