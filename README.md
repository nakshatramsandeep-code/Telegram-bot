# Skinstinct LinkedIn Post Bot

A Telegram bot that turns Meera's raw notes into polished LinkedIn posts in her authentic voice.

## What it does

```
Meera types a note in Telegram
        ↓
Bot receives the message
        ↓
Reads voice.txt (Meera's voice reference)
        ↓
LLM generates a LinkedIn post in Meera's voice
        ↓
Bot replies in the same Telegram chat
```

No dashboards. No databases. No scheduling. Just: raw note → LinkedIn post.

---

## Requirements

- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- An Anthropic or OpenAI API key

---

## Installation

```bash
git clone <repo-url>
cd mesa-ai-track-telegram
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `LLM_PROVIDER` | No | `anthropic` (default) or `openai` |
| `LLM_API_KEY` | Yes | API key for the chosen provider |
| `LLM_MODEL` | No | Model ID (defaults: `claude-opus-5-5` / `gpt-4o`) |
| `AUTHORIZED_TELEGRAM_CHAT_ID` | No | Only process messages from this chat ID |
| `VOICE_FILE_PATH` | No | Path to voice.txt (default: `voice.txt`) |

### Getting your Telegram chat ID

Send a message to your bot, then visit:
```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```
Look for `"chat": {"id": ...}` in the response.

---

## How to run locally

```bash
python main.py
```

The bot will start polling Telegram. Send it a message and it will reply with a generated LinkedIn post.

---

## voice.txt

`voice.txt` lives in the project root. It contains Meera's voice profile - writing style, vocabulary, structure, and formatting rules.

**The bot reads this file dynamically on every request.** Update it any time; the next generated post will use the new version automatically.

To use a different path, set `VOICE_FILE_PATH` in `.env`.

---

## How to test generation locally (no Telegram needed)

Run the local test script with a sample note:

```bash
python scripts/test_local.py "I was at the manufacturing unit today and noticed that customers keep asking us why our product has fewer ingredients."
```

Or without arguments to use the built-in sample:

```bash
python scripts/test_local.py
```

---

## How to run the test suite

```bash
pytest
```

All tests mock the LLM and Telegram so no API keys are needed.

---

## Troubleshooting

**Bot does not respond**
- Check `TELEGRAM_BOT_TOKEN` is correct
- Make sure the bot has been added to the chat and has permission to send messages
- If `AUTHORIZED_TELEGRAM_CHAT_ID` is set, confirm the chat ID matches

**`voice.txt not found` error**
- Ensure `voice.txt` exists in the project root (or wherever `VOICE_FILE_PATH` points)

**`Couldn't generate the post right now`**
- Check `LLM_API_KEY` is valid and has quota
- Check `LLM_PROVIDER` and `LLM_MODEL` are correct
- Check the logs for the underlying error

**Long posts**
- Posts longer than 4096 characters are automatically split across multiple messages at paragraph/sentence boundaries.
