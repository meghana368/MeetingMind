"""MeetingMind - Streamlit entry point. Run with: streamlit run app.py"""
import logging

import streamlit as st

from ui import components
from ui.about import render_about
from ui.dashboard import render_dashboard
from ui.meeting_notes import render_meeting_notes
from ui.memory_view import render_memory_view
from ui.prepare_meeting import render_prepare_meeting

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="MeetingMind", page_icon="🧠", layout="wide")

PAGES = {
    "Dashboard": render_dashboard,
    "Prepare Meeting": render_prepare_meeting,
    "Add Meeting Notes": render_meeting_notes,
    "Memory / Learning View": render_memory_view,
    "About / Architecture": render_about,
}


def main() -> None:
    components.inject_css()
    st.session_state.setdefault("page", "Dashboard")
    with st.sidebar:
        st.title("🧠 MeetingMind")
        st.caption("Agents that learn using Hindsight")
        st.radio("Navigate", list(PAGES), key="page")
    components.render_sidebar_status()
    PAGES[st.session_state["page"]]()


main()
