from __future__ import annotations

from app.db.queries import ContentRepository
from app.formatters.telegram_formatter import format_roman_post
from app.rubrics.base_rubric import BaseRubric
from app.services.dataset_loader import load_csv_rows


class RomanLawTodayRubric(BaseRubric):
    rubric_type = "roman_law_today"

    def __init__(self, dataset_path: str, repo: ContentRepository):
        self.dataset_path = dataset_path
        self.repo = repo

    def _next_row(self) -> dict[str, str]:
        rows = load_csv_rows(self.dataset_path)
        blocked_ids = self.repo.used_source_ids(self.rubric_type, statuses=("published", "skipped"))
        for row in rows:
            if row["reference"] not in blocked_ids:
                return row
        return rows[0]

    def load_next_item(self) -> tuple[str, str]:
        item = self._next_row()
        return item["reference"], format_roman_post(item)

    def render_post(self, source_item_id: str) -> str:
        rows = load_csv_rows(self.dataset_path)
        item = next(row for row in rows if row["reference"] == source_item_id)
        return format_roman_post(item)

    def mark_published(self, source_item_id: str) -> None:
        self.repo.mark_dataset_used(self.rubric_type, source_item_id, status="published")

    def peek_next_item(self) -> tuple[str, str]:
        item = self._next_row()
        latin_short = item["latin"][:80] + ("..." if len(item["latin"]) > 80 else "")
        return item["reference"], latin_short

    def mark_skipped(self, source_item_id: str) -> None:
        self.repo.mark_dataset_used(self.rubric_type, source_item_id, status="skipped")
