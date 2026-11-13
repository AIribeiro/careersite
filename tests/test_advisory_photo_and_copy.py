"""Regression checks for Advisory account copy and authentic portrait delivery."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / "images" / "advisory-portrait.webp.b64"
PUBLIC_PAGE = ROOT / "src" / "page_public_services.py"
PORTAL = ROOT / "src" / "page_advisory_portal.py"


def test_advisory_portrait_asset_is_present_and_valid_webp():
    assert PHOTO.is_file(), "Advisory photo is missing from the repository"
    data = base64.b64decode(PHOTO.read_text(encoding="ascii").strip(), validate=True)
    assert len(data) > 6000
    assert data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def test_advisory_page_loads_the_committed_portrait_from_canonical_image_directory():
    source = PUBLIC_PAGE.read_text(encoding="utf-8")
    assert "from site_media import IMAGE_DIR" in source
    assert '"advisory-portrait.webp.b64"' in source
    assert '"data:image/webp;base64," + encoded_photo' in source
    assert '<img src="{photo}"' in source


def test_direct_advisory_account_language_is_consistent():
    page = PUBLIC_PAGE.read_text(encoding="utf-8")
    portal = PORTAL.read_text(encoding="utf-8")
    assert "Create a separate Advisory account" not in page
    assert "Create your advisory account." in page
    assert '>{cta}</a>' in page
    assert "Open my advisory space" in page
    assert "A professional introduction, without the paperwork." in portal
    assert '["Create your advisory account", "Sign in to advisory"]' in portal


def test_advisory_intake_is_collected_upfront_and_carried_into_verified_profile():
    import ast
    portal = PORTAL.read_text(encoding="utf-8")
    reader = (ROOT / "src" / "page_reader_native.py").read_text(encoding="utf-8")
    ast.parse(portal, filename=str(PORTAL))
    ast.parse(reader, filename="src/page_reader_native.py")
    assert 'with st.form("advisory_initial_registration")' in portal
    for field in (
        "First name *", "Last name *", "Job title / role *",
        "Organization *", "Professional email *",
        "What decision, challenge or business outcome brings you here? *",
    ):
        assert field in portal
    assert "Advisory focus (optional)" in portal
    assert "Decision timeframe (optional)" in portal
    assert "def _validate_intake" in portal
    assert "def _signup_context" in portal
    assert "advisory_intake_v1" in reader
    assert 'advisory_intake={**details, "privacy_notice_ack": True}' in portal
    assert "def _register_advisory" in portal
    assert "payload={" in portal
    assert "def _update_context" in portal


def test_advisory_signin_stays_simple_and_reader_permissions_remain_distinct():
    portal = PORTAL.read_text(encoding="utf-8")
    assert 'with st.form("advisory_password_recovery")' in portal
    assert '_request_password_recovery(address, destination="advisory-access")' in portal
    assert 'with st.form("advisory_password_signin"' in portal
    assert 'if not EMAIL.fullmatch(address)' in portal
    assert 'if not user.get("email_confirmed_at")' in portal
    assert '"POST", _rest_url("portfolio_advisory_profiles")' in portal
    assert "advisory_signup_intake" in portal
    assert 'st.query_params["page"] = "readers"' in portal
    assert "Registration does not subscribe you to editorial emails." in portal
