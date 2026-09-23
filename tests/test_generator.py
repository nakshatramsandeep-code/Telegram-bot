"""Tests for the AI post generator and message splitting."""
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ai.generator import generate_linkedin_post, load_voice_reference
from src.telegram.bot import split_message


# ---------------------------------------------------------------------------
# load_voice_reference
# ---------------------------------------------------------------------------

def test_load_voice_reference_success(tmp_path):
    voice_file = tmp_path / "voice.txt"
    voice_file.write_text("This is the voice reference.", encoding="utf-8")
    result = load_voice_reference(str(voice_file))
    assert result == "This is the voice reference."


def test_load_voice_reference_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="voice.txt not found"):
        load_voice_reference(str(tmp_path / "nonexistent.txt"))


# ---------------------------------------------------------------------------
# generate_linkedin_post
# ---------------------------------------------------------------------------

def test_generate_post_anthropic_success(tmp_path):
    voice_file = tmp_path / "voice.txt"
    voice_file.write_text("Voice reference content.", encoding="utf-8")

    with patch("src.ai.generator._call_anthropic", return_value="Generated LinkedIn post.") as mock_call:
        post = generate_linkedin_post(
            raw_note="My raw thought.",
            voice_file_path=str(voice_file),
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model="claude-test",
        )

    assert post == "Generated LinkedIn post."
    mock_call.assert_called_once()
    _, _, user_prompt = mock_call.call_args[0]
    assert "Voice reference content." in user_prompt
    assert "My raw thought." in user_prompt


def test_generate_post_openai_success(tmp_path):
    voice_file = tmp_path / "voice.txt"
    voice_file.write_text("Voice reference content.", encoding="utf-8")

    with patch("src.ai.generator._call_openai", return_value="OpenAI post.") as mock_call:
        post = generate_linkedin_post(
            raw_note="My raw thought.",
            voice_file_path=str(voice_file),
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4o",
        )

    assert post == "OpenAI post."
    mock_call.assert_called_once()


def test_generate_post_voice_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        generate_linkedin_post(
            raw_note="Some note.",
            voice_file_path=str(tmp_path / "missing.txt"),
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model="claude-test",
        )


def test_generate_post_llm_failure(tmp_path):
    voice_file = tmp_path / "voice.txt"
    voice_file.write_text("Voice reference.", encoding="utf-8")

    with patch("src.ai.generator._call_anthropic", side_effect=Exception("API error")):
        with pytest.raises(Exception, match="API error"):
            generate_linkedin_post(
                raw_note="Some note.",
                voice_file_path=str(voice_file),
                llm_provider="anthropic",
                llm_api_key="test-key",
                llm_model="claude-test",
            )


def test_generate_post_gemini_success(tmp_path):
    voice_file = tmp_path / "voice.txt"
    voice_file.write_text("Voice reference content.", encoding="utf-8")

    with patch("src.ai.generator._call_gemini", return_value="Gemini post.") as mock_call:
        post = generate_linkedin_post(
            raw_note="My raw thought.",
            voice_file_path=str(voice_file),
            llm_provider="gemini",
            llm_api_key="test-key",
            llm_model="gemini-2.5-flash",
        )

    assert post == "Gemini post."
    mock_call.assert_called_once()


def test_generate_post_unsupported_provider(tmp_path):
    voice_file = tmp_path / "voice.txt"
    voice_file.write_text("Voice reference.", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        generate_linkedin_post(
            raw_note="Some note.",
            voice_file_path=str(voice_file),
            llm_provider="cohere",
            llm_api_key="test-key",
            llm_model="some-model",
        )


# ---------------------------------------------------------------------------
# split_message
# ---------------------------------------------------------------------------

def test_split_message_short():
    text = "This is a short post."
    assert split_message(text) == [text]


def test_split_message_long_splits_at_paragraph():
    para1 = "A" * 100
    para2 = "B" * 100
    text = para1 + "\n\n" + para2
    parts = split_message(text, max_length=120)
    assert len(parts) == 2
    assert parts[0] == para1
    assert parts[1] == para2


def test_split_message_very_long_no_breaks():
    text = "x" * 10000
    parts = split_message(text, max_length=4096)
    assert all(len(p) <= 4096 for p in parts)
    assert "".join(parts) == text


def test_split_message_empty():
    assert split_message("") == []


def test_split_message_exact_limit():
    text = "x" * 4096
    parts = split_message(text)
    assert parts == [text]
