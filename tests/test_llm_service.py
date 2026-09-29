from types import SimpleNamespace

import pytest

from models.meeting import MeetingExtraction
from services.llm_service import LLMService, parse_json_object
from utils.config import load_settings
from utils.errors import LLMError


class FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)

    def create(self, **kwargs):
        content = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _service(replies):
    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(replies)))
    return LLMService(load_settings({"GROQ_API_KEY": "x"}), client=client)


def test_parse_json_strips_fences_and_chatter():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Sure! {"a": 2} hope it helps') == {"a": 2}


def test_malformed_output_is_retried():
    service = _service(["not json at all", '{"concerns": ["timeline"]}'])
    result = service.generate_structured("sys", "user", MeetingExtraction)
    assert result.concerns == ["timeline"]


def test_persistently_bad_output_raises_friendly_error():
    service = _service(["nope", "still nope"])
    with pytest.raises(LLMError):
        service.generate_structured("sys", "user", MeetingExtraction)


def test_missing_key_message():
    service = LLMService(load_settings({}))
    with pytest.raises(LLMError, match="GROQ_API_KEY"):
        service.generate_structured("s", "u", MeetingExtraction)
