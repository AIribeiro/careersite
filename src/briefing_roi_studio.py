from __future__ import annotations

"""Self-contained approved image and PNG download for the AI ROI briefing."""

from html import escape

from briefing_infographic_engine import INFOGRAPHIC_CSS, infographic_html
from briefing_roi_artwork import artwork_data_uri

ROI_STUDIO_CSS = """<style>
.site .roi-artwork-figure{max-width:900px;margin-inline:auto;background:#fffdf9;padding:clamp(8px,1.4vw,20px);box-shadow:0 14px 38px rgba(19,42,62,.05)}
.site .roi-artwork-figure img{display:block;width:100%;height:auto;aspect-ratio:3/4;max-width:100%;background:#fbfcfe}
.site .roi-artwork-actions{display:flex;justify-content:flex-end;margin-top:12px}
.site .roi-artwork-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:10px 17px;color:#0b3553!important;text-decoration:none!important;border:1px solid #8cafbf;border-radius:6px;font:700 12px/1.4 Arial,sans-serif;transition:background-color .2s}
.site .roi-artwork-actions a:hover{background:#e9f4f7}
.site .roi-artwork-actions a:focus-visible{outline:3px solid #147ba0;outline-offset:3px}
@media(max-width:700px){.site .roi-artwork-figure{padding:8px}.site .roi-artwork-actions a{width:100%}}
</style>"""


def approved_roi_studio(article, row: dict) -> str:
    """Respect CMS approval/fingerprint; draw the original once for this reader.

    Data URIs work inside Streamlit st.html where static /app/static image URLs
    have intermittently failed. The PNG link holds real 1800 x 2400 image bytes.
    """
    alt = str(row.get("alt_text") or "").strip()
    if len(alt) < 40:
        return ""
    try:
        display = artwork_data_uri("display")
        download = artwork_data_uri("download")
    except (OSError, ValueError):
        display = download = ""
    if not display or not download:
        return infographic_html(row["spec"], alt, row.get("caption", ""), article.slug)
    caption = str(row.get("caption") or "").strip() or (
        "Original executive AI ROI infographic by Jair Ribeiro. Financial returns "
        "require a baseline, attribution, realized benefits and complete AI costs."
    )
    return (
        INFOGRAPHIC_CSS + ROI_STUDIO_CSS
        + '<section class="ebi-section roi-artwork" data-analytics-section="briefing-infographic" '
        + 'data-hq-content-slug="' + escape(article.slug, quote=True) + '">'
        + '<figure class="ebi-figure roi-artwork-figure">'
        + '<span class="ebi-kicker">The executive visual · AI ROI evidence chain</span>'
        + '<img src="' + display + '" alt="' + escape(alt, quote=True)
        + '" width="1800" height="2400" loading="eager" decoding="async"/>'
        + '<figcaption>' + escape(caption) + '</figcaption>'
        + '<div class="roi-artwork-actions"><a href="' + download
        + '" download="ai-roi-proof-before-scale-executive-infographic.png" '
        + 'aria-label="Download the full-resolution AI ROI executive infographic as PNG">'
        + 'Download the infographic (PNG)</a></div>'
        + '</figure></section>'
    )
