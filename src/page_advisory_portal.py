"""Private, verified executive-advisory registration and account space.

Advisory and Reader have different profiles and access decisions. Both use one
Supabase Auth identity: an advisory member receives Reader membership, while a
Reader account alone never creates or authorizes an advisory profile.
"""
from __future__ import annotations

import re
from urllib.parse import quote

import streamlit as st

from page_reader_native import (
    _consume_query_verification,
    _password_signin,
    _request_email,
    _session,
    _set_reader_password,
    _verify,
)
from reader_membership import EMAIL, _utc_now
from site_assets import ADVISORY_EMAIL, PRIVACY_EMAIL
from site_cms import _request_json, _rest_url

ADVISORY_CSS = """
<style>
[data-testid="stAppViewContainer"]{background:#f4f0e8}
.advisory-private-hero{padding:clamp(38px,6vw,76px) clamp(24px,5vw,66px);
 background:linear-gradient(130deg,#0b1729,#192d43);color:#faf8f1;
 border-bottom:4px solid #c78759;margin-bottom:26px}
.advisory-private-hero .eyebrow{color:#dcaa84;text-transform:uppercase;
 font-size:11px;font-weight:800;letter-spacing:.18em}
.advisory-private-hero h1{max-width:900px;font:500 clamp(40px,5vw,69px)/1.07 Georgia,serif;
 letter-spacing:-.035em;margin:17px 0 20px}
.advisory-private-hero p:not(.eyebrow){max-width:770px;font-size:18px;line-height:1.7;color:#d1dbe5}
.advisory-private-hero .benefit{font-size:13px!important;color:#e7bc9c!important;font-weight:750}
.advisory-portal-intro{padding:12px 5px 20px;color:#445166;max-width:780px;font-size:16px;line-height:1.7}
.advisory-portal-intro h2{color:#182d42;font:500 33px/1.18 Georgia,serif;margin:0 0 10px}
.advisory-portal-badge{border-left:3px solid #bd774b;padding:16px 24px;
 background:#fffaf3;margin:16px 0 29px;color:#34475b;line-height:1.65}
.advisory-portal-badge strong{color:#162c43}
[data-testid="stForm"]{border:1px solid #d5cabf!important;
 background:#fffdfa!important;padding:clamp(20px,3vw,34px)!important;
 box-shadow:0 12px 30px rgba(16,31,48,.045)}
[data-testid="stForm"] label{color:#22364b!important}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#b76c42!important;
 color:#fff!important;border-color:#b76c42!important;font-weight:700!important}
</style>
"""

def _get_advisory_profile(session: dict, user: dict) -> dict | None:
    token = str(session["access_token"])
    rows = _request_json(
        "GET",
        _rest_url("portfolio_advisory_profiles?select=*&user_id=eq."
                  + quote(str(user["id"]), safe="") + "&limit=1"),
        token=token, timeout=10,
    )
    return rows[0] if isinstance(rows, list) and rows else None


def _register_advisory(session: dict, user: dict, name: str,
                       organization: str, role_title: str, decision: str) -> None:
    name = str(name or "").strip()
    organization = str(organization or "").strip()
    role_title = str(role_title or "").strip()
    decision = str(decision or "").strip()
    if not name or len(name) > 80:
        raise ValueError("Enter your first name.")
    if len(organization) > 180 or len(role_title) > 160 or len(decision) > 1200:
        raise ValueError("One or more fields are too long.")
    if not user.get("email_confirmed_at"):
        raise ValueError("Verify your email first.")
    _request_json(
        "POST", _rest_url("portfolio_advisory_profiles"),
        token=str(session["access_token"]),
        payload={
            "user_id": str(user["id"]),
            "email": str(user["email"]).lower(),
            "first_name": name,
            "organization": organization,
            "role_title": role_title,
            "decision_context": decision,
        }, prefer="return=representation", timeout=12,
    )


def _update_context(session: dict, user: dict, organization: str,
                    role_title: str, decision: str) -> None:
    _request_json(
        "PATCH", _rest_url("portfolio_advisory_profiles?user_id=eq."
                           + quote(str(user["id"]), safe="")),
        token=str(session["access_token"]),
        payload={
            "organization": organization.strip()[:180],
            "role_title": role_title.strip()[:160],
            "decision_context": decision.strip()[:1200],
            "updated_at": _utc_now(),
        }, timeout=12,
    )


def _open_library() -> None:
    st.query_params.clear()
    st.query_params["page"] = "readers"
    st.rerun()


def _sign_out() -> None:
    # The underlying Supabase identity is shared, not the membership rights.
    st.session_state.pop("reader_native_session", None)
    st.session_state.pop("reader_native_user", None)
    st.session_state.pop("advisory_member", None)
    st.session_state.pop("advisory_pending_email", None)
    st.rerun()


def _advisory_login() -> None:
    st.html("""<section class="advisory-portal-intro"><h2>A private point of contact for executive work.</h2>
<p>Create your advisory account to share your decision context and maintain a direct professional
relationship. Registration is complimentary and does not establish a consulting engagement.
It also includes access to the complete Premium Reader library.</p></section>""")
    returning = st.radio(
        "Advisory account", ["Create your advisory account", "Sign in to advisory"],
        index=1 if st.query_params.get("signin") == "1" else 0,
        horizontal=True, key="advisory_auth_mode",
    ) == "Sign in to advisory"

    if returning:
        signin_method = st.radio(
            "Sign-in method", ["Email and password", "Email verification code"],
            horizontal=True, key="advisory_signin_method",
        )
        if signin_method == "Email and password":
            with st.form("advisory_password_signin", clear_on_submit=True):
                email = st.text_input("Email address", max_chars=254)
                password = st.text_input("Password", type="password", max_chars=128)
                submit = st.form_submit_button("Sign in", type="primary")
            if submit:
                try:
                    _password_signin(str(email).strip().lower(), str(password))
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError, KeyError):
                    st.error("Sign-in failed. Verify your details or use an email code.")
            st.caption("No password yet? Choose Email verification code to verify your address.")
            return

    with st.form("advisory_email_access"):
        name = st.text_input("First name", max_chars=80, disabled=returning)
        email = st.text_input("Professional email", max_chars=254, placeholder="you@organization.com")
        submit = st.form_submit_button(
            "Send my advisory access link" if not returning else "Email my sign-in link",
            type="primary",
        )
    if submit:
        address = str(email).strip().lower()
        if not EMAIL.fullmatch(address) or (not returning and not str(name).strip()):
            st.error("Enter your first name and a valid email address.")
        else:
            try:
                _request_email(str(name).strip(), address, False, returning,
                               destination="advisory-access")
                st.session_state["advisory_pending_email"] = address
                st.success("Check your inbox for your secure verification link or code.")
            except (RuntimeError, ValueError, TimeoutError):
                st.error("Verification email could not be sent. Please try again.")

    pending = st.session_state.get("advisory_pending_email")
    if pending:
        with st.form("advisory_email_code"):
            code = st.text_input("Email verification code", max_chars=10)
            verified = st.form_submit_button("Verify and continue")
        if verified:
            if not re.fullmatch(r"\d{6,10}", str(code).strip()):
                st.error("Enter the numeric code from the email.")
            else:
                try:
                    _verify({"email": pending, "token": str(code).strip(), "type": "email"})
                    st.session_state.pop("advisory_pending_email", None)
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("The code expired or could not be verified.")
    st.caption("Editorial emails are not enabled by creating an advisory account.")
    st.markdown(f"Privacy and account questions: [{PRIVACY_EMAIL}](mailto:{PRIVACY_EMAIL}).")


def _advisory_enroll(session: dict, user: dict) -> None:
    st.html("""<section class="advisory-portal-intro"><h2>Complete your advisory registration.</h2>
<p>Your email is verified. Add enough professional context to make an initial conversation useful.
This does not book a meeting or create a paid engagement. You can return to update your context.</p></section>""")
    meta = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}
    with st.form("advisory_complete_registration"):
        first = st.text_input("First name", value=str(meta.get("reader_first_name") or ""), max_chars=80)
        organization = st.text_input("Organization (optional)", max_chars=180)
        role = st.text_input("Role / title (optional)", max_chars=160)
        question = st.text_area(
            "The business decision or challenge you are considering (optional)",
            max_chars=1200, height=130,
            help="Do not share confidential, regulated or personal information here.",
        )
        accepted = st.checkbox("I have read the Privacy & Data notice and understand how this information is used.")
        submit = st.form_submit_button("Create my advisory account", type="primary")
    if submit:
        if not accepted:
            st.error("Please read and acknowledge the privacy notice.")
            return
        try:
            _register_advisory(session, user, first, organization, role, question)
            st.success("Advisory access created. Your full Reader library is included.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except (RuntimeError, TimeoutError, KeyError):
            st.error("We could not create the account. Please retry or contact advisory support.")
    st.caption(f"Questions: {ADVISORY_EMAIL} · [Privacy notice](?page=privacy)")


def _advisory_account(session: dict, user: dict, profile: dict) -> None:
    if profile.get("account_status") != "active":
        st.error("This advisory account is not currently active. Contact advisory support.")
        return
    st.session_state["advisory_member"] = True
    name = str(profile.get("first_name") or "there")
    st.html("""<div class="advisory-portal-badge">
<strong>Your advisory account is active.</strong> Full access to the Premium Reader library
is included. Registration gives you a direct advisory contact channel;
scope, availability and commercial terms are agreed separately.</div>""")
    st.markdown("### Welcome, " + name.replace("<", "").replace(">", "") + ".")
    st.write(
        "Use this space to keep the executive question current. For an actual engagement, "
        "we begin with the decision, mandate, stakeholders and available evidence, "
        "then agree a focused scope and tangible outputs."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open my full Premium Reader library", type="primary", use_container_width=True):
            _open_library()
    with col2:
        st.link_button(
            "Discuss an advisory decision",
            f"mailto:{ADVISORY_EMAIL}?subject=Advisory%20discussion",
            use_container_width=True,
        )

    st.markdown("#### Your advisory context")
    st.caption("Only you and authorized service administrators can access your stored context. Never upload sensitive material here.")
    with st.form("advisory_context"):
        organization = st.text_input(
            "Organization", value=str(profile.get("organization") or ""), max_chars=180)
        role = st.text_input(
            "Role / title", value=str(profile.get("role_title") or ""), max_chars=160)
        decision = st.text_area(
            "The decision you are working through",
            value=str(profile.get("decision_context") or ""),
            max_chars=1200, height=130,
        )
        save = st.form_submit_button("Update my advisory context")
    if save:
        try:
            _update_context(session, user, organization, role, decision)
            st.success("Your advisory context has been updated.")
            st.rerun()
        except (RuntimeError, ValueError, TimeoutError):
            st.error("The update could not be saved.")
    st.markdown("#### How we work")
    st.write(
        "**1. Frame the decision.** Identify the business outcome, decision rights and time horizon.  "
        "**2. Assess the situation.** Review evidence, risks, operating dependencies and viable options.  "
        "**3. Agree the engagement.** Define the counterpart, working sessions and deliverables.  "
        "**4. Make the next move.** Leave with documented recommendations, owners and the next decision point."
    )
    st.caption(
        "Your account is not a contract, subscription purchase or promise of availability. "
        "Scheduling and commercial terms are agreed directly."
    )
    with st.expander("Account security and sign-out"):
        with st.form("advisory_set_password", clear_on_submit=True):
            pwd = st.text_input("Set or change password (12 characters minimum)", type="password", max_chars=128)
            confirm = st.text_input("Confirm password", type="password", max_chars=128)
            do_change = st.form_submit_button("Save password")
        if do_change:
            if pwd != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    _set_reader_password(session, str(pwd))
                    st.success("Password updated. This secures your shared sign-in identity.")
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("The password could not be changed.")
        if st.button("Sign out of advisory and reader access"):
            _sign_out()
    st.caption(f"Privacy requests: {PRIVACY_EMAIL} · Advisory correspondence: {ADVISORY_EMAIL}")


def render_advisory_portal() -> None:
    # Consume OTP hash before rendering page media or other scripts.
    _consume_query_verification()
    st.html(ADVISORY_CSS)
    st.html("""<header class="advisory-private-hero">
<p class="eyebrow">Jair Ribeiro / Private Executive Advisory</p>
<h1>Clearer decisions. Practical next steps.</h1>
<p>A direct place to explore enterprise AI, data, governance, portfolio priorities
and the operating decisions behind measurable business value.</p>
<p class="benefit">Included with Advisory access: the complete Premium Reader library,
Executive AI Briefings, full articles and downloadable infographics.</p>
</header>""")
    session, user = _session()
    if session is None or user is None:
        _advisory_login()
        return
    try:
        profile = _get_advisory_profile(session, user)
    except (RuntimeError, ValueError, TimeoutError):
        st.error("We could not confirm your advisory membership. Please retry.")
        return
    if not profile:
        st.session_state.pop("advisory_member", None)
        _advisory_enroll(session, user)
        return
    _advisory_account(session, user, profile)
