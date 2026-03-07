from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.db.models import ContentStatus
from app.db.queries import ContentRepository
from app.rubrics.base_rubric import BaseRubric

router = Router()


class ModerationHandlers:
    def __init__(self, repo: ContentRepository, rubrics: dict[str, BaseRubric], channel_id: str):
        self.repo = repo
        self.rubrics = rubrics
        self.channel_id = channel_id

    def register(self, target_router: Router) -> None:
        target_router.message.register(self.start, F.text == "/start")
        target_router.callback_query.register(self.publish, F.data.startswith("publish:"))
        target_router.callback_query.register(self.regenerate, F.data.startswith("regen:"))
        target_router.callback_query.register(self.skip, F.data.startswith("skip:"))

    async def start(self, message: Message) -> None:
        await message.answer("Private Law Library bot запущен.")

    async def publish(self, callback: CallbackQuery) -> None:
        _, rubric_type, content_id_str = callback.data.split(":")
        content_id = int(content_id_str)
        item = self.repo.get_content_item(content_id)
        if not item:
            await callback.answer("Запись не найдена", show_alert=True)
            return
        await callback.bot.send_message(chat_id=self.channel_id, text=item.formatted_text)
        self.repo.update_content_status(content_id, ContentStatus.PUBLISHED)
        self.rubrics[rubric_type].mark_published(item.source_item_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Опубликовано")

    async def regenerate(self, callback: CallbackQuery) -> None:
        _, rubric_type, content_id_str = callback.data.split(":")
        content_id = int(content_id_str)
        item = self.repo.get_content_item(content_id)
        if not item:
            await callback.answer("Запись не найдена", show_alert=True)
            return
        rubric = self.rubrics[rubric_type]
        new_text = rubric.render_post(item.source_item_id)
        self.repo.update_content_status(content_id, ContentStatus.ARCHIVED)
        new_id = self.repo.create_content_item(
            rubric_type=rubric_type,
            source_item_id=item.source_item_id,
            formatted_text=new_text,
            status=ContentStatus.DRAFT,
        )
        from app.bot.moderation import moderation_keyboard

        await callback.message.edit_text(
            f"Черновик: {rubric_type}\n\n{new_text}",
            reply_markup=moderation_keyboard(content_id=new_id, rubric_type=rubric_type),
        )
        await callback.answer("Перегенерировано")

    async def skip(self, callback: CallbackQuery) -> None:
        _, rubric_type, content_id_str = callback.data.split(":")
        content_id = int(content_id_str)
        item = self.repo.get_content_item(content_id)
        if not item:
            await callback.answer("Запись не найдена", show_alert=True)
            return
        self.repo.update_content_status(content_id, ContentStatus.ARCHIVED)
        self.repo.mark_dataset_used(rubric_type, item.source_item_id, status="skipped")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Пропущено")
