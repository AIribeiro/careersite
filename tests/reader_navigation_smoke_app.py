"""Browser-only session continuity harness for the reader's navigation bridge.

Runs locally under GitHub Actions; no real user, Supabase key, or credentials.
"""
from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from site_reader_navigation import mount_reader_navigation

st.set_page_config(page_title="Reader navigation smoke", layout="wide")
st.session_state.setdefault("reader_native_session", {"test": "verified"})
st.session_state.setdefault("reader_marker", str(uuid4()))
mount_reader_navigation()

page = str(st.query_params.get("page", "briefings"))
st.write("MEMBER SESSION: " + st.session_state["reader_marker"])
st.write("READER PAGE: " + page)
st.write("WORKSHEET ROUTE: " + str(st.query_params.get("worksheet", "")))

st.html("""<section class="site">
  <a id="smoke-briefing-a" href="?page=briefing&article=too-many-ai-opportunities-too-little-capacity" target="_self">Briefing A</a>
  <a id="smoke-briefing-b" href="?page=briefing&article=ai-governance-explained-to-executives" target="_self">Briefing B</a>
  <a id="smoke-renewal-record" href="?page=briefing&amp;article=would-you-fund-the-same-ai-initiatives-today&amp;worksheet=1" target="_self">Decision record</a>
  <a id="smoke-catalog" href="?page=briefings" target="_self">All Briefings</a>
  <a id="smoke-library" href="?page=readers" target="_self">My Library</a>
  <a id="smoke-advisory-account" href="?page=advisory-access&amp;view=scorecard" target="_self">Advisory account</a>
  <a id="smoke-branded-advisory" href="https://advisory.jairribeiro.com/?page=advisory-access&amp;view=rollout" target="_self">Branded Advisory</a>
  <a id="smoke-rollout-public" href="?page=advisory-rollout" target="_self">Public Rollout</a>
  <a id="smoke-branded-home" href="https://jairribeiro.com/" target="_self">Branded home</a>
</section>""")
