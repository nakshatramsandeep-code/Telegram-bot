"""Tests for the Telegram bot handler."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.telegram.bot import handle_message, split_message
from src.config import Config


def make_config(authorized_chat_id=None, voice_file_path="voice.txt"):
    return Config(
        telegram_token="fake-token",
        llm_provider="anthropic",
        llm_api_key="fake-key",
        llm_model="claude-test",
        authorized_chat_id=authorized_chat_id,
        voice_file_path=voice_file_path,
    )


def make_update(chat_id: int, text: str) -> MagicMock:
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.message.text = text
    update.message.reply_text = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    return update


def make_context(config: Config) -> MagicMock:
    context = MagicMock()
    context.application.bot_data = {"config": config}
    context.bot.send_message = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_handle_message_success():
    config = make_config()
    update = make_update(chat_id=123, text="My raw thought.")
    context = make_context(config)

    with patch("src.telegram.bot.generate_linkedin_post", return_value="Generated post."):
        await handle_message(update, context)

    update.message.reply_text.assert_called_once_with("Writing your post...")
    processing_msg = update.message.reply_text.return_value
    processing_msg.edit_text.assert_called_once_with("Generated post.")


@pytest.mark.asyncio
async def test_handle_message_unauthorized_chat():
    config = make_config(authorized_chat_id=999)
    update = make_update(chat_id=123, text="My raw thought.")
    context = make_context(config)

    with patch("src.telegram.bot.generate_linkedin_post") as mock_gen:
        await handle_message(update, context)

    mock_gen.assert_not_called()
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_authorized_chat():
    config = make_config(authorized_chat_id=123)
    update = make_update(chat_id=123, text="Authorized note.")
    context = make_context(config)

    with patch("src.telegram.bot.generate_linkedin_post", return_value="Post."):
        await handle_message(update, context)

    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_voice_missing():
    config = make_config()
    update = make_update(chat_id=123, text="Note.")
    context = make_context(config)

    with patch(
        "src.telegram.bot.generate_linkedin_post",
        side_effect=FileNotFoundError("voice.txt not found"),
    ):
        await handle_message(update, context)

    processing_msg = update.message.reply_text.return_value
    processing_msg.edit_text.assert_called_once_with(
        "Couldn't generate the post right now. Please try again."
    )


@pytest.mark.asyncio
async def test_handle_message_llm_failure():
    config = make_config()
    update = make_update(chat_id=123, text="Note.")
    context = make_context(config)

    with patch(
        "src.telegram.bot.generate_linkedin_post",
        side_effect=Exception("API error"),
    ):
        await handle_message(update, context)

    processing_msg = update.message.reply_text.return_value
    processing_msg.edit_text.assert_called_once_with(
        "Couldn't generate the post right now. Please try again."
    )


@pytest.mark.asyncio
async def test_handle_message_long_post_splits():
    config = make_config()
    update = make_update(chat_id=123, text="Note.")
    context = make_context(config)

    # Generate a post that exceeds Telegram's 4096-char limit
    long_post = ("Word " * 1000).strip()  # ~5000 chars

    with patch("src.telegram.bot.generate_linkedin_post", return_value=long_post):
        await handle_message(update, context)

    processing_msg = update.message.reply_text.return_value
    processing_msg.edit_text.assert_called_once()
    # Additional parts sent via send_message
    assert context.bot.send_message.call_count >= 1


@pytest.mark.asyncio
async def test_handle_multiple_messages_independent():
    """Each message triggers its own independent generation request."""
    config = make_config()

    update1 = make_update(chat_id=1, text="Note one.")
    update2 = make_update(chat_id=2, text="Note two.")
    context1 = make_context(config)
    context2 = make_context(config)

    call_order = []

    def fake_gen(raw_note, **kwargs):
        call_order.append(raw_note)
        return f"Post for: {raw_note}"

    with patch("src.telegram.bot.generate_linkedin_post", side_effect=fake_gen):
        await handle_message(update1, context1)
        await handle_message(update2, context2)

    assert len(call_order) == 2
    assert "Note one." in call_order[0]
    assert "Note two." in call_order[1]

    msg1 = update1.message.reply_text.return_value
    msg1.edit_text.assert_called_once_with("Post for: Note one.")
    msg2 = update2.message.reply_text.return_value
    msg2.edit_text.assert_called_once_with("Post for: Note two.")
