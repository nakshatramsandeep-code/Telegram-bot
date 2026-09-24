import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from src.utils.logger import get_logger

logger = get_logger(__name__)

_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
_BASE_QUERY = "skincare beauty D2C India founders startup"


def _note_keywords(note: str) -> str:
    """Use the first 6 words of the note as extra query context."""
    words = note.split()[:6]
    return " ".join(words)


def fetch_industry_news(raw_note: str, max_results: int = 3) -> list[dict]:
    """Fetch top Google News articles relevant to the note. Never raises."""
    query = f"{_note_keywords(raw_note)} {_BASE_QUERY}"
    url = _RSS_URL.format(query=quote_plus(query))
    logger.info("Fetching news: %s", query)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml_bytes = resp.read()

        root = ET.fromstring(xml_bytes)
        channel = root.find("channel")
        if channel is None:
            return []

        articles = []
        for item in channel.findall("item")[:max_results]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if title:
                articles.append({"title": title, "url": link})

        logger.info("Fetched %d articles", len(articles))
        return articles

    except Exception as exc:
        logger.warning("News fetch failed, continuing without news: %s", exc)
        return []


def build_news_context(articles: list[dict]) -> str:
    """Format articles into a string for the LLM prompt."""
    if not articles:
        return ""
    lines = ["RELEVANT INDUSTRY NEWS (use for context and relevance only — do not copy headlines):"]
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. {a['title']}")
    return "\n".join(lines)
