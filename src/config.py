import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    telegram_token: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    authorized_chat_id: Optional[int]
    voice_file_path: str


def load_config() -> Config:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    llm_provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if llm_provider not in ("anthropic", "openai", "gemini"):
        raise ValueError(f"LLM_PROVIDER must be 'anthropic', 'openai', or 'gemini', got: {llm_provider}")

    llm_api_key = os.environ.get("LLM_API_KEY")
    if not llm_api_key:
        raise ValueError("LLM_API_KEY is required")

    defaults = {"anthropic": "claude-opus-5-5", "openai": "gpt-4o", "gemini": "gemini-2.5-flash"}
    default_model = defaults.get(llm_provider, "gemini-2.5-flash")
    llm_model = os.environ.get("LLM_MODEL", default_model)

    authorized_chat_id_str = os.environ.get("AUTHORIZED_TELEGRAM_CHAT_ID", "").strip()
    authorized_chat_id = int(authorized_chat_id_str) if authorized_chat_id_str else None

    voice_file_path = os.environ.get("VOICE_FILE_PATH", "voice.txt")

    return Config(
        telegram_token=token,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        authorized_chat_id=authorized_chat_id,
        voice_file_path=voice_file_path,
    )
