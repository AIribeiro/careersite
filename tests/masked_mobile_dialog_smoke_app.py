"""Anonymous browser fixture for the actual Streamlit React Aria sign-in modal.

No credentials, network authentication or production URLs are used.
The fixture applies the same shared mobile CSS/JS as public article routes.
"""
from pathlib import Path
import sys

import streamlit as st

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from site_embedded_mobile import mount_masked_mobile_fix

st.set_page_config(
    page_title="Mobile dialog viewport regression",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.html(
    '<div class="site" style="background:#152331;color:#fff;padding:16px">'
    '<h1>Executive briefing mobile test</h1>'
    '<p>Public article preview. This is not a live briefing.</p></div>'
)
mount_masked_mobile_fix()


@st.dialog("Executive AI Briefing · Free reader access", width="large")
def demo_dialog() -> None:
    st.markdown("### Explore the complete executive briefing")
    st.write(
        "Sign in to read the complete executive decision analysis. "
        "This is a synthetic test: no account data is requested or submitted."
    )
    st.radio(
        "Reader status",
        ["Register free", "I already have an account"],
        horizontal=True,
        index=1,
    )
    st.radio(
        "Sign-in method",
        ["Email and password", "Email verification code"],
        horizontal=True,
    )
    with st.form("synthetic_reader_signin"):
        st.text_input("Email address", placeholder="you@example.com")
        st.text_input("Password", type="password")
        st.form_submit_button("Sign in to my library", type="primary")


demo_dialog()
