from __future__ import annotations

from aiogram import Bot, Dispatcher

from app.bot.handlers import ModerationHandlers, router
from app.config import Settings
from app.db.queries import ContentRepository
from app.rubrics.base_rubric import BaseRubric


def build_dispatcher(settings: Settings, repo: ContentRepository, rubrics: dict[str, BaseRubric]) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    ModerationHandlers(repo=repo, rubrics=rubrics, channel_id=settings.channel_id).register(router)
    dp.include_router(router)
    return bot, dp
