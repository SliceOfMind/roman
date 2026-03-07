from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.models import ContentStatus
from app.bot.publisher import TelegramPublisher
from app.db.queries import ContentRepository, RuntimeSettingsRepository
from app.rubrics.base_rubric import BaseRubric
from app.services.dataset_loader import load_csv_rows
from app.services.openai_client import OpenAIClient

router = Router()


class ModerationHandlers:
    def __init__(
        self,
        repo: ContentRepository,
        runtime_repo: RuntimeSettingsRepository,
        rubrics: dict[str, BaseRubric],
        channel_id: str,
        admin_chat_id: int,
        sqlite_path: str,
        roman_dataset_path: str,
        argument_dataset_path: str,
        scheduler: AsyncIOScheduler,
        ai_client: OpenAIClient,
        roman_post_hour: int,
        argument_post_hour: int,
        publisher: TelegramPublisher,
    ):
        self.repo = repo
        self.runtime_repo = runtime_repo
        self.rubrics = rubrics
        self.channel_id = channel_id
        self.admin_chat_id = admin_chat_id
        self.sqlite_path = sqlite_path
        self.roman_dataset_path = roman_dataset_path
        self.argument_dataset_path = argument_dataset_path
        self.scheduler = scheduler
        self.ai_client = ai_client
        self.roman_post_hour = roman_post_hour
        self.argument_post_hour = argument_post_hour
        self.publisher = publisher

    def register(self, target_router: Router) -> None:
        target_router.message.register(self.start, Command("start"))
        target_router.message.register(self.help_admin, Command("help_admin"))
        target_router.message.register(self.status, Command("status"))
        target_router.message.register(self.health, Command("health"))
        target_router.message.register(self.stats, Command("stats"))
        target_router.message.register(self.test_roman, Command("test_roman"))
        target_router.message.register(self.test_argument, Command("test_argument"))
        target_router.message.register(self.publish_roman, Command("publish_roman"))
        target_router.message.register(self.publish_argument, Command("publish_argument"))
        target_router.message.register(self.next_roman, Command("next_roman"))
        target_router.message.register(self.next_argument, Command("next_argument"))
        target_router.message.register(self.skip_roman, Command("skip_roman"))
        target_router.message.register(self.skip_argument, Command("skip_argument"))
        target_router.message.register(self.autopublish_on, Command("autopublish_on"))
        target_router.message.register(self.autopublish_off, Command("autopublish_off"))
        target_router.message.register(self.scheduler_status, Command("scheduler_status"))

        target_router.callback_query.register(self.publish, F.data.startswith("publish:"))
        target_router.callback_query.register(self.regenerate, F.data.startswith("regen:"))
        target_router.callback_query.register(self.skip, F.data.startswith("skip:"))

    def _is_admin(self, message: Message) -> bool:
        return bool(message.chat and message.chat.id == self.admin_chat_id)

    async def _deny(self, message: Message) -> None:
        await message.answer("Доступ запрещен.")

    async def _admin_guard(self, message: Message) -> bool:
        if self._is_admin(message):
            return True
        await self._deny(message)
        return False

    def _auto_publish(self) -> bool:
        return self.runtime_repo.get_bool("auto_publish", default=False)

    async def start(self, message: Message) -> None:
        await message.answer("Private Law Library bot запущен.")

    async def help_admin(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        await message.answer(
            "Команды администратора:\n"
            "/help_admin — список команд\n"
            "/status — текущий статус системы\n"
            "/health — проверка здоровья\n"
            "/stats — статистика публикаций\n"
            "/test_roman — тестовый черновик Roman Law Today\n"
            "/test_argument — тестовый черновик Аргумент дня\n"
            "/publish_roman — опубликовать следующий Roman Law Today\n"
            "/publish_argument — опубликовать следующий Аргумент дня\n"
            "/next_roman — показать следующий Roman item\n"
            "/next_argument — показать следующий topic\n"
            "/skip_roman — пропустить следующий Roman item\n"
            "/skip_argument — пропустить следующий Argument topic\n"
            "/autopublish_on — включить автопубликацию\n"
            "/autopublish_off — выключить автопубликацию\n"
            "/scheduler_status — задачи планировщика"
        )

    async def status(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        roman_rows = load_csv_rows(self.roman_dataset_path)
        argument_rows = load_csv_rows(self.argument_dataset_path)
        roman_used = self.repo.used_source_ids("roman_law_today", statuses=("published", "skipped"))
        argument_used = self.repo.used_source_ids("argument_of_the_day", statuses=("published", "skipped"))

        await message.answer(
            "Статус системы:\n"
            f"• Автопубликация: {'ON' if self._auto_publish() else 'OFF'}\n"
            f"• OpenAI: {'ON' if self.ai_client.enabled else 'OFF'}\n"
            f"• Планировщик: {'запущен' if self.scheduler.running else 'остановлен'}\n"
            f"• Roman расписание: ежедневно в {self.roman_post_hour:02d}:00\n"
            f"• Argument расписание: ежедневно в {self.argument_post_hour:02d}:00\n"
            f"• База данных: {self.sqlite_path}\n"
            f"• Roman dataset: всего {len(roman_rows)}, неиспользовано {max(0, len(roman_rows)-len(roman_used))}\n"
            f"• Argument dataset: всего {len(argument_rows)}, неиспользовано {max(0, len(argument_rows)-len(argument_used))}\n"
            f"• Режим модерации: {'включен' if not self._auto_publish() else 'выключен'}"
        )

    async def health(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        checks: list[str] = ["• Bot: OK"]
        critical_errors: list[str] = []

        try:
            _ = self.repo.count_content()
            checks.append("• SQLite: OK")
        except Exception as exc:
            checks.append(f"• SQLite: ошибка ({exc})")
            critical_errors.append("SQLite")

        try:
            load_csv_rows(self.roman_dataset_path)
            checks.append("• Roman dataset: OK")
        except Exception as exc:
            checks.append(f"• Roman dataset: ошибка ({exc})")
            critical_errors.append("Roman dataset")

        try:
            load_csv_rows(self.argument_dataset_path)
            checks.append("• Argument dataset: OK")
        except Exception as exc:
            checks.append(f"• Argument dataset: ошибка ({exc})")
            critical_errors.append("Argument dataset")

        checks.append(f"• Планировщик: {'OK' if self.scheduler.running else 'ошибка (не запущен)'}")
        checks.append(f"• OpenAI: {'ON' if self.ai_client.enabled else 'OFF'}")

        summary = "Критических проблем нет." if not critical_errors else f"Критические проблемы: {', '.join(critical_errors)}"
        await message.answer("Health check:\n" + "\n".join(checks) + f"\n\n{summary}")

    async def stats(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        roman_published = self.repo.count_content("roman_law_today", ContentStatus.PUBLISHED.value)
        argument_published = self.repo.count_content("argument_of_the_day", ContentStatus.PUBLISHED.value)
        skipped = len(self.repo.used_source_ids("roman_law_today", statuses=("skipped",))) + len(
            self.repo.used_source_ids("argument_of_the_day", statuses=("skipped",))
        )
        ready_drafts = self.repo.count_content(status=ContentStatus.DRAFT.value)
        archived = self.repo.count_content(status=ContentStatus.ARCHIVED.value)
        await message.answer(
            "Статистика:\n"
            f"• Опубликовано Roman: {roman_published}\n"
            f"• Опубликовано Argument: {argument_published}\n"
            f"• Пропущено элементов: {skipped}\n"
            f"• Черновиков: {ready_drafts}\n"
            f"• Архивных: {archived}"
        )

    async def test_roman(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, text = self.rubrics["roman_law_today"].load_next_item()
        await message.answer(f"Тестовый черновик Roman ({source_item_id}):\n\n{text}")

    async def test_argument(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, text = self.rubrics["argument_of_the_day"].load_next_item()
        await message.answer(f"Тестовый черновик Argument ({source_item_id}):\n\n{text}")

    async def publish_roman(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, text = self.rubrics["roman_law_today"].load_next_item()
        content_id = await self.publisher.publish_or_moderate("roman_law_today", source_item_id, text)
        if self._auto_publish():
            self.rubrics["roman_law_today"].mark_published(source_item_id)
        await message.answer(f"Roman item обработан (ID записи: {content_id}).")

    async def publish_argument(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, text = self.rubrics["argument_of_the_day"].load_next_item()
        content_id = await self.publisher.publish_or_moderate("argument_of_the_day", source_item_id, text)
        if self._auto_publish():
            self.rubrics["argument_of_the_day"].mark_published(source_item_id)
        await message.answer(f"Argument item обработан (ID записи: {content_id}).")

    async def next_roman(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, latin_short = self.rubrics["roman_law_today"].peek_next_item()
        await message.answer(
            "Следующий Roman item:\n"
            f"• ID: {source_item_id}\n"
            f"• Reference: {source_item_id}\n"
            f"• Latin: {latin_short}"
        )

    async def next_argument(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, topic = self.rubrics["argument_of_the_day"].peek_next_item()
        await message.answer(
            "Следующий Argument item:\n"
            f"• ID: {source_item_id}\n"
            f"• Topic: {topic}"
        )

    async def skip_roman(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, _ = self.rubrics["roman_law_today"].peek_next_item()
        self.rubrics["roman_law_today"].mark_skipped(source_item_id)
        await message.answer(f"Roman item {source_item_id} отмечен как пропущенный.")

    async def skip_argument(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        source_item_id, _ = self.rubrics["argument_of_the_day"].peek_next_item()
        self.rubrics["argument_of_the_day"].mark_skipped(source_item_id)
        await message.answer(f"Argument item {source_item_id} отмечен как пропущенный.")

    async def autopublish_on(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        self.runtime_repo.set_bool("auto_publish", True)
        await message.answer("Автопубликация включена (runtime setting).")

    async def autopublish_off(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        self.runtime_repo.set_bool("auto_publish", False)
        await message.answer("Автопубликация выключена (runtime setting).")

    async def scheduler_status(self, message: Message) -> None:
        if not await self._admin_guard(message):
            return
        jobs = self.scheduler.get_jobs()
        if not jobs:
            await message.answer("Планировщик не содержит задач.")
            return
        lines = ["Задачи планировщика:"]
        for job in jobs:
            lines.append(f"• {job.id}: next_run={job.next_run_time}")
        await message.answer("\n".join(lines))

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
        self.rubrics[rubric_type].mark_skipped(item.source_item_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Пропущено")
