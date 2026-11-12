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

def _accept_reader_session(session: dict) -> dict:
    """Validate email and account status before accepting an Auth session."""
    if not isinstance(session, dict) or not session.get("access_token") or not session.get("refresh_token"):
        raise RuntimeError("Authentication did not establish a reader session.")
    token = str(session["access_token"])
    user = _verified_user(token)
    status = _request_json(
        "POST", _rest_url("rpc/portfolio_reader_member_status_v1"),
        token=token, payload={}, timeout=10,
    )
    if status != "active":
        raise ValueError("Reader account access is unavailable.")
    _register_profile(session, user)
    st.session_state["reader_native_session"] = session
    st.session_state["reader_native_user"] = user
    st.session_state.pop("reader_native_sent_email", None)
    return user


def _verify(payload: dict) -> dict:
    session = _request_json(
        "POST", ANALYTICS_URL.rstrip("/") + "/auth/v1/verify",
        payload=payload, timeout=12,
    )
    return _accept_reader_session(session)


def _password_signin(email: str, password: str) -> dict:
    """Use Supabase Auth, never a local password table or credential cookie."""
    if not EMAIL.fullmatch(str(email or "").strip().lower()) or not password:
        raise ValueError("Valid email and password required.")
    session = _request_json(
        "POST", ANALYTICS_URL.rstrip("/") + "/auth/v1/token?grant_type=password",
        payload={"email": email.strip().lower(), "password": password},
        timeout=12,
    )
    return _accept_reader_session(session)


def _set_reader_password(session: dict, new_password: str) -> None:
    """Supabase Auth owns the secret; never persist it in reader profiles."""
    if len(new_password) < 12 or len(new_password) > 128:
        raise ValueError("Choose a password between 12 and 128 characters.")
    updated = _request_json(
        "PUT", ANALYTICS_URL.rstrip("/") + "/auth/v1/user",
        token=str(session["access_token"]),
        payload={"password": new_password}, timeout=12,
    )
    if not isinstance(updated, dict) or not updated.get("id"):
        raise RuntimeError("The password change was not confirmed.")


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
        # Administrative access suspensions are enforced server-side on every
        # verified reader check. The RPC exposes only the caller's own status,
        # not internal owner notes, tags or mailing suppression.
        status = _request_json(
            "POST", _rest_url("rpc/portfolio_reader_member_status_v1"),
            token=str(session["access_token"]), payload={}, timeout=10,
        )
        if status != "active":
            st.session_state["reader_native_flash"] = (
                "error",
                "This reader account cannot access complete briefings. "
                "Please contact the portfolio owner.",
            )
            st.session_state.pop("reader_native_session", None)
            st.session_state.pop("reader_native_user", None)
            return None, None
        return session, user
    except (RuntimeError, ValueError, TimeoutError, KeyError) as exc:
        LOG.warning("Reader session refresh failed: %s", type(exc).__name__)
        st.session_state.pop("reader_native_session", None)
        st.session_state.pop("reader_native_user", None)
        return None, None

def _briefing_access_request() -> tuple[str, str]:
    """Only accept a validated slug and first-party access/PDF intent."""
    page = st.query_params.get("page", "")
    article = st.query_params.get("article", "")
    pdf_flag = st.query_params.get("pdf", "")
    access_flag = st.query_params.get("access", "")
    if not all(isinstance(x, str) for x in (page, article, pdf_flag, access_flag)):
        return "", ""
    if page != "briefing" or (pdf_flag != "1" and access_flag != "1"):
        return "", ""
    slug = _clean_slug(article)
    return (slug, "pdf" if pdf_flag == "1" else "access") if slug else ("", "")


def _request_email(first_name: str, email: str, subscribe: bool, returning: bool) -> None:
    target = _host_origin() + "/?page=readers"
    requested, purpose = _briefing_access_request()
    page = "briefing" if requested else ""
    if not requested and st.query_params.get("page") == "thinking" and st.query_params.get("access") == "1":
        requested = _clean_slug(st.query_params.get("article", ""))
        page, purpose = "thinking", "access"
    if requested:
        # Preserve the specific publication after email verification even
        # if the reader opens the secure link in a fresh browser tab.
        # Add same-host briefing callback patterns to the Supabase allowlist.
        target = _host_origin() + "/?" + urlencode({
            "page": page, "article": requested,
            "pdf" if purpose == "pdf" else "access": "1",
        })
    url = ANALYTICS_URL.rstrip("/") + "/auth/v1/otp?" + urlencode({"redirect_to": target})
    data = {} if returning else {
        "reader_first_name": first_name,
        "reader_editorial_opt_in": bool(subscribe),
        "reader_notice_version": CONSENT_VERSION,
        "reader_acquisition_source": (
            "weekly_ai" if page == "thinking" and requested.startswith("weekly-ai-")
            else "articles" if page == "thinking" else "briefings"
        ),
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

def _login(requested_title: str = "", *, resource_kind: str = "briefing") -> None:
    if requested_title and resource_kind == "weekly_ai":
        st.markdown("### Continue with the complete Weekly AI edition")
        st.write(
            "Read **" + requested_title +
            "** in full, including the editorial perspective behind this week's "
            "enterprise AI developments. Audio is available when published. "
            "Premium Reader access is complimentary."
        )
    elif requested_title and resource_kind == "article":
        st.markdown("### Continue beyond the article preview")
        st.write(
            "Access the full perspective on **" + requested_title +
            "**, including the business trade-offs and practical questions "
            "behind the analysis. Premium Reader access is complimentary."
        )
    elif requested_title:
        st.markdown("### Explore the complete executive briefing")
        st.write(
            "Read **" + requested_title +
            "** beyond the public preview, including the leadership decisions "
            "and original infographic where available. "
            "Premium Reader access is complimentary."
        )
    else:
        st.html("""<div class="reader-join-heading">
        <span class="reader-join-eyebrow">YOUR READER ACCESS</span>
        <h2>Read beyond the summary.</h2>
        <p>One account opens complete Executive AI Briefings, Premium Articles
        and the latest Weekly AI edition. Save the perspectives relevant to
        your work and return to your infographic downloads in your own library.</p>
        </div>""")
        st.caption(
            "Complimentary membership · No payment details · "
            "Editorial updates only with your consent."
        )

    returning = st.radio(
        "Reader status", ["Create my reader access", "I already have an account"],
        index=1 if str(st.query_params.get("signin", "")) == "1" else 0,
        horizontal=True, label_visibility="collapsed", key="reader_native_mode",
    ) == "I already have an account"

    if returning:
        method = st.radio(
            "Sign-in method", ["Email and password", "Email verification code"],
            horizontal=True, key="reader_signin_method",
        )
        if method == "Email and password":
            with st.form("reader_password_signin_form", clear_on_submit=True):
                email = st.text_input(
                    "Email address", max_chars=254,
                    placeholder="you@example.com", key="reader_password_email",
                )
                password = st.text_input(
                    "Password", type="password", max_chars=128,
                    key="reader_password_secret",
                )
                sign_in = st.form_submit_button("Sign in to my library", type="primary")
            if sign_in:
                try:
                    _password_signin(str(email or "").strip(), str(password or ""))
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError, KeyError):
                    # Keep failures generic: do not reveal registered addresses.
                    st.error("Could not sign in. Check your credentials or use email verification.")
            st.caption(
                "No password yet, or forgotten it? Select Email verification code "
                "above. After signing in, set a password in My Profile."
            )
            st.caption("Reader support: info@jairribeiro.com")
            return

    with st.form("reader_native_login_form"):
        first = st.text_input("First name", max_chars=80, disabled=returning)
        email = st.text_input("Email address", max_chars=254, placeholder="you@example.com")
        subscribe = st.checkbox(
            "Send me new briefings, articles and Weekly AI perspectives by email (optional).",
            value=False, disabled=returning,
        )
        sent = st.form_submit_button(
            "Send my Premium Reader access link" if not returning else "Email me a sign-in link",
            type="primary",
        )
    st.caption("We will email a verification link. No newsletter subscription is required.")
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
                st.error("We couldn't send the verification email. Try again or contact reader support.")
    if st.session_state.get("reader_native_sent_email"):
        st.info("Open the verification link in your email, or enter its one-time code below.")
        with st.form("reader_native_code_form"):
            code = st.text_input("Email verification code", max_chars=10, placeholder="6-digit code")
            verified = st.form_submit_button("Verify code")
        if verified:
            code = str(code or "").strip()
            if not re.fullmatch(r"\d{6,10}", code):
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
        "Your verified email keeps the library and PDF history attached to your account. "
        "Editorial emails are separate and optional."
    )
    st.caption("Questions about access? info@jairribeiro.com.")


def _record_download(token: str, user_id: str, slug: str) -> None:
    try:
        _request_json("POST", _rest_url("portfolio_reader_downloads"),
                      token=token,
                      payload={"user_id": user_id,
                               "article_slug": slug,
                               "source": "pdf_download"})
    except (RuntimeError, ValueError, TimeoutError):
        LOG.warning("Unable to record a native reader PDF download.")

_READER_TOPICS = (
    "AI strategy", "AI governance", "Responsible AI", "AI adoption",
    "AI agents", "AI value and ROI", "Data governance",
    "Data and analytics leadership", "AI operating models",
    "Leadership and organizational change", "Process improvement",
    "EU AI regulation",
)
_READER_LEVELS = (
    "", "Individual contributor", "Manager", "Senior Manager", "Head of function",
    "Director", "VP / Executive", "C-suite", "Founder / Owner",
    "Consultant / Advisor", "Research / Academia", "Other",
)
_READER_SIZES = (
    "", "1–49", "50–249", "250–999", "1,000–4,999",
    "5,000–19,999", "20,000+", "Not applicable",
)
_READER_GOALS = (
    "", "Professional development", "Leading AI adoption",
    "Developing AI strategy or governance", "Evaluating enterprise AI",
    "Research / education", "Exploring business collaboration", "Other",
)
_READER_STAGES = (
    "", "Exploring", "Experimenting / pilots", "Scaling adoption",
    "Established enterprise capability", "Not applicable / unsure",
)


def _profile_option(options: tuple[str, ...], value: object) -> int:
    """Preserve a user's chosen option; missing older values map to blank."""
    return options.index(str(value or "")) if str(value or "") in options else 0


def _profile_url(raw: str, *, linkedin: bool = False) -> str:
    """Accept only https public professional links; never arbitrary schemes."""
    from urllib.parse import urlsplit
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise ValueError("Enter a valid HTTPS website.") from exc
    if (
        parts.scheme.lower() != "https" or not parts.hostname or
        parts.username or parts.password or any(ch.isspace() for ch in value)
    ):
        raise ValueError("Professional links must use HTTPS.")
    if linkedin and (parts.hostname.lower() not in {"linkedin.com", "www.linkedin.com"}):
        raise ValueError("Use your LinkedIn profile URL.")
    if len(value) > 350:
        raise ValueError("Professional links cannot exceed 350 characters.")
    return value


def _render_preferences(session: dict, profile: dict, user: dict) -> None:
    st.markdown("#### Your professional profile")
    st.caption(
        "All professional fields are optional except first name. They help us "
        "understand the audience and develop more relevant executive resources. "
        "Your information is not shown publicly and is not a mailing-list subscription."
    )
    with st.form("reader_native_preferences"):
        st.markdown("**About you**")
        a, b = st.columns(2)
        with a:
            first = st.text_input("First name", value=str(profile.get("first_name") or ""), max_chars=80)
        with b:
            last = st.text_input("Last name (optional)", value=str(profile.get("last_name") or ""), max_chars=80)
        a, b = st.columns(2)
        with a:
            job_title = st.text_input("Job title / professional role", value=str(profile.get("job_title") or ""), max_chars=160)
            role_level = st.selectbox(
                "Professional level", _READER_LEVELS,
                index=_profile_option(_READER_LEVELS, profile.get("role_level")),
            )
        with b:
            organization = st.text_input("Company / organization", value=str(profile.get("organization") or ""), max_chars=180)
            industry = st.text_input("Industry / sector", value=str(profile.get("industry") or ""), max_chars=100)
        size = st.selectbox(
            "Organization size (employees)", _READER_SIZES,
            index=_profile_option(_READER_SIZES, profile.get("organization_size")),
        )
        a, b = st.columns(2)
        with a:
            country = st.text_input("Country", value=str(profile.get("country") or ""), max_chars=100)
        with b:
            city = st.text_input("City / region", value=str(profile.get("city") or ""), max_chars=100)
        preferred_language = st.text_input(
            "Preferred reading language", value=str(profile.get("preferred_language") or ""),
            max_chars=70, placeholder="e.g. English",
        )
        a, b = st.columns(2)
        with a:
            linkedin = st.text_input(
                "LinkedIn profile URL", value=str(profile.get("linkedin_url") or ""),
                max_chars=350, placeholder="https://www.linkedin.com/in/...",
            )
        with b:
            website = st.text_input(
                "Professional website", value=str(profile.get("professional_website") or ""),
                max_chars=350, placeholder="https://...",
            )
        st.divider()
        st.markdown("**Your interests and current context**")
        old_topics = profile.get("interests") or []
        selected_interests = st.multiselect(
            "Executive AI topics you follow (up to 10)",
            _READER_TOPICS,
            default=[topic for topic in old_topics if topic in _READER_TOPICS][:10],
        )
        a, b = st.columns(2)
        with a:
            reading_goal = st.selectbox(
                "What brings you to these briefings?", _READER_GOALS,
                index=_profile_option(_READER_GOALS, profile.get("reading_goal")),
            )
        with b:
            ai_stage = st.selectbox(
                "AI adoption stage in your organization", _READER_STAGES,
                index=_profile_option(_READER_STAGES, profile.get("ai_adoption_stage")),
            )
        challenge = st.text_area(
            "Leadership question or AI challenge (optional)",
            value=str(profile.get("primary_challenge") or ""),
            max_chars=600, height=95,
            help="Share only professional context you are comfortable providing.",
        )
        st.divider()
        st.markdown("**Editorial communication**")
        subscribed = st.checkbox(
            "Receive editorial emails",
            value=bool(profile.get("newsletter_opt_in")),
            help="Optional. Changing your profile never subscribes you automatically.",
        )
        saved = st.form_submit_button("Save my profile", type="primary")
    if saved:
        first = first.strip()
        if not first:
            st.error("First name is required.")
            return
        try:
            linkedin_value = _profile_url(linkedin, linkedin=True)
            site_value = _profile_url(website)
            if len(selected_interests) > 10:
                raise ValueError("Select up to 10 interests.")
            before = bool(profile.get("newsletter_opt_in"))
            payload = {
                "first_name": first, "last_name": last.strip(),
                "job_title": job_title.strip(), "organization": organization.strip(),
                "industry": industry.strip(), "role_level": role_level,
                "organization_size": size, "country": country.strip(),
                "city": city.strip(), "preferred_language": preferred_language.strip(),
                "linkedin_url": linkedin_value, "professional_website": site_value,
                "interests": selected_interests, "reading_goal": reading_goal,
                "ai_adoption_stage": ai_stage, "primary_challenge": challenge.strip(),
                "newsletter_opt_in": bool(subscribed),
                "newsletter_consent_at": (
                    _utc_now() if subscribed and not before
                    else profile.get("newsletter_consent_at") if subscribed else None
                ),
                "consent_notice_version": CONSENT_VERSION if subscribed else None,
                "updated_at": _utc_now(),
            }
            _request_json(
                "PATCH", _rest_url("portfolio_reader_profiles?user_id=eq." + str(user["id"])),
                token=str(session["access_token"]), payload=payload,
            )
            if before != bool(subscribed):
                _log_consent(str(session["access_token"]), str(user["id"]), bool(subscribed), "preferences")
            st.success("Your profile has been updated.")
            st.rerun()
        except (RuntimeError, ValueError, TimeoutError):
            st.error("The profile couldn't be saved. Check your links and try again.")


def _render_password_settings(session: dict) -> None:
    with st.expander("Account security · Password", expanded=False):
        st.write(
            "Set a password after verifying your email once. On future visits "
            "you can sign in with your email and password without requesting an OTP."
        )
        with st.form("reader_set_password", clear_on_submit=True):
            password = st.text_input(
                "New password", type="password", max_chars=128,
                help="Use at least 12 characters. A long, unique passphrase is recommended.",
            )
            confirm = st.text_input("Confirm new password", type="password", max_chars=128)
            change = st.form_submit_button("Set or update password", type="primary")
        if change:
            if password != confirm:
                st.error("The passwords do not match.")
            else:
                try:
                    _set_reader_password(session, str(password))
                    st.success("Password saved. Use email and password next time you sign in.")
                except ValueError as exc:
                    st.error(str(exc))
                except (RuntimeError, TimeoutError, KeyError):
                    st.error(
                        "The password could not be changed. You may need recent email "
                        "verification. Sign in with an email code and try again."
                    )
        st.caption(
            "Forgot your password? Use the email verification option to access "
            "your account, then set a new password here. "
            "For help, email info@jairribeiro.com."
        )


def _reader_collection(
    session: dict, user: dict, table: str, *, order: str, limit: int = 200,
) -> list[dict]:
    """Read only this verified user's rows; RLS independently enforces scope."""
    if table not in {"portfolio_reader_downloads", "portfolio_reader_saved_briefings"}:
        raise ValueError("Unsupported reader collection.")
    from urllib.parse import quote
    user_id = str(user["id"])
    result = _request_json(
        "GET", _rest_url(
            table + "?select=*&user_id=eq." + quote(user_id, safe="")
            + "&order=" + order + "&limit=" + str(min(limit, 200))
        ),
        token=str(session["access_token"]),
    )
    if not isinstance(result, list):
        raise RuntimeError("Reader collection could not be loaded.")
    return [row for row in result if isinstance(row, dict)]


def _update_saved(session: dict, user: dict, slug: str, *, saved: bool) -> None:
    from urllib.parse import quote
    clean = _clean_slug(slug)
    if not clean:
        raise ValueError("Invalid briefing identifier.")
    target = "portfolio_reader_saved_briefings"
    token = str(session["access_token"])
    if saved:
        _request_json("POST", _rest_url(target), token=token,
                      payload={"user_id": str(user["id"]), "article_slug": clean})
    else:
        _request_json(
            "DELETE", _rest_url(
                target + "?user_id=eq." + quote(str(user["id"]), safe="")
                + "&article_slug=eq." + quote(clean, safe="")
            ), token=token,
        )


def _open_reader_briefing(slug: str) -> None:
    """Navigate inside the active Streamlit session; do not reload the tab."""
    st.query_params.from_dict({"page": "briefing", "article": _clean_slug(slug)})
    st.rerun()


def _reader_pdf_controls(
    session: dict, user: dict, slug: str, *, view: str,
) -> None:
    if not has_briefing_pdf(slug):
        st.caption("An A4 infographic PDF is not published for this edition.")
        return
    selected_key = "reader_native_prepared"
    if st.button("Prepare infographic PDF", key="reader_prepare_" + view):
        st.session_state[selected_key] = (view, slug)
    if st.session_state.get(selected_key) != (view, slug):
        return
    try:
        with st.spinner("Preparing your A4 infographic"):
            pdf = _pdf_for_article(slug)
        if pdf:
            st.download_button(
                "Download A4 infographic",
                data=pdf,
                file_name=f"{slug}-executive-infographic.pdf",
                mime="application/pdf",
                type="primary",
                key="reader_download_" + view,
                on_click=_record_download,
                args=(session["access_token"], str(user["id"]), slug),
            )
        else:
            st.warning("This infographic is temporarily unavailable.")
    except (RuntimeError, ValueError, TimeoutError, OSError):
        st.error("The infographic could not be prepared.")


def _reader_section_header(kicker: str, title: str, description: str) -> None:
    """Consistent editorial introduction for every private library section."""
    st.html(
        '<header class="reader-section-header">'
        '<span class="reader-section-kicker">' + html_escape(kicker) + '</span>'
        '<h3>' + html_escape(title) + '</h3>'
        '<p>' + html_escape(description) + '</p>'
        '</header>'
    )


def _reader_selected_edition(
    session: dict, user: dict, articles: list, saved_slugs: set[str],
    *, view: str,
) -> None:
    """Compact, easy-to-scan edition cards with primary reading actions."""
    if not articles:
        st.info(
            "Nothing to show here yet. Browse All briefings to discover a "
            "perspective worth returning to." if view == "saved"
            else "No briefings match your search. Try a broader topic."
        )
        return
    st.caption(f"{len(articles)} briefing" + ("" if len(articles) == 1 else "s") + " in this view")
    page_size = 5
    page_count = (len(articles) + page_size - 1) // page_size
    page = (
        st.selectbox(
            "Browse library pages", range(page_count),
            format_func=lambda i: f"Page {i + 1} of {page_count}",
            key="reader_catalog_page_" + view,
        ) if page_count > 1 else 0
    )
    offset = int(page) * page_size
    for article in articles[offset: offset + page_size]:
        slug = _clean_slug(str(article.slug))
        if not slug:
            continue
        pdf_available = has_briefing_pdf(slug)
        with st.container(border=True, key="reader_edition_" + view + "_" + slug):
            topic = str(article.category or "Executive AI").strip()
            st.caption("EXECUTIVE AI BRIEFING · " + topic)
            st.markdown("#### " + str(article.title))
            subtitle = str(article.subtitle or article.excerpt or "").strip()
            if subtitle:
                st.write(subtitle)
            st.caption(
                str(article.published_label) + "  ·  Full edition included"
                + ("  ·  A4 infographic available" if pdf_available else "")
            )
            left, right = st.columns([1.15, 1], gap="small")
            with left:
                if st.button(
                    "Read complete briefing", type="primary",
                    key="reader_open_" + view + "_" + slug,
                    use_container_width=True,
                ):
                    _open_reader_briefing(slug)
            with right:
                saved = slug in saved_slugs
                label = "Remove from saved" if saved else "Save to my library"
                if st.button(
                    label, key="reader_save_" + view + "_" + slug,
                    use_container_width=True,
                ):
                    try:
                        _update_saved(session, user, slug, saved=not saved)
                        st.rerun()
                    except (RuntimeError, ValueError, TimeoutError):
                        st.error("Your reading list couldn't be updated. Please try again.")
            if pdf_available:
                _reader_pdf_controls(session, user, slug, view=view + "_" + slug)


def _library(session: dict, user: dict) -> None:
    """Member hub: full catalog, saved editions, PDF history, profile."""
    try:
        profile = _register_profile(session, user)
    except (RuntimeError, ValueError, TimeoutError):
        st.error("Your verified account could not be loaded.")
        return

    first = str(profile.get("first_name") or "").strip()
    welcome = ("Welcome back, " + first + "." if first else "Welcome to your reader library.")
    st.html(
        '<section class="reader-member-welcome" aria-label="Premium Reader welcome">'
        '<span class="reader-member-eyebrow">YOUR PREMIUM READER SPACE</span>'
        '<h2>' + html_escape(welcome) + '</h2>'
        '<p>Independent perspectives on AI strategy, accountability and adoption, '
        'with complete editions, saved reading and original decision visuals '
        'within easy reach.</p></section>'
    )

    try:
        articles = [
            item for item in fetch_published_articles()
            if str(item.kind).strip().casefold() == "executive briefing"
            and _clean_slug(str(item.slug))
        ]
        articles.sort(key=lambda a: str(a.published_at or a.created_at or ""),
                      reverse=True)
    except (RuntimeError, ValueError, TimeoutError):
        st.error("The complete briefing catalog is temporarily unavailable.")
        articles = []

    collection_error = False
    try:
        saved = _reader_collection(
            session, user, "portfolio_reader_saved_briefings",
            order="saved_at.desc",
        )
        downloaded = _reader_collection(
            session, user, "portfolio_reader_downloads",
            order="downloaded_at.desc",
        )
    except (RuntimeError, ValueError, TimeoutError):
        collection_error = True
        saved, downloaded = [], []
    if collection_error:
        st.warning("Saved briefings or download history could not be loaded.")

    saved_slugs = {str(row.get("article_slug") or "") for row in saved}
    by_slug = {str(article.slug): article for article in articles}
    unique_downloads: dict[str, dict] = {}
    for row in downloaded:
        slug = str(row.get("article_slug") or "")
        if slug and slug not in unique_downloads:
            unique_downloads[slug] = row

    st.html(
        '<section class="reader-member-stats" aria-label="Your library at a glance">'
        '<div class="reader-member-stat"><strong class="reader-member-number">'
        + str(len(articles)) + '</strong><span class="reader-member-stat-label">'
        'Complete briefings</span></div>'
        '<div class="reader-member-stat"><strong class="reader-member-number">'
        + str(len(saved_slugs)) + '</strong><span class="reader-member-stat-label">'
        'Saved for later</span></div>'
        '<div class="reader-member-stat"><strong class="reader-member-number">'
        + str(len(unique_downloads)) + '</strong><span class="reader-member-stat-label">'
        'Infographics in your history</span></div></section>'
    )
    st.caption("Choose a collection below. Your membership stays active as you explore.")
    st.html(
        '<div class="reader-tab-hint"><strong>YOUR COLLECTIONS</strong>'
        '<span>Swipe to see all six sections →</span></div>'
    )

    all_tab, articles_tab, weekly_tab, saved_tab, pdf_tab, profile_tab = st.tabs([
        "All briefings", "Articles", "Weekly AI", "Saved", "My PDFs", "My profile",
    ])
    with weekly_tab:
        _reader_section_header(
            "WEEKLY AI · EXECUTIVE PERSPECTIVES",
            "What changed this week — and why it matters.",
            "A concise reading or listening perspective on developments worth "
            "examining in your own business. The latest edition is included "
            "with your reader membership.",
        )
        from thinking_weekly_brief import sorted_editions, edition_label
        from weekly_ai_reader_access import weekly_ai_is_premium
        try:
            weekly_issues = sorted_editions(list(fetch_published_articles()))
        except (RuntimeError, ValueError, TimeoutError):
            weekly_issues = []
            st.warning("Weekly AI is temporarily unavailable. Your other collections remain accessible.")
        if weekly_issues:
            weekly_search = st.text_input(
                "Find a Weekly AI edition",
                placeholder="Search a week, headline or topic",
                key="reader_weekly_search",
            ).strip().casefold()
            matching_weekly = [
                item for item in weekly_issues
                if weekly_search in (
                    str(item.title) + " " + str(item.subtitle or "") + " "
                    + str(item.excerpt or "") + " " + str(item.category or "")
                ).casefold()
            ]
            st.caption(f"{len(matching_weekly)} edition" + ("" if len(matching_weekly) == 1 else "s") + " in this view")
            page_size = 6
            pages = max(1, (len(matching_weekly) + page_size - 1) // page_size)
            current = (
                st.selectbox(
                    "Browse Weekly AI pages", range(pages),
                    format_func=lambda i: f"Page {i + 1} of {pages}",
                    key="reader_weekly_page",
                )
                if pages > 1 else 0
            )
            for item in matching_weekly[int(current) * page_size:(int(current) + 1) * page_size]:
                slug = _clean_slug(str(item.slug))
                if not slug:
                    continue
                with st.container(border=True, key="reader_edition_weekly_" + slug):
                    premium = weekly_ai_is_premium(item, published=weekly_issues)
                    st.caption(
                        edition_label(item) + " · " +
                        ("CURRENT PREMIUM EDITION" if premium else "OPEN ARCHIVE")
                    )
                    st.markdown("#### " + str(item.title))
                    st.write(str(item.excerpt or item.subtitle or ""))
                    if st.button(
                        "Read this Weekly AI edition", type="primary",
                        use_container_width=True, key="reader_weekly_open_" + slug,
                    ):
                        st.query_params.from_dict({"page": "thinking", "article": slug})
                        st.rerun()
            if not matching_weekly:
                st.info("No edition matches your search. Try a broader topic.")
        else:
            st.info("No Weekly AI editions are published yet.")

    with articles_tab:
        _reader_section_header(
            "ARTICLES · LEADERSHIP JUDGMENT",
            "Longer perspectives behind the decisions.",
            "Explore the evidence, assumptions and operating trade-offs behind "
            "enterprise AI. Your membership includes complete Premium Articles "
            "alongside the open editorial archive.",
        )
        from article_access import is_editorial_article, article_is_locked
        try:
            editorial = [
                item for item in fetch_published_articles()
                if is_editorial_article(item) and _clean_slug(str(item.slug))
            ]
        except (RuntimeError, ValueError, TimeoutError):
            editorial = []
            st.warning("The article collection is temporarily unavailable.")
        editorial.sort(key=lambda a: str(a.published_at or ""), reverse=True)
        if editorial:
            article_search = st.text_input(
                "Find an article",
                placeholder="Search a topic, decision or title",
                key="reader_articles_search",
            ).strip().casefold()
            matching_editorial = [
                item for item in editorial
                if article_search in (
                    str(item.title) + " " + str(item.subtitle or "") + " "
                    + str(item.excerpt or "") + " " + str(item.category or "")
                ).casefold()
            ]
            st.caption(f"{len(matching_editorial)} article" + ("" if len(matching_editorial) == 1 else "s") + " in this view")
            page_size = 6
            pages = max(1, (len(matching_editorial) + page_size - 1) // page_size)
            current = (
                st.selectbox(
                    "Browse article pages", range(pages),
                    format_func=lambda i: f"Page {i + 1} of {pages}",
                    key="reader_articles_page",
                )
                if pages > 1 else 0
            )
            for item in matching_editorial[int(current) * page_size:(int(current) + 1) * page_size]:
                slug = _clean_slug(str(item.slug))
                if not slug:
                    continue
                with st.container(border=True, key="reader_edition_article_" + slug):
                    premium = article_is_locked(item, published=editorial)
                    st.caption(
                        str(item.published_label) + " · "
                        + ("PREMIUM ARTICLE · FULL ACCESS" if premium else "OPEN ACCESS")
                    )
                    st.markdown("#### " + str(item.title))
                    st.write(str(item.subtitle or item.excerpt or ""))
                    if st.button(
                        "Read complete article", type="primary",
                        use_container_width=True, key="reader_article_open_" + slug,
                    ):
                        st.query_params.from_dict({"page": "thinking", "article": slug})
                        st.rerun()
            if not matching_editorial:
                st.info("No articles match your search. Try another phrase.")
        else:
            st.info("No articles are published yet.")

    with all_tab:
        _reader_section_header(
            "THE COMPLETE BRIEFING LIBRARY",
            "A reference library for consequential AI decisions.",
            "Work through the questions behind AI investments, ownership, "
            "governance, adoption and business value. Every published briefing "
            "is available here in full.",
        )
        search = st.text_input(
            "Find a briefing", placeholder="Search a title, executive decision or topic",
            key="reader_find_briefing",
        ).strip().casefold()
        matching = [
            article for article in articles
            if search in (
                str(article.title) + " " + str(article.category or "") + " "
                + str(article.subtitle or "") + " " + str(article.excerpt or "")
            ).casefold()
        ]
        _reader_selected_edition(
            session, user, matching, saved_slugs, view="all",
        )

    with saved_tab:
        _reader_section_header(
            "YOUR PERSONAL READING LIST",
            "Keep the decisions worth revisiting.",
            "Return to the briefings you have saved for discussion, "
            "reference or a decision ahead. Remove any title when it no longer "
            "belongs in your reading list.",
        )
        # The server returns most recently saved first; preserve that order.
        saved_articles = [
            by_slug[str(row.get("article_slug") or "")]
            for row in saved
            if str(row.get("article_slug") or "") in by_slug
        ]
        _reader_selected_edition(
            session, user, saved_articles, saved_slugs, view="saved",
        )

    with pdf_tab:
        _reader_section_header(
            "YOUR DECISION VISUALS",
            "Your infographic collection.",
            "Find the original A4 briefing visuals you have previously "
            "downloaded. Prepare a fresh copy whenever you need one "
            "for your own review or discussion.",
        )
        available_downloads = [
            (by_slug[slug], row) for slug, row in unique_downloads.items()
            if slug in by_slug
        ]
        if not available_downloads:
            st.info(
                "No infographic downloads in your history yet. "
                "Open an Executive AI Briefing to find its available A4 visual."
            )
        else:
            pdf_search = st.text_input(
                "Find a downloaded infographic",
                placeholder="Search your briefing visuals",
                key="reader_pdf_search",
            ).strip().casefold()
            matching_pdfs = [
                (article, row) for article, row in available_downloads
                if pdf_search in (
                    str(article.title) + " " + str(article.category or "")
                ).casefold()
            ]
            st.caption(
                f"{len(matching_pdfs)} infographic"
                + ("" if len(matching_pdfs) == 1 else "s")
                + " in your download history"
            )
            pdf_page_size = 5
            pdf_pages = max(1, (len(matching_pdfs) + pdf_page_size - 1) // pdf_page_size)
            pdf_page = (
                st.selectbox(
                    "Browse PDF history pages", range(pdf_pages),
                    format_func=lambda i: f"Page {i + 1} of {pdf_pages}",
                    key="reader_pdf_history_page",
                )
                if pdf_pages > 1 else 0
            )
            for article, row in matching_pdfs[
                int(pdf_page) * pdf_page_size:(int(pdf_page) + 1) * pdf_page_size
            ]:
                slug = _clean_slug(str(article.slug))
                if not slug:
                    continue
                last_download = str(row.get("downloaded_at") or "")[:10] or "Date unavailable"
                times = sum(
                    1 for event in downloaded
                    if str(event.get("article_slug") or "") == slug
                )
                with st.container(border=True, key="reader_resource_" + slug):
                    st.caption(
                        "EXECUTIVE INFOGRAPHIC · "
                        + str(article.category or "Enterprise AI")
                    )
                    st.markdown("#### " + str(article.title))
                    st.caption(
                        "Last downloaded: " + last_download
                        + " · " + str(times) + " previous download"
                        + ("" if times == 1 else "s")
                    )
                    st.caption("Download again from the original briefing's A4 visual.")
                    if st.button(
                        "Open related briefing",
                        key="reader_pdf_open_" + slug,
                        use_container_width=False,
                    ):
                        _open_reader_briefing(slug)
                    _reader_pdf_controls(
                        session, user, slug, view="history_" + slug,
                    )
            if not matching_pdfs:
                st.info("No saved PDF matches that search. Try another topic.")

    with profile_tab:
        _reader_section_header(
            "YOUR ACCOUNT & READING PREFERENCES",
            "A library that stays yours.",
            "Manage how you return to your reading, the professional topics "
            "you follow and whether you receive editorial emails. "
            "Profile information is not displayed publicly.",
        )
        email = html_escape(str(user.get("email") or ""))
        joined = html_escape(str(profile.get("created_at") or "")[:10] or "Not recorded")
        updates = "On — by your choice" if profile.get("newsletter_opt_in") else "Off"
        st.html(
            '<section class="reader-account-summary" aria-label="Membership overview">'
            '<div><span>READER IDENTITY</span><strong>' + email + '</strong>'
            '<small>Verified email</small></div>'
            '<div><span>MEMBER SINCE</span><strong>' + joined + '</strong>'
            '<small>Complimentary Premium Reader access</small></div>'
            '<div><span>EDITORIAL EMAILS</span><strong>' + updates + '</strong>'
            '<small>Your preference, managed below</small></div></section>'
        )
        with st.expander("Edit my professional profile and editorial interests", expanded=False):
            _render_preferences(session, profile, user)
        _render_password_settings(session)
        st.caption(
            "Questions about your account or data? Email info@jairribeiro.com."
        )

    st.divider()
    if st.button("Sign out", key="reader_native_logout"):
        try:
            _request_json("POST", ANALYTICS_URL.rstrip("/") + "/auth/v1/logout",
                          token=session["access_token"], payload={})
        except (RuntimeError, ValueError, TimeoutError):
            pass
        for key in ("reader_native_session", "reader_native_user",
                    "reader_native_prepared"):
            st.session_state.pop(key, None)
        st.rerun()


def _dismiss_briefing_dialog() -> None:
    # Dismiss a prompt, not the reader's verified session.
    st.query_params.pop("pdf", None)
    st.query_params.pop("access", None)
    st.query_params.pop("signin", None)


@st.dialog("Executive AI Briefing · Free reader access", width="large",
           on_dismiss=_dismiss_briefing_dialog)
def _briefing_access_dialog(slug: str, title: str, purpose: str) -> None:
    """Passwordless full-edition access and the selected PDF in one dialog."""
    st.html("""<style>
    [data-testid="stDialog"] [data-testid="stDialogContent"] {
      background:#fffdf8!important;color:#11151b;border-radius:3px;
      border:1px solid #d8c6b7;
    }
    [data-testid="stDialog"] h3 {
      font:500 29px/1.15 Georgia,serif!important;color:#0b1220!important;
    }
    [data-testid="stDialog"] button[kind="primary"] {
      background:#b86134!important;border-color:#b86134!important;
      color:#fff!important;border-radius:0!important;min-height:46px;
    }
    </style>""")
    if not slug:
        st.warning("This briefing is not available.")
        return
    notice = st.session_state.pop("reader_native_flash", None)
    if notice:
        (st.success if notice[0] == "success" else st.error)(notice[1])
    session, user = _session()
    if not session or not user:
        _login(title or "this Executive AI Briefing")
        return

    st.markdown("### Your complete briefing is unlocked")
    st.write(
        "The full edition and executive decision framework are now available "
        "on this page."
    )
    if has_briefing_pdf(slug):
        try:
            with st.spinner("Preparing the A4 infographic"):
                pdf = _pdf_for_article(slug)
            if pdf:
                st.download_button(
                    "Download A4 infographic",
                    data=pdf,
                    file_name=f"{slug}-executive-infographic.pdf",
                    mime="application/pdf",
                    type="primary",
                    key="reader_dialog_download",
                    on_click=_record_download,
                    args=(session["access_token"], str(user["id"]), slug),
                )
            else:
                st.info("The infographic PDF is temporarily unavailable.")
        except (RuntimeError, ValueError, TimeoutError, OSError):
            st.info("The PDF could not be prepared; the full edition remains available.")
    else:
        st.caption("An A4 infographic PDF is not available for this edition.")
    st.caption("Signed in as " + str(user.get("email") or ""))
    if st.button("Continue reading the complete briefing", key="reader_dialog_close"):
        _dismiss_briefing_dialog()
        st.rerun()


def _dismiss_article_dialog() -> None:
    st.query_params.pop("access", None)
    st.query_params.pop("signin", None)


@st.dialog("Article · Free early access", width="large",
           on_dismiss=_dismiss_article_dialog)
def _article_access_dialog(slug: str, title: str) -> None:
    session, user = _session()
    if not session or not user:
        _login(title or "this article", resource_kind="article")
        return
    st.markdown("### Full article unlocked")
    st.write("This account also opens every Executive AI Briefing.")
    st.caption("Signed in as " + str(user.get("email") or ""))
    if st.button("Continue reading the article", key="reader_article_dialog_close",
                 type="primary"):
        _dismiss_article_dialog()
        st.rerun()


def render_article_access_dialog(slug: str, title: str = "") -> None:
    clean = _clean_slug(slug)
    if clean:
        _article_access_dialog(clean, title)


@st.dialog("Weekly AI · Premium Reader edition", width="large",
           on_dismiss=_dismiss_article_dialog)
def _weekly_ai_access_dialog(slug: str, title: str) -> None:
    """Same free reader account, password and email verification as Briefings."""
    session, user = _session()
    if not session or not user:
        _login(title or "this week's Weekly AI", resource_kind="weekly_ai")
        return
    st.markdown("### This week's complete Weekly AI is available")
    st.write("Previous editions are open to everyone. Your account also opens complete Executive AI Briefings.")
    st.caption("Signed in as " + str(user.get("email") or ""))
    if st.button("Continue to Weekly AI", key="reader_weekly_dialog_close",
                 type="primary"):
        _dismiss_article_dialog()
        st.rerun()


def render_weekly_ai_access_dialog(slug: str, title: str = "") -> None:
    clean = _clean_slug(slug)
    if clean and clean.startswith("weekly-ai-"):
        _weekly_ai_access_dialog(clean, title)


def render_briefing_access_dialog(slug: str, title: str = "",
                                  purpose: str = "access") -> None:
    """Authenticate for the specific edition, not a detached PDF library."""
    cleaned = _clean_slug(slug)
    if cleaned:
        _briefing_access_dialog(cleaned, title, purpose)


def render_reader_native() -> None:
    """Verified reader flow embedded in the real portfolio navigation and footer."""
    # Consume the single-use token BEFORE rendering the shared navigation logo
    # or any external media. The token must never leak in a Referer header.
    _consume_query_verification()
    staging = _host_origin().startswith("https://jairribeiro-reader-test.")
    st.html(reader_header(staging=staging))
    with st.container(key="reader_flow"):
        # Same-page editorial CTA lands directly at the real Streamlit form.
        st.html('<span id="reader-access" aria-hidden="true"></span>')
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
                "name, verified email, saved briefings and PDF download "
                "history to provide library access. Optional professional "
                "profile fields (role, organization, location, interests and "
                "leadership context) help us understand readers and improve "
                "future resources; these details are not displayed publicly."
            )
            st.write(
                "We use Supabase for authentication and reader records, and "
                "a transactional email provider for one-time access messages. "
                "Editorial emails are optional and are sent only when you "
                "affirmatively choose to subscribe; you can withdraw that "
                "preference in the reader library."
            )
            st.write(
                "For account help, access, correction, deletion or "
                "questions about your information, email "
                "info@jairribeiro.com."
            )
    st.html(reader_footer())
