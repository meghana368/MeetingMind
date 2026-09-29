"""Dashboard page."""
from __future__ import annotations

import streamlit as st

from ui import components


def render_dashboard() -> None:
    st.title("🧠 MeetingMind")
    st.caption(
        "An AI meeting-preparation agent that remembers every conversation, learns, "
        "and prepares you better each time - powered by Hindsight memory."
    )
    for problem in components.config_problems():
        st.warning(problem)

    log = components.get_agent().log
    records = log.all()
    contacts = log.contacts()

    m1, m2, m3 = st.columns(3)
    m1.metric("Meetings recorded", len(records))
    m2.metric("Contacts remembered", len(contacts))
    m3.metric("Memories retained", sum(len(r.memory_statements) for r in records))

    b1, b2, b3 = st.columns(3)
    b1.button("📋 Prepare a meeting", on_click=components.set_page, args=("Prepare Meeting",),
              use_container_width=True)
    b2.button("📝 Add meeting notes", on_click=components.set_page, args=("Add Meeting Notes",),
              use_container_width=True)
    b3.button("🎬 Load Demo Scenario", on_click=components.start_demo, type="primary",
              use_container_width=True)

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Recent contacts")
        if not contacts:
            st.info("No contacts yet. Add meeting notes or load the demo scenario.")
        for name in contacts[:5]:
            last = log.for_contact(name)[-1]
            st.markdown(f"**{name}** - last met {last.meeting_date} ({len(log.for_contact(name))} meetings)")
    with right:
        st.subheader("Recent meeting activity")
        if not records:
            st.info("Nothing recorded yet.")
        for record in sorted(records, key=lambda r: r.recorded_at, reverse=True)[:5]:
            st.markdown(
                f"**{record.meeting_date}** - {record.contact_name}: {record.title}  \n"
                f"<small>{len(record.memory_statements)} memories retained</small>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown(
        "**The learning loop:** Notes → Extraction → **Hindsight retain** → "
        "**Hindsight recall** → Reasoning → Brief → new notes → better brief"
    )
    with st.expander("Demo utilities"):
        st.caption(
            "Clears only the local activity log. Memories already in Hindsight stay there - "
            "use a new HINDSIGHT_BANK_ID in .env for a completely fresh demo."
        )
        if st.button("Clear local activity log"):
            log.reset()
            st.session_state.pop("brief_history", None)
            st.rerun()
