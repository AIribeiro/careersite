"""Shared portfolio shell for the native Streamlit reader experience.

This page keeps the genuine Streamlit forms and file download controls, but
reuses the portfolio's actual navigation, footer, typography and color system.
Staging navigation points back to the public portfolio because its standalone
launcher renders only the reader flow, regardless of ?page.
"""
from __future__ import annotations

from site_components import footer, nav
from site_image_styles import IMAGE_CSS
from site_styles import CSS
from thinking_articles import BASE_URL


READER_SHELL_CSS = r"""
<style>
/* Reader-only overrides: never change shared portfolio page styles. */
[data-testid="stAppViewContainer"] { background:#f4f0e8!important; }
[data-testid="stHeader"],[data-testid="stToolbar"] { display:none!important; }
[data-testid="stMainBlockContainer"],.block-container {
  width:100%!important;max-width:none!important;padding:0!important;
}
[data-testid="stVerticalBlock"] {gap:0!important}
.reader-shell .reader-hero {padding:64px 0 67px;overflow:hidden;}
.reader-shell .reader-hero h1 {
  max-width:1030px;font:500 clamp(43px,6vw,72px)/1.04 Georgia,serif;
  letter-spacing:-.034em;margin:0;
}
.reader-shell .reader-hero p.reader-intro {
  max-width:760px;margin:19px 0 0;font-size:clamp(15px,1.6vw,19px);
  line-height:1.68;color:#c9d1dd;
}
.reader-shell .reader-crumb {
  display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 19px;
  color:#e5ae86;font-size:11px;font-weight:750;letter-spacing:.04em;
}
.reader-shell .reader-crumb a {text-decoration:none;color:#f0c19f!important}
.reader-shell .reader-crumb a:hover {text-decoration:underline}
.reader-shell .reader-hero-cta {display:flex;gap:12px;flex-wrap:wrap;margin-top:25px}
.reader-shell .reader-hero-cta a {
  border:1px solid rgba(255,255,255,.32);padding:11px 17px;
  color:#fff!important;text-decoration:none!important;font-size:12px;font-weight:800
}
.reader-shell .reader-hero-cta a:hover {background:rgba(255,255,255,.1)}
/* These native Streamlit elements are the interactive part of the same site. */
.st-key-reader_flow {
  width:min(980px,calc(100% - 44px));max-width:980px!important;
  margin:48px auto 74px!important;padding:39px 45px 42px!important;
  border:1px solid rgba(17,21,27,.14);
  background:#fffdf8;
  box-shadow:0 18px 55px rgba(11,18,32,.055);
  color:#11151b;
}
.st-key-reader_flow [data-testid="stVerticalBlock"] {gap:12px!important}
.st-key-reader_flow h3 {
  font:500 clamp(27px,3vw,37px)/1.18 Georgia,serif!important;
  letter-spacing:-.017em!important;color:#0b1220!important;
}
.st-key-reader_flow p, .st-key-reader_flow label {
  color:#49525d;line-height:1.65;
}
.st-key-reader_flow [data-testid="stForm"] {
  border:1px solid #ded6cc!important;border-radius:0!important;
  background:#fbf9f5!important;padding:22px!important;
}
.st-key-reader_flow [data-testid="stWidgetLabel"] p {
  font-size:13px!important;font-weight:750;color:#293241!important;
}
.st-key-reader_flow [data-testid="stTextInput"] input {
  min-height:46px;background:#fff!important;border-color:#d2c9be!important;
  color:#11151b!important;border-radius:0!important;
}
.st-key-reader_flow [data-testid="stFormSubmitButton"] button[kind="primary"],
.st-key-reader_flow [data-testid="stButton"] button[kind="primary"],
.st-key-reader_flow [data-testid="stDownloadButton"] button[kind="primary"] {
  background:#b86134!important;border:1px solid #b86134!important;
  color:#fff!important;font-weight:800!important;border-radius:0!important;
  min-height:46px;
}
.st-key-reader_flow [data-testid="stFormSubmitButton"] button:hover,
.st-key-reader_flow [data-testid="stDownloadButton"] button:hover {
  filter:brightness(.94);
}
.st-key-reader_flow [data-testid="stDivider"] {margin:13px 0!important}
.st-key-reader_flow [data-testid="stAlert"] {border-radius:0!important}
.st-key-reader_flow [data-testid="stSelectbox"] {max-width:100%}
.st-key-reader_flow .reader-publication-link {margin:3px 0 19px}
.st-key-reader_flow .reader-publication-link a {
  display:inline-flex;min-height:41px;align-items:center;
  color:#854a2a!important;font-size:12px;font-weight:800;
  text-decoration:none!important;border-bottom:1px solid rgba(184,97,52,.45);
}
.st-key-reader_flow .reader-publication-link a:hover {
  color:#b86134!important;border-bottom-color:#b86134;
}
/* Shared site stylesheet hides the native Streamlit footer. Re-show the real
   portfolio HTML footer, exactly as rendered on all other portfolio pages. */
.reader-shell-footer footer.footer {display:block!important;}
.reader-shell-footer {width:100%;}
.reader-shell-footer .reader-account-help {
 text-align:center;background:#f1ece4;color:#384a57;
 padding:17px 20px;font:500 13px/1.65 Arial,sans-serif;
}
.reader-shell-footer .reader-account-help a {
 color:#a65d39!important;text-decoration:underline;font-weight:750;
}
@media(max-width:700px) {
  .reader-shell .reader-hero {padding:48px 0 52px}
  .reader-shell .reader-hero h1 {font-size:clamp(38px,10vw,55px)}
  .st-key-reader_flow {
    width:calc(100% - 28px)!important;margin:24px auto 44px!important;
    padding:23px 17px 30px!important;
  }
  .st-key-reader_flow [data-testid="stForm"] {padding:15px!important}
  .reader-shell .reader-hero-cta a {width:100%;text-align:center}
}
</style>
"""


def _portfolio_link(page: str, *, staging: bool) -> str:
    if staging:
        return BASE_URL.rstrip("/") + "/?page=" + page
    return "?page=" + page


def reader_header(*, staging: bool = False) -> str:
    """Render real global navigation plus a matching editorial page hero."""
    top = nav("thinking")
    if staging:
        # The test launcher has no general page dispatcher. Navigation must
        # reach the published website rather than appear to be a broken menu.
        top = top.replace('href="?page=', 'href="' + BASE_URL.rstrip("/") + '/?page=')
    thinking = _portfolio_link("thinking", staging=staging)
    briefings = _portfolio_link("briefings", staging=staging)
    return (
        CSS + IMAGE_CSS + READER_SHELL_CSS
        + '<div class="site reader-shell">' + top
        + '<main><section class="pagehero reader-hero"><div class="container">'
        + '<div class="reader-crumb" aria-label="Breadcrumb">'
        + f'<a href="{thinking}" target="_self">Thinking</a>'
        + '<span aria-hidden="true">/</span>'
        + f'<a href="{briefings}" target="_self">Executive AI Briefings</a>'
        + '<span aria-hidden="true">/</span><span>Reader library</span></div>'
        + '<h1>Your complete briefing library.</h1>'
        + '<p class="reader-intro">Each edition begins with a useful public preview. '
        + 'Your free verified reader account opens the complete analysis, '
        + 'executive decision frameworks and original infographic PDFs.</p>'
        + '<div class="reader-hero-cta">'
        + f'<a href="{briefings}" target="_self">Explore all briefings</a>'
        + f'<a href="{thinking}" target="_self">Back to Thinking</a>'
        + '</div></div></section></main></div>'
    )


def reader_footer() -> str:
    support = (
        '<div class="reader-account-help" role="note">'
        'Need help with your account or briefing downloads? '
        '<a href="mailto:info@jairribeiro.com">info@jairribeiro.com</a>'
        '</div>'
    )
    return '<div class="site reader-shell-footer">' + support + footer() + '</div>'
