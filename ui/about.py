"""About / Architecture page."""
from __future__ import annotations

import streamlit as st

DIAGRAM = """User
 ↓
Streamlit UI
 ↓
Meeting Agent
 ↙        ↘
Hindsight   Groq LLM
Memory       Reasoning
 ↘        ↙
Personalized Meeting Brief
 ↓
Meeting Notes → Memory Extraction → Hindsight → Better Future Preparation"""


def render_about() -> None:
    st.header("ℹ️ About / Architecture")
    st.code(DIAGRAM, language="text")
    st.markdown(
        """
**Why Hindsight is central.** MeetingMind does not just search old notes. After every
meeting the agent extracts concerns, promises, decisions, preferences and resolutions and
retains them as memories in Hindsight. Before the next meeting it recalls those memories
and reasons over them, so the brief changes as the relationship evolves:

- **Meeting 1** - initial concern + a promise
- **Meeting 2** - follow-up needed → concern resolved, new interest learned
- **Meeting 3** - the brief drops the resolved concern and focuses on the new interest
"""
    )
