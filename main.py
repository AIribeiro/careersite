from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_styles import CSS
from site_image_styles import IMAGE_CSS
from site_meta import inject_article_metadata, inject_metadata
from site_analytics import inject_analytics
from thinking_articles import resolve_article
from thinking_social import ensure_all_article_social_assets

# Load curated production media and bind the canonical repository-backed CV
# before page modules import shared asset constants. PDF generation itself is a
# CI/build concern and never runs in the deployed Streamlit process.
import site_media  # noqa: F401
import site_cv_runtime  # noqa: F401

from page_home import home
from page_impact import impact
from page_thinking import thinking
from page_about import about
from page_contact import contact
from page_analytics import render_analytics_dashboard
from site_lenses import enterprise, transformation, governance, consulting

PAGE = st.query_params.get("page", "home")
if isinstance(PAGE, list):
    PAGE = PAGE[0] if PAGE else "home"
PAGE = str(PAGE).lower().strip()
PUBLIC_VALID = {"home", "impact", "thinking", "about", "contact", "enterprise", "transformation", "governance", "consulting"}
VALID = PUBLIC_VALID | {"analytics"}
PAGE = PAGE if PAGE in VALID else "home"

ARTICLE_QUERY = st.query_params.get("article", "") if PAGE == "thinking" else ""
if isinstance(ARTICLE_QUERY, list):
    ARTICLE_QUERY = ARTICLE_QUERY[0] if ARTICLE_QUERY else ""
ARTICLE_META = resolve_article(str(ARTICLE_QUERY).strip().lower()) if ARTICLE_QUERY else None

TITLES = {
    "home": "Jair Ribeiro | Enterprise AI & Data Leader",
    "impact": "Leadership Impact | Jair Ribeiro",
    "thinking": "Selected Thinking | Jair Ribeiro",
    "about": "About | Jair Ribeiro",
    "contact": "Discuss a Leadership Opportunity | Jair Ribeiro",
    "enterprise": "Enterprise AI & Data Leadership | Jair Ribeiro",
    "transformation": "AI Transformation & Adoption | Jair Ribeiro",
    "governance": "AI Governance & Operating Model | Jair Ribeiro",
    "consulting": "Business-Driven AI & Consulting | Jair Ribeiro",
    "analytics": "Hiring-Funnel Analytics | Jair Ribeiro",
}

PAGE_TITLE = ARTICLE_META.seo_title if ARTICLE_META is not None else TITLES[PAGE]
PAGE_ICON = ROOT / "images" / "profile_red_bg.jpg.jpg"

try:
    ensure_all_article_social_assets()
except OSError:
    # Routes also generate social assets on demand, so the app remains usable
    # if a constrained runtime cannot pre-warm the derivative cache.
    pass

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=str(PAGE_ICON),
    layout="wide",
    initial_sidebar_state="collapsed",
)

if PAGE == "analytics":
    render_analytics_dashboard()
else:
    if ARTICLE_META is not None:
        inject_article_metadata(ARTICLE_META)
    else:
        inject_metadata(PAGE, PAGE_TITLE)

    RENDER = {
        "home": home,
        "impact": impact,
        "thinking": thinking,
        "about": about,
        "contact": contact,
        "enterprise": enterprise,
        "transformation": transformation,
        "governance": governance,
        "consulting": consulting,
    }

    st.html(CSS + IMAGE_CSS + '<div class="site">' + RENDER[PAGE]() + '</div>')
    inject_analytics(PAGE, source="streamlit")
