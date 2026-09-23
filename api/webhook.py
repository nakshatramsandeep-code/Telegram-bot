import asyncio
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import telegram

from src.config import load_config
from src.ai.generator import generate_linkedin_post
from src.telegram.bot import split_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            asyncio.run(_handle_update(body))
        except Exception as exc:
            logger.error("Unhandled error in webhook: %s", exc)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # suppress default access logs


async def _handle_update(body: bytes) -> None:
    data = json.loads(body)

    message = data.get("message")
    if not message or not message.get("text"):
        return

    text: str = message["text"]
    if text.startswith("/"):
        return

    chat_id: int = message["chat"]["id"]
    message_id: int = message["message_id"]

    config = load_config()

    if config.authorized_chat_id and chat_id != config.authorized_chat_id:
        logger.warning("Ignored message from unauthorized chat_id=%s", chat_id)
        return

    logger.info("Webhook message received (chat_id=%s, length=%d)", chat_id, len(text))

    bot = telegram.Bot(config.telegram_token)
    async with bot:
        sent = await bot.send_message(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            text="Writing your post...",
        )

        try:
            post = generate_linkedin_post(
                raw_note=text,
                voice_file_path=config.voice_file_path,
                llm_provider=config.llm_provider,
                llm_api_key=config.llm_api_key,
                llm_model=config.llm_model,
            )
            parts = split_message(post)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent.message_id,
                text=parts[0],
            )
            for part in parts[1:]:
                await bot.send_message(chat_id=chat_id, text=part)

            logger.info("Response sent (chat_id=%s, parts=%d)", chat_id, len(parts))

        except FileNotFoundError as exc:
            logger.error("voice.txt missing: %s", exc)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent.message_id,
                text="Couldn't generate the post right now. Please try again.",
            )
        except Exception as exc:
            logger.error("Generation failed (chat_id=%s): %s", chat_id, exc)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent.message_id,
                text="Couldn't generate the post right now. Please try again.",
            )
