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
    if requested:
        # Preserve the specific publication after email verification even
        # if the reader opens the secure link in a fresh browser tab.
        # Add same-host briefing callback patterns to the Supabase allowlist.
        target = _host_origin() + "/?" + urlencode({
            "page": "briefing", "article": requested,
            "pdf" if purpose == "pdf" else "access": "1",
        })
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

def _login(requested_title: str = "") -> None:
    if requested_title:
        st.markdown("### Continue to the complete briefing")
        st.write(
            "Verify your email to read **" + requested_title +
            "** in full, including the executive decision framework and "
            "original infographic. Access is free, and editorial emails "
            "are optional."
        )
    else:
        st.markdown("### Complimentary access to executive resources")
        st.write(
            "Read the opening of any briefing without an account. "
            "Verify your email for complete Executive AI Briefings, original "
            "infographics and A4 PDF downloads. Editorial updates are optional."
        )
    returning = st.radio(
        "Reader status", ["I'm new here", "I already have an account"],
        index=1 if str(st.query_params.get("signin", "")) == "1" else 0,
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


def _reader_selected_edition(
    session: dict, user: dict, articles: list, saved_slugs: set[str],
    *, view: str,
) -> None:
    if not articles:
        st.info("No briefings match this selection.")
        return
    selected = st.selectbox(
        "Select an Executive AI Briefing",
        range(len(articles)), key="reader_select_" + view,
        format_func=lambda index: str(articles[index].title),
    )
    article = articles[selected]
    slug = _clean_slug(str(article.slug))
    st.markdown("#### " + str(article.title))
    st.write(str(article.subtitle or article.excerpt or
                 "An executive perspective on AI and business decisions."))
    left, right = st.columns(2)
    with left:
        if st.button("Read complete briefing", type="primary",
                     key="reader_open_" + view):
            _open_reader_briefing(slug)
    with right:
        saved = slug in saved_slugs
        label = "Remove from saved" if saved else "Save to my library"
        if st.button(label, key="reader_save_" + view):
            try:
                _update_saved(session, user, slug, saved=not saved)
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Could not update your saved briefings.")
    _reader_pdf_controls(session, user, slug, view=view)


def _library(session: dict, user: dict) -> None:
    """Member hub: full catalog, saved editions, PDF history, profile."""
    try:
        profile = _register_profile(session, user)
    except (RuntimeError, ValueError, TimeoutError):
        st.error("Your verified account could not be loaded.")
        return

    first = str(profile.get("first_name") or "").strip()
    st.markdown("### Your Executive AI Briefings library")
    st.write(
        ("Welcome, " + first + ". " if first else "")
        + "Your verified reader access unlocks every published complete edition "
        + "and its infographic wherever available."
    )
    st.caption("Signed in as " + str(user.get("email") or ""))
    st.divider()

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

    st.caption(
        f"{len(articles)} complete editions · "
        f"{len(saved_slugs)} saved · "
        f"{len(unique_downloads)} previously downloaded PDFs"
    )

    all_tab, saved_tab, pdf_tab, profile_tab = st.tabs([
        "All briefings", "Saved", "My PDFs", "My profile",
    ])
    with all_tab:
        st.markdown("#### Complete Executive AI Briefings")
        st.caption("Every published edition is available with this verified account.")
        search = st.text_input(
            "Find a briefing", placeholder="Search by title or topic",
            key="reader_find_briefing",
        ).strip().casefold()
        matching = [
            article for article in articles
            if search in (
                str(article.title) + " " +
                str(article.subtitle or article.excerpt or "")
            ).casefold()
        ]
        _reader_selected_edition(
            session, user, matching, saved_slugs, view="all",
        )

    with saved_tab:
        st.markdown("#### Your saved editions")
        st.caption("Save or remove editions at any time. Saved titles remain "
                   "available when you return and sign in again.")
        saved_articles = [
            by_slug[slug] for slug in saved_slugs if slug in by_slug
        ]
        saved_articles.sort(key=lambda a: str(a.title).casefold())
        _reader_selected_edition(
            session, user, saved_articles, saved_slugs, view="saved",
        )

    with pdf_tab:
        st.markdown("#### Your infographic PDFs")
        st.caption(
            "Review which briefing PDFs you downloaded and download them again. "
            "Actual files are generated when requested, rather than stored "
            "as personal copies on the website."
        )
        available_downloads = [
            (by_slug[slug], row) for slug, row in unique_downloads.items()
            if slug in by_slug
        ]
        if not available_downloads:
            st.info("No infographic PDFs have been downloaded with this account.")
        else:
            summary = []
            for article, row in available_downloads:
                when = str(row.get("downloaded_at") or "")
                summary.append({
                    "Briefing": str(article.title),
                    "Last download": when[:10] if when else "Not recorded",
                    "Downloads": sum(
                        1 for event in downloaded
                        if str(event.get("article_slug")) == str(article.slug)
                    ),
                })
            st.dataframe(summary, hide_index=True, use_container_width=True)
            chosen = st.selectbox(
                "Download again",
                range(len(available_downloads)),
                format_func=lambda i: str(available_downloads[i][0].title),
                key="reader_select_pdf_history",
            )
            article, _ = available_downloads[chosen]
            _reader_pdf_controls(
                session, user, str(article.slug), view="history",
            )

    with profile_tab:
        st.markdown("#### My reader profile")
        st.write("**Verified email:** " + str(user.get("email") or ""))
        st.write("**Member since:** " + str(profile.get("created_at") or "")[:10])
        st.write(
            "**Editorial updates:** "
            + ("Subscribed" if profile.get("newsletter_opt_in") else "Not subscribed")
        )
        _render_preferences(session, profile, user)

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
