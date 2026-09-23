from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from src.ai.generator import generate_linkedin_post
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

TELEGRAM_MAX_LENGTH = 4096


def split_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Split text at paragraph/sentence boundaries to fit Telegram limits."""
    if not text:
        return []
    if len(text) <= max_length:
        return [text]

    parts = []
    remaining = text
    while remaining:
        if len(remaining) <= max_length:
            parts.append(remaining)
            break

        # Prefer paragraph break, then line break, then sentence end, then hard cut
        split_at = max_length
        for sep in ("\n\n", "\n", ". ", " "):
            idx = remaining.rfind(sep, 0, max_length)
            if idx != -1:
                split_at = idx + len(sep)
                break

        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    return [p for p in parts if p]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: Config = context.application.bot_data["config"]
    chat_id = update.effective_chat.id

    if config.authorized_chat_id and chat_id != config.authorized_chat_id:
        logger.warning("Ignored message from unauthorized chat_id=%s", chat_id)
        return

    if not update.message or not update.message.text:
        return

    raw_note = update.message.text
    logger.info("Telegram message received (chat_id=%s, length=%d)", chat_id, len(raw_note))

    processing_msg = await update.message.reply_text("Writing your post...")

    try:
        post = generate_linkedin_post(
            raw_note=raw_note,
            voice_file_path=config.voice_file_path,
            llm_provider=config.llm_provider,
            llm_api_key=config.llm_api_key,
            llm_model=config.llm_model,
        )

        parts = split_message(post)

        await processing_msg.edit_text(parts[0])
        for part in parts[1:]:
            await context.bot.send_message(chat_id=chat_id, text=part)

        logger.info("Response sent (chat_id=%s, parts=%d)", chat_id, len(parts))

    except FileNotFoundError as exc:
        logger.error("voice.txt missing: %s", exc)
        await processing_msg.edit_text(
            "Couldn't generate the post right now. Please try again."
        )
    except Exception as exc:
        logger.error("Generation failed (chat_id=%s): %s", chat_id, exc)
        await processing_msg.edit_text(
            "Couldn't generate the post right now. Please try again."
        )


def create_bot(config: Config) -> Application:
    app = Application.builder().token(config.telegram_token).build()
    app.bot_data["config"] = config
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
