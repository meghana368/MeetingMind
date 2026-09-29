from utils.config import DEFAULT_GROQ_MODEL, load_settings


def test_missing_keys_reported_without_leaking_values():
    problems = load_settings({}).missing_configuration()
    assert any("GROQ_API_KEY" in p for p in problems)
    assert any("HINDSIGHT_API_KEY" in p for p in problems)


def test_complete_configuration_has_no_problems():
    settings = load_settings({"GROQ_API_KEY": "g", "HINDSIGHT_API_KEY": "h"})
    assert settings.missing_configuration() == []
    assert settings.groq_model == DEFAULT_GROQ_MODEL


def test_local_hindsight_needs_no_key():
    settings = load_settings({"GROQ_API_KEY": "g", "HINDSIGHT_BASE_URL": "http://localhost:8888"})
    assert settings.missing_configuration() == []


def test_model_and_bank_are_configurable():
    settings = load_settings({"GROQ_MODEL": "my-model", "HINDSIGHT_BANK_ID": "bank-x"})
    assert settings.groq_model == "my-model"
    assert settings.hindsight_bank_id == "bank-x"
