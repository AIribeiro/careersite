from __future__ import annotations

"""Approved image and A4 PDF download for the AI ROI briefing."""

from html import escape

from briefing_infographic_engine import INFOGRAPHIC_CSS, infographic_html
# The artwork is built once into the public repository as an immutable artifact.
# Keep image bytes out of the Streamlit HTML payload; long inline data URLs
# produced missing images and bloated article rendering on the live site.
ROI_WEBP = (
    "https://raw.githubusercontent.com/AIribeiro/careersite/main/"
    "static/briefing-ai-roi-proof-before-scale.webp"
)

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
    have intermittently failed. The CTA delivers a print-ready, high-resolution A4 PDF.
    """
    alt = str(row.get("alt_text") or "").strip()
    if len(alt) < 40:
        return ""
    # Serve the tested, pre-built image via GitHub's public asset host. Image
    # delivery no longer depends on a Pillow render or huge data URI inside
    # the Streamlit HTML document.
    display = ROI_WEBP
    download = "/~/+/readers/download/" + escape(article.slug, quote=True) + ".pdf"
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
        + '" target="_blank" rel="noopener" data-hq-event="briefing_reader_pdf" '
        + 'aria-label="Download the high-resolution A4 PDF AI ROI executive infographic">'
        + 'Download the infographic (PDF)</a></div>'
        + '</figure></section>'
    )
