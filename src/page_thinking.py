from __future__ import annotations

import html
import re

from thinking_articles import article_by_key, article_relative_url, resolve_article
from site_cms import fetch_public_article, inject_cms_landing, render_cms_article
from thinking_core import query_value
from thinking_landing import CURRENT_PRIMARY, CURRENT_SECONDARY, RECENT, landing
from thinking_visuals import visual_spec
from thinking_week1 import pilot_to_scale, governance_accountability
from thinking_week2 import investable_portfolio, adoption_metric
from thinking_week3 import coe_not_ai_department, strategy_to_value_framework
from thinking_week4 import stop_ai_use_case, roi_diagnosed_too_late

# Public-copy guard anchors retained here because tests intentionally inspect this module.
PUBLIC_COPY_GUARD = (
    "I write selectively, usually when a recurring operating question is worth working through. "
    "Writing, speaking and research extend the operating perspective."
)

VISUAL_CSS = r'''<style>
.article-cover,.thinking-thumb{
  position:relative;display:block;width:100%;aspect-ratio:16/9;overflow:hidden;
  container-type:inline-size;background:linear-gradient(118deg,#063a67 0%,#087ba5 58%,#19b5c8 100%);
  border:1px solid rgba(255,255,255,.22);isolation:isolate;color:#fff;
}
.article-cover:before,.thinking-thumb:before{
  content:"";position:absolute;inset:0;z-index:-2;
  background-image:linear-gradient(rgba(138,232,244,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(138,232,244,.12) 1px,transparent 1px);
  background-size:7% 12.5%;
}
.article-cover:after,.thinking-thumb:after{
  content:"";position:absolute;inset:-25% -12%;z-index:-1;
  background:radial-gradient(circle at 88% 82%,rgba(21,238,240,.28),transparent 24%),radial-gradient(circle at 9% 8%,rgba(12,37,91,.34),transparent 35%);
}
.article-cover{margin:24px 0 0;box-shadow:0 20px 48px rgba(0,0,0,.22)}
.featured-thinking .thinking-thumb,.decision-note .thinking-thumb{margin:0 0 22px}
.recent-card .thinking-thumb{margin:0 0 18px;border-color:var(--line)}
.cover-content{position:absolute;left:5.3%;top:6.3%;width:60%;z-index:3}
.cover-eyebrow{font:800 clamp(8px,1.15cqw,19px)/1.1 Inter,Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#ffc089;margin-bottom:3.5cqw}
.cover-title{font:760 clamp(18px,4.55cqw,76px)/1.02 Inter,Arial,sans-serif;letter-spacing:-.035em;color:#fff;text-wrap:balance}
.cover-subtitle{margin-top:1.45cqw;max-width:96%;font:400 clamp(10px,1.72cqw,29px)/1.28 Inter,Arial,sans-serif;color:#d8edf4;text-wrap:balance}
.cover-signature{position:absolute;right:3.8%;bottom:4.5%;z-index:4;display:flex;align-items:center;gap:1cqw;font:400 clamp(9px,1.35cqw,22px)/1 Inter,Arial,sans-serif;color:#fff}
.cover-signature:before{content:"";width:3.4cqw;min-width:18px;border-top:2px solid rgba(255,255,255,.9)}
.cover-motif{position:absolute;right:4.8%;top:25%;width:34%;height:54%;z-index:2;color:#74efff}
.cover-motif *{box-sizing:border-box}
.m-node,.m-panel,.m-ring,.m-bar,.m-line,.m-dot{position:absolute}
.m-node,.m-panel{border:2px solid currentColor;box-shadow:0 0 18px rgba(80,230,255,.18)}
.m-node{width:15%;aspect-ratio:1;border-radius:10%;transform:rotate(0deg)}
.m-panel{width:17%;height:42%;border-radius:4%}
.m-line{height:2px;background:currentColor;transform-origin:left center}
.m-dot{width:2.8%;aspect-ratio:1;border-radius:50%;background:currentColor;box-shadow:0 0 12px currentColor}
.m-ring{border:2px dashed rgba(255,183,97,.92);border-radius:50%}
.m-amber{color:#ffb25f}.m-white{color:#f7fbff}.m-dim{color:#87c5d8}
/* scale */
.motif-scale .n1{left:4%;top:58%;width:13%}.motif-scale .n2{left:40%;top:37%;width:18%;color:#ffb25f}.motif-scale .n3{right:4%;top:14%;width:23%}.motif-scale .l1{left:18%;top:65%;width:25%}.motif-scale .l2{left:58%;top:49%;width:20%;color:#f7fbff}.motif-scale .d1{left:28%;top:64%}.motif-scale .d2{left:69%;top:48%;color:#ffb25f}.motif-scale .r1{right:0;top:1%;width:58%;height:96%;opacity:.55}
/* gate */
.motif-gate .flow{left:2%;top:51%;width:92%;color:#87c5d8}.motif-gate .gate{left:43%;top:8%;width:20%;height:84%;color:#ffb25f;background:rgba(255,178,95,.07)}.motif-gate .person{left:49%;top:39%;width:8%;aspect-ratio:1;border:2px solid #fff;border-radius:50%}.motif-gate .r1{left:34%;top:1%;width:38%;height:96%}
/* portfolio */
.motif-portfolio .tile{width:11%;aspect-ratio:1;border:1.5px solid #87c5d8;border-radius:13%}.motif-portfolio .t1{left:0;top:12%}.motif-portfolio .t2{left:15%;top:2%}.motif-portfolio .t3{left:1%;top:39%}.motif-portfolio .t4{left:16%;top:30%;color:#ffb25f}.motif-portfolio .t5{left:31%;top:12%}.motif-portfolio .funnel{left:46%;top:18%;width:18%;height:60%;border:2px solid #f7fbff;clip-path:polygon(0 0,100% 0,62% 45%,62% 100%,38% 100%,38% 45%)}.motif-portfolio .pick1{right:14%;top:14%;width:18%;color:#74efff}.motif-portfolio .pick2{right:0;top:50%;width:18%;color:#ffb25f}
/* adoption */
.motif-adoption .bar1{left:2%;bottom:18%;width:8%;height:20%;background:#87c5d8}.motif-adoption .bar2{left:13%;bottom:18%;width:8%;height:36%;background:#74efff}.motif-adoption .bar3{left:24%;bottom:18%;width:8%;height:52%;background:#74efff}.motif-adoption .flow{left:38%;top:55%;width:52%;color:#74efff}.motif-adoption .step1{left:39%;top:44%;width:15%;color:#f7fbff}.motif-adoption .step2{left:65%;top:35%;width:16%;color:#74efff}.motif-adoption .check{right:0;top:23%;width:20%;height:48%;color:#ffb25f}.motif-adoption .check:after{content:"✓";position:absolute;inset:0;display:grid;place-items:center;font:800 7cqw/1 Arial;color:#fff}
/* coe */
.motif-coe .hub{left:39%;top:33%;width:24%;color:#ffb25f;border-radius:50%}.motif-coe .sat{width:14%}.motif-coe .s1{left:4%;top:8%}.motif-coe .s2{left:2%;bottom:5%}.motif-coe .s3{right:2%;top:8%}.motif-coe .s4{right:0;bottom:5%}.motif-coe .c1{left:16%;top:27%;width:29%;transform:rotate(22deg)}.motif-coe .c2{left:17%;top:70%;width:28%;transform:rotate(-18deg)}.motif-coe .c3{left:60%;top:28%;width:29%;transform:rotate(-22deg)}.motif-coe .c4{left:60%;top:70%;width:29%;transform:rotate(18deg)}
/* chain */
.motif-chain{top:35%;height:35%;width:38%}.motif-chain .stage{position:absolute;top:22%;width:15%;aspect-ratio:1;border:2px solid #74efff;border-radius:50%;display:grid;place-items:center;font:700 clamp(8px,1.5cqw,20px)/1 Arial;color:#fff}.motif-chain .s1{left:0;color:#ffb25f}.motif-chain .s2{left:21%}.motif-chain .s3{left:42%}.motif-chain .s4{left:63%}.motif-chain .s5{left:84%;color:#ffb25f}.motif-chain .chainline{left:8%;top:49%;width:84%;height:2px;background:#87c5d8;z-index:-1}
/* stop */
.motif-stop .start{left:2%;top:41%;width:15%}.motif-stop .trunk{left:17%;top:50%;width:28%}.motif-stop .branch-up{left:45%;top:50%;width:31%;transform:rotate(-30deg);color:#ffb25f}.motif-stop .branch-down{left:45%;top:50%;width:32%;transform:rotate(30deg)}.motif-stop .stopbox{right:3%;top:3%;width:19%;height:34%;color:#ffb25f}.motif-stop .stopbox:after{content:"×";position:absolute;inset:0;display:grid;place-items:center;font:300 8cqw/1 Arial;color:#ffb25f}.motif-stop .gobox{right:2%;bottom:1%;width:19%;height:34%}.motif-stop .gobox:after{content:"✓";position:absolute;inset:0;display:grid;place-items:center;font:700 6cqw/1 Arial;color:#fff}
/* roi */
.motif-roi .axis{left:2%;bottom:10%;width:88%;color:#87c5d8}.motif-roi .b1{left:20%;bottom:11%;width:13%;height:22%;background:#74efff}.motif-roi .b2{left:42%;bottom:11%;width:13%;height:42%;background:#74efff}.motif-roi .b3{left:65%;bottom:11%;width:14%;height:67%;background:#ffb25f}.motif-roi .arrow{left:16%;top:67%;width:67%;transform:rotate(-28deg);color:#f7fbff}.motif-roi .r1{right:0;top:0;width:58%;height:100%;opacity:.58}
@media(min-width:701px){.article-hero h1,.article-hero .standfirst{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}}
@media(max-width:700px){.article-cover{margin-top:20px}.featured-thinking .thinking-thumb,.decision-note .thinking-thumb{margin-bottom:18px}.cover-content{width:62%}.cover-motif{opacity:.92}}
</style>'''


ROUTES = {
    "pilot_to_scale": pilot_to_scale,
    "governance_accountability": governance_accountability,
    "investable_portfolio": investable_portfolio,
    "adoption_metric": adoption_metric,
    "coe_not_ai_department": coe_not_ai_department,
    "strategy_to_value_framework": strategy_to_value_framework,
    "stop_ai_use_case": stop_ai_use_case,
    "roi_diagnosed_too_late": roi_diagnosed_too_late,
}


def _motif_html(kind: str) -> str:
    if kind == "scale":
        return '<span class="m-node n1"></span><span class="m-line l1"></span><span class="m-dot d1"></span><span class="m-node n2"></span><span class="m-line l2"></span><span class="m-dot d2"></span><span class="m-node n3"></span><span class="m-ring r1"></span>'
    if kind == "gate":
        return '<span class="m-line flow"></span><span class="m-panel gate"></span><span class="person"></span><span class="m-ring r1"></span>'
    if kind == "portfolio":
        return ''.join(f'<span class="m-node tile t{i}"></span>' for i in range(1,6)) + '<span class="funnel"></span><span class="m-node pick1"></span><span class="m-node pick2"></span>'
    if kind == "adoption":
        return '<span class="m-bar bar1"></span><span class="m-bar bar2"></span><span class="m-bar bar3"></span><span class="m-line flow"></span><span class="m-node step1"></span><span class="m-node step2"></span><span class="m-panel check"></span>'
    if kind == "coe":
        return '<span class="m-node hub"></span><span class="m-node sat s1"></span><span class="m-node sat s2"></span><span class="m-node sat s3"></span><span class="m-node sat s4"></span><span class="m-line c1"></span><span class="m-line c2"></span><span class="m-line c3"></span><span class="m-line c4"></span>'
    if kind == "chain":
        labels = "SPGAV"
        return '<span class="chainline"></span>' + ''.join(f'<span class="stage s{i+1}">{label}</span>' for i, label in enumerate(labels))
    if kind == "stop":
        return '<span class="m-node start"></span><span class="m-line trunk"></span><span class="m-line branch-up"></span><span class="m-line branch-down"></span><span class="m-panel stopbox"></span><span class="m-panel gobox"></span>'
    return '<span class="m-line axis"></span><span class="m-bar b1"></span><span class="m-bar b2"></span><span class="m-bar b3"></span><span class="m-line arrow"></span><span class="m-ring r1"></span>'


def _image(article_key: str, css_class: str) -> str:
    article = article_by_key(article_key)
    spec = visual_spec(article_key)
    title = '<br>'.join(html.escape(line) for line in spec.title_lines)
    subtitle = '<br>'.join(html.escape(line) for line in spec.subtitle_lines)
    return (
        f'<div class="{css_class}" role="img" aria-label="{html.escape(article.title + " — Jair Ribeiro", quote=True)}">'
        '<div class="cover-content">'
        '<div class="cover-eyebrow">Leading in the AI Enterprise</div>'
        f'<div class="cover-title">{title}</div>'
        f'<div class="cover-subtitle">{subtitle}</div>'
        '</div>'
        f'<div class="cover-motif motif-{html.escape(spec.motif, quote=True)}" aria-hidden="true">{_motif_html(spec.motif)}</div>'
        '<div class="cover-signature">Jair Ribeiro</div>'
        '</div>'
    )


def _decorate_article(document: str, article_key: str) -> str:
    marker = '</div></section><section class="section paper">'
    image = _image(article_key, "article-cover")
    if marker in document:
        document = document.replace(marker, image + marker, 1)
    return VISUAL_CSS + document


def _decorate_landing(document: str) -> str:
    primary_tag = '<article class="featured-thinking">'
    secondary_tag = '<article class="decision-note">'
    document = document.replace(primary_tag, primary_tag + _image(CURRENT_PRIMARY, "thinking-thumb"), 1)
    document = document.replace(secondary_tag, secondary_tag + _image(CURRENT_SECONDARY, "thinking-thumb"), 1)

    for key, _desc, _event in RECENT:
        article = article_by_key(key)
        href = html.escape(article_relative_url(article), quote=True)
        pattern = re.compile(r'(<a class="recent-card" href="' + re.escape(href) + r'"[^>]*>)')
        document = pattern.sub(r'\1' + _image(key, "thinking-thumb"), document, count=1)
    return VISUAL_CSS + document


def thinking() -> str:
    slug = query_value("article")
    if slug:
        try:
            cms_article = fetch_public_article(slug)
        except RuntimeError:
            cms_article = None
        if cms_article is not None:
            return VISUAL_CSS + render_cms_article(cms_article)

    article = resolve_article(slug)
    if article is None:
        document = _decorate_landing(landing())
        try:
            return inject_cms_landing(document)
        except RuntimeError:
            return document
    renderer = ROUTES.get(article.key)
    if renderer is None:
        document = _decorate_landing(landing())
        try:
            return inject_cms_landing(document)
        except RuntimeError:
            return document
    return _decorate_article(renderer(), article.key)
