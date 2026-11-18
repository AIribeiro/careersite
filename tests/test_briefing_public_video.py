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
    assert "/briefing-preview-video/" in html
    assert "briefing-preview-video-title" in html


def test_video_not_exposed_on_other_editions_or_unknown_files():
    assert render_briefing_video_preview("unrelated-briefing") == ""
    assert public_preview_media_path(BRIEFING_VIDEO_SLUG, "../preview.mp4") is None
    assert public_preview_media_path("unrelated-briefing", "preview.mp4") is None
