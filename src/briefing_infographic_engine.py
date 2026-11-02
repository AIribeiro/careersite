from __future__ import annotations

"""Executive Briefing Infographic Engine.

Generates original, structured, first-party SVGs from an editorial specification.
No remote images, SVG scripts, model hallucinations or infographic-source copying.
An editor must approve a version before public use.
"""

import base64
import hashlib
import html
import re
import textwrap
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Mapping


PATTERNS = ("comparison", "flow", "layers", "decision", "timeline", "questions")
REVIEW_KEYS = (
    "factual_accuracy", "originality", "anonymity",
    "readability", "mobile", "content_fit",
)
NAVY = "#142e43"
INK = "#213d50"
COPPER = "#b98058"
CREAM = "#faf7f1"
SAND = "#e8c8a9"
MUTED = "#566c77"
TEAL = "#2d6771"
WHITE = "#ffffff"


class _Headings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.level = ""
        self.headings = []
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3"):
            self.level = tag
            self.buffer = []

    def handle_data(self, data):
        if self.level:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == self.level:
            heading = " ".join(" ".join(self.buffer).split())
            if heading:
                self.headings.append(heading)
            self.level = ""
            self.buffer = []


def source_fingerprint(article) -> str:
    """Matches the PostgreSQL sha256 calculation used in backfill."""
    seed = "|".join((
        str(getattr(article, "title", "") or ""),
        str(getattr(article, "subtitle", "") or ""),
        str(getattr(article, "content_html", "") or ""),
    ))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _clean(value: object, limit: int = 180) -> str:
    return " ".join(html.unescape(str(value or "")).split())[:limit]


def validate_spec(spec: Mapping) -> None:
    if not isinstance(spec, Mapping):
        raise ValueError("Infographic specification must be a JSON object.")
    if spec.get("pattern") not in PATTERNS:
        raise ValueError("Select a supported visual pattern.")
    if len(_clean(spec.get("title"))) < 8:
        raise ValueError("Infographic needs a precise title.")
    items = spec.get("items")
    if not isinstance(items, list) or not 2 <= len(items) <= 7:
        raise ValueError("Provide between two and seven editorial proof points.")
    for item in items:
        if not isinstance(item, dict) or not _clean(item.get("title")):
            raise ValueError("Each proof point must have a title.")
        if len(_clean(item.get("detail"))) < 12:
            raise ValueError("Each proof point needs specific, explanatory evidence.")
        if len(_clean(item.get("detail"))) > 176:
            raise ValueError("Use concise detail text (176 characters maximum).")
    if spec.get("pattern") == "timeline" and len(items) > 5:
        raise ValueError("Timelines support at most five milestones.")
    if len(_clean(spec.get("conclusion"))) < 12:
        raise ValueError("State the executive conclusion, not just a topic.")
    from briefing_content_policy import validate_briefing_employer_anonymity
    from types import SimpleNamespace
    validate_briefing_employer_anonymity(SimpleNamespace(
        kind="Executive Briefing",
        content_html=str(spec),
    ))


def generate_infographic_spec(article) -> dict:
    """Deterministic field-guided first draft; editors refine and approve.

    The input is the article's own headings and decision language. This
    function does NOT assert a generative model evaluated the facts.
    """
    title = _clean(getattr(article, "title", ""), 110)
    subtitle = _clean(getattr(article, "subtitle", ""), 135)
    parser = _Headings()
    parser.feed(str(getattr(article, "content_html", "") or ""))
    headings = [h for h in parser.headings if not re.search(
        r"references|sources|contact|disclaimer|editorial note", h, re.I
    )]
    low = title.lower()
    if " vs " in low or "versus" in low:
        pattern = "comparison"
    elif "act" in low or "regulat" in low or "deadline" in low:
        pattern = "timeline"
    elif "layer" in low or "governance explained" in low:
        pattern = "layers"
    elif "questions" in low:
        pattern = "questions"
    elif "fund" in low or "decision" in low or "invest" in low:
        pattern = "decision"
    else:
        pattern = "flow"
    if len(headings) < 2:
        headings = ["Business outcome", "Accountability", "Evidence", "Decision gate"]
    items = [
        {"label": f"{i:02d}", "title": _clean(heading, 39),
         "detail": f"Check the relevant evidence and decision owner for {heading.lower().rstrip('.')}."}
        for i, heading in enumerate(headings[:5] if pattern == "timeline" else headings[:7], start=1)
    ]
    return {
        "pattern": pattern, "title": title,
        "deck": subtitle or "The operating evidence behind an executive decision.",
        "items": items,
        "conclusion": "A decision needs clear evidence, ownership and a next review gate.",
        "version": 1,
    }


def _svg_text(x, y, value, *, size=23, color=INK, weight=500, chars=45,
              lines=2, leading=1.26, family="Arial,Helvetica,sans-serif") -> str:
    wrapped = textwrap.wrap(_clean(value, 220), width=chars,
                            break_long_words=False, break_on_hyphens=False)
    if not wrapped:
        return ""
    wrapped = wrapped[:lines]
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else round(size * leading)}">'
        f'{html.escape(line, quote=True)}</tspan>'
        for i, line in enumerate(wrapped)
    )
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}">{spans}</text>')


def _rect(x,y,w,h,fill,stroke="none",r=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


def _node(item, i, x, y, w, h, accent=COPPER, *, compact=False):
    detail = _clean(item.get("detail"), 176)
    title = _clean(item.get("title"), 68)
    label = _clean(item.get("label") or f"{i+1:02d}", 16)
    pieces = [_rect(x,y,w,h,WHITE,"#dce1dd",13),
              _rect(x,y,6,h,accent,r=2),
              _svg_text(x+24,y+31,label.upper(),size=14,weight=800,color=accent,chars=24,lines=1),
              _svg_text(x+24,y+66,title,size=23 if not compact else 21,
                        weight=700,color=NAVY,chars=33 if w>420 else 24,lines=2),
              _svg_text(x+24,y+116 if not compact else y+110,detail,size=17 if not compact else 16,
                        color=MUTED,chars=42 if w>420 else 29,lines=3)]
    return "".join(pieces)


def _base_start(width, height, spec, mobile=False):
    title = _clean(spec.get("title"), 115)
    deck = _clean(spec.get("deck"), 150)
    top = ['<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           'role="img" aria-label="Original executive infographic">',
           _rect(0,0,width,height,CREAM,r=0),
           _rect(0,0,width,10,COPPER,r=0),
           '<rect x="0" y="10" width="13" height="125" fill="#285669"/>',
           _svg_text(50 if mobile else 64,48,"EXECUTIVE DECISION GRAPHIC",
                     size=13,color=TEAL,weight=800,chars=40,lines=1),
           _svg_text(50 if mobile else 64,87,title,
                     size=35 if mobile else 41,color=NAVY,weight=700,
                     chars=31 if mobile else 55,lines=2,
                     family="Georgia,Times New Roman,serif"),
           _svg_text(50 if mobile else 64,165 if mobile else 175,deck,
                     size=18 if mobile else 19,color=MUTED,
                     chars=45 if mobile else 105,lines=2)]
    return top


def _conclusion(spec, y, width, mobile=False):
    x=20 if mobile else 64
    w=width-40 if mobile else width-128
    h=142 if mobile else 96
    return "".join([
        _rect(x,y,w,h,NAVY,r=14),
        _svg_text(x+22,y+28,"EXECUTIVE DECISION",size=13,color=SAND,weight=800,
                  chars=50,lines=1),
        _svg_text(x+22,y+59,spec.get("conclusion",""),size=21 if mobile else 23,
                  color=WHITE,weight=600,chars=30 if mobile else 81,
                  lines=3 if mobile else 2),
    ])


def _desktop(spec):
    items=spec["items"]
    n=len(items)
    pattern=spec["pattern"]
    width=1200
    height=1040 if (n>=7 and pattern not in ("layers", "timeline")) or (pattern=="comparison" and n>4) else 810
    p=_base_start(width,height,spec)
    if pattern=="comparison":
        # Two editorial columns. Not a restatement of the source infographic.
        p.extend([_rect(64,206,530,40,"#d9edf0",r=8),
                  _rect(606,206,530,40,"#f2dfce",r=8),
                  _svg_text(87,233,"INFORMATION / INPUTS",size=16,color=NAVY,weight=800),
                  _svg_text(630,233,"BEHAVIOUR / ACTION",size=16,color=NAVY,weight=800)])
        split=(n+1)//2
        for i,item in enumerate(items):
            column=0 if i<split else 1
            index=i if column==0 else i-split
            x=64 if column==0 else 606
            y=259+index*205
            p.append(_node(item,i,x,y,530,190,TEAL if column==0 else COPPER,compact=True))
    elif pattern=="timeline":
        p.append('<path d="M 88 308 H 1110" fill="none" stroke="#c8a584" stroke-width="5"/>')
        count=min(n,5)
        w=210
        gap=(1040-w*count)/(max(1,count-1)) if count>1 else 0
        for i,item in enumerate(items[:count]):
            x=64+round(i*(w+gap))
            p.append(f'<circle cx="{x+100}" cy="308" r="14" fill="{COPPER}" stroke="{CREAM}" stroke-width="6"/>')
            p.append(_node(item,i,x,345,w,267,TEAL if i%2==0 else COPPER,compact=True))
    elif pattern=="layers":
        for i,item in enumerate(items):
            y=201+i*67
            p.extend([_rect(64+i*14,y,1072-i*28,60, "#e7f0ef" if i%2==0 else "#f2e5d7", r=9),
               _svg_text(90+i*14,y+25,item.get("label") or f"{i+1:02d}",size=14,weight=800,color=TEAL,chars=10,lines=1),
               _svg_text(142+i*14,y+26,item.get("title"),size=21,weight=700,color=NAVY,chars=36,lines=1),
               _svg_text(560,y+26,item.get("detail"),size=17,color=INK,chars=62,lines=1)])
    else:
        # Three independent visual grammars for flow, questions and decision.
        if pattern=="questions":
            p.extend([_rect(423,218,354,67,NAVY,r=31),
                      _svg_text(466,259,"CHALLENGE THE DECISION",size=17,color=WHITE,weight=800,chars=36,lines=1)])
        cols=3 if n>=5 else 2
        cell_w=round((1072-(cols-1)*14)/cols)
        rows=(n+cols-1)//cols
        h=182 if rows>=3 else 224
        first_y=307 if pattern=="questions" else 215
        for i,item in enumerate(items):
            row=i//cols; col=i%cols
            x=64+col*(cell_w+14); y=first_y+row*(h+13)
            accent=TEAL if pattern=="questions" else COPPER if (i%2) else TEAL
            p.append(_node(item,i,x,y,cell_w,h,accent,compact=True))
            if pattern=="flow" and i<n-1 and col<cols-1:
                p.append(_svg_text(x+cell_w+2,y+107,"›",size=25,color=COPPER,weight=800,chars=2,lines=1))
    p.append(_conclusion(spec,height-119,width))
    p.append('</svg>')
    return "".join(p)


def _mobile(spec):
    """A genuinely narrow SVG canvas: type stays legible at phone CSS widths."""
    items=spec["items"]
    width=420
    title=_clean(spec.get("title"),115)
    deck=_clean(spec.get("deck"),150)
    title_lines=textwrap.wrap(title,width=22,break_long_words=False,break_on_hyphens=False)
    deck_lines=textwrap.wrap(deck,width=40,break_long_words=False,break_on_hyphens=False)
    deck_y=84+max(0,len(title_lines)-1)*35+42
    first_y=deck_y+max(0,len(deck_lines)-1)*24+56
    conclusion_y=first_y+len(items)*174+12
    height=conclusion_y+160
    p=[
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="Executive decision infographic">',
        _rect(0,0,width,height,CREAM,r=0),
        _rect(0,0,width,8,COPPER,r=0),
        _svg_text(22,42,"EXECUTIVE DECISION GRAPHIC",size=12,color=TEAL,
                  weight=800,chars=40,lines=1),
        _svg_text(22,84,title,size=29,color=NAVY,weight=700,
                  chars=22,lines=6,leading=1.21,
                  family="Georgia,Times New Roman,serif"),
        _svg_text(22,deck_y,deck,size=17,color=MUTED,chars=40,lines=4),
    ]
    for i,item in enumerate(items):
        y=first_y+i*174
        p.append(_node(item,i,20,y,380,160,TEAL if i%2==0 else COPPER,compact=True))
    p.append(_conclusion(spec,conclusion_y,width,True))
    p.append("</svg>")
    return "".join(p)


def render_svg(spec: Mapping, *, mobile: bool=False) -> str:
    validate_spec(spec)
    return _mobile(spec) if mobile else _desktop(spec)


def svg_image_data(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


INFOGRAPHIC_CSS = """<style>
.site .ebi-figure{margin:22px 0 29px;padding:15px;background:#f8f5ef;border:1px solid #d7d8d3}
.site .ebi-kicker{display:block;font:800 10px/1.5 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#8b603f;margin:0 0 9px}
.site .ebi-picture{display:block}
.site .ebi-picture img{display:block;width:100%;height:auto;max-width:100%;border:0}
.site .ebi-figure figcaption{padding:12px 3px 2px;font:400 12px/1.65 Arial,sans-serif;color:#465e6d}
@media(max-width:650px){.site .ebi-figure{margin:16px 0 22px;padding:8px}.site .ebi-figure figcaption{font-size:11px}}
</style>"""


def infographic_html(spec: Mapping, alt: str, caption: str, slug: str) -> str:
    """Only approved data should call this in a public reader."""
    alt=_clean(alt, 400)
    if len(alt)<40:
        raise ValueError("The visual requires detailed accessible alt text.")
    desktop=svg_image_data(render_svg(spec))
    mobile=svg_image_data(render_svg(spec,mobile=True))
    return (INFOGRAPHIC_CSS
            + '<section class="ebi-section" data-analytics-section="briefing-infographic" '
            + f'data-hq-content-slug="{html.escape(_clean(slug,150),quote=True)}">'
            + '<figure class="ebi-figure">'
            + '<span class="ebi-kicker">The executive visual</span>'
            + '<picture class="ebi-picture">'
            + f'<source media="(max-width: 700px)" srcset="{mobile}"/>'
            + f'<img src="{desktop}" alt="{html.escape(alt,quote=True)}" loading="eager" decoding="async"/>'
            + '</picture><figcaption>'
            + html.escape(_clean(caption,300))
            + '</figcaption></figure></section>')
