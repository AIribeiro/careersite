#!/usr/bin/env python3
"""Idempotent Weekly AI audio publication for GitHub Actions.

Google Cloud TTS is preferred when GOOGLE_TTS_SERVICE_ACCOUNT_JSON is set.
Otherwise use the free edge-tts neural voice, clearly identified in the build log.
Runs AFTER the portfolio's weekly article publishing task. Generates once per
edition and commits an MP3 plus the exact narration transcript.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import sys
from urllib import parse, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from weekly_ai_audio import AUDIO_DIR, prepare_spoken_script, valid_slug  # noqa: E402

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://rnqweoxtynelfirffmlr.supabase.co").rstrip("/")
PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
VOICE_GOOGLE = os.getenv("GOOGLE_TTS_VOICE", "en-US-Neural2-D")
VOICE_FREE = os.getenv("EDGE_TTS_VOICE", "en-US-AndrewNeural")


def published_briefings() -> list[dict]:
    if not PUBLISHABLE_KEY:
        raise RuntimeError("A public Supabase publishable key is needed for published-article reads")
    query = parse.urlencode({
        "select": "slug,content_html,kind,category,status,published_at",
        "status": "eq.published",
        "kind": "eq.Weekly Brief",
        "category": "eq.Weekly AI",
        "order": "published_at.desc",
        "limit": "80",
    })
    headers = {"apikey": PUBLISHABLE_KEY, "Accept": "application/json"}
    req = request.Request(SUPABASE_URL + "/rest/v1/careersite_articles?" + query, headers=headers)
    with request.urlopen(req, timeout=30) as response:
        records = json.loads(response.read().decode("utf-8"))
    if not isinstance(records, list):
        raise RuntimeError("Unexpected CMS response")
    return [item for item in records if valid_slug(str(item.get("slug") or ""))]


def _issue_week(slug: str) -> tuple[int, int]:
    from datetime import date, timedelta
    published = date.fromisoformat(slug.removeprefix("weekly-ai-"))
    covered = published - timedelta(days=1) if published.weekday() == 0 else published
    iso = covered.isocalendar()
    return iso.week, iso.year


def _google_audio(text: str) -> bytes:
    import google.auth.transport.requests
    from google.oauth2 import service_account
    credentials_json = json.loads(os.environ["GOOGLE_TTS_SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    body = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": "en-US", "name": VOICE_GOOGLE},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.03},
    }).encode("utf-8")
    req = request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        data=body, method="POST",
        headers={
            "Authorization": "Bearer " + credentials.token,
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return base64.b64decode(payload["audioContent"])


async def _edge_audio(text: str, filename: Path) -> None:
    import edge_tts
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, VOICE_FREE, rate="+3%").save(str(filename))
            return
        except Exception:
            filename.unlink(missing_ok=True)
            if attempt == 2:
                raise
            await asyncio.sleep(2 * (attempt + 1))


def publish(article: dict, *, dry_run: bool) -> bool:
    slug = str(article["slug"])
    dest = AUDIO_DIR / (slug + ".mp3")
    transcript = AUDIO_DIR / (slug + ".txt")
    if dest.exists() and dest.stat().st_size > 1024:
        print("Audio already exists:", slug)
        return False
    week, year = _issue_week(slug)
    script = prepare_spoken_script(slug, str(article.get("content_html") or ""), week=week, iso_year=year)
    if not 95 <= len(script.split()) <= 260:
        raise ValueError("Narration length outside safe spoken brief range: " + slug)
    print("Preparing", slug, "with", len(script.split()), "words")
    if dry_run:
        print(script)
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(".tmp.mp3")
    temp.unlink(missing_ok=True)
    try:
        if os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON", "").strip():
            print("Using Google Cloud Text-to-Speech:", VOICE_GOOGLE)
            temp.write_bytes(_google_audio(script))
        else:
            print("Using free edge-tts neural voice:", VOICE_FREE)
            asyncio.run(_edge_audio(script, temp))
        payload = temp.read_bytes()
        valid_frame = len(payload) >= 2 and payload[0] == 0xFF and (payload[1] & 0xE0) == 0xE0
        if len(payload) < 4000 or not (payload.startswith(b"ID3") or valid_frame):
            raise RuntimeError("Synthesizer returned an invalid or empty MP3")
        temp.replace(dest)
        transcript.write_text(script + "\n", encoding="utf-8")
    finally:
        temp.unlink(missing_ok=True)
    print("Published", dest, len(payload), "bytes")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    editions = published_briefings()
    if not editions:
        print("No published weekly articles; nothing to produce")
        return 0
    # Each weekly edition has one stable file. Reruns never regenerate existing audio.
    added = 0
    for article in editions:
        if publish(article, dry_run=args.dry_run):
            added += 1
    print("Generated", added, "new audio editions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
