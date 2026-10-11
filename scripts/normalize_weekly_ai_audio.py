#!/usr/bin/env python3
"""Normalize WEEKLY AI recordings to widely supported MPEG-1 Layer III audio.

Some neural speech services return 24 kHz MPEG-2 Layer III. Although valid MP3,
a 44.1 kHz MPEG-1 output has wider mobile browser compatibility. This runs
only in the publishing workflow, not for each visitor.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "static" / "weekly-ai"


def _probe(path: Path) -> dict:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_name,sample_rate,channels",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    streams = json.loads(p.stdout).get("streams") or []
    if len(streams) != 1:
        raise ValueError(f"Expected one audio stream: {path.name}")
    return streams[0]


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
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
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
