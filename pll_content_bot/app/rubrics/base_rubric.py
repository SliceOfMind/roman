from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRubric(ABC):
    rubric_type: str

    @abstractmethod
    def load_next_item(self) -> tuple[str, str]:
        """Return source_item_id and formatted text for next post."""

    @abstractmethod
    def render_post(self, source_item_id: str) -> str:
        """Render post text for a given source item id."""

    @abstractmethod
    def mark_published(self, source_item_id: str) -> None:
        """Mark source item as published/used."""

    @abstractmethod
    def peek_next_item(self) -> tuple[str, str]:
        """Return source item id and short description for the next dataset item."""

    @abstractmethod
    def mark_skipped(self, source_item_id: str) -> None:
        """Mark source item as skipped so it is not selected immediately."""
