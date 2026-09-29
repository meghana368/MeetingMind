"""MeetingAgent: orchestrates Hindsight memory and Groq reasoning."""
from __future__ import annotations

import logging
from typing import List, Optional

from agent.prompts import (
    BRIEF_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    build_brief_prompt,
    build_extraction_prompt,
)
from models.meeting import (
    MeetingBrief,
    MeetingExtraction,
    MeetingRecord,
    PreparationResult,
    ProcessingResult,
)
from services.hindsight_service import HindsightService
from services.llm_service import LLMService
from services.meeting_service import (
    MeetingLog,
    build_memory_statements,
    require_text,
    to_timestamp,
)
from utils.errors import AgentError, HindsightError

logger = logging.getLogger(__name__)


class MeetingAgent:
    """Prepares meetings from recalled memories and learns from new meeting notes."""

    def __init__(self, memory: HindsightService, llm: LLMService, log: MeetingLog) -> None:
        self._memory = memory
        self._llm = llm
        self._log = log

    @property
    def memory(self) -> HindsightService:
        return self._memory

    @property
    def log(self) -> MeetingLog:
        return self._log

    @staticmethod
    def build_recall_query(contact_name: str, purpose: str = "") -> str:
        query = (
            f"What do we know about {contact_name} from previous meetings, including "
            "concerns, commitments, unresolved issues, preferences and recent changes?"
        )
        return f"{query} Upcoming meeting purpose: {purpose}" if purpose else query

    def recall_for_contact(self, contact_name: str) -> List[str]:
        """Recall everything Hindsight currently knows about a contact."""
        contact = require_text(contact_name, "a contact name")
        return self._memory.recall_memories(self.build_recall_query(contact))

    def reflect_on_contact(self, contact_name: str) -> str:
        """Ask Hindsight to reason about how its knowledge of a contact has evolved."""
        contact = require_text(contact_name, "a contact name")
        return self._memory.reflect_on_memories(
            f"Summarise what we know about {contact}: what concerns were raised, which were "
            "resolved, what commitments are still open, and what they are interested in now."
        )

    def prepare_meeting(
        self,
        contact_name: str,
        purpose: str,
        meeting_date: Optional[str] = None,
        extra_context: str = "",
    ) -> PreparationResult:
        """Memory -> Recall -> Reasoning -> Meeting brief."""
        contact = require_text(contact_name, "a contact name")
        purpose = require_text(purpose, "the meeting purpose")

        query = self.build_recall_query(contact, purpose)
        memories = self._memory.recall_memories(query)
        logger.info("Recalled %d memories for %s", len(memories), contact)

        prompt = build_brief_prompt(
            contact, purpose, meeting_date or "", extra_context.strip(), memories
        )
        brief = self._llm.generate_structured(BRIEF_SYSTEM_PROMPT, prompt, MeetingBrief)
        return PreparationResult(contact, query, memories, brief, purpose)

    def process_meeting(
        self, contact_name: str, meeting_date: str, title: str, notes: str
    ) -> ProcessingResult:
        """Notes -> Extraction -> Memory statements -> Retain in Hindsight."""
        contact = require_text(contact_name, "a contact name")
        meeting_date = require_text(meeting_date, "the meeting date")
        title = require_text(title, "a meeting title")
        notes = require_text(notes, "meeting notes")

        extraction = self._llm.generate_structured(
            EXTRACTION_SYSTEM_PROMPT,
            build_extraction_prompt(contact, meeting_date, title, notes),
            MeetingExtraction,
        )
        if extraction.is_empty():
            raise AgentError(
                "No useful information could be extracted from these notes. "
                "Try adding more detail (concerns, promises, decisions)."
            )

        statements = build_memory_statements(contact, meeting_date, title, extraction)
        retained, failed = self._retain_all(contact, meeting_date, statements)

        self._log.add(
            MeetingRecord(
                contact_name=contact,
                meeting_date=meeting_date,
                title=title,
                notes=notes,
                extraction=extraction,
                memory_statements=statements,
            )
        )
        warnings = [f"{failed} memory statement(s) could not be saved."] if failed else []
        return ProcessingResult(extraction, statements, retained, failed, warnings)

    def _retain_all(self, contact: str, meeting_date: str, statements: List[str]) -> tuple:
        """Retain each statement; fail fast if nothing could be stored."""
        timestamp = to_timestamp(meeting_date)
        context = f"Meeting notes for {contact}"
        retained = failed = 0
        for statement in statements:
            try:
                self._memory.retain_memory(statement, context=context, timestamp=timestamp)
                retained += 1
            except HindsightError:
                if retained == 0:
                    raise  # e.g. bad API key: no point trying the rest
                failed += 1
        return retained, failed
