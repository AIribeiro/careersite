"""Advisory portfolio-native page smoke test with real widget controls."""
from __future__ import annotations
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import streamlit as st
from page_advisory_portal import render_advisory_portal
st.set_page_config(page_title="Executive Advisory | Portfolio",layout="wide")
render_advisory_portal()
