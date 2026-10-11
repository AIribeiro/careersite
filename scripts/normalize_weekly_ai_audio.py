#!/usr/bin/env python3
"""Normalize WEEKLY AI recordings to widely supported MPEG-1 Layer III audio.

Some neural speech services return 24 kHz MPEG-2 Layer III. Although valid MP3,
a 44.1 kHz MPEG-1 output has wider mobile browser compatibility. This runs
only in the publishing workflow, not for each visitor.
"""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "static" / "weekly-ai"


@lru_cache(maxsize=1)
def ffmpeg_binary() -> str:
    """Use the wheel's bundled executable on minimal GitHub runners."""
    try:
        import imageio_ffmpeg
    except ImportError:
        system_ffmpeg = shutil.which("ffmpeg")
        if not system_ffmpeg:
            raise RuntimeError(
                "Audio normalization needs imageio-ffmpeg (bundled binary) "
                "or an installed ffmpeg executable."
            )
        return system_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _probe(path: Path) -> dict:
    """Read audio stream metadata with ffmpeg; ffprobe is not installed on all runners.

    The command intentionally specifies no output. ffmpeg prints stream details
    to stderr and exits nonzero; that is expected for metadata inspection.
    """
    result = subprocess.run(
        [ffmpeg_binary(), "-hide_banner", "-i", str(path)],
        capture_output=True, text=True, check=False,
    )
    match = re.search(
        r"Audio:\s*([a-z0-9_]+)(?:\s*\([^)]*\))?,\s*(\d+) Hz,\s*(mono|stereo)",
        result.stderr, flags=re.I,
    )
    if match is None:
        raise ValueError(f"Could not read MP3 metadata for {path.name}: {result.stderr[-250:]}")
    codec, rate, layout = match.groups()
    return {
        "codec_name": codec.lower(),
        "sample_rate": rate,
        "channels": 1 if layout.lower() == "mono" else 2,
    }


def normalize_audio(path: Path) -> bool:
    """Avoid re-encoding already normalized files; replace atomically."""
    if path.suffix != ".mp3" or not path.is_file() or path.stat().st_size < 1024:
        return False
    meta = _probe(path)
    if meta.get("codec_name") != "mp3":
        raise ValueError(f"Unexpected audio codec: {path.name}")
    if int(meta.get("sample_rate") or 0) == 44100 and int(meta.get("channels") or 0) == 1:
        print("Already mobile-compatible:", path.name)
        return False
    temp = path.with_name(path.stem + ".normalized.mp3")
    temp.unlink(missing_ok=True)
    try:
        subprocess.run(
            [ffmpeg_binary(), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(path), "-vn", "-ac", "1", "-ar", "44100",
             "-c:a", "libmp3lame", "-b:a", "96k", str(temp)],
            check=True,
        )
        normalized = _probe(temp)
        if (normalized.get("codec_name") != "mp3"
                or int(normalized.get("sample_rate") or 0) != 44100
                or int(normalized.get("channels") or 0) != 1
                or temp.stat().st_size < 4000):
            raise ValueError(f"Normalization failed for {path.name}")
        temp.replace(path)
        print("Normalized audio for mobile:", path.name, path.stat().st_size)
        return True
    finally:
        temp.unlink(missing_ok=True)


def main() -> int:
    if not AUDIO_DIR.is_dir():
        print("No weekly audio files available")
        return 0
    changed = 0
    for path in sorted(AUDIO_DIR.glob("weekly-ai-*.mp3")):
        changed += int(normalize_audio(path))
    print("Normalized:", changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
