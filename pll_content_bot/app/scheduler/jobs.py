from __future__ import annotations

import logging

from app.bot.publisher import TelegramPublisher
from app.db.models import ContentStatus
from app.db.queries import ContentRepository
from app.rubrics.base_rubric import BaseRubric

logger = logging.getLogger(__name__)


async def run_rubric_job(
    rubric: BaseRubric,
    publisher: TelegramPublisher,
    repo: ContentRepository,
) -> None:
    source_item_id, text = rubric.load_next_item()
    content_id = await publisher.publish_or_moderate(rubric.rubric_type, source_item_id, text)

    item = repo.get_content_item(content_id)
    if item and item.status == ContentStatus.PUBLISHED.value:
        rubric.mark_published(source_item_id)
    logger.info("Rubric job done: %s item=%s", rubric.rubric_type, source_item_id)
