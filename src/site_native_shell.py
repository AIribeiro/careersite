"""Shared site chrome for native Streamlit pages.

Public editorial pages already include site_components.nav/footer in their HTML.
Native Streamlit pages must use the same components without resetting the
native widget layout or carrying authentication secrets into links.
"""
from __future__ import annotations

from html import escape
import re

from site_components import footer, nav

NATIVE_SHELL_CSS = r"""
<style>
/* Shared identity and footer for form-driven Streamlit pages. */
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stStatusWidget"], [data-testid="stDecoration"],
[data-testid="stFooter"], #MainMenu {display:none!important}
[data-testid="stMainBlockContainer"], .block-container {
  width:100%!important;max-width:none!important;padding:0!important
}
[data-testid="stAppViewContainer"] {background:#f4f0e8!important}
.site.native-shell, .site.native-shell * {box-sizing:border-box}
.site.native-shell {font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#182c41}
.site.native-shell a {color:inherit}
.site.native-shell .container {width:min(1180px,calc(100% - 44px));margin:0 auto}
.site.native-shell .nav {position:relative;z-index:100;background:rgba(11,18,32,.98);
 color:#fff;border-bottom:1px solid rgba(255,255,255,.1)}
.site.native-shell .navin {width:min(1240px,calc(100% - 34px));
 min-height:68px;margin:auto;display:flex;align-items:center;
 justify-content:space-between;gap:20px}
.site.native-shell .brand {display:flex;gap:11px;align-items:center;text-decoration:none!important}
.site.native-shell .brand img {width:38px;height:38px;border-radius:50%;
 object-fit:cover;border:1px solid rgba(255,255,255,.35)}
.site.native-shell .brand strong {display:block;font-size:14px;color:#fff}
.site.native-shell .brand span {display:block;margin-top:3px;color:#9aa6b7;
 font-size:9px;letter-spacing:.08em;text-transform:uppercase}
.site.native-shell .links {display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}
.site.native-shell .link {padding:9px 10px;color:#c9d0da!important;
 text-decoration:none!important;font-size:12px;font-weight:700}
.site.native-shell .link:hover,.site.native-shell .link.on {
 color:#fff!important;background:rgba(255,255,255,.08)
}
.site.native-shell .contactlink {border:1px solid rgba(255,255,255,.28)}
.site.native-shell .native-hero {
 padding:clamp(44px,6vw,76px) 0 clamp(44px,5vw,65px);
 background:linear-gradient(130deg,#0b1729 0%,#15283e 65%,#20364b 100%);
 color:#f8f7f2
}
.site.native-shell .native-hero--compact {padding:36px 0 39px}
.site.native-shell .native-crumb {display:flex;gap:12px;flex-wrap:wrap;
 align-items:center;margin:0 0 24px;color:#e7b48e;
 font-size:11px;font-weight:750;letter-spacing:.02em}
.site.native-shell .native-crumb a {color:#e7b48e!important;
 text-underline-offset:4px;text-decoration:none}
.site.native-shell .native-crumb a:hover {text-decoration:underline}
.site.native-shell .native-crumb .current {color:#f3f1ed}
.site.native-shell .native-hero .eyebrow {
 display:block;color:#e5af83;font-size:10px;font-weight:800;
 letter-spacing:.17em;text-transform:uppercase;margin:0 0 15px
}
.site.native-shell .native-hero h1 {
 font:500 clamp(39px,5.5vw,66px)/1.08 Georgia,serif;
 letter-spacing:-.036em;margin:0;max-width:900px;text-wrap:balance
}
.site.native-shell .native-hero--compact h1 {font-size:clamp(33px,4.4vw,52px)}
.site.native-shell .native-hero .lede {
 max-width:780px;color:#cbd5df;font-size:clamp(14px,1.45vw,17px);
 line-height:1.72;margin:18px 0 0
}
.site.native-shell .native-hero .included {
 display:inline-flex;gap:9px;flex-wrap:wrap;margin:25px 0 0;
 color:#f0c3a2;font-size:12px;font-weight:750;line-height:1.6
}
.site.native-shell .native-hero .included a {
 color:#f0c3a2!important;text-underline-offset:4px
}
.site.native-shell .native-support {
 width:min(1180px,calc(100% - 44px));margin:0 auto;
 border-top:1px solid #ddd4c8;padding:20px 0 25px;
 color:#54657a;font-size:12px;line-height:1.6
}
.site.native-shell .native-support a {color:#915538!important;font-weight:700}
.site.native-shell .footer {display:block!important;padding:45px 0 33px;
 background:#080d16;color:#95a1b0}
.site.native-shell .footertop {display:grid;grid-template-columns:1fr auto;gap:35px}
.site.native-shell .footer strong {color:#fff;font:500 24px/1.2 Georgia,serif}
.site.native-shell .footer p {max-width:650px;font-size:12px;line-height:1.6}
.site.native-shell .footerlinks {display:flex;gap:15px;flex-wrap:wrap;
 justify-content:flex-end}
.site.native-shell .footer a {color:#c6ced8!important;text-decoration:none;
 font-size:11px;font-weight:700}
.site.native-shell .footer a:hover {color:#fff!important;text-decoration:underline}
.site.native-shell .copy {margin-top:27px;color:#637081;font-size:10px}
.st-key-native_advisory_content {
 width:min(1040px,calc(100% - 44px));margin:0 auto;
 padding:38px 0 65px
}
.st-key-native_analytics_content {
 width:min(1340px,calc(100% - 44px));margin:0 auto;
 padding:38px 0 65px
}
.st-key-native_advisory_content [data-testid="stForm"] {
 max-width:1040px
}
@media(max-width:800px) {
 .site.native-shell .footertop {grid-template-columns:1fr}
 .site.native-shell .footerlinks {justify-content:flex-start}
 .site.native-shell .navin {align-items:flex-start;gap:12px;
  flex-direction:column;padding:12px 0}
 .site.native-shell .links {justify-content:flex-start;width:100%;gap:2px}
}
@media(max-width:620px) {
 .site.native-shell .container {width:calc(100% - 30px)}
 .site.native-shell .navin {width:calc(100% - 24px)}
 .site.native-shell .brand span {display:none}
 .site.native-shell .link {padding:8px 7px;font-size:11px}
 .site.native-shell .native-hero {padding:40px 0 45px}
 .site.native-shell .native-hero--compact {padding:28px 0 34px}
 .site.native-shell .native-crumb {gap:8px;margin-bottom:18px}
 .site.native-shell .native-support {width:calc(100% - 30px)}
 .st-key-native_advisory_content,.st-key-native_analytics_content {
  width:calc(100% - 30px);padding:25px 0 45px
 }
}
</style>
"""


def _inert_links(markup: str) -> str:
    """Keep the site menu visible during CMS editing without clickable routes."""
    def replace_tag(match: re.Match[str]) -> str:
        attrs = re.sub(
            r'\s+(?:href|target|rel|download|data-hq-event)="[^"]*"',
            "", match.group(1),
        )
        return ('<span' + attrs + ' aria-disabled="true"'
                ' title="Finish editing before navigating">')
    return re.sub(r'<a\b([^>]*)>', replace_tag, markup).replace('</a>', '</span>')


def native_header(page: str, *, navigation_locked: bool = False) -> str:
    """Render the real site menu and a contextual editorial header."""
    if page == "advisory-access":
        active = "advisory-access"
        title = "Your executive advisory space."
        kicker = "JAIR RIBEIRO / PRIVATE EXECUTIVE ADVISORY"
        introduction = (
            "A direct relationship for the business decisions behind enterprise AI "
            "and Data. Register, verify your email and set your password, or return "
            "to your existing advisory account."
        )
        trail = (
            ('?page=home', 'Home'),
            ('?page=advisory', 'Executive Advisory'),
            ('', 'Your advisory account'),
        )
        included = (
            '<a href="?page=readers" target="_self">Complete Premium Reader library included</a>'
        )
        compact = ""
    elif page == "analytics":
        active = "analytics"
        title = "Portfolio intelligence."
        kicker = "JAIR RIBEIRO / PORTFOLIO"
        introduction = (
            "Content readership, engagement and publication intelligence, "
            "with private workspaces available only to the authorized owner."
        )
        trail = (
            ('?page=home', 'Home'),
            ('', 'Portfolio intelligence'),
        )
        included = ""
        compact = " native-hero--compact"
    else:
        raise ValueError("Unknown native portfolio page")

    crumbs = []
    for target, label in trail:
        if target:
            crumbs.append('<a href="' + target + '" target="_self">'
                          + escape(label) + '</a>')
        else:
            crumbs.append('<span class="current" aria-current="page">'
                          + escape(label) + '</span>')
    trail_html = '<span aria-hidden="true">/</span>'.join(crumbs)
    if navigation_locked:
        trail_html = _inert_links(trail_html)
        included = _inert_links(included)
    top_menu = nav(active)
    if navigation_locked:
        top_menu = _inert_links(top_menu)
    return (
        NATIVE_SHELL_CSS
        + '<div class="site native-shell native-shell-header">'
        + top_menu
        + '<header class="native-hero' + compact + '">'
        + '<div class="container"><nav class="native-crumb" aria-label="Breadcrumb">'
        + trail_html + '</nav>'
        + '<span class="eyebrow">' + escape(kicker) + '</span>'
        + '<h1>' + escape(title) + '</h1>'
        + '<p class="lede">' + escape(introduction) + '</p>'
        + ('<p class="included">' + included + '</p>' if included else '')
        + '</div></header></div>'
    )


def native_footer(page: str, *, navigation_locked: bool = False) -> str:
    """Real portfolio footer plus contextual support, never credentials."""
    if page == "advisory-access":
        from site_assets import ADVISORY_EMAIL, PRIVACY_EMAIL
        note = (
            'Need help with your advisory account? '
            f'<a href="mailto:{ADVISORY_EMAIL}">{ADVISORY_EMAIL}</a> · '
            f'<a href="mailto:{PRIVACY_EMAIL}">Privacy contact</a> · '
            '<a href="?page=privacy" target="_self">Privacy &amp; data</a>'
        )
    elif page == "analytics":
        note = (
            '<a href="?page=home" target="_self">Return to portfolio</a> · '
            '<a href="?page=privacy" target="_self">Privacy &amp; data</a>'
        )
    else:
        raise ValueError("Unknown native portfolio page")
    site_footer = footer()
    if navigation_locked:
        note = _inert_links(note)
        site_footer = _inert_links(site_footer)
    return (
        '<div class="site native-shell native-shell-footer">'
        + '<div class="native-support" role="note">' + note + '</div>'
        + site_footer + '</div>'
    )
