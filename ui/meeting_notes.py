"""Add Meeting Notes page."""
from __future__ import annotations

from datetime import date

import streamlit as st

from ui import components


def render_meeting_notes() -> None:
    st.header("📝 Add Meeting Notes")
    st.caption("MeetingMind extracts the important facts and stores them in Hindsight.")
    components.require_configuration()
    components.render_demo_panel("notes")

    for key, default in (("notes_contact", ""), ("notes_date", date.today()),
                         ("notes_title", ""), ("notes_text", "")):
        st.session_state.setdefault(key, default)

    left, right = st.columns(2)
    with left:
        st.text_input("Contact Name", key="notes_contact")
        st.text_input("Meeting Title", key="notes_title")
    with right:
        st.date_input("Meeting Date", key="notes_date")
    st.text_area("Meeting Notes", key="notes_text", height=220,
                 placeholder="Paste or type your notes from the meeting...")

    if st.button("Process & Remember Meeting", type="primary"):
        try:
            with st.spinner("Extracting facts and saving them to Hindsight..."):
                result = components.get_agent().process_meeting(
                    st.session_state["notes_contact"],
                    st.session_state["notes_date"].isoformat(),
                    st.session_state["notes_title"],
                    st.session_state["notes_text"],
                )
        except Exception as exc:
            components.show_error(exc)
            return

        st.subheader("What the agent extracted")
        components.render_extraction(result.extraction)
        st.subheader("Memories created in Hindsight")
        for statement in result.memory_statements:
            st.markdown(f"- {statement}")
        for warning in result.warnings:
            st.warning(warning)
        st.success("Memory updated successfully.")
        st.caption("Now prepare the next meeting with this contact to see the agent use it.")
