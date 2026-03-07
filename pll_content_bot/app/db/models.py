from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ContentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SKIPPED = "skipped"


@dataclass
class ContentItem:
    id: int
    rubric_type: str
    source_item_id: str
    formatted_text: str
    status: str
    created_at: datetime
    published_at: datetime | None
