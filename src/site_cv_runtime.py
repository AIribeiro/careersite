from __future__ import annotations

"""Production delivery binding for the canonical repository-backed CV.

The PDF is generated and validated by GitHub Actions, then committed under
/static. Production must not regenerate or overwrite that file at Streamlit
runtime: Community Cloud guarantees serving repository-backed static files,
while runtime-created files are not guaranteed to persist across sessions.
"""

from pathlib import Path

import site_assets

CV_FILENAME = "Jair_Ribeiro_Enterprise_AI_Data_Leader_CV_2026.pdf"
ROOT = Path(__file__).resolve().parents[1]
CV_PATH = ROOT / "static" / CV_FILENAME

# Streamlit static files must use the app-relative route documented by
# Streamlit: app/static/<filename>. A leading slash can be handled by the
# Community Cloud frontend as an application route and return the Streamlit
# HTML shell with a .pdf filename instead of the PDF bytes.
site_assets.CV_BYTES = CV_PATH.read_bytes()
site_assets.CV_URI = f"app/static/{CV_FILENAME}"
