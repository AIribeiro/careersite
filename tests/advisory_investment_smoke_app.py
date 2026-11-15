"""Isolated native widget smoke for the free investment decision service."""
from pathlib import Path
import sys
import streamlit as st
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_advisory_investment import _input_ui
st.set_page_config(page_title='Executive decision smoke')
_input_ui('unit-test-token', '00000000-0000-0000-0000-000000000001')
