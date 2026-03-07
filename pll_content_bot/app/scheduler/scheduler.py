from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.bot.publisher import TelegramPublisher
from app.config import Settings
from app.db.queries import ContentRepository
from app.rubrics.base_rubric import BaseRubric
from app.scheduler.jobs import run_rubric_job


def build_scheduler(
    settings: Settings,
    publisher: TelegramPublisher,
    repo: ContentRepository,
    rubrics: dict[str, BaseRubric],
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_rubric_job,
        CronTrigger(hour=settings.roman_post_hour, minute=0),
        kwargs={"rubric": rubrics["roman_law_today"], "publisher": publisher, "repo": repo},
        id="roman_law_today_job",
        replace_existing=True,
    )
    scheduler.add_job(
        run_rubric_job,
        CronTrigger(hour=settings.argument_post_hour, minute=0),
        kwargs={"rubric": rubrics["argument_of_the_day"], "publisher": publisher, "repo": repo},
        id="argument_of_the_day_job",
        replace_existing=True,
    )
    return scheduler
