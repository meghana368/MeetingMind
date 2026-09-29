import pytest

from models.meeting import MeetingExtraction, MeetingRecord
from services.meeting_service import MeetingLog, build_memory_statements, require_text, to_timestamp
from utils.errors import InputValidationError


def test_memory_statements_are_dated_and_name_the_contact():
    ex = MeetingExtraction(
        topics=["timeline"], concerns=["implementation timeline"],
        commitments=["The user promised a proposal"], resolved_issues=["timeline concern resolved"],
    )
    statements = build_memory_statements("Sarah Johnson", "2026-09-15", "Follow-up", ex)
    assert len(statements) == 4
    assert all(s.startswith("[2026-09-15] Meeting with Sarah Johnson") for s in statements)
    assert any("RESOLVED" in s and "timeline concern resolved" in s for s in statements)


def test_require_text_rejects_blank():
    with pytest.raises(InputValidationError):
        require_text("   ", "a contact name")
    assert require_text(" Sarah ", "a contact name") == "Sarah"


def test_to_timestamp():
    assert to_timestamp("2026-09-01") == "2026-09-01T09:00:00Z"
    assert to_timestamp("not a date") is None


def test_meeting_log_roundtrip_and_ordering(tmp_path):
    log = MeetingLog(tmp_path / "log.json")
    for date in ("2026-09-15", "2026-09-01"):
        log.add(MeetingRecord(contact_name="Sarah Johnson", meeting_date=date, title="m",
                              notes="n", extraction=MeetingExtraction(topics=["t"])))
    records = log.for_contact("sarah johnson")
    assert [r.meeting_date for r in records] == ["2026-09-01", "2026-09-15"]
    assert log.contacts() == ["Sarah Johnson"]
    log.reset()
    assert log.all() == []


def test_meeting_log_survives_corrupt_file(tmp_path):
    path = tmp_path / "log.json"
    path.write_text("{not json", encoding="utf-8")
    assert MeetingLog(path).all() == []
