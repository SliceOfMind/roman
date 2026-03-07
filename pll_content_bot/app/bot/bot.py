from __future__ import annotations

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.handlers import ModerationHandlers, router
from app.bot.publisher import TelegramPublisher
from app.config import Settings
from app.db.queries import ContentRepository, RuntimeSettingsRepository
from app.rubrics.base_rubric import BaseRubric
from app.services.openai_client import OpenAIClient


def build_dispatcher(
    settings: Settings,
    repo: ContentRepository,
    runtime_repo: RuntimeSettingsRepository,
    rubrics: dict[str, BaseRubric],
    scheduler: AsyncIOScheduler,
    ai_client: OpenAIClient,
    publisher: TelegramPublisher,
) -> tuple[Bot, Dispatcher]:
    bot = publisher.bot
    dp = Dispatcher()
    ModerationHandlers(
        repo=repo,
        runtime_repo=runtime_repo,
        rubrics=rubrics,
        channel_id=settings.channel_id,
        admin_chat_id=settings.admin_chat_id,
        sqlite_path=settings.sqlite_path,
        roman_dataset_path=settings.roman_dataset_path,
        argument_dataset_path=settings.argument_dataset_path,
        scheduler=scheduler,
        ai_client=ai_client,
        roman_post_hour=settings.roman_post_hour,
        argument_post_hour=settings.argument_post_hour,
        publisher=publisher,
    ).register(router)
    dp.include_router(router)
    return bot, dp
