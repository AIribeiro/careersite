"""Public advisory offering and privacy notice.

These two first-party pages are deliberately separate from reader authentication
and the privileged owner/CMS account. No email is sent by these page renderers.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib import request as url_request

import streamlit as st

from site_assets import ADVISORY_EMAIL, EMAIL, PRIVACY_EMAIL, READERS_EMAIL
from site_media import IMAGE_DIR
from site_components import footer, nav
from site_analytics import ANALYTICS_URL
from site_analytics_public import public_analytics_rpc_headers
from advisory_service_visibility import public_service_cta, service_enabled, viewer_is_admin


_ADVISORY_DEFAULT_ORDER = (
    "advisory-decision",
    "advisory-rollout",
    "advisory-scorecard",
    "advisory-leadership",
    "advisory-renewal",
    "advisory-market-signals",
)


@st.cache_data(ttl=3900, max_entries=4, show_spinner=False)
def _advisory_order_for_hour(utc_hour: str) -> tuple[str, ...]:
    """Retrieve aggregate service popularity once per hour, never visitor data.

    The UTC hour argument makes a new visit in the next hour refresh the cache.
    Supabase resolves ties by increasingly broad Europe/Stockholm periods.
    """
    endpoint = f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_advisory_service_order_v1"
    req = url_request.Request(
        endpoint,
        data=b"{}",
        method="POST",
        headers=public_analytics_rpc_headers(),
    )
    with url_request.urlopen(req, timeout=3) as response:
        ranked_pages = json.load(response)
    if (
        not isinstance(ranked_pages, list)
        or len(ranked_pages) != len(_ADVISORY_DEFAULT_ORDER)
        or any(not isinstance(page, str) for page in ranked_pages)
        or set(ranked_pages) != set(_ADVISORY_DEFAULT_ORDER)
    ):
        raise ValueError("Unexpected Advisory popularity response.")
    return tuple(ranked_pages)


def _ordered_advisory_cards(cards: dict[str, str]) -> str:
    """Keep only enabled cards; update displayed numbers after ranking."""
    try:
        utc_hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
        ranked_pages = _advisory_order_for_hour(utc_hour)
    except (OSError, ValueError, RuntimeError):
        # Analytics outages must not prevent public Advisory discovery.
        ranked_pages = _ADVISORY_DEFAULT_ORDER

    visible = [cards[page] for page in ranked_pages if cards.get(page)]
    total = len(visible)
    return "".join(
        re.sub(
            r'(?<=<span class="advisory-ready-number">)\d{2} / 06(?=</span>)',
            f"{position:02d} / {total:02d}",
            card,
        )
        for position, card in enumerate(visible, 1)
    )


SERVICES_CSS = """
<style>
.site .advisory-page,.site .privacy-page{color:#142032;background:#f6f3ed}
.site .advisory-page *, .site .privacy-page *{box-sizing:border-box}
.site .service-eyebrow{margin:0 0 19px;color:#b96b40;font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}
.site .service-lede{font-size:clamp(18px,2vw,22px);line-height:1.62;max-width:760px;color:#c5ced9}
.site .advisory-hero{background:#0c1728;color:#f9f6f0;padding:104px 0 90px;overflow:hidden}
.site .advisory-hero-grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(275px,.68fr);gap:72px;align-items:center}
.site .advisory-hero h1{font:500 clamp(48px,6.6vw,82px)/1.03 Georgia,serif;letter-spacing:-.045em;max-width:900px;margin:0 0 27px}
.site .advisory-actions{display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-top:34px}
.site .advisory-button{display:inline-flex;align-items:center;justify-content:center;min-height:51px;padding:15px 23px;background:#d69b75;color:#142032!important;text-decoration:none!important;font-size:13px;font-weight:850;letter-spacing:.01em;border:1px solid #d69b75;transition:background .15s ease}
.site .advisory-button:hover{background:#edbb9c}
.site .advisory-button--outline{background:transparent;color:#f3eee8!important;border-color:#7e8b9b}
.site .advisory-button--outline:hover{background:#263850}
.site .advisory-aside{border:1px solid #586777;padding:38px 33px;background:linear-gradient(155deg,#1b2e46,#101c2f);position:relative}
.site .advisory-aside:before{content:"";display:block;width:52px;height:3px;background:#d69b75;margin-bottom:40px}
.site .advisory-aside small{display:block;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#d4b39d;font-weight:800}
.site .advisory-aside blockquote{font:500 clamp(25px,2.7vw,36px)/1.23 Georgia,serif;letter-spacing:-.02em;margin:24px 0 26px}
.site .advisory-aside p{font-size:13px;line-height:1.75;color:#bdc8d5;margin:0}
.site .service-section{padding:85px 0}
.site .service-section--white{background:#fffefa}
.site .service-section--ink{background:#102039;color:#f6f4ee}
.site .service-section-header{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.75fr);gap:60px;align-items:end;margin-bottom:36px}
.site .service-section h2{font:500 clamp(37px,4.6vw,61px)/1.08 Georgia,serif;letter-spacing:-.025em;margin:0}
.site .service-section-header>p,.site .service-intro{line-height:1.78;color:#546276;font-size:16px;margin:0}
.site .service-section--ink .service-section-header>p,.site .service-section--ink .service-intro{color:#c4cfdb}
.site .service-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.site .service-card{background:#f6f3ed;border:1px solid #e0d9ce;padding:32px 35px;min-height:230px}
.site .service-card span{display:block;font-size:10px;letter-spacing:.17em;text-transform:uppercase;color:#b46439;font-weight:850}
.site .service-card h3{font:500 29px/1.16 Georgia,serif;margin:24px 0 13px;letter-spacing:-.015em}
.site .service-card p{line-height:1.75;font-size:14px;color:#526174;margin:0}
.site .service-formats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.site .service-format{border-top:2px solid #ca8a5d;padding:25px 26px;background:#1c2e46;min-height:252px}
.site .service-format small{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#d6a682;font-weight:800}
.site .service-format h3{font:500 27px/1.22 Georgia,serif;margin:26px 0 13px}
.site .service-format p{font-size:14px;line-height:1.76;color:#c0ccd9;margin:0}
.site .service-steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:1px solid #ded8cd;border-bottom:1px solid #ded8cd;margin-top:36px}
.site .service-step{padding:29px 25px 29px 0}
.site .service-step+.service-step{border-left:1px solid #ded8cd;padding-left:25px}
.site .service-step span{font:500 32px Georgia,serif;color:#b86c43}
.site .service-step h3{font-size:16px;line-height:1.3;margin:22px 0 10px}
.site .service-step p{font-size:13px;line-height:1.75;color:#526174;margin:0}
.site .service-contact{background:#f1e7da;border-top:1px solid #dccbb8;padding:66px 0}
.site .service-contact-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(270px,.65fr);gap:55px;align-items:center}
.site .service-contact h2{font:500 clamp(37px,4.6vw,58px)/1.09 Georgia,serif;letter-spacing:-.02em;margin:0 0 15px}
.site .service-contact p{line-height:1.73;font-size:15px;max-width:680px;color:#536073}
.site .service-contact .service-mail{font-size:17px;font-weight:750;overflow-wrap:anywhere;color:#18304d}
.site .service-note{font-size:12px!important;color:#6b6d6b!important;line-height:1.6!important}
.site .privacy-hero{background:#0e1c31;color:#f9f6ef;padding:90px 0 75px}
.site .privacy-hero h1{margin:0 0 18px;font:500 clamp(47px,6vw,76px)/1.06 Georgia,serif;letter-spacing:-.035em}
.site .privacy-hero p:not(.service-eyebrow){max-width:790px;color:#c7d1df;font-size:19px;line-height:1.65}
.site .privacy-effective{color:#e0b294!important;font-size:12px!important;letter-spacing:.04em}
.site .privacy-body{display:grid;grid-template-columns:250px minmax(0,780px);gap:70px;align-items:start;padding:75px 0 95px}
.site .privacy-toc{position:sticky;top:105px;padding:20px 23px;background:#eee8df;border:1px solid #ddd5c8}
.site .privacy-toc strong{display:block;font-size:11px;letter-spacing:.15em;text-transform:uppercase;margin-bottom:16px}
.site .privacy-toc a{display:block;margin:12px 0;color:#2d4563!important;text-decoration:none!important;font-size:13px;line-height:1.4}
.site .privacy-content section{padding:0 0 34px;margin:0 0 37px;border-bottom:1px solid #dcd5cb;scroll-margin-top:110px}
.site .privacy-content h2{font:500 31px/1.2 Georgia,serif;letter-spacing:-.015em;margin:0 0 17px}
.site .privacy-content p,.site .privacy-content li{font-size:15px;line-height:1.82;color:#45566b}
.site .privacy-content ul{padding-left:22px}
.site .privacy-content li{margin-bottom:9px}
.site .privacy-content a{color:#214d77!important;text-underline-offset:3px}
.site .privacy-contact{display:flex;align-items:flex-start;flex-direction:column;gap:5px;border-left:3px solid #b96b40;padding:16px 20px;background:#f0e9df}
.site .privacy-contact a{font-weight:800;overflow-wrap:anywhere}
@media(max-width:850px){
.site .advisory-hero-grid,.site .service-section-header,.site .service-contact-layout{grid-template-columns:1fr;gap:29px}
.site .service-formats{grid-template-columns:1fr}
.site .service-steps{grid-template-columns:repeat(2,minmax(0,1fr))}
.site .service-step:nth-child(3){border-left:0;padding-left:0}
.site .privacy-body{grid-template-columns:1fr;gap:26px}
.site .privacy-toc{position:static}
}
@media(max-width:620px){
.site .advisory-hero{padding:62px 0}
.site .advisory-hero h1{font-size:clamp(42px,11vw,60px)}
.site .advisory-aside{padding:26px}
.site .service-section{padding:58px 0}
.site .service-grid,.site .service-steps{grid-template-columns:1fr}
.site .service-step,.site .service-step+.service-step{border-left:0;border-bottom:1px solid #ddd5cb;padding:24px 0}
.site .service-card{padding:26px;min-height:0}
.site .service-contact{padding:50px 0}
.site .privacy-hero{padding:62px 0 50px}
.site .privacy-body{padding:48px 0}
}

.site .advisory-hero{padding:86px 0 76px}
.site .advisory-hero-grid{grid-template-columns:minmax(0,1.26fr) minmax(280px,.72fr);gap:62px}
.site .advisory-hero h1{font-size:clamp(45px,6vw,75px);line-height:1.08}
.site .advisory-proofline{display:flex;flex-wrap:wrap;gap:10px;margin-top:34px}
.site .advisory-proofline span{border:1px solid #5d7184;padding:9px 13px;font-size:11px;font-weight:700;color:#e2e9f2}
.site .service-section--ink .service-eyebrow{color:#e4ad84}
.site .service-intro a{color:#a35a31!important;text-underline-offset:3px}
.site .advisory-personal{display:grid;grid-template-columns:minmax(250px,.77fr) minmax(0,1.15fr);gap:70px;align-items:center}
.site .advisory-portrait{margin:0;position:relative}
.site .advisory-portrait img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:#d5d0c8;filter:saturate(.85)}
.site .advisory-portrait figcaption{font-size:12px;line-height:1.5;color:#687381;margin-top:14px}
.site .advisory-personal h2{font:500 clamp(36px,4.4vw,58px)/1.1 Georgia,serif;letter-spacing:-.025em;margin:0 0 22px}
.site .advisory-personal p:not(.service-eyebrow){line-height:1.82;color:#49586b;font-size:15px;margin:0 0 17px}
.site .advisory-personal .advisory-signoff{color:#173047!important;font-weight:800;font-size:13px!important;letter-spacing:.02em;margin-top:24px!important}
.site .advisory-results{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;margin-top:22px}
.site .advisory-result{padding:26px;border:1px solid #d7d1c8;background:#fffefa}
.site .advisory-result strong{display:block;font:500 22px/1.22 Georgia,serif;color:#1a2d43;margin-bottom:12px}
.site .advisory-result p{font-size:13px;color:#536175;line-height:1.72;margin:0}
.site .advisory-access{padding:66px 0;background:#102039;color:#f6f4ef;border-top:1px solid #26394e}
.site .advisory-access-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(250px,.8fr);gap:60px;align-items:center}
.site .advisory-access h2{font:500 clamp(36px,4vw,56px)/1.13 Georgia,serif;margin:0 0 19px}
.site .advisory-access p{color:#c4d0dc;font-size:15px;line-height:1.76}
.site .advisory-access .advisory-access-inclusion{border-left:3px solid #db9b70;padding-left:20px}
.site .advisory-access .advisory-access-inclusion strong{display:block;color:#ffe2cb;font:500 24px/1.3 Georgia,serif;margin-bottom:12px}
.site .advisory-small-link{display:inline-block;font-size:13px;font-weight:750;text-decoration:underline!important;color:#f8eee7!important;text-underline-offset:4px;margin-top:16px}

.site .advisory-access .service-eyebrow{color:#e9b58e}
.site .advisory-access .advisory-actions{margin-top:27px}
.site .advisory-access .advisory-access-inclusion{padding-top:7px}
.site .advisory-access-direct{margin-top:27px;padding-top:24px;border-top:1px solid rgba(255,255,255,.2);scroll-margin-top:100px}
.site .advisory-access-direct span{display:block;font-size:13px;font-weight:800;color:#faf5f0;letter-spacing:.01em}
.site .advisory-access-direct p{margin:9px 0 12px;color:#c4d0dc;font-size:13px;line-height:1.67}
.site .advisory-access-direct a{color:#f0b98f!important;font-size:13px;font-weight:800;text-decoration:underline!important;text-underline-offset:4px;overflow-wrap:anywhere}
.site .advisory-access-direct a:focus-visible{outline:3px solid #e9b48b;outline-offset:4px}

.site .service-method-note{margin:25px 0 0;font-size:13px;line-height:1.75;color:#627185}
.site .advisory-button:focus-visible,.site .advisory-small-link:focus-visible{outline:3px solid #e9b48b;outline-offset:4px}
@media(max-width:850px){
.site .advisory-personal,.site .advisory-access-grid{grid-template-columns:1fr;gap:30px}
.site .advisory-results{grid-template-columns:1fr}
.site .advisory-personal .advisory-portrait{max-width:520px}
}
@media(max-width:620px){
.site .advisory-hero{padding:60px 0}
.site .advisory-proofline{gap:7px}
.site .advisory-proofline span{padding:8px 10px}
.site .advisory-access{padding:53px 0}
}

/* Minimal additions: original premium layout and desktop typography are intact.
   Only ensure the original intended mobile grid wins over its desktop override. */
@media(max-width:850px){
.site .advisory-hero-grid{grid-template-columns:minmax(0,1fr);gap:29px}
.site .advisory-hero-grid>*{min-width:0}
}
@media(max-width:620px){
.site .advisory-hero h1{font-size:clamp(42px,11vw,60px)}
}


/* Discreet access links above the hero's primary message. */
.site .advisory-hero-access{
 display:inline-flex;max-width:100%;align-items:center;flex-wrap:wrap;gap:9px 14px;
 padding:10px 14px;margin:0 0 28px;
 border:1px solid rgba(196,213,231,.3);background:rgba(255,255,255,.035);
 font-size:12px;line-height:1.45
}
.site .advisory-hero-access-label{
 font-size:10px;letter-spacing:.13em;text-transform:uppercase;font-weight:850;color:#b5c3d2
}
.site .advisory-hero-access a{
 color:#f0ba94!important;text-decoration:none!important;font-weight:850;
 padding:3px 0;border-bottom:1px solid rgba(240,186,148,.52)
}
.site .advisory-hero-access a:hover{color:#ffe0c8!important;border-bottom-color:#ffe0c8}
.site .advisory-hero-access a:focus-visible{outline:2px solid #e9b48b;outline-offset:4px}
.site .advisory-hero-access-divider{width:1px;height:14px;background:rgba(255,255,255,.27)}
.site .advisory-hero-access-status{color:#c7d2df;font-weight:700;font-size:11px}
@media(max-width:620px){
 .site .advisory-hero-access{margin-bottom:23px;gap:8px 12px;padding:10px 12px}
}

/* Featured on-demand advisory services: distinct from working formats. */
.site .advisory-ready{padding:78px 0 84px;background:#f1eee8;border-top:1px solid #dfd9d0;border-bottom:1px solid #dfd9d0;scroll-margin-top:90px}
.site .advisory-ready-header{display:flex;align-items:end;justify-content:space-between;gap:32px;margin-bottom:29px}
.site .advisory-ready-header>div{max-width:800px;min-width:0}
.site .advisory-ready .service-eyebrow{margin:0 0 14px}
.site .advisory-ready h2{font:500 clamp(37px,4.5vw,57px)/1.08 Georgia,serif;letter-spacing:-.027em;color:#13263d;margin:0 0 16px}
.site .advisory-ready-lede{font-size:15px;line-height:1.73;color:#536276;margin:0;max-width:760px}
.site .advisory-ready-count{flex:0 0 auto;border-top:2px solid #bd7953;padding-top:14px;color:#6c5e52;font-size:11px;font-weight:850;letter-spacing:.12em;text-transform:uppercase;white-space:nowrap}
.site .advisory-ready-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:stretch}
.site .advisory-ready-card{display:flex;min-width:0;flex-direction:column;padding:28px 26px 26px;background:#fffefa;border:1px solid #ddd6cd;border-top:3px solid #bd7953;box-shadow:0 13px 32px rgba(17,33,53,.045);transition:border-color .16s ease,box-shadow .16s ease,transform .16s ease}
.site .advisory-ready-card:hover{border-color:#b5a38e;box-shadow:0 19px 42px rgba(17,33,53,.095);transform:translateY(-2px)}
.site .advisory-ready-card--self{border-top-color:#1c3852}
.site .advisory-ready-card-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.site .advisory-ready-category{font-size:10px;font-weight:850;letter-spacing:.1em;text-transform:uppercase;color:#a05e3b;line-height:1.6}
.site .advisory-ready-card--self .advisory-ready-category{color:#254a68}
.site .advisory-ready-number{font-size:11px;font-weight:750;color:#92908b;white-space:nowrap}
.site .advisory-ready-card h3{font:500 clamp(25px,2.35vw,31px)/1.16 Georgia,serif;letter-spacing:-.017em;color:#13263d;margin:23px 0 17px;min-height:73px}
.site .advisory-ready-question{font-size:15px;line-height:1.48;font-weight:800;color:#203952;margin:0 0 13px}
.site .advisory-ready-description{font-size:13px;line-height:1.77;color:#536174;margin:0 0 23px}
.site .advisory-ready-card-bottom{margin-top:auto;padding-top:17px;border-top:1px solid #e4ddd4}
.site .advisory-ready-detail{margin:0 0 14px;font-size:12px;line-height:1.55;color:#5c6879}
.site .advisory-ready-detail span{display:block;font-size:10px;font-weight:850;letter-spacing:.1em;text-transform:uppercase;color:#8a654f;margin-bottom:4px}
.site .advisory-ready-detail strong{font-weight:750;color:#263c52}
.site .advisory-ready-link{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:48px;margin-top:23px;padding:12px 15px;background:#17324b;color:#fffaf5!important;text-decoration:none!important;font-size:12px;font-weight:850;line-height:1.35;transition:background .15s ease}
.site .advisory-ready-link:hover{background:#294d6b;color:#fff!important}
.site .advisory-ready-link:focus-visible{outline:3px solid #b86e46;outline-offset:4px}
.site .advisory-ready-link span{font-size:18px;font-weight:500;line-height:1}
.site .advisory-ready-link--unavailable{background:#e7e6e3!important;color:#546172!important;border:1px solid #cbd0d1;cursor:not-allowed;justify-content:center}
.site .advisory-ready-link--unavailable:hover{background:#e7e6e3!important;color:#546172!important}
.site .advisory-ready-tail{font-size:12px;line-height:1.65;color:#637081;margin:22px 0 0}
.site .advisory-ready-tail a{color:#244c6d!important;font-weight:800;text-underline-offset:3px}
@media(max-width:1050px){
.site .advisory-ready-grid{grid-template-columns:1fr;gap:13px}
.site .advisory-ready-card{padding:26px 28px}
.site .advisory-ready-card h3{min-height:0;margin:16px 0;font-size:29px}
.site .advisory-ready-description{margin-bottom:19px}
}
@media(max-width:620px){
.site .advisory-ready{padding:57px 0 60px}
.site .advisory-ready-header{display:block;margin-bottom:24px}
.site .advisory-ready h2{font-size:clamp(37px,10vw,46px)}
.site .advisory-ready-lede{font-size:14px}
.site .advisory-ready-count{display:inline-block;margin-top:20px;padding-top:10px}
.site .advisory-ready-card{padding:24px 21px}
.site .advisory-ready-card h3{font-size:28px}
.site .advisory-ready-link{min-height:50px}
}
@media(prefers-reduced-motion:reduce){
.site .advisory-ready-card,.site .advisory-ready-link{transition:none}
.site .advisory-ready-card:hover{transform:none}
}

</style>
"""


def advisory() -> str:
    """Executive-grade advisory value, method, fit and distinct access."""
    member_signed_in = st.session_state.get("advisory_member") is True
    is_admin = viewer_is_admin()
    personal_available = service_enabled("requests", admin=is_admin)
    ready_count = sum(service_enabled(key, admin=is_admin) for key in ("decision", "rollout", "scorecard", "workshop", "renewal", "market-signals"))
    ready_lede = (
        f"{ready_count} executive decision tools currently accepting new starts. "
        "Compare their outputs and access conditions before you begin."
        if ready_count else
        "The decision tools are temporarily unavailable for new starts. "
        "Their scope and methods remain visible for reference."
    )
    hero_discussion_cta = (
        '<a class="advisory-button advisory-button--outline" href="#advisory-contact" '
        'data-hq-event="advisory_email_primary">Discuss a decision →</a>'
        if personal_available else ""
    )
    invitation = ("Continue your advisory conversation." if member_signed_in
                  else "Submit a decision for pro-bono review.")
    cta = ("Open my advisory space →" if member_signed_in
           else "Register for free to request advice →")
    invitation_text = (
        "Your private conversation, requests and next steps are available in your "
        "Advisory account. Your Reader Library is included."
        if member_signed_in
        else "Register for free to describe the AI or data decision you are facing. "
        "I review requests individually and may offer a focused pro-bono discussion "
        "where a senior external perspective could help. There is no charge, "
        "but availability is limited and registration does not guarantee a session."
    )

    if not personal_available:
        invitation = "Explore the available Advisory tools."
        cta = "Open my Advisory account →"
        invitation_text = (
            "New personal pro-bono discussions are currently paused. "
            "Your Advisory account and existing conversations remain available; "
            "you can still use any enabled self-service tools."
        )

    hero_account_access = (
        '<span class="advisory-hero-access-status">Signed in</span>'
        '<a href="?page=advisory-access" target="_self" '
        'data-hq-event="advisory_hero_open_account">Open my advisory space →</a>'
        if member_signed_in
        else
        '<a href="?page=advisory-access" target="_self" '
        'data-hq-event="advisory_hero_register">Register for free</a>'
        '<span class="advisory-hero-access-divider" aria-hidden="true"></span>'
        '<a href="?page=advisory-access&amp;signin=1" target="_self" '
        'data-hq-event="advisory_hero_signin">Sign in</a>'
    )

    # A repository-backed, optimized WebP; committed as plain base64 text so
    # it can be delivered reliably through the managed code connection.
    try:
        encoded_photo = (IMAGE_DIR / "advisory-portrait.webp.b64").read_text(encoding="ascii").strip()
        photo = "data:image/webp;base64," + encoded_photo if encoded_photo.startswith("UklGR") else ""
    except OSError:
        photo = ""
    portrait = (
        f'<img src="{photo}" alt="Jair Ribeiro in a relaxed professional portrait beside a stack of books" '
        'loading="lazy" decoding="async" width="540" height="540">'
        if photo else ""
    )
    decision_card = f'''\n   <article class="advisory-ready-card advisory-ready-card--self" data-analytics-section="advisory-decision">
    <div class="advisory-ready-card-head"><span class="advisory-ready-category">Self-service · Included with registration</span><span class="advisory-ready-number">01 / 06</span></div>
    <h3>AI Investment Decision Advisor</h3>
    <p class="advisory-ready-question">Should this AI opportunity move forward?</p>
    <p class="advisory-ready-description">Assess one AI opportunity and receive an invest, experiment, hold or stop recommendation, with the reasoning and three priority actions.</p>
    <div class="advisory-ready-card-bottom">
     <p class="advisory-ready-detail"><span>What you receive</span><strong>Executive verdict · Downloadable decision brief</strong></p>
     <p class="advisory-ready-detail"><span>Access</span><strong>Free with an Advisory account. No individual approval needed.</strong></p>
     {public_service_cta("decision", "?page=advisory-decision", "Explore investment advisor", "advisory_investment_service", admin=is_admin)}
    </div>
   </article>\n''' if service_enabled("decision", admin=is_admin) else ""
    rollout_card = f'''\n   <article class="advisory-ready-card" data-analytics-section="advisory-rollout">
    <div class="advisory-ready-card-head"><span class="advisory-ready-category">On-demand assessment · Individual approval</span><span class="advisory-ready-number">02 / 06</span></div>
    <h3>Enterprise AI Rollout Readiness Advisor</h3>
    <p class="advisory-ready-question">Is this AI use case ready for enterprise rollout?</p>
    <p class="advisory-ready-description">Assess business value, operations, governance, adoption and ability to scale, then see the readiness verdict and the evidence gaps to resolve.</p>
    <div class="advisory-ready-card-bottom">
     <p class="advisory-ready-detail"><span>What you receive</span><strong>Executive readiness verdict · Three priority actions</strong></p>
     <p class="advisory-ready-detail"><span>Access</span><strong>Free pro-bono service. Individual approval required.</strong></p>
     {public_service_cta("rollout", "?page=advisory-rollout", "Explore rollout advisor", "advisory_rollout_service", admin=is_admin)}
    </div>
   </article>\n''' if service_enabled("rollout", admin=is_admin) else ""
    scorecard_card = f'''\n   <article class="advisory-ready-card" data-analytics-section="advisory-scorecard">
    <div class="advisory-ready-card-head"><span class="advisory-ready-category">Portfolio assessment · Individual approval</span><span class="advisory-ready-number">03 / 06</span></div>
    <h3>AI Portfolio Prioritization Scorecard</h3>
    <p class="advisory-ready-question">Which AI opportunities deserve scarce resources?</p>
    <p class="advisory-ready-description">Compare initiatives and decide what to advance, test, hold or stop using a constrained portfolio view and alternative scenarios.</p>
    <div class="advisory-ready-card-bottom">
     <p class="advisory-ready-detail"><span>What you receive</span><strong>Portfolio recommendation · Scenarios · Decision memo</strong></p>
     <p class="advisory-ready-detail"><span>Access</span><strong>Free pro-bono service. Individual approval required.</strong></p>
     {public_service_cta("scorecard", "?page=advisory-scorecard", "Explore portfolio scorecard", "advisory_scorecard_service", admin=is_admin)}
    </div>
   </article>\n''' if service_enabled("scorecard", admin=is_admin) else ""
    workshop_card = f'''\n   <article class="advisory-ready-card advisory-ready-card--self" data-analytics-section="advisory-leadership-workshop">
    <div class="advisory-ready-card-head"><span class="advisory-ready-category">Executive leadership · Free self-service</span><span class="advisory-ready-number">04 / 06</span></div>
    <h3>Executive AI Leadership Workshop</h3>
    <p class="advisory-ready-question">Are your leaders prepared to own and sustain AI adoption?</p>
    <p class="advisory-ready-description">Assess seven leadership conditions, discuss realistic AI adoption dilemmas and document the decisions, responsibilities and evidence needed next. Individual and invited team formats.</p>
    <div class="advisory-ready-card-bottom">
     <p class="advisory-ready-detail"><span>What you receive</span><strong>Leadership profile · Discussion exercises · Executive decision PDF</strong></p>
     <p class="advisory-ready-detail"><span>Access</span><strong>Free with a verified Advisory account. No individual approval required.</strong></p>
     {public_service_cta("workshop", "?page=advisory-leadership", "Explore leadership workshop", "advisory_workshop_service", admin=is_admin)}
    </div>
   </article>\n''' if service_enabled("workshop", admin=is_admin) else ""
    renewal_card = f'''
   <article class="advisory-ready-card advisory-ready-card--self" data-analytics-section="advisory-renewal">
     <div class="advisory-ready-card-head"><span class="advisory-ready-category">Existing investments · Free self-service</span><span class="advisory-ready-number">05 / 06</span></div>
     <h3>AI Portfolio Renewal Advisor</h3>
     <p class="advisory-ready-question">Would you still fund this AI initiative today?</p>
     <p class="advisory-ready-description">Challenge an existing commitment against a credible alternative. Compare future value, evidence, scarce capacity, switching costs and mandatory obligations. Record renew, replace, test, stop or hold.</p>
     <div class="advisory-ready-card-bottom">
      <p class="advisory-ready-detail"><span>What you receive</span><strong>Two-pass challenge · Saved scenarios · Executive decision report</strong></p>
      <p class="advisory-ready-detail"><span>Access</span><strong>Free with a verified Advisory account. No separate approval required.</strong></p>
      {public_service_cta("renewal", "?page=advisory-renewal", "Explore renewal advisor", "advisory_renewal_service", admin=is_admin)}
     </div>
   </article>
''' if service_enabled("renewal", admin=is_admin) else ""
    market_card = f'''
   <article class="advisory-ready-card advisory-ready-card--self" data-analytics-section="advisory-market-signals">
     <div class="advisory-ready-card-head"><span class="advisory-ready-category">Verified market intelligence · Free access</span><span class="advisory-ready-number">06 / 06</span></div>
     <h3>AI &amp; Data Market Signals</h3>
     <p class="advisory-ready-question">Where is the AI &amp; Data market moving—and what should leaders decide next?</p>
     <p class="advisory-ready-description">Explore source-linked adoption, leadership demand, capabilities and consulting conditions. Challenge interpretations with counterevidence and export a premium executive decision brief.</p>
     <div class="advisory-ready-card-bottom">
      <p class="advisory-ready-detail"><span>What you receive</span><strong>Interactive dashboards · Source ledger · Executive PDF</strong></p>
      <p class="advisory-ready-detail"><span>Access</span><strong>Free for verified Advisory members. No individual approval required.</strong></p>
      {public_service_cta("market-signals", "?page=advisory-market-signals", "Explore market signals", "advisory_market_signals_service", admin=is_admin)}
     </div>
   </article>
''' if service_enabled("market-signals", admin=is_admin) else ""
    ready_cards = _ordered_advisory_cards({
        "advisory-decision": decision_card,
        "advisory-rollout": rollout_card,
        "advisory-scorecard": scorecard_card,
        "advisory-leadership": workshop_card,
        "advisory-renewal": renewal_card,
        "advisory-market-signals": market_card,
    })
    return f'''{SERVICES_CSS}{nav("advisory")}
<main class="advisory-page">
<section class="advisory-hero" aria-labelledby="advisory-title">
 <div class="container advisory-hero-grid">
  <div>
   <nav class="advisory-hero-access" aria-label="Advisory account access">
    <span class="advisory-hero-access-label">Advisory account</span>
    {hero_account_access}
   </nav>
   <p class="service-eyebrow">Selective pro-bono executive advisory / AI &amp; Data</p>
   <h1 id="advisory-title">Better AI decisions. Clearer ownership. Measurable business value.</h1>
   <p class="service-lede">{'For leaders facing decisions on AI investment, governance, adoption or operating ownership. I consider a limited number of focused pro-bono discussions to examine options, trade-offs and a practical next step.' if personal_available else 'For leaders considering AI investment, governance, adoption or operating ownership. Explore the executive tools currently available to support a practical decision.'}</p>
   <div class="advisory-actions">
    <a class="advisory-button" href="#advisory-services" data-hq-event="advisory_explore_value">Explore the services →</a>
    {hero_discussion_cta}
   </div>
   <div class="advisory-proofline" aria-label="Advisory disciplines"><span>Portfolio judgement</span><span>AI &amp; data governance</span><span>Operating model</span><span>Adoption &amp; value</span></div>
  </div>
  <aside class="advisory-aside" aria-label="Advisory principle">
   <small>Executive judgement</small>
   <blockquote>What should the business decide, own and measure differently?</blockquote>
   <p>The technology matters. The business case, decision rights and evidence for change determine whether it earns a place in operations.</p>
  </aside>
 </div>
</section>

<section class="advisory-ready" id="advisory-services" aria-labelledby="advisory-services-title" data-analytics-section="advisory-services">
 <div class="container">
  <div class="advisory-ready-header">
   <div>
    <p class="service-eyebrow">Available advisory services</p>
    <h2 id="advisory-services-title">Choose the decision you need to make.</h2>
    <p class="advisory-ready-lede">{ready_lede}</p>
   </div>
   <span class="advisory-ready-count">{ready_count:02d} / Available now</span>
  </div>
  <div class="advisory-ready-grid">{ready_cards}</div>
  {('<p class="advisory-ready-tail">Not sure which service fits? <a href="#advisory-contact" data-hq-event="advisory_services_ask">Describe the decision you are facing →</a></p>' if personal_available else '')}
 </div>
</section>

<section class="service-section service-section--white" id="advisory-focus" data-analytics-section="advisory-focus">
 <div class="container">
  <p class="service-eyebrow">Where I contribute</p>
  <div class="service-section-header"><h2>The decisions between AI ambition and business results.</h2>
   <p>I work at the intersection of strategy, governance, data, Lean and the way people actually work. The aim is not to produce more AI activity; it is to improve the quality of the decisions that determine value.</p>
  </div>
  <div class="service-grid">
   <article class="service-card"><span>01 / Investment judgement</span><h3>Which AI bets deserve capital?</h3><p>Challenge the portfolio against value, feasibility, reuse, cost and risk. Identify what to stop, test further, consolidate or prepare to scale—before another pilot becomes a permanent commitment.</p></article>
   <article class="service-card"><span>02 / Operating accountability</span><h3>Who owns the result?</h3><p>Set useful decision rights, business ownership and CoE responsibilities. Clarify how priorities are approved, how exceptions move, and where accountability sits after delivery.</p></article>
   <article class="service-card"><span>03 / Adoption and business change</span><h3>What will change in the work?</h3><p>Connect AI to process design, people, confidence and incentives. Measure changed workflows, decision quality and operational outcomes—not just licences, attendance or tool launches.</p></article>
   <article class="service-card"><span>04 / Trustworthy scale</span><h3>What conditions make scale credible?</h3><p>Examine data ownership and quality, AI controls, lifecycle evidence, stewardship and regulation. Make governance proportional to the business risk, without losing the ability to act.</p></article>
  </div>
 </div>
</section>

<section class="service-section" id="advisory-outcomes" data-analytics-section="advisory-outcomes">
 <div class="container">
  <p class="service-eyebrow">What the business should gain</p>
  <div class="service-section-header"><h2>Clarity you can take into the next decision.</h2>
   <p>Where a request is selected, the value should be a clearer decision: options, ownership and an evidence-based next step that can be used in a leadership discussion. Scope depends on the question and available information.</p>
  </div>
  <div class="advisory-results">
   <article class="advisory-result"><strong>A defensible decision</strong><p>Options, trade-offs, assumptions and a recommendation that makes the cost of action—and inaction—visible.</p></article>
   <article class="advisory-result"><strong>Named accountability</strong><p>Decision owners, milestones, governance boundaries and the dependencies that must be resolved.</p></article>
   <article class="advisory-result"><strong>A way to test value</strong><p>Business measures, evidence thresholds and a practical next step for stop, adapt, prove or scale.</p></article>
  </div>
 </div>
</section>

<section class="service-section service-section--ink" id="advisory-engagements" data-analytics-section="advisory-engagements">
 <div class="container">
  <p class="service-eyebrow">Ways of working</p>
  <div class="service-section-header"><h2>The right level of involvement for the decision.</h2>
   <p>I consider short decision reviews and defined working discussions on a selective, pro-bono basis. Fit, available time and the question to be examined determine what is possible.</p>
  </div>
  <div class="service-formats">
   <article class="service-format"><small>01 / Independent assessment</small><h3>Decision review</h3><p>Challenge a strategy, AI business case, investment portfolio or governance proposal. Typical result: a concise assessment of options, assumptions, risks and the recommended next decision.</p></article>
   <article class="service-format"><small>02 / Leadership working engagement</small><h3>Executive working sessions</h3><p>Work with sponsors and accountable leaders to define priorities, decision rights, operating measures and a practical route forward. Typical result: a decision record and agreed actions.</p></article>
   <article class="service-format"><small>03 / Selective follow-up</small><h3>Next-step review</h3><p>Where useful, revisit the decision record, remaining evidence gaps and named owners after an initial discussion. Follow-up is limited to the agreed question, not ongoing consulting support.</p></article>
  </div>

 </div>
</section>

<section class="service-section service-section--white" id="advisory-method" data-analytics-section="advisory-method">
 <div class="container">
  <p class="service-eyebrow">The method</p>
  <div class="service-section-header"><h2>From executive question to an owned next move.</h2>
   <p>The method is deliberately simple. It draws on enterprise portfolio management, Lean, evidence-based prioritisation, risk controls and experience of the organisational realities behind AI adoption.</p>
  </div>
  <div class="service-steps">
   <div class="service-step"><span>01</span><h3>Frame the decision</h3><p>Business outcome, sponsor, affected process, constraints and the cost of doing nothing.</p></div>
   <div class="service-step"><span>02</span><h3>Examine the evidence</h3><p>Current state, value case, data readiness, process friction, risk, stakeholders and missing facts.</p></div>
   <div class="service-step"><span>03</span><h3>Challenge the options</h3><p>What to stop, rework, test or scale; consequences, ownership and proportional controls.</p></div>
   <div class="service-step"><span>04</span><h3>Agree action and proof</h3><p>Decision record, named owners, next milestone and measures for checking whether it worked.</p></div>
  </div>
  <p class="service-method-note">I assess each request for relevance and available time. If selected, we agree the question, information boundaries and a focused next step. Pro-bono discussions are free of charge; registration alone does not confirm an engagement.</p>
 </div>
</section>

<section class="service-section" id="advisory-perspective" data-analytics-section="advisory-credibility">
 <div class="container advisory-personal">
  <figure class="advisory-portrait">{portrait}<figcaption>Jair Ribeiro · Enterprise AI &amp; Data leadership</figcaption></figure>
  <div>
   <p class="service-eyebrow">The person behind the advice</p>
   <h2>Experience from inside the decisions, not outside the business.</h2>
   <p>I have worked across enterprise AI, analytics and data leadership, often in the uncomfortable space between an attractive idea and the realities of funding, governance, ownership and adoption.</p>
   <p>I have led portfolio assessment and opportunity development, worked directly with technical teams on requirements and prototype testing, designed governance and decision responsibilities, and developed AI literacy and Champions foundations to help business teams take ownership.</p>
   <p>That experience shapes my approach: listen to the people accountable for the result, examine what the evidence supports, and make the next decision clearer. I don't offer a substitute for engineering delivery or legal advice.</p>
   <p class="advisory-signoff">Jair Ribeiro / Independent executive perspective</p>
   <p><a href="?page=impact" target="_self">Explore my leadership experience →</a> &nbsp; <a href="?page=thinking" target="_self">Read my perspectives →</a></p>
  </div>
 </div>
</section>

<section class="advisory-access" id="advisory-membership" data-analytics-section="advisory-membership">
 <div class="container advisory-access-grid">
  <div>
   <p class="service-eyebrow">Your next step</p>
   <h2>{invitation}</h2>
   <p>{invitation_text}</p>
   <div class="advisory-actions">
    <a class="advisory-button" href="?page=advisory-access" target="_self" data-hq-event="advisory_access_register">{cta}</a>
   </div>
   <a class="advisory-small-link" href="?page=advisory-access&amp;signin=1" target="_self" data-hq-event="advisory_access_signin">Already have an account? Sign in</a>
  </div>
  <aside class="advisory-access-inclusion" aria-label="Included access and direct contact">
   <strong>The Executive AI Reader Library is also free.</strong>
   <p>Register separately or use your verified account to read complete briefings, current articles and Weekly AI, with available infographic downloads. No advisory request is needed.</p>
   <div class="advisory-access-direct" id="advisory-contact" data-analytics-section="advisory-inquiry">
    <span>Prefer a direct introduction?</span>
    <p>Tell me what decision you are facing, who owns it and when it matters. No confidential details are needed.</p>
    {f'<a href="mailto:{ADVISORY_EMAIL}?subject=Executive%20advisory%20discussion" data-hq-event="advisory_email_final">Email {ADVISORY_EMAIL} →</a>' if personal_available else '<span aria-disabled="true">New discussion requests are paused</span>'}
   </div>
  </aside>
 </div>
</section>
</main>{footer()}'''

def privacy() -> str:
    """Concise GDPR notice: describe actual processing without excessive promises."""
    return f'''{SERVICES_CSS}{nav("privacy")}
<main class="privacy-page">
<section class="privacy-hero"><div class="container">
 <p class="service-eyebrow">Privacy / Reader trust</p>
 <h1>Privacy &amp; data.</h1>
 <p>A short explanation of what this website handles, why, and how to contact me. Registration does not sign you up for editorial emails.</p>
 <p class="privacy-effective">Last updated: 26 November 2026</p>
</div></section>
<div class="container privacy-body">
 <nav class="privacy-toc" aria-label="Privacy notice sections">
  <strong>In this notice</strong>
  <a href="#privacy-controller">Responsible contact</a>
  <a href="#privacy-collection">Information and purposes</a>
  <a href="#privacy-providers">Service providers</a>
  <a href="#privacy-storage">Statistics and retention</a>
  <a href="#privacy-rights">Your rights</a>
 </nav>
 <div class="privacy-content">
  <section id="privacy-controller"><h2>Who is responsible</h2>
   <p>Jair Ribeiro, based in Gothenburg, Sweden, operates this professional portfolio, Reader Library and Advisory services. For privacy requests, email <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>.</p>
  </section>
  <section id="privacy-collection"><h2>Information and why it is used</h2>
   <p>When you register, I process your name, email address, authentication and account records to provide access. Download and saved-content records support your library. Professional profile fields are optional unless needed for a service you request.</p>
   <p>If you request Advisory support, submit an assessment, or join a workshop, I process the information and correspondence you choose to provide to deliver that service. Some collaborative workshops let participants choose whether to share their responses with the organizer; the relevant sharing choice is presented in the workshop.</p>
   <p><strong>Optional Advisory service feedback:</strong> if you leave a rating or comment, it may be used to understand and improve the service. Leaving feedback is optional and does not enroll you in editorial emails.</p>
   <p>The legal grounds are providing requested services or taking steps you request before an agreement (GDPR Article 6(1)(b)); legitimate interests in securing the site and responding to inquiries (Article 6(1)(f)); consent for optional editorial emails (Article 6(1)(a)); and legal obligations where applicable (Article 6(1)(c)). Editorial emails are always optional; site-usage measurement is part of the website experience. Providing an email address is required for registered access.</p>
   <p>Please do not submit sensitive personal details or confidential business material unless suitable handling arrangements have been agreed.</p>
  </section>
  <section id="privacy-providers"><h2>Service providers</h2>
   <p>The website runs on Streamlit Community Cloud, which hosts apps in the United States. The Supabase database is in an EU region. Authentication, domain and transactional email services and their subprocessors may process information needed for those functions. External links, including LinkedIn, have separate privacy practices.</p>
   <p>Some processing may take place outside the European Economic Area. Supabase describes international transfers and its contractual safeguards in its <a href="https://supabase.com/legal/customer-resources/data-processing-addendum" target="_blank" rel="noopener noreferrer">data-processing agreement</a>. Other provider arrangements may differ. For details relevant to your information, contact <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>.</p>
  </section>
  <section id="privacy-storage"><h2>Statistics, cookies and retention</h2>
   <p>When you visit this portfolio, first-party website analytics record page and publication opens, source and campaign tags, the referring domain where available, clicked links and calls to action, reading and session duration, scroll depth, section exposure, reading interactions, audio milestones, and technical performance. Browser-derived context may include browser and operating-system family, device class, language, timezone, viewport and screen dimensions, network category, orientation and device capability indicators. A randomly generated, temporary per-tab session identifier links events within a visit; it is held in browser session storage. This site does not use advertising trackers or record passwords, authentication codes, private form contents or private message contents as website-analytics events.</p>
   <p>Basic server-side page and publication counts are also recorded as daily totals without session identifiers. Browser statistics run when the site loads; no separate statistics opt-in is currently shown. Browser restrictions and blocking tools can affect what can be recorded. For questions or objections relating to website-usage data, contact <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>. Essential authentication and security cookies may be used for access.</p>
   <p>Raw website analytics are scheduled for deletion after 90 days; longer-term reports may retain aggregated counts. Account information and saved service work are kept while the account or requested service is active, and reviewed for deletion on closure or a verified deletion request, subject to applicable security or legal requirements. Correspondence is kept for the inquiry and any resulting relationship, then reviewed for deletion.</p>
  </section>
  <section id="privacy-rights"><h2>Your rights</h2>
   <p>Under applicable conditions, you may request access, correction, deletion, restriction, portability, or object to certain processing. You may withdraw consent to optional editorial emails and object to processing based on legitimate interests, subject to applicable conditions. Identity verification may be needed before disclosing or deleting account information.</p>
   <p>Email <a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a> for requests. Reader access support: <a href="mailto:{READERS_EMAIL}">{READERS_EMAIL}</a>. You can also complain to Sweden's <a href="https://www.imy.se/en/" target="_blank" rel="noopener noreferrer">Integritetsskyddsmyndigheten (IMY)</a>.</p>
  </section>
 </div>
</div>
</main>{footer()}'''
