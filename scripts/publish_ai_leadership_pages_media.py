"""Publish exactly the owner-approved AI leadership media through existing Pages.
No private article content, voice recording, credentials or unapproved assets are copied.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

SLUG = "before-you-hire-your-next-ai-engineer-who-is-leading-your-enterprise-ai"
EP = "20261127-10971877f74e"
STAGING = "cb4aace4cb3ca5bde60a488b4d3f50e473ee8fe3"
REL = f"public-media/thinking-articles/{SLUG}/{EP}"
BASE = "https://airibeiro.github.io/careersite/" + REL + "/"
MANIFEST = Path("static/article-videos") / SLUG / "manifest.json"
ASSETS = {
    "video": ("web-10971877f74e.mp4", 3942344, "10971877f74e3b2c2cba722ef260fb1b62e2c4ea3c2c568313e7ed03fbfac549", "video/mp4"),
    "poster": ("poster-24d721d86696.png", 77643, "24d721d86696326b380cc11cb7e1d271089cba7b595cd8b65e4a1e522f33458b", "image/png"),
}
def validate(data, size, digest):
    assert len(data) == size, (len(data), size)
    assert hashlib.sha256(data).hexdigest() == digest, "SHA256 mismatch"

def build():
    subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", STAGING], check=True)
    def part(name):
        return subprocess.check_output(["git", "show", STAGING + ":approved-media/" + name])
    data = {"video": b"".join(part(f"part{i:02d}") for i in range(11)), "poster": part("poster.png")}
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
    assert m["content_sha256"] == "d859abb2c596467055c6d92e89218d4ecbf24807d38cd1d186fc1700bc57cf36"
    assert m["title_sha256"] == "95f66c0c3e7a42169a977da3acab0961b1a7c47eac98ae274ef1fb559bc19a17"
    assert m["subtitle_sha256"] == "e0a8fdbd42ffecf01968b32e659b771d4a759bec601e8a07e61d02ad68cfbcd1"
    assert m["excerpt_sha256"] == "a1e1ff6d578973983c8b82f33d7246510d998c33ae8c23342960ed5ad76d680e"
    assert m["published_at"] == "2026-11-27T11:22:27.485762+00:00"
    assert m["script_sha256"] == "8c22b8ab4e38fc407b19073bf73457dc08ba691658210624ad9412127291e74e"
    for kind, (_, size, digest, mime) in ASSETS.items():
        assert m[kind]["sha256"] == digest and m[kind]["bytes"] == size
        m[kind]["url"] = checks[kind]["url"]
    m["state"] = "published_verified"
    m["media_verified"] = True
    m["media_verification"] = checks
    m["release_note"] = "Owner-approved exact web master and poster; public GitHub Pages delivery independently checked for full SHA-256, MIME, length and video byte ranges. Article content and reader access unchanged."
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Verified manifest ready for commit", flush=True)

if __name__ == "__main__":
    if sys.argv[1:] == ["build"]:
        build()
    elif sys.argv[1:] == ["activate"]:
        activate()
    else:
        raise SystemExit("usage: build|activate")
