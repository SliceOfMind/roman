from __future__ import annotations

import logging

from aiogram import Bot

from app.bot.moderation import moderation_keyboard
from app.config import Settings
from app.db.models import ContentStatus
from app.db.queries import ContentRepository

logger = logging.getLogger(__name__)


class TelegramPublisher:
    def __init__(self, bot: Bot, settings: Settings, repo: ContentRepository):
        self.bot = bot
        self.settings = settings
        self.repo = repo

    async def publish_or_moderate(self, rubric_type: str, source_item_id: str, text: str) -> int:
        status = ContentStatus.PUBLISHED if self.settings.auto_publish else ContentStatus.DRAFT
        content_id = self.repo.create_content_item(rubric_type, source_item_id, text, status)
        if self.settings.auto_publish:
            await self.bot.send_message(chat_id=self.settings.channel_id, text=text)
        else:
            await self.bot.send_message(
                chat_id=self.settings.admin_chat_id,
                text=f"Черновик: {rubric_type}\n\n{text}",
                reply_markup=moderation_keyboard(content_id=content_id, rubric_type=rubric_type),
            )
        logger.info("Handled content item %s for rubric %s", content_id, rubric_type)
        return content_id
