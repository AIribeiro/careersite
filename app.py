from pathlib import Path
import base64
import io
import zipfile

ROOT = Path(__file__).resolve().parent
encoded = "".join(p.read_text(encoding="ascii") for p in sorted((ROOT / "payload_parts").glob("part_*.b64")))

with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
    source = bundle.read("site.py").decode("utf-8")
    ASSET_BYTES = {
        Path(name).name: bundle.read(name)
        for name in bundle.namelist()
        if name.startswith("assets/")
    }

# Override the legacy embedded photographs with the repository's full-size
# asset bundle. Keeping the high-resolution media separate from the legacy
# payload prevents the older compressed images from being rendered on large
# or retina displays.
hq_media = ROOT / "hq_media.zip"
if hq_media.exists():
    with zipfile.ZipFile(hq_media) as media:
        for name in media.namelist():
            if not name.endswith("/"):
                ASSET_BYTES[Path(name).name] = media.read(name)

# Use the Learn AI portrait supplied by Jair as both the browser/page icon and
# the visible site identity mark in the persistent navigation.
if "site-icon.png" in ASSET_BYTES:
    source = source.replace(
        'page_icon="🧭"',
        'page_icon=io.BytesIO(ASSET_BYTES["site-icon.png"])',
        1,
    )
    source = source.replace(
        'def nav(page: str) -> None:\n    links = []',
        'def nav(page: str) -> None:\n    brand_icon = image_data_uri("site-icon.png")\n    links = []',
        1,
    )
    source = source.replace(
        '<span class="brand-mark">JR</span><span class="brand-name">Jair Ribeiro</span>',
        '<img class="brand-mark-image" src="{brand_icon}" alt="Jair Ribeiro"/><span class="brand-name">Jair Ribeiro</span>',
        1,
    )
    source = source.replace(
        '.brand-name { font-weight:700; font-size:14px; white-space:nowrap; }',
        '.brand-mark-image { width:36px; height:36px; object-fit:cover; border-radius:50%; border:1px solid rgba(255,255,255,.35); display:block; }\n.brand-name { font-weight:700; font-size:14px; white-space:nowrap; }',
        1,
    )

# The Impact19 collage is source-limited (197×200), so it is deliberately
# displayed as a compact editorial accent rather than stretched across a wide
# hero area. That preserves visual quality while placing it where it supports
# the Expertise narrative.
if "impact19-header.png" in ASSET_BYTES:
    impact_uri = "data:image/png;base64," + base64.b64encode(ASSET_BYTES["impact19-header.png"]).decode("ascii")
    expertise_intro = '<p class="body-lg muted" style="max-width:820px;margin-top:24px;">My strongest work sits between strategy and delivery — where technical choices, business value, governance and organizational behavior have to work at the same time.</p>'
    expertise_feature = expertise_intro + f'''\n              <div class="expertise-feature">\n                <img src="{impact_uri}" alt="Jair Ribeiro speaking at an industry event"/>\n                <div><span>In the room</span><strong>Turning complex AI questions into conversations leaders can act on.</strong></div>\n              </div>'''
    source = source.replace(expertise_intro, expertise_feature, 1)
    source = source.replace(
        '.expertise-top { background:var(--white); }',
        '.expertise-top { background:var(--white); }\n.expertise-feature { margin:34px 0 10px; display:flex; align-items:center; gap:22px; max-width:760px; padding:16px; border:1px solid var(--line); background:var(--paper); }\n.expertise-feature img { width:190px; height:190px; object-fit:cover; flex:0 0 auto; }\n.expertise-feature span { display:block; margin-bottom:8px; font-size:11px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); }\n.expertise-feature strong { display:block; max-width:420px; font:500 24px/1.25 Georgia,serif; }\n@media (max-width:620px) { .expertise-feature { align-items:flex-start; } .expertise-feature img { width:112px; height:112px; } .expertise-feature strong { font-size:19px; } }',
        1,
    )

# Keep the dedicated Blog renderer introduced in the previous fix.
BLOG_BRANCH = """elif page == "blog":
    from blog_page import render_blog
    render_blog(footer)
"""

blog_start = source.find('elif page == "blog":')
contact_start = source.find('elif page == "contact":')
if blog_start == -1 or contact_start == -1 or contact_start <= blog_start:
    raise RuntimeError("Unable to locate the Blog page in the embedded site source.")
source = source[:blog_start] + BLOG_BRANCH + "\n" + source[contact_start:]

exec(compile(source, "site_app.py", "exec"), globals(), globals())
