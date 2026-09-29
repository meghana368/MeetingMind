"""Pydantic models and result containers for MeetingMind."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_str_list(value: Any) -> List[str]:
    """Coerce messy LLM output (None, str, dicts, lists) into a list of strings."""
    if value is None:
        return []
    if isinstance(value, (str, dict)):
        value = [value]
    items: List[str] = []
    for item in value:
        if isinstance(item, dict):
            item = "; ".join(str(v) for v in item.values() if v)
        text = str(item).strip()
        if text:
            items.append(text)
    return items


class _LenientModel(BaseModel):
    """Base model that tolerates slightly malformed LLM JSON."""

    model_config = ConfigDict(extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def _coerce(cls, value: Any, info: Any) -> Any:
        annotation = cls.model_fields[info.field_name].annotation
        if annotation == List[str]:
            return _to_str_list(value)
        if annotation is str:
            return "" if value is None else str(value).strip()
        return value


class MeetingExtraction(_LenientModel):
    """Structured facts extracted from raw meeting notes."""

    topics: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    commitments: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    unresolved_issues: List[str] = Field(default_factory=list)
    outcomes: List[str] = Field(default_factory=list)
    resolved_issues: List[str] = Field(default_factory=list)

    def is_empty(self) -> bool:
        """True when nothing useful was extracted."""
        return not any(getattr(self, name) for name in type(self).model_fields)


class MeetingBrief(_LenientModel):
    """A personalised pre-meeting brief."""

    contact_context: str = ""
    previous_discussions: List[str] = Field(default_factory=list)
    open_commitments: List[str] = Field(default_factory=list)
    missed_followups: List[str] = Field(default_factory=list)
    current_concerns: List[str] = Field(default_factory=list)
    recent_changes: List[str] = Field(default_factory=list)
    suggested_agenda: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    important_reminders: List[str] = Field(default_factory=list)
    how_memory_shaped_this_brief: List[str] = Field(default_factory=list)


class MeetingRecord(BaseModel):
    """A processed meeting, kept in the local activity log for the UI."""

    contact_name: str
    meeting_date: str
    title: str
    notes: str
    extraction: MeetingExtraction
    memory_statements: List[str] = Field(default_factory=list)
    recorded_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )


@dataclass
class PreparationResult:
    """Everything the UI needs after preparing a meeting."""

    contact_name: str
    query: str
    recalled_memories: List[str]
    brief: MeetingBrief
    purpose: str = ""


@dataclass
class ProcessingResult:
    """Everything the UI needs after processing meeting notes."""

    extraction: MeetingExtraction
    memory_statements: List[str]
    retained_count: int
    failed_count: int = 0
    warnings: List[str] = field(default_factory=list)


# (field name, title, icon) - display order of brief sections in the UI.
BRIEF_SECTIONS: List[Tuple[str, str, str]] = [
    ("previous_discussions", "Previous Discussions", "🗂️"),
    ("open_commitments", "Open Commitments", "🤝"),
    ("missed_followups", "Missed Follow-ups", "⏰"),
    ("current_concerns", "Current Concerns", "⚠️"),
    ("recent_changes", "Recent Changes", "🔄"),
    ("suggested_agenda", "Suggested Agenda", "📋"),
    ("suggested_questions", "Suggested Questions", "❓"),
    ("important_reminders", "Important Reminders", "📌"),
]
