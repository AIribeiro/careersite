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
    _request_password_recovery,
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
.advisory-process-guide{margin:24px 0 32px;padding:25px;border:1px solid #d9cdbd;background:#fffaf3}
.advisory-process-steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}
.advisory-process-steps div{padding:0 13px 0 0;border-right:1px solid #e8ded0}
.advisory-process-steps div:last-child{border-right:none}
.advisory-process-steps strong{display:block;font:700 13px/1.5 Arial,sans-serif;color:#172d42}
.advisory-process-steps span{display:block;font:12px/1.6 Arial,sans-serif;color:#5c6875;margin-top:8px}
@media(max-width:720px), (max-device-width:720px){
 .advisory-process-steps{grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
 .advisory-process-steps div{border-right:0}
}
@media(max-width:420px), (max-device-width:420px){
 .advisory-process-guide{padding:20px 16px}
 .advisory-process-steps{grid-template-columns:1fr;gap:12px}
 .advisory-process-steps div{padding-bottom:12px;border-bottom:1px solid #e8ded0}
}
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
    st.session_state.pop("advisory_password_saved_user_id", None)
    st.session_state.pop("advisory_recovery_verified", None)
    st.session_state.pop("advisory_member_navigation", None)
    st.session_state.pop("advisory_member_conversation", None)
    st.query_params.pop("view", None)
    st.query_params.pop("request", None)
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


class AdvisoryPasswordSigninPending(RuntimeError):
    """Password is saved (or already current), but automatic sign-in did not finish."""


def _existing_password_error(exc: Exception) -> bool:
    """Supabase returns 422 same_password for an idempotent password submission."""
    detail = str(exc).casefold()
    return "same_password" in detail or (
        "new password should be different from the old password" in detail
    )


def _complete_advisory_password_setup(session: dict, user: dict, password: str) -> bool:
    """Set a password, or reuse the same current one; then authenticate it.

    Return True if the supplied password was already current. An Auth update
    and a subsequent Reader session/provisioning are separate operations.
    Never suggest that the password failed merely because sign-in failed.
    """
    already_current = False
    try:
        _set_reader_password(session, str(password))
    except RuntimeError as exc:
        if not _existing_password_error(exc):
            raise
        already_current = True

    try:
        _password_signin(str(user["email"]).strip().lower(), str(password))
    except (RuntimeError, ValueError, TimeoutError, KeyError) as exc:
        raise AdvisoryPasswordSigninPending(
            "The password is saved, but automatic sign-in did not complete."
        ) from exc
    return already_current


def _first_password_form(session: dict, user: dict) -> None:
    account_id = str(user.get("id") or "")
    if st.session_state.get("advisory_password_saved_user_id") == account_id:
        st.html("""<section class="advisory-portal-intro">
<h2>Your password is ready. Complete your sign-in.</h2>
<p>The password is already set. Sign in with it to finish activating your
Advisory account. No new email or password reset is required.</p>
</section>""")
        with st.form("advisory_finish_password_signin", clear_on_submit=True):
            saved_password = st.text_input(
                "Your account password", type="password", max_chars=128,
            )
            finish = st.form_submit_button(
                "Sign in and open my advisory account", type="primary",
            )
        if finish:
            try:
                _password_signin(str(user["email"]).strip().lower(), str(saved_password))
                st.session_state.pop("advisory_password_saved_user_id", None)
                st.session_state.pop("advisory_pending_email", None)
                st.session_state.pop("advisory_recovery_verified", None)
                st.rerun()
            except (RuntimeError, ValueError, TimeoutError, KeyError):
                st.error(
                    "Sign-in could not be completed. Check your existing password "
                    "or use password recovery on the sign-in page."
                )
        if st.button("Choose a different password instead", key="advisory_choose_new_password"):
            st.session_state.pop("advisory_password_saved_user_id", None)
            st.rerun()
        return

    is_recovery = st.session_state.get("advisory_recovery_verified") is True
    if is_recovery:
        st.html("""<section class="advisory-portal-intro">
<h2>Reset your Advisory password.</h2>
<p>Your password-recovery email has been verified. Choose a new password below.
Once saved, sign in to return to your Advisory account.</p>
</section>""")
    else:
        st.html("""<section class="advisory-portal-intro">
<h2>Email confirmed. Set your password.</h2>
<p>Your email has been confirmed. Choose a password to activate your Advisory
account. If you already use a password for the Reader library, you may keep it.
Future visits use your email and password, not an email access link.</p>
</section>""")
    with st.form("advisory_first_password", clear_on_submit=True):
        password = st.text_input(
            "New password" if is_recovery else "New or existing password",
            type="password", max_chars=128,
            help="Use a unique password of at least 12 characters.",
        )
        confirmation = st.text_input(
            "Confirm password", type="password", max_chars=128,
        )
        submit = st.form_submit_button(
            "Reset password and sign in" if is_recovery
            else "Set password and activate my account", type="primary",
        )
    if not submit:
        st.caption("Advisory access remains inactive until password sign-in succeeds.")
        with st.expander("Already have an advisory password?"):
            with st.form("advisory_existing_password"):
                existing_password = st.text_input(
                    "Existing password", type="password", max_chars=128,
                )
                use_existing = st.form_submit_button("Sign in with existing password")
            if use_existing:
                try:
                    _password_signin(str(user["email"]).strip().lower(),
                                     str(existing_password))
                    st.rerun()
                except (RuntimeError, ValueError, TimeoutError, KeyError):
                    st.error("Sign-in failed. Check your password.")
        return
    if password != confirmation:
        st.error("The passwords do not match.")
        return

    try:
        already_current = _complete_advisory_password_setup(session, user, str(password))
    except ValueError as exc:
        st.error(str(exc))
        return
    except AdvisoryPasswordSigninPending:
        # A password can be saved successfully even when subsequent sign-in or
        # Reader profile provisioning encounters an unrelated failure.
        st.session_state["advisory_password_saved_user_id"] = account_id
        st.rerun()
        return
    except (RuntimeError, TimeoutError, KeyError):
        st.error(
            "Supabase could not save the password. Your account was not changed "
            "by this attempt. Please verify your email session or use password "
            "recovery if you already have an account."
        )
        return

    st.session_state.pop("advisory_password_saved_user_id", None)
    st.session_state.pop("advisory_pending_email", None)
    st.session_state.pop("advisory_recovery_verified", None)
    if already_current:
        st.session_state["advisory_activation_message"] = (
            "Your existing password was accepted. Advisory access is ready."
        )
    st.rerun()


def _advisory_login() -> None:
    st.html("""<section class="advisory-portal-intro">
<h2>Bring a specific AI or data leadership decision.</h2>
<p>Register free to submit a decision or challenge for individual review.
I consider a limited number of focused pro-bono discussions where an external
perspective may help. Registration does not guarantee a meeting.
Your account also provides free access to the Executive AI Reader Library.</p>
</section>""")
    returning = st.radio(
        "Advisory account", ["Register free", "Sign in to advisory"],
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
                        _request_password_recovery(address, destination="advisory-access")
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
        st.caption("Review the [Privacy & Data notice](?page=privacy). Registration is free. Pro-bono requests are reviewed individually; a meeting is not guaranteed.")
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
would like to discuss. Registration is free and does not guarantee a pro-bono discussion.</p>
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
            st.success("Your account is ready. You can submit a pro-bono request or use the free reader library.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except (RuntimeError, TimeoutError, KeyError):
            st.error("The account could not be created. Please retry or contact advisory support.")
    st.caption(f"Questions: {ADVISORY_EMAIL} · [Privacy & Data notice](?page=privacy)")


def _advisory_account(session: dict, user: dict, profile: dict) -> None:
    """Verified account shell. Render one section, never every service at once."""
    if profile.get("account_status") != "active":
        st.error("This advisory account is not currently active. Contact advisory support.")
        return
    st.session_state["advisory_member"] = True
    from page_advisory_member_experience import (
        MEMBER_CSS, member_navigation, render_overview, render_requests,
        render_messages, section_heading,
    )
    st.html(MEMBER_CSS)
    view = member_navigation()
    if view == "overview":
        render_overview(session, user, profile)
    elif view == "requests":
        render_requests(session, user, profile)
    elif view == "messages":
        render_messages(session, user)
    elif view == "scorecard":
        section_heading(
            "APPROVED ADVISORY WORKSPACE", "AI Portfolio Prioritization",
            "Compare AI opportunities, examine capacity and record executive decisions."
        )
        from page_advisory_scorecard_workspace import render_private_scorecard
        render_private_scorecard(session, user)
    elif view == "rollout":
        section_heading(
            "EXECUTIVE DECISION SERVICE", "Rollout readiness",
            "Evaluate the conditions for responsible expansion and receive "
            "a focused decision brief."
        )
        from page_advisory_rollout import render_private_rollout
        render_private_rollout(session, user)
    elif view == "account":
        _advisory_account_settings(session, user, profile)
    if view in ("scorecard", "rollout"):
        st.divider()
        if st.button("Return to Advisory overview",
                     key="advisory_return_" + view):
            from page_advisory_member_experience import navigate
            navigate("overview")


def _advisory_account_settings(session: dict, user: dict, profile: dict) -> None:
    """Professional details and credentials live in account settings alone."""
    from page_advisory_member_experience import section_heading
    section_heading(
        "ACCOUNT MANAGEMENT", "Profile and security",
        "Maintain your professional context, password and access to "
        "the included Premium Reader Library."
    )
    profile_tab, security_tab = st.tabs(["Professional profile", "Security & sign-out"])
    with profile_tab:
        st.caption("Only high-level, non-confidential professional context belongs here.")
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
                "Decision or business outcome",
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
            save = st.form_submit_button("Save profile changes", type="primary")
        if save:
            try:
                _update_context(session, user, {
                    "first_name": first, "last_name": last, "organization": organization,
                    "role_title": role, "decision_context": decision,
                    "advisory_focus": focus, "decision_horizon": horizon,
                })
                st.success("Your professional profile has been updated.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except (RuntimeError, TimeoutError):
                st.error("The update could not be saved.")
        from page_advisory_service_feedback import ADVISORY_SERVICE, render_optional_feedback
        render_optional_feedback(
            str(session["access_token"]), str(user["id"]),
            ADVISORY_SERVICE, "registration_access",
        )
    with security_tab:
        st.markdown("#### Password")
        st.caption("Your Advisory and Premium Reader accounts share one Supabase Auth identity.")
        with st.form("advisory_set_password", clear_on_submit=True):
            pwd = st.text_input(
                "New password (12 characters minimum)", type="password", max_chars=128)
            confirm = st.text_input(
                "Confirm new password", type="password", max_chars=128)
            do_change = st.form_submit_button("Change password", type="primary")
        if do_change:
            if pwd != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    _set_reader_password(session, str(pwd))
                    st.success("Password updated for your shared sign-in identity.")
                except (RuntimeError, ValueError, TimeoutError):
                    st.error("The password could not be changed.")
        st.divider()
        st.markdown("#### Session")
        if st.button("Sign out of Advisory and Reader", key="advisory_signout"):
            _sign_out()
    st.divider()
    if st.button("Open my Premium Reader Library", key="advisory_settings_library"):
        _open_library()
    st.caption(f"Privacy requests: {PRIVACY_EMAIL} · Advisory support: {ADVISORY_EMAIL}")


def render_advisory_portal() -> None:
    """Advisory registration, confirmation, password and member views in one site."""
    # Strip one-time tokens before any menu, logo, media or footer renders.
    _consume_query_verification()
    from site_native_shell import native_header, native_footer

    st.html(native_header("advisory-access"))
    st.html(ADVISORY_CSS)

    with st.container(key="native_advisory_content"):
        advisory_notice = st.session_state.pop("advisory_activation_message", None)
        if advisory_notice:
            st.success(str(advisory_notice))
        session, user = _session()
        if session is None or user is None:
            notice = st.session_state.pop("reader_native_flash", None)
            if isinstance(notice, tuple):
                if notice[0] == "error":
                    st.error(str(notice[1]))
                elif notice[0] == "success":
                    st.success(str(notice[1]))
            st.session_state.pop("advisory_member", None)
            _advisory_login()
        elif not _password_authenticated(session):
            # Verified email is identity proof, not permission to use Advisory.
            st.session_state.pop("advisory_member", None)
            _first_password_form(session, user)
        else:
            try:
                profile = _get_advisory_profile(session, user)
            except (RuntimeError, ValueError, TimeoutError):
                st.error("We could not confirm your advisory membership. Please retry.")
            else:
                if not profile:
                    st.session_state.pop("advisory_member", None)
                    _advisory_enroll(session, user)
                else:
                    _advisory_account(session, user, profile)

    st.html(native_footer("advisory-access"))
    # A branded domain hosted via a legacy masked frame may expose a 980px
    # desktop layout viewport to a real phone. The native form, not only the
    # HTML header/footer, must participate in the mobile scale correction.
    from site_embedded_mobile import mount_native_masked_mobile_fix
    mount_native_masked_mobile_fix()
