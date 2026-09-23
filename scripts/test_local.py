"""
Local generation test - runs the full voice.txt + LLM pipeline
without needing a Telegram message.

Usage:
    python scripts/test_local.py "Your raw note here"
    python scripts/test_local.py  # uses the built-in sample note
"""
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.config import load_config
from src.ai.generator import generate_linkedin_post

SAMPLE_NOTE = (
    "I was at the manufacturing unit today and noticed that customers keep asking us "
    "why our product has fewer ingredients. I think people assume more ingredients "
    "means the product is more effective."
)


def main():
    raw_note = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE_NOTE

    print("=" * 60)
    print("RAW NOTE:")
    print(raw_note)
    print("=" * 60)

    config = load_config()

    print(f"\nProvider : {config.llm_provider}")
    print(f"Model    : {config.llm_model}")
    print(f"Voice    : {config.voice_file_path}")
    print("\nGenerating...\n")

    post = generate_linkedin_post(
        raw_note=raw_note,
        voice_file_path=config.voice_file_path,
        llm_provider=config.llm_provider,
        llm_api_key=config.llm_api_key,
        llm_model=config.llm_model,
    )

    print("=" * 60)
    print("GENERATED LINKEDIN POST:")
    print("=" * 60)
    print(post)
    print("=" * 60)
    print(f"\nWord count : {len(post.split())}")
    print(f"Char count : {len(post)}")


if __name__ == "__main__":
    main()
