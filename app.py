from __future__ import annotations

import streamlit as st

from site_styles import CSS
from site_image_styles import IMAGE_CSS
from site_meta import inject_metadata
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

# Keep page configuration independent from content photography. A damaged image
# asset must never prevent the application itself from starting.
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
