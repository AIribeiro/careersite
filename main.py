from __future__ import annotations

from pathlib import Path
from time import perf_counter

# Include initial imports in the diagnostic, not just page rendering.
RUN_STARTED = perf_counter()

import logging
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_styles import CSS
from site_embedded_mobile import mount_masked_mobile_fix, support_masked_mobile_media
from site_image_styles import IMAGE_CSS
from site_meta import inject_article_metadata, inject_metadata
from site_analytics import inject_analytics
from site_article_analytics import inject_article_analytics
from site_behavior_telemetry_v2 import mount_behavior_telemetry
from site_weekly_audio_telemetry import inject_weekly_audio_telemetry
from site_share_guard import inject_share_guard
from site_shortlinks import expand_shortlink
from thinking_articles import resolve_article

# Load curated production media and bind the canonical repository-backed CV
# before page modules import shared asset constants. PDF generation itself is a
# CI/build concern and never runs in the deployed Streamlit process.
import site_media  # noqa: F401
import site_cv_runtime  # noqa: F401

from page_home_featured import inject_writing_footer
from site_portfolio_continuation import inject_portfolio_continuation

# Expand registered first-party short links before page selection and analytics.
# The browser's URL becomes the complete native article URL, so both trackers
# read the actual declared social source instead of an untagged alias.
SHORT_CODE = st.query_params.get("go", "")
SHORT_TARGET = expand_shortlink(SHORT_CODE)
if SHORT_TARGET is not None:
    st.query_params.from_dict(SHORT_TARGET)

PAGE = st.query_params.get("page", "home")
if isinstance(PAGE, list):
    PAGE = PAGE[0] if PAGE else "home"
PAGE = str(PAGE).lower().strip()
# Retired Presence page: keep incoming bookmarks working and preserve attribution.
LEGACY_PRESENCE_LINK = PAGE == "presence"
LEGACY_CREDENTIALS_LINK = PAGE == "certifications"
LEGACY_LENS_LINK = PAGE in {"enterprise", "transformation", "governance", "consulting"}
if LEGACY_PRESENCE_LINK or LEGACY_CREDENTIALS_LINK:
    PAGE = "about"
elif LEGACY_LENS_LINK:
    PAGE = "impact"

# Preserve historical ?page=admin bookmarks, but use one canonical Analytics
# page with authenticated private reporting and CMS workspaces.
LEGACY_ADMIN_LINK = PAGE == "admin"
if LEGACY_ADMIN_LINK:
    PAGE = "analytics"

PUBLIC_VALID = {"home", "impact", "thinking", "briefings", "briefing", "about", "certifications", "contact", "advisory", "advisory-access", "privacy", "enterprise", "transformation", "governance", "consulting", "ai-data-governance", "readers"}
VALID = PUBLIC_VALID | {"analytics", "admin"}
PAGE = PAGE if PAGE in VALID else "home"

ARTICLE_QUERY = st.query_params.get("article", "") if PAGE in {"thinking", "briefing"} else ""
if isinstance(ARTICLE_QUERY, list):
    ARTICLE_QUERY = ARTICLE_QUERY[0] if ARTICLE_QUERY else ""
# Handle email-link tokens before any article HTML, image, or analytics script
# renders. Supabase OTP one-time secrets must never reach external referrers.
if ARTICLE_QUERY and (
    (PAGE == "briefing" and str(st.query_params.get("pdf", "")) == "1")
    or (PAGE in {"thinking", "briefing"} and str(st.query_params.get("access", "")) == "1")
):
    from page_reader_native import _consume_query_verification, _session
    _consume_query_verification()
    if str(st.query_params.get("access", "")) == "1":
        # The full briefing is rendered only after validating an Auth session.
        # Once verified, return immediately to reading without another gate.
        reader_session, verified_identity = _session()
        if reader_session and verified_identity:
            st.query_params.pop("access", None)
            st.query_params.pop("signin", None)

CMS_ARTICLE_META = None
if ARTICLE_QUERY:
    # Only individual content readers need the public CMS lookup.
    from site_cms import fetch_public_article
    try:
        CMS_ARTICLE_META = fetch_public_article(str(ARTICLE_QUERY).strip().lower())
    except RuntimeError:
        CMS_ARTICLE_META = None
ARTICLE_META = None if CMS_ARTICLE_META is not None else (
    resolve_article(str(ARTICLE_QUERY).strip().lower()) if ARTICLE_QUERY else None
)

TITLES = {
    "home": "Jair Ribeiro | Enterprise AI & Data Leader",
    "impact": "Selected Experience | Jair Ribeiro",
    "thinking": "Articles & Perspectives | Jair Ribeiro",
    "briefings": "Executive AI Briefings | Jair Ribeiro",
    "briefing": "Executive AI Briefing | Jair Ribeiro",
    "readers": "Premium Reader Library | Jair Ribeiro",
    "about": "About | Jair Ribeiro",
    "contact": "Contact | Jair Ribeiro",
    "advisory": "Executive AI & Data Advisory | Jair Ribeiro",
    "advisory-access": "Executive Advisory Account | Jair Ribeiro",
    "privacy": "Privacy & Data | Jair Ribeiro",
    "ai-data-governance": "AI & Data Governance Leadership | Jair Ribeiro",
    "analytics": "Portfolio & Career Intelligence | Jair Ribeiro",
    "admin": "Content Studio | Jair Ribeiro",
}

PAGE_TITLE = (
    CMS_ARTICLE_META.seo_title
    if CMS_ARTICLE_META is not None and CMS_ARTICLE_META.seo_title
    else ARTICLE_META.seo_title
    if ARTICLE_META is not None
    else TITLES[PAGE]
)
PAGE_ICON = ROOT / "images" / "profile_red_bg.jpg.jpg"

# Article/social derivatives are generated by CI or their crawler routes, not
# on every Streamlit navigation and component-triggered rerun.


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=str(PAGE_ICON),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Verified readers must keep the same Streamlit WebSocket when navigating
# through the portfolio's HTML cards, header and footer. Ordinary HTML links
# create new sessions and would otherwise require email authentication again.
# Only mount this first-party navigation bridge for an existing Auth session.
if isinstance(st.session_state.get("reader_native_session"), dict):
    from site_reader_navigation import mount_reader_navigation
    mount_reader_navigation()

# Normalize the address after configuring Streamlit, leaving its public
# render flow untouched. Old Admin bookmarks now open the unified CMS.
if LEGACY_ADMIN_LINK:
    st.query_params["page"] = "analytics"
    st.query_params["workspace"] = "cms"
if LEGACY_PRESENCE_LINK or LEGACY_CREDENTIALS_LINK:
    st.query_params["page"] = "about"
if LEGACY_LENS_LINK:
    st.query_params["page"] = "impact"

if PAGE == "readers":
    # Native forms and downloads travel through Streamlit's supported widget
    # channel. Community Cloud currently returns 500 on the separate Starlette
    # HTML POST routes, so reader signup never invokes those routes.
    # Do not mount page analytics before one-time token hashes are consumed.
    from page_reader_native import render_reader_native
    render_reader_native()
elif PAGE == "advisory-access":
    # Dedicated verified membership. Advisory members inherit Reader access;
    # existing Reader sign-in never grants Advisory membership.
    from page_advisory_portal import render_advisory_portal
    render_advisory_portal()
elif PAGE == "analytics":
    # Heavy, authenticated analytics dependencies are not imported for public pages.
    from page_analytics_v2 import render_analytics_dashboard
    render_analytics_dashboard()
else:
    if CMS_ARTICLE_META is not None:
        from site_cms import inject_cms_article_metadata
        inject_cms_article_metadata(CMS_ARTICLE_META)
    elif ARTICLE_META is not None:
        inject_article_metadata(ARTICLE_META)
    else:
        inject_metadata(PAGE, PAGE_TITLE)

    # Do not import the entire site on every page visit. The governance page
    # especially does not need the Thinking, CMS reader or briefing engines.
    if PAGE == "home":
        from page_home import home
        render_page = home
    elif PAGE == "impact":
        from page_impact import impact
        render_page = impact
    elif PAGE == "thinking":
        from page_thinking import thinking
        render_page = thinking
    elif PAGE in {"briefings", "briefing"}:
        from page_executive_briefings import executive_briefings, executive_briefing_page
        render_page = executive_briefing_page if PAGE == "briefing" else executive_briefings
    elif PAGE == "about":
        from page_about import about
        render_page = about
    elif PAGE == "contact":
        from page_contact import contact
        render_page = contact
    elif PAGE == "advisory":
        from page_public_services import advisory
        render_page = advisory
    elif PAGE == "privacy":
        from page_public_services import privacy
        render_page = privacy
    elif PAGE == "ai-data-governance":
        from page_ai_data_governance import ai_data_governance
        render_page = ai_data_governance
    else:
        from page_home import home
        render_page = home

    # Separate Python build, footer selection and Streamlit HTML emission.
    # This helps distinguish cold imports from content or DOM work in Cloud logs.
    build_started = perf_counter()
    raw_document = render_page()
    raw_document = inject_portfolio_continuation(
        raw_document,
        PAGE,
        article_slug=str(ARTICLE_QUERY or ""),
        weekly_archive=(str(st.query_params.get("weekly_ai", "")).lower() == "archive"),
    )
    build_done = perf_counter()
    page_document = inject_writing_footer(raw_document, PAGE, article_slug=str(ARTICLE_QUERY or ""))
    footer_done = perf_counter()
    page_html_size = len(page_document.encode("utf-8"))
    # The executive Home navigation has a dedicated, scoped visual system.
    # Load it only for Home, after the shared CSS to avoid changing other pages.
    if PAGE == "home":
        from home_pathways_styles import HOME_PATHWAYS_CSS
        pathway_css = HOME_PATHWAYS_CSS
    else:
        pathway_css = ""
    st.html(support_masked_mobile_media(CSS + IMAGE_CSS + pathway_css) + '<div class="site">' + page_document + '</div>')
    # Compensate for mobile devices whose masking-provider frame is ~980px wide.
    # The adapter is inert for normal Streamlit visits and desktop iframes.
    mount_masked_mobile_fix()
    html_done = perf_counter()
    # Both the preview's free-access invitation and the infographic CTA
    # open one native sign-in dialog anchored to the current publication.
    if (
        PAGE == "briefing"
        and ARTICLE_QUERY
        and (
            str(st.query_params.get("pdf", "")) == "1"
            or str(st.query_params.get("access", "")) == "1"
        )
    ):
        from page_reader_native import render_briefing_access_dialog
        selected_article = CMS_ARTICLE_META or ARTICLE_META
        if selected_article is not None and str(getattr(selected_article, "kind", "")).strip().casefold() == "executive briefing":
            selected_title = str(getattr(selected_article, "title", "") or "")
            purpose = "pdf" if str(st.query_params.get("pdf", "")) == "1" else "access"
            render_briefing_access_dialog(str(ARTICLE_QUERY), selected_title, purpose)
    if (
        PAGE == "thinking"
        and ARTICLE_QUERY
        and str(st.query_params.get("access", "")) == "1"
        and CMS_ARTICLE_META is not None
    ):
        from article_access import article_is_locked
        from weekly_ai_reader_access import weekly_ai_is_premium
        if weekly_ai_is_premium(CMS_ARTICLE_META):
            from page_reader_native import render_weekly_ai_access_dialog
            render_weekly_ai_access_dialog(
                str(ARTICLE_QUERY), str(CMS_ARTICLE_META.title or "")
            )
        elif article_is_locked(CMS_ARTICLE_META):
            from page_reader_native import render_article_access_dialog
            render_article_access_dialog(
                str(ARTICLE_QUERY), str(CMS_ARTICLE_META.title or "")
            )
    if (
        PAGE == "thinking"
        and not ARTICLE_QUERY
        and str(st.query_params.get("weekly_ai", "")).lower() != "archive"
    ):
        from thinking_dynamic_order import mount_thinking_hourly_order
        mount_thinking_hourly_order()
    if PAGE == "home":
        # Live publications load in the browser, so CMS latency never blocks Home.
        from home_whats_new import inject_live_home_update
        inject_live_home_update()

    # Bind article interactions before the generic analytics listener. The
    # share guard then prevents social-share controls from being misclassified
    # as contact or generic article-click conversions.
    # Only an actual article reader needs the secondary session, heartbeat,
    # share guard and click listener. Catalogue clicks are captured by the
    # lightweight base analytics client with the destination article slug.
    if CMS_ARTICLE_META is not None or ARTICLE_META is not None:
        inject_article_analytics(PAGE, CMS_ARTICLE_META or ARTICLE_META, source="streamlit")
        inject_share_guard()
    inject_analytics(PAGE, source="streamlit")
    mount_behavior_telemetry(PAGE, CMS_ARTICLE_META or ARTICLE_META)
    if PAGE == "thinking" and CMS_ARTICLE_META is not None and CMS_ARTICLE_META.slug.startswith("weekly-ai-"):
        inject_weekly_audio_telemetry()


# Slow-only, privacy-preserving diagnostics. No article content or visitors.
# Reader Library and Analytics render through native Streamlit widgets, not
# the HTML build pipeline above. Their build timers/page_html_size do not
# exist, so never access those variables outside the public HTML branch.
elapsed_ms = round((perf_counter() - RUN_STARTED) * 1000)
if elapsed_ms >= 750:
    if PAGE in {"readers", "analytics"}:
        timings = (0, 0, 0)
        html_kib = 0
    else:
        timings = (
            round((build_done - build_started) * 1000),
            round((footer_done - build_done) * 1000),
            round((html_done - footer_done) * 1000),
        )
        html_kib = round(page_html_size / 1024)
    logging.getLogger("careersite.performance").warning(
        "slow_page_render page=%s elapsed_ms=%d html_kib=%d "
        "build_ms=%d footer_ms=%d html_emit_ms=%d",
        PAGE, elapsed_ms, html_kib, *timings,
    )
