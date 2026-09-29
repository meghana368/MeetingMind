"""Prepare Meeting page."""
from __future__ import annotations

from datetime import date

import streamlit as st

from ui import components


def render_prepare_meeting() -> None:
    st.header("📋 Prepare Meeting")
    st.caption("MeetingMind recalls what it learned from past meetings and writes your brief.")
    components.require_configuration()
    components.render_demo_panel("prepare")

    for key, default in (("prep_contact", ""), ("prep_purpose", ""),
                         ("prep_date", date.today()), ("prep_context", "")):
        st.session_state.setdefault(key, default)

    left, right = st.columns(2)
    with left:
        st.text_input("Contact Name", key="prep_contact", placeholder="e.g. Sarah Johnson")
        st.text_input("Meeting Purpose", key="prep_purpose",
                      placeholder="e.g. Follow-up on implementation")
    with right:
        st.date_input("Meeting Date (optional)", key="prep_date")
        st.text_area("Additional Context (optional)", key="prep_context", height=100)

    if st.button("Prepare My Meeting", type="primary"):
        st.session_state["last_prep"] = None
        try:
            with st.spinner("Recalling memories from Hindsight and preparing your brief..."):
                result = components.get_agent().prepare_meeting(
                    st.session_state["prep_contact"],
                    st.session_state["prep_purpose"],
                    st.session_state["prep_date"].isoformat(),
                    st.session_state["prep_context"],
                )
            st.session_state["last_prep"] = result
            st.session_state.setdefault("brief_history", []).append(result)
        except Exception as exc:  # shown as a friendly message
            components.show_error(exc)

    result = st.session_state.get("last_prep")
    if result:
        components.render_preparation(result)
    else:
        st.info("Enter a contact and purpose, then click **Prepare My Meeting**.")
