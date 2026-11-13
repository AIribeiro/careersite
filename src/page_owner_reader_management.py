"""Owner-only reader management, editorial mailing segmentation and audit.

Only an already verified portfolio CMS owner can invoke this workspace. Every
read and write carries the owner's personal JWT, subject to database RLS; the
owner-only action RPC performs authoritative identity checks and atomically
records mutations. No automatic email sends or user consent modifications.
"""
from __future__ import annotations

from collections import Counter
from csv import writer
from datetime import datetime
from io import StringIO
from urllib.parse import urlencode

import streamlit as st
import json

from site_analytics import ANALYTICS_URL
from site_cms import OWNER_EMAIL, _request_json, _rest_url

_BATCH = 500
_MAX_ROWS = 10000

_TABLES = {
    "portfolio_reader_profiles": ("*", "created_at.desc"),
    "portfolio_reader_downloads": ("user_id,article_slug,downloaded_at,source", "downloaded_at.desc"),
    "portfolio_reader_saved_briefings": ("user_id,article_slug,saved_at", "saved_at.desc"),
    "portfolio_reader_consent_events": (
        "user_id,subscribed,source,notice_version,recorded_at", "recorded_at.desc",
    ),
    "portfolio_reader_admin_controls": (
        "user_id,account_status,mailing_suppressed,tags,internal_notes,updated_at",
        "updated_at.desc",
    ),
    "portfolio_reader_admin_audit": (
        "user_id,actor_id,action,detail,created_at", "created_at.desc",
    ),
    "portfolio_advisory_profiles": ("user_id,account_status", "created_at.desc"),
    "portfolio_advisory_intents": ("user_id,email", "created_at.desc"),
}


def _verify_owner(session: dict) -> str:
    """Do not trust workspace routing or Streamlit session state as authority."""
    token = str(session.get("access_token") or "")
    if not token:
        raise PermissionError("Owner access is required.")
    identity = _request_json(
        "GET", ANALYTICS_URL.rstrip("/") + "/auth/v1/user",
        token=token, timeout=10,
    )
    if not isinstance(identity, dict) or (
        str(identity.get("email") or "").lower() != OWNER_EMAIL
    ):
        raise PermissionError("This workspace is restricted to the portfolio owner.")
    return token


def _read_table(token: str, table: str) -> list[dict]:
    if table not in _TABLES:
        raise ValueError("Unsupported owner data source.")
    columns, order = _TABLES[table]
    rows: list[dict] = []
    for offset in range(0, _MAX_ROWS, _BATCH):
        query = urlencode({
            "select": columns,
            "order": order,
            "limit": _BATCH,
            "offset": offset,
        })
        batch = _request_json(
            "GET", _rest_url(table + "?" + query),
            token=token, timeout=16,
        )
        if not isinstance(batch, list):
            raise RuntimeError("The reader administration source is unavailable.")
        rows.extend(record for record in batch if isinstance(record, dict))
        if len(batch) < _BATCH:
            return rows
    st.warning("A reader table reached the 10,000-row pagination safety limit. "
               "Export may be incomplete; extend server-side pagination before relying on it.")
    return rows


def _safe_csv(value: object) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    if text.lstrip().startswith(("=", "+", "-", "@", "\t")):
        return "'" + text
    return text


def _csv_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    buffer = StringIO()
    output = writer(buffer)
    output.writerow(headers)
    for row in rows:
        output.writerow([_safe_csv(value) for value in row])
    return buffer.getvalue().encode("utf-8-sig")


def _effective_mailing(
    profiles: list[dict], controls: dict[str, dict],
) -> list[dict]:
    """Only affirmative recorded opt-ins, not simply all registered users."""
    return [
        row for row in profiles
        if row.get("newsletter_opt_in") is True
        and row.get("newsletter_consent_at")
        and row.get("consent_notice_version")
        and not controls.get(str(row.get("user_id")), {}).get("mailing_suppressed", False)
        and controls.get(str(row.get("user_id")), {}).get("account_status", "active") == "active"
    ]


def _admin_action(token: str, user_id: str, action: str, *,
                  tags: list[str] | None = None, note: str | None = None) -> dict:
    """Database RPC checks current owner identity and writes one audit event."""
    if action not in {
        "suspend", "reinstate", "mailing_suppress", "mailing_restore",
        "note_update", "tag_update",
    }:
        raise ValueError("Unsupported reader action.")
    payload: dict[str, object] = {"p_user_id": user_id, "p_action": action}
    if action == "tag_update":
        payload["p_tags"] = tags if tags is not None else []
    if action == "note_update":
        payload["p_note"] = note if note is not None else ""
    result = _request_json(
        "POST", _rest_url("rpc/portfolio_reader_admin_action_v1"),
        token=token, payload=payload, timeout=16,
    )
    if not isinstance(result, dict) or str(result.get("user_id")) != str(user_id):
        raise RuntimeError("The administrative action was not confirmed.")
    return result


def _profile_snapshot(profile: dict, downloads: list[dict], saved: list[dict],
                      consents: list[dict], controls: dict) -> None:
    user_id = str(profile.get("user_id") or "")
    st.markdown("#### " + str(profile.get("first_name") or "Reader"))
    st.write("**Verified email:** " + str(profile.get("email") or ""))
    st.write("**Registered:** " + str(profile.get("created_at") or "")[:19])
    st.write("**Source:** " + str(profile.get("acquisition_source") or "Unknown"))
    st.markdown("**Reader-provided professional context**")
    st.write("**Full name:** " + " ".join(
        part for part in (
            str(profile.get("first_name") or "").strip(),
            str(profile.get("last_name") or "").strip()
        ) if part
    ))
    st.write("**Professional role:** " + str(profile.get("job_title") or "Not provided"))
    st.write("**Level:** " + str(profile.get("role_level") or "Not provided"))
    st.write("**Organization:** " + str(profile.get("organization") or "Not provided"))
    st.write("**Organization size:** " + str(profile.get("organization_size") or "Not provided"))
    st.write("**Sector:** " + str(profile.get("industry") or "Not provided"))
    st.write(
        "**Location:** " + ", ".join(
            part for part in (
                str(profile.get("city") or "").strip(),
                str(profile.get("country") or "").strip(),
            ) if part
        ) if (profile.get("city") or profile.get("country")) else
        "**Location:** Not provided"
    )
    st.write("**Preferred language:** " + str(profile.get("preferred_language") or "Not provided"))
    st.write("**LinkedIn:** " + str(profile.get("linkedin_url") or "Not provided"))
    st.write("**Professional website:** " + str(profile.get("professional_website") or "Not provided"))
    st.write("**Interests:** " + ", ".join(profile.get("interests") or []))
    st.write("**Reading goal:** " + str(profile.get("reading_goal") or "Not provided"))
    st.write("**AI adoption stage:** " + str(profile.get("ai_adoption_stage") or "Not provided"))
    if profile.get("primary_challenge"):
        st.write("**Leadership question shared by reader:**")
        st.text(str(profile.get("primary_challenge") or ""))
    st.caption(
        "Professional details are voluntarily supplied by readers. "
        "Passwords are managed only by Supabase Auth and are never visible here."
    )
    st.write(
        "**Editorial email consent:** "
        + ("Yes" if profile.get("newsletter_opt_in") is True else "No")
    )
    status = str(controls.get("account_status", "active"))
    st.write("**Account status:** " + status.title())
    st.write(
        "**Internal mailing suppression:** "
        + ("On" if controls.get("mailing_suppressed") else "Off")
    )
    reader_downloads = [
        row for row in downloads if str(row.get("user_id") or "") == user_id
    ]
    reader_saved = [
        row for row in saved if str(row.get("user_id") or "") == user_id
    ]
    reader_consents = [
        row for row in consents if str(row.get("user_id") or "") == user_id
    ]
    cols = st.columns(3)
    cols[0].metric("Recorded downloads", len(reader_downloads))
    cols[1].metric("Saved briefings", len(reader_saved))
    cols[2].metric("Consent events", len(reader_consents))
    with st.expander("Download activity", expanded=False):
        if reader_downloads:
            st.dataframe([
                {
                    "Briefing": str(row.get("article_slug") or ""),
                    "Downloaded": str(row.get("downloaded_at") or "")[:19],
                    "Source": str(row.get("source") or ""),
                } for row in reader_downloads
            ], hide_index=True, use_container_width=True)
        else:
            st.caption("No PDF download events.")
    with st.expander("Saved editions", expanded=False):
        if reader_saved:
            st.dataframe([
                {
                    "Briefing": str(row.get("article_slug") or ""),
                    "Saved": str(row.get("saved_at") or "")[:19],
                } for row in reader_saved
            ], hide_index=True, use_container_width=True)
        else:
            st.caption("No saved editions.")
    with st.expander("Consent audit history", expanded=False):
        if reader_consents:
            st.dataframe([
                {
                    "Subscribed": bool(row.get("subscribed")),
                    "When": str(row.get("recorded_at") or "")[:19],
                    "Source": str(row.get("source") or ""),
                    "Notice": str(row.get("notice_version") or ""),
                } for row in reader_consents
            ], hide_index=True, use_container_width=True)
        else:
            st.caption("No recorded consent events.")
    st.caption(
        "An administrator cannot subscribe a reader on their behalf. "
        "Editorial consent remains under the reader's control."
    )


def _reader_origin_tag(profile: dict) -> str:
    """Stable segmentation tag from immutable registration source."""
    source = str(profile.get("acquisition_source") or "").strip().casefold()
    if source == "articles":
        return "origin:articles"
    if source == "weekly_ai":
        return "origin:weekly_ai"
    if source == "advisory":
        return "origin:advisory"
    return "origin:briefings"


def _reader_management(
    token: str, profiles: list[dict], downloads: list[dict],
    saved: list[dict], consents: list[dict], controls: dict[str, dict],
    advisory_membership: dict[str, str] | None = None,
) -> None:
    advisory_membership = advisory_membership or {}
    st.subheader("Reader directory")
    st.caption(
        "Reader entitlement is independent of the Advisory relationship. "
        "An Advisory account includes Reader access, but registration here "
        "does not grant Advisory access."
    )
    search = st.text_input(
        "Find a registered reader",
        placeholder="Search name, email or tag",
        key="admin_readers_search",
    ).strip().casefold()
    status_filter = st.selectbox(
        "Audience filter",
        ["All readers", "Registered via Articles", "Registered via Briefings",
         "Registered via Weekly AI", "Editorial opt-in", "Not subscribed",
         "Mailing suppressed", "Suspended",
         "Advisory included", "Advisory pending"],
        key="admin_readers_filter",
    )

    def included(p: dict) -> bool:
        user_id = str(p.get("user_id") or "")
        control = controls.get(user_id, {})
        matched = search in " ".join([
            str(p.get("first_name") or ""), str(p.get("last_name") or ""),
            str(p.get("email") or ""), str(p.get("job_title") or ""),
            str(p.get("organization") or ""), str(p.get("industry") or ""),
            str(p.get("country") or ""), str(p.get("city") or ""),
            " ".join(p.get("interests") or []),
            " ".join(control.get("tags") or []),
            _reader_origin_tag(p),
        ]).casefold()
        if not matched:
            return False
        if status_filter == "Registered via Articles":
            return _reader_origin_tag(p) == "origin:articles"
        if status_filter == "Registered via Briefings":
            return _reader_origin_tag(p) == "origin:briefings"
        if status_filter == "Registered via Weekly AI":
            return _reader_origin_tag(p) == "origin:weekly_ai"
        if status_filter == "Advisory included":
            return advisory_membership.get(user_id) == "Advisory + Reader"
        if status_filter == "Advisory pending":
            return advisory_membership.get(user_id) == "Advisory pending"
        if status_filter == "Editorial opt-in":
            return p.get("newsletter_opt_in") is True
        if status_filter == "Not subscribed":
            return p.get("newsletter_opt_in") is not True
        if status_filter == "Mailing suppressed":
            return bool(control.get("mailing_suppressed"))
        if status_filter == "Suspended":
            return control.get("account_status") == "suspended"
        return True

    matching = [p for p in profiles if included(p)]
    st.caption(f"{len(matching):,} matching readers")
    st.dataframe([
        {
            "Name": " ".join(
                part for part in (
                    str(p.get("first_name") or ""),
                    str(p.get("last_name") or "")
                ) if part
            ),
            "Email": str(p.get("email") or ""),
            "Role": str(p.get("job_title") or ""),
            "Organization": str(p.get("organization") or ""),
            "Sector": str(p.get("industry") or ""),
            "Country": str(p.get("country") or ""),
            "Registered": str(p.get("created_at") or "")[:10],
            "Registration origin": _reader_origin_tag(p),
            "Membership": advisory_membership.get(str(p.get("user_id")), "Reader only"),
            "Editorial opt-in": bool(p.get("newsletter_opt_in")),
            "Status": str(controls.get(str(p.get("user_id")), {}).get("account_status", "active")),
            "Suppressed": bool(controls.get(str(p.get("user_id")), {}).get("mailing_suppressed")),
            "Tags": ", ".join(controls.get(str(p.get("user_id")), {}).get("tags") or []),
        } for p in matching[:500]
    ], hide_index=True, use_container_width=True)
    if len(matching) > 500:
        st.caption("First 500 matches displayed; narrow the filter to inspect a reader.")
    if not matching:
        return
    selection = st.selectbox(
        "Reader details",
        range(len(matching)),
        format_func=lambda i: (
            str(matching[i].get("first_name") or "Reader")
            + " — " + str(matching[i].get("email") or "")
        ),
        key="admin_selected_reader",
    )
    p = matching[selection]
    user_id = str(p["user_id"])
    control = controls.get(user_id, {})
    st.divider()
    _profile_snapshot(p, downloads, saved, consents, control)

    with st.expander("Export reader data · privacy requests", expanded=False):
        snapshot = {
            "profile": p,
            "administrative_controls": control,
            "downloads": [
                row for row in downloads if str(row.get("user_id")) == user_id
            ],
            "saved_briefings": [
                row for row in saved if str(row.get("user_id")) == user_id
            ],
            "consent_history": [
                row for row in consents if str(row.get("user_id")) == user_id
            ],
        }
        st.download_button(
            "Export this reader's records (JSON)",
            data=json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="reader-" + user_id + "-private-data.json",
            mime="application/json",
            key="admin_reader_personal_export_" + user_id,
        )
        st.caption(
            "Private export for owner review and access requests. "
            "Assess internal notes before disclosing records to a reader. "
            "Deletion is not performed here; use the authorized identity "
            "administration workflow and verify related records."
        )

    st.markdown("#### Internal reader management")
    with st.form("admin_reader_note_form_" + user_id):
        note = st.text_area(
            "Private administrative note",
            value=str(control.get("internal_notes") or ""),
            max_chars=10000, key="admin_reader_note_" + user_id,
            help="Owner-only CRM notes. Never include passwords or authentication tokens.",
        )
        note_save = st.form_submit_button("Save private note")
    if note_save:
        try:
            _admin_action(token, user_id, "note_update", note=note)
            st.success("Private note saved and audited.")
            st.rerun()
        except (RuntimeError, ValueError, TimeoutError):
            st.error("The note could not be saved.")

    with st.form("admin_reader_tags_form_" + user_id):
        tags = st.text_input(
            "Internal tags (comma-separated)",
            value=", ".join(control.get("tags") or []),
            max_chars=900, key="admin_reader_tags_" + user_id,
            help="Use tags to prepare editorial segments. Tags do not constitute consent.",
        )
        tag_save = st.form_submit_button("Save segment tags")
    if tag_save:
        cleaned = list(dict.fromkeys(tag.strip() for tag in tags.split(",") if tag.strip()))
        try:
            _admin_action(token, user_id, "tag_update", tags=cleaned)
            st.success("Segmentation tags saved and audited.")
            st.rerun()
        except (RuntimeError, ValueError, TimeoutError):
            st.error("Tags could not be saved. Use up to 20 short alphanumeric tags.")

    with st.expander("Mailing suppression and account access", expanded=False):
        st.caption(
            "Mailing suppression excludes an address from the internal export, "
            "without changing its historical consent. Suspending an account "
            "blocks the verified-reader access check; it does not delete data."
        )
        confirm = st.text_input(
            "Type the reader's email to confirm an access change",
            value="", key="admin_reader_action_confirmation_" + user_id,
            placeholder=str(p.get("email") or ""),
        )
        confirmed = confirm.strip().casefold() == str(p.get("email") or "").strip().casefold()
        a, b = st.columns(2)
        with a:
            suppressed = bool(control.get("mailing_suppressed"))
            label = "Restore to eligible mailing list" if suppressed else "Suppress from mailing list"
            if st.button(label, disabled=not confirmed,
                         key="admin_reader_mailing_action_" + user_id):
                action = "mailing_restore" if suppressed else "mailing_suppress"
                try:
                    _admin_action(token, user_id, action)
                    st.success("Mailing status updated and audited.")
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("Mailing status could not be changed.")
        with b:
            suspended = control.get("account_status") == "suspended"
            label = "Reinstate reader access" if suspended else "Suspend reader access"
            if st.button(label, disabled=not confirmed,
                         key="admin_reader_account_action_" + user_id):
                action = "reinstate" if suspended else "suspend"
                try:
                    _admin_action(token, user_id, action)
                    st.success("Account access updated and audited.")
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("Account status could not be changed.")
        st.caption(
            "Permanent identity deletion and GDPR data erasure are not "
            "performed by this interface. Use an authorized Supabase Auth "
            "administrative process after checking applicable retention rules."
        )


def _mailing_workspace(
    profiles: list[dict], controls: dict[str, dict],
) -> None:
    st.subheader("Internal editorial mailing list")
    eligible = _effective_mailing(profiles, controls)
    st.caption(
        "Only verified readers who affirmatively opted in, have a recorded "
        "consent timestamp, are not internally suppressed and have active access "
        "are eligible. This workspace never sends emails automatically."
    )
    st.metric("Eligible editorial subscribers", len(eligible))
    registered = len(profiles)
    st.caption(
        f"{registered:,} registered readers · "
        f"{sum(bool(p.get('newsletter_opt_in')) for p in profiles):,} declared opt-ins · "
        f"{len(eligible):,} currently eligible"
    )
    tags = sorted({
        tag for p in eligible
        for tag in (
            list(controls.get(str(p.get("user_id")), {}).get("tags") or [])
            + [_reader_origin_tag(p)]
        )
    })
    tag = st.selectbox(
        "Segment by internal tag", ["All eligible readers"] + tags,
        key="admin_mailing_segment",
    )
    segment = [
        p for p in eligible
        if tag == "All eligible readers" or tag in (
            list(controls.get(str(p.get("user_id")), {}).get("tags") or [])
            + [_reader_origin_tag(p)]
        )
    ]
    phrase = st.text_input(
        "Filter by name or email", key="admin_mailing_search"
    ).strip().casefold()
    if phrase:
        segment = [
            p for p in segment
            if phrase in (
                str(p.get("first_name") or "") + " " + str(p.get("email") or "")
            ).casefold()
        ]
    st.caption(f"{len(segment)} selected, consented recipients")
    table = [{
        "Name": p.get("first_name"),
        "Email": p.get("email"),
        "Consent date": str(p.get("newsletter_consent_at") or "")[:10],
        "Tags": ", ".join(
            list(controls.get(str(p.get("user_id")), {}).get("tags") or [])
            + [_reader_origin_tag(p)]
        ),
    } for p in segment]
    st.dataframe(table[:500], hide_index=True, use_container_width=True)
    csv = _csv_bytes(
        ["First name", "Email", "Consent timestamp", "Notice version", "Tags"],
        [[p.get("first_name"), p.get("email"), p.get("newsletter_consent_at"),
          p.get("consent_notice_version"),
          ", ".join(
              list(controls.get(str(p.get("user_id")), {}).get("tags") or [])
              + [_reader_origin_tag(p)]
          )]
         for p in segment],
    )
    st.download_button(
        "Export consented mailing list (CSV)",
        data=csv,
        file_name="jairribeiro-consented-readers.csv",
        mime="text/csv",
        key="admin_mailing_export",
        disabled=not segment,
    )
    st.info(
        "For a campaign, use the consented export with a mailing provider that "
        "supports unsubscribes, complaint handling and suppression syncing. "
        "A registration alone never authorizes marketing email."
    )


def render_owner_reader_management(session: dict) -> None:
    """Only entry point; all private reads occur after live owner verification."""
    try:
        token = _verify_owner(session)
    except (PermissionError, RuntimeError, TimeoutError, ValueError):
        st.error("The reader back office is restricted to the signed-in portfolio owner.")
        return

    st.title("Reader Management")
    st.caption(
        "Owner-only audience operations · Executive AI Briefings membership, "
        "consented mailing lists and reader activity."
    )
    st.link_button(
        "Open Premium Reader library ↗",
        "https://jairribeiro.com/?page=readers",
    )
    if st.button("Refresh reader data", key="admin_refresh_reader_records"):
        st.rerun()

    try:
        profiles = _read_table(token, "portfolio_reader_profiles")
        downloads = _read_table(token, "portfolio_reader_downloads")
        saved = _read_table(token, "portfolio_reader_saved_briefings")
        consents = _read_table(token, "portfolio_reader_consent_events")
        flags = _read_table(token, "portfolio_reader_admin_controls")
        audit = _read_table(token, "portfolio_reader_admin_audit")
        advisory = _read_table(token, "portfolio_advisory_profiles")
        pending_advisory = _read_table(token, "portfolio_advisory_intents")
    except (RuntimeError, ValueError, TimeoutError, PermissionError):
        st.error("Reader management data is temporarily unavailable.")
        return

    controls = {str(row["user_id"]): row for row in flags}
    advisory_membership = {
        str(p.get("user_id")): "Advisory pending"
        for p in pending_advisory if p.get("user_id")
    }
    advisory_membership.update({
        str(p.get("user_id")): "Advisory + Reader"
        for p in advisory if p.get("user_id") and p.get("account_status") == "active"
    })
    eligible = _effective_mailing(profiles, controls)
    kpis = st.columns(4)
    kpis[0].metric("Registered readers", len(profiles))
    kpis[1].metric("Consented recipients", len(eligible))
    kpis[2].metric("PDF downloads", len(downloads))
    kpis[3].metric(
        "Suspended accounts",
        sum(row.get("account_status") == "suspended" for row in flags),
    )
    directory, mailing, drafts, changes = st.tabs([
        "Registered readers", "Mailing list", "Campaign drafts", "Admin activity",
    ])
    with directory:
        _reader_management(token, profiles, downloads, saved, consents, controls,
                           advisory_membership)
    with mailing:
        _mailing_workspace(profiles, controls)
    with drafts:
        from page_reader_campaign_drafts import render_reader_campaign_drafts
        render_reader_campaign_drafts(token, eligible, controls)
    with changes:
        st.subheader("Owner action audit")
        st.caption(
            "Administrative access changes, mailing suppression and notes "
            "are recorded with an owner identity and timestamp."
        )
        emails = {
            str(p.get("user_id")): str(p.get("email") or "")
            for p in profiles
        }
        if audit:
            st.dataframe([
                {
                    "When": str(row.get("created_at") or "")[:19],
                    "Reader": emails.get(str(row.get("user_id")), "Removed account"),
                    "Action": str(row.get("action") or ""),
                    "Detail": str(row.get("detail") or ""),
                } for row in audit[:500]
            ], hide_index=True, use_container_width=True)
        else:
            st.caption("No recorded administrative changes.")
