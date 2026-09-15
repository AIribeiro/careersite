from pathlib import Path
import base64
import io
import zipfile

ROOT = Path(__file__).resolve().parent
encoded = "".join(p.read_text(encoding="ascii") for p in sorted((ROOT / "payload_parts").glob("part_*.b64")))
with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
    source = bundle.read("site.py").decode("utf-8")
    ASSET_BYTES = {Path(name).name: bundle.read(name) for name in bundle.namelist() if name.startswith("assets/")}

# Featured thought-leadership article. Kept here so new blog links can be
# published without repacking the embedded visual/site bundle.
_blog_anchor = '''              <div class="beliefs">\n                <article class="belief"><span class="num">01</span><p>“A portfolio with twenty pilots and no stopping rules is not an AI strategy.”</p></article>'''
_featured_article = '''              <div style="margin:44px 0 54px;padding:32px;border:1px solid rgba(16,19,26,.14);background:#fffdf9;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:center;">\n                <div>\n                  <p class="kicker" style="margin-bottom:10px;">Latest article</p>\n                  <h3 style="font-family:Georgia,serif;font-size:clamp(28px,3vw,42px);font-weight:500;line-height:1.12;margin:0 0 12px;">Latest thought leadership</h3>\n                  <p style="font-size:17px;line-height:1.65;color:#505653;margin:0;">A new article extending the themes behind this site: practical judgment, responsible AI adoption, enterprise value and the human work behind scale.</p>\n                </div>\n                <a class="btn btn-dark" href="https://lnkd.in/eFNiAX8M" target="_blank" rel="noopener noreferrer">Read the article ↗</a>\n              </div>\n              <div class="beliefs">\n                <article class="belief"><span class="num">01</span><p>“A portfolio with twenty pilots and no stopping rules is not an AI strategy.”</p></article>'''
if _blog_anchor in source:
    source = source.replace(_blog_anchor, _featured_article, 1)

exec(compile(source, "site_app.py", "exec"), globals(), globals())
