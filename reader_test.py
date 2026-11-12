"""Standalone staging launcher for the verified Executive AI Briefings reader flow.

Run this file as the Streamlit Community Cloud main file in the dedicated
jairribeiro-reader-test app, not in production. This deliberately bypasses
the portfolio's general page-dispatcher and the experimental Starlette App
wrapper. All signup and PDF actions use native Streamlit widget messages.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# This launcher is staging-only. Set a fixed callback origin so Supabase OTP
# redirects cannot accidentally point to the public portfolio or localhost.
# Before merging, restore app.py's main.py entrypoint.
os.environ["PORTFOLIO_READER_CALLBACK_ORIGIN"] = (
    "https://jairribeiro-reader-test.streamlit.app"
)

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

st.set_page_config(
    page_title="Executive AI Briefings — Reader Test | Jair Ribeiro",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from page_reader_native import render_reader_native  # noqa: E402

render_reader_native()
