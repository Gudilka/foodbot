from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    app_env: str
    log_level: str


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    return Settings(
        bot_token=bot_token,
        database_url=database_url,
        app_env=os.getenv("APP_ENV", "local").strip() or "local",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip() or "INFO",
    )
