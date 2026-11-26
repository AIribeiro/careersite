"""Publish exactly the owner-approved AI literacy media through existing Pages.
No private article content, voice recording, credentials or unapproved assets are copied.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

SLUG = "how-to-build-an-ai-literate-organization"
EP = "20261125-fd1409953395"
STAGING = "023b3896219baad1bd9022cb45e0e0076183187d"
REL = f"public-media/thinking-articles/{SLUG}/{EP}"
BASE = "https://airibeiro.github.io/careersite/" + REL + "/"
MANIFEST = Path("static/article-videos") / SLUG / "manifest.json"
ASSETS = {
    "video": ("web-fd1409953395.mp4", 4447995, "fd1409953395b04fcdd1aaa72811057b37e43157e6cd60530ace4e8d4ae1bd97", "video/mp4"),
    "poster": ("poster-a5d06a73832f.png", 89783, "a5d06a73832f015c314ee95a326cedba38627d783675acb1d7d8a10fa87d3a76", "image/png"),
}
def validate(data, size, digest):
    assert len(data) == size, (len(data), size)
    assert hashlib.sha256(data).hexdigest() == digest, "SHA256 mismatch"

def build():
    subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", STAGING], check=True)
    def part(name):
        return subprocess.check_output(["git", "show", STAGING + ":approved-media/" + name])
    data = {"video": b"".join(part(f"part{i:02d}") for i in range(12)), "poster": part("poster.png")}
    dest = Path("_share_site") / REL
    dest.mkdir(parents=True, exist_ok=True)
    for kind, (name, size, digest, mime) in ASSETS.items():
        validate(data[kind], size, digest)
        (dest / name).write_bytes(data[kind])
        print("EXACT APPROVED MEDIA", kind, size, digest, flush=True)

def verify():
    checks = {}
    for kind, (name, size, digest, mime) in ASSETS.items():
        url = BASE + name
        with urlopen(Request(url, method="HEAD"), timeout=40) as response:
            assert response.status == 200 and response.geturl() == url
            assert response.headers.get_content_type() == mime, response.headers.get_content_type()
            assert int(response.headers["Content-Length"]) == size
        with urlopen(url, timeout=60) as response:
            assert response.status == 200 and response.geturl() == url
            data = response.read()
        validate(data, size, digest)
        if kind == "video":
            for start in (0, size // 2, size - 1024):
                end = start + 1023
                req = Request(url, headers={"Range": f"bytes={start}-{end}"})
                with urlopen(req, timeout=40) as response:
                    assert response.status == 206, response.status
                    assert response.headers["Content-Range"] == f"bytes {start}-{end}/{size}"
                    assert response.read() == data[start:end+1]
        checks[kind] = {"url": url, "sha256": digest, "bytes": size, "head": 200, "mime": mime, "range_verified": kind == "video"}
    print(json.dumps(checks, indent=2), flush=True)
    return checks

def activate():
    checks = None
    for attempt in range(5):
        try:
            checks = verify()
            break
        except Exception:
            if attempt == 4:
                raise
            time.sleep(10)
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m["slug"] == SLUG and m["episode_id"] == EP and m["owner_approved"] is True
    assert m["content_sha256"] == "cb2dbb72775ee0c7fd9861c39cc29b4fbfec2d698698f51a3b2ec0ac2ddeb60a"
    for kind, (_, size, digest, mime) in ASSETS.items():
        assert m[kind]["sha256"] == digest and m[kind]["bytes"] == size
        m[kind]["url"] = checks[kind]["url"]
    m["state"] = "published_verified"
    m["media_verified"] = True
    m["media_verification"] = checks
    m["release_note"] = "Owner-approved exact web master and poster; public GitHub Pages delivery independently checked for full SHA-256, MIME, length and video byte ranges. Companion briefing links preserved."
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Verified manifest ready for commit", flush=True)

if __name__ == "__main__":
    if sys.argv[1:] == ["build"]:
        build()
    elif sys.argv[1:] == ["activate"]:
        activate()
    else:
        raise SystemExit("usage: build|activate")
