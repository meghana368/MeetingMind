from models.meeting import MeetingBrief, MeetingExtraction


def test_extraction_coerces_messy_llm_output():
    ex = MeetingExtraction.model_validate(
        {"concerns": "timeline", "commitments": [{"who": "user", "what": "send proposal"}],
         "topics": None, "unexpected": 1}
    )
    assert ex.concerns == ["timeline"]
    assert ex.commitments == ["user; send proposal"]
    assert ex.topics == []


def test_extraction_is_empty():
    assert MeetingExtraction().is_empty()
    assert not MeetingExtraction(concerns=["x"]).is_empty()


def test_brief_defaults_and_coercion():
    brief = MeetingBrief.model_validate({"contact_context": None, "suggested_agenda": "Demo"})
    assert brief.contact_context == ""
    assert brief.suggested_agenda == ["Demo"]
    assert brief.open_commitments == []
