from __future__ import annotations

"""Final delivery override for the downloadable CV.

Keep the website-aligned PDF produced by site_cv_patch, but restore the original
in-page download behaviour. A data URI respects the existing HTML download
attribute and avoids sending visitors to a raw GitHub PDF page.
"""

import base64

import site_assets as assets

if getattr(assets, "CV_BYTES", b""):
    assets.CV_URI = (
        "data:application/pdf;base64,"
        + base64.b64encode(assets.CV_BYTES).decode("ascii")
    )
