from __future__ import annotations

import random

from app.db.queries import ContentRepository
from app.formatters.telegram_formatter import format_argument_post
from app.rubrics.base_rubric import BaseRubric
from app.services.dataset_loader import load_csv_rows
from app.services.openai_client import OpenAIClient


class ArgumentOfTheDayRubric(BaseRubric):
    rubric_type = "argument_of_the_day"

    def __init__(self, dataset_path: str, repo: ContentRepository, ai_client: OpenAIClient):
        self.dataset_path = dataset_path
        self.repo = repo
        self.ai_client = ai_client

    def _pick_item(self) -> tuple[str, str]:
        rows = load_csv_rows(self.dataset_path)
        used_ids = self.repo.used_source_ids(self.rubric_type)
        indexed_rows = list(enumerate(rows))
        available = [(idx, row) for idx, row in indexed_rows if str(idx) not in used_ids]
        if not available:
            available = indexed_rows
        idx, row = random.choice(available)
        return str(idx), row["topic"]

    def load_next_item(self) -> tuple[str, str]:
        source_item_id, topic = self._pick_item()
        generated = self.ai_client.generate_arguments(topic)
        return source_item_id, format_argument_post(topic, generated)

    def render_post(self, source_item_id: str) -> str:
        rows = load_csv_rows(self.dataset_path)
        topic = rows[int(source_item_id)]["topic"]
        generated = self.ai_client.generate_arguments(topic)
        return format_argument_post(topic, generated)

    def mark_published(self, source_item_id: str) -> None:
        self.repo.mark_dataset_used(self.rubric_type, source_item_id, status="published")
