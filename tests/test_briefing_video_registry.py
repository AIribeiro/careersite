"""Multiple Executive AI Briefing videos must be manifest-approved and byte-perfect."""
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from briefing_reader_preview_video import (
    BRIEFING_VIDEO_SLUG, MEDIA_ROOT, public_preview_media_path,
    render_briefing_video_preview,
)

AGENT_SLUG = "when-an-ai-agent-stops-who-finishes-the-work"

def test_both_approved_manifests_match_uploaded_binaries():
    for slug in (BRIEFING_VIDEO_SLUG, AGENT_SLUG):
        manifest = json.loads((MEDIA_ROOT / slug / "video-manifest.json").read_text())
        assert manifest["slug"] == slug
        assert manifest["status"] == "approved" and manifest["approved_by_owner"] is True
        for name in ("preview.mp4", "poster.jpg"):
            part = "web" if name == "preview.mp4" else "poster"
            media = public_preview_media_path(slug, name)
            assert media is not None, f"Upload the exact approved media for {slug}/{name}"
            assert hashlib.sha256(media.read_bytes()).hexdigest() == manifest[part]["sha256"]

def test_new_video_player_is_accessible_and_shows_canonical_duration():
    html = render_briefing_video_preview(AGENT_SLUG)
    assert html.count('<section class="briefing-preview-video"') == 1
    assert "Watch the executive explainer · 1 min 41 sec" in html
    assert 'controls playsinline preload="metadata"' in html
    assert 'autoplay' not in html.split("<video", 1)[1].split(">", 1)[0]
    assert "when-an-ai-agent-stops-who-finishes-the-work" in html
    assert "Scaling AI Across" not in html
    assert "Captions included" in html
    assert "Open video separately" in html

def test_unknown_slug_and_path_traversal_fail_closed():
    assert render_briefing_video_preview("not-a-published-video") == ""
    assert render_briefing_video_preview(AGENT_SLUG, source_fingerprint="0"*64) == ""
    assert render_briefing_video_preview("../etc") == ""
    assert public_preview_media_path(AGENT_SLUG, "../preview.mp4") is None
    assert public_preview_media_path(AGENT_SLUG, "video-manifest.json") is None

def test_new_video_precedes_editorial_opening_without_unlock_bypass():
    from briefing_reader_preview import render_public_briefing_preview
    article = SimpleNamespace(
        slug=AGENT_SLUG, title="When an AI Agent Stops, Who Finishes the Work?",
        subtitle="AI agent operational governance", excerpt="Executive briefing",
        content_html=(
            "<h2>The Leadership Decision</h2>"
            "<p>Before giving an AI agent permission to act across business systems, "
            "decide who will account for the work when its run ends. The owner must "
            "verify the outcome and prevent unsafe retries if the external state is unknown.</p>"
            "<p>The next operational step is checking the system of record for the "
            "actual change and assigning a business owner who can recover the work.</p>"
        )
    )
    from unittest.mock import patch
    with patch("briefing_reader_preview.briefing_source_fingerprint",
               return_value="ab5355f0dc78cf28a4806c1794db57c1d6814a9fd5a70e5a363204d7ae6117cd"):
        html = render_public_briefing_preview(article, "18 Nov 2026")
    video = html.index('<section class="briefing-preview-video"')
    decision = html.index('<div class="briefing-preview-decision">')
    access = html.index('<section class="briefing-unlock"')
    assert video < decision < access
    assert html.count('<section class="briefing-preview-video"') == 1
    assert '<main class="briefing-preview briefing-preview--wide">' in html
    assert "Free registration" in html

def test_original_video_is_reassembled_byte_exactly_without_actions():
    """The canonical MP4 is reconstructed offline from validated Git chunks."""
    from briefing_reader_preview_video import _approved_manifest, _assemble_verified_video
    import hashlib
    manifest = _approved_manifest(AGENT_SLUG)
    assert manifest and len(manifest["web"]["chunks"]) == 9
    target = MEDIA_ROOT / AGENT_SLUG / "preview.mp4"
    expected_hash = manifest["web"]["sha256"]
    assert _assemble_verified_video(AGENT_SLUG, manifest, target)
    assert target.stat().st_size == manifest["web"]["size_bytes"]
    assert hashlib.sha256(target.read_bytes()).hexdigest() == expected_hash

def test_chunk_tampering_rejected_without_fallback():
    from briefing_reader_preview_video import _approved_manifest
    manifest = _approved_manifest(AGENT_SLUG)
    assert manifest and manifest["web"]["chunks"][0]["sha256"].startswith("bc70a878")


def test_agent_playback_uses_public_mp4_and_poster_not_ephemeral_streamlit_media():
    """P0 regression: both media URLs must work without a Streamlit session."""
    html = render_briefing_video_preview(AGENT_SLUG)
    assert (
        '<source src="https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/'
        'object/public/portfolio-public-videos/executive-briefings/'
        'when-an-ai-agent-stops-who-finishes-the-work/'
        'preview-v1-d0fbd81b.mp4" type="video/mp4">'
    ) in html
    assert (
        'poster="https://raw.githubusercontent.com/AIribeiro/careersite/main/'
        'static/briefing-videos/when-an-ai-agent-stops-who-finishes-the-work/'
        'poster.jpg?v=05968e6939ec"'
    ) in html
    assert "agent-briefing-video-delivery" not in html
    assert (
        'app/static/briefing-videos/'
        'when-an-ai-agent-stops-who-finishes-the-work/preview.mp4'
    ) not in html
