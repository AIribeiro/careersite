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

BLOG_BRANCH = """elif page == \"blog\":
    from blog_page import render_blog
    render_blog(footer)
"""

blog_start = source.find('elif page == "blog":')
contact_start = source.find('elif page == "contact":')

if blog_start == -1 or contact_start == -1 or contact_start <= blog_start:
    raise RuntimeError("Unable to locate the Blog page in the embedded site source.")

source = source[:blog_start] + BLOG_BRANCH + "\n" + source[contact_start:]

exec(compile(source, "site_app.py", "exec"), globals(), globals())
