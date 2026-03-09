from __future__ import annotations

import asyncio

from aiogram import Bot

from app.bot.bot import build_dispatcher
from app.bot.publisher import TelegramPublisher
from app.config import get_settings
from app.db.database import Database
from app.db.queries import ContentRepository, RuntimeSettingsRepository
from app.logger import setup_logging
from app.rubrics.argument_of_the_day import ArgumentOfTheDayRubric
from app.rubrics.roman_law_today import RomanLawTodayRubric
from app.scheduler.scheduler import build_scheduler
from app.services.openai_client import OpenAIClient


async def run() -> None:
    setup_logging()
    settings = get_settings()

    database = Database(settings.sqlite_path)
    database.init_db()
    repo = ContentRepository(database)
    runtime_repo = RuntimeSettingsRepository(database)
    runtime_repo.ensure_defaults({"auto_publish": "true" if settings.auto_publish else "false"})

    ai_client = OpenAIClient(settings.openai_api_key)
    rubrics = {
        "roman_law_today": RomanLawTodayRubric(settings.roman_dataset_path, repo),
        "argument_of_the_day": ArgumentOfTheDayRubric(settings.argument_dataset_path, repo, ai_client),
    }

    bot = Bot(token=settings.bot_token)
    publisher = TelegramPublisher(bot, settings, repo, runtime_repo)
    scheduler = build_scheduler(settings, publisher, repo, rubrics)
    scheduler.start()

    bot, dp = build_dispatcher(settings, repo, runtime_repo, rubrics, scheduler, ai_client, publisher)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(run())
