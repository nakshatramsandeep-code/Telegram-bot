import telegram

from src.ai.generator import generate_linkedin_post
from src.ai.scorer import score_note
from src.config import Config
from src.news.fetcher import build_news_context, fetch_industry_news
from src.telegram.bot import split_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _score_bar(score: int) -> str:
    return "▓" * score + "░" * (10 - score)


def _rejection_text(score: int, reason: str) -> str:
    bar = _score_bar(score)
    safe_reason = _escape_html(reason)
    return (
        f"🔍 <b>Note scored {score}/10</b>\n\n"
        f"<code>{bar}</code>\n\n"
        f"<i>{safe_reason}</i>\n\n"
        f"Try adding a specific example, number, or observation."
    )


async def process_note(
    bot: telegram.Bot,
    chat_id: int,
    reply_to_message_id: int,
    raw_note: str,
    config: Config,
) -> None:
    """Full pipeline: score → (reject or fetch news + generate) → reply."""
    sent = await bot.send_message(
        chat_id=chat_id,
        reply_to_message_id=reply_to_message_id,
        text="Reviewing your note...",
    )
    sent_id = sent.message_id

    try:
        score, reason = score_note(
            raw_note=raw_note,
            llm_provider=config.llm_provider,
            llm_api_key=config.llm_api_key,
            llm_model=config.llm_model,
        )

        if score < config.post_score_threshold:
            logger.info("Note rejected (score=%d, threshold=%d)", score, config.post_score_threshold)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent_id,
                text=_rejection_text(score, reason),
                parse_mode="HTML",
            )
            return

        logger.info("Note accepted (score=%d) — generating post", score)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_id,
            text="Writing your post...",
        )

        articles = fetch_industry_news(raw_note)
        news_context = build_news_context(articles)

        post = generate_linkedin_post(
            raw_note=raw_note,
            voice_file_path=config.voice_file_path,
            llm_provider=config.llm_provider,
            llm_api_key=config.llm_api_key,
            llm_model=config.llm_model,
            news_context=news_context,
        )

        parts = split_message(post)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_id,
            text=parts[0],
        )
        for part in parts[1:]:
            await bot.send_message(chat_id=chat_id, text=part)

        logger.info("Post sent (chat_id=%s, score=%d, parts=%d)", chat_id, score, len(parts))

    except FileNotFoundError as exc:
        logger.error("voice.txt missing: %s", exc)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_id,
            text="Couldn't generate the post right now. Please try again.",
        )
    except Exception as exc:
        logger.error("Processing failed (chat_id=%s): %s", chat_id, exc)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=sent_id,
            text="Couldn't generate the post right now. Please try again.",
        )
