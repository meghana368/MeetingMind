"""Agent workflow tests with fake Hindsight + fake LLM (no network, no keys)."""
from unittest.mock import MagicMock

import pytest

from agent.meeting_agent import MeetingAgent
from models.meeting import MeetingBrief, MeetingExtraction
from services.meeting_service import MeetingLog
from utils.errors import AgentError, HindsightError, InputValidationError


class FakeMemory:
    """In-memory stand-in for HindsightService."""

    def __init__(self):
        self.store = []

    def retain_memory(self, content, context=None, timestamp=None):
        self.store.append(content)

    def recall_memories(self, query, max_results=30):
        return list(self.store)


def _agent(tmp_path, llm, memory=None):
    return MeetingAgent(memory or FakeMemory(), llm, MeetingLog(tmp_path / "log.json"))


def test_prepare_requires_contact_and_purpose(tmp_path):
    agent = _agent(tmp_path, MagicMock())
    with pytest.raises(InputValidationError):
        agent.prepare_meeting("", "purpose")
    with pytest.raises(InputValidationError):
        agent.prepare_meeting("Sarah", "  ")


def test_process_requires_notes(tmp_path):
    with pytest.raises(InputValidationError):
        _agent(tmp_path, MagicMock()).process_meeting("Sarah", "2026-09-01", "t", "")


def test_retain_then_recall_feeds_the_brief(tmp_path):
    memory = FakeMemory()
    llm = MagicMock()
    llm.generate_structured.side_effect = [
        MeetingExtraction(concerns=["implementation timeline"],
                          commitments=["The user promised the implementation proposal"]),
        MeetingBrief(contact_context="ctx"),
    ]
    agent = _agent(tmp_path, llm, memory)

    result = agent.process_meeting("Sarah Johnson", "2026-09-01", "Call 1", "notes")
    assert result.retained_count == 2 and len(memory.store) == 2
    assert agent.log.for_contact("Sarah Johnson")

    prep = agent.prepare_meeting("Sarah Johnson", "Follow-up")
    assert prep.recalled_memories == memory.store
    brief_prompt = llm.generate_structured.call_args_list[1].args[1]
    assert "implementation proposal" in brief_prompt  # recalled memory reached the LLM


def test_empty_extraction_is_rejected(tmp_path):
    llm = MagicMock()
    llm.generate_structured.return_value = MeetingExtraction()
    with pytest.raises(AgentError):
        _agent(tmp_path, llm).process_meeting("Sarah", "2026-09-01", "t", "hi")


def test_total_hindsight_failure_propagates_and_is_not_logged(tmp_path):
    llm = MagicMock()
    llm.generate_structured.return_value = MeetingExtraction(concerns=["x"])
    memory = MagicMock()
    memory.retain_memory.side_effect = HindsightError("Hindsight rejected the API key.")
    agent = _agent(tmp_path, llm, memory)
    with pytest.raises(HindsightError):
        agent.process_meeting("Sarah", "2026-09-01", "t", "notes")
    assert agent.log.all() == []
