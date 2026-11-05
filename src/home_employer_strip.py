from __future__ import annotations

from html import escape


# Employment history, not client endorsements or a partnership claim.
# External original logos remain separate lightweight assets rather than
# increasing the size of the Streamlit page HTML with embedded base64 images.
EMPLOYERS = (
    ("MSX International", "https://www.msxi.com/", "https://www.onetrust.com/content/dam/onetrust/brand/content/graphic/thumbnail/customer/OT-customer-logo-MSX-international.png", "msx"),
    ("Volvo Group", "https://www.volvogroup.com/", "https://commons.wikimedia.org/wiki/Special:FilePath/Volvo_logo.svg", "volvo"),
    ("Kimberly-Clark", "https://www.kimberly-clark.com/", "https://commons.wikimedia.org/wiki/Special:FilePath/Kimberly-Clark_logo.svg", "kimberly"),
    ("IBM", "https://www.ibm.com/", "https://commons.wikimedia.org/wiki/Special:FilePath/IBM_logo.svg", "ibm"),
    ("Hewlett Packard Enterprise", "https://www.hpe.com/", "https://commons.wikimedia.org/wiki/Special:FilePath/Hewlett_Packard_Enterprise_logo_2025_expanded.svg", "hpe"),
)

_STYLE = """
<style>
.site .career-employers{
  background:#ffffff;
  border-top:1px solid #d8c9b9;
  border-bottom:1px solid #dacbb9;
  color:#172238;
}
.site .career-employers .container{padding:18px 0 16px}
.site .career-employers-head{text-align:center;margin:0 auto 13px;max-width:820px}
.site .career-employers-head .eyebrow{margin:0 0 5px;color:#a75d40;font-size:10px}
.site .career-employers-head h2{
  margin:0;font:500 clamp(20px,2.2vw,28px)/1.15 Georgia,serif;
  letter-spacing:-.025em;
}
.site .career-employers-head p:last-child{
  color:#66717f;font-size:11px;line-height:1.45;margin:6px 0 0
}
.site .career-employers-grid{
  display:grid;grid-template-columns:repeat(5,minmax(0,1fr));
  gap:0;list-style:none;margin:0;padding:0;
}
.site .career-employers-grid li{min-width:0;border-left:1px solid rgba(38,50,65,.16)}
.site .career-employers-grid li:first-child{border-left:0}
.site .career-employer{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  min-width:0;min-height:84px;gap:7px;padding:4px 10px;
  text-decoration:none!important;color:#243148!important;
  transition:background .16s ease;
}
.site .career-employer:hover,.site .career-employer:focus-visible{background:rgba(184,97,52,.065)}
.site .career-employer:focus-visible{outline:2px solid #b86134;outline-offset:-2px}
.site .career-employer-logo{
  display:flex;align-items:center;justify-content:center;
  height:40px;width:100%;min-width:0
}
.site .career-employer-logo img{
  display:block;width:auto;max-width:100%;height:auto;max-height:40px;
  object-fit:contain
}
.site .career-employer--msx .career-employer-logo{gap:0}
.site .career-employer--msx .career-employer-logo img{max-width:142px;max-height:39px}
.site .career-employer--volvo .career-employer-logo img{max-width:128px;max-height:32px}
.site .career-employer--kimberly .career-employer-logo img{max-width:151px;max-height:31px}
.site .career-employer--ibm .career-employer-logo img{max-width:82px;max-height:36px}
.site .career-employer--hpe .career-employer-logo img{max-width:158px;max-height:40px}
.site .career-employer-name{
  font-size:10px;line-height:1.25;font-weight:720;text-align:center;
  color:#344052
}
@media(max-width:760px){
  .site .career-employers .container{padding:16px 0 14px}
  .site .career-employers-head{margin-bottom:12px}
  .site .career-employers-grid{grid-template-columns:repeat(3,minmax(0,1fr));row-gap:8px}
  .site .career-employers-grid li:nth-child(4){border-left:0}
  .site .career-employer{min-height:76px;padding:4px 7px;gap:6px}
}
@media(max-width:440px){
  .site .career-employers-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .site .career-employers-grid li:nth-child(odd){border-left:0}
  .site .career-employers-grid li:nth-child(even){border-left:1px solid rgba(38,50,65,.16)}
}
@media(prefers-reduced-motion:reduce){
  .site .career-employer{transition:none}
}
</style>
"""


def home_employer_strip() -> str:
    cards = []
    for name, url, image_url, logo_kind in EMPLOYERS:
        image = (
            f'<img src="{escape(image_url, quote=True)}" alt="" '
            'loading="lazy" decoding="async">'
        )
        cards.append(
            '<li>'
            f'<a class="career-employer career-employer--{logo_kind}" '
            f'href="{escape(url, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer" aria-label="{escape(name, quote=True)} — official website">'
            f'<span class="career-employer-logo">{image}</span>'
            f'<span class="career-employer-name">{escape(name)}</span>'
            '</a></li>'
        )
    return (
        _STYLE
        + '<section class="career-employers" aria-labelledby="career-employers-title" '
        'data-analytics-section="home-employer-history"><div class="container">'
        '<div class="career-employers-head">'
        '<p class="eyebrow">Professional background</p>'
        '<h2 id="career-employers-title">A career shaped by global enterprises.</h2>'
        '<p>Career experience across global enterprises in technology, AI and Data leadership.</p>'
        '</div><ul class="career-employers-grid">'
        + "".join(cards)
        + '</ul></div></section>'
    )
