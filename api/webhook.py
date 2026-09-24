import asyncio
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import telegram

from src.config import load_config
from src.telegram.handler import process_note
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

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook is live.")

    def log_message(self, format, *args):
        pass


async def _handle_update(body: bytes) -> None:
    data = json.loads(body)

    message = data.get("message") or data.get("channel_post")
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

    async with telegram.Bot(config.telegram_token) as bot:
        await process_note(
            bot=bot,
            chat_id=chat_id,
            reply_to_message_id=message_id,
            raw_note=text,
            config=config,
        )
