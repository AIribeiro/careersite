"""Isolated, unauthenticated Streamlit Advisory form smoke launcher."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
from page_advisory_portal import ADVISORY_CSS, _advisory_login

st.set_page_config(page_title="Advisory account registration test", layout="wide")
st.html(ADVISORY_CSS)
_advisory_login()
