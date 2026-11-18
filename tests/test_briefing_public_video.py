"""Source-locked public video stays scoped to the correct briefing."""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from briefing_reader_preview_video import (
    BRIEFING_VIDEO_SLUG, MEDIA_SHA256, MEDIA_DIR,
    public_preview_media_path, render_briefing_video_preview,
)


def test_preview_video_assets_exist_and_match_approved_hashes():
    for name, digest in MEDIA_SHA256.items():
        path = public_preview_media_path(BRIEFING_VIDEO_SLUG, name)
        assert path is not None
        assert path.is_file()
        assert path.parent == MEDIA_DIR
        assert len(digest) == 64


def test_preview_player_is_accessible_and_not_autoplaying():
    html = render_briefing_video_preview(BRIEFING_VIDEO_SLUG)
    assert '<video controls playsinline preload="metadata"' in html
    assert "autoplay" not in html.split("<video", 1)[1].split(">", 1)[0]
    assert "aspect-ratio:16/9" in html
    assert "briefing-public-video" in html
    # Streamlit's built-in static path serves H.264/AAC with video/mp4.
    # The custom ASGI route can be intercepted by a framed domain/proxy.
    assert "https://jairribeiro-ai.streamlit.app/app/static/briefing-videos/" in html
    assert "raw.githubusercontent.com/AIribeiro/careersite/main/static/briefing-videos/" in html
    assert 'type="video/mp4"' in html
    assert "/briefing-preview-video/" not in html
    assert "Open video separately" in html
    assert "briefing-preview-video-title" in html


def test_video_not_exposed_on_other_editions_or_unknown_files():
    assert render_briefing_video_preview("unrelated-briefing") == ""
    assert public_preview_media_path(BRIEFING_VIDEO_SLUG, "../preview.mp4") is None
    assert public_preview_media_path("unrelated-briefing", "preview.mp4") is None


def test_video_appears_before_editorial_opening_and_member_access():
    """The explainer must precede the decision, not interrupt the registration CTA."""
    from types import SimpleNamespace
    from briefing_reader_preview import render_public_briefing_preview

    article = SimpleNamespace(
        slug=BRIEFING_VIDEO_SLUG,
        title="Scaling AI Across the Enterprise",
        subtitle="What must change when AI expands beyond the first team?",
        excerpt="A practical executive test for receiving teams.",
        content_html=(
            "<h2>The Leadership Decision</h2>"
            "<p>Approve wider AI deployment only when the receiving business unit "
            "can reproduce the intended outcome under its own operating conditions. "
            "The business owner should verify the complete process before expansion.</p>"
            "<p>Another team may have different records, decisions, capacity, "
            "and exception rates. These differences affect the actual operating "
            "outcome even if the AI model is unchanged.</p>"
        ),
    )
    html = render_public_briefing_preview(article, "18 Nov 2026")
    video_at = html.index('<section class="briefing-preview-video"')
    opening_at = html.index('<div class="briefing-preview-grid">')
    unlock_at = html.index('<section class="briefing-unlock"')
    assert video_at < opening_at < unlock_at
    assert "What leaders need to decide" in html
    assert "From the published edition" not in html
