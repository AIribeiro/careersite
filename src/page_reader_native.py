"""Native Streamlit reader membership.

Community Cloud can serve the Starlette GET pages but currently returns 500 on
custom HTML POSTs (even with a zero-data probe). This version performs form
submission and verification through Streamlit's supported widget channel. All
Supabase requests are issued from Python with the public/publishable API key and
the verified user's access token; no service-role key is needed.

For email links set Confirm signup + Magic Link templates to point to:
{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=email
The configured OTP redirect_to is always https://<app>.streamlit.app/?page=readers.
Optionally include {{ .Token }} in each email for manual code verification.
"""
from __future__ import annotations

import logging
import os
import re
import time
from html import escape as html_escape
from urllib.parse import urlencode, urlsplit

import streamlit as st

from reader_membership import (
    CONSENT_VERSION,
    EMAIL,
    _clean_slug,
    _log_consent,
    _pdf_for_article,
    _refresh,
    _register_profile,
    _utc_now,
    _verified_user,
    has_briefing_pdf,
)
from site_assets import EMAIL as PORTFOLIO_CONTACT_EMAIL
from site_analytics import ANALYTICS_URL
from site_reader_shell import reader_footer, reader_header
from site_cms import _request_json, _rest_url, fetch_published_articles
from thinking_articles import BASE_URL

LOG = logging.getLogger("careersite.reader")

def _host_origin() -> str:
    """Explicit, allowlisted HTTPS origin; no request-Host-based redirects."""
    configured = os.environ.get("PORTFOLIO_READER_CALLBACK_ORIGIN", "").strip()
    if not configured:
        try:
            configured = str(st.secrets.get("PORTFOLIO_READER_CALLBACK_ORIGIN", "")).strip()
        except (FileNotFoundError, KeyError):
            pass
    if not configured:
        configured = BASE_URL
    parts = urlsplit(configured)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or not re.fullmatch(r"[a-z0-9-]+\.streamlit\.app", parts.hostname)
        or parts.username or parts.password or parts.port
        or parts.path not in ("", "/")
        or parts.query or parts.fragment
    ):
        raise ValueError("Invalid configured reader callback origin.")
    return "https://" + parts.hostname

def _verify(payload: dict) -> dict:
    session = _request_json(
        "POST", ANALYTICS_URL.rstrip("/") + "/auth/v1/verify",
        payload=payload, timeout=12,
    )
    if not isinstance(session, dict) or not session.get("access_token") or not session.get("refresh_token"):
        raise RuntimeError("Verification did not establish a reader session.")
    user = _verified_user(session["access_token"])
    _register_profile(session, user)
    st.session_state["reader_native_session"] = session
    st.session_state["reader_native_user"] = user
    st.session_state.pop("reader_native_sent_email", None)
    return user

def _session() -> tuple[dict | None, dict | None]:
    session = st.session_state.get("reader_native_session")
    if not isinstance(session, dict):
        return None, None
    try:
        expiration = int(session.get("expires_at") or 0)
        if expiration <= time.time() + 90:
            session = _refresh(str(session.get("refresh_token") or ""))
            st.session_state["reader_native_session"] = session
        user = _verified_user(str(session.get("access_token") or ""))
        return session, user
    except (RuntimeError, ValueError, TimeoutError, KeyError) as exc:
        LOG.warning("Reader session refresh failed: %s", type(exc).__name__)
        st.session_state.pop("reader_native_session", None)
        st.session_state.pop("reader_native_user", None)
        return None, None

def _request_email(first_name: str, email: str, subscribe: bool, returning: bool) -> None:
    target = _host_origin() + "/?page=readers"
    url = ANALYTICS_URL.rstrip("/") + "/auth/v1/otp?" + urlencode({"redirect_to": target})
    data = {} if returning else {
        "reader_first_name": first_name,
        "reader_editorial_opt_in": bool(subscribe),
        "reader_notice_version": CONSENT_VERSION,
    }
    _request_json("POST", url, payload={
        "email": email, "create_user": not returning, "data": data,
    }, timeout=12)
    st.session_state["reader_native_sent_email"] = email

def _consume_query_verification() -> None:
    token = st.query_params.get("token_hash", "")
    if isinstance(token, list):
        token = token[0] if token else ""
    if not token:
        return
    auth_type = st.query_params.get("type", "email")
    # Remove the one-time secret before rendering content or invoking analytics.
    st.query_params.pop("token_hash", None)
    st.query_params.pop("type", None)
    if not isinstance(token, str) or len(token) > 512 or not re.fullmatch(r"[A-Za-z0-9._~-]{20,512}", token):
        st.session_state["reader_native_flash"] = ("error", "Invalid verification link. Request a new email.")
        return
    if auth_type != "email":
        st.session_state["reader_native_flash"] = ("error", "Unsupported verification link. Request a new email.")
        return
    try:
        _verify({"token_hash": token, "type": "email"})
        st.session_state["reader_native_flash"] = ("success", "Email verified. Welcome to your reader library.")
    except (RuntimeError, ValueError, TimeoutError):
        st.session_state["reader_native_flash"] = ("error", "The verification link has expired or could not be confirmed. Request a new email.")

def _login() -> None:
    st.markdown("### Complimentary access to executive resources")
    st.write(
        "Read the briefings online without an account. Register once to access "
        "the downloadable A4 infographic PDFs. The newsletter is optional."
    )
    returning = st.radio(
        "Reader status", ["I'm new here", "I already have an account"],
        horizontal=True, label_visibility="visible", key="reader_native_mode",
    ) == "I already have an account"
    with st.form("reader_native_login_form"):
        first = st.text_input("First name", max_chars=80, disabled=returning)
        email = st.text_input("Email address", max_chars=254, placeholder="you@example.com")
        subscribe = st.checkbox(
            "Email me new Executive AI Briefings and occasional AI leadership resources.",
            value=False, disabled=returning,
        )
        sent = st.form_submit_button("Send my secure access email", type="primary")
    if sent:
        first = str(first or "").strip()
        email = str(email or "").strip().lower()
        if (not returning and not first) or len(first) > 80 or not EMAIL.fullmatch(email):
            st.error("Enter your first name and a valid email address.")
        else:
            try:
                _request_email(first, email, bool(subscribe), returning)
                st.success("Check your inbox for a verification email.")
            except (RuntimeError, ValueError, TimeoutError):
                # Avoid disclosing whether an email address is already registered.
                st.error("We couldn't send the verification email. Check the email delivery settings and try again.")
    if st.session_state.get("reader_native_sent_email"):
        st.info("Open the verification link in your email, or enter its one-time code below.")
        with st.form("reader_native_code_form"):
            code = st.text_input("Email verification code", max_chars=10, placeholder="6-digit code")
            verified = st.form_submit_button("Verify code")
        if verified:
            code = str(code or "").strip()
            if not re.fullmatch(r"\d{6,8}", code):
                st.error("Enter the numeric code shown in the email.")
            else:
                try:
                    _verify({
                        "email": st.session_state["reader_native_sent_email"],
                        "token": code,
                        "type": "email",
                    })
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("The code was invalid or expired. Request a new email.")
    st.caption(
        "We use your email to verify reader access and track requested PDFs. "
        "Editorial updates are sent only if you choose to subscribe."
    )

def _record_download(token: str, user_id: str, slug: str) -> None:
    try:
        _request_json("POST", _rest_url("portfolio_reader_downloads"),
                      token=token,
                      payload={"user_id": user_id,
                               "article_slug": slug,
                               "source": "pdf_download"})
    except (RuntimeError, ValueError, TimeoutError):
        LOG.warning("Unable to record a native reader PDF download.")

def _render_preferences(session: dict, profile: dict, user: dict) -> None:
    with st.expander("Reader preferences", expanded=False):
        with st.form("reader_native_preferences"):
            first = st.text_input("First name", value=str(profile.get("first_name") or ""), max_chars=80)
            subscribed = st.checkbox("Receive editorial emails", value=bool(profile.get("newsletter_opt_in")))
            saved = st.form_submit_button("Save preferences")
        if saved:
            first = first.strip()
            if not first:
                st.error("First name is required.")
            else:
                before = bool(profile.get("newsletter_opt_in"))
                payload = {
                    "first_name": first,
                    "newsletter_opt_in": subscribed,
                    "newsletter_consent_at": (
                        _utc_now() if subscribed and not before
                        else profile.get("newsletter_consent_at") if subscribed else None
                    ),
                    "consent_notice_version": CONSENT_VERSION if subscribed else None,
                    "updated_at": _utc_now(),
                }
                try:
                    _request_json("PATCH", _rest_url(
                        "portfolio_reader_profiles?user_id=eq." + user["id"]),
                        token=session["access_token"], payload=payload)
                    if before != subscribed:
                        _log_consent(session["access_token"], user["id"], subscribed, "preferences")
                    st.success("Preferences saved.")
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("Your preferences could not be saved.")

def _library(session: dict, user: dict) -> None:
    try:
        profile = _register_profile(session, user)
    except (RuntimeError, ValueError, TimeoutError):
        st.error("Your verified account could not be loaded.")
        return
    name = str(profile.get("first_name") or "").strip()
    st.markdown("### Your executive library")
    st.write("Welcome" + (", " + name if name else "") + ". Your A4 executive infographic PDFs are available below.")
    st.caption("Authenticated as " + str(user.get("email") or ""))
    st.divider()

    try:
        articles = [
            item for item in fetch_published_articles()
            if str(item.kind).strip().casefold() == "executive briefing"
        ]
        articles.sort(key=lambda a: str(a.published_at or a.created_at or ""), reverse=True)
        available = [a for a in articles if _clean_slug(a.slug) and has_briefing_pdf(a.slug)]
    except (RuntimeError, ValueError, TimeoutError):
        st.error("The briefing catalog is temporarily unavailable.")
        available = []
    if not available:
        st.info("There are no downloadable briefings available yet.")
    else:
        options = {a.title: a.slug for a in available}
        requested = str(st.query_params.get("download", "") or "")
        initial = next((i for i, a in enumerate(available) if a.slug == requested), 0)
        selected = st.selectbox("Select an Executive AI Briefing", list(options.keys()), index=initial)
        slug = options[selected]
        # Return readers to the specific publication that brought them here.
        # Staging has a standalone dispatcher, so editorial links return to
        # the main portfolio; production stays in this same portfolio.
        relative = "/?page=briefing&article=" + slug
        briefing_url = (BASE_URL.rstrip("/") + relative) if _host_origin().startswith(
            "https://jairribeiro-reader-test."
        ) else relative
        st.html(
            '<div class="reader-publication-link">'
            '<a href="' + html_escape(briefing_url, quote=True)
            + '" target="_self">Read this briefing on the portfolio →</a>'
            '</div>'
        )
        if st.button("Prepare PDF", key="reader_native_prepare"):
            st.session_state["reader_native_prepared"] = slug
        if st.session_state.get("reader_native_prepared") == slug:
            try:
                with st.spinner("Preparing your infographic"):
                    pdf = _pdf_for_article(slug)
                if not pdf:
                    st.warning("A verified PDF is not available for this edition.")
                else:
                    st.download_button(
                        "Download A4 infographic",
                        data=pdf,
                        file_name=f"{slug}-executive-infographic.pdf",
                        mime="application/pdf",
                        type="primary",
                        key="reader_native_download_button",
                        on_click=_record_download,
                        args=(session["access_token"], str(user["id"]), slug),
                    )
            except (RuntimeError, ValueError, TimeoutError, OSError):
                st.error("The requested PDF could not be generated.")
    _render_preferences(session, profile, user)
    if st.button("Sign out", key="reader_native_logout"):
        try:
            _request_json("POST", ANALYTICS_URL.rstrip("/") + "/auth/v1/logout",
                          token=session["access_token"], payload={})
        except (RuntimeError, ValueError, TimeoutError):
            pass
        for key in ("reader_native_session", "reader_native_user", "reader_native_prepared"):
            st.session_state.pop(key, None)
        st.rerun()

def render_reader_native() -> None:
    """Verified reader flow embedded in the real portfolio navigation and footer."""
    # Consume the single-use token BEFORE rendering the shared navigation logo
    # or any external media. The token must never leak in a Referer header.
    _consume_query_verification()
    staging = _host_origin().startswith("https://jairribeiro-reader-test.")
    st.html(reader_header(staging=staging))
    with st.container(key="reader_flow"):
        notice = st.session_state.pop("reader_native_flash", None)
        if notice and notice[0] == "success":
            st.success(notice[1])
        elif notice and notice[0] == "error":
            st.error(notice[1])

        session, user = _session()
        if session and user:
            _library(session, user)
        else:
            _login()
        st.divider()
        st.caption(
            "Reader registration confirms email access; it does not subscribe "
            "you to editorial updates. Download activity and preferences are "
            "stored with your verified reader account."
        )
        with st.expander("Reader privacy & account information"):
            st.write(
                "Jair Ribeiro is responsible for the personal information "
                "collected through this independent portfolio. We store your "
                "name, verified email address, reader preferences and PDF "
                "download history to provide the requested library access "
                "and administer the free resources."
            )
            st.write(
                "We use Supabase for authentication and reader records, and "
                "a transactional email provider for one-time access messages. "
                "Editorial emails are optional and are sent only when you "
                "affirmatively choose to subscribe; you can withdraw that "
                "preference in the reader library."
            )
            st.write(
                "For access, correction, deletion or questions about your "
                "information, use the portfolio Contact page or email "
                + PORTFOLIO_CONTACT_EMAIL + "."
            )
    st.html(reader_footer())
