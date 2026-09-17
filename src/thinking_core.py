from __future__ import annotations

import html
from urllib.parse import quote

import streamlit as st

from site_components import nav, footer, opportunity
from thinking_articles import article_by_key, article_share_url, article_url

THINKING_CSS = r'''<style>
.thinking-now{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(300px,.7fr);gap:18px;align-items:stretch}
.featured-thinking{padding:34px;background:var(--navy);color:#fff;border:1px solid rgba(255,255,255,.12);display:flex;flex-direction:column;min-height:420px}
.featured-thinking .kicker,.decision-note .kicker,.format-card span,.article-meta,.article-aside span,.recent-card .kicker,.upcoming-item .kicker{font-size:9px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.featured-thinking .kicker{color:#e5aa7c}.featured-thinking h2{max-width:760px;margin:28px 0 18px;font:500 clamp(38px,5vw,58px)/1.03 Georgia,serif;letter-spacing:-.025em}.featured-thinking p{max-width:760px;margin:0;color:#bdc7d4;font-size:15px;line-height:1.72}.featured-thinking .meta{margin-top:auto;padding-top:34px;color:#8f9daf;font-size:11px}.featured-thinking .read-live{display:inline-flex;margin-top:20px;color:#fff!important;text-decoration:none!important;font-size:12px;font-weight:850}
.decision-note{padding:30px;background:var(--white);border:1px solid var(--line);border-top:4px solid var(--copper);display:flex;flex-direction:column}.decision-note .kicker{color:var(--copper)}.decision-note h3{margin:25px 0 14px;font:500 30px/1.08 Georgia,serif}.decision-note p{margin:0;color:var(--muted);font-size:14px;line-height:1.72}.decision-note .meta{margin-top:auto;padding-top:28px;color:#7b838c;font-size:10px}
.upcoming-wrap{margin-top:34px;padding:28px;background:var(--navy);color:#fff;border:1px solid rgba(255,255,255,.1)}.upcoming-head{display:flex;justify-content:space-between;gap:28px;align-items:end;margin-bottom:20px}.upcoming-head .eyebrow{color:#e5aa7c}.upcoming-head h3{margin:8px 0 0;font:500 28px/1.12 Georgia,serif}.upcoming-head p{max-width:520px;margin:0;color:#aeb9c7;font-size:12px;line-height:1.65}.upcoming-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.12)}.upcoming-item{padding:20px;background:#111b2c;min-height:160px}.upcoming-item .kicker{color:#e5aa7c}.upcoming-item strong{display:block;margin-top:14px;font:500 19px/1.22 Georgia,serif}.upcoming-item p{margin:9px 0 0;color:#aeb9c7;font-size:11px;line-height:1.58}
.format-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:30px;background:var(--line);border:1px solid var(--line)}.format-card{padding:18px;background:var(--white)}.format-card span{color:var(--copper)}.format-card strong{display:block;margin-top:8px;font:500 18px/1.2 Georgia,serif}.format-card p{margin:7px 0 0;color:var(--muted);font-size:11px;line-height:1.55}.themebar{display:flex;gap:8px;flex-wrap:wrap;margin-top:26px}.themebar span{padding:9px 11px;border:1px solid var(--line);background:var(--white);font-size:10px;font-weight:750}
.recent-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.recent-card{display:flex;flex-direction:column;min-height:230px;padding:25px;background:var(--white);border:1px solid var(--line);text-decoration:none!important}.recent-card .kicker{color:var(--copper)}.recent-card h3{margin:22px 0 11px;font:500 27px/1.12 Georgia,serif}.recent-card p{margin:0;color:var(--muted);font-size:13px;line-height:1.66}.recent-card .read{margin-top:auto;padding-top:18px;font-size:11px;font-weight:850}
.article-hero{padding:76px 0 58px;background:var(--navy);color:#fff}.article-back{display:inline-block;margin-bottom:30px;color:#c5ced9!important;text-decoration:none!important;font-size:11px;font-weight:800}.article-meta{color:#e5aa7c}.article-hero h1{max-width:920px;margin:16px 0 22px;font:500 clamp(48px,6.4vw,78px)/.99 Georgia,serif;letter-spacing:-.035em}.article-hero .standfirst{max-width:820px;margin:0;color:#c1cbd7;font-size:20px;line-height:1.65}.article-date{margin-top:22px;color:#8996a7;font-size:11px}
.article-layout{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:70px;align-items:start}.article-body{max-width:780px}.article-body p{margin:0 0 22px;color:#343b43;font-size:16px;line-height:1.82}.article-body h2{margin:48px 0 18px;font:500 34px/1.12 Georgia,serif}.article-body blockquote{margin:36px 0;padding:3px 0 3px 24px;border-left:4px solid var(--copper);font:500 25px/1.42 Georgia,serif;color:#222a32}.article-body .rule{margin-top:34px;padding:24px;background:var(--white);border:1px solid var(--line)}.article-body .rule strong{font:500 23px/1.25 Georgia,serif}.article-body .rule p{margin:10px 0 0;font-size:14px}.article-aside{position:sticky;top:98px;padding:22px;background:var(--white);border:1px solid var(--line)}.article-aside span{color:var(--copper)}.article-aside strong{display:block;margin-top:10px;font:500 20px/1.25 Georgia,serif}.article-aside p{margin:12px 0 0;color:var(--muted);font-size:12px;line-height:1.65}.article-questions{margin-top:18px;border-top:1px solid var(--line)}.article-questions div{padding:11px 0;border-bottom:1px solid var(--line);font-size:11px;line-height:1.5}
.note-full{max-width:760px;padding:32px;background:var(--white);border-left:4px solid var(--copper)}.note-full h2{margin:0 0 16px;font:500 34px/1.12 Georgia,serif}.note-full p{margin:0;color:#3e454d;font-size:16px;line-height:1.8}
.article-share{margin-top:42px;padding:28px;background:var(--navy);color:#fff;border-top:4px solid var(--copper)}.article-share-grid{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:center}.article-share .eyebrow{color:#e5aa7c}.article-share h3{margin:7px 0 9px;font:500 28px/1.15 Georgia,serif}.article-share p{max-width:620px;margin:0;color:#aeb9c7;font-size:12px;line-height:1.65}.share-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}.share-btn{appearance:none;border:1px solid rgba(255,255,255,.25);background:transparent;color:#fff!important;padding:11px 13px;font:800 11px/1 system-ui,sans-serif;text-decoration:none!important;cursor:pointer}.share-btn:hover{border-color:#e5aa7c}.share-btn.primary{background:var(--copper);border-color:var(--copper)}.share-meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px;color:#8f9daf;font-size:10px}.share-meta a{color:#cbd4df!important;text-decoration:none!important}.share-copy-status{display:inline-block;min-width:48px;color:#e5aa7c}
@media(max-width:980px){.thinking-now,.article-layout{grid-template-columns:1fr}.format-strip,.recent-grid{grid-template-columns:repeat(2,1fr)}.upcoming-grid{grid-template-columns:repeat(2,1fr)}.upcoming-head{align-items:start;flex-direction:column}.article-aside{position:static}.featured-thinking{min-height:360px}.article-share-grid{grid-template-columns:1fr}.share-actions{justify-content:flex-start}}
@media(max-width:700px){.format-strip,.recent-grid,.upcoming-grid{grid-template-columns:1fr}.featured-thinking,.decision-note{padding:24px}.upcoming-wrap{padding:22px}.article-hero{padding:58px 0 48px}.article-body p{font-size:15px}.article-body h2{font-size:30px}.article-share{padding:22px}.share-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.share-btn{text-align:center}}
</style>'''


def query_value(name: str) -> str:
    value = st.query_params.get(name, "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).strip().lower()


def _share_footer(article_key: str) -> str:
    article = article_by_key(article_key)
    canonical = article_url(article)
    share = article_share_url(article)
    linkedin_target = f"https://airibeiro.github.io/careersite/thinking/{article.slug}/"
    linkedin = "https://www.linkedin.com/sharing/share-offsite/?url=" + quote(linkedin_target, safe="")
    x_share = "https://twitter.com/intent/tweet?url=" + quote(share, safe="") + "&text=" + quote(article.social_title, safe="")
    mailto = "mailto:?subject=" + quote(article.social_title, safe="") + "&body=" + quote(f"{article.social_description}\n\n{canonical}", safe="")
    return f'''<section class="article-share"><div class="article-share-grid"><div><p class="eyebrow">Share this article</p><h3>Useful for someone working through the same decision?</h3><p>Share it directly, or copy the permanent article link.</p></div><div class="share-actions"><a class="share-btn primary" href="{html.escape(linkedin, quote=True)}" target="_blank" rel="noopener noreferrer" data-hq-event="article_share_linkedin">LinkedIn ↗</a><a class="share-btn" href="{html.escape(x_share, quote=True)}" target="_blank" rel="noopener noreferrer" data-hq-event="article_share_x">X ↗</a><a class="share-btn" href="{html.escape(mailto, quote=True)}" data-hq-event="article_share_email">Email</a><button class="share-btn" type="button" data-copy-url="{html.escape(canonical, quote=True)}" data-hq-event="article_share_copy">Copy link</button></div></div><div class="share-meta"><span>{html.escape(article.kind_topic)}</span><span>·</span><span>{html.escape(article.published_label)}</span><span>·</span><a href="?page=thinking" target="_self">More Thinking</a><span class="share-copy-status" data-copy-status></span></div></section>'''


def render_long(article_key: str, body: str, aside: str) -> str:
    article = article_by_key(article_key)
    return f'''{THINKING_CSS}{nav("thinking")}<main><section class="article-hero"><div class="container"><a class="article-back" href="?page=thinking" target="_self">← Back to Thinking</a><div class="article-meta">{html.escape(article.kind_topic)}</div><h1>{html.escape(article.title)}</h1><p class="standfirst">{html.escape(article.standfirst)}</p><div class="article-date">{html.escape(article.read_label)}</div></div></section><section class="section paper"><div class="container article-layout"><article class="article-body">{body}{_share_footer(article_key)}</article><aside class="article-aside">{aside}</aside></div></section>{opportunity()}</main>{footer()}'''


def render_note(article_key: str, note_title: str, body: str) -> str:
    article = article_by_key(article_key)
    return f'''{THINKING_CSS}{nav("thinking")}<main><section class="article-hero"><div class="container"><a class="article-back" href="?page=thinking" target="_self">← Back to Thinking</a><div class="article-meta">{html.escape(article.kind_topic)}</div><h1>{html.escape(article.title)}</h1><p class="standfirst">{html.escape(article.standfirst)}</p><div class="article-date">{html.escape(article.read_label)}</div></div></section><section class="section paper"><div class="container"><article class="note-full"><h2>{html.escape(note_title)}</h2><p>{body}</p></article>{_share_footer(article_key)}</div></section>{opportunity()}</main>{footer()}'''
