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
BASE_URL = "https://jairribeiro.com"  # Branded public address for staging back-links.


READER_SHELL_CSS = r"""
<style>
/* Reader membership: an editorial experience within the shared portfolio. */
[data-testid="stAppViewContainer"] {background:#f3f0e9!important}
[data-testid="stHeader"],[data-testid="stToolbar"] {display:none!important}
[data-testid="stMainBlockContainer"],.block-container {
  width:100%!important;max-width:none!important;padding:0!important
}
[data-testid="stVerticalBlock"] {gap:0!important}
.reader-shell .reader-hero {
  padding:62px 0 72px;overflow:hidden;
  background:linear-gradient(132deg,#11283d 0%,#192d42 60%,#26394b 100%)
}
.reader-shell .reader-hero-grid {
  display:grid;grid-template-columns:minmax(0,1.16fr) minmax(275px,.84fr);
  gap:clamp(34px,5vw,75px);align-items:center
}
.reader-shell .reader-hero-main {min-width:0}
.reader-shell .reader-crumb {
  display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:0 0 28px;
  color:#e3b38f;font:750 11px/1.55 Arial,sans-serif;letter-spacing:.035em
}
.reader-shell .reader-crumb a {text-decoration:none;color:#e3b38f!important}
.reader-shell .reader-crumb a:hover{text-decoration:underline;text-underline-offset:3px}
.reader-shell .reader-hero-kicker {
  display:block;margin:0 0 13px;color:#eab990;
  font:800 10px/1.5 Arial,sans-serif;letter-spacing:.17em;text-transform:uppercase
}
.reader-shell .reader-hero h1 {
  max-width:730px;margin:0;color:#fff;
  font:500 clamp(40px,5.2vw,68px)/1.07 Georgia,serif;
  letter-spacing:-.038em;text-wrap:balance
}
.reader-shell .reader-hero p.reader-intro {
  max-width:630px;margin:22px 0 0;color:#e0e4e8;
  font:400 clamp(15px,1.35vw,17px)/1.75 Arial,sans-serif
}
.reader-shell .reader-hero-support {
  margin-top:22px!important;color:#b8c9d7!important;
  font:500 12px/1.65 Arial,sans-serif!important
}
.reader-shell .reader-hero-actions {
  display:flex;align-items:center;flex-wrap:wrap;gap:14px 22px;margin-top:24px
}
.reader-shell .reader-hero-join {
  display:inline-flex;align-items:center;justify-content:center;
  min-height:46px;padding:12px 20px;
  background:#e9bc99;color:#172d40!important;
  font:800 13px/1.4 Arial,sans-serif;text-decoration:none!important
}
.reader-shell .reader-hero-join:hover {background:#f5d0b2}
.reader-shell .reader-hero-link {
  display:inline-flex;align-items:center;gap:8px;
  padding-bottom:4px;border-bottom:1px solid rgba(234,185,144,.6);
  color:#f2bf9c!important;text-decoration:none!important;
  font:750 12px/1.5 Arial,sans-serif
}
.reader-shell .reader-hero-link:hover {
  color:#fff!important;border-color:#fff
}
.reader-shell .reader-hero-benefits {
  min-width:0;padding:4px 0 4px 32px;border-left:1px solid rgba(245,235,223,.24)
}
.reader-shell .reader-benefits-label {
  display:block;margin-bottom:12px;color:#eab990;
  font:800 10px/1.5 Arial,sans-serif;letter-spacing:.17em;text-transform:uppercase
}
.reader-shell .reader-benefit {
  display:grid;grid-template-columns:24px minmax(0,1fr);gap:13px;
  padding:16px 0 18px;border-bottom:1px solid rgba(255,255,255,.15)
}
.reader-shell .reader-benefit:last-child {border-bottom:0;padding-bottom:5px}
.reader-shell .reader-benefit-index {
  color:#d5a881;font:700 11px/1.6 Arial,sans-serif
}
.reader-shell .reader-benefit strong {
  display:block;margin:0 0 5px;color:#fff;
  font:500 clamp(17px,1.7vw,21px)/1.25 Georgia,serif
}
.reader-shell .reader-benefit p {
  margin:0!important;max-width:34ch;color:#bdc9d4!important;
  font:400 12px/1.65 Arial,sans-serif!important
}
/* The Streamlit form is a continuation of the editorial page, not an app
   dashboard nested inside a second card. All inputs retain native semantics. */
.st-key-reader_flow {
  position:relative;z-index:1;
  width:min(900px,calc(100% - 44px));max-width:900px!important;
  margin:-29px auto 76px!important;padding:38px clamp(24px,4.2vw,52px) 37px!important;
  border:1px solid #ddd4c7;border-top:3px solid #aa7654;
  border-radius:0!important;background:#fffdf9;
  box-shadow:0 19px 49px rgba(15,30,45,.09);color:#192c3e
}
.st-key-reader_flow [data-testid="stVerticalBlock"]{gap:12px!important}
.st-key-reader_flow .reader-join-heading {
  max-width:730px;padding-bottom:17px;border-bottom:1px solid #e5dfd5;
  margin-bottom:5px
}
.st-key-reader_flow .reader-join-eyebrow {
  display:block;margin-bottom:10px;color:#975e3d;
  font:800 10px/1.4 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase
}
.st-key-reader_flow .reader-join-heading h2 {
  margin:0 0 11px;color:#1c3143;
  font:500 clamp(32px,3.8vw,43px)/1.14 Georgia,serif;
  letter-spacing:-.025em
}
.st-key-reader_flow .reader-join-heading p {
  max-width:660px;margin:0;color:#485565;
  font:400 15px/1.72 Arial,sans-serif
}
.st-key-reader_flow h3 {
  font:500 clamp(28px,3vw,36px)/1.2 Georgia,serif!important;
  letter-spacing:-.018em!important;color:#1b3041!important
}
.st-key-reader_flow p,.st-key-reader_flow label {
  color:#475563;line-height:1.65
}
.st-key-reader_flow [data-testid="stRadio"] {
  margin:4px 0;padding:10px 14px;border:1px solid #e1d9cf;background:#f7f3ed
}
.st-key-reader_flow [data-testid="stRadio"] label {color:#273746!important}
.st-key-reader_flow [data-testid="stForm"] {
  border:0!important;border-radius:0!important;background:transparent!important;
  padding:13px 0 0!important
}
.st-key-reader_flow [data-testid="stWidgetLabel"] p {
  font-size:13px!important;font-weight:750!important;color:#24374a!important
}
.st-key-reader_flow [data-testid="stTextInput"] input {
  min-height:48px;background:#fff!important;border:1px solid #cfc6ba!important;
  color:#1b2936!important;border-radius:2px!important
}
.st-key-reader_flow [data-testid="stTextInput"] input:focus {
  border-color:#946346!important;box-shadow:0 0 0 2px rgba(148,99,70,.14)!important
}
.st-key-reader_flow [data-testid="stFormSubmitButton"] {width:100%}
.st-key-reader_flow [data-testid="stFormSubmitButton"] button[kind="primary"],
.st-key-reader_flow [data-testid="stButton"] button[kind="primary"],
.st-key-reader_flow [data-testid="stDownloadButton"] button[kind="primary"] {
  background:#19364c!important;border:1px solid #19364c!important;
  color:#fff!important;font-weight:750!important;border-radius:2px!important;
  min-height:49px
}
.st-key-reader_flow [data-testid="stFormSubmitButton"] button[kind="primary"] {
  width:100%!important;font-size:14px!important;letter-spacing:.005em
}
.st-key-reader_flow [data-testid="stFormSubmitButton"] button:hover,
.st-key-reader_flow [data-testid="stDownloadButton"] button:hover {
  filter:brightness(1.14)
}
.st-key-reader_flow [data-testid="stCaptionContainer"] p {
  color:#596676!important;font-size:12px!important;line-height:1.65!important
}
.st-key-reader_flow [data-testid="stDivider"]{margin:12px 0!important}
.st-key-reader_flow [data-testid="stAlert"]{border-radius:2px!important}
.st-key-reader_flow [data-testid="stSelectbox"]{max-width:100%}
.st-key-reader_flow .reader-publication-link {margin:3px 0 19px}
.st-key-reader_flow .reader-publication-link a {
  display:inline-flex;min-height:41px;align-items:center;
  color:#854a2a!important;font-size:12px;font-weight:800;
  text-decoration:none!important;border-bottom:1px solid rgba(184,97,52,.45)
}
.st-key-reader_flow .reader-publication-link a:hover {
  color:#b86134!important;border-bottom-color:#b86134
}
.reader-shell-footer footer.footer {display:block!important}
.reader-shell-footer {width:100%}
.reader-shell-footer .reader-account-help {
  text-align:center;background:#f1ece4;color:#384a57;
  padding:17px 20px;font:500 13px/1.65 Arial,sans-serif
}
.reader-shell-footer .reader-account-help a {
  color:#a65d39!important;text-decoration:underline;font-weight:750
}
@media(max-width:900px) {
  .reader-shell .reader-hero-grid {grid-template-columns:minmax(0,1fr);gap:29px}
  .reader-shell .reader-hero-benefits {
    padding:18px 0 0;border-left:0;border-top:1px solid rgba(245,235,223,.24)
  }
  .reader-shell .reader-hero-benefits .reader-benefits-list {
    display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px
  }
  .reader-shell .reader-benefit {
    grid-template-columns:1fr;gap:5px;padding:10px 0;border-bottom:0
  }
}
@media(max-width:650px) {
  .reader-shell .reader-hero {padding:37px 0 55px}
  .reader-shell .reader-hero h1 {font-size:clamp(37px,9vw,47px)}
  .reader-shell .reader-crumb {margin-bottom:23px}
  .reader-shell .reader-hero-actions {align-items:flex-start;flex-direction:column;gap:11px}
  .reader-shell .reader-hero-benefits .reader-benefits-list {
    grid-template-columns:minmax(0,1fr);gap:0
  }
  .reader-shell .reader-benefit {
    grid-template-columns:23px minmax(0,1fr);gap:10px;
    border-bottom:1px solid rgba(255,255,255,.14);padding:13px 0
  }
  .reader-shell .reader-benefit:last-child {border-bottom:0}
  .st-key-reader_flow {
    width:calc(100% - 28px)!important;margin:-18px auto 42px!important;
    padding:26px 20px 30px!important
  }
  .st-key-reader_flow [data-testid="stRadio"] {padding:10px 11px}
  .st-key-reader_flow [data-testid="stForm"]{padding:7px 0 0!important}
}
@media(prefers-reduced-motion:reduce) {
  .reader-shell .reader-hero-link {transition:none}
}
</style>
"""


def _portfolio_link(page: str, *, staging: bool) -> str:
    if staging:
        return BASE_URL.rstrip("/") + "/?page=" + page
    return "?page=" + page


def reader_header(*, staging: bool = False) -> str:
    """Portfolio-native executive library front door; account-aware copy."""
    import streamlit as st

    top = nav("thinking")
    if staging:
        # Staging only hosts the reader page. Back-links go to the real portfolio.
        top = top.replace('href="?page=', 'href="' + BASE_URL.rstrip("/") + '/?page=')
    thinking = _portfolio_link("thinking", staging=staging)
    briefings = _portfolio_link("briefings", staging=staging)
    is_member = isinstance(st.session_state.get("reader_native_session"), dict)

    if is_member:
        headline = "Your reading, in one place."
        intro = (
            "Return to complete Executive AI Briefings, current Premium Articles "
            "and Weekly AI. Your saved editions, PDF history and reader profile "
            "are available below."
        )
        context = "YOUR PERSONAL READING SPACE"
        benefit_heading = "EXPLORE YOUR LIBRARY"
        benefits = (
            ("01", "Complete briefings", "Read the full executive perspectives and the decisions they examine."),
            ("02", "Current analysis", "Return to Premium Articles and the latest Weekly AI edition."),
            ("03", "Your collection", "Revisit saved briefings and downloadable infographics, where available."),
        )
    else:
        headline = "A clearer view of the AI decisions that matter."
        intro = (
            "An independent reading library for executives accountable for AI "
            "investment, governance and adoption. Explore the business choices, "
            "trade-offs and operating conditions behind meaningful results."
        )
        context = "PREMIUM READER LIBRARY · JAIR RIBEIRO"
        benefit_heading = "WHAT YOU CAN WORK WITH"
        benefits = (
            ("01", "Decision-focused briefings",
             "Complete executive perspectives on the decisions, risks and trade-offs leaders must own."),
            ("02", "Deeper editorial analysis",
             "Premium Articles and the latest Weekly AI perspective, beyond the public summaries."),
            ("03", "Original decision visuals",
             "Downloadable A4 briefing infographics, where available, to support discussion and review."),
        )

    from html import escape
    benefits_markup = "".join(
        '<div class="reader-benefit"><span class="reader-benefit-index">'
        + escape(number) + '</span><div><strong>' + escape(title)
        + '</strong><p>' + escape(detail) + '</p></div></div>'
        for number, title, detail in benefits
    )
    return (
        CSS + IMAGE_CSS + READER_SHELL_CSS
        + '<div class="site reader-shell">' + top
        + '<main><section class="pagehero reader-hero"><div class="container">'
        + '<div class="reader-crumb" aria-label="Breadcrumb">'
        + f'<a href="{thinking}" target="_self">Thinking</a>'
        + '<span aria-hidden="true">/</span>'
        + f'<a href="{briefings}" target="_self">Executive AI Briefings</a>'
        + '<span aria-hidden="true">/</span><span>Reader library</span></div>'
        + '<div class="reader-hero-grid">'
        + '<div class="reader-hero-main">'
        + '<span class="reader-hero-kicker">' + escape(context) + '</span>'
        + '<h1>' + escape(headline) + '</h1>'
        + '<p class="reader-intro">' + escape(intro) + '</p>'
        + ('<p class="reader-hero-support">Grounded in enterprise AI and Data '
           'leadership, governance and adoption experience.</p>' if not is_member else '')
        + '<div class="reader-hero-actions">'
        + '<a class="reader-hero-join" href="#reader-access">'
        + ('Open my library' if is_member else 'Get Premium Reader access')
        + ' <span aria-hidden="true">→</span></a>'
        + f'<a class="reader-hero-link" href="{briefings}" target="_self">'
        + 'Preview the Executive AI Briefings <span aria-hidden="true">→</span></a>'
        + '</div></div><aside class="reader-hero-benefits" aria-label="Library benefits">'
        + '<span class="reader-benefits-label">' + escape(benefit_heading) + '</span>'
        + '<div class="reader-benefits-list">' + benefits_markup + '</div>'
        + '</aside></div></div></section></main></div>'
    )


def reader_footer() -> str:
    support = (
        '<div class="reader-account-help" role="note">'
        'Need help with your reader account or available downloads? '
        '<a href="mailto:info@jairribeiro.com">info@jairribeiro.com</a>'
        '</div>'
    )
    return '<div class="site reader-shell-footer">' + support + footer() + '</div>'
