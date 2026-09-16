from __future__ import annotations

"""Production delivery binding for the canonical repository-backed CV.

The PDF is generated and validated by GitHub Actions, then committed under
/static. Production must not regenerate or overwrite that file at Streamlit
runtime: Community Cloud guarantees serving repository-backed static files,
while runtime-created files are not guaranteed to persist across sessions.
"""

from pathlib import Path

import site_assets

CV_FILENAME = "Jair_Ribeiro_Senior_AI_Data_Leader_CV_2026.pdf"
ROOT = Path(__file__).resolve().parents[1]
CV_PATH = ROOT / "static" / CV_FILENAME

# Keep shared components aligned with the exact repository-backed artifact.
site_assets.CV_BYTES = CV_PATH.read_bytes()
site_assets.CV_URI = f"/app/static/{CV_FILENAME}"
