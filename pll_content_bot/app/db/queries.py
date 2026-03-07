from __future__ import annotations

from datetime import datetime, timezone

from app.db.database import Database
from app.db.models import ContentItem, ContentStatus


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContentRepository:
    def __init__(self, database: Database):
        self.db = database

    def create_content_item(
        self,
        rubric_type: str,
        source_item_id: str,
        formatted_text: str,
        status: ContentStatus,
        tags: str | None = None,
    ) -> int:
        with self.db.get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO content_items (rubric_type, source_item_id, formatted_text, status, created_at, tags)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rubric_type, source_item_id, formatted_text, status.value, now_iso(), tags),
            )
            return int(cur.lastrowid)

    def update_content_status(self, content_id: int, status: ContentStatus) -> None:
        published_at = now_iso() if status == ContentStatus.PUBLISHED else None
        with self.db.get_conn() as conn:
            conn.execute(
                """
                UPDATE content_items
                SET status = ?, published_at = COALESCE(?, published_at)
                WHERE id = ?
                """,
                (status.value, published_at, content_id),
            )

    def get_content_item(self, content_id: int) -> ContentItem | None:
        with self.db.get_conn() as conn:
            row = conn.execute("SELECT * FROM content_items WHERE id = ?", (content_id,)).fetchone()
        if not row:
            return None
        return ContentItem(
            id=row["id"],
            rubric_type=row["rubric_type"],
            source_item_id=row["source_item_id"],
            formatted_text=row["formatted_text"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
        )

    def mark_dataset_used(self, rubric_type: str, source_item_id: str, status: str = "published") -> None:
        with self.db.get_conn() as conn:
            conn.execute(
                "INSERT INTO dataset_usage (rubric_type, source_item_id, used_at, status) VALUES (?, ?, ?, ?)",
                (rubric_type, source_item_id, now_iso(), status),
            )

    def used_source_ids(self, rubric_type: str) -> set[str]:
        with self.db.get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT source_item_id FROM dataset_usage WHERE rubric_type = ? AND status = 'published'",
                (rubric_type,),
            ).fetchall()
        return {str(row["source_item_id"]) for row in rows}
