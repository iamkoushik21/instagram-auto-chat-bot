"""Centralised configuration loaded from environment variables / .env file."""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
    return value


# Instagram credentials
INSTAGRAM_USERNAME: str = _require("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD: str = _require("INSTAGRAM_PASSWORD")

# OpenAI
OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Bot behaviour
BOT_SYSTEM_PROMPT: str = os.getenv(
    "BOT_SYSTEM_PROMPT",
    "You are a friendly and helpful Instagram assistant. Reply concisely and warmly.",
)
POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "30"))
MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "10"))
