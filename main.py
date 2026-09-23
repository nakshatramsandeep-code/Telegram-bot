import logging

from dotenv import load_dotenv

load_dotenv()

from src.config import load_config
from src.telegram.bot import create_bot

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)

if __name__ == "__main__":
    config = load_config()
    app = create_bot(config)
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)
