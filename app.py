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
from site_meta import inject_metadata
from site_analytics import inject_analytics

# Load curated production media and the canonical public CV before page modules
# import the shared asset constants. The delivery layer replaces the static-file
# URL with a data URI containing the exact validated PDF bytes.
import site_media  # noqa: F401
import site_cv  # noqa: F401
import site_cv_delivery  # noqa: F401

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
    "analytics": "Hiring-Funnel Analytics | Jair Ribeiro",
}

st.set_page_config(
    page_title=TITLES[PAGE],
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if PAGE == "analytics":
    render_analytics_dashboard()
else:
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
    inject_analytics(PAGE, source="streamlit")
