from pathlib import Path
import base64
import io
import zipfile

ROOT = Path(__file__).resolve().parent
encoded = "".join(p.read_text(encoding="ascii") for p in sorted((ROOT / "payload_parts").glob("part_*.b64")))
with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as bundle:
    source = bundle.read("site.py").decode("utf-8")
    ASSET_BYTES = {Path(name).name: bundle.read(name) for name in bundle.namelist() if name.startswith("assets/")}
exec(compile(source, "site_app.py", "exec"), globals(), globals())
