"""Shared Streamlit helpers: session wiring, cards, errors and demo controls."""
from __future__ import annotations

import logging
from datetime import date
from typing import List

import streamlit as st

from agent.meeting_agent import MeetingAgent
from models.meeting import BRIEF_SECTIONS, MeetingBrief, MeetingExtraction, PreparationResult
from services.hindsight_service import HindsightService
from services.llm_service import LLMService
from services.meeting_service import MeetingLog
from utils import demo_data
from utils.config import Settings, load_settings
from utils.errors import MeetingMindError

logger = logging.getLogger(__name__)

EXTRACTION_SECTIONS = [
    ("topics", "Topics", "🗣️"),
    ("decisions", "Decisions", "✅"),
    ("commitments", "Commitments", "🤝"),
    ("concerns", "Concerns", "⚠️"),
    ("action_items", "Action Items", "📝"),
    ("preferences", "Preferences & Interests", "💡"),
    ("unresolved_issues", "Unresolved Issues", "⏳"),
    ("resolved_issues", "Resolved / Completed", "🎉"),
    ("outcomes", "Outcomes", "🏁"),
]

_CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1150px;}
.mm-pill {display:inline-block; padding:4px 12px; border-radius:999px;
          background:#eef2ff; color:#3730a3; font-weight:600; font-size:0.85rem;}
.mm-pill.empty {background:#fef3c7; color:#92400e;}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


# ---- session wiring -------------------------------------------------------
def get_settings() -> Settings:
    if "settings" not in st.session_state:
        st.session_state["settings"] = load_settings()
    return st.session_state["settings"]


def get_agent() -> MeetingAgent:
    """Build the agent once per browser session (API clients are created lazily)."""
    if "agent" not in st.session_state:
        settings = get_settings()
        st.session_state["agent"] = MeetingAgent(
            HindsightService(settings),
            LLMService(settings),
            MeetingLog(settings.data_dir / "meeting_log.json"),
        )
    return st.session_state["agent"]


def config_problems() -> List[str]:
    return get_settings().missing_configuration()


def require_configuration() -> None:
    """Show configuration problems and stop the page if any exist."""
    problems = config_problems()
    if problems:
        for problem in problems:
            st.error(problem)
        st.info("Copy `.env.example` to `.env`, add your keys, then restart the app.")
        st.stop()


def show_error(exc: Exception) -> None:
    """Show a friendly error; never expose stack traces to the user."""
    if isinstance(exc, MeetingMindError):
        st.error(str(exc))
    else:
        logger.error("Unexpected error", exc_info=exc)
        st.error("Something unexpected went wrong. Please try again (details are in the log).")


def set_page(name: str) -> None:
    st.session_state["page"] = name


# ---- cards ----------------------------------------------------------------
def bullet_card(title: str, icon: str, items: List[str], empty_text: str = "Nothing to report.") -> None:
    with st.container(border=True):
        st.markdown(f"**{icon} {title}**")
        if items:
            st.markdown("\n".join(f"- {item}" for item in items))
        else:
            st.caption(empty_text)


def render_brief(brief: MeetingBrief) -> None:
    with st.container(border=True):
        st.markdown("**👤 Contact Context**")
        st.write(brief.contact_context or "No context available.")
    columns = st.columns(2)
    for index, (name, title, icon) in enumerate(BRIEF_SECTIONS):
        with columns[index % 2]:
            bullet_card(title, icon, getattr(brief, name))


def render_extraction(extraction: MeetingExtraction) -> None:
    columns = st.columns(3)
    for index, (name, title, icon) in enumerate(EXTRACTION_SECTIONS):
        with columns[index % 3]:
            bullet_card(title, icon, getattr(extraction, name), "None found.")


def render_preparation(result: PreparationResult) -> None:
    """Show the brief plus proof that Hindsight memory shaped it."""
    st.subheader(f"Meeting Brief - {result.contact_name}")
    count = len(result.recalled_memories)
    if count:
        st.markdown(
            f'<span class="mm-pill">🧠 Hindsight recalled {count} memories</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="mm-pill empty">🧠 No memories yet - first-meeting brief</span>',
            unsafe_allow_html=True,
        )
    st.write("")
    render_brief(result.brief)
    st.subheader("How Hindsight shaped this brief")
    bullet_card(
        "Memory → Brief",
        "🔗",
        result.brief.how_memory_shaped_this_brief,
        "No memories were available, so nothing was adapted yet.",
    )
    with st.expander(f"Show the {count} memories recalled from Hindsight"):
        st.caption(f"Recall query: {result.query}")
        for memory in result.recalled_memories:
            st.markdown(f"- {memory}")
        if not count:
            st.caption("Nothing recalled.")


# ---- demo controls ----------------------------------------------------------
def fill_prepare_demo(step: int) -> None:
    prep = demo_data.DEMO_PREP[step]
    st.session_state["prep_contact"] = demo_data.DEMO_CONTACT
    st.session_state["prep_purpose"] = prep["purpose"]
    st.session_state["prep_date"] = date.fromisoformat(prep["date"])
    st.session_state["prep_context"] = ""


def fill_notes_demo(step: int) -> None:
    notes = demo_data.DEMO_NOTES[step]
    st.session_state["notes_contact"] = demo_data.DEMO_CONTACT
    st.session_state["notes_date"] = date.fromisoformat(notes["date"])
    st.session_state["notes_title"] = notes["title"]
    st.session_state["notes_text"] = notes["notes"]


def start_demo() -> None:
    """Dashboard 'Load Demo Scenario' callback: pre-fill step 1 and open the prepare page."""
    st.session_state["demo_active"] = True
    fill_prepare_demo(1)
    fill_notes_demo(1)
    set_page("Prepare Meeting")


def render_demo_panel(kind: str) -> None:
    """Guided demo controls. ``kind`` is 'prepare' or 'notes'."""
    if not st.session_state.get("demo_active"):
        return
    with st.container(border=True):
        st.markdown("**🎬 Demo scenario: Sarah Johnson**")
        if kind == "prepare":
            st.caption(
                "Order: prepare M1 (before learning) → add M1 notes → prepare M2 → "
                "add M2 notes → prepare M3."
            )
            cols = st.columns(3)
            for step, col in zip((1, 2, 3), cols):
                col.button(
                    f"Fill Meeting {step} prep",
                    key=f"demo_prep_{step}",
                    on_click=fill_prepare_demo,
                    args=(step,),
                )
        else:
            cols = st.columns(2)
            for step, col in zip((1, 2), cols):
                col.button(
                    f"Fill Meeting {step} notes",
                    key=f"demo_notes_{step}",
                    on_click=fill_notes_demo,
                    args=(step,),
                )


def render_sidebar_status() -> None:
    settings = get_settings()
    st.sidebar.divider()
    problems = config_problems()
    if problems:
        st.sidebar.warning("Configuration incomplete")
    else:
        st.sidebar.success("Configuration OK")
    st.sidebar.caption(f"Bank: `{settings.hindsight_bank_id}`  \nModel: `{settings.groq_model}`")
    if st.sidebar.button("Check Hindsight connection", disabled=bool(problems)):
        ok, message = get_agent().memory.health_check()
        (st.sidebar.success if ok else st.sidebar.error)(message)
