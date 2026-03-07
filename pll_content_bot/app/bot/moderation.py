from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def moderation_keyboard(content_id: int, rubric_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Publish", callback_data=f"publish:{rubric_type}:{content_id}")],
            [InlineKeyboardButton(text="🔁 Regenerate", callback_data=f"regen:{rubric_type}:{content_id}")],
            [InlineKeyboardButton(text="⏭ Skip", callback_data=f"skip:{rubric_type}:{content_id}")],
        ]
    )
