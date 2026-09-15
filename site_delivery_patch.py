from __future__ import annotations

"""Final public delivery override for the downloadable CV only.

Photography is validated and mapped by site_photo_patch. Keeping that concern in
one place prevents a later runtime layer from replacing the selected conference
photos with a different image or an on-the-fly crop.
"""

from pathlib import Path

import site_assets as assets

ROOT = Path(__file__).resolve().parent

CV_FILENAME = "Jair_Ribeiro_Senior_AI_Data_Leader_CV_2026.pdf"
CV_PATH = ROOT / "static" / CV_FILENAME
CV_PUBLIC_URL = (
    "https://raw.githubusercontent.com/AIribeiro/careersite/main/static/"
    + CV_FILENAME
)

try:
    cv_bytes = CV_PATH.read_bytes()
    if cv_bytes.startswith(b"%PDF") and len(cv_bytes) > 4000:
        assets.CV_BYTES = cv_bytes
except OSError:
    pass

assets.CV_URI = CV_PUBLIC_URL
