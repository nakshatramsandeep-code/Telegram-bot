"""Tests for config loading."""
import os
import pytest
from unittest.mock import patch

from src.config import load_config


BASE_ENV = {
    "TELEGRAM_BOT_TOKEN": "test-token",
    "LLM_API_KEY": "test-api-key",
}


def test_load_config_minimal():
    with patch.dict(os.environ, BASE_ENV, clear=True):
        config = load_config()
    assert config.telegram_token == "test-token"
    assert config.llm_provider == "anthropic"
    assert config.llm_api_key == "test-api-key"
    assert config.llm_model == "claude-opus-5-5"
    assert config.authorized_chat_id is None
    assert config.voice_file_path == "voice.txt"


def test_load_config_openai_defaults():
    env = {**BASE_ENV, "LLM_PROVIDER": "openai"}
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4o"


def test_load_config_custom_model():
    env = {**BASE_ENV, "LLM_PROVIDER": "anthropic", "LLM_MODEL": "claude-haiku-4-5-20251001"}
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.llm_model == "claude-haiku-4-5-20251001"


def test_load_config_authorized_chat_id():
    env = {**BASE_ENV, "AUTHORIZED_TELEGRAM_CHAT_ID": "987654321"}
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.authorized_chat_id == 987654321


def test_load_config_missing_token():
    with patch.dict(os.environ, {"LLM_API_KEY": "key"}, clear=True):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            load_config()


def test_load_config_missing_api_key():
    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "token"}, clear=True):
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            load_config()


def test_load_config_gemini_provider():
    env = {**BASE_ENV, "LLM_PROVIDER": "gemini"}
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.llm_provider == "gemini"
    assert config.llm_model == "gemini-2.5-flash"


def test_load_config_invalid_provider():
    env = {**BASE_ENV, "LLM_PROVIDER": "cohere"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError, match="LLM_PROVIDER"):
            load_config()
