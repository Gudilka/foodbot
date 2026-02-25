from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import load_settings
from bot.db.bootstrap import bootstrap_database
from bot.db.health import db_health_check
from bot.db.session import build_engine, build_session_factory
from bot.fsm.storage import DatabaseFSMStorage
from bot.handlers import create_registration_router
from bot.services import RegistrationService


async def run() -> None:
    settings = load_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    storage = DatabaseFSMStorage(session_factory)

    await bootstrap_database(engine, session_factory)

    async with session_factory() as session:
        await db_health_check(session)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="profile", description="Показать профиль"),
            BotCommand(command="edit_profile", description="Редактировать профиль"),
            BotCommand(command="cancel", description="Отменить анкету"),
        ]
    )

    dispatcher = Dispatcher(storage=storage)
    service = RegistrationService(session_factory=session_factory)
    dispatcher.include_router(create_registration_router(service))

    try:
        await dispatcher.start_polling(bot)
    finally:
        await storage.close()
        await bot.session.close()
        await engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
