from __future__ import annotations

import streamlit as st

from site_styles import CSS
from site_image_styles import IMAGE_CSS
from site_meta import inject_metadata

# Validate and expose the manually installed /images photography before page
# modules import the URI constants from site_assets.
import site_photo_patch  # noqa: F401

# Replace the legacy downloadable CV with the website-aligned, ATS-readable
# canonical version before page modules import CV_URI from site_assets.
import site_cv_patch  # noqa: F401

# Final public-delivery overrides: verified high-resolution photography and a
# direct repository-backed PDF URL, applied before page modules import assets.
import site_delivery_patch  # noqa: F401

from page_home import home
from page_impact import impact
from page_thinking import thinking
from page_about import about
from page_contact import contact
from site_lenses import enterprise, transformation, consulting

PAGE = st.query_params.get("page", "home")
if isinstance(PAGE, list):
    PAGE = PAGE[0] if PAGE else "home"
PAGE = str(PAGE).lower().strip()
VALID = {"home", "impact", "thinking", "about", "contact", "enterprise", "transformation", "consulting"}
PAGE = PAGE if PAGE in VALID else "home"

TITLES = {
    "home": "Jair Ribeiro | Senior AI & Data Leader",
    "impact": "Leadership Impact | Jair Ribeiro",
    "thinking": "Selected Thinking | Jair Ribeiro",
    "about": "About | Jair Ribeiro",
    "contact": "Discuss a Leadership Opportunity | Jair Ribeiro",
    "enterprise": "Enterprise AI & Data Leadership | Jair Ribeiro",
    "transformation": "AI Transformation & Capability | Jair Ribeiro",
    "consulting": "Business-Driven AI & Consulting | Jair Ribeiro",
}

# Page configuration is deliberately independent from content photography.
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
    "consulting": consulting,
}

st.html(CSS + IMAGE_CSS + '<div class="site">' + RENDER[PAGE]() + '</div>')
