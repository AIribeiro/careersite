"""Public Executive AI Briefing previews and free-member access invitations.

All preview HTML is assembled from the actual editorial text and escaped.
No full CMS article HTML or full infographic markup goes into the anonymous
Streamlit document. This is a UX access gate, not DRM: publication assets and
the underlying public CMS API may remain reachable outside the site UI.
"""
from __future__ import annotations

from html import escape, unescape
from html.parser import HTMLParser
import re

from site_components import footer, nav
from thinking_core import THINKING_CSS


PREVIEW_CSS = r"""<style>
.site .briefing-preview-hero {background:radial-gradient(ellipse at 92% 14%,rgba(63,91,109,.34),transparent 43%),#0d2031;color:#fff;padding:clamp(58px,7vw,94px) 0 clamp(58px,6vw,80px)}
.site .briefing-preview-hero .container {max-width:1050px}
.site .briefing-preview-hero .briefing-preview-back {font:750 11px/1.4 Arial,sans-serif;color:#e9c19f!important;text-decoration:none!important}
.site .briefing-preview-hero .briefing-preview-back:hover {text-decoration:underline!important}
.site .briefing-preview-index {display:block;margin-top:29px;font:850 10px/1.6 Arial,sans-serif;letter-spacing:.17em;text-transform:uppercase;color:#d4a77f}
.site .briefing-preview-hero h1 {max-width:950px;font:400 clamp(40px,5.8vw,70px)/1.08 Georgia,serif;letter-spacing:-.037em;margin:15px 0 0;color:#fff}
.site .briefing-preview-hero .briefing-preview-deck {max-width:800px;font:400 clamp(16px,1.9vw,21px)/1.65 Arial,sans-serif;color:#cbd5de;margin:22px 0 0}
.site .briefing-preview-hero .briefing-preview-meta {border-top:1px solid rgba(255,255,255,.14);padding-top:20px;margin-top:32px;color:#b6a9a0;font:700 11px/1.5 Arial,sans-serif}
.site .briefing-preview-body {background:#f7f4ee;padding:clamp(48px,5vw,78px) 0 88px}
.site .briefing-preview-body .container{max-width:1050px}
.site .briefing-preview-grid {display:grid;grid-template-columns:minmax(0,1.35fr) minmax(240px,.65fr);gap:clamp(25px,5vw,70px);align-items:start}
.site .briefing-preview-copy {max-width:745px}
.site .briefing-preview-copy .eyebrow{font-size:10px;color:#b86134}
.site .briefing-preview-copy h2{font:400 clamp(30px,3.6vw,43px)/1.17 Georgia,serif;letter-spacing:-.025em;margin:13px 0 23px;color:#142c3f}
.site .briefing-preview-copy p {font:400 clamp(15px,1.45vw,17px)/1.82 Arial,sans-serif;color:#344653;margin:0 0 21px}
.site .briefing-preview-copy p:last-child{margin-bottom:0}
.site .briefing-preview-decision{margin:0 0 31px;padding:0 0 28px;border-bottom:1px solid #d6d1c8}
.site .briefing-preview-decision h2{font:400 clamp(31px,3.8vw,45px)/1.12 Georgia,serif;color:#173348;margin:11px 0 23px}
.site .briefing-preview-move{margin:4px 0 34px;padding:24px 28px 25px;border-left:3px solid #b86134;background:#eee6dc}
.site .briefing-preview-move p{margin-bottom:0!important;font-weight:550}
.site .briefing-preview-small-head{display:block;margin:0 0 12px;color:#a55e39;font:850 10px/1.5 Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase}
.site .briefing-preview-context{padding-bottom:10px}
.site .briefing-preview-aside {background:#e7e0d4;padding:27px 25px;border-top:3px solid #b86134}
.site .briefing-preview-aside strong {display:block;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#a05c36}
.site .briefing-preview-aside p {font:400 13px/1.7 Arial,sans-serif;color:#455460;margin:13px 0 0}
.site .briefing-unlock {margin-top:clamp(45px,6vw,82px);background:#112c40;color:#fff;padding:clamp(30px,4vw,50px);border:1px solid rgba(221,163,120,.5);box-shadow:0 20px 55px rgba(14,30,45,.12)}
.site .briefing-unlock-inner {display:grid;grid-template-columns:minmax(0,1.2fr) minmax(240px,.8fr);gap:36px;align-items:center}
.site .briefing-unlock .eyebrow {color:#edc29d!important}
.site .briefing-unlock h2 {color:#fff;font:400 clamp(31px,3.7vw,48px)/1.12 Georgia,serif;letter-spacing:-.03em;margin:12px 0 16px}
.site .briefing-unlock p {max-width:635px;color:#c7d2db;font:400 15px/1.7 Arial,sans-serif;margin:0}
.site .briefing-unlock-benefits {display:grid;gap:12px;margin:0;padding:0;list-style:none}
.site .briefing-unlock-benefits li {display:flex;gap:11px;font:750 13px/1.55 Arial,sans-serif;color:#e6edf0;align-items:start}
.site .briefing-unlock-benefits li:before {content:"✓";color:#f0bf96;font-size:15px}
.site .briefing-unlock-actions {display:flex;flex-wrap:wrap;align-items:center;gap:15px 25px;margin-top:29px}
.site .briefing-unlock-primary {display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:13px 22px;background:#e8b78e;color:#102536!important;text-decoration:none!important;font:850 12px/1.35 Arial,sans-serif}
.site .briefing-unlock-primary:hover {background:#f6d9bd}
.site .briefing-unlock-secondary {display:inline-flex;align-items:center;min-height:44px;border-bottom:1px solid #d1a786;color:#fff!important;text-decoration:none!important;font:750 12px/1.35 Arial,sans-serif}
.site .briefing-unlock-note {color:#b5c5cf!important;margin-top:18px!important;font-size:11px!important}
@media(max-width:810px) {
 .site .briefing-preview-grid,.site .briefing-unlock-inner{grid-template-columns:minmax(0,1fr)}
 .site .briefing-preview-aside{max-width:none}
}
@media(max-width:600px) {
 .site .briefing-preview-hero {padding:43px 0 51px}
 .site .briefing-preview-body {padding:40px 0 55px}
 .site .briefing-unlock {padding:27px 22px}
 .site .briefing-unlock-primary,.site .briefing-unlock-secondary {width:100%;justify-content:center}
}
</style>"""


_SKIP = frozenset({
    "figure", "figcaption", "svg", "style", "script", "noscript", "table",
    "aside", "nav", "footer", "details", "form", "button",
})


class _EditorialOpening(HTMLParser):
    """Extract genuine editorial paragraphs, not artwork or hidden controls."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.skip: list[str] = []
        self.active = False
        self.fragments: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _SKIP:
            self.skip.append(tag)
        if tag == "p" and not self.skip:
            self.active = True
            self.fragments.clear()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "p" and self.active:
            paragraph = re.sub(r"\s+", " ", unescape("".join(self.fragments))).strip()
            if len(paragraph) >= 55:
                self.paragraphs.append(paragraph)
            self.active = False
            self.fragments.clear()
        if tag in _SKIP and self.skip and tag == self.skip[-1]:
            self.skip.pop()

    def handle_data(self, data: str) -> None:
        if self.active and not self.skip:
            self.fragments.append(data)


def opening_paragraphs(content_html: str, *, max_words: int = 300) -> tuple[str, ...]:
    """Read only a defensible opening portion, never the entire CMS body."""
    parser = _EditorialOpening()
    parser.feed(content_html or "")
    paragraphs = parser.paragraphs
    total = sum(len(p.split()) for p in paragraphs)
    if not total:
        return ()
    # Offer the actual decision, first move and at least one reason from the
    # published edition. A preview must be credible, not a generic cliffhanger.
    # The fraction bounds protect especially short editions from full release.
    budget = min(max_words, 375, max(90, int(total * .38)))
    selected: list[str] = []
    count = 0
    for paragraph in paragraphs:
        words = paragraph.split()
        remaining = budget - count
        if remaining < 24 or len(selected) >= 4:
            break
        if len(words) <= remaining:
            selected.append(paragraph)
            count += len(words)
            continue
        if len(selected) >= 2:
            break
        # For long first/second paragraphs preserve whole sentences.
        excerpt = " ".join(words[:remaining])
        sentence = re.search(r"^(.+[.!?])(?:\\s|$)", excerpt)
        if sentence and len(sentence.group(1)) > 90:
            selected.append(sentence.group(1))
        else:
            selected.append(excerpt.rstrip(" ,;:") + "…")
        break
    return tuple(selected)


def render_public_briefing_preview(article, read_metadata: str = "") -> str:
    """A substantive, accessible original-edition preview followed by a free gate."""
    slug = escape(str(article.slug or ""), quote=True)
    title = escape(str(article.title or "Executive AI Briefing"))
    subtitle = escape(str(article.subtitle or article.excerpt or ""))
    opening = opening_paragraphs(str(article.content_html or ""))
    if not opening:
        opening = (
            str(article.excerpt or article.subtitle or
                "The executive question starts with the business decision, its owner and the evidence needed before committing."),
        )
    # Use precisely the editorial judgments the author published; never
    # synthesize claims, benefits, sources, percentages or quotations.
    decision = re.sub(r"^The Leadership Decision\\s*:?\\s*", "", opening[0], flags=re.I)
    move = (
        re.sub(r"^Next move\\s*:?\\s*", "", opening[1], flags=re.I)
        if len(opening) > 1 else ""
    )
    context = opening[2:] if len(opening) > 2 else ()
    decision_html = f"<p>{escape(decision)}</p>"
    move_html = (
        '<aside class="briefing-preview-move"><span class="briefing-preview-small-head">'
        'A decision to put to work</span>'
        + f"<p>{escape(move)}</p></aside>"
        if move else ""
    )
    context_html = (
        '<div class="briefing-preview-context"><span class="briefing-preview-small-head">'
        'Why the choice is not straightforward</span>'
        + "".join(f"<p>{escape(p)}</p>" for p in context) + '</div>'
        if context else ""
    )
    access_base = f"?page=briefing&amp;article={slug}&amp;access=1"
    return (
        THINKING_CSS + PREVIEW_CSS + nav("thinking")
        + '<main class="briefing-preview">'
        '<section class="briefing-preview-hero" data-analytics-section="briefing-public-preview-intro">'
        '<div class="container"><a class="briefing-preview-back" href="?page=briefings" target="_self">'
        '← All Executive AI Briefings</a>'
        '<span class="briefing-preview-index">Executive AI Briefing · Free preview</span>'
        f'<h1>{title}</h1><p class="briefing-preview-deck">{subtitle}</p>'
        f'<div class="briefing-preview-meta">{escape(str(read_metadata))} · By Jair Ribeiro</div>'
        '</div></section>'
        '<section class="briefing-preview-body" data-analytics-section="briefing-public-opening">'
        '<div class="container"><div class="briefing-preview-grid">'
        '<article class="briefing-preview-copy"><div class="briefing-preview-decision">'
        '<span class="briefing-preview-small-head">From the published edition</span>'
        '<h2>The Leadership Decision</h2>' + decision_html + '</div>'
        + move_html + context_html + '</article>'
        '<aside class="briefing-preview-aside">'
        '<strong>What comes next</strong>'
        '<p>The complete edition develops the leadership decision, trade-offs, '
        'responsibilities and supporting evidence. Its original executive '
        'infographic is available as a downloadable PDF.</p></aside></div>'
        '<section class="briefing-unlock" data-analytics-section="briefing-reader-free-access">'
        '<div class="briefing-unlock-inner"><div><p class="eyebrow">Free verified reader access</p>'
        '<h2>Continue with the full briefing.</h2>'
        '<p>Get the complete executive perspective and its infographic, '
        'not just the opening section. Registration is free and only requires '
        'an email verification.</p></div>'
        '<ul class="briefing-unlock-benefits">'
        '<li>Read the entire briefing and supporting reasoning</li>'
        '<li>Explore the decision framework and original infographic</li>'
        '<li>Keep the A4 PDF for your next discussion</li>'
        '</ul></div><div class="briefing-unlock-actions">'
        f'<a class="briefing-unlock-primary" href="{access_base}" target="_self" '
        'data-hq-event="briefing_unlock_register">Get full briefing · Free</a>'
        f'<a class="briefing-unlock-secondary" href="{access_base}&amp;signin=1" target="_self" '
        'data-hq-event="briefing_unlock_signin">Already registered? Sign in</a>'
        '</div><p class="briefing-unlock-note">'
        'No payment details. Editorial email updates are optional and unchecked by default.'
        '</p></section></div></section></main>' + footer()
    )
