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

FOCUS_OPTIONS = (
    "", "AI strategy and investment priorities", "AI & data governance",
    "Adoption and business value", "Operating model and ownership",
    "Data readiness and stewardship", "Other / exploring",
)
HORIZON_OPTIONS = (
    "", "Within 30 days", "1–3 months", "3–6 months",
    "Exploratory / no date yet",
)
INTAKE_LIMITS = {
    "first_name": 80, "last_name": 80, "organization": 180,
    "role_title": 160, "decision_context": 1200,
    "advisory_focus": 90, "decision_horizon": 60,
}


def _validate_intake(raw: dict) -> dict:
    """Validate professional context before OTP and again after email verification."""
    value = {key: str(raw.get(key) or "").strip() for key in INTAKE_LIMITS}
    for key, limit in INTAKE_LIMITS.items():
        if len(value[key]) > limit:
            raise ValueError("One or more registration fields are too long.")
    required = ("first_name", "last_name", "organization", "role_title")
    if any(not value[key] for key in required):
        raise ValueError("Please enter your full name, professional role and organization.")
    if len(value["decision_context"]) < 12:
        raise ValueError("Briefly describe the decision or outcome you are considering (at least 12 characters).")
    if value["advisory_focus"] not in FOCUS_OPTIONS or value["decision_horizon"] not in HORIZON_OPTIONS:
        raise ValueError("Select one of the available advisory options.")
    return value


def _signup_context(user: dict) -> dict | None:
    """Return a user's staged intake, never an authorization claim."""
    email = str(user.get("email") or "").strip().lower()
    staged = st.session_state.get("advisory_signup_intake")
    if isinstance(staged, dict) and staged.get("_email") == email and staged.get("privacy_notice_ack") is True:
        try:
            return _validate_intake(staged)
        except ValueError:
            pass
    metadata = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}
    if metadata.get("advisory_intake_v1") is not True or metadata.get("advisory_privacy_notice_ack") is not True:
        return None
    raw = {key: metadata.get("advisory_" + key) for key in INTAKE_LIMITS}
    try:
        return _validate_intake(raw)
    except ValueError:
        return None


def _get_advisory_profile(session: dict, user: dict) -> dict | None:
    token = str(session["access_token"])
    rows = _request_json(
        "GET",
        _rest_url("portfolio_advisory_profiles?select=*&user_id=eq."
                  + quote(str(user["id"]), safe="") + "&limit=1"),
        token=token, timeout=10,
    )
    return rows[0] if isinstance(rows, list) and rows else None


def _register_advisory(session: dict, user: dict, intake: dict) -> None:
    details = _validate_intake(intake)
    if not user.get("email_confirmed_at"):
        raise ValueError("Verify your email first.")
    _request_json(
        "POST", _rest_url("portfolio_advisory_profiles"),
        token=str(session["access_token"]),
        payload={
            "user_id": str(user["id"]),
            "email": str(user["email"]).strip().lower(),
            **details,
        }, prefer="return=representation", timeout=12,
    )


def _update_context(session: dict, user: dict, intake: dict) -> None:
    details = _validate_intake(intake)
    _request_json(
        "PATCH", _rest_url("portfolio_advisory_profiles?user_id=eq."
                           + quote(str(user["id"]), safe="")),
        token=str(session["access_token"]),
        payload={**details, "updated_at": _utc_now()}, timeout=12,
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
    st.session_state.pop("advisory_signup_intake", None)
    st.rerun()


def _password_authenticated(session: dict) -> bool:
    """The server checks the Auth password method; Supabase RLS enforces it too."""
    try:
        return _request_json(
            "POST", _rest_url("rpc/portfolio_advisory_password_session_v1"),
            token=str(session["access_token"]), payload={}, timeout=10,
        ) is True
    except (RuntimeError, ValueError, TimeoutError, KeyError):
        return False


def _first_password_form(session: dict, user: dict) -> None:
    st.html("""<section class="advisory-portal-intro">
<h2>Email confirmed. Set your password.</h2>
<p>Your email has been confirmed. Set a password to activate your Advisory account.
Future visits use your email and password, not an email access link.</p>
</section>""")
    with st.form("advisory_first_password", clear_on_submit=True):
        password = st.text_input(
            "New password", type="password", max_chars=128,
            help="Use a unique password of at least 12 characters.",
        )
        confirmation = st.text_input(
            "Confirm password", type="password", max_chars=128,
        )
        submit = st.form_submit_button(
            "Set password and activate my account", type="primary",
        )
    if not submit:
        st.caption("Advisory access remains inactive until your password is saved.")
        return
    if password != confirmation:
        st.error("The passwords do not match.")
        return
    try:
        _set_reader_password(session, str(password))
        # A new password login creates a fresh signed JWT with AMR=password,
        # required by the Advisory database policy before profile activation.
        _password_signin(str(user["email"]).strip().lower(), str(password))
        st.session_state.pop("advisory_pending_email", None)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except (RuntimeError, TimeoutError, KeyError):
        st.error("The password could not be confirmed. "
                 "Try again, or request a new password reset email.")


def _advisory_login() -> None:
    st.html("""<section class="advisory-portal-intro">
<h2>A professional introduction, without the paperwork.</h2>
<p>Tell me who you are and the decision you are facing. This gives our first
conversation useful context without requiring a lengthy application.
Your advisory account also includes the complete Premium Reader library.</p>
</section>""")
    returning = st.radio(
        "Advisory account", ["Create your advisory account", "Sign in to advisory"],
        index=1 if st.query_params.get("signin") == "1" else 0,
        horizontal=True, key="advisory_auth_mode",
    ) == "Sign in to advisory"

    if returning:
        with st.form("advisory_password_signin", clear_on_submit=True):
            email = st.text_input("Email address", max_chars=254)
            password = st.text_input("Password", type="password", max_chars=128)
            submit = st.form_submit_button("Sign in to advisory", type="primary")
        if submit:
            try:
                _password_signin(str(email).strip().lower(), str(password))
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError):
                st.error("Sign-in failed. Check your email and password.")
        with st.expander("Forgot your password?"):
            st.write("Request a one-time email confirmation to set a new password.")
            with st.form("advisory_password_recovery"):
                recovery_email = st.text_input("Account email address", max_chars=254)
                recover = st.form_submit_button("Send password reset email")
            if recover:
                address = str(recovery_email).strip().lower()
                if not EMAIL.fullmatch(address):
                    st.error("Enter a valid email address.")
                else:
                    try:
                        _request_email("", address, False, True, destination="advisory-access")
                        st.success("If the account exists, check that inbox for a "
                                   "confirmation link to set a new password.")
                    except (RuntimeError, ValueError, TimeoutError):
                        st.error("Password recovery email could not be sent.")
        return
    else:
        st.caption("Professional details · Required fields are marked *")
        with st.form("advisory_initial_registration"):
            a, b = st.columns(2)
            with a:
                first = st.text_input("First name *", max_chars=80, placeholder="First name")
            with b:
                last = st.text_input("Last name *", max_chars=80, placeholder="Last name")
            a, b = st.columns(2)
            with a:
                role = st.text_input("Job title / role *", max_chars=160, placeholder="e.g. Chief Operating Officer")
            with b:
                company = st.text_input("Organization *", max_chars=180, placeholder="Company or organization")
            email = st.text_input("Professional email *", max_chars=254, placeholder="you@organization.com")
            decision = st.text_area(
                "What decision, challenge or business outcome brings you here? *",
                max_chars=1200, height=110,
                placeholder="A couple of sentences are enough. What needs a clearer decision?",
                help="Please do not include confidential business data, contracts or personal information.",
            )
            a, b = st.columns(2)
            with a:
                focus = st.selectbox(
                    "Advisory focus (optional)", FOCUS_OPTIONS,
                    format_func=lambda v: v or "Select if relevant",
                )
            with b:
                horizon = st.selectbox(
                    "Decision timeframe (optional)", HORIZON_OPTIONS,
                    format_func=lambda v: v or "Not decided",
                )
            st.caption("Keep the description high-level. No budget, confidential documents or phone number are required.")
            accepted = st.checkbox("I have read the Privacy & Data notice.")
            submit = st.form_submit_button("Email my verification link", type="primary")
        st.caption("Review the [Privacy & Data notice](?page=privacy). Advisory registration is complimentary; any paid engagement is agreed separately.")
        if submit:
            address = str(email).strip().lower()
            try:
                if not EMAIL.fullmatch(address):
                    raise ValueError("Enter a valid professional email address.")
                if not accepted:
                    raise ValueError("Please read and acknowledge the privacy notice.")
                details = _validate_intake({
                    "first_name": first, "last_name": last,
                    "role_title": role, "organization": company,
                    "decision_context": decision, "advisory_focus": focus,
                    "decision_horizon": horizon,
                })
                _request_email(first.strip(), address, False, False,
                               destination="advisory-access",
                               advisory_intake={**details, "privacy_notice_ack": True})
                st.session_state["advisory_signup_intake"] = {
                    **details, "privacy_notice_ack": True, "_email": address,
                }
                st.session_state["advisory_pending_email"] = address
                st.success("Open the verification link sent to your email. It will take you to the password setup page; your Advisory account activates only after you set a password.")
            except ValueError as exc:
                st.error(str(exc))
            except (RuntimeError, TimeoutError):
                st.error("Verification email could not be sent. Please try again.")

    if st.session_state.get("advisory_pending_email"):
        st.info("Check your inbox and follow the verification link to set your password. "
                "No sign-in link or verification code is needed.")
    st.caption("Registration does not subscribe you to editorial emails.")
    st.markdown(f"Questions: [{ADVISORY_EMAIL}](mailto:{ADVISORY_EMAIL}) · [Privacy & Data notice](?page=privacy)")


def _advisory_enroll(session: dict, user: dict) -> None:
    # First-time sign-ups normally completed the professional intake before
    # email verification. Carry it into the protected profile automatically.
    # Existing Reader identities and missing/stale metadata get a short form.
    staged = _signup_context(user)
    if staged:
        try:
            _register_advisory(session, user, staged)
            st.session_state.pop("advisory_signup_intake", None)
            st.rerun()
            return
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            st.warning("Your email is verified. Please confirm your professional details below.")

    st.html("""<section class="advisory-portal-intro">
<h2>Complete your advisory account.</h2>
<p>Your email is verified. Confirm your professional details and the decision you
would like to discuss. This does not establish a commercial engagement.</p>
</section>""")
    meta = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}
    pref = {}
    for field in INTAKE_LIMITS:
        pref[field] = str(meta.get("advisory_" + field) or "").strip()
    pref["first_name"] = pref["first_name"] or str(meta.get("reader_first_name") or "")
    with st.form("advisory_complete_registration"):
        a, b = st.columns(2)
        with a:
            first = st.text_input("First name *", value=pref["first_name"], max_chars=80)
        with b:
            last = st.text_input("Last name *", value=pref["last_name"], max_chars=80)
        a, b = st.columns(2)
        with a:
            role = st.text_input("Job title / role *", value=pref["role_title"], max_chars=160)
        with b:
            company = st.text_input("Organization *", value=pref["organization"], max_chars=180)
        decision = st.text_area(
            "Decision, challenge or business outcome *",
            value=pref["decision_context"], max_chars=1200, height=120,
            help="Please share only non-confidential, high-level context.",
        )
        a, b = st.columns(2)
        with a:
            focus = st.selectbox(
                "Advisory focus (optional)", FOCUS_OPTIONS,
                index=FOCUS_OPTIONS.index(pref["advisory_focus"]) if pref["advisory_focus"] in FOCUS_OPTIONS else 0,
                format_func=lambda v: v or "Select if relevant",
            )
        with b:
            horizon = st.selectbox(
                "Decision timeframe (optional)", HORIZON_OPTIONS,
                index=HORIZON_OPTIONS.index(pref["decision_horizon"]) if pref["decision_horizon"] in HORIZON_OPTIONS else 0,
                format_func=lambda v: v or "Not decided",
            )
        accepted = st.checkbox("I have read the Privacy & Data notice.")
        submit = st.form_submit_button("Create my advisory account", type="primary")
    if submit:
        try:
            if not accepted:
                raise ValueError("Please read and acknowledge the privacy notice.")
            details = _validate_intake({
                "first_name": first, "last_name": last, "organization": company,
                "role_title": role, "decision_context": decision,
                "advisory_focus": focus, "decision_horizon": horizon,
            })
            _register_advisory(session, user, details)
            st.session_state.pop("advisory_signup_intake", None)
            st.success("Your advisory account is ready. Full Premium Reader access is included.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except (RuntimeError, TimeoutError, KeyError):
            st.error("The account could not be created. Please retry or contact advisory support.")
    st.caption(f"Questions: {ADVISORY_EMAIL} · [Privacy & Data notice](?page=privacy)")


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

    st.markdown("#### Your professional context")
    st.caption("Keep your information current. Only high-level, non-confidential business context should be entered here.")
    with st.form("advisory_context"):
        a, b = st.columns(2)
        with a:
            first = st.text_input(
                "First name", value=str(profile.get("first_name") or ""), max_chars=80)
        with b:
            last = st.text_input(
                "Last name", value=str(profile.get("last_name") or ""), max_chars=80)
        a, b = st.columns(2)
        with a:
            role = st.text_input(
                "Job title / role", value=str(profile.get("role_title") or ""), max_chars=160)
        with b:
            organization = st.text_input(
                "Organization", value=str(profile.get("organization") or ""), max_chars=180)
        decision = st.text_area(
            "The decision or business outcome you are working through",
            value=str(profile.get("decision_context") or ""),
            max_chars=1200, height=120,
        )
        a, b = st.columns(2)
        with a:
            current_focus = str(profile.get("advisory_focus") or "")
            focus = st.selectbox(
                "Advisory focus", FOCUS_OPTIONS,
                index=FOCUS_OPTIONS.index(current_focus) if current_focus in FOCUS_OPTIONS else 0,
                format_func=lambda v: v or "Not specified",
            )
        with b:
            current_horizon = str(profile.get("decision_horizon") or "")
            horizon = st.selectbox(
                "Decision timeframe", HORIZON_OPTIONS,
                index=HORIZON_OPTIONS.index(current_horizon) if current_horizon in HORIZON_OPTIONS else 0,
                format_func=lambda v: v or "Not specified",
            )
        save = st.form_submit_button("Update my advisory context")
    if save:
        try:
            _update_context(session, user, {
                "first_name": first, "last_name": last, "organization": organization,
                "role_title": role, "decision_context": decision,
                "advisory_focus": focus, "decision_horizon": horizon,
            })
            st.success("Your advisory context has been updated.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except (RuntimeError, TimeoutError):
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
        notice = st.session_state.get("reader_native_flash")
        if isinstance(notice, tuple) and notice[0] == "error":
            st.error(str(notice[1]))
            st.session_state.pop("reader_native_flash", None)
        _advisory_login()
        return
    if not _password_authenticated(session):
        # Email confirmation establishes identity only; never Advisory access.
        _first_password_form(session, user)
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
