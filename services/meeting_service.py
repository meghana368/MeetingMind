"""Meeting business logic: input validation, memory formatting, local activity log."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.meeting import MeetingExtraction, MeetingRecord
from utils.errors import InputValidationError

logger = logging.getLogger(__name__)

# (extraction field, label used inside the memory statement)
MEMORY_LABELS = [
    ("decisions", "Decision made"),
    ("commitments", "Commitment (open until fulfilled)"),
    ("concerns", "Concern raised"),
    ("action_items", "Action item (pending)"),
    ("preferences", "Preference / important fact"),
    ("unresolved_issues", "Unresolved issue (still open)"),
    ("outcomes", "Outcome"),
    ("resolved_issues", "RESOLVED / COMPLETED - no longer open"),
]


def require_text(value: Optional[str], label: str) -> str:
    """Return stripped text or raise a friendly validation error."""
    cleaned = (value or "").strip()
    if not cleaned:
        raise InputValidationError(f"Please enter {label}.")
    return cleaned


def to_timestamp(meeting_date: str) -> Optional[str]:
    """Convert YYYY-MM-DD into an ISO timestamp for Hindsight (None if invalid)."""
    try:
        return datetime.fromisoformat(meeting_date).strftime("%Y-%m-%dT09:00:00Z")
    except ValueError:
        return None


def build_memory_statements(
    contact_name: str, meeting_date: str, title: str, extraction: MeetingExtraction
) -> List[str]:
    """Turn an extraction into self-contained, dated memory statements.

    Each statement names the contact and date so it still makes sense on its own
    when Hindsight recalls it months later, and so the LLM can order them in time.
    """
    prefix = f"[{meeting_date}] Meeting with {contact_name} ('{title}')"
    statements: List[str] = []
    if extraction.topics:
        statements.append(f"{prefix} - Topics discussed: {'; '.join(extraction.topics)}.")
    for field_name, label in MEMORY_LABELS:
        for item in getattr(extraction, field_name):
            statements.append(f"{prefix} - {label}: {item}")
    return statements


class MeetingLog:
    """Small JSON log of processed meetings, used only for UI display.

    Hindsight remains the source of truth for what the agent recalls.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def all(self) -> List[MeetingRecord]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return [MeetingRecord.model_validate(item) for item in raw]
        except (OSError, ValueError) as exc:
            logger.warning("Could not read meeting log (%s); starting empty.", exc)
            return []

    def add(self, record: MeetingRecord) -> None:
        records = self.all() + [record]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([r.model_dump() for r in records], indent=2)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self._path)

    def for_contact(self, contact_name: str) -> List[MeetingRecord]:
        key = contact_name.strip().casefold()
        matches = [r for r in self.all() if r.contact_name.strip().casefold() == key]
        return sorted(matches, key=lambda r: (r.meeting_date, r.recorded_at))

    def contacts(self) -> List[str]:
        """Contact names, most recently active first (case-insensitive unique)."""
        seen, names = set(), []
        for record in sorted(self.all(), key=lambda r: r.recorded_at, reverse=True):
            key = record.contact_name.strip().casefold()
            if key not in seen:
                seen.add(key)
                names.append(record.contact_name)
        return names

    def reset(self) -> None:
        if self._path.exists():
            self._path.unlink()
