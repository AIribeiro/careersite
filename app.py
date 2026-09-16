from __future__ import annotations

import streamlit as st

from site_styles import CSS
from site_image_styles import IMAGE_CSS
from site_meta import inject_metadata

# Load the curated public photography before page modules import asset URIs.
import site_media  # noqa: F401

# Build the canonical ATS-readable public CV and expose its same-origin static URL
# before page modules import CV_URI from site_assets.
import site_cv  # noqa: F401

from page_home import home
from page_impact import impact
from page_thinking import thinking
from page_about import about
from page_contact import contact
from site_lenses import enterprise, transformation, governance, consulting

PAGE = st.query_params.get("page", "home")
if isinstance(PAGE, list):
    PAGE = PAGE[0] if PAGE else "home"
PAGE = str(PAGE).lower().strip()
VALID = {"home", "impact", "thinking", "about", "contact", "enterprise", "transformation", "governance", "consulting"}
PAGE = PAGE if PAGE in VALID else "home"

TITLES = {
    "home": "Jair Ribeiro | Enterprise AI & Data Leadership",
    "impact": "Leadership Impact | Jair Ribeiro",
    "thinking": "Selected Thinking | Jair Ribeiro",
    "about": "About | Jair Ribeiro",
    "contact": "Discuss a Leadership Opportunity | Jair Ribeiro",
    "enterprise": "Data & AI Leadership | Jair Ribeiro",
    "transformation": "AI Transformation & Adoption | Jair Ribeiro",
    "governance": "AI Governance & Operating Model | Jair Ribeiro",
    "consulting": "Business-Driven AI & Consulting | Jair Ribeiro",
}

st.set_page_config(
    page_title=TITLES[PAGE],
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_metadata(PAGE, TITLES[PAGE])

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
