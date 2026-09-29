"""Memory / Learning View page: shows how knowledge about a contact evolved."""
from __future__ import annotations

from typing import List

import streamlit as st

from models.meeting import MeetingRecord
from ui import components


def _stage_label(index: int, total: int) -> str:
    if total == 1:
        return "First meeting"
    if index == 0:
        return "Earlier"
    if index == total - 1:
        return "Latest"
    return "Later"


def _timeline_lines(record: MeetingRecord) -> List[str]:
    ex = record.extraction
    lines: List[str] = []
    lines += [f"⚠️ Concern: {c}" for c in ex.concerns]
    lines += [f"⏳ Open issue: {u}" for u in ex.unresolved_issues]
    lines += [f"🤝 Commitment: {c}" for c in ex.commitments]
    lines += [f"✅ Resolved: {r}" for r in ex.resolved_issues]
    lines += [f"💡 Interest/preference: {p}" for p in ex.preferences]
    lines += [f"📌 Decision: {d}" for d in ex.decisions]
    return lines


def _render_timeline(records: List[MeetingRecord]) -> None:
    for index, record in enumerate(records):
        stage = _stage_label(index, len(records))
        with st.container(border=True):
            st.markdown(f"**{stage}** - {record.meeting_date}: *{record.title}*")
            lines = _timeline_lines(record)
            st.markdown("\n".join(f"- {line}" for line in lines) if lines else "_Nothing notable._")


def _render_brief_comparison(contact: str) -> None:
    history = [r for r in st.session_state.get("brief_history", [])
               if r.contact_name.strip().casefold() == contact.strip().casefold()]
    if len(history) < 2:
        st.caption("Prepare at least two meetings for this contact to compare how the briefs changed.")
        return
    first, last = history[0], history[-1]
    left, right = st.columns(2)
    for column, title, item in ((left, "First brief", first), (right, "Latest brief", last)):
        with column:
            st.markdown(f"**{title}** - _{item.purpose}_ ({len(item.recalled_memories)} memories)")
            components.bullet_card("Current Concerns", "⚠️", item.brief.current_concerns)
            components.bullet_card("Open Commitments", "🤝", item.brief.open_commitments)
            components.bullet_card("Suggested Agenda", "📋", item.brief.suggested_agenda)


def render_memory_view() -> None:
    st.header("🧠 Memory / Learning View")
    st.caption("How the agent's knowledge about a contact has evolved through Hindsight.")
    components.require_configuration()
    agent = components.get_agent()

    known = agent.log.contacts()
    st.session_state.setdefault("mem_contact", known[0] if known else "")
    st.text_input("Contact Name", key="mem_contact")
    if known:
        st.caption("Known contacts: " + ", ".join(known))
    contact = st.session_state["mem_contact"].strip()
    if not contact:
        st.info("Enter a contact name to see what MeetingMind has learned.")
        return

    st.subheader("Learning timeline")
    records = agent.log.for_contact(contact)
    if records:
        _render_timeline(records)
    else:
        st.info("No meetings recorded for this contact yet. Add meeting notes first.")

    st.subheader("How preparation changed")
    _render_brief_comparison(contact)

    st.subheader("Live from Hindsight")
    c1, c2 = st.columns(2)
    if c1.button("Recall memories now"):
        try:
            with st.spinner("Recalling..."):
                memories = agent.recall_for_contact(contact)
            st.markdown(f"**{len(memories)} memories recalled from Hindsight**")
            for memory in memories:
                st.markdown(f"- {memory}")
            if not memories:
                st.caption("Hindsight has no memories for this contact yet.")
        except Exception as exc:
            components.show_error(exc)
    if c2.button("Ask Hindsight to reflect"):
        try:
            with st.spinner("Reflecting..."):
                st.markdown(agent.reflect_on_contact(contact) or "_No reflection returned._")
        except Exception as exc:
            components.show_error(exc)
